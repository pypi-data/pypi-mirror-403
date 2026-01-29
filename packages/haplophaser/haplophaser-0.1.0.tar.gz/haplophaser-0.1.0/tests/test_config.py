"""Tests for configuration system."""

from __future__ import annotations

from pathlib import Path

import pytest

from haplophaser.core.config import (
    CONFIG_TEMPLATE,
    FilterConfig,
    HMMConfig,
    LoggingConfig,
    OutputConfig,
    PhaserConfig,
    WindowConfig,
    get_default_config,
    load_config,
    load_config_with_overrides,
    write_config_template,
)


class TestWindowConfig:
    """Tests for WindowConfig."""

    def test_default_values(self) -> None:
        """Test default window configuration."""
        cfg = WindowConfig()
        assert cfg.size == 100_000
        assert cfg.step == 100_000  # Defaults to size
        assert cfg.min_variants == 10
        assert cfg.min_samples == 1

    def test_custom_values(self) -> None:
        """Test custom window configuration."""
        cfg = WindowConfig(size=50_000, step=25_000, min_variants=5)
        assert cfg.size == 50_000
        assert cfg.step == 25_000
        assert cfg.min_variants == 5

    def test_step_defaults_to_size(self) -> None:
        """Test that step defaults to window size if not specified."""
        cfg = WindowConfig(size=75_000)
        assert cfg.step == 75_000

    def test_validation(self) -> None:
        """Test validation constraints."""
        with pytest.raises(ValueError):
            WindowConfig(size=100)  # Below minimum

        with pytest.raises(ValueError):
            WindowConfig(min_variants=0)  # Below minimum


class TestFilterConfig:
    """Tests for FilterConfig."""

    def test_default_values(self) -> None:
        """Test default filter configuration."""
        cfg = FilterConfig()
        assert cfg.min_qual == 30.0
        assert cfg.min_maf == 0.01
        assert cfg.max_missing == 0.2
        assert cfg.biallelic_only is True
        assert cfg.snps_only is False

    def test_validation(self) -> None:
        """Test validation constraints."""
        with pytest.raises(ValueError):
            FilterConfig(min_maf=0.6)  # Above 0.5

        with pytest.raises(ValueError):
            FilterConfig(max_missing=1.5)  # Above 1.0


class TestHMMConfig:
    """Tests for HMMConfig."""

    def test_default_values(self) -> None:
        """Test default HMM configuration."""
        cfg = HMMConfig()
        assert cfg.n_states is None
        assert cfg.transition_rate == 1e-6
        assert cfg.error_rate == 0.01
        assert cfg.min_confidence == 0.8

    def test_validation(self) -> None:
        """Test validation constraints."""
        with pytest.raises(ValueError):
            HMMConfig(n_states=1)  # Minimum 2

        with pytest.raises(ValueError):
            HMMConfig(error_rate=0.6)  # Above 0.5


class TestOutputConfig:
    """Tests for OutputConfig."""

    def test_default_values(self) -> None:
        """Test default output configuration."""
        cfg = OutputConfig()
        assert cfg.directory == Path("phaser_output")
        assert cfg.prefix == "phaser"
        assert "tsv" in cfg.formats
        assert cfg.compress is True

    def test_formats_validation(self) -> None:
        """Test that only valid formats are accepted."""
        cfg = OutputConfig(formats=["bed", "json"])
        assert cfg.formats == ["bed", "json"]


class TestLoggingConfig:
    """Tests for LoggingConfig."""

    def test_default_values(self) -> None:
        """Test default logging configuration."""
        cfg = LoggingConfig()
        assert cfg.level == "INFO"
        assert cfg.file is None

    def test_valid_levels(self) -> None:
        """Test all valid logging levels."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR"]:
            cfg = LoggingConfig(level=level)
            assert cfg.level == level


class TestPhaserConfig:
    """Tests for main PhaserConfig."""

    def test_default_config(self, default_config: PhaserConfig) -> None:
        """Test default configuration creation."""
        assert default_config.ploidy == 2
        assert default_config.n_threads == 1
        assert default_config.random_seed is None
        assert isinstance(default_config.window, WindowConfig)
        assert isinstance(default_config.filter, FilterConfig)

    def test_custom_config(self, custom_config: PhaserConfig) -> None:
        """Test custom configuration."""
        assert custom_config.ploidy == 4
        assert custom_config.n_threads == 4
        assert custom_config.window.size == 50_000
        assert custom_config.filter.min_qual == 20.0

    def test_nested_config_dict(self) -> None:
        """Test nested configuration from dict."""
        cfg = PhaserConfig(
            window={"size": 25_000, "min_variants": 3},
            filter={"min_qual": 15.0},
        )
        assert cfg.window.size == 25_000
        assert cfg.window.min_variants == 3
        assert cfg.filter.min_qual == 15.0

    def test_with_updates(self, default_config: PhaserConfig) -> None:
        """Test configuration update method."""
        updated = default_config.with_updates(ploidy=4, n_threads=8)
        assert updated.ploidy == 4
        assert updated.n_threads == 8
        # Original unchanged
        assert default_config.ploidy == 2

    def test_with_nested_updates(self, default_config: PhaserConfig) -> None:
        """Test nested configuration updates."""
        updated = default_config.with_updates(window={"size": 50_000})
        assert updated.window.size == 50_000
        # Other window defaults preserved
        assert updated.window.min_variants == 10

    def test_immutable(self, default_config: PhaserConfig) -> None:
        """Test that config is frozen/immutable."""
        with pytest.raises(Exception):
            default_config.ploidy = 4


class TestConfigIO:
    """Tests for configuration file I/O."""

    def test_load_config(self, tmp_config_yaml: Path) -> None:
        """Test loading configuration from YAML file."""
        cfg = load_config(tmp_config_yaml)
        assert cfg.window.size == 50_000
        assert cfg.window.min_variants == 5
        assert cfg.filter.min_qual == 20.0
        assert cfg.ploidy == 4

    def test_load_missing_file(self, tmp_path: Path) -> None:
        """Test error on missing file."""
        with pytest.raises(FileNotFoundError):
            load_config(tmp_path / "nonexistent.yaml")

    def test_save_and_load_config(self, tmp_path: Path, custom_config: PhaserConfig) -> None:
        """Test round-trip save and load."""
        path = tmp_path / "saved_config.yaml"
        custom_config.to_yaml(path)

        loaded = load_config(path)
        assert loaded.ploidy == custom_config.ploidy
        assert loaded.window.size == custom_config.window.size

    def test_write_config_template(self, tmp_path: Path) -> None:
        """Test writing configuration template."""
        path = tmp_path / "template.yaml"
        write_config_template(path)

        assert path.exists()
        content = path.read_text()
        assert "window:" in content
        assert "filter:" in content

    def test_load_empty_config(self, tmp_path: Path) -> None:
        """Test loading empty YAML file uses defaults."""
        path = tmp_path / "empty.yaml"
        path.write_text("")

        cfg = load_config(path)
        assert cfg.ploidy == 2  # Default value

    def test_load_partial_config(self, tmp_path: Path) -> None:
        """Test loading partial config merges with defaults."""
        path = tmp_path / "partial.yaml"
        path.write_text("ploidy: 4\n")

        cfg = load_config(path)
        assert cfg.ploidy == 4
        assert cfg.n_threads == 1  # Default


class TestConfigWithOverrides:
    """Tests for load_config_with_overrides."""

    def test_no_file_uses_defaults(self) -> None:
        """Test that missing file uses defaults."""
        cfg = load_config_with_overrides(path=None)
        assert cfg.ploidy == 2

    def test_overrides_applied(self) -> None:
        """Test explicit overrides are applied."""
        cfg = load_config_with_overrides(
            path=None,
            overrides={"ploidy": 6, "n_threads": 4},
        )
        assert cfg.ploidy == 6
        assert cfg.n_threads == 4

    def test_overrides_with_file(self, tmp_config_yaml: Path) -> None:
        """Test overrides take precedence over file."""
        cfg = load_config_with_overrides(
            path=tmp_config_yaml,
            overrides={"ploidy": 8},
        )
        # Override wins over file value (4)
        assert cfg.ploidy == 8
        # File value preserved where not overridden
        assert cfg.window.size == 50_000

    def test_nested_overrides(self) -> None:
        """Test nested dictionary overrides."""
        cfg = load_config_with_overrides(
            path=None,
            overrides={"window": {"size": 25_000}},
        )
        assert cfg.window.size == 25_000


class TestGetDefaultConfig:
    """Tests for get_default_config convenience function."""

    def test_returns_defaults(self) -> None:
        """Test that default config is returned."""
        cfg = get_default_config()
        assert isinstance(cfg, PhaserConfig)
        assert cfg.ploidy == 2

    def test_returns_new_instance(self) -> None:
        """Test that each call returns a new instance."""
        cfg1 = get_default_config()
        cfg2 = get_default_config()
        # Should be equal but not same object
        assert cfg1 == cfg2


class TestConfigTemplate:
    """Tests for CONFIG_TEMPLATE constant."""

    def test_template_is_valid_yaml(self, tmp_path: Path) -> None:
        """Test that template is valid YAML that can be loaded."""
        path = tmp_path / "template.yaml"
        path.write_text(CONFIG_TEMPLATE)

        cfg = load_config(path)
        assert isinstance(cfg, PhaserConfig)

    def test_template_has_all_sections(self) -> None:
        """Test that template includes all config sections."""
        assert "window:" in CONFIG_TEMPLATE
        assert "filter:" in CONFIG_TEMPLATE
        assert "hmm:" in CONFIG_TEMPLATE
        assert "output:" in CONFIG_TEMPLATE
        assert "logging:" in CONFIG_TEMPLATE
