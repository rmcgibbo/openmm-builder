"""
Chaco GUI environment to exec an OpenMM script, dynamically capturing
the output from a StateDataReporter and plotting it to the screen, live.
"""
##############################################################################
# Imports
##############################################################################

# stdlib
import os
import StringIO
import time
import Queue
import threading
import itertools
import tokenize

# enthought
from traits.api import HasTraits, String, Bool, Instance
from traitsui.api import View, Item, Group, HGroup, spring
from enable.component_editor import ComponentEditor
from chaco.api import Plot, ArrayPlotData, PlotAxis, VPlotContainer

import numpy as np

# openmm
from simtk.openmm.app import StateDataReporter


##############################################################################
# Functions
##############################################################################


def queue_reporter_factory(queue):
    """Factory function that returns a dynamically defined OpenMM
    reporter class which reports by sending dicts down a synchronous queue"""

    class QueueStateDataReporter(StateDataReporter):
        """Subclass of StateDataReporter sends its results down a synchronous
        Queue, as opposed to printing them to a file-like object
        """

        def __init__(self, file, *args, **kwargs):
            with open(os.devnull, 'w') as f:
                # send in a fake file
                super(QueueStateDataReporter, self).__init__(f, *args, **kwargs)

            # this is where we'll store the names of the fields that
            # are being reported in
            self._headers = []

        def report(self, simulation, state):
            was_initialized = self._hasInitialized

            # spoof the file-like object with a string buffer
            self._out = StringIO.StringIO()
            super(QueueStateDataReporter, self).report(simulation, state)


            if not was_initialized:
                # the first report has two lines on it -- we want to
                # look at the first, as it contains the headers
                initial, line = self._out.getvalue().split(os.linesep, 1)
                headers = initial.strip().split(self._separator)
                # filter out some extra quotation marks and comment
                # characters
                self._headers = [e.strip('#"\'') for e in headers]
            else:
                line = self._out.getvalue()

            # split the line based on whatever separator we know
            # that the parent was using, and then cast to float
            values = map(float, line.strip().split(self._separator))
            msg = dict(zip(self._headers, values))
            queue.put(msg)


    return QueueStateDataReporter


def run_openmm_script(code, queue):
    """Run an OpenMM script, dynamiclly redefining a StateDataReporter
    to capture the output, sending it into this queue
    """

    def fix_code():
        """Replae the token 'StateDataReporter' with
        '__queue_reporter_factory(__queue)'

        Also, we make sure that the sentenel signal (None) is sent
        down the queue at the very end of the script
        """
        itoks = tokenize.generate_tokens(StringIO.StringIO(code).readline)
        def run():
            for toktype, toktext, (srow, scol), (erow, ecol), line in itoks:
                if toktext == 'StateDataReporter':
                    toktext = '__queue_reporter_factory(__queue)'
                yield (toktype, toktext, (srow, scol), (erow, ecol), line)

        return tokenize.untokenize(run()) + '__queue.put(None)'

    try:
        code = fix_code()
    except tokenize.TokenError:
        raise ValueError('The script has a syntax error!')

    exec code in globals(), {'__queue': queue,
                '__queue_reporter_factory': queue_reporter_factory}


def chaco_scatter(dataview, x_name, y_name, x_label=None, y_label=None,
                  color=None):
    """Utility function to build a chaco scatter plot
    """

    plot = Plot(dataview)
    plot.plot((x_name, y_name), type="scatter", marker='dot', color=color)

    if x_label is None:
        x_label = x_name
    if y_label is None:
        y_label = y_name
    x_axis = PlotAxis(mapper=plot.x_mapper, orientation='bottom', title=x_label)
    y_axis = PlotAxis(mapper=plot.y_mapper, orientation='left', title=y_label)
    plot.underlays.append(x_axis)
    plot.underlays.append(y_axis)
    return plot


##############################################################################
# Classes
##############################################################################


class OpenMMScriptRunner(HasTraits):
    plots = Instance(VPlotContainer)
    plots_created = Bool
    openmm_script_code = String
    status = String

    traits_view = View(
        Group(
            HGroup(spring, Item('status', style='readonly'), spring),
            Item('plots', editor=ComponentEditor(),
                show_label=False)
        ),
        width=800, height=600, resizable=True,
        title='OpenMM Script Runner'
    )


    def __init__(self, **traits):
        super(OpenMMScriptRunner, self).__init__(**traits)

        self._plots_created = False

        q = Queue.Queue()
        # start up two threads. the first, t1, will run the script
        # and place the statedata into the queue
        # the second will remove elements from the queue and update the
        # plots in the UI
        t1 = threading.Thread(target=run_openmm_script,
                              args=(self.openmm_script_code, q))
        t2 = threading.Thread(target=self.queue_consumer, args=(q,))
        t1.start()
        t2.start()

    def queue_consumer(self, q):
        """Main loop for a thread that consumes the messages from the queue
        and plots them"""

        self.status = 'Running...'

        while True:
            try:
                msg = q.get_nowait()
                if msg is None:
                    break
                self.update_plot(msg)
            except Queue.Empty:
                time.sleep(0.1)

        self.status = 'Done'

    def create_plots(self, keys):
        """Create the plots

        Paramters
        ---------
        keys : list of strings
            A list of all of the keys in the msg dict. This should be something
            like ['Step', 'Temperature', 'Potential Energy']. We'll create the
            ArrayPlotData container in which each of these timeseries will
            get put.
        """

        self.plots = VPlotContainer(resizable = "hv", bgcolor="lightgray",
                               fill_padding=True, padding = 10)
        # this looks cryptic, but it is equivalent to
        # ArrayPlotData(a=[], b=[], c=[])
        # if the keys are a,b,c. This just does it for all of the keys.
        self.plotdata = ArrayPlotData(**dict(zip(keys, [[]]*len(keys))))

        # figure out which key will be the x axis
        if 'Step' in keys:
            x = 'Step'
        elif 'Time (ps)' in keys:
            x = 'Time (ps)'
        else:
            raise ValueError('The reporter published neither the step nor time'
                'count, so I don\'t know what to plot on the x-axis!')


        colors = itertools.cycle(['blue', 'green', 'silver', 'pink', 'lightblue',
                                  'red', 'darkgray', 'lightgreen',])
        for y in filter(lambda y: y != x, keys):
            self.plots.add(chaco_scatter(self.plotdata, x_name=x, y_name=y,
                                         color=colors.next()))

    def update_plot(self, msg):
        """Add data points from the message to the plots

        Paramters
        ---------
        msg : dict
            This is the message sent over the Queue from the script
        """
        if not self.plots_created:
            self.create_plots(msg.keys())
            self.plots_created = True

        for k, v in msg.iteritems():
            current = self.plotdata.get_data(k)
            self.plotdata.set_data(k, np.r_[current, v])
