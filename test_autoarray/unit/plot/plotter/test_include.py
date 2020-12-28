from autoarray.plot.plotter import include as inc


def test__loads_default_values_from_config_if_not_input():

    include = inc.Include()

    assert include.origin == True
    assert include.mask == True
    assert include.grid == True
    assert include.border == True
    assert include.parallel_overscan == True
    assert include.serial_prescan == True
    assert include.serial_overscan == False

    include = inc.Include(origin=False, border=False, serial_overscan=True)

    assert include.origin == False
    assert include.mask == True
    assert include.grid == True
    assert include.border == False
    assert include.parallel_overscan == True
    assert include.serial_prescan == True
    assert include.serial_overscan == True


def test__visuals_from_array(array_7x7):

    include = inc.Include(origin=True, mask=True, border=True)

    visuals = include.visuals_from_array(array=array_7x7)

    assert visuals.origin.in_1d_list == [(0.0, 0.0)]
    assert (visuals.mask == array_7x7.mask).all()
    assert (
        visuals.border == array_7x7.mask.geometry.border_grid_sub_1.in_1d_binned
    ).all()

    include = inc.Include(origin=False, mask=False, border=False)

    visuals = include.visuals_from_array(array=array_7x7)

    assert visuals.origin == None
    assert visuals.mask == None
    assert visuals.border == None


def test__visuals_from_frame(frame_7x7):

    include = inc.Include(origin=True, mask=True, border=True)

    visuals = include.visuals_from_frame(frame=frame_7x7)

    assert visuals.origin.in_1d_list == [(0.0, 0.0)]
    assert (visuals.mask == frame_7x7.mask).all()
    assert (
        visuals.border == frame_7x7.mask.geometry.border_grid_sub_1.in_1d_binned
    ).all()

    include = inc.Include(origin=False, mask=False, border=False)

    visuals = include.visuals_from_frame(frame=frame_7x7)

    assert visuals.origin == None
    assert visuals.mask == None
    assert visuals.border == None


def test__visuals_from_grid(grid_7x7):

    include = inc.Include(origin=True, mask=True, border=True)

    visuals = include.visuals_from_grid(grid=grid_7x7)

    assert visuals.origin.in_1d_list == [(0.0, 0.0)]
    assert (visuals.mask == grid_7x7.mask).all()
    assert (
        visuals.border == grid_7x7.mask.geometry.border_grid_sub_1.in_1d_binned
    ).all()

    include = inc.Include(origin=False, mask=False, border=False)

    visuals = include.visuals_from_grid(grid=grid_7x7)

    assert visuals.origin == None
    assert visuals.mask == None
    assert visuals.border == None
