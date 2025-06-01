import os

def GetFilepath(rel_filename):
    # Get the current file's path (module.py)
    current_dir = os.path.dirname(__file__)  # This will give you the path to the module
    # Now, get the path to the file relative to the current module
    return os.path.join(current_dir, rel_filename)