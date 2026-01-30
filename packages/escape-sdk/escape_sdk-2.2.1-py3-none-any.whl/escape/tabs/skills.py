"""Skills tab module."""

from escape.types.gametab import GameTab, GameTabs

SKILL_NAMES: list[str] = [
    "Attack",
    "Defence",
    "Strength",
    "Hitpoints",
    "Ranged",
    "Prayer",
    "Magic",
    "Cooking",
    "Woodcutting",
    "Fletching",
    "Fishing",
    "Firemaking",
    "Crafting",
    "Smithing",
    "Mining",
    "Herblore",
    "Agility",
    "Thieving",
    "Slayer",
    "Farming",
    "Runecrafting",
    "Hunter",
    "Construction",
    "Sailing",
]


class Skills(GameTabs):
    """Skills tab for viewing skill levels and XP."""

    TAB_TYPE = GameTab.SKILLS

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance

    def _init(self):
        """Actual initialization, runs once."""
        GameTabs.__init__(self)
        self._last_total_xp: int | None = None

    def _get_skill_data(self, skill_name: str) -> dict[str, int]:
        """Get skill data from cache."""
        from escape.client import client

        # Get from cache
        data = client.cache.get_all_skills().get(skill_name)
        if data:
            return data

        # Default fallback
        return {"level": 1, "xp": 0, "boosted_level": 1}

    def get_level(self, skill_name: str) -> int:
        """Get current boosted level for a skill."""
        return self._get_skill_data(skill_name)["boosted_level"]

    def get_real_level(self, skill_name: str) -> int:
        """Get real (unboosted) level for a skill."""
        return self._get_skill_data(skill_name)["level"]

    def get_experience(self, skill_name: str) -> int:
        """Get experience for a skill."""
        return self._get_skill_data(skill_name)["xp"]

    def get_total_level(self) -> int:
        """Get total level across all skills."""
        from escape.client import client

        skills_data = client.cache.get_all_skills()
        return sum(data["level"] for data in skills_data.values())

    def get_total_experience(self) -> int:
        """Get total experience across all skills."""
        from escape.client import client

        skills_data = client.cache.get_all_skills()
        return sum(data["xp"] for data in skills_data.values())

    def gained_xp(self) -> bool:
        """Check if XP was gained since last check."""
        current_xp = self.get_total_experience()

        # Initialize on first call
        if self._last_total_xp is None:
            self._last_total_xp = current_xp
            return False

        # Check if gained
        if current_xp > self._last_total_xp:
            self._last_total_xp = current_xp
            return True

        return False

    def wait_xp(self, timeout: float = 5.0) -> bool:
        """Wait for XP gain with timeout."""
        import time

        # Initialize baseline
        if self._last_total_xp is None:
            self._last_total_xp = self.get_total_experience()

        # Check if already gained
        if self.gained_xp():
            return True

        # Wait for XP gain
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.gained_xp():
                return True
            time.sleep(0.05)

        return False


# Module-level instance
skills = Skills()
