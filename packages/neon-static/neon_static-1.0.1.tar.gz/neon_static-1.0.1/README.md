# Neon Static

A clean, professional Sphinx theme with a static layout and no animations.

## Install

```bash
pip install neon-static
```

Or in `requirements.txt`:

```
neon-static==1.0.0
```

For local development:

```bash
pip install -e /path/to/neon-static
```

## Standalone Sphinx usage

```python
# conf.py
import os

project = "My Docs"

html_theme = "neon-static"

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
    "neonbook_perf_log": "on" if _env_flag("NEONBOOK_PERF_LOG", "off") else "off",
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

- `NEONBOOK_PERF_LOG`: enable performance console logging (default: `off`)

`NEONBOOK_VHS`, `NEONBOOK_PERF_SOUND`, and `NEONBOOK_PERF_NOTIFY` are not used by this theme.

For boolean flags, any value other than `0`, `off`, `false`, or `no` is treated as on.

## License

Apache License 2.0. See `LICENSE`.
