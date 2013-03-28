# we need to make sure we're using qt right at the beginning
# because on my machine, wx (the default) doesn't work at all (?)
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'

import os
import pystache
from traits.api import (HasTraits, Str, Int, Enum, Float, Instance,
                        Button, String, Bool, Code, File)
from traitsui.api import (View, Item, Group, Handler,  VGroup, HGroup, HSplit)


class InputFile(HasTraits):
    file = File(os.path.abspath('.'), filter=['*.pdb'])

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
                    label='protein')
    water = Enum('tip3p.xml', ['spce.xml', 'tip3p.xml', 'tip4pew.xml',
                               'tip5p.xml'],
                    label='water')
    water_active = Bool(True)

    def _protein_changed(self, protein):
        self.water_active = not (("gbvi" in protein) or ("obc" in protein))

    #-- Trait View Definitions ----------------------------------
    main_group = Group(Item(name='protein'))
    water_group = Group(Item(name='water'),
        visible_when='water_active')
    view = View(Group(main_group, water_group, show_border=True,
        label='Forcefield'), resizable=True)


class Integrator(HasTraits):
    #-- Trait Definitions ----------------------------------
    # general traits
    timestep = Float
    kind = Enum('Langevin', ['Verlet', 'Langevin', 'Brownian'])
    stochastic_active = Bool(True)

    def _kind_changed(self, kind):
        self.stochastic_active = (kind in ["Langevin", "Brownian"])

    # traits for stochastic integrators only only:
    temperature = Float
    friction = Float

    #-- Trait View Definitions ----------------------------------
    main_group = Group(
        Item(name='kind'),
        Item(name='timestep'),
        show_border=True
    )

    stochastic_group = Group(
        Item(name='friction'),
        Item(name='temperature'),
        label='Addition info for stochastic integrators',
        show_border=True,
        visible_when='stochastic_active')

    view = View(
        Group(main_group,
        stochastic_group,
        label='Integrator Options',
        show_border=True),
        resizable=True,
    )

    def validate(self):
        raise ValueError('Sorry!')


class System(HasTraits):
    #-- Trait Definitions ----------------------------------
    nonbonded_method = Enum('PME', ['NoCutoff', 'CutoffNonPeriodic',
                                    'CutoffPeriodic', 'Ewald', 'PME'])
    nonbonded_cutoff = Float(10)
    constraints = Enum('None', ['None', 'HBonds', 'HAngles', 'AllBonds'])
    rigid_water = Bool(True)
    nonbonded_cutoff_active = Bool(True)

    def _nonbonded_method_changed(self, nonbonded_method):
        self.nonbonded_cutoff_active = (nonbonded_method != 'NoCutoff')

    #-- Trait View Definitions ----------------------------------
    main_group = Group('nonbonded_method', 'constraints', 'rigid_water')
    cutoff_group = Group(Item('nonbonded_cutoff'),
        visible_when = 'nonbonded_cutoff_active')
    view = View(Group(main_group, cutoff_group, show_border=True,
        label='System Options'), resizable=True)


class App(HasTraits):
    inputfile = Instance(InputFile(), InputFile)
    forcefield = Instance(Forcefield(), Forcefield)
    integrator = Instance(Integrator(), Integrator)
    system = Instance(System(), System)
    display = Code
    #create = Button('Create Script!')

    renderer = pystache.Renderer()
    template = pystache.parse(u'''
    from simtk.openmm.app import *
    from simtk.openmm import *
    from simtk.unit import *

    print('Loading...')
    pdb = PDBFile('{{inputfile.file}}')
    forcefield = ForceField('{{forcefield.protein}}'{{#forcefield.water_active}}, '{{forcefield.water}}'{{/forcefield.water_active}})

    system = forcefield.createSystem(pdb.topology, nonbondedMethod={{system.nonbonded_method}},
        {{#system.nonbonded_cutoff_active}}nonbondedCutoff={{system.nonbonded_cutoff}},{{/system.nonbonded_cutoff_active}} constraints={{system.constraints}}, rigidWater={{system.rigid_water}})
    integrator = {{integrator.kind}}Integrator({{#integrator.stochastic_active}}{{integrator.temperature}}, {{integrator.friction}}, {{/integrator.stochastic_active}}{{integrator.timestep}})

    simulation = Simulation(pdb.topology, system, integrator)
    simulation.context.setPositions(pdb.positions)
    simulation.minimizeEnergy(maxIterations=100)
    print('Saving...')
    positions = simulation.context.getState(getPositions=True).getPositions()
    PDBFile.writeFile(simulation.topology, positions, open('output.pdb', 'w'))
    print('Done')
    ''')


    #-- Trait View Definitions ----------------------------------
    view = View(
        HSplit(
            VGroup(
                Item('inputfile',  show_label=False, width=50),
                Item('forcefield', show_label=False, width=50),
                Item('integrator', show_label=False, width=50),
                Item('system',     show_label=False, width=50),
                #Item('create',     show_label=False, width=50),
            ),
            Item('display', show_label=False)
        ),
        style='custom',
        title='OpenMM Script Builder',
        resizable=True
    )

    def __init__(self, **traits):
        # register dynamic handlers that rebuild the script
        # anytime a trait changes
        self.inputfile.on_trait_change(self.update_display)
        self.forcefield.on_trait_change(self.update_display)
        self.integrator.on_trait_change(self.update_display)
        self.system.on_trait_change(self.update_display)

        super(App, self).__init__(**traits)

    def update_display(self):
        contents = self.renderer.render(self.template, self)
        self.display = '\n'.join([line[4:] for line in contents.split('\n')[1:]])

if __name__ == '__main__':
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    App().configure_traits()
