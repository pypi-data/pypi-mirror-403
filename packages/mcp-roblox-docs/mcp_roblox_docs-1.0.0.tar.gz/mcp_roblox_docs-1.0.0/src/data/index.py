"""
Search Index - Full-text search across Roblox API.

Builds an inverted index for fast text search with simple scoring.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """A single search result."""

    type: str  # "class", "member", "enum"
    name: str
    class_name: str | None  # For members
    description: str
    score: float
    tags: list[str] = field(default_factory=list)
    member_type: str | None = None  # For members: Property, Method, Event, Callback


@dataclass
class SearchIndex:
    """
    Inverted index for full-text search.

    Index structure:
    - token -> [(type, name, class_name, score_boost), ...]
    """

    def __init__(self):
        self._index: dict[str, list[tuple[str, str, str | None, float]]] = defaultdict(list)
        self._class_data: dict[str, dict[str, Any]] = {}
        self._enum_data: dict[str, dict[str, Any]] = {}
        self._docs_data: dict[str, dict[str, Any]] = {}
        self._built = False

    def _tokenize(self, text: str) -> list[str]:
        """Tokenize text into searchable terms."""
        if not text:
            return []

        # Split camelCase and PascalCase
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)

        # Split on non-alphanumeric
        tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())

        return tokens

    def _add_to_index(
        self,
        tokens: list[str],
        type_: str,
        name: str,
        class_name: str | None = None,
        score_boost: float = 1.0,
    ) -> None:
        """Add tokens to the inverted index."""
        for token in tokens:
            if len(token) >= 2:  # Skip very short tokens
                self._index[token].append((type_, name, class_name, score_boost))

    def build(
        self,
        classes: list[dict[str, Any]],
        enums: list[dict[str, Any]],
        docs: dict[str, Any] | None = None,
    ) -> None:
        """Build the search index from API data."""
        logger.info("Building search index...")

        self._index.clear()
        self._class_data.clear()
        self._enum_data.clear()
        self._docs_data = docs or {}

        # Index classes
        for cls in classes:
            name = cls.get("Name", "")
            if not name:
                continue

            self._class_data[name] = cls

            # Index class name (high boost)
            tokens = self._tokenize(name)
            self._add_to_index(tokens, "class", name, score_boost=3.0)

            # Index class description from docs
            if docs and name in docs:
                desc = docs.get(name, {}).get("description", "")
                if desc:
                    desc_tokens = self._tokenize(desc)
                    self._add_to_index(desc_tokens, "class", name, score_boost=1.0)

            # Index members
            for member in cls.get("Members", []):
                member_name = member.get("Name", "")
                if not member_name:
                    continue

                # Index member name (medium boost)
                member_tokens = self._tokenize(member_name)
                self._add_to_index(member_tokens, "member", member_name, name, score_boost=2.0)

                # Index by member type
                member_type = member.get("MemberType", "")
                if member_type:
                    self._add_to_index(
                        [member_type.lower()], "member", member_name, name, score_boost=1.5
                    )

        # Index enums
        for enum in enums:
            name = enum.get("Name", "")
            if not name:
                continue

            self._enum_data[name] = enum

            # Index enum name (high boost)
            tokens = self._tokenize(name)
            self._add_to_index(tokens, "enum", name, score_boost=3.0)

            # Index enum items
            for item in enum.get("Items", []):
                item_name = item.get("Name", "")
                if item_name:
                    item_tokens = self._tokenize(item_name)
                    self._add_to_index(item_tokens, "enum", name, score_boost=1.5)

        self._built = True
        logger.info(
            f"Index built: {len(self._index)} unique tokens, "
            f"{len(self._class_data)} classes, {len(self._enum_data)} enums"
        )

    def search(self, query: str, limit: int = 25) -> list[SearchResult]:
        """
        Search the index for matching results.

        Returns results sorted by relevance score.
        """
        if not self._built:
            logger.warning("Search index not built yet")
            return []

        tokens = self._tokenize(query)
        if not tokens:
            return []

        # Accumulate scores
        scores: dict[tuple[str, str, str | None], float] = defaultdict(float)

        for token in tokens:
            # Exact match
            if token in self._index:
                for type_, name, class_name, boost in self._index[token]:
                    key = (type_, name, class_name)
                    scores[key] += boost * 2.0

            # Prefix match
            for indexed_token, entries in self._index.items():
                if indexed_token.startswith(token) and indexed_token != token:
                    for type_, name, class_name, boost in entries:
                        key = (type_, name, class_name)
                        scores[key] += boost * 0.5

        # Sort by score and build results
        sorted_items = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:limit]

        results = []
        seen = set()  # Dedupe

        for (type_, name, class_name), score in sorted_items:
            key = (type_, name, class_name)
            if key in seen:
                continue
            seen.add(key)

            result = self._build_result(type_, name, class_name, score)
            if result:
                results.append(result)

        return results

    def _build_result(
        self, type_: str, name: str, class_name: str | None, score: float
    ) -> SearchResult | None:
        """Build a SearchResult from index data."""
        if type_ == "class":
            cls = self._class_data.get(name)
            if not cls:
                return None

            # Get description from docs
            desc = ""
            if name in self._docs_data:
                desc = self._docs_data[name].get("description", "")[:200]

            return SearchResult(
                type="class",
                name=name,
                class_name=None,
                description=desc or f"Class: {name}",
                score=score,
                tags=cls.get("Tags", []),
            )

        elif type_ == "member":
            if not class_name:
                return None
            cls = self._class_data.get(class_name)
            if not cls:
                return None

            # Find the member
            member = None
            for m in cls.get("Members", []):
                if m.get("Name") == name:
                    member = m
                    break

            if not member:
                return None

            member_type = member.get("MemberType", "")

            # Build description
            if member_type == "Property":
                value_type = member.get("ValueType", {}).get("Name", "unknown")
                desc = f"Property: {value_type}"
            elif member_type in ("Method", "Function"):
                params = member.get("Parameters", [])
                param_str = ", ".join(p.get("Name", "") for p in params)
                return_type = member.get("ReturnType", {}).get("Name", "void")
                desc = f"Method({param_str}) -> {return_type}"
            elif member_type == "Event":
                params = member.get("Parameters", [])
                param_str = ", ".join(p.get("Name", "") for p in params)
                desc = f"Event({param_str})"
            elif member_type == "Callback":
                desc = "Callback"
            else:
                desc = member_type or "Unknown"

            return SearchResult(
                type="member",
                name=name,
                class_name=class_name,
                description=desc,
                score=score,
                tags=member.get("Tags", []),
                member_type=member_type,
            )

        elif type_ == "enum":
            enum = self._enum_data.get(name)
            if not enum:
                return None

            item_count = len(enum.get("Items", []))

            return SearchResult(
                type="enum",
                name=name,
                class_name=None,
                description=f"Enum with {item_count} values",
                score=score,
                tags=[],
            )

        return None

    def is_built(self) -> bool:
        """Check if index has been built."""
        return self._built

    def get_stats(self) -> dict[str, int]:
        """Get index statistics."""
        return {
            "unique_tokens": len(self._index),
            "classes": len(self._class_data),
            "enums": len(self._enum_data),
            "total_entries": sum(len(v) for v in self._index.values()),
        }
