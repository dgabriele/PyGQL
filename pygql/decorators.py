def memoized_property(func):
    def wrapper(*args, **kwargs):
        if not hasattr(func, '_retval'):
            func._retval = func(*args, **kwargs)
        return func._retval
    return property(wrapper)
