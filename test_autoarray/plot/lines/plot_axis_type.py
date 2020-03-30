import autoarray.plot as aplt
import numpy as np

aplt.Line(
    y=np.array([1.0, 2.0, 3.0]), x=np.array([0.5, 1.0, 1.5]), plot_axis_type="linear"
)
aplt.Line(
    y=np.array([1.0, 2.0, 3.0]), x=np.array([0.5, 1.0, 1.5]), plot_axis_type="semilogy"
)
aplt.Line(
    y=np.array([1.0, 2.0, 3.0]), x=np.array([0.5, 1.0, 1.5]), plot_axis_type="loglog"
)
aplt.Line(
    y=np.array([1.0, 2.0, 3.0]), x=np.array([0.5, 1.0, 1.5]), plot_axis_type="scatter"
)
