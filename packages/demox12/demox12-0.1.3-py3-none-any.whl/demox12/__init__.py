from importlib.resources import files

def get_data_path():
    """Return path to packaged data folder."""
    return files("demox12").joinpath("data")