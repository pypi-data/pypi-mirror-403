"""
Data Syncer - Downloads and updates Roblox API data from GitHub sources.

Data Sources (all FREE):
- API-Dump.json: Complete API structure (classes, members, enums)
- api-docs/{lang}.json: Human-readable descriptions
- version.txt: Version tracking for incremental sync
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import httpx
import orjson

logger = logging.getLogger(__name__)

# GitHub raw URLs for Roblox Client Tracker
GITHUB_RAW_BASE = "https://raw.githubusercontent.com/MaximumADHD/Roblox-Client-Tracker/roblox"

SOURCES = {
    "api_dump": f"{GITHUB_RAW_BASE}/API-Dump.json",
    "full_api_dump": f"{GITHUB_RAW_BASE}/Full-API-Dump.json",
    "version": f"{GITHUB_RAW_BASE}/version.txt",
    "version_guid": f"{GITHUB_RAW_BASE}/version-guid.txt",
}

# Language codes available in api-docs
AVAILABLE_LANGUAGES = [
    "en-us",
    "de-de",
    "es-es",
    "fr-fr",
    "id-id",
    "it-it",
    "ja-jp",
    "ko-kr",
    "pl-pl",
    "pt-br",
    "th-th",
    "tr-tr",
    "vi-vn",
    "zh-cn",
    "zh-tw",
]


def get_api_docs_url(lang: str = "en-us") -> str:
    """Get the URL for API docs in a specific language."""
    if lang not in AVAILABLE_LANGUAGES:
        lang = "en-us"
    return f"{GITHUB_RAW_BASE}/api-docs/{lang}.json"


class DataSyncer:
    """Handles downloading and caching of Roblox API data."""

    def __init__(self, cache_dir: Path, language: str = "en-us"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.language = language if language in AVAILABLE_LANGUAGES else "en-us"
        self.meta_path = self.cache_dir / "meta.json"
        self._client: httpx.AsyncClient | None = None

    @property
    def api_dump_path(self) -> Path:
        return self.cache_dir / "api-dump.json"

    @property
    def api_docs_path(self) -> Path:
        return self.cache_dir / f"api-docs-{self.language}.json"

    @property
    def full_api_dump_path(self) -> Path:
        return self.cache_dir / "full-api-dump.json"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(60.0, connect=10.0),
                follow_redirects=True,
                headers={"User-Agent": "mcp-roblox-docs/1.0"},
            )
        return self._client

    async def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _load_meta(self) -> dict[str, Any]:
        """Load sync metadata."""
        if self.meta_path.exists():
            try:
                return orjson.loads(self.meta_path.read_bytes())
            except Exception:
                pass
        return {}

    def _save_meta(self, meta: dict[str, Any]) -> None:
        """Save sync metadata."""
        self.meta_path.write_bytes(orjson.dumps(meta, option=orjson.OPT_INDENT_2))

    async def get_remote_version(self) -> str | None:
        """Fetch current Roblox version from GitHub."""
        try:
            client = await self._get_client()
            response = await client.get(SOURCES["version"])
            response.raise_for_status()
            return response.text.strip()
        except Exception as e:
            logger.warning(f"Failed to fetch remote version: {e}")
            return None

    def get_local_version(self) -> str | None:
        """Get locally cached version."""
        meta = self._load_meta()
        return meta.get("version")

    async def needs_sync(self, force: bool = False) -> bool:
        """Check if data needs to be synced."""
        if force:
            return True

        # Check if cache exists
        if not self.api_dump_path.exists():
            logger.info("No cached data found, sync required")
            return True

        meta = self._load_meta()

        # Check sync age
        last_sync = meta.get("last_sync")
        if last_sync:
            last_sync_time = datetime.fromisoformat(last_sync)
            age_hours = (datetime.now(timezone.utc) - last_sync_time).total_seconds() / 3600
            if age_hours > 24:
                logger.info(f"Cache is {age_hours:.1f} hours old, checking for updates")
                # Check version
                remote_version = await self.get_remote_version()
                local_version = meta.get("version")
                if remote_version and remote_version != local_version:
                    logger.info(f"New version available: {remote_version} (was: {local_version})")
                    return True

        return False

    async def _download_file(self, url: str, dest: Path) -> bool:
        """Download a file from URL to destination."""
        try:
            client = await self._get_client()
            logger.info(f"Downloading {url}")
            response = await client.get(url)
            response.raise_for_status()
            dest.write_bytes(response.content)
            logger.info(f"Saved to {dest} ({len(response.content):,} bytes)")
            return True
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return False

    async def sync(self, force: bool = False) -> bool:
        """
        Sync data from remote sources.

        Returns True if sync was successful.
        """
        if not await self.needs_sync(force):
            logger.info("Data is up to date, skipping sync")
            return True

        logger.info("Starting data sync...")
        success = True

        # Download API dump (required)
        if not await self._download_file(SOURCES["api_dump"], self.api_dump_path):
            success = False

        # Download API docs for current language
        docs_url = get_api_docs_url(self.language)
        if not await self._download_file(docs_url, self.api_docs_path):
            logger.warning(f"Failed to download docs for {self.language}, trying en-us")
            if self.language != "en-us":
                docs_url = get_api_docs_url("en-us")
                await self._download_file(docs_url, self.cache_dir / "api-docs-en-us.json")

        # Download full API dump (optional, for default values)
        await self._download_file(SOURCES["full_api_dump"], self.full_api_dump_path)

        # Get version info
        remote_version = await self.get_remote_version()

        # Update metadata
        meta = {
            "version": remote_version,
            "last_sync": datetime.now(timezone.utc).isoformat(),
            "language": self.language,
            "sources": list(SOURCES.keys()),
        }
        self._save_meta(meta)

        await self.close()

        if success:
            logger.info(f"Sync complete! Version: {remote_version}")
        else:
            logger.warning("Sync completed with some errors")

        return success

    async def sync_language(self, lang: str) -> bool:
        """Download API docs for a specific language."""
        if lang not in AVAILABLE_LANGUAGES:
            logger.error(f"Unknown language: {lang}")
            return False

        dest = self.cache_dir / f"api-docs-{lang}.json"
        url = get_api_docs_url(lang)
        return await self._download_file(url, dest)

    def get_available_languages(self) -> list[str]:
        """Get list of available language codes."""
        return AVAILABLE_LANGUAGES.copy()

    def get_cached_languages(self) -> list[str]:
        """Get list of languages that are already cached."""
        cached = []
        for lang in AVAILABLE_LANGUAGES:
            if (self.cache_dir / f"api-docs-{lang}.json").exists():
                cached.append(lang)
        return cached


async def main():
    """CLI entry point for manual sync."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    cache_dir = Path(__file__).parent.parent.parent / "cache"
    syncer = DataSyncer(cache_dir, language="en-us")

    # Also download Indonesian for multi-language support
    await syncer.sync(force=True)
    await syncer.sync_language("id-id")

    print(f"Sync complete! Cache directory: {cache_dir}")


if __name__ == "__main__":
    asyncio.run(main())
