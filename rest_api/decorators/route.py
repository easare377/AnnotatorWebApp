# utils/decorators.py
def route(url):
    def decorator(cls):
        cls._route = url
        return cls
    return decorator
