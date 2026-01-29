"""
Output Formatter - Formats API data for readable output.

Provides consistent, well-formatted output for all tools.
"""

from __future__ import annotations

from typing import Any


def format_class(
    cls: dict[str, Any],
    docs: dict[str, Any] | None = None,
    include_members: bool = True,
    member_limit: int = 50,
) -> str:
    """Format a class for display."""
    name = cls.get("Name", "Unknown")
    superclass = cls.get("Superclass", "")
    tags = cls.get("Tags", [])
    members = cls.get("Members", [])

    lines = []

    # Header
    lines.append(f"CLASS: {name}")
    if superclass and superclass != "<<<ROOT>>>":
        lines.append(f"Inherits: {superclass}")

    # Tags
    if tags:
        tag_str = ", ".join(tags)
        lines.append(f"Tags: {tag_str}")

    # Description from docs
    if docs:
        desc = docs.get("description", "")
        if desc:
            lines.append("")
            lines.append("DESCRIPTION:")
            # Wrap description
            words = desc.split()
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 > 80:
                    lines.append(current_line)
                    current_line = word
                else:
                    current_line = f"{current_line} {word}".strip()
            if current_line:
                lines.append(current_line)

    if include_members and members:
        # Group members by type
        properties = [m for m in members if m.get("MemberType") == "Property"]
        methods = [m for m in members if m.get("MemberType") in ("Method", "Function")]
        events = [m for m in members if m.get("MemberType") == "Event"]
        callbacks = [m for m in members if m.get("MemberType") == "Callback"]

        if properties:
            lines.append("")
            lines.append(f"PROPERTIES ({len(properties)}):")
            for prop in properties[:member_limit]:
                lines.append(format_property(prop))

        if methods:
            lines.append("")
            lines.append(f"METHODS ({len(methods)}):")
            for method in methods[:member_limit]:
                lines.append(format_method(method))

        if events:
            lines.append("")
            lines.append(f"EVENTS ({len(events)}):")
            for event in events[:member_limit]:
                lines.append(format_event(event))

        if callbacks:
            lines.append("")
            lines.append(f"CALLBACKS ({len(callbacks)}):")
            for callback in callbacks[:member_limit]:
                lines.append(format_callback(callback))

    # Documentation link
    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/reference/engine/classes/{name}")

    return "\n".join(lines)


def format_property(prop: dict[str, Any]) -> str:
    """Format a property member."""
    name = prop.get("Name", "Unknown")
    value_type = prop.get("ValueType", {})
    type_name = (
        value_type.get("Name", "unknown") if isinstance(value_type, dict) else str(value_type)
    )
    tags = prop.get("Tags", [])

    tag_str = ""
    if tags:
        important_tags = [
            t for t in tags if t in ["ReadOnly", "Deprecated", "NotReplicated", "Hidden"]
        ]
        if important_tags:
            tag_str = f" [{', '.join(important_tags)}]"

    security = prop.get("Security", {})
    if isinstance(security, dict):
        read_sec = security.get("Read", "None")
        write_sec = security.get("Write", "None")
        if read_sec != "None" or write_sec != "None":
            tag_str += f" (Security: R={read_sec}, W={write_sec})"

    return f"  {name}: {type_name}{tag_str}"


def format_method(method: dict[str, Any]) -> str:
    """Format a method member."""
    name = method.get("Name", "Unknown")
    params = method.get("Parameters", [])
    return_type = method.get("ReturnType", {})
    return_name = return_type.get("Name", "void") if isinstance(return_type, dict) else "void"
    tags = method.get("Tags", [])

    # Format parameters
    param_parts = []
    for p in params:
        p_name = p.get("Name", "arg")
        p_type = p.get("Type", {})
        p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
        param_parts.append(f"{p_name}: {p_type_name}")

    param_str = ", ".join(param_parts)

    tag_str = ""
    if "Deprecated" in tags:
        tag_str = " [Deprecated]"
    if "Yields" in tags:
        tag_str += " [Yields]"

    return f"  {name}({param_str}) -> {return_name}{tag_str}"


def format_event(event: dict[str, Any]) -> str:
    """Format an event member."""
    name = event.get("Name", "Unknown")
    params = event.get("Parameters", [])
    tags = event.get("Tags", [])

    # Format parameters
    param_parts = []
    for p in params:
        p_name = p.get("Name", "arg")
        p_type = p.get("Type", {})
        p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
        param_parts.append(f"{p_name}: {p_type_name}")

    param_str = ", ".join(param_parts) if param_parts else ""

    tag_str = ""
    if "Deprecated" in tags:
        tag_str = " [Deprecated]"

    return f"  {name}({param_str}){tag_str}"


def format_callback(callback: dict[str, Any]) -> str:
    """Format a callback member."""
    name = callback.get("Name", "Unknown")
    params = callback.get("Parameters", [])
    return_type = callback.get("ReturnType", {})
    return_name = return_type.get("Name", "void") if isinstance(return_type, dict) else "void"

    param_parts = []
    for p in params:
        p_name = p.get("Name", "arg")
        p_type = p.get("Type", {})
        p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
        param_parts.append(f"{p_name}: {p_type_name}")

    param_str = ", ".join(param_parts)

    return f"  {name}({param_str}) -> {return_name}"


def format_enum(enum: dict[str, Any]) -> str:
    """Format an enum for display."""
    name = enum.get("Name", "Unknown")
    items = enum.get("Items", [])

    lines = []
    lines.append(f"ENUM: {name}")
    lines.append(f"Values ({len(items)} items):")
    lines.append("")

    # Sort by value
    sorted_items = sorted(items, key=lambda x: x.get("Value", 0))

    for item in sorted_items:
        item_name = item.get("Name", "Unknown")
        item_value = item.get("Value", 0)
        lines.append(f"  {item_name} = {item_value}")

    lines.append("")
    lines.append(f"DOCS: https://create.roblox.com/docs/reference/engine/enums/{name}")

    return "\n".join(lines)


def format_member(
    member: dict[str, Any], class_name: str, docs: dict[str, Any] | None = None
) -> str:
    """Format a single member with full details."""
    name = member.get("Name", "Unknown")
    member_type = member.get("MemberType", "Unknown")
    tags = member.get("Tags", [])
    security = member.get("Security", {})

    lines = []

    # Header
    lines.append(f"{member_type.upper()}: {class_name}.{name}")

    # Tags
    if tags:
        lines.append(f"Tags: {', '.join(tags)}")

    # Type-specific details
    if member_type == "Property":
        value_type = member.get("ValueType", {})
        type_name = (
            value_type.get("Name", "unknown") if isinstance(value_type, dict) else str(value_type)
        )
        lines.append(f"Type: {type_name}")

        if isinstance(security, dict):
            lines.append(f"Read: {security.get('Read', 'None')}")
            lines.append(f"Write: {security.get('Write', 'None')}")

        default = member.get("Default")
        if default is not None:
            lines.append(f"Default: {default}")

    elif member_type in ("Method", "Function"):
        params = member.get("Parameters", [])
        return_type = member.get("ReturnType", {})
        return_name = return_type.get("Name", "void") if isinstance(return_type, dict) else "void"

        lines.append(f"Returns: {return_name}")

        if params:
            lines.append("Parameters:")
            for p in params:
                p_name = p.get("Name", "arg")
                p_type = p.get("Type", {})
                p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
                p_default = p.get("Default")
                default_str = f" = {p_default}" if p_default is not None else ""
                lines.append(f"  {p_name}: {p_type_name}{default_str}")

        if "Yields" in tags:
            lines.append("Note: This method yields (async)")

    elif member_type == "Event":
        params = member.get("Parameters", [])
        if params:
            lines.append("Event Parameters:")
            for p in params:
                p_name = p.get("Name", "arg")
                p_type = p.get("Type", {})
                p_type_name = p_type.get("Name", "any") if isinstance(p_type, dict) else "any"
                lines.append(f"  {p_name}: {p_type_name}")

    # Description from docs
    if docs:
        desc = docs.get(name, {}).get("description", "")
        if desc:
            lines.append("")
            lines.append("DESCRIPTION:")
            lines.append(desc[:500])

    # Deprecation warning
    if "Deprecated" in tags:
        lines.append("")
        lines.append("WARNING: This member is deprecated!")

    lines.append("")
    lines.append(
        f"DOCS: https://create.roblox.com/docs/reference/engine/classes/{class_name}#{name}"
    )

    return "\n".join(lines)


def format_deprecation(
    name: str,
    is_class: bool,
    is_deprecated: bool,
    class_name: str | None = None,
    tags: list[str] | None = None,
    alternatives: list[str] | None = None,
) -> str:
    """Format deprecation status."""
    lines = []

    if is_class:
        full_name = name
    else:
        full_name = f"{class_name}.{name}" if class_name else name

    if is_deprecated:
        lines.append(f"DEPRECATED: {full_name}")
        lines.append("")
        lines.append("Status: This API is deprecated and should not be used in new code.")

        if alternatives:
            lines.append("")
            lines.append("Recommended Alternatives:")
            for alt in alternatives:
                lines.append(f"  - {alt}")

        if tags:
            other_tags = [t for t in tags if t != "Deprecated"]
            if other_tags:
                lines.append(f"Other Tags: {', '.join(other_tags)}")
    else:
        lines.append(f"NOT DEPRECATED: {full_name}")
        lines.append("")
        lines.append("Status: This API is current and safe to use.")

        if tags:
            lines.append(f"Tags: {', '.join(tags)}")

    return "\n".join(lines)


def format_search_results(results: list[Any], query: str) -> str:
    """Format search results."""
    if not results:
        return f"No results found for '{query}'"

    lines = []
    lines.append(f"Search results for '{query}' ({len(results)} found):")
    lines.append("")

    for i, result in enumerate(results, 1):
        type_icon = {"class": "[C]", "member": "[M]", "enum": "[E]"}.get(result.type, "[?]")

        if result.class_name:
            name = f"{result.class_name}.{result.name}"
        else:
            name = result.name

        tag_str = ""
        if result.tags:
            important = [t for t in result.tags if t in ["Deprecated", "Service", "NotCreatable"]]
            if important:
                tag_str = f" [{', '.join(important)}]"

        lines.append(f"{i:2}. {type_icon} {name}{tag_str}")
        lines.append(f"      {result.description}")

    return "\n".join(lines)


def format_inheritance(class_name: str, chain: list[str], subclasses: list[str]) -> str:
    """Format class inheritance hierarchy."""
    lines = []

    lines.append(f"INHERITANCE: {class_name}")
    lines.append("")

    # Ancestors
    lines.append("Inheritance Chain (ancestors):")
    for i, ancestor in enumerate(chain):
        indent = "  " * i
        arrow = "-> " if i > 0 else ""
        marker = " <-- (this class)" if ancestor == class_name else ""
        lines.append(f"{indent}{arrow}{ancestor}{marker}")

    # Subclasses
    if subclasses:
        lines.append("")
        lines.append(f"Direct Subclasses ({len(subclasses)}):")
        for sub in sorted(subclasses)[:30]:
            lines.append(f"  - {sub}")
        if len(subclasses) > 30:
            lines.append(f"  ... and {len(subclasses) - 30} more")

    return "\n".join(lines)


def format_services(services: list[dict[str, Any]]) -> str:
    """Format list of services."""
    lines = []

    lines.append(f"ROBLOX SERVICES ({len(services)} total)")
    lines.append("")
    lines.append("Services are singleton objects that provide core functionality:")
    lines.append("")

    for service in sorted(services, key=lambda s: s.get("Name", "")):
        name = service.get("Name", "Unknown")
        tags = service.get("Tags", [])

        tag_str = ""
        if "Deprecated" in tags:
            tag_str = " [Deprecated]"
        elif "NotCreatable" in tags:
            tag_str = " [Singleton]"

        lines.append(f"  - {name}{tag_str}")

    lines.append("")
    lines.append("Access services with: game:GetService('ServiceName')")

    return "\n".join(lines)
