import importlib.metadata

try:
    assert "/site-packages/" in __file__ or "/dist-packages/" in __file__
    VERSION_STR = importlib.metadata.version("cal-mkdocs")
except Exception:
    VERSION_STR = "DEV"  # type:ignore
