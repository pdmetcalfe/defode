defode is a convenient way to generate ordinary differential equations
as used by the standard VODE solver.  The equations are declared in
Python code that then generates compilable C code that can be used
normally.  The library was originally applied to the generation of
ODEs for PBPK models, which can be a few hundred
not-terribly-structured ODEs, and are a crawling horror to code
manually and efficiently.

The supported mathematical operations can be easily extended, and
there is also a convenience layer that simplifies compartmental
modelling.

Herewith an example: a very simplified PK model that renders
compilable C code to standard output.  The keen viewer will note that
the generated code needs to be compiled with some reasonable
optimization level, but is also very susceptible to optimization.

```python
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

The ODEs thus generated have variables in 4 categories: input
variables, constants, state variables, and time-dependent variables.
The *inputs* are the fixed parameters of the ODE system.  The
*constants* are things that can be derived from the inputs.  The
*state variables* are the variables that have differential equations.
The *time-dependent variables* are the variables that depend on time
or the state variables.

The generated C code lists the names of the variables in each category,
together with three functions: `compute`, which computes the constants
from the inputs, `odefun`, which defines the rate equations for the
ODEs, and `timedepfun`, which provides a way to compute the
time-dependent variables.  This should hopefully be pretty obvious
when you read the generated code.

It is a simple matter to interface this code to a decent ODE solver
like the [sundials
suite](https://computation.llnl.gov/casc/sundials/main.html
"SUNDIALS").
