from hestia_earth.utils.tools import omit


def run(site: dict):
    return omit(site, ["cycles"])
