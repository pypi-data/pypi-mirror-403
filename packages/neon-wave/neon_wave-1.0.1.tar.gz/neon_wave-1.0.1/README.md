# Neon Wave

A neon-wave Sphinx theme with neon grid styling and dark/light/system modes.

## Install

```bash
pip install neon-wave
```

Or in `requirements.txt`:

```
neon-wave==1.0.0
```

For local development:

```bash
pip install -e /path/to/neon-wave
```

## Standalone Sphinx usage

```python
# conf.py
import os

project = "My Docs"

html_theme = "neon-wave"

html_theme_options = {
    "light_logo": "logo-light.svg",
    "dark_logo": "logo-dark.svg",
    "sidebar_hide_name": False,
    "navigation_with_keys": True,
    "default_theme": "system",
    "show_toc_level": 2,
}

def _env_flag(name, default="off"):
    return os.getenv(name, default).lower() not in ("0", "off", "false", "no")

html_context = {
    "neonbook_vhs": "on" if _env_flag("NEONBOOK_VHS", "on") else "off",
    "neonbook_perf_log": "on" if _env_flag("NEONBOOK_PERF_LOG", "off") else "off",
    "neonbook_perf_sound": "on" if _env_flag("NEONBOOK_PERF_SOUND", "off") else "off",
    "neonbook_perf_notify": "on" if _env_flag("NEONBOOK_PERF_NOTIFY", "off") else "off",
}
```

## Theme options

- `light_logo`: logo for light mode
- `dark_logo`: logo for dark mode
- `sidebar_hide_name`: hide project name in the sidebar
- `navigation_with_keys`: enable keyboard navigation
- `default_theme`: `"dark"`, `"light"`, or `"system"`
- `show_toc_level`: depth of headings shown in the sidebar

Logo files are expected under `_static/` (for example, `_static/logo-light.svg`).

## Environment variables

These are optional. The theme reads them from `html_context`, so you can either set the keys directly or wire them from environment variables in `conf.py`.

- `NEONBOOK_VHS`: toggle VHS effects (default: `on`)
- `NEONBOOK_PERF_LOG`: enable performance console logging (default: `off`)
- `NEONBOOK_PERF_SOUND`: play a siren on heavy load (default: `off`)
- `NEONBOOK_PERF_NOTIFY`: desktop notification on heavy load (default: `off`)

For boolean flags, any value other than `0`, `off`, `false`, or `no` is treated as on.

## License

Apache License 2.0. See `LICENSE`.
