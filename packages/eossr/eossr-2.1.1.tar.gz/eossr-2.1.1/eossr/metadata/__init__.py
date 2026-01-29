from semver import VersionInfo


def valid_semver(version):
    """Return True if the version is valid according to semver.org
    Strips leading 'v' from the version string.
    """
    return VersionInfo.isvalid(version.lstrip("v"))
