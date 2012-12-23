"""
Common code for ODE modelling.
"""

import collections
import itertools
import warnings

import networkx as NX

class Node(object):
    """
    Represent a node in the calculation tree.

    This class just exists as a location for all the
    operator overloading.
    """
    def __add__(self, other):
        return Sum(self, other)

    def __radd__(self, other):
        return Sum(other, self)

    def __mul__(self, other):
        return Multiply(self, other)

    def __rmul__(self, other):
        return Multiply(other, self)

    def __sub__(self, other):
        return Difference(self, other)

    def __rsub__(self, other):
        return Difference(other, self)

    def __div__(self, other):
        return Division(self, other)

    def __rdiv__(self, other):
        return Division(other, self)


class Calculation(Node):
    """Represent a calculation."""
    def __init__(self, *args):
        self.terms = args

    def dependencies(self):
        """What are my dependencies?"""
        return [term for term in self.terms if isinstance(term, Node)]

    def names(self, name_map):
        return [name_map(item) for item in self.terms]

    def render(self, target, name_map):
        """Render to the target file."""
        raise NotImplementedError()


class Constant(Calculation):
    """Represent a constant term."""
    def __init__(self, arg):
        Calculation.__init__(self, arg)

    def render(self, target, name_map):
        name, = self.names(name_map)
        target(name)


class Sum(Calculation):
    """Represent a sum."""
    def render(self, target, name_map):
        target(' + '.join(self.names(name_map)))


class Multiply(Calculation):
    """Represent a product."""
    def render(self, target, name_map):
        target(' * '.join(self.names(name_map)))


class Difference(Calculation):
    """Represent a subtraction."""
    def __init__(self, term1, term2):
        Calculation.__init__(self, term1, term2)

    def render(self, target, name_map):
        target(' - '.join(self.names(name_map)))


class Division(Calculation):
    """Represent a quotient."""

    def __init__(self, term1, term2):
        Calculation.__init__(self, term1, term2)

    def render(self, target, name_map):
        target(' / '.join(self.names(name_map)))


class Function(Calculation):
    """Represent a function call."""
    def __init__(self, function_name, *args):
        self.function_name = function_name
        Calculation.__init__(self, *args)

    def render(self, target, name_map):
        target('%s(%s)' % (self.function_name, 
                           ', '.join(self.names(name_map))))

def function_factory(name, arg_len=None):
    """Build a call to a function."""
    def result(*args):
        if (arg_len is not None) and (len(args) != arg_len):
            raise ValueError("Bad argument list for %s" % name)
        return Function(name, *args)
    return result


class Variable(Node):
    """Represent a variable: either input, computed, or evolving."""
    FREE = 0
    COMPUTED = 1
    EVOLVING = 2

    def __init__(self):
        self.state = self.FREE
        self.calculation = None

    def _update(self, new_calculation, new_state, yes_really):
        """Update myself."""
        if yes_really:
            # we are forcing an override here
            # so we must have something to override
            assert(self.calculation is not None)

        if not yes_really:
            if self.calculation is not None:
                warnings.warn("Overriding calculation.")

        if not isinstance(new_calculation, Calculation):
            new_calculation = Constant(new_calculation)

        self.state = new_state
        self.calculation = new_calculation

    def compute(self, new_calculation, yes_really=False):
        self._update(new_calculation, self.COMPUTED, yes_really)

    def evolve(self, new_calculation, yes_really=False):
        self._update(new_calculation, self.EVOLVING, yes_really)

    @property
    def is_free(self):
        return self.state == self.FREE

    @property
    def is_calculated(self):
        return self.state == self.COMPUTED

    @property
    def is_evolving(self):
        return self.state == self.EVOLVING


def classify_all(time, variables):
    """Classify all the variables."""
    graph = NX.DiGraph()
    graph.add_node(time)
    pending = list(variables)
    seen = set()
    while pending:
        current = pending.pop()
        seen.add(current)
        if isinstance(current, Calculation):
            for item in current.dependencies():
                graph.add_edge(item, current)
                if item not in seen:
                    pending.append(item)
        else:
            # it's a variable
            if current.is_calculated:
                calc = current.calculation
                graph.add_edge(calc, current)
                if calc not in seen:
                    pending.append(calc)
            elif current.is_evolving:
                graph.add_edge(time, current)
                calc = current.calculation
                if calc not in seen:
                    pending.append(calc)
    tsort = NX.topological_sort(graph)
    time_deps = NX.single_source_shortest_path_length(graph, time)
    target = {False : [],
              True : []}
    for item in tsort:
        target[item in time_deps].append(item)
    return target[False], target[True]


class SymbolMap(object):
    def __init__(self):
        self.store = {}
        self.count = itertools.count()
        self.pattern = 'var%i'
        
    def representation(self, item):
        """How is this item to be represented?"""
        if isinstance(item, (int, float)):
            return repr(item)
        try:
            return self.store[item]
        except KeyError:
            pass
        next_name = self.pattern % next(self.count)
        self.store[item] = next_name
        return next_name


def split_given_vars(time_deps, desired):
    time_deps = set(time_deps)
    inputs = []
    derived_constants = []
    evolving = []
    time_dep = []
    for name, variable in desired:
        if variable.is_evolving:
            evolving.append((name, variable))
        elif variable.is_calculated:
            if variable in time_deps:
                time_dep.append((name, variable))
            else:
                derived_constants.append((name, variable))
        else:
            assert(variable not in time_deps)
            inputs.append((name, variable))
    return inputs, derived_constants, evolving, time_dep
    

def _blat(target, pattern, iterable, representation):
    """Blat out the variables."""
    for ind, (name, variable) in enumerate(iterable):
        target('const double %s = %s[%i];\n' % (representation(variable),
                                                pattern,
                                                ind))


def write_constfun(target, representation,
                   input_vars, derived_constants, constants):
    """Write out a function that computes any constants."""
    target("""\
void compute(double* constants,
             const double* input) {
""")
    _blat(target, 'input', input_vars, representation)
    for item in constants:
        if isinstance(item, Variable) and not item.is_free:
            target('const double %s = %s;\n' % 
                   (representation(item),
                    representation(item.calculation)))
        elif isinstance(item, Calculation):
            target('const double %s = ' % representation(item))
            item.render(target, representation)
            target(';\n')
    for ind, (name, var) in enumerate(derived_constants):
        target('constants[%i] = %s;\n' % (ind, representation(var)))
    target("}\n")


def write_time_common(target, representation, time,
                      input_vars, derived_constants, state,
                      to_stuff, time_deps,
                      func_name, arr_name):
    target("""\
void %s(double* %s, const double* time,
        const double* state, const double* input) {
""" % (func_name, arr_name))
    target('const double *constants = input + %i;\n' %
           (len(input_vars)))
    target('const double %s = *time;\n' % representation(time))
    # first load everything out of arrays
    _blat(target, 'input', input_vars, representation)
    _blat(target, 'constants', derived_constants, representation)
    _blat(target, 'state', state, representation)
    # now compute that which we need to
    for item in time_deps:
        if item is time:
            continue
        if isinstance(item, Variable) and not item.is_evolving:
            target('const double %s = %s;\n' % 
                   (representation(item),
                    representation(item.calculation)))
        elif isinstance(item, Calculation):
            target('const double %s = ' % representation(item))
            item.render(target, representation)
            target(';\n')
    # now we're in a position to write the rate equations
    for ind, (name, var) in enumerate(to_stuff):
        target('%s[%i] = %s;\n' % (arr_name, 
                                   ind, 
                                   representation(var.calculation)))

    target('}\n')


def write_odefun(target, representation, time,
                 input_vars, derived_constants, state, time_deps):
    """Write out the ODE function."""
    write_time_common(target, representation, time,
                      input_vars, derived_constants, state,
                      state, time_deps,
                      'odefun', 'rate')


def write_timedep(target, representation, time,
                  input_vars, derived_constants, state,
                  time_dep_vars, time_deps):
    """Write out something that computes the time-dependent variables."""
    write_time_common(target, representation, time,
                      input_vars, derived_constants, state, 
                      time_dep_vars, time_deps,
                      'timedepfun', 'timedeps')

def render_names(target, **kwargs):
    """Render the lists of variable names."""
    for key in sorted(kwargs):
        names = [name for name, variable in kwargs[key]]
        target('const int num_%s = %i;\n' % (key, len(names)))
        target('const char* %s[] = {\n' % key)
        target(',\n'.join('"%s"' % name for name in names))
        target(',0\n};\n\n')


class ODESet(object):
    """Represent a set of ODEs."""
    def __init__(self):
        self.time = Variable()
        self.variables = collections.OrderedDict()

    def new(self, name):
        """Create a new variable."""
        if name in self.variables:
            raise ValueError("Duplicate variable name : %s" % name)
        if not isinstance(name, basestring):
            raise ValueError("Variable name must be a string.")
        created = Variable()
        self.variables[name] = created
        return created

    def render(self, target, reorder=None):
        """Render myself to this target."""
        items = self.variables.items()
        constants, time_deps = classify_all(self.time,
                                            self.variables.values())
        if reorder is not None:
            items = reorder(items)
        # now we classify the actual variables
        (input_vars, derived_constants,
         state_vars, time_dep_vars) = split_given_vars(time_deps,
                                                       items)
        render_names(target, 
                     inputs=input_vars, 
                     constants=derived_constants,
                     state=state_vars,
                     timedep=time_dep_vars)

        write_constfun(target, 
                       SymbolMap().representation,
                       input_vars, derived_constants, constants)
        write_odefun(target, SymbolMap().representation,
                     self.time,
                     input_vars, derived_constants, 
                     state_vars, time_deps)
        write_timedep(target, SymbolMap().representation,
                      self.time,
                      input_vars, derived_constants, state_vars, 
                      time_dep_vars, time_deps)
        
