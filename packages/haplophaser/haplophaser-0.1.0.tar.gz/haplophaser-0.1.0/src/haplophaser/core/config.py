"""
Configuration system for Phaser.

Provides YAML-based configuration with sensible defaults and validation.
Configuration can be loaded from files, environment variables, or set
programmatically.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

logger = logging.getLogger(__name__)


class WindowConfig(BaseModel):
    """Configuration for genomic window analysis.

    Parameters
    ----------
    size : int
        Window size in base pairs.
    step : int, optional
        Step size for sliding windows. Defaults to window size (non-overlapping).
    min_variants : int
        Minimum number of informative variants per window.
    min_samples : int
        Minimum samples with data in window.
    """

    model_config = ConfigDict(frozen=True)

    size: int = Field(default=100_000, ge=1000, le=100_000_000, description="Window size (bp)")
    step: int | None = Field(default=None, ge=1000, description="Step size (bp)")
    min_variants: int = Field(default=10, ge=1, description="Minimum variants per window")
    min_samples: int = Field(default=1, ge=1, description="Minimum samples per window")

    @model_validator(mode="after")
    def set_default_step(self) -> WindowConfig:
        """Set step to size if not specified (non-overlapping windows)."""
        if self.step is None:
            # Use object.__setattr__ since model is frozen
            object.__setattr__(self, "step", self.size)
        return self


class FilterConfig(BaseModel):
    """Configuration for variant filtering.

    Parameters
    ----------
    min_qual : float
        Minimum variant quality score.
    min_maf : float
        Minimum minor allele frequency.
    max_missing : float
        Maximum proportion of missing genotypes (0-1).
    biallelic_only : bool
        Restrict to biallelic variants.
    snps_only : bool
        Restrict to SNPs (exclude indels).
    """

    model_config = ConfigDict(frozen=True)

    min_qual: float = Field(default=30.0, ge=0, description="Minimum quality score")
    min_maf: float = Field(default=0.01, ge=0, le=0.5, description="Minimum MAF")
    max_missing: float = Field(default=0.2, ge=0, le=1.0, description="Maximum missing rate")
    biallelic_only: bool = Field(default=True, description="Biallelic variants only")
    snps_only: bool = Field(default=False, description="SNPs only")


class HMMConfig(BaseModel):
    """Configuration for Hidden Markov Model parameters.

    Parameters
    ----------
    n_states : int
        Number of hidden states (typically number of founders).
    transition_rate : float
        Per-base probability of haplotype transition (recombination).
    error_rate : float
        Genotyping error rate.
    min_confidence : float
        Minimum posterior probability for haplotype assignment.
    """

    model_config = ConfigDict(frozen=True)

    n_states: int | None = Field(default=None, ge=2, description="Number of hidden states")
    transition_rate: float = Field(
        default=1e-6, ge=1e-10, le=1e-2, description="Transition rate per bp"
    )
    error_rate: float = Field(default=0.01, ge=0, le=0.5, description="Genotyping error rate")
    min_confidence: float = Field(
        default=0.8, ge=0, le=1.0, description="Minimum assignment confidence"
    )


class OutputConfig(BaseModel):
    """Configuration for output files and formats.

    Parameters
    ----------
    directory : Path
        Output directory path.
    prefix : str
        Prefix for output filenames.
    formats : list[str]
        Output formats to generate.
    compress : bool
        Compress output files with gzip.
    """

    model_config = ConfigDict(frozen=True)

    directory: Path = Field(default=Path("phaser_output"), description="Output directory")
    prefix: str = Field(default="phaser", description="Output file prefix")
    formats: list[Literal["tsv", "bed", "json", "vcf"]] = Field(
        default=["tsv", "bed"], description="Output formats"
    )
    compress: bool = Field(default=True, description="Gzip compress outputs")


class LoggingConfig(BaseModel):
    """Configuration for logging.

    Parameters
    ----------
    level : str
        Logging level (DEBUG, INFO, WARNING, ERROR).
    file : Path, optional
        Log file path. None for stderr only.
    format : str
        Log message format string.
    """

    model_config = ConfigDict(frozen=True)

    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO", description="Logging level"
    )
    file: Path | None = Field(default=None, description="Log file path")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )


class PhaserConfig(BaseModel):
    """Main configuration for Phaser analysis.

    Configuration can be loaded from YAML files and overridden programmatically.
    Supports all analysis modes: proportion estimation, painting, and scaffolding.

    Parameters
    ----------
    window : WindowConfig
        Window analysis parameters.
    filter : FilterConfig
        Variant filtering parameters.
    hmm : HMMConfig
        HMM model parameters.
    output : OutputConfig
        Output configuration.
    logging : LoggingConfig
        Logging configuration.
    ploidy : int
        Default sample ploidy.
    n_threads : int
        Number of threads for parallel operations.
    random_seed : int, optional
        Random seed for reproducibility.

    Examples
    --------
    >>> config = PhaserConfig()  # Use defaults
    >>> config = PhaserConfig(window=WindowConfig(size=50000))
    >>> config = load_config("analysis.yaml")
    """

    model_config = ConfigDict(frozen=True, validate_assignment=True)

    window: WindowConfig = Field(default_factory=WindowConfig, description="Window parameters")
    filter: FilterConfig = Field(default_factory=FilterConfig, description="Filter parameters")
    hmm: HMMConfig = Field(default_factory=HMMConfig, description="HMM parameters")
    output: OutputConfig = Field(default_factory=OutputConfig, description="Output configuration")
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )
    ploidy: int = Field(default=2, ge=1, le=16, description="Default ploidy")
    n_threads: int = Field(default=1, ge=1, le=128, description="Number of threads")
    random_seed: int | None = Field(default=None, ge=0, description="Random seed")

    def to_yaml(self, path: Path | str) -> None:
        """Write configuration to YAML file.

        Parameters
        ----------
        path : Path or str
            Output file path.
        """
        path = Path(path)
        data = self.model_dump(mode="json")
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
        logger.info(f"Configuration written to {path}")

    def with_updates(self, **kwargs: Any) -> PhaserConfig:
        """Return a new config with specified fields updated.

        Parameters
        ----------
        **kwargs
            Fields to update. Nested fields can be passed as dicts.

        Returns
        -------
        PhaserConfig
            New configuration instance with updates applied.

        Examples
        --------
        >>> new_config = config.with_updates(ploidy=4, n_threads=8)
        >>> new_config = config.with_updates(window={"size": 50000})
        """
        current = self.model_dump()

        for key, value in kwargs.items():
            if isinstance(value, dict) and key in current and isinstance(current[key], dict):
                current[key].update(value)
            else:
                current[key] = value

        return PhaserConfig.model_validate(current)

    def setup_logging(self) -> None:
        """Configure logging based on config settings."""
        handlers: list[logging.Handler] = [logging.StreamHandler()]

        if self.logging.file is not None:
            self.logging.file.parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(self.logging.file))

        logging.basicConfig(
            level=getattr(logging, self.logging.level),
            format=self.logging.format,
            handlers=handlers,
            force=True,
        )
        logger.info(f"Logging configured at {self.logging.level} level")


def load_config(path: Path | str) -> PhaserConfig:
    """Load configuration from YAML file.

    Parameters
    ----------
    path : Path or str
        Path to YAML configuration file.

    Returns
    -------
    PhaserConfig
        Validated configuration instance.

    Raises
    ------
    FileNotFoundError
        If config file doesn't exist.
    ValueError
        If config file is invalid.

    Examples
    --------
    >>> config = load_config("analysis.yaml")
    >>> config = load_config(Path("configs/default.yaml"))
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")

    logger.info(f"Loading configuration from {path}")

    with open(path) as f:
        data = yaml.safe_load(f)

    if data is None:
        data = {}

    return PhaserConfig.model_validate(data)


def load_config_with_overrides(
    path: Path | str | None = None,
    overrides: dict[str, Any] | None = None,
    env_prefix: str = "PHASER_",
) -> PhaserConfig:
    """Load configuration with optional file and overrides.

    Priority (highest to lowest):
    1. Explicit overrides dict
    2. Environment variables
    3. Config file
    4. Defaults

    Parameters
    ----------
    path : Path or str, optional
        Path to YAML configuration file.
    overrides : dict, optional
        Explicit configuration overrides.
    env_prefix : str
        Prefix for environment variables.

    Returns
    -------
    PhaserConfig
        Merged configuration instance.

    Examples
    --------
    >>> config = load_config_with_overrides(
    ...     "analysis.yaml",
    ...     overrides={"n_threads": 8},
    ... )
    """
    config = load_config(path) if path is not None else PhaserConfig()

    # Apply environment variables
    env_overrides: dict[str, Any] = {}

    env_mapping = {
        f"{env_prefix}PLOIDY": ("ploidy", int),
        f"{env_prefix}N_THREADS": ("n_threads", int),
        f"{env_prefix}RANDOM_SEED": ("random_seed", int),
        f"{env_prefix}LOG_LEVEL": ("logging", lambda x: {"level": x}),
        f"{env_prefix}OUTPUT_DIR": ("output", lambda x: {"directory": x}),
    }

    for env_var, (key, converter) in env_mapping.items():
        value = os.environ.get(env_var)
        if value is not None:
            try:
                env_overrides[key] = converter(value)
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid value for {env_var}: {value} ({e})")

    if env_overrides:
        config = config.with_updates(**env_overrides)

    # Apply explicit overrides
    if overrides:
        config = config.with_updates(**overrides)

    return config


def get_default_config() -> PhaserConfig:
    """Return default configuration.

    Returns
    -------
    PhaserConfig
        Configuration with all default values.
    """
    return PhaserConfig()


# Example configuration template as YAML string
CONFIG_TEMPLATE = """\
# Phaser Configuration File
# See documentation for full parameter descriptions

# Window analysis parameters
window:
  size: 100000        # Window size in base pairs
  step: null          # Step size (null = same as size, non-overlapping)
  min_variants: 10    # Minimum informative variants per window
  min_samples: 1      # Minimum samples with data

# Variant filtering
filter:
  min_qual: 30.0      # Minimum variant quality
  min_maf: 0.01       # Minimum minor allele frequency
  max_missing: 0.2    # Maximum missing genotype rate
  biallelic_only: true
  snps_only: false

# Hidden Markov Model parameters
hmm:
  n_states: null      # Number of founder states (auto-detected if null)
  transition_rate: 1.0e-6  # Per-bp transition probability
  error_rate: 0.01    # Genotyping error rate
  min_confidence: 0.8 # Minimum assignment confidence

# Output settings
output:
  directory: phaser_output
  prefix: phaser
  formats:
    - tsv
    - bed
  compress: true

# Logging
logging:
  level: INFO
  file: null          # Log file (null = stderr only)

# General settings
ploidy: 2             # Default sample ploidy
n_threads: 1          # Parallel threads
random_seed: null     # Random seed (null = random)
"""


def write_config_template(path: Path | str) -> None:
    """Write example configuration file.

    Parameters
    ----------
    path : Path or str
        Output file path.
    """
    path = Path(path)
    path.write_text(CONFIG_TEMPLATE)
    logger.info(f"Configuration template written to {path}")
