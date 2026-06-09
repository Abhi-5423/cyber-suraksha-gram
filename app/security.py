from functools import wraps

import bleach
from flask import abort
from flask_login import current_user

ALLOWED_TAGS = ["p", "ul", "ol", "li", "strong", "em", "br", "h3", "h4"]


def sanitize_text(value):
    if value is None:
        return ""
    return bleach.clean(str(value).strip(), tags=[], strip=True)


def sanitize_html(value):
    if value is None:
        return ""
    return bleach.clean(str(value).strip(), tags=ALLOWED_TAGS, strip=True)


def roles_required(*roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.role not in roles:
                abort(403)
            return func(*args, **kwargs)

        return wrapper

    return decorator
