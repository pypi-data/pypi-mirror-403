from pathlib import Path

import torchio as tio


def load_sample_ct(clip: bool = True) -> tio.ScalarImage:
    """Get a sample CT image."""
    ct = get_sample_ct()
    if clip:
        clamp = tio.Clamp(-1000, 1000)
        ct = clamp(ct)
    else:
        ct.load()
    return ct


def get_sample_ct() -> tio.ScalarImage:
    """Download a sample CT image if not already present."""
    return tio.datasets.Slicer("CTChest").CT_chest  # type: ignore[reportAttributeAccessIssue]


def get_sample_ct_path() -> Path:
    """Get the path to a sample CT image."""
    return get_sample_ct().path  # type: ignore[reportReturnType]
