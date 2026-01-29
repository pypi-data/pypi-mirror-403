"""
Expression data I/O for Salmon, Kallisto, and featureCounts.

Supports loading expression quantification from common RNA-seq tools
and converting to standardized ExpressionMatrix format.
"""

from __future__ import annotations

import gzip
import logging
from pathlib import Path

import numpy as np

from haplophaser.expression.models import (
    ExpressionFormat,
    ExpressionMatrix,
    ExpressionSample,
)

logger = logging.getLogger(__name__)


def detect_expression_format(path: Path | str) -> ExpressionFormat:
    """Detect expression data format from file.

    Parameters
    ----------
    path : Path or str
        Path to expression file or directory.

    Returns
    -------
    ExpressionFormat
        Detected format.

    Raises
    ------
    ValueError
        If format cannot be determined.
    """
    path = Path(path)

    # Check for Salmon output directory
    if path.is_dir():
        if (path / "quant.sf").exists():
            return ExpressionFormat.SALMON
        if (path / "abundance.tsv").exists():
            return ExpressionFormat.KALLISTO
        raise ValueError(f"Cannot determine format from directory: {path}")

    # Check file contents
    suffix = path.suffix.lower()
    if suffix == ".gz":
        suffix = path.with_suffix("").suffix.lower()
        opener = gzip.open
    else:
        opener = open

    with opener(path, "rt") as f:
        header = f.readline().strip()

    header_lower = header.lower()

    # Salmon quant.sf
    if header_lower.startswith("name\tlength\teffectivelength\ttpm"):
        return ExpressionFormat.SALMON

    # Kallisto abundance.tsv
    if header_lower.startswith("target_id\tlength\teff_length\test_counts\ttpm"):
        return ExpressionFormat.KALLISTO

    # featureCounts
    if "geneid" in header_lower and ("chr" in header_lower or "start" in header_lower):
        return ExpressionFormat.FEATURECOUNTS

    # Generic TPM matrix
    if "tpm" in header_lower or header.count("\t") > 2:
        return ExpressionFormat.TPM_MATRIX

    # Generic counts
    if "count" in header_lower:
        return ExpressionFormat.RAW_COUNTS

    return ExpressionFormat.TPM_MATRIX


def load_salmon_quant(
    path: Path | str,
    sample_id: str | None = None,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Load Salmon quant.sf file.

    Parameters
    ----------
    path : Path or str
        Path to quant.sf file or directory containing it.
    sample_id : str, optional
        Sample ID (defaults to directory name).

    Returns
    -------
    tuple[list[str], np.ndarray, np.ndarray]
        (gene_ids, tpm_values, count_values)
    """
    path = Path(path)
    if path.is_dir():
        quant_file = path / "quant.sf"
        sample_id = sample_id or path.name
    else:
        quant_file = path
        sample_id = sample_id or path.parent.name

    gene_ids = []
    tpm_values = []
    counts = []

    opener = gzip.open if str(quant_file).endswith(".gz") else open

    with opener(quant_file, "rt") as f:
        f.readline()  # Skip header
        for line in f:
            fields = line.strip().split("\t")
            if len(fields) >= 5:
                gene_ids.append(fields[0])
                tpm_values.append(float(fields[3]))
                counts.append(float(fields[4]))

    return gene_ids, np.array(tpm_values), np.array(counts)


def load_kallisto_abundance(
    path: Path | str,
    sample_id: str | None = None,
) -> tuple[list[str], np.ndarray, np.ndarray]:
    """Load Kallisto abundance.tsv file.

    Parameters
    ----------
    path : Path or str
        Path to abundance.tsv file or directory containing it.
    sample_id : str, optional
        Sample ID (defaults to directory name).

    Returns
    -------
    tuple[list[str], np.ndarray, np.ndarray]
        (gene_ids, tpm_values, count_values)
    """
    path = Path(path)
    if path.is_dir():
        abundance_file = path / "abundance.tsv"
        sample_id = sample_id or path.name
    else:
        abundance_file = path
        sample_id = sample_id or path.parent.name

    gene_ids = []
    tpm_values = []
    counts = []

    opener = gzip.open if str(abundance_file).endswith(".gz") else open

    with opener(abundance_file, "rt") as f:
        f.readline()  # Skip header
        for line in f:
            fields = line.strip().split("\t")
            if len(fields) >= 5:
                gene_ids.append(fields[0])
                counts.append(float(fields[3]))
                tpm_values.append(float(fields[4]))

    return gene_ids, np.array(tpm_values), np.array(counts)


def load_featurecounts(
    path: Path | str,
) -> tuple[list[str], list[str], np.ndarray]:
    """Load featureCounts output.

    Parameters
    ----------
    path : Path or str
        Path to featureCounts output file.

    Returns
    -------
    tuple[list[str], list[str], np.ndarray]
        (gene_ids, sample_ids, count_matrix)
    """
    path = Path(path)

    gene_ids = []
    counts_list = []

    opener = gzip.open if str(path).endswith(".gz") else open

    with opener(path, "rt") as f:
        # Skip comment lines
        line = f.readline()
        while line.startswith("#"):
            line = f.readline()

        # Parse header
        header = line.strip().split("\t")
        # First columns are Geneid, Chr, Start, End, Strand, Length
        # Sample columns start after these
        sample_start = 6
        sample_ids = header[sample_start:]

        # Parse data
        for line in f:
            fields = line.strip().split("\t")
            if len(fields) > sample_start:
                gene_ids.append(fields[0])
                row_counts = [float(x) for x in fields[sample_start:]]
                counts_list.append(row_counts)

    counts = np.array(counts_list)
    return gene_ids, sample_ids, counts


def counts_to_tpm(
    counts: np.ndarray,
    lengths: np.ndarray | None = None,
) -> np.ndarray:
    """Convert raw counts to TPM.

    Parameters
    ----------
    counts : np.ndarray
        Raw count matrix (genes x samples).
    lengths : np.ndarray, optional
        Gene lengths for length normalization.

    Returns
    -------
    np.ndarray
        TPM values.
    """
    if lengths is not None:
        # Normalize by length (reads per kilobase)
        rpk = counts / (lengths[:, np.newaxis] / 1000)
    else:
        rpk = counts

    # Scale to TPM (per million)
    scaling = rpk.sum(axis=0) / 1e6
    tpm = rpk / scaling

    return tpm


def load_expression_matrix(
    path: Path | str,
    format: ExpressionFormat | None = None,
    sample_metadata: dict[str, dict] | None = None,
) -> ExpressionMatrix:
    """Load expression matrix from various formats.

    Parameters
    ----------
    path : Path or str
        Path to expression file.
    format : ExpressionFormat, optional
        File format (auto-detected if not specified).
    sample_metadata : dict, optional
        Metadata for samples: {sample_id: {condition: str, tissue: str, ...}}.

    Returns
    -------
    ExpressionMatrix
        Loaded expression matrix.
    """
    path = Path(path)

    if format is None:
        format = detect_expression_format(path)

    logger.info(f"Loading expression data as {format.value} format")

    if format == ExpressionFormat.SALMON:
        gene_ids, tpm, counts = load_salmon_quant(path)
        sample_id = path.name if path.is_dir() else path.stem
        sample_ids = [sample_id]
        values = tpm.reshape(-1, 1)
        unit = "tpm"

    elif format == ExpressionFormat.KALLISTO:
        gene_ids, tpm, counts = load_kallisto_abundance(path)
        sample_id = path.name if path.is_dir() else path.stem
        sample_ids = [sample_id]
        values = tpm.reshape(-1, 1)
        unit = "tpm"

    elif format == ExpressionFormat.FEATURECOUNTS:
        gene_ids, sample_ids, counts = load_featurecounts(path)
        values = counts_to_tpm(counts)
        unit = "tpm"

    else:  # TPM_MATRIX or RAW_COUNTS
        gene_ids, sample_ids, values, unit = _load_generic_matrix(path)

    # Create sample objects
    samples = []
    for sid in sample_ids:
        meta = (sample_metadata or {}).get(sid, {})
        samples.append(ExpressionSample(
            sample_id=sid,
            condition=meta.get("condition"),
            tissue=meta.get("tissue"),
            replicate=meta.get("replicate"),
            metadata=meta,
        ))

    return ExpressionMatrix(
        gene_ids=gene_ids,
        samples=samples,
        values=values,
        unit=unit,
    )


def _load_generic_matrix(
    path: Path | str,
) -> tuple[list[str], list[str], np.ndarray, str]:
    """Load generic expression matrix.

    Parameters
    ----------
    path : Path or str
        Path to matrix file.

    Returns
    -------
    tuple
        (gene_ids, sample_ids, values, unit)
    """
    path = Path(path)

    gene_ids = []
    values_list = []

    opener = gzip.open if str(path).endswith(".gz") else open

    with opener(path, "rt") as f:
        header = f.readline().strip().split("\t")
        # First column is gene ID, rest are samples
        sample_ids = header[1:]

        for line in f:
            fields = line.strip().split("\t")
            if len(fields) > 1:
                gene_ids.append(fields[0])
                row_values = [float(x) if x and x != "NA" else 0.0 for x in fields[1:]]
                values_list.append(row_values)

    values = np.array(values_list)

    # Guess unit from header
    unit = "tpm"
    header_str = "\t".join(header).lower()
    if "count" in header_str:
        unit = "counts"
    elif "fpkm" in header_str:
        unit = "fpkm"
    elif "cpm" in header_str:
        unit = "cpm"

    return gene_ids, sample_ids, values, unit


def load_multiple_samples(
    sample_dirs: list[Path | str],
    format: ExpressionFormat | None = None,
    sample_metadata: dict[str, dict] | None = None,
) -> ExpressionMatrix:
    """Load and merge expression data from multiple sample directories.

    Parameters
    ----------
    sample_dirs : list[Path | str]
        List of sample directories (Salmon or Kallisto output).
    format : ExpressionFormat, optional
        File format (auto-detected if not specified).
    sample_metadata : dict, optional
        Metadata for samples.

    Returns
    -------
    ExpressionMatrix
        Merged expression matrix.
    """
    if not sample_dirs:
        raise ValueError("No sample directories provided")

    # Determine format from first sample
    if format is None:
        format = detect_expression_format(sample_dirs[0])

    all_gene_ids = None
    all_samples = []
    all_values = []

    for sample_dir in sample_dirs:
        sample_dir = Path(sample_dir)
        sample_id = sample_dir.name

        if format == ExpressionFormat.SALMON:
            gene_ids, tpm, _ = load_salmon_quant(sample_dir)
        elif format == ExpressionFormat.KALLISTO:
            gene_ids, tpm, _ = load_kallisto_abundance(sample_dir)
        else:
            raise ValueError(f"Cannot load multiple samples for format {format}")

        if all_gene_ids is None:
            all_gene_ids = gene_ids
        elif gene_ids != all_gene_ids:
            # Reorder to match first sample
            gene_to_idx = {g: i for i, g in enumerate(gene_ids)}
            reordered_tpm = np.zeros(len(all_gene_ids))
            for i, g in enumerate(all_gene_ids):
                if g in gene_to_idx:
                    reordered_tpm[i] = tpm[gene_to_idx[g]]
            tpm = reordered_tpm

        meta = (sample_metadata or {}).get(sample_id, {})
        all_samples.append(ExpressionSample(
            sample_id=sample_id,
            condition=meta.get("condition"),
            tissue=meta.get("tissue"),
            replicate=meta.get("replicate"),
            metadata=meta,
        ))
        all_values.append(tpm)

    values = np.column_stack(all_values)

    return ExpressionMatrix(
        gene_ids=all_gene_ids,
        samples=all_samples,
        values=values,
        unit="tpm",
    )


def parse_sample_metadata(
    metadata_file: Path | str,
) -> dict[str, dict]:
    """Parse sample metadata from file.

    Parameters
    ----------
    metadata_file : Path or str
        Path to metadata TSV file with columns:
        sample_id, condition, tissue, replicate, ...

    Returns
    -------
    dict
        Sample ID to metadata mapping.
    """
    path = Path(metadata_file)
    metadata = {}

    with open(path) as f:
        header = f.readline().strip().split("\t")

        for line in f:
            fields = line.strip().split("\t")
            if not fields:
                continue

            sample_id = fields[0]
            sample_meta = {}

            for i, col in enumerate(header[1:], 1):
                if i < len(fields):
                    value = fields[i]
                    # Try to convert to int for replicate
                    if col.lower() == "replicate" and value.isdigit():
                        sample_meta[col.lower()] = int(value)
                    else:
                        sample_meta[col.lower()] = value

            metadata[sample_id] = sample_meta

    return metadata


def write_expression_matrix(
    matrix: ExpressionMatrix,
    output: Path | str,
    include_metadata: bool = True,
) -> None:
    """Write expression matrix to file.

    Parameters
    ----------
    matrix : ExpressionMatrix
        Expression matrix to write.
    output : Path or str
        Output file path.
    include_metadata : bool
        Include sample metadata as header comment.
    """
    output = Path(output)

    with open(output, "w") as f:
        # Write metadata comment
        if include_metadata:
            f.write(f"# unit: {matrix.unit}\n")
            f.write(f"# n_genes: {matrix.n_genes}\n")
            f.write(f"# n_samples: {matrix.n_samples}\n")

        # Write header
        header = ["gene_id"] + matrix.sample_ids
        f.write("\t".join(header) + "\n")

        # Write data
        for i, gene_id in enumerate(matrix.gene_ids):
            values = matrix.values[i, :]
            row = [gene_id] + [f"{v:.4f}" for v in values]
            f.write("\t".join(row) + "\n")

    logger.info(f"Wrote expression matrix to {output}")
