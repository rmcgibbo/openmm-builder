import simtk.unit
from traits.api import Any, Instance


# DIRTY HACK HACK HACK HACK HACK
# replace the __str__ function in simtk.unit.Quantity with a new version
# of our creation that outputs a representation that is suitable for use
# in an input piece of source code

# for example, using the old __str__, we would get
# (2.0*femotosecond).__str__() == '2.0 fs'
# but with this __str__, we get
# (2.0*femotosecond).__str__() == '2.0*femtosecond'

# we need this because during the templating and the rendering of the
# traitvalue into the traitui, the str() method is called on the object
def _new_str_(self):
    uname = self.unit.get_name()
    if uname.startswith('/'):
        return str(self._value) + uname
    return '%s*%s' % (self._value, uname)
simtk.unit.Quantity.__str__ = _new_str_
# END DIRTY HACK


# add a few aliases to the unit package, so that if someone types them
# inside the traitsui input box, they'll be parsed correctly
simtk.unit.fs = simtk.unit.femtosecond
simtk.unit.ps = simtk.unit.picosecond
simtk.unit.nm = simtk.unit.nanometers


class UnittedFloat(Any):
    """Trait corresponding to a float with units (from simtk.unit)
    """
    unit = Instance(simtk.unit.Unit)

    def __init__(self, default, **traits):
        """Create a UnittedFloat with a default value.
        The appropriate units for the trait will be extracted from
        the default value.

        Parameters
        ----------
        default : simtk.units.Quantity
            The default value of the trait.
        """
        super(UnittedFloat, self).__init__(default, **traits)
        self.unit = default.unit

    def validate(self, object, name, value):
        parsed_val = self._parse(object, name, value)
        try:
            if not parsed_val.unit.is_compatible(self.unit):
                self.error(object, name, value)
        except Exception as e:
            self.error(object, name, value)
        return parsed_val

    def _parse(self, object, name, value):
        try:
            # either just eval it
            v = eval(value, simtk.unit.__dict__)
        except Exception as e:
            try:
                # or try splitting it into two components, and multiplying
                # them. This enables something like "2.0 femtoseconds"
                # to be parsed correctly, with the implicit multiplication
                pre, post = value.split(None, 1)
                v = float(pre) * eval(post, simtk.unit.__dict__)
            except:
                self.error(object, name, value)
        return v