##############################################################################
# Imports
##############################################################################

# stdlib
import os

# enthought
from traits.api import HasTraits, Int, Enum, Regex, Bool, File
from traitsui.api import View, Item, Group

# openmm
import simtk.unit as unit

# this package
from .units import UnittedFloat

##############################################################################
# Classes
##############################################################################


class InputFile(HasTraits):
    file = File(os.path.abspath(os.path.curdir), filter=['*.pdb'])

    view = View(Group('file', show_border=True, label='Input File'))


class Forcefield(HasTraits):
    #-- Trait Definitions ----------------------------------
    protein = Enum('amber99sb.xml', ['amber03.xml', 'amber03_gbvi.xml',
                                     'amber03_obc.xml', 'amber10.xml',
                                     'amber10_gbvi.xml', 'amber10_obc.xml',
                                     'amber96.xml', 'amber96_gbvi.xml',
                                     'amber96_obc.xml', 'amber99_gbvi.xml',
                                     'amber99_obc.xml', 'amber99sb.xml',
                                     'amber99sbildn.xml', 'amber99sbnmr.xml'],
                    label='protein',
                    help='which forcefield to use for the protein')
    water = Enum('tip3p.xml', ['spce.xml', 'tip3p.xml', 'tip4pew.xml',
                               'tip5p.xml'],
                    label='water',
                    help='which forcefield to use for water')
    water_active = Bool(True, help='''flag indicating whether the "water"
        variable is actually required. to be set dynamically by the value
        of protein (i.e. if protein indicates an implicit solvent...)''')

    def _protein_changed(self, protein):
        self.water_active = not (("gbvi" in protein) or ("obc" in protein))

    #-- Trait View Definitions -----------------------------
    main_group = Group(Item(name='protein'))
    water_group = Group(Item(name='water'),
        visible_when='water_active')
    view = View(Group(main_group, water_group, show_border=True,
        label='Forcefield'), resizable=True)


class Integrator(HasTraits):
    #-- Trait Definitions ----------------------------------
    # general traits
    timestep = UnittedFloat(2.0*unit.femtosecond)
    kind = Enum('Langevin', ['Verlet', 'Langevin', 'Brownian'])
    stochastic_active = Bool(True, help='''flag indicating whether or not
        the special options for stochastic integrators should be
        displayed''')

    def _kind_changed(self, kind):
        self.stochastic_active = (kind in ["Langevin", "Brownian"])

    # traits for stochastic integrators only only:
    temperature = UnittedFloat(300.0*unit.kelvin)
    friction = UnittedFloat(91.0/unit.picosecond)

    #-- Trait View Definitions -----------------------------
    main_group = Group('kind', 'timestep',
        show_border=True,)

    stochastic_group = Group('friction', 'temperature',
        label='Addition info for stochastic integrators',
        show_border=True,
        visible_when='stochastic_active',)

    view = View(
        Group(main_group, stochastic_group,
        label='Integrator Options',
        show_border=True),
        resizable=True,)


class System(HasTraits):
    #-- Trait Definitions ----------------------------------
    nonbonded_method = Enum('PME', ['NoCutoff', 'CutoffNonPeriodic',
                                    'CutoffPeriodic', 'Ewald', 'PME'])
    nonbonded_cutoff = UnittedFloat(1*unit.nanometers)
    constraints = Enum('None', ['None', 'HBonds', 'HAngles', 'AllBonds'])
    rigid_water = Bool(True)
    nonbonded_cutoff_active = Bool(True, help='''flag indicating whether
        or not the nonbonded_cutoff option is required (depends on the
        nonbonded_method)''')

    def _nonbonded_method_changed(self, nonbonded_method):
        self.nonbonded_cutoff_active = (nonbonded_method != 'NoCutoff')

    #-- Trait View Definitions -----------------------------
    main_group = Group('nonbonded_method', 'constraints', 'rigid_water')
    cutoff_group = Group(Item('nonbonded_cutoff'),
        visible_when = 'nonbonded_cutoff_active')
    view = View(Group(main_group, cutoff_group, show_border=True,
        label='System Options'), resizable=True)


class Reporters(HasTraits):
    dcd_active = Bool(True, label='Use DCDReporter')
    dcd_freq = Int(100, help='frequency to print to dcd file (timesteps)',
        label='DCD freq. [steps]')
    dcd_out = Regex('output.dcd', regex='.+\.dcd$', label='DCD output')

    statedata_active = Bool(True, label='Use StateDataReporter')
    statedata_freq = Int(100, label='StateData Freq. [steps]')

    main_group = Group('dcd_active', 'statedata_active')
    dcd_group = Group('dcd_freq', 'dcd_out',
        show_border=True,
        label='DCDReporter Options',
        visible_when='dcd_active')
    statedata_group=Group('statedata_freq',
        show_border=True,
        label='StateDataReporter Options',
        visible_when='statedata_active')
    view = View(Group(main_group, dcd_group, statedata_group,
                      show_border=True,
                      label='Reporters',
                ), resizable=True)


class Simulation(HasTraits):
    #-- Trait Definitions ----------------------------------
    n_steps = Int(1000, help='Number of time steps to run', label='Number of steps')

    minimize = Bool(True, help='Run minimization first', label='Minimize First')
    minimize_max_iters = Int(100, help='''Maximum number of iterations of
        minimization to run''', label='Max minimization iterations')

    #-- Trait View Definitions -----------------------------
    main_group = Group('n_steps')
    minimize_group = Group('minimize', 'minimize_max_iters',
        show_border=True,
        label='Minimization Options',
        visible_when = 'minimize')
    view = View(Group(main_group, minimize_group, show_border=True,
                      label='Simulation Options'), resizable=True)