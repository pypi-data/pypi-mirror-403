"""RuneLite API Scraper and Auto-Updater."""

from ..updater.api import RuneLiteAPIUpdater

__all__ = ["RuneLiteAPIUpdater", "ensure_api_data"]


def ensure_api_data(force: bool = False, max_age_days: int = 7, quiet: bool = False) -> bool:
    """Ensure API data is present and up-to-date."""
    import sys
    from io import StringIO

    updater = RuneLiteAPIUpdater()

    # Redirect output if quiet
    if quiet:
        old_stdout = sys.stdout
        sys.stdout = StringIO()

    try:
        success = updater.update(force=force, max_age_days=max_age_days)
        return success
    finally:
        if quiet:
            sys.stdout = old_stdout
