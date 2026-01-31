"""Global configuration for Wafer CLI.

Handles API URLs, environment presets (staging/prod/local), and user preferences.
Separate from config.py which handles Docker execution config for `wafer run`.
"""

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

# Config file location
CONFIG_DIR = Path.home() / ".wafer"
CONFIG_FILE = CONFIG_DIR / "config.toml"

# Environment type
EnvironmentName = Literal["staging", "prod", "local"]


@dataclass(frozen=True)
class ApiEnvironment:
    """API environment configuration. Immutable."""

    name: str
    api_url: str
    supabase_url: str
    supabase_anon_key: str

    def __post_init__(self) -> None:
        assert self.name, "environment name cannot be empty"
        assert self.api_url, "api_url cannot be empty"
        assert self.supabase_url, "supabase_url cannot be empty"
        assert self.supabase_anon_key, "supabase_anon_key cannot be empty"


# Built-in environment presets
# Anon keys are public (used client-side) - safe to embed
BUILTIN_ENVIRONMENTS: dict[str, ApiEnvironment] = {
    "staging": ApiEnvironment(
        name="staging",
        api_url="https://wafer-api-staging.onrender.com",
        supabase_url="https://xudshwhzytyfxwwyofli.supabase.co",
        supabase_anon_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inh1ZHNod2h6eXR5Znh3d3lvZmxpIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjU4Mzc5MDEsImV4cCI6MjA4MTQxMzkwMX0.JvuF4349z1ermKmrxEKGDHQj9I_ylLZYjjuouJleYhY",
    ),
    "prod": ApiEnvironment(
        name="prod",
        api_url="https://www.api.wafer.ai",
        supabase_url="https://auth.wafer.ai",
        supabase_anon_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imh2bHB0aGNueGx5d2xxdWljaXFlIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjQ2MjQ1NTIsImV4cCI6MjA4MDIwMDU1Mn0.1ywPDp-QHgbqPOJocQvXEKKDjGt3BsoNluvVoQ7EW3o",
    ),
    "local": ApiEnvironment(
        name="local",
        api_url="http://localhost:8000",
        supabase_url="http://localhost:54321",
        supabase_anon_key="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0",
    ),
}

# Default environment when no config exists
DEFAULT_ENVIRONMENT = "prod"


@dataclass(frozen=True)
class Preferences:
    """User preferences. Immutable.

    mode: "implicit" (default) = quiet output, use -v for status messages
          "explicit" = verbose output, shows [wafer] status messages
    analytics_enabled: True (default) = send anonymous usage analytics to PostHog
                       False = disable all analytics tracking
    """

    mode: Literal["explicit", "implicit"] = "implicit"
    analytics_enabled: bool = True


@dataclass(frozen=True)
class Defaults:
    """Default values for commands. Immutable."""

    workspace: str | None = None
    gpu: str = "H100"
    exec_timeout: int = 300  # seconds


@dataclass(frozen=True)
class GlobalConfig:
    """Global Wafer CLI configuration. Immutable."""

    environment: str = DEFAULT_ENVIRONMENT
    environments: dict[str, ApiEnvironment] = field(
        default_factory=lambda: BUILTIN_ENVIRONMENTS.copy()
    )
    preferences: Preferences = field(default_factory=Preferences)
    defaults: Defaults = field(default_factory=Defaults)

    def __post_init__(self) -> None:
        # Validate environment exists
        assert self.environment in self.environments, (
            f"environment '{self.environment}' not found. "
            f"Available: {list(self.environments.keys())}"
        )

    def get_api_environment(self) -> ApiEnvironment:
        """Get the current API environment."""
        return self.environments[self.environment]

    @property
    def api_url(self) -> str:
        """Get current API URL."""
        return self.get_api_environment().api_url

    @property
    def supabase_url(self) -> str:
        """Get current Supabase URL."""
        return self.get_api_environment().supabase_url


def _parse_config_file(path: Path) -> GlobalConfig:
    """Parse config from TOML file.

    Args:
        path: Path to config file

    Returns:
        GlobalConfig instance
    """
    with open(path, "rb") as f:
        data = tomllib.load(f)

    # Parse API section
    api_data = data.get("api", {})
    environment = api_data.get("environment", DEFAULT_ENVIRONMENT)

    # Merge built-in environments with user-defined ones
    environments = BUILTIN_ENVIRONMENTS.copy()
    user_envs = api_data.get("environments", {})
    for name, env_config in user_envs.items():
        if isinstance(env_config, dict):
            # User can override built-in or define new
            base_env = environments.get(name, BUILTIN_ENVIRONMENTS["prod"])
            environments[name] = ApiEnvironment(
                name=name,
                api_url=env_config.get("url", base_env.api_url),
                supabase_url=env_config.get("supabase_url", base_env.supabase_url),
                supabase_anon_key=env_config.get("supabase_anon_key", base_env.supabase_anon_key),
            )

    # Parse preferences
    pref_data = data.get("preferences", {})
    mode = pref_data.get("mode", "explicit")
    assert mode in ("explicit", "implicit"), f"mode must be 'explicit' or 'implicit', got '{mode}'"
    analytics_enabled = pref_data.get("analytics_enabled", True)
    assert isinstance(analytics_enabled, bool), f"analytics_enabled must be true or false, got '{analytics_enabled}'"
    preferences = Preferences(mode=mode, analytics_enabled=analytics_enabled)

    # Parse defaults
    defaults_data = data.get("defaults", {})
    defaults = Defaults(
        workspace=defaults_data.get("workspace"),
        gpu=defaults_data.get("gpu", "H100"),
        exec_timeout=defaults_data.get("exec_timeout", 300),
    )

    return GlobalConfig(
        environment=environment,
        environments=environments,
        preferences=preferences,
        defaults=defaults,
    )


# Cached config instance
_cached_config: GlobalConfig | None = None


def load_global_config() -> GlobalConfig:
    """Load global config from file, with env var overrides.

    Priority (highest to lowest):
    1. Environment variables (WAFER_API_URL, SUPABASE_URL)
    2. Config file (~/.wafer/config.toml)
    3. Built-in defaults (prod environment)

    Returns:
        GlobalConfig instance
    """
    global _cached_config

    if _cached_config is not None:
        return _cached_config

    # Start with defaults
    if CONFIG_FILE.exists():
        config = _parse_config_file(CONFIG_FILE)
    else:
        config = GlobalConfig()

    _cached_config = config
    return config


def get_api_url() -> str:
    """Get API URL with env var override.

    Priority:
    1. WAFER_API_URL env var
    2. Config file
    3. Default (prod)
    """
    env_url = os.environ.get("WAFER_API_URL")
    if env_url:
        return env_url
    return load_global_config().api_url


def get_supabase_url() -> str:
    """Get Supabase URL with env var override.

    Priority:
    1. SUPABASE_URL env var
    2. Config file
    3. Default (prod)
    """
    env_url = os.environ.get("SUPABASE_URL")
    if env_url:
        return env_url
    return load_global_config().supabase_url


def get_supabase_anon_key() -> str:
    """Get Supabase anon key for current environment.

    The anon key is public and used for client-side auth operations
    like token refresh.
    """
    return load_global_config().get_api_environment().supabase_anon_key


def get_preferences() -> Preferences:
    """Get user preferences."""
    return load_global_config().preferences


def get_defaults() -> Defaults:
    """Get default values."""
    return load_global_config().defaults


def clear_config_cache() -> None:
    """Clear cached config. Useful after config changes."""
    global _cached_config
    _cached_config = None


def save_global_config(config: GlobalConfig) -> None:
    """Save config to TOML file, preserving existing Docker config sections.

    Merges the global API config with any existing [default] and [environments.*]
    sections that are used by the Docker execution config (WaferConfig).
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing config to preserve Docker sections
    existing_data: dict = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE, "rb") as f:
            existing_data = tomllib.load(f)

    # Build new content, preserving Docker config sections
    lines = []

    # Preserve [default] section (Docker config)
    if "default" in existing_data:
        lines.append("[default]")
        for key, value in existing_data["default"].items():
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f"{key} = {value}")
        lines.append("")

    # API section (global config)
    lines.append("[api]")
    lines.append(f'environment = "{config.environment}"')
    lines.append("")

    # Only write non-builtin API environments
    for name, env in config.environments.items():
        if name not in BUILTIN_ENVIRONMENTS or env != BUILTIN_ENVIRONMENTS[name]:
            lines.append(f"[api.environments.{name}]")
            lines.append(f'url = "{env.api_url}"')
            lines.append(f'supabase_url = "{env.supabase_url}"')
            lines.append("")

    # Preserve [environments.*] sections (Docker config)
    if "environments" in existing_data:
        for name, env_config in existing_data["environments"].items():
            if isinstance(env_config, dict):
                lines.append(f"[environments.{name}]")
                for key, value in env_config.items():
                    if isinstance(value, str):
                        lines.append(f'{key} = "{value}"')
                    else:
                        lines.append(f"{key} = {value}")
                lines.append("")

    # Preferences section (only if non-default values)
    pref_lines = []
    if config.preferences.mode != "implicit":
        pref_lines.append(f'mode = "{config.preferences.mode}"')
    if not config.preferences.analytics_enabled:
        pref_lines.append("analytics_enabled = false")

    if pref_lines:
        lines.append("[preferences]")
        lines.extend(pref_lines)
        lines.append("")

    # Defaults section (only if non-default values)
    defaults_lines = []
    if config.defaults.workspace:
        defaults_lines.append(f'workspace = "{config.defaults.workspace}"')
    if config.defaults.gpu != "H100":
        defaults_lines.append(f'gpu = "{config.defaults.gpu}"')
    if config.defaults.exec_timeout != 300:
        defaults_lines.append(f"exec_timeout = {config.defaults.exec_timeout}")

    if defaults_lines:
        lines.append("[defaults]")
        lines.extend(defaults_lines)
        lines.append("")

    CONFIG_FILE.write_text("\n".join(lines))
    clear_config_cache()


def init_config(environment: str = DEFAULT_ENVIRONMENT) -> GlobalConfig:
    """Initialize config file with defaults.

    Args:
        environment: Initial environment to use

    Returns:
        The created GlobalConfig
    """
    config = GlobalConfig(environment=environment)
    save_global_config(config)
    return config
