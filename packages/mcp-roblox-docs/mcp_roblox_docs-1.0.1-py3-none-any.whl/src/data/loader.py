"""
Data Loader - Lazy loading and in-memory caching of Roblox API data.

Provides efficient access to:
- Classes (with members, inheritance)
- Enums (with items)
- Documentation (descriptions, examples)
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TypedDict

import orjson

logger = logging.getLogger(__name__)


class MemberInfo(TypedDict, total=False):
    """Type definition for API member."""

    MemberType: str
    Name: str
    ValueType: dict[str, str] | None
    ReturnType: dict[str, str] | None
    Parameters: list[dict[str, Any]]
    Security: dict[str, str] | str
    Tags: list[str]
    ThreadSafety: str
    Default: Any


class ClassInfo(TypedDict, total=False):
    """Type definition for API class."""

    Name: str
    Superclass: str
    Members: list[MemberInfo]
    Tags: list[str]
    MemoryCategory: str


class EnumItem(TypedDict):
    """Type definition for enum item."""

    Name: str
    Value: int


class EnumInfo(TypedDict):
    """Type definition for enum."""

    Name: str
    Items: list[EnumItem]


class ApiDump(TypedDict):
    """Type definition for API dump structure."""

    Version: int
    Classes: list[ClassInfo]
    Enums: list[EnumInfo]


class DataLoader:
    """
    Lazy-loading data manager with in-memory caching.

    Data is loaded on first access and cached for subsequent calls.
    """

    def __init__(self, cache_dir: Path, language: str = "en-us"):
        self.cache_dir = Path(cache_dir)
        self.language = language

        # In-memory caches (lazy loaded)
        self._api_dump: ApiDump | None = None
        self._api_docs: dict[str, Any] | None = None
        self._full_api_dump: ApiDump | None = None

        # Pre-computed lookups (built after first load)
        self._class_map: dict[str, ClassInfo] | None = None
        self._enum_map: dict[str, EnumInfo] | None = None
        self._member_map: dict[str, dict[str, MemberInfo]] | None = None
        self._inheritance_map: dict[str, list[str]] | None = None
        self._docs_map: dict[str, dict[str, Any]] | None = None

    @property
    def api_dump_path(self) -> Path:
        return self.cache_dir / "api-dump.json"

    @property
    def api_docs_path(self) -> Path:
        return self.cache_dir / f"api-docs-{self.language}.json"

    @property
    def full_api_dump_path(self) -> Path:
        return self.cache_dir / "full-api-dump.json"

    def _load_json(self, path: Path) -> dict[str, Any] | None:
        """Load JSON file with error handling."""
        if not path.exists():
            logger.warning(f"File not found: {path}")
            return None
        try:
            return orjson.loads(path.read_bytes())
        except Exception as e:
            logger.error(f"Failed to load {path}: {e}")
            return None

    def get_api_dump(self) -> ApiDump | None:
        """Get API dump with lazy loading."""
        if self._api_dump is None:
            data = self._load_json(self.api_dump_path)
            if data:
                self._api_dump = data  # type: ignore
                self._build_lookups()
        return self._api_dump

    def get_api_docs(self) -> dict[str, Any] | None:
        """Get API docs with lazy loading."""
        if self._api_docs is None:
            self._api_docs = self._load_json(self.api_docs_path)
            if self._api_docs:
                self._build_docs_map()
        return self._api_docs

    def get_full_api_dump(self) -> ApiDump | None:
        """Get full API dump (with default values)."""
        if self._full_api_dump is None:
            data = self._load_json(self.full_api_dump_path)
            if data:
                self._full_api_dump = data  # type: ignore
        return self._full_api_dump

    def _build_lookups(self) -> None:
        """Build pre-computed lookup tables for fast access."""
        if self._api_dump is None:
            return

        # Build class map
        self._class_map = {}
        self._member_map = {}
        self._inheritance_map = {}

        for cls in self._api_dump.get("Classes", []):
            name = cls.get("Name", "")
            if name:
                self._class_map[name] = cls
                self._class_map[name.lower()] = cls  # Case-insensitive lookup

                # Build member map
                self._member_map[name] = {}
                for member in cls.get("Members", []):
                    member_name = member.get("Name", "")
                    if member_name:
                        self._member_map[name][member_name] = member
                        self._member_map[name][member_name.lower()] = member

        # Build inheritance map
        for cls in self._api_dump.get("Classes", []):
            name = cls.get("Name", "")
            if name:
                self._inheritance_map[name] = self._get_inheritance_chain(name)

        # Build enum map
        self._enum_map = {}
        for enum in self._api_dump.get("Enums", []):
            name = enum.get("Name", "")
            if name:
                self._enum_map[name] = enum
                self._enum_map[name.lower()] = enum

        logger.info(
            f"Built lookups: {len(self._class_map) // 2} classes, {len(self._enum_map) // 2} enums"
        )

    def _build_docs_map(self) -> None:
        """Build documentation lookup map."""
        if self._api_docs is None:
            return

        self._docs_map = {}

        # API docs structure varies, try to normalize
        for key, value in self._api_docs.items():
            if isinstance(value, dict):
                self._docs_map[key] = value
                self._docs_map[key.lower()] = value

    def _get_inheritance_chain(self, class_name: str) -> list[str]:
        """Get full inheritance chain for a class."""
        chain = []
        current = class_name
        seen = set()

        while current and current != "<<<ROOT>>>" and current not in seen:
            seen.add(current)
            chain.append(current)
            cls = self._class_map.get(current) if self._class_map else None
            if cls:
                current = cls.get("Superclass", "")
            else:
                break

        return chain

    def get_class(self, name: str) -> ClassInfo | None:
        """Get class by name (case-insensitive)."""
        self.get_api_dump()  # Ensure loaded
        if self._class_map:
            return self._class_map.get(name) or self._class_map.get(name.lower())
        return None

    def get_all_classes(self) -> list[ClassInfo]:
        """Get all classes."""
        dump = self.get_api_dump()
        return dump.get("Classes", []) if dump else []

    def get_enum(self, name: str) -> EnumInfo | None:
        """Get enum by name (case-insensitive)."""
        self.get_api_dump()  # Ensure loaded
        if self._enum_map:
            return self._enum_map.get(name) or self._enum_map.get(name.lower())
        return None

    def get_all_enums(self) -> list[EnumInfo]:
        """Get all enums."""
        dump = self.get_api_dump()
        return dump.get("Enums", []) if dump else []

    def get_member(
        self, class_name: str, member_name: str, include_inherited: bool = True
    ) -> MemberInfo | None:
        """Get a specific member from a class, optionally including inherited members."""
        self.get_api_dump()  # Ensure loaded
        if not self._member_map:
            return None

        # First check direct class members
        class_members = self._member_map.get(class_name) or self._member_map.get(
            class_name.lower(), {}
        )
        member = class_members.get(member_name) or class_members.get(member_name.lower())

        if member:
            return member

        # If not found and include_inherited, check parent classes
        if include_inherited:
            chain = self.get_inheritance(class_name)
            for parent_class in chain[1:]:  # Skip the class itself
                parent_members = self._member_map.get(parent_class, {})
                member = parent_members.get(member_name) or parent_members.get(member_name.lower())
                if member:
                    return member

        return None

    def get_class_members(
        self, class_name: str, member_type: str | None = None
    ) -> list[MemberInfo]:
        """Get all members of a class, optionally filtered by type."""
        cls = self.get_class(class_name)
        if not cls:
            return []

        members = cls.get("Members", [])
        if member_type:
            members = [m for m in members if m.get("MemberType") == member_type]

        return members

    def get_inheritance(self, class_name: str) -> list[str]:
        """Get inheritance chain for a class."""
        self.get_api_dump()  # Ensure loaded
        if self._inheritance_map:
            return self._inheritance_map.get(class_name, [])
        return self._get_inheritance_chain(class_name)

    def get_subclasses(self, class_name: str) -> list[str]:
        """Get all direct subclasses of a class."""
        dump = self.get_api_dump()
        if not dump:
            return []

        subclasses = []
        for cls in dump.get("Classes", []):
            if cls.get("Superclass") == class_name:
                subclasses.append(cls.get("Name", ""))

        return subclasses

    def get_class_doc(self, class_name: str) -> dict[str, Any] | None:
        """Get documentation for a class."""
        self.get_api_docs()  # Ensure loaded
        if self._docs_map:
            return self._docs_map.get(class_name) or self._docs_map.get(class_name.lower())
        return None

    def get_services(self) -> list[ClassInfo]:
        """Get all service classes."""
        classes = self.get_all_classes()
        return [c for c in classes if "Service" in c.get("Tags", [])]

    def get_deprecated_classes(self) -> list[ClassInfo]:
        """Get all deprecated classes."""
        classes = self.get_all_classes()
        return [c for c in classes if "Deprecated" in c.get("Tags", [])]

    def is_deprecated(self, class_name: str, member_name: str | None = None) -> bool:
        """Check if a class or member is deprecated."""
        if member_name:
            member = self.get_member(class_name, member_name)
            if member:
                return "Deprecated" in member.get("Tags", [])
            return False
        else:
            cls = self.get_class(class_name)
            if cls:
                return "Deprecated" in cls.get("Tags", [])
            return False

    def get_version(self) -> int | None:
        """Get API dump version."""
        dump = self.get_api_dump()
        return dump.get("Version") if dump else None

    def clear_cache(self) -> None:
        """Clear in-memory caches (forces reload on next access)."""
        self._api_dump = None
        self._api_docs = None
        self._full_api_dump = None
        self._class_map = None
        self._enum_map = None
        self._member_map = None
        self._inheritance_map = None
        self._docs_map = None
        logger.info("Cleared in-memory cache")

    def set_language(self, language: str) -> None:
        """Change documentation language."""
        from src.data.syncer import AVAILABLE_LANGUAGES

        if language in AVAILABLE_LANGUAGES:
            self.language = language
            self._api_docs = None  # Clear docs cache
            self._docs_map = None
            logger.info(f"Switched language to {language}")
