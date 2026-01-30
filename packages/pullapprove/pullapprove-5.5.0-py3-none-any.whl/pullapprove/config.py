from __future__ import annotations

import re
import tomllib
from collections.abc import Generator
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    RootModel,
    field_validator,
    model_validator,
)
from wcmatch import glob

from .checklists import Checklist

CONFIG_FILENAME_PREFIX = "CODEREVIEW"
CONFIG_FILENAME = "CODEREVIEW.toml"


def _expand_aliases(
    values: list[str],
    aliases: dict[str, list[str]],
    _seen: set[str] | None = None,
    _path: list[str] | None = None,
) -> list[str]:
    """Replace alias references in a list with their mapped values recursively."""
    if _seen is None:
        _seen = set()
    if _path is None:
        _path = []

    expanded: list[str] = []
    for value in values:
        if isinstance(value, str) and value.startswith("$"):
            alias_name = value[1:]
            if alias_name in _seen:
                # Cycle detected, raise an error with the cycle path
                cycle_path = _path[_path.index(alias_name) :] + [alias_name]
                raise ValueError(
                    f"Circular reference detected in aliases: {' -> '.join(cycle_path)}"
                )
            if alias_name in aliases:
                _seen.add(alias_name)
                _path.append(alias_name)
                # Recursively expand the alias values
                nested_expanded = _expand_aliases(
                    aliases[alias_name], aliases, _seen, _path
                )
                expanded.extend(nested_expanded)
                _path.pop()
                _seen.remove(alias_name)
        else:
            expanded.append(value)

    # Remove duplicates while preserving order
    return list(dict.fromkeys(expanded))


class ReviewedForChoices(str, Enum):
    EMPTY = ""
    REQUIRED = "required"
    IGNORED = "ignored"


class OwnershipChoices(str, Enum):
    EMPTY = ""
    APPEND = "append"
    GLOBAL = "global"


class ScopeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Required fields
    name: str = Field(min_length=1)
    paths: list[str] = Field(min_length=1)

    # Optional fields

    # Expanded version of lines could be dict
    # with fnmatch, regex, exclude patterns, etc?
    code: list[str] = []

    # This only filtering field that can't be used with raw diff/files...
    # If we get into that, the others are:
    # - labels
    # - ref (have branches at the root level...)
    # - statuses
    # - dates
    # - body
    # - title
    # - other scopes
    # (this is how I ended up with expressions...
    # I'm not trying to build a general purpose workflow tool,
    # but I do need to support the legit use cases and AI/bot review is one, so is team hierarchy)
    authors: list[str] = []

    # (defaults should be the "empty" values)
    description: str = ""
    reviewers: list[str] = []
    alternates: list[str] = []
    cc: list[str] = []

    # Review scoring
    require: int = 0
    reviewed_for: ReviewedForChoices = ReviewedForChoices.EMPTY
    author_value: int = 0

    # How scopes are combined
    ownership: OwnershipChoices = OwnershipChoices.EMPTY

    # Actionable items
    request: int = 0
    labels: list[str] = []
    instructions: str = ""

    # Approval checklist
    checklist: Checklist | None = None

    @model_validator(mode="after")
    def validate_reviewers_for_require(self) -> ScopeModel:
        all_reviewers = self.reviewers + self.alternates

        # Skip if wildcard - anyone can review
        if "*" in all_reviewers:
            return self

        # Skip if aliases not yet expanded (will validate again after compilation)
        if any(r.startswith("$") for r in all_reviewers):
            return self

        if len(all_reviewers) < self.require:
            raise ValueError(
                f"has require={self.require} but only {len(all_reviewers)} reviewers/alternates specified"
            )
        return self

    @model_validator(mode="after")
    def validate_checklist_reviewed_for(self) -> ScopeModel:
        if self.checklist and self.reviewed_for == ReviewedForChoices.REQUIRED:
            raise ValueError(
                "checklist and reviewed_for='required' cannot be used together. "
                "The checklist already requires explicit scope acknowledgment."
            )
        return self

    def printed_name(self) -> str:
        match self.ownership:
            case OwnershipChoices.APPEND:
                return "+" + self.name
            case OwnershipChoices.GLOBAL:
                return "*" + self.name

        return self.name

    def __eq__(self, other: Any) -> bool:
        return self.name == other.name

    def matches_path(self, path: Path) -> bool:
        # TODO paths shouldn't start with /
        return glob.globmatch(
            path,
            self.paths,
            flags=glob.GLOBSTAR
            | glob.BRACE
            | glob.NEGATE
            | glob.IGNORECASE
            | glob.DOTGLOB,
        )

    def matches_code(self, code: str) -> Generator[dict[str, int], None, None]:
        patterns = getattr(self, "_line_regex_patterns", [])
        if not patterns:
            patterns = [re.compile(pattern, re.MULTILINE) for pattern in self.code]
            self._code_regex_patterns = patterns  # Cache the compiled patterns

        for pattern in patterns:
            for match in pattern.finditer(code):
                start_index = match.start()
                end_index = match.end()

                start_line = code.count("\n", 0, start_index) + 1
                start_col = start_index - code.rfind("\n", 0, start_index)

                end_line = code.count("\n", 0, end_index) + 1
                end_col = end_index - code.rfind("\n", 0, end_index)

                yield {
                    "start_line": start_line,
                    "start_col": start_col,
                    "end_line": end_line,
                    "end_col": end_col,
                }

    def matches_author(self, author_username: str) -> bool:
        if not self.authors:
            # No authors specified, so assume it matches
            return True

        negated_authors = [a[1:] for a in self.authors if a.startswith("!")]
        authors = [a for a in self.authors if not a.startswith("!")]

        if author_username in negated_authors:
            # If the author is in the negated list, return False
            return False

        if author_username in authors:
            # If the author is in the authors list, return True
            return True

        return False

    def enabled_for_pullrequest(self, author_username: str) -> bool:
        # Paths/code are matched during diff parsing,
        # but we also consider authors in the context of a pull request so do that here.
        return self.matches_author(author_username)


class LargeScaleChangeModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Note, an LSC only applies to diffs, not raw files,
    # because we have to know what *changed*.

    # Pretty similar to a scope, but more manual.
    # There has to be at least one reviewer. So if a LSC config is not defined, an LSC PR error until you add one.
    require: int = 1
    reviewers: list[str] = []  # Field(min_length=1)
    # min_paths: int = 300
    # min_lines: int = 3000
    labels: list[str] = []
    # really need author value too...?


class ConfigModel(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # Nothing is technically required
    extends: list[str] = []
    template: bool = False
    branches: list[str] = []
    aliases: dict[str, list[str]] = {}
    large_scale_change: LargeScaleChangeModel | None = None
    scopes: list[ScopeModel] = []

    @field_validator("scopes", mode="after")
    @classmethod
    def validate_unique_scope_names(cls, scopes: list[ScopeModel]) -> list[ScopeModel]:
        seen: set[str] = set()
        for scope in scopes:
            if scope.name in seen:
                raise ValueError(f"Duplicate scope name: {scope.name}")
            seen.add(scope.name)

        return scopes

    @field_validator("extends", mode="before")
    @classmethod
    def validate_extends(cls, extends: list[str]) -> list[str]:
        for i, path in enumerate(extends):
            basename = Path(path).name
            if not basename.startswith(CONFIG_FILENAME_PREFIX):
                raise ValueError(
                    f"Invalid extends path: {path}. It should start with '{CONFIG_FILENAME_PREFIX}'."
                )
        return extends

    def compiled_config(
        self, config_path: Path, other_configs: ConfigModels
    ) -> ConfigModel:
        """
        Merge extends, replace aliases.
        """

        if getattr(self, "_compiled_config", None) is not None:
            return self._compiled_config

        # Create a copy of the data from what we have currently
        compiled_data = self.model_dump()

        for extend_path in self.extends:
            if extend_path not in other_configs:
                raise ValueError(f"Config {extend_path} not found")

            extended_config = other_configs[extend_path]
            extended_config.compiled_config(Path(extend_path), other_configs)

            extended_config_dumped = extended_config.model_dump(
                include={"branches", "aliases", "scopes", "large_scale_change"}
            )

            compiled_data["scopes"] = (
                extended_config_dumped["scopes"] + compiled_data["scopes"]
            )
            compiled_data["large_scale_change"] = (
                compiled_data["large_scale_change"]
                or extended_config_dumped["large_scale_change"]
            )
            compiled_data["aliases"] = (
                extended_config_dumped["aliases"] | compiled_data["aliases"]
            )
            compiled_data["branches"] = (
                extended_config_dumped["branches"] + compiled_data["branches"]
            )

        # Root aliases
        for field in ["extends", "branches"]:
            if field in compiled_data:
                compiled_data[field] = _expand_aliases(
                    compiled_data[field], compiled_data["aliases"]
                )

        # Expand aliases for any aliasable list fields
        for scope in compiled_data["scopes"]:
            for field in [
                "paths",
                "code",
                "authors",
                "reviewers",
                "alternates",
                "cc",
                "labels",
            ]:
                if field in scope:
                    scope[field] = _expand_aliases(
                        scope[field], compiled_data["aliases"]
                    )

        if large_scale_change := compiled_data.get("large_scale_change"):
            for field in ["reviewers", "labels"]:
                large_scale_change[field] = _expand_aliases(
                    large_scale_change[field],
                    compiled_data["aliases"],
                )

        # Create a new config from the merged data
        self._compiled_config = ConfigModel.from_data(
            data=compiled_data,
            path=config_path,
        )

        return self._compiled_config

    @classmethod
    def from_filesystem(cls, path: Path | str) -> ConfigModel:
        with open(path, "rb") as f:
            return cls.from_data(tomllib.load(f), path)

    @classmethod
    def from_content(cls, content: str, path: Path | str) -> ConfigModel:
        return cls.from_data(tomllib.loads(content), path)

    @classmethod
    def from_data(cls, data: dict[str, Any], path: Path | str) -> ConfigModel:
        # config = cls(path)

        # config.data = data
        # config = ConfigModel(**config.data)

        return cls(**data)

    def matches_branches(self, base_branch: str, head_branch: str) -> bool:
        if not self.branches:
            # No branches specified, so assume it matches
            return True

        for pattern in self.branches:
            splitter = "..." if "..." in pattern else ".."
            parts = pattern.split(splitter)
            base_pattern = parts[0]
            head_pattern = parts[1] if len(parts) > 1 else None

            base_match = (
                glob.globmatch(base_branch, base_pattern) if base_pattern else True
            )
            head_match = (
                glob.globmatch(head_branch, head_pattern) if head_pattern else True
            )

            if base_match and head_match:
                return True

        return False

    def enabled_for_pullrequest(self, base_branch: str, head_branch: str) -> bool:
        return self.matches_branches(base_branch, head_branch)

    # Kinda want the original toml if you dump? with comments etc
    # def as_toml(self) -> str:
    #     """
    #     Convert the config to a TOML string.
    #     """
    #     return tomllib.dumps(self.model_dump())

    # def matches_branch(self, base_branch: str, head_branch: str) -> bool:
    #     for pattern in self.branches:
    #         splitter = "..." if "..." in pattern else ".."
    #         parts = pattern.split(splitter)
    #         base_pattern = parts[0]
    #         head_pattern = parts[1] if len(parts) > 1 else None

    #         base_match = fnmatch.fnmatch(base_branch, base_pattern) if base_pattern else True
    #         head_match = fnmatch.fnmatch(head_branch, head_pattern) if head_pattern else True

    #         if base_match and head_match:
    #             return True

    #     return False


class ConfigModels(RootModel):
    root: dict[str, ConfigModel]

    # def __init__(self, configs: dict[str, CodeReviewConfig] = None):
    #     if configs is None:
    #         configs = {}
    #     self = configs

    # def __repr__(self):
    #     return f"CodeReviewConfigs({self})"

    @classmethod
    def from_configs_data(cls, data: dict[str, Any]) -> ConfigModels:
        """Load configs from a dict of data"""
        configs = cls(root={})

        for path, config_data in data.items():
            config = ConfigModel.from_data(config_data, Path(path))
            configs.add_config(config, Path(path))

        return configs

    @classmethod
    def from_config_models(cls, models: dict[str, ConfigModel]) -> ConfigModels:
        """Load configs from a dict of models"""
        configs = cls(root={})

        for path, config_model in models.items():
            # config = ConfigModel.from_model(config_model, Path(path))
            configs.add_config(config_model, Path(path))

        return configs

    def get_config_models(self) -> dict[str, ConfigModel]:
        return dict(self.root.items())

    def add_config(self, config: ConfigModel, path: Path) -> None:
        self.root[str(path)] = config

    def get_default_large_scale_change(self) -> LargeScaleChangeModel:
        """Get the root config, which is the first one found in the list"""
        primary_config = CONFIG_FILENAME

        if primary_config in self.root:
            if lsc := self.root[primary_config].large_scale_change:
                return lsc

        return LargeScaleChangeModel()

    def __bool__(self) -> bool:
        return bool(self.root)

    def __getitem__(self, key: str) -> ConfigModel:
        return self.root[key]

    def __contains__(self, key: str) -> bool:
        return key in self.root

    def __len__(self) -> int:
        return len(self.root)

    def compile_closest_config(self, file_path: Path) -> ConfigModel:
        """Find the closest config file to this file"""
        for parent in file_path.parents:
            parent_config_path = str(parent / CONFIG_FILENAME)

            if parent_config_path in self.root:
                config = self.root[parent_config_path]

                if config.template:
                    # Skip templates
                    continue

                compiled = config.compiled_config(Path(parent_config_path), self)

                return compiled

        raise ValueError(f"No config found for {file_path}")

    def iter_compiled_configs(self) -> Generator[tuple[str, ConfigModel], None, None]:
        for config_path, config in self.root.items():
            if config.template:
                # Skip templates
                continue

            yield config_path, config.compiled_config(Path(config_path), self)

    def num_scopes(self) -> int:
        """
        Count the total number of scopes across all configs.
        """
        return sum(len(config.scopes) for config in self.root.values())

    def num_reviewers(self) -> int:
        """
        Count the total number of reviewers across all configs.
        """
        return sum(
            len(scope.reviewers)
            for config in self.root.values()
            for scope in config.scopes
        )

    def filter_for_pullrequest(
        self,
        base_branch: str,
        head_branch: str,
        author_username: str,
    ) -> ConfigModels:
        """
        Look at all configs (including templates) and filter out
        configs and scopes based on branches, authors, etc.
        """
        filtered_configs = {}

        for config_path, config in self.root.items():
            compiled_config = config.compiled_config(Path(config_path), self)

            if not compiled_config.enabled_for_pullrequest(base_branch, head_branch):
                # Remove the config from the list
                continue

            # Collect the names of scopes to remove
            scopes_to_remove = set()
            for scope in compiled_config.scopes:
                if not scope.enabled_for_pullrequest(author_username):
                    scopes_to_remove.add(scope.name)

            # Create a filtered copy of the config data
            filtered_config_data = config.model_dump()

            # Filter scopes in a simple, declarative way
            if "scopes" in filtered_config_data:
                filtered_config_data["scopes"] = [
                    scope
                    for scope in filtered_config_data["scopes"]
                    if scope["name"] not in scopes_to_remove
                ]

            # Rebuild using the origial/modified raw data
            filtered_configs[config_path] = filtered_config_data

        return ConfigModels.from_configs_data(filtered_configs)

        # for config in configs.iter_compiled_configs():
        #     if config.enabled_for_pullrequest(self):
        #         filtered_configs.add_config(config)

        #         # Paths/code are similar, but we need to iterate the diff to process them,
        #         # so this is almost a pre-process for metadata of the PR
        #         scopes_to_remove = []
        #         for scope in config.scopes:
        #             if not scope.enabled_for_pullrequest(self):
        #                 scopes_to_remove.append(scope)
        #         for scope in scopes_to_remove:
        #             config.scopes.remove(scope)
