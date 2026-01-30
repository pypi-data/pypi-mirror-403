from pathlib import Path

import numpy as np
import pytest

from trap import io


@pytest.mark.parametrize(
    "path, expected_nr_files",
    [
        ("tests/data/lofar1", 3),
        ("tests/data/lofar1/*", 3),
        ("tests/data/lofar1/GRB201006A_final_2min_srcs-t000*-image-pb.fits", 3),
        ("tests/data/lofar1/GRB201006A_final_2min_srcs-t0001-image-pb.fits", 1),
        ("tests/data*/lofar*/GRB201006A_*.fits", 3),
    ],
)
def test_find_fits(path, expected_nr_files):
    fits_files = io.find_fits(path)

    assert len(fits_files) == expected_nr_files
    for f in fits_files:
        assert isinstance(f, Path)
        assert f.exists()


def test_source_list_from_db():
    """Here we test the reconstruction of a source list from an existing database.
    The source list must fit the format to be usable in association.
    The test checks each of the columns in the reconstruction through a proxy (mean or sum).
    These proxies are meant to serve as a check that fails the test if one or more of the
    values in the columns change.
    This is not a perfect check, i.e. values can be swapped and the mean and sum would not change,
    but it saves having to store the full expected table.
    """
    project_root = Path(__file__).resolve().parents[1]
    db_path = project_root / "tests/data/lofar1/GRB201006A_60_images.db"
    reconstructed_source_list = io.source_list_from_db("sqlite", str(db_path))

    # Make sure there are no NaN values in the table, this would indicate an incomplete reconstruction
    assert np.all(
        np.isfinite(reconstructed_source_list.to_numpy())
    ), "Found NaN values in reconstructed_source_list"

    # Validate nr_consecutive_force_fits column
    expected_nr_sources_with_consecutive_force_fit = sum(
        reconstructed_source_list.nr_consecutive_force_fits > 0
    )
    assert expected_nr_sources_with_consecutive_force_fit == 229
    assert reconstructed_source_list.nr_consecutive_force_fits.sum() == 1859

    # Validate the index of the dataframe ('src_id')
    np.testing.assert_array_equal(
        reconstructed_source_list.index, range(0, len(reconstructed_source_list))
    )
    # Validate ra and dec
    assert reconstructed_source_list.ra.mean() == 61.95652894911309
    assert reconstructed_source_list.dec.mean() == 65.13534756583392
    # Validate latest_extracted_source_id. The src_id (df index) is expected to be a neat range,
    # but that is not the case here. We therefore test the sum to still get a quick indication
    # if a extracted source index changed.
    assert reconstructed_source_list.latest_extracted_source_id.sum() == 6882916
