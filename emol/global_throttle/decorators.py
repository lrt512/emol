from functools import wraps

def exempt_from_throttling(view_func):
    """Decorator to exempt a view from global throttling"""
    def wrapped_view(*args, **kwargs):
        return view_func(*args, **kwargs)

    wrapped_view.exempt_from_throttling = True
    return wraps(view_func)(wrapped_view)
