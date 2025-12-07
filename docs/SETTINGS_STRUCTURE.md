# Django Settings Structure

## Active Settings Files

The following settings files are actively used and should remain in `emol/emol/settings/`:

*   **`defaults.py`**: Base settings inherited by all environments. Contains shared configuration like `INSTALLED_APPS`, `MIDDLEWARE`, logging, etc.
*   **`dev.py`**: Development environment settings. Used when `DJANGO_SETTINGS_MODULE=emol.settings.dev`.
*   **`test.py`**: Test environment settings. Used when `DJANGO_SETTINGS_MODULE=emol.settings.test`.
*   **`prod.py`**: Production environment settings. Used when `DJANGO_SETTINGS_MODULE=emol.settings.prod`. Automatically loads `emol_production.py` if it exists.

## Settings Location

Settings are located at `emol/emol/settings/`, which is the Django project package level. This is the standard Django convention:
- `emol/` (outer) = project root
- `emol/emol/` = Django project package
- `emol/emol/settings/` = settings package

## Production Overrides

Production settings can be overridden by mounting `/opt/emol_config/emol_production.py` into the container at `/opt/emol/emol/emol/settings/emol_production.py`. The `prod.py` file automatically imports this if it exists:

```python
try:
    from emol.settings import emol_production  # noqa: F401
except ImportError:
    pass
```

## Documentation

Template and sample files have been moved to `docs/`:
- `docs/SETTINGS_TEMPLATE.md`: Template for creating `emol_production.py`
- `docs/SETTINGS_SAMPLE_PRODUCTION.md`: Reference for production settings
- `docs/SETTINGS_SAMPLE_DEV.md`: Reference for development settings

## Removed Files

The following files have been removed or moved:
- `emol/settings/dev.py` (duplicate, removed)
- `emol/emol/settings/sample_settings.py` → `docs/SETTINGS_SAMPLE_PRODUCTION.md`
- `emol/emol/settings/dev_sample.py` → `docs/SETTINGS_SAMPLE_DEV.md`

