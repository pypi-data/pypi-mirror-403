from pathlib import Path

import pytest
from pydantic import ValidationError

from pullapprove.config import ConfigModel, ConfigModels
from pullapprove.matches import match_diff


def test_empty_configs():
    configs = ConfigModels.from_configs_data({"CODEREVIEW.toml": {}})
    assert bool(configs)
    assert "CODEREVIEW.toml" in configs
    assert not configs["CODEREVIEW.toml"].template


def test_angular_diff(snapshot):
    cfg = ConfigModel.from_filesystem(Path(__file__).parent / "config.toml")
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": cfg})
    diff = (Path(__file__).parent / "test.diff").read_text()
    diff_results = match_diff(configs, diff)
    assert not diff_results.config_paths_modified
    assert (
        diff_results.additions == 2975
    )  # Expected number of additions (matches diffstat)
    assert (
        diff_results.deletions == 8512
    )  # Expected number of deletions (matches diffstat)
    assert snapshot("angular.json") == diff_results.matches.model_dump()


class TestReviewersForRequireValidation:
    """Test the validate_reviewers_for_require model validator."""

    def test_empty_reviewers_with_require_raises(self):
        """Empty reviewers with require > 0 should raise ValidationError."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": [],
                    "require": 1,
                }
            ]
        }
        with pytest.raises(
            ValidationError,
            match="has require=1 but only 0 reviewers/alternates specified",
        ):
            ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))

    def test_insufficient_reviewers_raises(self):
        """Fewer reviewers than require should raise ValidationError."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["alice"],
                    "require": 2,
                }
            ]
        }
        with pytest.raises(
            ValidationError,
            match="has require=2 but only 1 reviewers/alternates specified",
        ):
            ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))

    def test_alternates_count_toward_total(self):
        """Alternates should count toward the reviewer total."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["alice"],
                    "alternates": ["bob"],
                    "require": 2,
                }
            ]
        }
        # Should not raise - 1 reviewer + 1 alternate = 2, which meets require=2
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].require == 2

    def test_wildcard_skips_validation(self):
        """Wildcard in reviewers should skip validation."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["*"],
                    "require": 5,
                }
            ]
        }
        # Should not raise - wildcard means anyone can review
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].require == 5

    def test_wildcard_in_alternates_skips_validation(self):
        """Wildcard in alternates should skip validation."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": [],
                    "alternates": ["*"],
                    "require": 5,
                }
            ]
        }
        # Should not raise - wildcard in alternates
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].require == 5

    def test_alias_skips_validation(self):
        """Unexpanded aliases should skip validation (will validate after expansion)."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["$team"],
                    "require": 5,
                }
            ]
        }
        # Should not raise - alias not yet expanded
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].require == 5

    def test_alias_in_alternates_skips_validation(self):
        """Unexpanded aliases in alternates should skip validation."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": [],
                    "alternates": ["$team"],
                    "require": 5,
                }
            ]
        }
        # Should not raise - alias not yet expanded
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].require == 5

    def test_zero_require_passes(self):
        """require=0 with no reviewers should pass."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": [],
                    "require": 0,
                }
            ]
        }
        # Should not raise - require=0 means no approvals needed
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].require == 0

    def test_valid_config_passes(self):
        """Valid config with enough reviewers should pass."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["alice", "bob", "carol"],
                    "require": 2,
                }
            ]
        }
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].require == 2

    def test_validation_after_alias_expansion(self):
        """Validation should catch issues after aliases are expanded."""
        config_data = {
            "aliases": {
                "small_team": ["alice"],
            },
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["$small_team"],
                    "require": 3,
                }
            ],
        }
        # Initial parse should pass (alias not expanded)
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        configs = ConfigModels.from_config_models({"CODEREVIEW.toml": config})

        # After compilation (alias expansion), should raise
        with pytest.raises(
            ValidationError,
            match="has require=3 but only 1 reviewers/alternates specified",
        ):
            config.compiled_config(Path("CODEREVIEW.toml"), configs)


class TestChecklistReviewedForValidation:
    """Test that checklist and reviewed_for='required' cannot be used together."""

    def test_checklist_with_reviewed_for_required_raises(self):
        """Checklist with reviewed_for='required' should raise ValidationError."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["alice"],
                    "reviewed_for": "required",
                    "checklist": {
                        "items": [{"label": "I reviewed the code"}],
                    },
                }
            ]
        }
        with pytest.raises(
            ValidationError,
            match="checklist and reviewed_for='required' cannot be used together",
        ):
            ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))

    def test_checklist_with_reviewed_for_ignored_passes(self):
        """Checklist with reviewed_for='ignored' should pass."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["alice"],
                    "reviewed_for": "ignored",
                    "checklist": {
                        "items": [{"label": "I reviewed the code"}],
                    },
                }
            ]
        }
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].checklist is not None

    def test_checklist_without_reviewed_for_passes(self):
        """Checklist without reviewed_for should pass."""
        config_data = {
            "scopes": [
                {
                    "name": "test",
                    "paths": ["*"],
                    "reviewers": ["alice"],
                    "checklist": {
                        "items": [{"label": "I reviewed the code"}],
                    },
                }
            ]
        }
        config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
        assert config.scopes[0].checklist is not None
