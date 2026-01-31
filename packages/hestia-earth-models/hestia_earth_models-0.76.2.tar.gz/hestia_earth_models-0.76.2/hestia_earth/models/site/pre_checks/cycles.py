from hestia_earth.models.utils.site import related_cycles


def run(site: dict):
    return site | {"cycles": related_cycles(site)}
