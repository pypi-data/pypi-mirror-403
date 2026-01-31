import xarray as xr
import numpy as np

def to_gridded_dataset(dataset: xr.Dataset, dimension: str = "dim_0") -> xr.Dataset:
    '''
    Converts a quantify dataset to a gridded dataset.
    '''
    if dimension not in dataset.dims:
        raise ValueError(f"Dimension {dimension} not in dims {dataset.dims}.")
    if "grid_2d" in dataset.attrs:
        # In some cases the type does not seem to be a python type, so checking for numpy type as well.
        if isinstance(dataset.attrs["grid_2d"], bool) and dataset.attrs["grid_2d"] is False:
            raise ValueError("Dataset is not gridded, this function cannot be applied.")
        if isinstance(dataset.attrs["grid_2d"], np.bool_) and dataset.attrs["grid_2d"] == np.bool_(False):
            raise ValueError("Dataset is not gridded, this function cannot be applied.")
    
    coords_names = sorted(v for v in dataset.variables if v.startswith("x"))[::-1]
    # legacy datasets saved this in vars ...
    dataset = dataset.set_coords(coords_names)

    if len(coords_names) == 1:
        # No unstacking needed just swap the dimension
        for var in dataset.data_vars:
            if dimension in dataset[var].dims:
                dataset = dataset.update(
                    {var: dataset[var].swap_dims({dimension: coords_names[0]})},
                )
    else:
        dataset = dataset.set_index({dimension: coords_names})
        dataset = dataset.unstack(dim=dimension)

    # per quantify convention.
    if "grid_2d" in dataset.attrs:
        dataset.attrs["grid_2d"] = False
    
    return dataset