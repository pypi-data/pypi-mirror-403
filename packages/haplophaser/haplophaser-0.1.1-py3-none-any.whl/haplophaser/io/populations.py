"""
Population and sample metadata I/O.

Functions for reading and writing sample/population assignment files
in TSV and YAML formats.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from haplophaser.core.models import Population, PopulationRole, Sample, Subgenome

logger = logging.getLogger(__name__)


class PopulationSpec(BaseModel):
    """Specification for loading populations from files.

    Intermediate representation used when parsing population files
    before constructing full Population objects.

    Parameters
    ----------
    name : str
        Population name.
    role : PopulationRole
        Role in analysis.
    samples : list[str]
        Sample names belonging to this population.
    ploidy : int
        Default ploidy for samples in this population.
    description : str, optional
        Population description.
    """

    name: str
    role: PopulationRole
    samples: list[str] = Field(default_factory=list)
    ploidy: int = Field(default=2, ge=1, le=16)
    description: str | None = None

    @field_validator("role", mode="before")
    @classmethod
    def parse_role(cls, v: str | PopulationRole) -> PopulationRole:
        """Parse role from string."""
        if isinstance(v, PopulationRole):
            return v
        return PopulationRole(v.lower())

    def to_population(self) -> Population:
        """Convert to Population with Sample objects.

        Returns
        -------
        Population
            Fully constructed Population instance.
        """
        sample_objects = [
            Sample(name=name, ploidy=self.ploidy, population=self.name)
            for name in self.samples
        ]
        return Population(
            name=self.name,
            samples=sample_objects,
            role=self.role,
            description=self.description,
        )


def load_populations_tsv(path: Path | str) -> list[Population]:
    """Load population assignments from TSV file.

    Expected TSV format (tab-separated, header required):
        sample<TAB>population<TAB>role[<TAB>ploidy]

    The ploidy column is optional (defaults to 2).

    Parameters
    ----------
    path : Path or str
        Path to TSV file.

    Returns
    -------
    list[Population]
        List of Population objects with assigned samples.

    Raises
    ------
    FileNotFoundError
        If file doesn't exist.
    ValueError
        If file format is invalid.

    Examples
    --------
    >>> populations = load_populations_tsv("samples.tsv")

    File format example::

        sample  population  role    ploidy
        B73     NAM_founders    founder 2
        Mo17    NAM_founders    founder 2
        RIL_001 NAM_derived derived 2
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Population file not found: {path}")

    logger.info(f"Loading populations from TSV: {path}")

    # Group samples by population
    pop_data: dict[str, dict[str, Any]] = {}

    with open(path) as f:
        header = f.readline().strip().split("\t")

        # Validate header
        required = {"sample", "population", "role"}
        header_set = {h.lower() for h in header}
        missing = required - header_set
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

        # Find column indices
        col_idx = {h.lower(): i for i, h in enumerate(header)}
        sample_idx = col_idx["sample"]
        pop_idx = col_idx["population"]
        role_idx = col_idx["role"]
        ploidy_idx = col_idx.get("ploidy")

        for line_num, line in enumerate(f, start=2):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            fields = line.split("\t")

            try:
                sample_name = fields[sample_idx]
                pop_name = fields[pop_idx]
                role_str = fields[role_idx]
                ploidy = int(fields[ploidy_idx]) if ploidy_idx and len(fields) > ploidy_idx else 2

                if pop_name not in pop_data:
                    pop_data[pop_name] = {
                        "name": pop_name,
                        "role": PopulationRole(role_str.lower()),
                        "samples": [],
                        "ploidy": ploidy,
                    }

                pop_data[pop_name]["samples"].append(sample_name)

            except (IndexError, ValueError) as e:
                raise ValueError(f"Invalid format at line {line_num}: {e}") from e

    # Convert to Population objects
    populations = []
    for data in pop_data.values():
        spec = PopulationSpec(**data)
        populations.append(spec.to_population())

    logger.info(f"Loaded {len(populations)} populations with {sum(len(p.samples) for p in populations)} samples")

    return populations


def load_populations_yaml(path: Path | str) -> list[Population]:
    """Load population definitions from YAML file.

    YAML format allows richer specification including subgenomes
    for polyploid samples.

    Parameters
    ----------
    path : Path or str
        Path to YAML file.

    Returns
    -------
    list[Population]
        List of Population objects.

    Raises
    ------
    FileNotFoundError
        If file doesn't exist.
    ValueError
        If YAML format is invalid.

    Examples
    --------
    >>> populations = load_populations_yaml("populations.yaml")

    YAML format example::

        populations:
          - name: NAM_founders
            role: founder
            ploidy: 2
            samples:
              - B73
              - Mo17
              - W22

          - name: wheat_founders
            role: founder
            ploidy: 6
            subgenomes:
              - name: A
                ploidy: 2
              - name: B
                ploidy: 2
              - name: D
                ploidy: 2
            samples:
              - Chinese_Spring
              - Jagger
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Population file not found: {path}")

    logger.info(f"Loading populations from YAML: {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    if data is None:
        raise ValueError("Empty YAML file")

    if "populations" not in data:
        raise ValueError("YAML must contain 'populations' key")

    populations = []

    for pop_def in data["populations"]:
        # Parse subgenomes if present
        subgenomes = []
        if "subgenomes" in pop_def:
            for sg_def in pop_def["subgenomes"]:
                subgenomes.append(Subgenome(**sg_def))

        # Parse samples with optional per-sample overrides
        samples = []
        sample_list = pop_def.get("samples", [])
        default_ploidy = pop_def.get("ploidy", 2)

        for sample_def in sample_list:
            if isinstance(sample_def, str):
                # Simple sample name
                samples.append(
                    Sample(
                        name=sample_def,
                        ploidy=default_ploidy,
                        subgenomes=subgenomes,
                        population=pop_def["name"],
                    )
                )
            elif isinstance(sample_def, dict):
                # Sample with overrides
                sample_subgenomes = subgenomes
                if "subgenomes" in sample_def:
                    sample_subgenomes = [
                        Subgenome(**sg) for sg in sample_def["subgenomes"]
                    ]
                samples.append(
                    Sample(
                        name=sample_def["name"],
                        ploidy=sample_def.get("ploidy", default_ploidy),
                        subgenomes=sample_subgenomes,
                        population=pop_def["name"],
                        metadata=sample_def.get("metadata", {}),
                    )
                )

        population = Population(
            name=pop_def["name"],
            samples=samples,
            role=PopulationRole(pop_def["role"].lower()),
            description=pop_def.get("description"),
        )
        populations.append(population)

    logger.info(f"Loaded {len(populations)} populations with {sum(len(p.samples) for p in populations)} samples")

    return populations


def write_populations_tsv(
    populations: list[Population],
    path: Path | str,
    include_ploidy: bool = True,
) -> None:
    """Write population assignments to TSV file.

    Parameters
    ----------
    populations : list[Population]
        Populations to write.
    path : Path or str
        Output file path.
    include_ploidy : bool
        Include ploidy column in output.

    Examples
    --------
    >>> write_populations_tsv(populations, "samples.tsv")
    """
    path = Path(path)

    logger.info(f"Writing populations to TSV: {path}")

    with open(path, "w") as f:
        # Write header
        columns = ["sample", "population", "role"]
        if include_ploidy:
            columns.append("ploidy")
        f.write("\t".join(columns) + "\n")

        # Write sample rows
        for pop in populations:
            for sample in pop.samples:
                row = [sample.name, pop.name, pop.role.value]
                if include_ploidy:
                    row.append(str(sample.ploidy))
                f.write("\t".join(row) + "\n")

    total_samples = sum(len(p.samples) for p in populations)
    logger.info(f"Wrote {len(populations)} populations, {total_samples} samples")


def write_populations_yaml(
    populations: list[Population],
    path: Path | str,
) -> None:
    """Write population definitions to YAML file.

    Parameters
    ----------
    populations : list[Population]
        Populations to write.
    path : Path or str
        Output file path.

    Examples
    --------
    >>> write_populations_yaml(populations, "populations.yaml")
    """
    path = Path(path)

    logger.info(f"Writing populations to YAML: {path}")

    data = {"populations": []}

    for pop in populations:
        pop_dict: dict[str, Any] = {
            "name": pop.name,
            "role": pop.role.value,
        }

        if pop.description:
            pop_dict["description"] = pop.description

        # Check if all samples have same ploidy
        ploidies = {s.ploidy for s in pop.samples}
        if len(ploidies) == 1:
            pop_dict["ploidy"] = ploidies.pop()

        # Check if samples have subgenomes
        any(s.subgenomes for s in pop.samples)

        # Build sample list
        sample_list: list[Any] = []
        for sample in pop.samples:
            if sample.subgenomes or sample.metadata or len(ploidies) > 1:
                # Complex sample representation
                sample_dict: dict[str, Any] = {"name": sample.name}
                if len(ploidies) > 1:
                    sample_dict["ploidy"] = sample.ploidy
                if sample.subgenomes:
                    sample_dict["subgenomes"] = [
                        {"name": sg.name, "ploidy": sg.ploidy}
                        for sg in sample.subgenomes
                    ]
                if sample.metadata:
                    sample_dict["metadata"] = sample.metadata
                sample_list.append(sample_dict)
            else:
                # Simple sample name
                sample_list.append(sample.name)

        pop_dict["samples"] = sample_list
        data["populations"].append(pop_dict)

    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    total_samples = sum(len(p.samples) for p in populations)
    logger.info(f"Wrote {len(populations)} populations, {total_samples} samples")


def infer_populations_from_vcf(
    vcf_samples: list[str],
    pattern: str | None = None,
) -> list[Population]:
    """Create default population from VCF sample names.

    Utility function when no population file is provided. All samples
    are assigned to a single 'default' population as derived.

    Parameters
    ----------
    vcf_samples : list[str]
        Sample names from VCF.
    pattern : str, optional
        Regex pattern to extract population from sample name.
        Not yet implemented.

    Returns
    -------
    list[Population]
        List containing single population with all samples.
    """
    samples = [Sample(name=name, ploidy=2, population="default") for name in vcf_samples]

    return [
        Population(
            name="default",
            samples=samples,
            role=PopulationRole.DERIVED,
            description="Auto-generated from VCF samples",
        )
    ]


def load_populations(path: Path | str) -> list[Population]:
    """Load population definitions, auto-detecting file format.

    Supports TSV (.tsv, .txt) and YAML (.yaml, .yml) formats.

    Parameters
    ----------
    path : Path or str
        Path to population file.

    Returns
    -------
    list[Population]
        List of Population objects.

    Raises
    ------
    FileNotFoundError
        If file doesn't exist.
    ValueError
        If file format is unknown or invalid.

    Examples
    --------
    >>> populations = load_populations("samples.tsv")
    >>> populations = load_populations("populations.yaml")
    """
    path = Path(path)
    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        return load_populations_yaml(path)
    elif suffix in (".tsv", ".txt", ".tab"):
        return load_populations_tsv(path)
    else:
        # Try to auto-detect based on content
        with open(path) as f:
            first_line = f.readline().strip()

        if first_line.startswith("populations:") or first_line.startswith("---"):
            return load_populations_yaml(path)
        elif "\t" in first_line or first_line.lower().startswith("sample"):
            return load_populations_tsv(path)
        else:
            raise ValueError(
                f"Unknown population file format: {path}. "
                "Use .tsv/.txt for TSV format or .yaml/.yml for YAML format."
            )


@dataclass
class PopulationValidationResult:
    """Result of validating populations against VCF samples.

    Parameters
    ----------
    valid : bool
        Whether validation passed.
    populations : list[Population]
        Validated population objects.
    vcf_samples : list[str]
        Sample names from VCF.
    found_samples : list[str]
        Population samples found in VCF.
    missing_samples : list[str]
        Population samples missing from VCF.
    extra_vcf_samples : list[str]
        VCF samples not in any population.
    ploidy_mismatches : list[tuple[str, int, int]]
        Samples with ploidy mismatches: (sample, expected, observed).
    warnings : list[str]
        Warning messages.
    errors : list[str]
        Error messages.
    """

    valid: bool
    populations: list[Population]
    vcf_samples: list[str]
    found_samples: list[str]
    missing_samples: list[str]
    extra_vcf_samples: list[str]
    ploidy_mismatches: list[tuple[str, int, int]]
    warnings: list[str]
    errors: list[str]

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "Population Validation Summary:",
            f"  Status: {'PASSED' if self.valid else 'FAILED'}",
            f"  VCF samples: {len(self.vcf_samples)}",
            f"  Population samples found: {len(self.found_samples)}",
            f"  Population samples missing: {len(self.missing_samples)}",
            f"  Extra VCF samples: {len(self.extra_vcf_samples)}",
        ]

        # Count by role
        n_founders = sum(
            len(p.samples) for p in self.populations if p.role == PopulationRole.FOUNDER
        )
        n_derived = sum(
            len(p.samples) for p in self.populations if p.role == PopulationRole.DERIVED
        )
        lines.append(f"  Founder samples: {n_founders}")
        lines.append(f"  Derived samples: {n_derived}")

        if self.warnings:
            lines.append("\nWarnings:")
            for w in self.warnings:
                lines.append(f"  - {w}")

        if self.errors:
            lines.append("\nErrors:")
            for e in self.errors:
                lines.append(f"  - {e}")

        return "\n".join(lines)


def validate_populations_against_vcf(
    populations: list[Population],
    vcf_samples: list[str],
    strict: bool = False,
) -> PopulationValidationResult:
    """Validate that population samples exist in VCF.

    Parameters
    ----------
    populations : list[Population]
        Populations to validate.
    vcf_samples : list[str]
        Sample names from VCF file.
    strict : bool
        If True, validation fails if any samples are missing.
        If False, missing samples generate warnings.

    Returns
    -------
    PopulationValidationResult
        Validation results.

    Examples
    --------
    >>> from haplophaser.io import get_sample_names, load_populations
    >>> populations = load_populations("samples.tsv")
    >>> vcf_samples = get_sample_names("variants.vcf.gz")
    >>> result = validate_populations_against_vcf(populations, vcf_samples)
    >>> if not result.valid:
    ...     print(result.summary())
    """
    vcf_sample_set = set(vcf_samples)
    pop_sample_names: list[str] = []
    for pop in populations:
        pop_sample_names.extend(s.name for s in pop.samples)

    found = [s for s in pop_sample_names if s in vcf_sample_set]
    missing = [s for s in pop_sample_names if s not in vcf_sample_set]
    extra = [s for s in vcf_samples if s not in set(pop_sample_names)]

    warnings: list[str] = []
    errors: list[str] = []
    ploidy_mismatches: list[tuple[str, int, int]] = []

    # Check for missing samples
    if missing:
        msg = f"{len(missing)} population samples not found in VCF: {missing[:5]}{'...' if len(missing) > 5 else ''}"
        if strict:
            errors.append(msg)
        else:
            warnings.append(msg)

    # Check for extra VCF samples
    if extra:
        warnings.append(
            f"{len(extra)} VCF samples not in any population: {extra[:5]}{'...' if len(extra) > 5 else ''}"
        )

    # Check for duplicate samples across populations
    seen: dict[str, str] = {}
    for pop in populations:
        for sample in pop.samples:
            if sample.name in seen:
                errors.append(
                    f"Sample '{sample.name}' appears in multiple populations: "
                    f"'{seen[sample.name]}' and '{pop.name}'"
                )
            else:
                seen[sample.name] = pop.name

    # Check for required roles
    has_founder = any(p.role == PopulationRole.FOUNDER for p in populations)
    has_derived = any(p.role == PopulationRole.DERIVED for p in populations)

    if not has_founder:
        warnings.append("No founder population defined")
    if not has_derived:
        warnings.append("No derived population defined")

    valid = len(errors) == 0

    return PopulationValidationResult(
        valid=valid,
        populations=populations,
        vcf_samples=vcf_samples,
        found_samples=found,
        missing_samples=missing,
        extra_vcf_samples=extra,
        ploidy_mismatches=ploidy_mismatches,
        warnings=warnings,
        errors=errors,
    )


def get_all_samples(populations: list[Population]) -> list[Sample]:
    """Get all samples from a list of populations.

    Parameters
    ----------
    populations : list[Population]
        List of populations.

    Returns
    -------
    list[Sample]
        All samples from all populations.
    """
    samples = []
    for pop in populations:
        samples.extend(pop.samples)
    return samples


def get_samples_by_role(
    populations: list[Population],
    role: PopulationRole,
) -> list[Sample]:
    """Get samples from populations with a specific role.

    Parameters
    ----------
    populations : list[Population]
        List of populations.
    role : PopulationRole
        Role to filter by.

    Returns
    -------
    list[Sample]
        Samples from populations with the specified role.
    """
    samples = []
    for pop in populations:
        if pop.role == role:
            samples.extend(pop.samples)
    return samples


def get_founder_sample_names(populations: list[Population]) -> list[str]:
    """Get names of all founder samples.

    Parameters
    ----------
    populations : list[Population]
        List of populations.

    Returns
    -------
    list[str]
        Names of founder samples.
    """
    return [s.name for s in get_samples_by_role(populations, PopulationRole.FOUNDER)]


def get_derived_sample_names(populations: list[Population]) -> list[str]:
    """Get names of all derived samples.

    Parameters
    ----------
    populations : list[Population]
        List of populations.

    Returns
    -------
    list[str]
        Names of derived samples.
    """
    return [s.name for s in get_samples_by_role(populations, PopulationRole.DERIVED)]
