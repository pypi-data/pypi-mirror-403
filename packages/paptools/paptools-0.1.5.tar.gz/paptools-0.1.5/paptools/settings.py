class Settings:

    def __init__(self):
        self.verbose = False
        self.debug_level = "info"  # options: "info", "debug", "trace"


settings = Settings()

def set_option(name: str, value) -> None:
    if not hasattr(settings, name):
        raise AttributeError(f"No such setting: '{name}'")
    setattr(settings, name, value)

def get_option(name: str) -> any:
    if not hasattr(settings, name):
        raise AttributeError(f"No such setting: '{name}'")
    return getattr(settings, name)