import os, sys
from traits.etsconfig.api import ETSConfig
ETSConfig.toolkit = 'qt4'
from traits.api import (HasTraits, Str, Int, Enum, Float, Instance,
                        Button, String, Bool, Code, File)
from traitsui.api import View, Item, Group, Handler,  VGroup, HGroup, HSplit


class InputFile(HasTraits):
    file = File(exists=True)
    
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
                    desc='The forcefield for protein')
    water = Enum('tip3p.xml', ['spce.xml', 'tip3p.xml', 'tip4pew.xml',
                               'tip5p.xml'],
                    label='water',
                    desc='The water forcefield')

    #-- Trait View Definitions ----------------------------------
    main_group = Group(Item(name='protein'))
    water_group = Group(Item(name='water'),
        visible_when='not (("gbvi" in protein) or ("obc" in protein))')
    view = View(Group(main_group, water_group, show_border=True,
        label='Forcefield'), resizable=True)


class Integrator(HasTraits):
    #-- Trait Definitions ----------------------------------
    # general traits
    timestep = Float
    kind = Enum(['Verlet', 'Langevin', 'Brownian'])

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
        visible_when='kind in ["Langevin", "Brownian"]')

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
    nonbonded_cutoff = Float
    constraints = Enum('None', ['None', 'HBonds', 'HAngles', 'AllBonds'])
    rigid_water = Bool(False)

    #-- Trait View Definitions ----------------------------------
    main_group = Group('nonbonded_method', 'constraints', 'rigid_water')
    cutoff_group = Group(Item('nonbonded_cutoff'),
        visible_when='nonbonded_method != "NoCutoff"')
    view = View(Group(main_group, cutoff_group, show_border=True,
        label='System Options'), resizable=True)


class App(HasTraits):
    inputfile = Instance(InputFile(), InputFile)
    forcefield = Instance(Forcefield(), Forcefield)
    integrator = Instance(Integrator(), Integrator)
    system = Instance(System(), System)
    display = Code
    create = Button('Create Script!')
    
    #-- Trait View Definitions ----------------------------------
    view = View(
        HSplit(
            VGroup(
                Item('inputfile',  show_label=False, width=50),
                Item('forcefield', show_label=False, width=50),
                Item('integrator', show_label=False, width=50),
                Item('system',     show_label=False, width=50),
                Item('create',     show_label=False, width=50),
            ),
            Item('display', show_label=False)
        ),
        style='custom',
        resizable=True
    )
    
    def _create_fired(self):
        try:
            self.integrator.validate()
        except Exception as e:
            self.display = '%s: %s' % (e.__class__.__name__, e.message)


App().configure_traits()
