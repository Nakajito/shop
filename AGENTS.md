# Project-specific lessons

## Django `static()` returns [] when DEBUG=False

`django.conf.urls.static.static()` checks `settings.DEBUG` internally and returns an empty list when `DEBUG=False`. Never rely on it for production media serving.

Always use `re_path` + `django.views.static.serve` directly for production:

```python
from django.urls import re_path
from django.views.static import serve

urlpatterns += [
    re_path(
        r"^%s(?P<path>.*)$" % re.escape(settings.MEDIA_URL.lstrip("/")),
        serve,
        kwargs={"document_root": settings.MEDIA_ROOT},
    ),
]
```

## Coolify + Docker persistent volumes

In Coolify deployments, `MEDIA_ROOT` in production must match the volume mount `Destination Path`. The Django `BASE_DIR` resolves to `/app/myshop` inside the container (`WORKDIR /app` + repo root is `myshop/`). If the Coolify volume is mounted at `/app/media`, override `MEDIA_ROOT` in `production.py`:

```python
MEDIA_ROOT = BASE_DIR.parent / "media"  # /app/media
```

## Debugging media files in production

Inside the Coolify container, verify `MEDIA_ROOT` and file existence:

```bash
python /app/myshop/manage.py shell -c "
from django.conf import settings
import os
print('MEDIA_ROOT:', settings.MEDIA_ROOT)
print('MEDIA_URL:', settings.MEDIA_URL)
print('Existe MEDIA_ROOT:', os.path.isdir(settings.MEDIA_ROOT))
"
find /app -name "*product-name*" -type f 2>/dev/null
```
