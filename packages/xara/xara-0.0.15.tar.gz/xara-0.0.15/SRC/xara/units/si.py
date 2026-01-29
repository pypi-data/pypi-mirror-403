from . import units, mks

Length = "meter"

def __getattr__(name):
    return units.Dimension(getattr(mks, name))

