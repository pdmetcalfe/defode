from defode.variable import ODESet

class Compartment(object):
    """
    Represent a compartment for compartmental modelling.

    Don't instantiate this class directly.
    """
    def __init__(self, name=None, odeset=None):
        if odeset is None:
            odeset = ODESet()
        self.odeset = odeset
        self.name = name
        self.children = {}
        
    @property
    def time(self):
        return self.odeset.time

    def __getitem__(self, name):
        return self.children[name]


    def _make_new_name(self, new_name):
        """Make a new name."""
        if new_name in self.children:
            raise ValueError("already extant name")
        if self.name is None:
            return new_name
        else:
            return '_'.join([self.name, new_name])

    def new_variable(self, name):
        """Make a new variable."""
        full_name = self._make_new_name(name)
        variable = self.odeset.new(full_name)
        self.children[name] = variable
        return variable

    def new_compartment(self, name):
        """Make a subcompartment."""
        full_name = self._make_new_name(name)
        comp = type(self)(name=full_name, odeset=self.odeset)
        self.children[name] = comp
        return comp

    def render(self, target):
        """Render this compartmental model."""
        return self.odeset.render(target)
