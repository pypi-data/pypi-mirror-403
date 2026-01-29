"""Centralized cache management for Escape using ~/.cache/escape/."""

import gzip
import json
import os
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path
from typing import Any

from escape._internal.logger import logger


class CacheManager:
    """Manages cache directories for Escape resources and generated files."""

    def __init__(self, base_path: Path | None = None):
        """Initialize cache manager with optional custom base path."""
        if base_path is None:
            # Use XDG_CACHE_HOME if set, otherwise default to ~/.cache
            xdg_cache = os.getenv("XDG_CACHE_HOME")
            if xdg_cache:
                self.base_path = Path(xdg_cache) / "escape"
            else:
                self.base_path = Path.home() / ".cache" / "escape"
        else:
            self.base_path = Path(base_path)

        # Define standard cache directories
        self.generated_dir = self.base_path / "generated"
        self.data_dir = self.base_path / "data"
        self.objects_dir = self.data_dir / "objects"
        self.varps_dir = self.data_dir / "varps"

    def ensure_dirs(self) -> None:
        """Create all cache directories if they don't exist."""
        self.generated_dir.mkdir(parents=True, exist_ok=True)
        self.objects_dir.mkdir(parents=True, exist_ok=True)
        self.varps_dir.mkdir(parents=True, exist_ok=True)

    def get_generated_path(self, filename: str) -> Path:
        """Get path for a generated file."""
        return self.generated_dir / filename

    def get_objects_path(self) -> Path:
        """Get path for objects data directory."""
        return self.objects_dir

    def get_varps_path(self) -> Path:
        """Get path for varps data directory."""
        return self.varps_dir

    def get_data_path(self, resource_type: str) -> Path:
        """Get path for a specific resource type."""
        return self.data_dir / resource_type

    def clear_cache(self) -> None:
        """Clear all cached files (use with caution)."""
        import shutil

        if self.base_path.exists():
            shutil.rmtree(self.base_path)

    def get_cache_size(self) -> int:
        """Get total size of cache in bytes."""
        total = 0
        if self.base_path.exists():
            for path in self.base_path.rglob("*"):
                if path.is_file():
                    total += path.stat().st_size
        return total


# Global cache manager instance
_cache_manager: CacheManager | None = None


def get_cache_manager() -> CacheManager:
    """Get global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
        _cache_manager.ensure_dirs()
    return _cache_manager


# Base URL for game resources
BASE_URL = "https://data.os-escape.com"
GRAPH_URL = "https://data.os-escape.com/resources/graph_data.zip"

# Track if resources have been loaded this session
_resources_loaded = False


def _download_file(url: str, dest: Path, decompress_gz: bool = True) -> bool:
    """Download a file from URL to destination."""
    try:
        logger.info(f"Downloading {url}")

        # Create request with cache-busting headers
        req = urllib.request.Request(url)
        req.add_header("Cache-Control", "no-cache, no-store, must-revalidate")
        req.add_header("Pragma", "no-cache")
        req.add_header("Expires", "0")

        with urllib.request.urlopen(req, timeout=30) as response:
            data = response.read()

            # Handle gzip decompression
            if decompress_gz and url.endswith(".gz"):
                # Write compressed file temporarily
                gz_file = dest.with_suffix(dest.suffix + ".gz")
                with open(gz_file, "wb") as f:
                    f.write(data)

                logger.info(f"Downloaded: {gz_file.stat().st_size:,} bytes")

                # Decompress to working file
                logger.info(f"Decompressing {gz_file.name}")
                with gzip.open(gz_file, "rb") as f_in, open(dest, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)

                logger.success(f"Decompressed: {dest.stat().st_size:,} bytes")

                # Delete the .gz file after decompression
                gz_file.unlink()
                logger.info("Removed compressed file")
            else:
                # Write directly
                with open(dest, "wb") as f:
                    f.write(data)
                logger.success(f"Downloaded: {dest.stat().st_size:,} bytes")

        return True

    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False


def _download_and_extract_zip(url: str, extract_dir: Path) -> bool:
    """Download a zip file and extract it to a directory."""
    try:
        logger.info(f"Downloading {url}")

        # Create request with cache-busting headers
        req = urllib.request.Request(url)
        req.add_header("Cache-Control", "no-cache, no-store, must-revalidate")
        req.add_header("Pragma", "no-cache")
        req.add_header("Expires", "0")

        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()

        # Write to temp zip file
        zip_path = extract_dir.parent / "temp_download.zip"
        with open(zip_path, "wb") as f:
            f.write(data)
        logger.info(f"Downloaded: {zip_path.stat().st_size:,} bytes")

        # Clear existing extract directory if it exists
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(parents=True, exist_ok=True)

        # Extract zip contents
        logger.info(f"Extracting to {extract_dir}")
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(extract_dir)
        logger.success(f"Extracted {len(list(extract_dir.rglob('*')))} files")

        # Clean up zip file
        zip_path.unlink()
        logger.info("Removed zip file")

        return True

    except Exception as e:
        logger.error(f"Failed to download/extract {url}: {e}")
        return False


def _get_remote_metadata() -> dict | None:
    """Fetch remote metadata to check current revision."""
    url = f"{BASE_URL}/varps/latest/metadata.json"
    try:
        req = urllib.request.Request(url)
        req.add_header("Cache-Control", "no-cache")
        with urllib.request.urlopen(req, timeout=10) as response:
            data = response.read()
            return json.loads(data)
    except Exception as e:
        logger.warning(f"Failed to fetch remote metadata: {e}")
        return None


def _needs_update(cache_dir: Path) -> bool:
    """Check if resources need updating."""
    # Check if files exist
    required_files = ["metadata.json", "varps.json", "varbits.json", "objects.db"]
    required_dirs = ["graph"]
    if not all((cache_dir / f).exists() for f in required_files):
        logger.info("Resources not found locally, downloading")
        return True
    if not all((cache_dir / d).is_dir() for d in required_dirs):
        print("🔄 Graph data not found locally, downloading...")
        return True

    # Get remote metadata
    remote_meta = _get_remote_metadata()
    if remote_meta is None:
        # Can't reach server, use cached data if available
        return False

    # Get local metadata
    metadata_file = cache_dir / "metadata.json"
    try:
        with open(metadata_file) as f:
            local_meta = json.load(f)
    except Exception:
        return True

    # Compare revisions
    remote_revision = remote_meta.get("cache_id") or remote_meta.get("revision")
    local_revision = local_meta.get("cache_id") or local_meta.get("revision")

    if remote_revision and local_revision and remote_revision != local_revision:
        logger.info(f"New revision available: {local_revision} → {remote_revision}")
        return True

    return False


def ensure_resources_loaded() -> bool:
    """Ensure game resources are downloaded and loaded."""
    global _resources_loaded

    if _resources_loaded:
        return True

    try:
        cache_manager = get_cache_manager()
        cache_dir = cache_manager.get_data_path("game_data")
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Check if update needed
        if _needs_update(cache_dir):
            logger.info("Updating game resources")
            base_url = f"{BASE_URL}/varps/latest"

            # Download all files
            files = {
                "metadata.json": "metadata.json",
                "varps.json": "varps.json",
                "varbits.json": "varbits.json",
                "objects.db": "objects.db.gz",  # Compressed
            }

            for local_name, remote_name in files.items():
                url = f"{base_url}/{remote_name}"
                dest = cache_dir / local_name
                decompress = remote_name.endswith(".gz")

                if not _download_file(url, dest, decompress_gz=decompress):
                    logger.warning(f"Failed to download {local_name}")
                    return False

            # Download and extract graph data
            graph_dir = cache_dir / "graph"
            if not _download_and_extract_zip(GRAPH_URL, graph_dir):
                logger.warning("Failed to download graph data")
                return False

            logger.success("Resources downloaded successfully")

        # Load resources into modules
        from escape._internal.resources import objects, varps

        # Load varps/varbits data
        varps_file = cache_dir / "varps.json"
        varbits_file = cache_dir / "varbits.json"

        with open(varps_file) as f:
            raw_varps = json.load(f)
            # Convert list to dict indexed by ID
            if isinstance(raw_varps, list):
                varps_data = {item["id"]: item for item in raw_varps if "id" in item}
            else:
                varps_data = raw_varps
            varps.set_varps_data(varps_data)
            logger.success(f"Loaded {varps.get_varps_data_count()} varps")

        with open(varbits_file) as f:
            raw_varbits = json.load(f)
            # Convert list to dict indexed by ID
            if isinstance(raw_varbits, list):
                varbits_data = {item["id"]: item for item in raw_varbits if "id" in item}
            else:
                varbits_data = raw_varbits
            varps.set_varbits_data(varbits_data)
            logger.success(f"Loaded {varps.get_varbits_data_count()} varbits")

        # Load objects database
        import sqlite3

        db_file = cache_dir / "objects.db"
        db_conn = sqlite3.connect(str(db_file))
        objects.set_db_connection(db_conn)
        logger.success("Loaded objects database")

        _resources_loaded = True
        return True

    except Exception as e:
        logger.error(f"Failed to load resources: {e}")
        import traceback

        traceback.print_exc()
        return False


def ensure_generated_in_path() -> Path:
    """Ensure the generated cache directory is in sys.path for imports."""
    cache_manager = get_cache_manager()
    generated_dir = cache_manager.generated_dir

    # Add to sys.path if not already there
    generated_str = str(generated_dir)
    if generated_str not in sys.path:
        sys.path.insert(0, generated_str)

    return generated_dir


def load_generated_module(module_name: str) -> Any | None:
    """Load a generated module from cache."""
    ensure_generated_in_path()

    try:
        # Try to import the module
        import importlib

        return importlib.import_module(module_name)
    except ImportError:
        return None


def reload_generated_module(module_name: str) -> Any | None:
    """Reload a generated module after regeneration."""
    ensure_generated_in_path()

    try:
        import importlib

        if module_name in sys.modules:
            return importlib.reload(sys.modules[module_name])
        else:
            return importlib.import_module(module_name)
    except ImportError:
        return None


def has_generated_files() -> bool:
    """Check if generated files exist in cache."""
    cache_manager = get_cache_manager()
    generated_dir = cache_manager.generated_dir

    constants_file = generated_dir / "constants.py"

    return constants_file.exists()


def ensure_generated_files():
    """Ensure generated files exist, triggering update if necessary."""
    if not has_generated_files():
        logger.warning("Generated files not found in cache, running updater")
        try:
            from escape._internal.updater.api import RuneLiteAPIUpdater

            updater = RuneLiteAPIUpdater()
            success = updater.update(force=False, max_age_days=7)

            if not success or not has_generated_files():
                raise FileNotFoundError(
                    "Failed to generate required files. "
                    "Run 'python -m escape._internal.updater --force' manually."
                )
        except Exception as e:
            raise FileNotFoundError(
                f"Could not generate required files: {e}\n"
                f"Run 'python -m escape._internal.updater --force' manually."
            ) from e


# Initialize on import - ensure generated path is available
ensure_generated_in_path()
