"""Provide chaining services for the LPW cinematic pipeline."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

from lpw.config import context_root, runtime_root
from lpw.errors import InvalidContextDataError
from lpw.utils.files import load_yaml
from lpw.utils.hashing import stable_hash
from lpw.utils.identifiers import validate_identifier


class ContextChainError(InvalidContextDataError):
    """Raised when a versioned context chain cannot be resolved safely."""


@dataclass(frozen=True)
class ResolvedContext:
    """Represent ResolvedContext behavior in the LPW pipeline.

    Attributes:
        context (dict[str, Any]): Stored context value.
        chain (list[dict[str, Any]]): Stored chain value.
        context_hash (str): Stored context hash value.
    """
    context: dict[str, Any]
    chain: list[dict[str, Any]]
    context_hash: str


class ContextChainResolver:
    """Resolve pinned cinema:// inheritance without modifying source context."""

    def __init__(
        self,
        source_root: Path | str | None = None,
        state_root: Path | str | None = None,
    ) -> None:
        """Initialize the service with its configured dependencies.

        Args:
            source_root (Path | str | None): Root directory containing immutable source
                context. Defaults to ``None``.
            state_root (Path | str | None): Root directory used for generated runtime
                state. Defaults to ``None``.
        """
        self._source_root = Path(source_root or context_root()).resolve()
        self._state_root = Path(state_root or runtime_root()).resolve()

    def resolve(self, uri: str) -> ResolvedContext:
        """Resolve resolve.

        Args:
            uri (str): Uri used by this operation.

        Returns:
            ResolvedContext: Result produced by the operation.
        """
        context, chain = self._resolve(uri, stack=())
        return ResolvedContext(context, chain, stable_hash(context))

    def compile_document(
        self,
        document: dict[str, Any],
        *,
        source_uri: str,
    ) -> ResolvedContext:
        """Compile document.

        Args:
            document (dict[str, Any]): Structured document to validate, merge, or
                persist.
            source_uri (str): Pinned URI identifying the source context document.

        Returns:
            ResolvedContext: Result produced by the operation.
        """
        context, chain = self._compile_document(
            deepcopy(document), source_uri=source_uri, stack=()
        )
        return ResolvedContext(context, chain, stable_hash(context))

    def _resolve(
        self, uri: str, *, stack: tuple[str, ...]
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Resolve resolve.

        Args:
            uri (str): Uri used by this operation.
            stack (tuple[str, ...]): Stack used by this operation.

        Returns:
            tuple[dict[str, Any], list[dict[str, Any]]]: Result produced by the operation.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        normalized, version = self._parse_pinned_uri(uri)
        if normalized in stack:
            cycle = " -> ".join((*stack, normalized))
            raise ContextChainError(f"Circular context inheritance detected: {cycle}")
        path = self._path_for_uri(normalized)
        document = load_yaml(path)
        actual_version = document.get("version")
        if actual_version != version:
            raise ContextChainError(
                f"Context '{normalized}' requested version {version}, "
                f"but '{path}' contains version {actual_version!r}."
            )
        return self._compile_document(
            document,
            source_uri=f"{normalized}@{version}",
            stack=(*stack, normalized),
        )

    def _compile_document(
        self,
        document: dict[str, Any],
        *,
        source_uri: str,
        stack: tuple[str, ...],
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Compile document.

        Args:
            document (dict[str, Any]): Structured document to validate, merge, or
                persist.
            source_uri (str): Pinned URI identifying the source context document.
            stack (tuple[str, ...]): Stack used by this operation.

        Returns:
            tuple[dict[str, Any], list[dict[str, Any]]]: Result produced by the operation.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        compiled: dict[str, Any] = {}
        chain: list[dict[str, Any]] = []
        immutable_paths: list[str] = []
        for parent_uri in self._string_list(document.get("extends", []), "extends"):
            parent, parent_chain = self._resolve(parent_uri, stack=stack)
            immutable_paths = self._immutable_paths(compiled, parent)
            compiled = self._merge(compiled, parent)
            chain.extend(parent_chain)

        imports = document.get("imports", {})
        if imports:
            if not isinstance(imports, dict):
                raise ContextChainError("imports must be an object of URI lists.")
            for namespace, values in imports.items():
                imported = []
                for import_uri in self._string_list(values, f"imports.{namespace}"):
                    value, imported_chain = self._resolve(import_uri, stack=stack)
                    imported.append(value)
                    chain.extend(imported_chain)
                compiled = self._merge(compiled, {namespace: imported})

        local = {
            key: deepcopy(value)
            for key, value in document.items()
            if key not in {"extends", "imports", "overrides", "patches"}
        }
        self._reject_immutable_changes(compiled, local, immutable_paths, source_uri)
        compiled = self._merge(compiled, local)

        overrides = document.get("overrides", {})
        if overrides:
            if not isinstance(overrides, dict):
                raise ContextChainError("overrides must be an object.")
            self._reject_immutable_changes(
                compiled, overrides, immutable_paths, source_uri
            )
            compiled = self._merge(compiled, overrides)

        patches = document.get("patches", [])
        if patches:
            if not isinstance(patches, list):
                raise ContextChainError("patches must be a list.")
            for patch in patches:
                self._apply_patch(compiled, patch, immutable_paths)

        chain.append(
            {
                "uri": source_uri,
                "id": document.get("id"),
                "type": document.get("type"),
                "version": document.get("version"),
                "source_hash": stable_hash(document),
            }
        )
        return compiled, self._deduplicate_chain(chain)

    @staticmethod
    def _merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
        """Execute merge.

        Args:
            base (dict[str, Any]): Base used by this operation.
            override (dict[str, Any]): Override used by this operation.

        Returns:
            dict[str, Any]: Result produced by the operation.
        """
        result = deepcopy(base)
        for key, value in override.items():
            current = result.get(key)
            if isinstance(current, dict) and isinstance(value, dict):
                result[key] = ContextChainResolver._merge(current, value)
            elif isinstance(current, list) and isinstance(value, list):
                result[key] = ContextChainResolver._merge_lists(key, current, value)
            else:
                result[key] = deepcopy(value)
        return result

    @staticmethod
    def _merge_lists(key: str, base: list[Any], override: list[Any]) -> list[Any]:
        """Execute lists.

        Args:
            key (str): Key used by this operation.
            base (list[Any]): Base used by this operation.
            override (list[Any]): Override used by this operation.

        Returns:
            list[Any]: Result produced by the operation.
        """
        if key in {"characters", "props"} and all(
            isinstance(item, dict) and item.get("id") for item in [*base, *override]
        ):
            by_id = {item["id"]: deepcopy(item) for item in base}
            for item in override:
                identifier = item["id"]
                by_id[identifier] = ContextChainResolver._merge(
                    by_id.get(identifier, {}), item
                )
            return list(by_id.values())
        if key in {"constraints", "forbidden", "references"}:
            result = deepcopy(base)
            for item in override:
                if item not in result:
                    result.append(deepcopy(item))
            return result
        return deepcopy(override)

    def _path_for_uri(self, uri: str) -> Path:
        """Execute for uri.

        Args:
            uri (str): Uri used by this operation.

        Returns:
            Path: Result produced by the operation.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        parsed = urlparse(uri)
        if parsed.scheme != "cinema":
            raise ContextChainError(f"Unsupported context URI: {uri}")
        parts = [parsed.netloc, *filter(None, parsed.path.split("/"))]
        if parts[:1] == ["studio"] and len(parts) == 2:
            path = self._source_root / "studio" / f"{parts[1]}.yaml"
        elif parts[:1] == ["projects"]:
            path = self._project_path(parts, uri)
        elif parts[:1] == ["runtime"] and len(parts) == 3 and parts[2] == "end-state":
            path = self._runtime_end_state_path(parts[1])
        else:
            raise ContextChainError(f"Unsupported context URI shape: {uri}")
        resolved = path.resolve()
        allowed_root = self._state_root if parts[0] == "runtime" else self._source_root
        if resolved != allowed_root and allowed_root not in resolved.parents:
            raise ContextChainError(f"Context URI escapes its configured root: {uri}")
        return resolved

    def _project_path(self, parts: list[str], uri: str) -> Path:
        """Execute path.

        Args:
            parts (list[str]): Parts used by this operation.
            uri (str): Uri used by this operation.

        Returns:
            Path: Result produced by the operation.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        if len(parts) < 2:
            raise ContextChainError(f"Project context URI is incomplete: {uri}")
        project_id = validate_identifier(parts[1], "project_id")
        project = self._source_root / "projects" / project_id
        if len(parts) == 2:
            return project / "project.yaml"
        kind = parts[2]
        if kind in {"characters", "locations", "sequences", "episodes"} and len(parts) == 4:
            identifier = validate_identifier(parts[3], f"{kind}_id")
            nested = project / kind / identifier / f"{kind[:-1]}.yaml"
            flat = project / kind / f"{identifier}.yaml"
            return nested if nested.is_file() else flat
        if kind == "scenes" and len(parts) >= 4:
            scene_id = validate_identifier(parts[3], "scene_id")
            scene = project / "scenes" / scene_id
            if len(parts) == 4:
                return scene / "scene.yaml"
            if len(parts) == 6 and parts[4] == "shots":
                shot_id = validate_identifier(parts[5], "shot_id")
                return scene / "shots" / shot_id / "shot.yaml"
            if len(parts) == 8 and parts[4] == "shots" and parts[6] == "segments":
                shot_id = validate_identifier(parts[5], "shot_id")
                segment_id = validate_identifier(parts[7], "segment_id")
                return scene / "shots" / shot_id / "segments" / f"{segment_id}.yaml"
        raise ContextChainError(f"Unsupported project context URI shape: {uri}")

    def _runtime_end_state_path(self, segment_id: str) -> Path:
        """Execute end state path.

        Args:
            segment_id (str): Stable identifier of the chained video segment.

        Returns:
            Path: Result produced by the operation.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        segment_id = validate_identifier(segment_id, "segment_id")
        matches = list(
            (self._state_root / "extensions").glob(
                f"*/*/*/v*/segments/{segment_id}/continuity-delta.yaml"
            )
        )
        if len(matches) != 1:
            raise ContextChainError(
                f"Expected one approved runtime end-state for '{segment_id}', "
                f"found {len(matches)}."
            )
        return matches[0]

    @staticmethod
    def _parse_pinned_uri(uri: str) -> tuple[str, int]:
        """Parse pinned uri.

        Args:
            uri (str): Uri used by this operation.

        Returns:
            tuple[str, int]: Result produced by the operation.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        if not isinstance(uri, str) or "@" not in uri:
            raise ContextChainError(f"Context URI must pin an integer version: {uri!r}")
        normalized, raw_version = uri.rsplit("@", 1)
        if raw_version == "latest" or not raw_version.isdigit():
            raise ContextChainError(f"Context URI must use an exact version: {uri}")
        return normalized, int(raw_version)

    @staticmethod
    def _string_list(value: Any, field: str) -> list[str]:
        """Execute list.

        Args:
            value (Any): Value inspected or transformed by the helper.
            field (str): Field used by this operation.

        Returns:
            list[str]: Result produced by the operation.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        if isinstance(value, str):
            value = [value]
        if not isinstance(value, list) or not all(
            isinstance(item, str) and item for item in value
        ):
            raise ContextChainError(f"{field} must be a string or string list.")
        return value

    @staticmethod
    def _immutable_paths(*contexts: dict[str, Any]) -> list[str]:
        """Execute paths.

        Args:
            *contexts (dict[str, Any]): Contexts used by this operation.

        Returns:
            list[str]: Result produced by the operation.
        """
        result: list[str] = []
        for context in contexts:
            policy = context.get("merge_policy", {})
            values = policy.get("immutable", []) if isinstance(policy, dict) else []
            if isinstance(values, list):
                result.extend(item for item in values if isinstance(item, str))
        return list(dict.fromkeys(result))

    def _reject_immutable_changes(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
        immutable_paths: Iterable[str],
        source_uri: str,
    ) -> None:
        """Reject immutable changes.

        Args:
            base (dict[str, Any]): Base used by this operation.
            override (dict[str, Any]): Override used by this operation.
            immutable_paths (Iterable[str]): Immutable paths used by this operation.
            source_uri (str): Pinned URI identifying the source context document.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        for path in immutable_paths:
            existing = self._get_dotted(base, path)
            proposed = self._get_dotted(override, path)
            if existing is not None and proposed is not None and existing != proposed:
                raise ContextChainError(
                    f"Context '{source_uri}' cannot override immutable field '{path}'."
                )

    def _apply_patch(
        self,
        document: dict[str, Any],
        patch: Any,
        immutable_paths: Iterable[str],
    ) -> None:
        """Apply patch.

        Args:
            document (dict[str, Any]): Structured document to validate, merge, or
                persist.
            patch (Any): Patch used by this operation.
            immutable_paths (Iterable[str]): Immutable paths used by this operation.

        Raises:
            ContextChainError: If inputs, context, state, or provider output are invalid.
        """
        if not isinstance(patch, dict):
            raise ContextChainError("Each context patch must be an object.")
        operation = patch.get("operation")
        pointer = patch.get("path")
        if operation not in {"add", "replace", "remove"} or not isinstance(
            pointer, str
        ):
            raise ContextChainError("Patch requires add/replace/remove and a path.")
        keys = [item.replace("~1", "/").replace("~0", "~") for item in pointer.split("/")[1:]]
        dotted = ".".join(keys)
        if dotted in immutable_paths:
            raise ContextChainError(f"Patch cannot modify immutable field '{dotted}'.")
        if not keys:
            raise ContextChainError("Patch cannot replace the document root.")
        target: dict[str, Any] = document
        for key in keys[:-1]:
            child = target.get(key)
            if not isinstance(child, dict):
                if operation == "add":
                    child = {}
                    target[key] = child
                else:
                    raise ContextChainError(f"Patch path does not exist: {pointer}")
            target = child
        leaf = keys[-1]
        if operation == "remove":
            if leaf not in target:
                raise ContextChainError(f"Patch path does not exist: {pointer}")
            del target[leaf]
        else:
            if operation == "replace" and leaf not in target:
                raise ContextChainError(f"Patch path does not exist: {pointer}")
            target[leaf] = deepcopy(patch.get("value"))

    @staticmethod
    def _get_dotted(document: dict[str, Any], path: str) -> Any:
        """Return dotted.

        Args:
            document (dict[str, Any]): Structured document to validate, merge, or
                persist.
            path (str): Filesystem path read or written by the operation.

        Returns:
            Any: Result produced by the operation.
        """
        current: Any = document
        for key in path.split("."):
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    @staticmethod
    def _deduplicate_chain(chain: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Execute chain.

        Args:
            chain (list[dict[str, Any]]): Chain used by this operation.

        Returns:
            list[dict[str, Any]]: Result produced by the operation.
        """
        result: list[dict[str, Any]] = []
        seen: set[str] = set()
        for item in chain:
            if item["uri"] not in seen:
                result.append(item)
                seen.add(item["uri"])
        return result
