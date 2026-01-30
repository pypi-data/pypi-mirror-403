#!/usr/bin/env python3
"""Automatic RuneLite API updater for downloading, version checking, and API data regeneration."""

import json
import shutil
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path

from escape._internal.logger import logger


class RuneLiteAPIUpdater:
    """Manages RuneLite API data downloading, version checking, and regeneration."""

    def __init__(self, project_root: Path | None = None):
        """Initialize updater with cache manager paths."""
        # Use cache manager for all paths
        from ..cache_manager import get_cache_manager

        cache_manager = get_cache_manager()
        self.data_dir = cache_manager.get_data_path("api")
        self.temp_dir = self.data_dir / "temp"  # Temporary download location
        self.api_data_file = self.data_dir / "runelite_api_data.json"
        self.version_file = self.data_dir / "runelite_version.json"

        # Store cache manager reference for proxy generation
        self.cache_manager = cache_manager

        # GitHub API URLs
        self.github_api_url = "https://api.github.com/repos/runelite/runelite"
        self.download_url = "https://github.com/runelite/runelite/archive/refs/heads/master.zip"

        # Ensure data directory exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def get_current_version(self) -> dict | None:
        """Get currently installed version info"""
        if not self.version_file.exists():
            return None

        try:
            with open(self.version_file) as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Could not read version file: {e}")
            return None

    def get_latest_github_version(self) -> dict | None:
        """Get latest commit info from GitHub."""
        try:
            req = urllib.request.Request(
                f"{self.github_api_url}/commits/master",
                headers={"Accept": "application/vnd.github.v3+json"},
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())

            return {
                "sha": data["sha"],
                "date": data["commit"]["committer"]["date"],
                "message": data["commit"]["message"].split("\n")[0],  # First line only
                "author": data["commit"]["author"]["name"],
            }

        except urllib.error.URLError as e:
            logger.warning(f"Could not fetch GitHub version: {e}")
            logger.info("(Continuing with cached data if available)")
            return None
        except Exception as e:
            logger.warning(f"Error parsing GitHub response: {e}")
            return None

    def should_update(self, force: bool = False, max_age_days: int = 7) -> tuple[bool, str]:
        """Determine if update is needed based on force flag, age, or new commits."""
        if force:
            return True, "Forced update requested"

        # Check if API data exists
        if not self.api_data_file.exists():
            return True, "API data not found"

        # Get current version
        current = self.get_current_version()
        if not current:
            return True, "No version info found"

        # Check age
        try:
            last_update = datetime.fromisoformat(current.get("updated_at", "1970-01-01"))
            age = datetime.now() - last_update
            if age > timedelta(days=max_age_days):
                return True, f"Data is {age.days} days old (max: {max_age_days})"
        except Exception:
            pass

        # Check against GitHub
        latest = self.get_latest_github_version()
        if latest and current.get("sha") != latest["sha"]:
            return True, f"New commit available: {latest['message'][:50]}"

        return False, "Up to date"

    def download_runelite_source(self) -> Path | None:
        """Download RuneLite source code to temporary location."""
        logger.info("Downloading RuneLite source from GitHub")

        # Create temp directory for download
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        zip_path = self.temp_dir / "runelite-master.zip"
        extract_path = self.temp_dir / "runelite-master"

        try:
            # Clean up any existing temp files first
            shutil.rmtree(extract_path, ignore_errors=True)
            if zip_path.exists():
                zip_path.unlink()

            # Download with progress
            logger.info(f"Downloading to {zip_path}")
            urllib.request.urlretrieve(self.download_url, zip_path)
            file_size_mb = zip_path.stat().st_size / 1024 / 1024
            logger.success(f"Downloaded {file_size_mb:.1f} MB")

            # Extract
            logger.info("Extracting ZIP")

            # Use unzip command
            result = subprocess.run(
                [
                    "unzip",
                    "-q",
                    str(zip_path),
                    "runelite-master/runelite-api/*",
                    "-d",
                    str(self.temp_dir),
                ],
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                logger.warning(f"unzip warning: {result.stderr}")

            api_path = (
                extract_path / "runelite-api" / "src" / "main" / "java" / "net" / "runelite" / "api"
            )

            if not api_path.exists():
                logger.error(f"API path not found: {api_path}")
                self.cleanup_temp_files()
                return None

            logger.success(f"Extracted to {api_path}")
            return api_path

        except Exception as e:
            logger.error(f"Download failed: {e}")
            self.cleanup_temp_files()
            return None

    def cleanup_temp_files(self):
        """Remove temporary download files."""
        if self.temp_dir.exists():
            logger.info("Cleaning up temporary files")
            shutil.rmtree(self.temp_dir, ignore_errors=True)
            logger.success("Temp files removed")

    def run_scraper(self, api_path: Path) -> bool:
        """Run the scraper on the API source."""
        logger.info("\n Running scraper on API source")

        try:
            # Import scraper
            from ..scraper.scraper import EfficientRuneLiteScraper

            # Create scraper and run
            scraper = EfficientRuneLiteScraper()
            scraper.scrape_local_directory(api_path)

            # Save to correct location
            output_file = self.api_data_file
            scraper.save(str(output_file))

            # Verify it was created
            if not output_file.exists():
                logger.error("API data file was not created")
                return False

            # Check it has data
            with open(output_file) as f:
                data = json.load(f)

            if len(data.get("methods", {})) == 0:
                logger.error("API data is empty")
                return False

            logger.success(f"API data saved to {output_file}")
            logger.info(f"Methods: {len(data['methods'])}")
            logger.info(f"Enums: {len(data['enums'])}")
            logger.info(f"Classes: {len(data['classes'])}")

            return True

        except Exception as e:
            logger.error(f"Scraper failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    def update_version_info(self):
        """Save version information after successful update"""
        version_info = {
            "updated_at": datetime.now().isoformat(),
            "data_file": str(self.api_data_file),
        }

        # Add GitHub info if available
        github_info = self.get_latest_github_version()
        if github_info:
            version_info.update(github_info)

        with open(self.version_file, "w") as f:
            json.dump(version_info, f, indent=2)

        logger.success(f"\n Version info saved to {self.version_file}")

    def regenerate_constants(self) -> bool:
        """Regenerate constants from API data."""
        logger.info("\n Regenerating constants")

        # Use cache manager for generated files
        generated_dir = self.cache_manager.generated_dir
        generated_dir.mkdir(parents=True, exist_ok=True)

        constants_file = generated_dir / "constants.py"

        try:
            # Import proxy generator (still used for constants)
            from ..scraper.proxy_generator import ProxyGenerator

            # Generate constants (takes file path, not dict)
            generator = ProxyGenerator(str(self.api_data_file))
            generator.save_constants(str(constants_file))

            # Verify it was created
            if not constants_file.exists():
                logger.error("Constants file was not created")
                return False

            constants_size_kb = constants_file.stat().st_size / 1024
            logger.success(f"Constants file generated: {constants_size_kb:.1f} KB")

            return True

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            import traceback

            traceback.print_exc()
            return False

    def update(self, force: bool = False, max_age_days: int = 7) -> bool:
        """Check for updates and download new API data if needed."""
        print("=" * 80)
        logger.info("RuneLite API Auto-Updater")
        print("=" * 80)

        # Check if update needed
        needs_update, reason = self.should_update(force, max_age_days)

        if not needs_update:
            logger.success(f"\n {reason}")
            return True

        logger.info(f"\n Update needed: {reason}")

        # Always download fresh source (no caching)
        # Download to temp directory
        api_path = self.download_runelite_source()
        if not api_path:
            logger.error("\n Failed to download RuneLite source")
            return False

        # Run scraper
        scrape_success = self.run_scraper(api_path)

        # Always cleanup temp files after scraping (success or failure)
        self.cleanup_temp_files()

        if not scrape_success:
            logger.error("\n Scraper failed")
            return False

        # Regenerate constants before updating version file
        # This ensures we don't mark as "updated" if generation fails
        constants_success = self.regenerate_constants()
        if not constants_success:
            logger.error("\n Constants generation failed")
            return False

        # Update version info LAST - only after everything succeeds
        # This prevents stale cache if we crash mid-run
        self.update_version_info()

        print("\n" + "=" * 80)
        logger.success("Update complete!")
        print("=" * 80)

        return True

    def clean_temp_files(self):
        """Remove temporary download files (alias for cleanup_temp_files)"""
        self.cleanup_temp_files()

    def status(self):
        """Print current status"""
        print("=" * 80)
        logger.info("RuneLite API Status")
        print("=" * 80)

        # Check API data
        if self.api_data_file.exists():
            size_mb = self.api_data_file.stat().st_size / 1024 / 1024
            logger.success(f"\n API data exists: {self.api_data_file}")
            logger.info(f"Size: {size_mb:.2f} MB")

            try:
                with open(self.api_data_file) as f:
                    data = json.load(f)
                logger.info(f"Methods: {len(data.get('methods', {}))}")
                logger.info(f"Enums: {len(data.get('enums', {}))}")
                logger.info(f"Classes: {len(data.get('classes', []))}")
            except Exception as e:
                logger.warning(f"Could not read data: {e}")
        else:
            logger.error(f"\n API data not found: {self.api_data_file}")

        # Check version
        version = self.get_current_version()
        if version:
            logger.info("\n Current version")
            logger.info(f"Updated: {version.get('updated_at', 'unknown')}")
            logger.info(f"Commit: {version.get('sha', 'unknown')[:8]}")
            logger.info(f"Message: {version.get('message', 'unknown')}")
        else:
            logger.warning("\n No version information")

        # Check for updates
        logger.info("\n Checking for updates")
        latest = self.get_latest_github_version()
        if latest:
            logger.info(f"Latest commit: {latest['sha'][:8]}")
            logger.info(f"Date: {latest['date']}")
            logger.info(f"Message: {latest['message']}")

            if version and version.get("sha") == latest["sha"]:
                logger.success("\n Up to date!")
            else:
                logger.warning("\n Update available")
        else:
            logger.warning("Could not check GitHub")

        # Check temp directory
        if self.temp_dir.exists():
            temp_files = list(self.temp_dir.iterdir())
            if temp_files:
                logger.warning(f"\n Temp files exist (should be cleaned): {len(temp_files)} files")
            else:
                logger.success("\n No temp files")
        else:
            logger.success("\n No temp directory")
