from pathlib import Path

import pytest

from pullapprove.config import ConfigModel, ConfigModels


@pytest.mark.parametrize(
    ("config_data", "expected"),
    [
        (
            {
                "aliases": {
                    "team": ["alice", "bob"],
                    "qa": ["carol"],
                    "extras": ["bob", "dave"],
                },
                "scopes": [
                    {
                        "name": "all",
                        "paths": ["*"],
                        "authors": ["$team", "carol", "$extras", "frank"],
                        "reviewers": ["$qa", "$team", "carol"],
                        "alternates": ["$extras", "grace", "$qa"],
                        "cc": ["$team", "$team", "eve"],
                        "labels": ["$qa", "bug", "bug"],
                    }
                ],
                "large_scale_change": {
                    "reviewers": ["$team", "hank", "$extras"],
                    "labels": ["$qa", "$qa", "feature"],
                },
            },
            {
                "authors": ["alice", "bob", "carol", "dave", "frank"],
                "reviewers": ["carol", "alice", "bob"],
                "alternates": ["bob", "dave", "grace", "carol"],
                "cc": ["alice", "bob", "eve"],
                "labels": ["carol", "bug"],
                "lsc_reviewers": ["alice", "bob", "hank", "dave"],
                "lsc_labels": ["carol", "feature"],
            },
        )
    ],
)
def test_alias_expansion(config_data, expected):
    config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": config})

    compiled = config.compiled_config(Path("CODEREVIEW.toml"), configs)

    scope = compiled.scopes[0]
    assert scope.authors == expected["authors"]
    assert scope.reviewers == expected["reviewers"]
    assert scope.alternates == expected["alternates"]
    assert scope.cc == expected["cc"]
    assert scope.labels == expected["labels"]

    lsc = compiled.large_scale_change
    assert lsc is not None
    assert lsc.reviewers == expected["lsc_reviewers"]
    assert lsc.labels == expected["lsc_labels"]


def test_nested_aliases():
    """Test that aliases can reference other aliases."""
    config_data = {
        "aliases": {
            "backend": ["alice", "bob"],
            "frontend": ["carol", "dave"],
            "qa": ["eve"],
            "all_devs": ["$backend", "$frontend"],
            "everyone": ["$all_devs", "$qa", "frank"],
            "leads": ["alice", "carol"],
            "all_leads": ["$leads", "george"],
        },
        "scopes": [
            {
                "name": "all",
                "paths": ["*"],
                "reviewers": ["$everyone"],
                "alternates": ["$all_leads"],
            }
        ],
    }

    config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": config})
    compiled = config.compiled_config(Path("CODEREVIEW.toml"), configs)

    scope = compiled.scopes[0]
    # everyone = all_devs + qa + frank = backend + frontend + qa + frank
    assert scope.reviewers == ["alice", "bob", "carol", "dave", "eve", "frank"]
    # all_leads = leads + george
    assert scope.alternates == ["alice", "carol", "george"]


def test_circular_alias_detection():
    """Test that circular references in aliases raise an error."""
    config_data = {
        "aliases": {
            "a": ["$b", "alice"],
            "b": ["$c", "bob"],
            "c": ["$a", "carol"],  # Creates a cycle: a -> b -> c -> a
        },
        "scopes": [
            {
                "name": "all",
                "paths": ["*"],
                "reviewers": ["$a"],
            }
        ],
    }

    config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": config})

    with pytest.raises(
        ValueError, match="Circular reference detected in aliases: a -> b -> c -> a"
    ):
        config.compiled_config(Path("CODEREVIEW.toml"), configs)


def test_self_referencing_alias():
    """Test that self-referencing aliases are detected."""
    config_data = {
        "aliases": {
            "self": ["$self", "alice"],
        },
        "scopes": [
            {
                "name": "all",
                "paths": ["*"],
                "reviewers": ["$self"],
            }
        ],
    }

    config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": config})

    with pytest.raises(
        ValueError, match="Circular reference detected in aliases: self -> self"
    ):
        config.compiled_config(Path("CODEREVIEW.toml"), configs)


def test_deeply_nested_aliases():
    """Test multiple levels of alias nesting."""
    config_data = {
        "aliases": {
            "level1": ["alice"],
            "level2": ["$level1", "bob"],
            "level3": ["$level2", "carol"],
            "level4": ["$level3", "dave"],
            "level5": ["$level4", "eve"],
        },
        "scopes": [
            {
                "name": "all",
                "paths": ["*"],
                "reviewers": ["$level5"],
            }
        ],
    }

    config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": config})
    compiled = config.compiled_config(Path("CODEREVIEW.toml"), configs)

    scope = compiled.scopes[0]
    assert scope.reviewers == ["alice", "bob", "carol", "dave", "eve"]


def test_mixed_nested_aliases():
    """Test aliases with mix of direct users and other aliases."""
    config_data = {
        "aliases": {
            "core": ["alice", "bob"],
            "extended": ["$core", "carol", "dave"],
            "all": ["$extended", "eve", "$core"],  # Includes duplicates
        },
        "scopes": [
            {
                "name": "all",
                "paths": ["*"],
                "reviewers": ["$all", "alice"],  # More duplicates
            }
        ],
    }

    config = ConfigModel.from_data(config_data, Path("CODEREVIEW.toml"))
    configs = ConfigModels.from_config_models({"CODEREVIEW.toml": config})
    compiled = config.compiled_config(Path("CODEREVIEW.toml"), configs)

    scope = compiled.scopes[0]
    # Should deduplicate while preserving order
    assert scope.reviewers == ["alice", "bob", "carol", "dave", "eve"]


def test_circular_alias_across_extends():
    """Test that circular references across extended configs are detected."""
    # Base config with alias 'a' that references 'b'
    base_config_data = {
        "template": True,
        "aliases": {
            "a": ["$b", "alice"],
        },
    }

    # Extended config that defines 'b' referencing 'a' (creating a cycle)
    extended_config_data = {
        "extends": ["CODEREVIEW.base.toml"],
        "aliases": {
            "b": ["$a", "bob"],
        },
        "scopes": [
            {
                "name": "all",
                "paths": ["*"],
                "reviewers": ["$a"],
            }
        ],
    }

    base_config = ConfigModel.from_data(base_config_data, Path("CODEREVIEW.base.toml"))
    extended_config = ConfigModel.from_data(
        extended_config_data, Path("CODEREVIEW.toml")
    )

    configs = ConfigModels.from_config_models(
        {
            "CODEREVIEW.base.toml": base_config,
            "CODEREVIEW.toml": extended_config,
        }
    )

    with pytest.raises(
        ValueError, match="Circular reference detected in aliases: a -> b -> a"
    ):
        extended_config.compiled_config(Path("CODEREVIEW.toml"), configs)
