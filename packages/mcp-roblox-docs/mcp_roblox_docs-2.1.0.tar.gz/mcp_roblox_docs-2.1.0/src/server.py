"""
MCP Roblox Docs - Main Server (v2.1.0)

A comprehensive MCP server for Roblox Studio documentation.
Provides always up-to-date API reference, FastFlags, Open Cloud API,
Luau language reference, DataTypes, Libraries, DevForum search, and more.

Data Sources:
- API-Dump.json: Complete Roblox API (classes, members, enums)
- api-docs/{lang}.json: Human-readable descriptions (15 languages)
- FVariables.txt: FastFlags (DFFlag, FFlag, etc.)
- LuauTypes.d.luau: Roblox Luau type definitions
- ReflectionMetadata.xml: Extra class metadata
- openapi.json: Open Cloud REST API specification
- Luau docs: Language reference documentation

Usage:
    uv run src/server.py

Or via MCP config:
    {
        "command": "uv",
        "args": ["--directory", "/path/to/mcp-roblox-docs", "run", "src/server.py"]
    }
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import platformdirs
from mcp.server.fastmcp import FastMCP

from src.data.loader import DataLoader
from src.data.syncer import DataSyncer, AVAILABLE_LANGUAGES, LUAU_DOCS_TOPICS
from src.data.index import SearchIndex
from src.utils.formatter import (
    format_class,
    format_enum,
    format_member,
    format_deprecation,
    format_search_results,
    format_inheritance,
    format_services,
    # Extended formatters
    format_fflag,
    format_fflag_search_results,
    format_luau_globals,
    format_luau_global,
    format_class_with_metadata,
    format_cloud_endpoint,
    format_cloud_search_results,
    format_luau_doc,
    # DataType and Library formatters
    format_datatype,
    format_datatype_list,
    format_library,
    format_library_function,
    format_library_list,
)

# Configure logging to stderr (important for MCP!)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("mcp-roblox-docs")

# Cache directory - uses platform-appropriate user cache location
# Windows: C:\Users\<user>\AppData\Local\mcp-roblox-docs\
# Linux: ~/.cache/mcp-roblox-docs/
# macOS: ~/Library/Caches/mcp-roblox-docs/
CACHE_DIR = Path(platformdirs.user_cache_dir("mcp-roblox-docs"))

# Initialize FastMCP server
mcp = FastMCP("roblox-docs")

# Global state (initialized on startup)
_loader: DataLoader | None = None
_index: SearchIndex | None = None
_syncer: DataSyncer | None = None
_language: str = "en-us"

# DevForum cache (query -> (timestamp, results))
_devforum_cache: dict[str, tuple[datetime, list[dict]]] = {}
_DEVFORUM_CACHE_TTL = 3600  # 1 hour in seconds


async def ensure_initialized() -> tuple[DataLoader, SearchIndex]:
    """Ensure data is loaded and index is built."""
    global _loader, _index, _syncer, _language

    if _loader is None:
        _syncer = DataSyncer(CACHE_DIR, language=_language)

        # Sync data if needed
        await _syncer.sync()

        _loader = DataLoader(CACHE_DIR, language=_language)

    if _index is None or not _index.is_built():
        _index = SearchIndex()

        # Build index
        classes = _loader.get_all_classes()
        enums = _loader.get_all_enums()
        docs = _loader.get_api_docs() or {}

        _index.build(classes, enums, docs)

    return _loader, _index


# ============================================================================
# CORE TOOLS
# ============================================================================


@mcp.tool()
async def roblox_search(query: str, limit: int = 25) -> str:
    """
    Search across all Roblox API - classes, members, enums.

    Use this to find APIs by name, functionality, or description.
    Supports partial matches and camelCase splitting.

    Args:
        query: Search query (e.g., "tween animation", "player character", "physics")
        limit: Maximum results to return (default 25, max 50)

    Returns:
        Formatted list of matching APIs with type, name, and description.
    """
    loader, index = await ensure_initialized()

    limit = min(max(1, limit), 50)
    results = index.search(query, limit=limit)

    return format_search_results(results, query)


@mcp.tool()
async def roblox_get_class(class_name: str, include_members: bool = True) -> str:
    """
    Get complete information about a Roblox class.

    Returns class description, inheritance, properties, methods, events, and callbacks.
    Also includes extra metadata like category and explorer icon when available.

    Args:
        class_name: Name of the class (e.g., "Part", "TweenService", "Player")
        include_members: Whether to include all members (default True)

    Returns:
        Formatted class information with all details.
    """
    loader, _ = await ensure_initialized()

    cls = loader.get_class(class_name)
    if not cls:
        return f"Class '{class_name}' not found. Try using roblox_search to find the correct name."

    docs = loader.get_class_doc(class_name)
    metadata = loader.get_class_metadata(class_name)

    # Use enhanced formatter if metadata is available
    if metadata:
        return format_class_with_metadata(cls, docs, metadata, include_members=include_members)
    return format_class(cls, docs, include_members=include_members)


@mcp.tool()
async def roblox_get_member(class_name: str, member_name: str) -> str:
    """
    Get detailed information about a specific class member.

    Works for properties, methods, events, and callbacks.

    Args:
        class_name: Name of the class (e.g., "Part", "TweenService")
        member_name: Name of the member (e.g., "Anchored", "Create", "Touched")

    Returns:
        Detailed member information including type, parameters, return values.
    """
    loader, _ = await ensure_initialized()

    cls = loader.get_class(class_name)
    if not cls:
        return f"Class '{class_name}' not found."

    member = loader.get_member(class_name, member_name)
    if not member:
        # Try to find similar members
        all_members = loader.get_class_members(class_name)
        member_names = [m.get("Name", "") for m in all_members]

        # Simple fuzzy match
        suggestions = [n for n in member_names if member_name.lower() in n.lower()][:5]

        if suggestions:
            return f"Member '{member_name}' not found in {class_name}. Did you mean: {', '.join(suggestions)}?"
        return f"Member '{member_name}' not found in class '{class_name}'."

    docs = loader.get_class_doc(class_name)

    return format_member(member, class_name, docs)


@mcp.tool()
async def roblox_get_enum(enum_name: str) -> str:
    """
    Get all values of a Roblox enum.

    Useful for finding valid values for enum-typed properties.

    Args:
        enum_name: Name of the enum (e.g., "Material", "PartType", "EasingStyle")

    Returns:
        Enum name and all its values with their numeric codes.
    """
    loader, _ = await ensure_initialized()

    enum = loader.get_enum(enum_name)
    if not enum:
        # Try to find similar enums
        all_enums = loader.get_all_enums()
        enum_names = [e.get("Name", "") for e in all_enums]

        suggestions = [n for n in enum_names if enum_name.lower() in n.lower()][:5]

        if suggestions:
            return f"Enum '{enum_name}' not found. Did you mean: {', '.join(suggestions)}?"
        return f"Enum '{enum_name}' not found. Use roblox_search('enum <name>') to find enums."

    return format_enum(enum)


@mcp.tool()
async def roblox_check_deprecated(name: str, class_name: str | None = None) -> str:
    """
    Check if a class or member is deprecated.

    Provides deprecation status and suggests alternatives when available.

    Args:
        name: Name of the class or member to check
        class_name: If checking a member, provide the class name

    Returns:
        Deprecation status with alternatives if available.
    """
    loader, _ = await ensure_initialized()

    if class_name:
        # Check member
        member = loader.get_member(class_name, name)
        if not member:
            return f"Member '{name}' not found in class '{class_name}'."

        tags = member.get("Tags", [])
        is_deprecated = "Deprecated" in tags

        # Known deprecation mappings
        alternatives = get_deprecation_alternatives(name, class_name)

        return format_deprecation(
            name,
            is_class=False,
            is_deprecated=is_deprecated,
            class_name=class_name,
            tags=tags,
            alternatives=alternatives,
        )
    else:
        # Check class
        cls = loader.get_class(name)
        if not cls:
            return f"Class '{name}' not found."

        tags = cls.get("Tags", [])
        is_deprecated = "Deprecated" in tags

        alternatives = get_deprecation_alternatives(name, None)

        return format_deprecation(
            name, is_class=True, is_deprecated=is_deprecated, tags=tags, alternatives=alternatives
        )


# ============================================================================
# EXTENDED TOOLS
# ============================================================================


@mcp.tool()
async def roblox_list_services() -> str:
    """
    List all Roblox services.

    Services are singleton objects that provide core game functionality.
    Access them with game:GetService("ServiceName").

    Returns:
        List of all available services with their status.
    """
    loader, _ = await ensure_initialized()

    services = loader.get_services()

    return format_services(services)


@mcp.tool()
async def roblox_get_inheritance(class_name: str) -> str:
    """
    Get the inheritance hierarchy of a class.

    Shows the full ancestor chain and direct subclasses.

    Args:
        class_name: Name of the class (e.g., "Part", "BasePart", "Instance")

    Returns:
        Inheritance chain and list of direct subclasses.
    """
    loader, _ = await ensure_initialized()

    cls = loader.get_class(class_name)
    if not cls:
        return f"Class '{class_name}' not found."

    chain = loader.get_inheritance(class_name)
    subclasses = loader.get_subclasses(class_name)

    return format_inheritance(class_name, chain, subclasses)


@mcp.tool()
async def roblox_search_devforum(query: str, limit: int = 10) -> str:
    """
    Search the Roblox Developer Forum for discussions and solutions.

    Great for finding best practices, tutorials, and community solutions.
    Results are cached for 1 hour to improve performance.

    Args:
        query: Search query (e.g., "memory optimization", "pathfinding", "datastore")
        limit: Maximum results (default 10, max 25)

    Returns:
        List of relevant DevForum threads with titles and links.
    """
    global _devforum_cache

    limit = min(max(1, limit), 25)
    cache_key = query.lower().strip()

    # Check cache
    if cache_key in _devforum_cache:
        cached_time, cached_topics = _devforum_cache[cache_key]
        age = (datetime.now(timezone.utc) - cached_time).total_seconds()
        if age < _DEVFORUM_CACHE_TTL:
            topics = cached_topics[:limit]
            return _format_devforum_results(query, topics, cached=True)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://devforum.roblox.com/search.json",
                params={"q": query},
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
    except Exception as e:
        logger.warning(f"DevForum search failed: {e}")
        # Return cached results if available, even if stale
        if cache_key in _devforum_cache:
            _, cached_topics = _devforum_cache[cache_key]
            return _format_devforum_results(query, cached_topics[:limit], cached=True, stale=True)
        return f"DevForum search failed: {e}. Try again later or search directly at https://devforum.roblox.com"

    topics = data.get("topics", [])

    # Cache results
    _devforum_cache[cache_key] = (datetime.now(timezone.utc), topics)

    # Limit cache size
    if len(_devforum_cache) > 100:
        # Remove oldest entries
        sorted_keys = sorted(_devforum_cache.keys(), key=lambda k: _devforum_cache[k][0])
        for key in sorted_keys[:20]:
            del _devforum_cache[key]

    return _format_devforum_results(query, topics[:limit])


def _format_devforum_results(
    query: str, topics: list[dict], cached: bool = False, stale: bool = False
) -> str:
    """Format DevForum search results."""
    if not topics:
        return f"No DevForum results for '{query}'. Try different keywords."

    lines = []
    cache_note = ""
    if cached:
        cache_note = " (cached)"
    if stale:
        cache_note = " (cached, may be outdated)"

    lines.append(f"DevForum results for '{query}' ({len(topics)} found){cache_note}:")
    lines.append("")

    for i, topic in enumerate(topics, 1):
        title = topic.get("title", "Unknown")
        topic_id = topic.get("id", 0)
        category_id = topic.get("category_id", 0)

        # Determine category
        category = {
            4: "Help and Feedback",
            6: "Resources",
            10: "Scripting Support",
            11: "Building Support",
            12: "Art Design Support",
            45: "Code Review",
            55: "Community Tutorials",
        }.get(category_id, "Discussion")

        url = f"https://devforum.roblox.com/t/{topic_id}"

        lines.append(f"{i}. {title}")
        lines.append(f"   Category: {category}")
        lines.append(f"   Link: {url}")
        lines.append("")

    return "\n".join(lines)


@mcp.tool()
async def roblox_recent_changes(days: int = 7) -> str:
    """
    Get information about recent API changes (placeholder).

    Note: This currently shows API version info. Full changelog tracking
    requires comparing historical API dumps.

    Args:
        days: Number of days to look back (currently unused)

    Returns:
        Current API version and available data sources.
    """
    loader, _ = await ensure_initialized()

    version = loader.get_version()

    lines = []
    lines.append("ROBLOX API VERSION INFO")
    lines.append("")
    lines.append(f"Current API Version: {version}")
    lines.append("")
    lines.append("Note: For detailed changelogs, see:")
    lines.append("  - https://github.com/MaximumADHD/Roblox-Client-Tracker")
    lines.append("  - https://devforum.roblox.com/c/updates/release-notes")
    lines.append("")
    lines.append("Use roblox_search_devforum('release notes') for recent updates.")

    return "\n".join(lines)


# ============================================================================
# UTILITY TOOLS
# ============================================================================


@mcp.tool()
async def roblox_sync(force: bool = False, language: str | None = None) -> str:
    """
    Force sync data from remote sources.

    Use this to update to the latest Roblox API data.

    Args:
        force: Force re-download even if data is current
        language: Switch documentation language (e.g., "en-us", "id-id", "ja-jp")

    Returns:
        Sync status and version information.
    """
    global _loader, _index, _syncer, _language

    # Update language if specified
    if language:
        if language not in AVAILABLE_LANGUAGES:
            return f"Unknown language: {language}. Available: {', '.join(AVAILABLE_LANGUAGES)}"
        _language = language

    # Clear caches
    if _loader:
        _loader.clear_cache()
    _index = None

    # Re-sync
    _syncer = DataSyncer(CACHE_DIR, language=_language)
    success = await _syncer.sync(force=force)

    # Reload
    _loader = DataLoader(CACHE_DIR, language=_language)

    if success:
        version = _loader.get_version()
        return f"Sync complete! API Version: {version}, Language: {_language}"
    else:
        return "Sync completed with some errors. Some data may be missing."


@mcp.tool()
async def roblox_list_enums(filter_text: str | None = None) -> str:
    """
    List all available Roblox enums.

    Args:
        filter_text: Optional filter to search enum names

    Returns:
        List of enum names (use roblox_get_enum for values).
    """
    loader, _ = await ensure_initialized()

    enums = loader.get_all_enums()

    if filter_text:
        filter_lower = filter_text.lower()
        enums = [e for e in enums if filter_lower in e.get("Name", "").lower()]

    if not enums:
        return f"No enums found matching '{filter_text}'" if filter_text else "No enums found."

    lines = []
    lines.append(f"ROBLOX ENUMS ({len(enums)} total)")
    lines.append("")

    for enum in sorted(enums, key=lambda e: e.get("Name", "")):
        name = enum.get("Name", "Unknown")
        item_count = len(enum.get("Items", []))
        lines.append(f"  {name} ({item_count} values)")

    lines.append("")
    lines.append("Use roblox_get_enum('EnumName') to see all values.")

    return "\n".join(lines)


# ============================================================================
# FASTFLAG TOOLS
# ============================================================================


@mcp.tool()
async def roblox_search_fflags(query: str, limit: int = 50) -> str:
    """
    Search Roblox FastFlags (FVariables).

    FastFlags are internal settings that control Roblox features.
    Includes FFlag, DFFlag, FInt, FString, and more.

    Args:
        query: Search query (e.g., "Physics", "Render", "Lua")
        limit: Maximum results (default 50, max 100)

    Returns:
        List of matching FastFlags grouped by type.
    """
    loader, _ = await ensure_initialized()

    limit = min(max(1, limit), 100)
    flags = loader.search_fflags(query, limit=limit)

    return format_fflag_search_results(flags, query)


@mcp.tool()
async def roblox_get_fflag(flag_name: str) -> str:
    """
    Get detailed information about a specific FastFlag.

    Args:
        flag_name: Name of the flag (e.g., "DFFlagDebugVisualizeFrustum")

    Returns:
        Detailed flag information including type and usage notes.
    """
    loader, _ = await ensure_initialized()

    flag = loader.get_fflag(flag_name)
    if not flag:
        # Try searching
        suggestions = loader.search_fflags(flag_name, limit=5)
        if suggestions:
            names = [f.full_name for f in suggestions]
            return f"FastFlag '{flag_name}' not found. Did you mean: {', '.join(names)}?"
        return f"FastFlag '{flag_name}' not found. Use roblox_search_fflags to search."

    return format_fflag(flag)


@mcp.tool()
async def roblox_list_fflag_prefixes() -> str:
    """
    List all FastFlag prefix types and their meanings.

    Returns:
        Explanation of each FastFlag prefix type.
    """
    lines = []
    lines.append("FASTFLAG PREFIX TYPES")
    lines.append("")
    lines.append("Boolean Flags (true/false):")
    lines.append("  FFlag   - Feature Flag (client)")
    lines.append("  DFFlag  - Dynamic Feature Flag (can change at runtime)")
    lines.append("  SFFlag  - Sync Feature Flag (synchronized)")
    lines.append("")
    lines.append("Integer Flags (numeric values):")
    lines.append("  FInt    - Feature Integer")
    lines.append("  DFInt   - Dynamic Feature Integer")
    lines.append("  SFInt   - Sync Feature Integer")
    lines.append("")
    lines.append("String Flags (text values):")
    lines.append("  FString - Feature String")
    lines.append("  DFString - Dynamic Feature String")
    lines.append("")
    lines.append("Log Flags (logging control):")
    lines.append("  FLog    - Feature Log")
    lines.append("  DFLog   - Dynamic Feature Log")
    lines.append("")
    lines.append("Usage in Studio:")
    lines.append("  game:SetFastFlagForTesting('FlagName', value)")
    lines.append("")
    lines.append("WARNING: FastFlags are internal and may change without notice.")

    return "\n".join(lines)


# ============================================================================
# LUAU GLOBALS TOOLS
# ============================================================================


@mcp.tool()
async def roblox_get_luau_globals(filter_kind: str | None = None) -> str:
    """
    Get Roblox Luau global functions and types.

    These are the built-in globals available in Roblox Luau scripts,
    like wait, delay, tick, time, task, spawn, etc.

    Args:
        filter_kind: Optional filter by kind: "function", "variable", or "type"

    Returns:
        List of Luau globals with their signatures.
    """
    loader, _ = await ensure_initialized()

    globals_list = loader.get_luau_globals()

    if not globals_list:
        return "Luau globals not available. Try roblox_sync(force=True) to download."

    return format_luau_globals(globals_list, filter_kind)


@mcp.tool()
async def roblox_get_luau_global(name: str) -> str:
    """
    Get detailed information about a specific Luau global.

    Args:
        name: Name of the global (e.g., "wait", "task", "tick")

    Returns:
        Detailed information about the global.
    """
    loader, _ = await ensure_initialized()

    global_item = loader.get_luau_global(name)
    if not global_item:
        # List available
        all_globals = loader.get_luau_globals()
        names = [g.name for g in all_globals if name.lower() in g.name.lower()][:10]
        if names:
            return f"Luau global '{name}' not found. Similar: {', '.join(names)}"
        return f"Luau global '{name}' not found. Use roblox_get_luau_globals() to list all."

    return format_luau_global(global_item)


# ============================================================================
# OPEN CLOUD API TOOLS
# ============================================================================


@mcp.tool()
async def roblox_search_cloud_api(query: str, limit: int = 25) -> str:
    """
    Search Roblox Open Cloud REST API endpoints.

    Open Cloud provides REST APIs for managing games, assets,
    datastores, messaging, and more from external services.

    Args:
        query: Search query (e.g., "datastore", "assets", "publish")
        limit: Maximum results (default 25, max 50)

    Returns:
        List of matching API endpoints grouped by category.
    """
    loader, _ = await ensure_initialized()

    limit = min(max(1, limit), 50)
    endpoints = loader.search_cloud_endpoints(query, limit=limit)

    return format_cloud_search_results(endpoints, query)


@mcp.tool()
async def roblox_get_cloud_endpoint(operation_id: str) -> str:
    """
    Get detailed information about an Open Cloud API endpoint.

    Args:
        operation_id: The operation ID from search results

    Returns:
        Complete endpoint documentation including parameters and responses.
    """
    loader, _ = await ensure_initialized()

    endpoint = loader.get_cloud_endpoint(operation_id)
    if not endpoint:
        # Try searching
        all_endpoints = loader.get_all_cloud_endpoints()
        matches = [ep for ep in all_endpoints if operation_id.lower() in ep.operation_id.lower()][
            :5
        ]
        if matches:
            names = [ep.operation_id for ep in matches]
            return f"Endpoint '{operation_id}' not found. Did you mean: {', '.join(names)}?"
        return f"Endpoint '{operation_id}' not found. Use roblox_search_cloud_api to search."

    return format_cloud_endpoint(endpoint)


@mcp.tool()
async def roblox_list_cloud_apis() -> str:
    """
    List all Open Cloud API categories.

    Returns:
        List of available Open Cloud API categories with endpoint counts.
    """
    loader, _ = await ensure_initialized()

    endpoints = loader.get_all_cloud_endpoints()
    tags = loader.get_cloud_api_tags()

    if not endpoints:
        return "Open Cloud API not available. Try roblox_sync(force=True) to download."

    lines = []
    lines.append(f"ROBLOX OPEN CLOUD API ({len(endpoints)} endpoints)")
    lines.append("")
    lines.append("Available API Categories:")
    lines.append("")

    # Count by tag
    tag_counts: dict[str, int] = {}
    for ep in endpoints:
        for tag in ep.tags:
            tag_counts[tag] = tag_counts.get(tag, 0) + 1

    for tag in sorted(tag_counts.keys()):
        count = tag_counts[tag]
        lines.append(f"  {tag}: {count} endpoints")

    lines.append("")
    lines.append("Use roblox_search_cloud_api('category') to explore endpoints.")
    lines.append("")
    lines.append("DOCS: https://create.roblox.com/docs/cloud/reference")

    return "\n".join(lines)


# ============================================================================
# LUAU LANGUAGE DOCUMENTATION TOOLS
# ============================================================================


@mcp.tool()
async def roblox_get_luau_topic(topic: str) -> str:
    """
    Get Luau language documentation for a specific topic.

    Available topics include: tables, functions, strings, control-structures,
    type-checking, metatables, operators, and more.

    Args:
        topic: Topic name (e.g., "tables", "functions", "type-checking")

    Returns:
        Luau documentation for the topic in markdown format.
    """
    loader, _ = await ensure_initialized()

    # Normalize topic name
    topic_normalized = topic.lower().replace(" ", "-").replace("_", "-")

    content = loader.get_luau_doc(topic_normalized)
    if not content:
        # List available topics
        available = loader.get_luau_doc_topics()
        if available:
            return f"Topic '{topic}' not found. Available topics: {', '.join(available)}"
        return f"Luau docs not available. Try roblox_sync(force=True) to download."

    return format_luau_doc(topic, content)


@mcp.tool()
async def roblox_list_luau_topics() -> str:
    """
    List all available Luau language documentation topics.

    Returns:
        List of Luau documentation topics.
    """
    loader, _ = await ensure_initialized()

    topics = loader.get_luau_doc_topics()

    if not topics:
        return f"Luau docs not available. Available topics: {', '.join(LUAU_DOCS_TOPICS)}"

    lines = []
    lines.append("LUAU LANGUAGE DOCUMENTATION")
    lines.append("")
    lines.append("Available Topics:")
    lines.append("")

    for topic in sorted(topics):
        lines.append(f"  - {topic}")

    lines.append("")
    lines.append("Use roblox_get_luau_topic('topic') to read documentation.")
    lines.append("")
    lines.append("DOCS: https://create.roblox.com/docs/luau")

    return "\n".join(lines)


# ============================================================================
# DATATYPE TOOLS
# ============================================================================


@mcp.tool()
async def roblox_get_datatype(name: str) -> str:
    """
    Get Roblox datatype documentation (Vector3, CFrame, Color3, etc.).

    DataTypes are fundamental value types used throughout the Roblox API.
    Includes constructors, properties, methods, and math operations.

    Args:
        name: Name of the datatype (e.g., "Vector3", "CFrame", "Color3", "UDim2")

    Returns:
        Detailed datatype documentation.
    """
    loader, _ = await ensure_initialized()

    dt = loader.get_datatype(name)
    if not dt:
        # List available datatypes
        all_dts = loader.get_all_datatypes()
        if all_dts:
            names = [d.name for d in all_dts if name.lower() in d.name.lower()][:10]
            if names:
                return f"DataType '{name}' not found. Similar: {', '.join(names)}"
            return f"DataType '{name}' not found. Use roblox_list_datatypes() to see all."
        return f"DataTypes not available. Try roblox_sync(force=True) to download."

    return format_datatype(dt)


@mcp.tool()
async def roblox_list_datatypes() -> str:
    """
    List all available Roblox datatypes.

    DataTypes are fundamental value types like Vector3, CFrame, Color3, etc.

    Returns:
        List of all Roblox datatypes with summaries.
    """
    loader, _ = await ensure_initialized()

    datatypes = loader.get_all_datatypes()

    if not datatypes:
        return "DataTypes not available. Try roblox_sync(force=True) to download."

    return format_datatype_list(datatypes)


# ============================================================================
# LIBRARY TOOLS
# ============================================================================


@mcp.tool()
async def roblox_get_library(name: str) -> str:
    """
    Get Luau library documentation (math, string, table, etc.).

    Standard libraries provide built-in functions for common operations.

    Args:
        name: Name of the library (e.g., "math", "string", "table", "task")

    Returns:
        Detailed library documentation with all functions.
    """
    loader, _ = await ensure_initialized()

    lib = loader.get_library(name)
    if not lib:
        # List available libraries
        all_libs = loader.get_all_libraries()
        if all_libs:
            names = [l.name for l in all_libs]
            return f"Library '{name}' not found. Available: {', '.join(names)}"
        return f"Libraries not available. Try roblox_sync(force=True) to download."

    return format_library(lib)


@mcp.tool()
async def roblox_get_library_function(library: str, function: str) -> str:
    """
    Get specific library function details (e.g., math.clamp, string.split).

    Args:
        library: Name of the library (e.g., "math", "string", "table")
        function: Name of the function (e.g., "clamp", "split", "find")

    Returns:
        Detailed function documentation with parameters and return types.
    """
    loader, _ = await ensure_initialized()

    lib = loader.get_library(library)
    if not lib:
        all_libs = loader.get_all_libraries()
        if all_libs:
            names = [l.name for l in all_libs]
            return f"Library '{library}' not found. Available: {', '.join(names)}"
        return f"Libraries not available. Try roblox_sync(force=True) to download."

    return format_library_function(lib, function)


@mcp.tool()
async def roblox_list_libraries() -> str:
    """
    List all available Luau libraries.

    Standard libraries include math, string, table, os, task, etc.

    Returns:
        List of all Luau libraries with function counts.
    """
    loader, _ = await ensure_initialized()

    libraries = loader.get_all_libraries()

    if not libraries:
        return "Libraries not available. Try roblox_sync(force=True) to download."

    return format_library_list(libraries)


# ============================================================================
# DEPRECATION ALTERNATIVES MAPPING
# ============================================================================


def get_deprecation_alternatives(name: str, class_name: str | None) -> list[str]:
    """Get known alternatives for deprecated APIs."""

    # Class-level deprecations (comprehensive list)
    class_alternatives = {
        # Body movers -> Constraints
        "BodyPosition": ["AlignPosition (constraint-based)"],
        "BodyGyro": ["AlignOrientation (constraint-based)"],
        "BodyVelocity": ["LinearVelocity (constraint-based)"],
        "BodyForce": ["VectorForce (constraint-based)"],
        "BodyAngularVelocity": ["AngularVelocity (constraint-based)"],
        "BodyThrust": ["VectorForce (constraint-based)"],
        "RocketPropulsion": ["AlignPosition + AlignOrientation"],
        # Old GUI
        "Message": ["ScreenGui with TextLabel"],
        "Hint": ["ScreenGui with TextLabel"],
        # Effects -> ParticleEmitter
        "Sparkles": ["ParticleEmitter with sparkle texture"],
        "Fire": ["ParticleEmitter with fire texture"],
        "Smoke": ["ParticleEmitter with smoke texture"],
        # Selection -> Highlight
        "SelectionBox": ["Highlight (better performance)"],
        "SelectionSphere": ["Highlight (better performance)"],
        "SelectionPartLasso": ["Highlight"],
        "SelectionPointLasso": ["Highlight"],
        # Old input
        "HopperBin": ["Tool with ContextActionService"],
        "ButtonStyle": ["Use ImageButton with custom images"],
        # Terrain
        "TerrainRegion": ["Terrain:ReadVoxels/WriteVoxels"],
        # Data
        "DataStorePages": ["DataStoreService:ListDataStoresAsync"],
        "GlobalDataStore": ["DataStoreService:GetDataStore"],
        # Animation
        "KeyframeSequence": ["Animation with AnimationController"],
        # Legacy
        "DebuggerManager": ["Studio debugging tools"],
        "Status": ["Use Humanoid.DisplayDistanceType"],
        "PointsService": ["Custom leaderboard system"],
        "BadgeService": ["Use Open Cloud Badges API"],
        "InsertService": ["AssetService or Open Cloud Assets API"],
        "MarketplaceService.ProcessReceipt": ["Still works, use with caution"],
    }

    # Member-level deprecations (comprehensive list)
    member_alternatives = {
        # Instance
        ("Instance", "IsA"): ["Still works - this is correct usage"],
        ("Instance", "Changed"): ["GetPropertyChangedSignal for specific props"],
        ("Instance", "ChildAdded"): ["Still works, but consider DescendantAdded"],
        ("Instance", "children"): ["GetChildren()"],
        ("Instance", "Remove"): ["Destroy()"],
        ("Instance", "remove"): ["Destroy()"],
        ("Instance", "isDescendantOf"): ["IsDescendantOf (capitalized)"],
        # Players
        ("Players", "LocalPlayer"): ["Still works - correct for client scripts"],
        ("Players", "GetPlayerFromCharacter"): ["Still works, or use Humanoid.RootPart.Parent"],
        # Workspace
        ("Workspace", "FilteringEnabled"): ["Always true - remove this check"],
        ("Workspace", "DistributedGameTime"): ["Use os.clock() or tick()"],
        # BasePart physics
        ("BasePart", "Velocity"): ["AssemblyLinearVelocity"],
        ("BasePart", "RotVelocity"): ["AssemblyAngularVelocity"],
        ("BasePart", "GetMass"): ["AssemblyMass or Mass property"],
        ("BasePart", "MakeJoints"): ["WeldConstraint or Motor6D"],
        ("BasePart", "BreakJoints"): ["Destroy welds directly"],
        ("BasePart", "GetConnectedParts"): ["GetJoints() or Constraints folder"],
        ("BasePart", "CanCollideWith"): ["Use CollisionGroups"],
        # Humanoid
        ("Humanoid", "WalkSpeed"): ["Still works - correct usage"],
        ("Humanoid", "LoadAnimation"): ["Use Animator:LoadAnimation instead"],
        ("Humanoid", "GetPlayingAnimationTracks"): ["Animator:GetPlayingAnimationTracks"],
        ("Humanoid", "EquipTool"): ["Still works, or use Tool.Parent = character"],
        ("Humanoid", "UnequipTools"): ["Still works, or set Tool.Parent = Backpack"],
        # Model
        ("Model", "GetPrimaryPartCFrame"): ["PrimaryPart.CFrame or Model:GetPivot()"],
        ("Model", "SetPrimaryPartCFrame"): ["Model:PivotTo() (preferred)"],
        ("Model", "GetModelSize"): ["Model:GetExtentsSize()"],
        ("Model", "GetModelCFrame"): ["Model:GetPivot() or GetBoundingBox()"],
        ("Model", "BreakJoints"): ["Destroy joints individually"],
        ("Model", "MakeJoints"): ["Use WeldConstraint or Motor6D"],
        # Camera
        ("Camera", "CoordinateFrame"): ["Camera.CFrame"],
        ("Camera", "Focus"): ["Camera.Focus (still works)"],
        # Sound
        ("Sound", "PlaybackLoudness"): ["Still works for visualization"],
        ("Sound", "IsPaused"): ["Check Sound.Playing and Sound.TimePosition"],
        # TweenService
        ("TweenService", "GetValue"): ["Use TweenInfo and create tween"],
        # Lighting
        ("Lighting", "GetMinutesAfterMidnight"): ["Lighting.ClockTime * 60"],
        ("Lighting", "SetMinutesAfterMidnight"): ["Lighting.ClockTime = minutes/60"],
        # DataStore
        ("GlobalDataStore", "IncrementAsync"): ["Use UpdateAsync for atomic ops"],
        # Misc
        ("StarterGui", "ShowDevelopmentGui"): ["StarterGui:SetCoreGuiEnabled"],
        ("GuiService", "GetEmotesMenuOpen"): ["Use PlayerModule for emotes"],
        ("RunService", "renderStepped"): ["RenderStepped (capitalized) or Heartbeat"],
        ("RunService", "stepped"): ["Stepped (capitalized) or Heartbeat"],
    }

    if class_name:
        return member_alternatives.get((class_name, name), [])
    else:
        return class_alternatives.get(name, [])


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================


def main():
    """Main entry point for the MCP server."""
    logger.info("Starting MCP Roblox Docs server...")

    # Run the server
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
