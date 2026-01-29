from __future__ import annotations
import os, json
from dataclasses import dataclass, asdict, replace
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

ENV_PREFIX = "glyph_"
DEFAULT_WORKSPACE_CONFIG = Path("glyph_workspace/default/output/configs/settings.json")

def _parse_bool(v: str) -> bool:
    return v.strip().lower() in {"1","true","yes","on"}

def _parse_list(v: str) -> List[str]:
    # Accept JSON array or comma-separated
    v = v.strip()
    if v.startswith("["):
        try:
            j = json.loads(v)
            return [str(x) for x in j]
        except Exception:
            pass
    return [s.strip() for s in v.split(",") if s.strip()]

def _env_overrides() -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for k, v in os.environ.items():
        if not k.startswith(ENV_PREFIX):
            continue
        key = k[len(ENV_PREFIX):]
        out[key] = v
    return out

def _coerce_type(field_name: str, field_type: Any, raw: Any) -> Any:
    # Minimal coercions for common types used below
    if raw is None:
        return None
    if field_type is bool:
        if isinstance(raw, str): return _parse_bool(raw)
        return bool(raw)
    if field_type is int:
        if isinstance(raw, str): return int(raw)
        return int(raw)
    if field_type is float:
        if isinstance(raw, str): return float(raw)
        return float(raw)
    if field_type is str:
        return str(raw)
    if field_type is List[str]:
        if isinstance(raw, str): return _parse_list(raw)
        return [str(x) for x in raw]
    if field_type is List[int]:
        if isinstance(raw, str): return [int(x) for x in _parse_list(raw)]
        return [int(x) for x in raw]
    if field_type is Dict[str, Any]:
        if isinstance(raw, str):
            try: return json.loads(raw)
            except Exception: return {}
        return dict(raw)
    return raw

def _load_json_file(path: Path) -> Dict[str, Any]:
    try:
        if path.is_file():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}

@dataclass(frozen=True)
class Settings:
    # --- Context Window (per-line classification) ---
    CONTEXT_WINDOW_DEFAULT: int = 2
    CONTEXT_ADAPTIVE_ENABLED: bool = False
    CONTEXT_ADAPTIVE_MAX: int = 4

    # --- Range Handlers (multi-line grouping) ---
    RANGE_HANDLERS_ENABLED: List[str] = None  # set in __post_init__
    LIST_BLANK_LINE_TOLERANCE: int = 0
    LIST_ALLOW_MIXED_MARKERS: bool = True
    LIST_WRAP_INDENT_SPACES: int = 2   # continuation lines threshold

    # --- Plaintext table parsing ---
    PLAINTEXT_TABLE_FORMS: List[str] = None  # set in __post_init__
    TABLE_MAX_COLS: int = 40
    TABLE_STRICT_DELIMS: bool = False

    # --- Emittables / routing ---
    EMITTABLES_ENABLED: bool = True

    # --- Logging / perf ---
    LOG_LEVEL: str = "INFO"
    SDK_VERBOSE_LOGGING: bool = False

    # --- Where to load project config by default ---
    WORKSPACE_CONFIG_PATH: str = str(DEFAULT_WORKSPACE_CONFIG)

    def __post_init__(self):
        # Provide default mutables safely
        if self.RANGE_HANDLERS_ENABLED is None:
            object.__setattr__(self, "RANGE_HANDLERS_ENABLED", ["list", "table"])
        if self.PLAINTEXT_TABLE_FORMS is None:
            object.__setattr__(self, "PLAINTEXT_TABLE_FORMS", ["pipe", "csv", "grid", "aligned_spaces"])

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def with_overrides(self, **overrides: Any) -> "Settings":
        # Coerce types based on dataclass annotations
        coerced: Dict[str, Any] = {}
        ann = self.__annotations__
        for k, v in overrides.items():
            if k in ann:
                coerced[k] = _coerce_type(k, ann[k], v)
        return replace(self, **coerced)

# cached singleton
_SETTINGS: Optional[Settings] = None

def get_settings(
    refresh: bool = False,
    config_path: Optional[Union[str, Path]] = None,
    domain_overrides: Optional[Dict[str, Any]] = None,
    **runtime_overrides: Any,
) -> Settings:
    """
    Load settings with precedence (lowest → highest):
      1) Defaults (code)
      2) Workspace config file (JSON)
      3) Domain overrides (e.g., resume/legal/scientific pack)
      4) Environment variables (glyph_*)
      5) Runtime overrides (kwargs)
    """
    global _SETTINGS
    if _SETTINGS is not None and not refresh and not runtime_overrides and not domain_overrides and not config_path:
        return _SETTINGS

    base = Settings()

    # 2) workspace file
    cfg_path = Path(config_path or base.WORKSPACE_CONFIG_PATH)
    file_cfg = _load_json_file(cfg_path)
    s = base.with_overrides(**file_cfg)

    # 3) domain pack overrides (optional dict, e.g. loaded from domain_packs/*.json under key "settings")
    if domain_overrides:
        s = s.with_overrides(**domain_overrides)

    # 4) environment
    env = _env_overrides()
    # Map env keys directly to dataclass fields; users set JSON for lists/dicts or comma lists
    env_coerced = {}
    for k, v in env.items():
        if k in s.__annotations__:
            env_coerced[k] = _coerce_type(k, s.__annotations__[k], v)
    s = s.with_overrides(**env_coerced)

    # 5) runtime kwargs
    if runtime_overrides:
        s = s.with_overrides(**runtime_overrides)

    _SETTINGS = s
    return s

def reset_settings_cache() -> None:
    global _SETTINGS
    _SETTINGS = None
