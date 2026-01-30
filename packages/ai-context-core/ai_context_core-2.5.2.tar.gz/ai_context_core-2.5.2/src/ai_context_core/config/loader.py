"""Configuration loading and profile management.

Handles merging default settings with project-specific profiles and
runtime overrides (CLI flags).
"""

import yaml
import pathlib
from typing import Dict, Any, Optional


class ConfigLoader:
    """Loads and manages analyzer configuration by merging defaults and profiles.

    Attributes:
        base_path: Absolute directory containing the loader.
        defaults_path: Path to the default YAML configuration.
        profiles_path: Path to the directory containing named profiles.
    """

    def __init__(self):
        """Initializes the ConfigLoader with standard project paths."""
        self.base_path = pathlib.Path(__file__).parent
        self.defaults_path = self.base_path / "defaults.yaml"
        self.profiles_path = self.base_path / "profiles"

    def load_config(
        self, profile_name: Optional[str] = None, override_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Loads a composite configuration by merging defaults, profiles, and overrides.

        Args:
            profile_name: Optional name of the profile to load (e.g., 'qgis-plugin').
            override_config: Dictionary containing specific configuration overrides.

        Returns:
            A finalized dictionary containing the merged configuration.
        """

        # 1. Load baseline defaults
        config = self._load_yaml(self.defaults_path)

        # 2. Layer profile configuration if specified
        if profile_name:
            profile_file = self.profiles_path / f"{profile_name}.yaml"
            if profile_file.exists():
                profile_config = self._load_yaml(profile_file)
                config = self._merge_dicts(config, profile_config)
            else:
                print(
                    f"⚠️ Profile '{profile_name}' not found in {self.profiles_path}. Using defaults."
                )

        # 3. Apply final overrides (e.g., from CLI arguments)
        if override_config:
            config = self._merge_dicts(config, override_config)

        return config

    def _load_yaml(self, path: pathlib.Path) -> Dict[str, Any]:
        """Safely loads a YAML file from disk.

        Args:
            path: Path to the YAML file.

        Returns:
            Parsed dictionary or an empty dict if the file is invalid or missing.
        """
        try:
            return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            print(f"❌ Error loading configuration {path}: {e}")
            return {}

    def _merge_dicts(self, base: Dict, update: Dict) -> Dict:
        """Recursively merges an update dictionary into a base dictionary.

        Args:
            base: The source dictionary to be updated.
            update: The dictionary containing new or overriding values.

        Returns:
            The modified base dictionary.
        """
        for key, value in update.items():
            if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                base[key] = self._merge_dicts(base[key], value)
            else:
                base[key] = value
        return base


def list_profiles() -> list[str]:
    """Retrieves a list of all available configuration profile names.

    Returns:
        A list of profile stem names (e.g., ['qgis-plugin', 'generic']).
    """
    profiles_dir = pathlib.Path(__file__).parent / "profiles"
    profiles = ["generic"]
    if not profiles_dir.exists():
        return profiles
    profiles.extend([p.stem for p in profiles_dir.glob("*.yaml")])
    return profiles
