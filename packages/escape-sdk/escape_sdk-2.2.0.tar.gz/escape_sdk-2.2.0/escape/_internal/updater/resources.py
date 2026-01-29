#!/usr/bin/env python3
"""
Resource Auto-Updater for Varps and Objects Database

Handles automatic version checking and updating of game resources.
Now delegates to cache_manager for actual download/load operations.
"""

from escape._internal.logger import logger


class ResourceUpdater:
    """Manages automatic updates for game resources (varps, objects, etc.)"""

    def should_update(self) -> tuple[bool, str]:
        """
        Check if game data needs update.

        Returns:
            Tuple of (should_update, reason)
        """
        from escape._internal.cache_manager import (
            _needs_update,
            get_cache_manager,
        )

        try:
            cache_manager = get_cache_manager()
            cache_dir = cache_manager.get_data_path("game_data")

            if _needs_update(cache_dir):
                return True, "Game data update available"
            return False, "Game data up to date"
        except Exception as e:
            return True, f"Game data check failed: {e}"

    def update_all(self, force: bool = False) -> bool:
        """
        Update all game data atomically.

        Downloads varps, varbits, and objects in one atomic operation
        to prevent version mismatches.

        Args:
            force: Force update even if up to date

        Returns:
            True if update successful
        """
        print("=" * 80)
        logger.info("Game Data Auto-Updater")
        print("=" * 80)

        # Check if update needed BEFORE downloading (unless forced)
        if not force:
            needs_update, reason = self.should_update()
            if not needs_update:
                logger.success(f"{reason}")
                print("=" * 80)
                return True
            logger.info(f"{reason}")

        logger.info("\n Updating game data")

        try:
            from escape._internal.cache_manager import (
                BASE_URL,
                _download_file,
                get_cache_manager,
            )

            cache_manager = get_cache_manager()
            cache_dir = cache_manager.get_data_path("game_data")
            cache_dir.mkdir(parents=True, exist_ok=True)

            # Force download by deleting existing files
            if force:
                logger.info("Forcing fresh download")
                for f in ["metadata.json", "varps.json", "varbits.json", "objects.db"]:
                    file_path = cache_dir / f
                    if file_path.exists():
                        file_path.unlink()

            # Download all files
            base_url = f"{BASE_URL}/varps/latest"
            files = {
                "metadata.json": "metadata.json",
                "varps.json": "varps.json",
                "varbits.json": "varbits.json",
                "objects.db": "objects.db.gz",
            }

            for local_name, remote_name in files.items():
                url = f"{base_url}/{remote_name}"
                dest = cache_dir / local_name
                decompress = remote_name.endswith(".gz")

                if not _download_file(url, dest, decompress_gz=decompress):
                    logger.error(f"\n Failed to download {local_name}")
                    print("\n" + "=" * 80)
                    logger.error("Update failed")
                    print("=" * 80)
                    return False

            print("\n" + "=" * 80)
            logger.success("Game data updated successfully!")
            print("=" * 80)
            return True

        except Exception as e:
            logger.error(f"\n Game data update failed: {e}")
            import traceback

            traceback.print_exc()
            print("\n" + "=" * 80)
            logger.error("Update failed")
            print("=" * 80)
            return False

    def status(self):
        """Print current game data status."""
        print("=" * 80)
        logger.info("Game Data Status")
        print("=" * 80)

        needs_update, reason = self.should_update()
        if needs_update:
            logger.warning(f"\n {reason}")
        else:
            logger.success(f"\n {reason}")

        print("\n" + "=" * 80)


def main():
    """Command-line interface for resource updater."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Resource Auto-Updater",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update all resources
  python -m escape._internal.updater.resources

  # Force update
  python -m escape._internal.updater.resources --force

  # Check status only
  python -m escape._internal.updater.resources --status
""",
    )

    parser.add_argument(
        "--force", "-f", action="store_true", help="Force update even if up to date"
    )

    parser.add_argument(
        "--status", "-s", action="store_true", help="Show status only, do not update"
    )

    args = parser.parse_args()

    updater = ResourceUpdater()

    if args.status:
        updater.status()
    else:
        success = updater.update_all(force=args.force)
        exit(0 if success else 1)


if __name__ == "__main__":
    main()
