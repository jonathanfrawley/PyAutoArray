import autoarray as aa

plotter = aa.plotter.Plotter()

array = aa.array.ones(shape_2d=(31, 31), pixel_scales=(1.0, 1.0), sub_size=2)
array[0] = 3.0

plotter.array.plot(array=array, points=[[(1.0, 1.0), (2.0, 2.0)], [(-1.0, -1.0)]])
