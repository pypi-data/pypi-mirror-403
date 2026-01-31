from types import SimpleNamespace



class AutoNamespace(SimpleNamespace):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        super().__setattr__("_frozen", False)

    def __getattr__(self, name):
        # Called only when the attribute does not exist
        if self._frozen:
            raise AttributeError(
                f"AutoNamespace is frozen, cannot create attribute '{name}'"
            )

        value = AutoNamespace()
        setattr(self, name, value)
        return value

    def __setattr__(self, name, value):
        # Prevent adding new attributes when frozen
        if getattr(self, "_frozen", False) and not hasattr(self, name):
            raise AttributeError(
                f"AutoNamespace is frozen, cannot add attribute '{name}'"
            )
        super().__setattr__(name, value)

    def freeze(self, recursive: bool = True):
        """
        Freeze this namespace.
        If recursive=True, all nested AutoNamespace objects are frozen as well.
        """
        super().__setattr__("_frozen", True)

        if recursive:
            for value in self.__dict__.values():
                if isinstance(value, AutoNamespace):
                    value.freeze(recursive=True)
    
    def __iter__(self):
        return iter([ v for k, v in self.__dict__.items() if k[0]!='_'])
    
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass