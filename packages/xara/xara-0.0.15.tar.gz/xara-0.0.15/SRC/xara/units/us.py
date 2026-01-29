from . import units, ips

Length = "inch"
Force  = "lbf"

def __getattr__(name):
    return units.Dimension(getattr(ips, name))

