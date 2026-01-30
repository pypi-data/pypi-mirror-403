"""Interaction systems - menu, clicking, hovering, widgets."""

from escape.interactions.menu import Menu, menu


class Interactions:
    """Interaction systems for right-click menus and context actions."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def menu(self) -> Menu:
        """Menu interaction handler."""
        return menu


# Module-level instance
interactions = Interactions()


__all__ = ["Interactions", "Menu", "interactions", "menu"]
