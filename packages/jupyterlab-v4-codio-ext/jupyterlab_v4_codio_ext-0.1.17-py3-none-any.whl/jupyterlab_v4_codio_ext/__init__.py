from ._version import __version__  # noqa

def _jupyter_labextension_paths():
    return [{"src": "labextension", "dest": "jupyterlab-v4-codio-ext"}]
