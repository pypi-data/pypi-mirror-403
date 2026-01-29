from findmydevice import __version__


def findmydevice_version_string(request):
    return {"version_string": f"v{__version__}"}
