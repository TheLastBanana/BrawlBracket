class KeySingleton(type):
    """
    A form of singleton where the singleton is based on a defining attribute.
    Only one instance for each defining attribute and class combination will be created.
    Uses the first variable as the key. If something else is needed as the key then
    KeySingleton must be subclassed.
    """
    instances = {}
    def __call__(cls, key, *args, **kw):
        if cls.__name__ not in cls.instances:
            cls.instances[cls.__name__] = {key: super(KeySingleton, cls).__call__(key, *args, **kw)}
        elif key not in cls.instances[cls.__name__]:
            cls.instances[cls.__name__][key] = super(KeySingleton, cls).__call__(key, *args, **kw)
        return cls.instances[cls.__name__][key]