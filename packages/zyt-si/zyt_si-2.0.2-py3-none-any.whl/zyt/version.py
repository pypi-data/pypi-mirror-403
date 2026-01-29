from importlib.metadata import version, PackageNotFoundError

def get_version() -> str:
    try:
        return version(__package__ or "zyt-si")
    except PackageNotFoundError:
        return "unknown"
        
