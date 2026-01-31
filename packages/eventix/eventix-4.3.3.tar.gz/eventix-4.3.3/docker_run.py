import logging
import subprocess
from os import getcwd

from semantic_version import Version

from eventix import __version__
from eventix.functions.tools import setup_logging

log = logging.getLogger(__name__)

base_image = "python:3.12.4-slim-bookworm"
poetry_version = "1.4.2"
image_name = "bsimpson888/eventix"


def run():
    setup_logging()
    versions = get_versions()
    tags = get_tags(versions)

    build_args = dict(FROM=base_image, POETRY_VERSION=poetry_version)

    log.info(f"Building Eventix Version {versions[-1]}")

    cmd = ["docker", "run", "-ti", "--rm", "--env-file", "./.env.local", tags[-1]]
    print(" ".join(cmd))
    subprocess.run(cmd)


def get_versions():
    version_string = __version__
    v = Version.coerce(version_string)
    if len(v.prerelease) == 0:
        versions = ["latest", f"{v.major}", f"{v.major}.{v.minor}", f"{v.major}.{v.minor}.{v.patch}"]
    else:
        versions = [str(v)]

    return versions


def get_tags(versions):
    tags = list(f"{image_name}:{version}" for version in versions)
    return tags


if __name__ == "__main__":
    run()
