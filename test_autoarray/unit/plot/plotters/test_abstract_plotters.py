from os import path
import matplotlib.pyplot as plt

import autoarray.plot as aplt
from autoarray.plot.plotters import abstract_plotters

directory = path.dirname(path.realpath(__file__))


class TestFromFunc:
    def test__title_from_func__uses_func_name_if_title_is_none(self):
        def toy_func():
            pass

        title_from_func = abstract_plotters.title_from_func(func=toy_func)

        assert title_from_func == "Toy_func"

        def figure_toy_func():
            pass

        title_from_func = abstract_plotters.title_from_func(func=figure_toy_func)

        assert title_from_func == "Toy_func"

    def test__units_from_func__uses_function_inputs_if_available(self):
        def toy_func():
            pass

        units_from_func = abstract_plotters.units_from_func(func=toy_func)

        assert units_from_func == None

        def toy_func(label_yunits="Hi"):
            pass

        units_from_func = abstract_plotters.units_from_func(
            func=toy_func, for_ylabel=True
        )
        assert units_from_func == "Hi"

        units_from_func = abstract_plotters.units_from_func(
            func=toy_func, for_ylabel=False
        )
        assert units_from_func == None

        def toy_func(label_xunits="Hi"):
            pass

        units_from_func = abstract_plotters.units_from_func(
            func=toy_func, for_ylabel=False
        )
        assert units_from_func == "Hi"

        units_from_func = abstract_plotters.units_from_func(
            func=toy_func, for_ylabel=True
        )
        assert units_from_func == None

    def test__filename_from_func__returns_function_name_if_no_filename(self):
        def toy_func():
            pass

        filename_from_func = abstract_plotters.filename_from_func(func=toy_func)

        assert filename_from_func == "toy_func"

        def figure_toy_func():
            pass

        filename_from_func = abstract_plotters.filename_from_func(func=figure_toy_func)

        assert filename_from_func == "toy_func"


class TestDecorator:
    def test__kpc_per_scaled_extacted_from_object_if_available(self):

        kwargs = {"hi": 1}

        kpc_per_scaled = abstract_plotters.kpc_per_scaled_of_object_from_kwargs(
            kwargs=kwargs
        )

        assert kpc_per_scaled == None

        class MockObj:
            def __init__(self, param1):

                self.param1 = param1

        obj = MockObj(param1=1)

        kwargs = {"hi": 1, "hello": obj}

        kpc_per_scaled = abstract_plotters.kpc_per_scaled_of_object_from_kwargs(
            kwargs=kwargs
        )

        assert kpc_per_scaled == None

        class MockObj:
            def __init__(self, param1, kpc_per_scaled):

                self.param1 = param1
                self.kpc_per_scaled = kpc_per_scaled

        obj = MockObj(param1=1, kpc_per_scaled=2)

        kwargs = {"hi": 1, "hello": obj}

        kpc_per_scaled = abstract_plotters.kpc_per_scaled_of_object_from_kwargs(
            kwargs=kwargs
        )

        assert kpc_per_scaled == 2


class TestAbstractPlotter:
    def test__subplot_figsize_for_number_of_subplots(self):

        plotter = abstract_plotters.AbstractPlotter()

        figsize = plotter.get_subplot_figsize(number_subplots=1)

        assert figsize == (18, 8)

        figsize = plotter.get_subplot_figsize(number_subplots=4)

        assert figsize == (13, 10)

        figure = aplt.Figure(figsize=(20, 20))

        plotter = abstract_plotters.AbstractPlotter(
            mat_plot_2d=aplt.MatPlot2D(figure=figure)
        )

        figsize = plotter.get_subplot_figsize(number_subplots=4)

        assert figsize == (20, 20)

    def test__plotter_number_of_subplots(self):

        plotter = abstract_plotters.AbstractPlotter()

        rows, columns = plotter.get_subplot_rows_columns(number_subplots=1)

        assert rows == 1
        assert columns == 2

        rows, columns = plotter.get_subplot_rows_columns(number_subplots=4)

        assert rows == 2
        assert columns == 2

    def test__open_and_close_subplot_figures(self):

        figure = aplt.Figure(figsize=(20, 20))

        plotter = abstract_plotters.AbstractPlotter(
            mat_plot_2d=aplt.MatPlot2D(figure=figure)
        )

        plotter.mat_plot_2d.figure.open()

        assert plt.fignum_exists(num=1) == True

        plotter.mat_plot_2d.figure.close()

        assert plt.fignum_exists(num=1) == False

        plotter = abstract_plotters.AbstractPlotter(
            mat_plot_2d=aplt.MatPlot2D(figure=figure)
        )

        assert plt.fignum_exists(num=1) == False

        plotter.open_subplot_figure(number_subplots=4)

        assert plt.fignum_exists(num=1) == True

        plotter.mat_plot_2d.figure.close()

        assert plt.fignum_exists(num=1) == False

    def test__uses_figure_or_subplot_configs_correctly(self):

        figure = aplt.Figure(figsize=(8, 8))
        cmap = aplt.Cmap(cmap="warm")

        mat_plot_2d = aplt.MatPlot2D(figure=figure, cmap=cmap)

        plotter = abstract_plotters.AbstractPlotter(mat_plot_2d=mat_plot_2d)

        assert plotter.mat_plot_2d.figure.config_dict_figure["figsize"] == (8, 8)
        assert plotter.mat_plot_2d.figure.config_dict_imshow["aspect"] == "square"
        assert plotter.mat_plot_2d.cmap.config_dict["cmap"] == "warm"
        assert plotter.mat_plot_2d.cmap.config_dict["norm"] == "linear"

        figure = aplt.Figure()
        figure.for_subplot = True

        cmap = aplt.Cmap()
        cmap.for_subplot = True

        mat_plot_2d = aplt.MatPlot2D(figure=figure, cmap=cmap)

        plotter = abstract_plotters.AbstractPlotter(mat_plot_2d=mat_plot_2d)

        assert plotter.mat_plot_2d.figure.config_dict_figure["figsize"] == None
        assert plotter.mat_plot_2d.figure.config_dict_imshow["aspect"] == "square"
        assert plotter.mat_plot_2d.cmap.config_dict["cmap"] == "jet"
        assert plotter.mat_plot_2d.cmap.config_dict["norm"] == "linear"