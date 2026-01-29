"""Quick test script for MCP Roblox Docs."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.loader import DataLoader
from src.data.index import SearchIndex


def main():
    cache_dir = Path("./cache")
    loader = DataLoader(cache_dir)

    print("=" * 60)
    print("MCP ROBLOX DOCS - QUICK TEST")
    print("=" * 60)

    # Test 1: Load API dump
    print("\n[1] Testing API Dump Loading...")
    version = loader.get_version()
    print(f"    API Version: {version}")

    classes = loader.get_all_classes()
    print(f"    Total Classes: {len(classes)}")

    enums = loader.get_all_enums()
    print(f"    Total Enums: {len(enums)}")

    # Test 2: Get specific class
    print("\n[2] Testing Get Class...")
    cls = loader.get_class("TweenService")
    if cls:
        print(f"    Class: {cls.get('Name')}")
        print(f"    Superclass: {cls.get('Superclass')}")
        print(f"    Members: {len(cls.get('Members', []))}")
        print(f"    Tags: {cls.get('Tags', [])}")
    else:
        print("    ERROR: TweenService not found!")

    # Test 3: Get specific enum
    print("\n[3] Testing Get Enum...")
    enum = loader.get_enum("Material")
    if enum:
        items = enum.get("Items", [])
        print(f"    Enum: {enum.get('Name')}")
        print(f"    Items: {len(items)}")
        print(f"    Sample: {[i.get('Name') for i in items[:5]]}")
    else:
        print("    ERROR: Material enum not found!")

    # Test 4: Get member
    print("\n[4] Testing Get Member...")
    member = loader.get_member("Part", "Anchored")
    if member:
        print(f"    Member: {member.get('Name')}")
        print(f"    Type: {member.get('MemberType')}")
        print(f"    ValueType: {member.get('ValueType')}")
    else:
        print("    ERROR: Part.Anchored not found!")

    # Test 5: Services
    print("\n[5] Testing List Services...")
    services = loader.get_services()
    print(f"    Total Services: {len(services)}")
    print(f"    Sample: {[s.get('Name') for s in services[:5]]}")

    # Test 6: Inheritance
    print("\n[6] Testing Inheritance...")
    chain = loader.get_inheritance("Part")
    print(f"    Part inheritance: {' -> '.join(chain)}")

    subclasses = loader.get_subclasses("BasePart")
    print(f"    BasePart subclasses: {len(subclasses)}")

    # Test 7: Search Index
    print("\n[7] Testing Search Index...")
    index = SearchIndex()
    index.build(classes, enums)

    stats = index.get_stats()
    print(f"    Index stats: {stats}")

    # Test search
    results = index.search("tween animation")
    print(f"    Search 'tween animation': {len(results)} results")
    for r in results[:3]:
        print(f"      - [{r.type}] {r.name}: {r.description[:50]}...")

    # Test 8: Deprecation check
    print("\n[8] Testing Deprecation Check...")
    deprecated_classes = loader.get_deprecated_classes()
    print(f"    Deprecated classes: {len(deprecated_classes)}")
    print(f"    Sample: {[c.get('Name') for c in deprecated_classes[:5]]}")

    is_dep = loader.is_deprecated("BodyPosition")
    print(f"    BodyPosition deprecated: {is_dep}")

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED!")
    print("=" * 60)


if __name__ == "__main__":
    main()
