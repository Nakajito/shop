"""Settings selector.

Reads ``DJANGO_SETTINGS_MODULE`` to decide which environment module to load:
- ``myshop.settings.production`` -> production overrides
- anything else (default) -> development overrides

Both extend ``base.py``.
"""

import os

_settings_module = os.getenv("DJANGO_SETTINGS_MODULE", "myshop.settings.development")

if _settings_module == "myshop.settings.production":
    from .production import *  # noqa: F401, F403
else:
    from .development import *  # noqa: F401, F403
