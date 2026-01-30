import sys
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt



cwd = Path(__file__).parent
if cwd.exists():
    sys.path.insert(0, cwd.as_posix())

from petal_qc.thermal import PipeFit, contours, DebugPlot

# create a global instance of DebugPlot
debug_plot = DebugPlot.DebugPlot()


class PipeIterFit:
    """makes an iterative fit removing outliers in each iteration."""

    def __init__(self, data):
        """Initialize class."""
        self.data = data
        ptype = PipeFit.PipeFit.guess_pipe_type(data)
        self.PF = PipeFit.PipeFit(ptype)

    def remove_outsiders(self, data, thrs):
        """Removes points which are further than thrs from the fit."""
        D = np.zeros(len(data))
        out = self.PF.transform_data(data, self.PF.R)
        i = 0
        for x, y in out:
            dst, P = contours.find_closest_point(x, y, self.PF.pipe)
            D[i] = dst
            i += 1

        indx = np.where(D < thrs)[0]
        return np.array(data[indx, :])

    def fit(self, threshold=20, factor=1.0, debug=False):
        """Do the fit."""
        global debug_plot
        if debug:
            debug_plot.setup_debug('IterFit')
        
        
        total_data = self.data
        data_size = len(total_data)

        M0 = self.PF.fit_ex(total_data, factor=factor, simplify=True)
        sample_data = self.remove_outsiders(self.PF.data, threshold)
        last_size = len(sample_data)
        if debug:
            ax = debug_plot.get_ax("IterFit")
            ax.clear()
            ax.plot(total_data[:, 0], total_data[:, 1], 'o')
            ax.plot(sample_data[:, 0], sample_data[:, 1], 'P')
            plt.draw()
            plt.pause(0.0001)
            
        # Adaptively determining the number of iterations
        while True:
            M0 = self.PF.fit_ex(sample_data, M0=M0, factor=factor, simplify=False)

            out = self.PF.transform_data(self.PF.data, M0)
            D = []
            for x, y in out:
                dst, P = contours.find_closest_point(x, y, self.PF.pipe)
                D.append(dst)

            if debug:
                ax = debug_plot.get_ax("IterFit")
                ax.clear()
                ax.hist(D)
                plt.draw()
                plt.pause(0.0001)
                self.PF.plot(ax=ax)
            
            sample_data = self.remove_outsiders(self.PF.data, 20)
            sample_size = len(sample_data)
            if sample_size == last_size:
                break

            last_size = sample_size

        if debug:
            self.PF.plot(ax=ax)
            
        return M0

    def plot(self):
        """Plot this fit."""
        global debug_plot
        self.PF.plot(ax=debug_plot.get_ax("IterFit"))
