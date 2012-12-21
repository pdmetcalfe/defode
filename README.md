defode is a convenient way to generate ordinary differential equations
as used by the standard VODE solver.  The equations are declared in
Python code that then generates compilable C code that can be used
normally.

The supported mathematical operations can be easily extended, and
there is also a convenience layer that simplifies compartmental
modelling.

Herewith an example: a very simplified PK model that renders
compilable C code to standard output.  The keen viewer will note that
the generated code needs to be compiled with some reasonable
optimization level, but is also very susceptible to optimization.

```python
import sys

from defode.variable import ODESet, function_factory
from defode.compartments import Compartment
import sys

from defode.compartments import Compartment


def main():
    """
    Main program.

    Establish a very very simple PK model (with no elimination!)
    but which demonstrates the features.  A real model would have
    better-structured code here!
    """

    model = Compartment()
    blood_flow = model.new_variable('bloodFlow')
    for which in ['veins', 'arteries', 'muscle']:
        comp = model.new_compartment(which)
        vol = comp.new_variable('volume')
	amount = comp.new_variable('amount')
	conc = comp.new_variable('concentration')
	conc.compute(amount / vol)

    muscle_partition = model['muscle'].new_variable('partition')
	
    veins_out = blood_flow * model['veins']['concentration']
    arts_out = blood_flow * model['arteries']['concentration']
    muscle_out = (blood_flow * model['muscle']['concentration'] /
                  muscle_partition)
    
    model['veins']['amount'].evolve(muscle_out - veins_out)
    model['arteries']['amount'].evolve(veins_out - arts_out)
    model['muscle']['amount'].evolve(arts_out - muscle_out)
    
    total = sum(model[item]['amount']
                for item in ['veins', 'arteries', 'muscle'])

    model.new_variable('amount').compute(total)

    model.render(sys.stdout.write)


if __name__ == '__main__':
    main()
```