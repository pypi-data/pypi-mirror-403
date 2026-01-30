import pathlib
from importlib import metadata

import asdf
import astropy.units as u
import dkist
import numpy as np
import pytest
from dkist.dataset import Dataset
from dkist.dataset import TiledDataset
from dkist.io import DKISTFileManager
from dkist_data_simulator.spec214.vbi import SimpleVBIDataset

from dkist_inventory.asdf_generator import asdf_tree_from_filenames
from dkist_inventory.asdf_generator import dataset_from_fits
from dkist_inventory.asdf_generator import references_from_filenames
from dkist_inventory.header_parsing import HeaderParser


@pytest.fixture()
def mock_input_dataset_parts() -> list[dict]:
    """Parameters in the shape dkist_inventory.ParameterParser expects (list[dict])."""
    return [
        {
            "parameterName": "test_param1",
            "parameterValues": [
                {
                    "parameterValue": "100",
                    "parameterValueId": 1,
                    "parameterValueStartDate": "2022-01-01T00:00:00",
                }
            ],
        },
        {
            "parameterName": "test_param2",
            "parameterValues": [
                {
                    "parameterValue": "true",
                    "parameterValueId": 2,
                    "parameterValueStartDate": "2022-01-02T00:00:00",
                }
            ],
        },
    ]


@pytest.fixture()
def mock_frame_documents() -> list[dict]:
    """Frame documents in the shape dkist_inventory.InputFrameMetadata expects (list[dict])."""
    return [
        {
            "bucket": "raw",
            "object_keys": [
                "pid_1_118/eid_1_118_opAvoqBr_R001.82591.13964206/2a726c8921fc43cf970dfcedc3ec3ec5.fits",
                "pid_1_118/eid_1_118_opAvoqBr_R001.82591.13964206/6ee53e057f8a46419366abc7dc077edc.fits",
            ],
        }
    ]


def test_array_container_shape(header_filenames):
    header_parser = HeaderParser.from_filenames(header_filenames, hdu=0)
    header_parser = header_parser.group_mosaic_tiles()[0]

    # References from filenames
    array_container = references_from_filenames(header_parser, hdu_index=0, relative_to=".")
    assert array_container.output_shape == array_container.dask_array.shape


def test_asdf_tree(header_filenames):
    tree = asdf_tree_from_filenames(header_filenames)
    assert isinstance(tree, dict)


def test_asdf_tree_with_headers_and_inventory_args():
    # given
    file_count = 5
    headers = []
    file_names = []
    for i, ds in enumerate(
        SimpleVBIDataset(
            n_time=file_count,
            time_delta=1,
            linewave=550 * u.nm,
            detector_shape=(10, 10),
        )
    ):
        h = ds.header()
        h["BITPIX"] = 8
        headers.append(h)
        file_names.append(f"wibble_{i}.fits")
    tree = asdf_tree_from_filenames(file_names, headers)
    assert isinstance(tree, dict)


def test_validator(header_parser):
    header_parser._headers[3]["NAXIS"] = 5
    # vbi-mosaic-single raises a KeyError because it's only one frame
    with pytest.raises((ValueError, KeyError), match="NAXIS"):
        header_parser._validate_headers()


def test_references_from_filenames(header_parser):
    # references_from_filenames only works on a single tile
    header_parser = header_parser.group_mosaic_tiles()[0]
    base = header_parser.filenames[0].parent
    refs: DKISTFileManager = references_from_filenames(
        header_parser,
        relative_to=base,
    )

    for ref in refs.filenames:
        assert base.as_posix() not in ref


def test_dataset_from_fits(header_directory):
    asdf_filename = "test_asdf.asdf"
    asdf_file = pathlib.Path(header_directory) / asdf_filename
    try:
        dataset_from_fits(header_directory, asdf_filename)

        assert asdf_file.exists()

        # Make sure the dang thing is loadable by `dkist`
        assert isinstance(repr(dkist.load_dataset(asdf_file)), str)

        with asdf.open(asdf_file) as adf:
            ds = adf["dataset"]
            assert isinstance(ds, (Dataset, TiledDataset))
            if isinstance(ds, Dataset):
                assert ds.unit is u.count
                # A simple test to see if the headers are 214 ordered
                assert ds.headers.colnames[0] == "SIMPLE"
                assert ds.headers.colnames[1] == "BITPIX"
            elif isinstance(ds, TiledDataset):
                assert ds[0, 0].unit is u.count

            history_entries = adf.get_history_entries()
            assert len(history_entries) == 1
            assert "dkist-inventory" in history_entries[0]["description"]
            software = history_entries[0]["software"]
            assert isinstance(software, dict)
            assert software["name"] == "dkist-inventory"
            assert software["version"] == metadata.distribution("dkist-inventory").version
    finally:
        asdf_file.unlink()


@pytest.fixture
def vtf_data_directory_with_suffix(simulated_dataset, suffix):
    dataset_name = "vtf"  # Chosen because it's light
    return simulated_dataset(dataset_name, suffix=suffix)


@pytest.mark.parametrize("suffix", ["fits", "dat"])
def test_dataset_from_fits_with_different_glob(vtf_data_directory_with_suffix, suffix):
    asdf_filename = "test_asdf.asdf"
    asdf_file = pathlib.Path(vtf_data_directory_with_suffix) / asdf_filename

    test_history = [
        (
            "Written in a dkist-inventory test.",
            {
                "name": "spam",
                "author": "King Arthur",
                "homepage": "https://ni.knight",
                "version": "7",
            },
        )
    ]

    dataset_from_fits(
        vtf_data_directory_with_suffix,
        asdf_filename,
        glob=f"*{suffix}",
        extra_history=test_history,
    )

    try:
        assert asdf_file.exists()

        with asdf.open(asdf_file) as adf:
            ds = adf["dataset"]
            assert isinstance(ds, (Dataset, TiledDataset))
            if isinstance(ds, Dataset):
                assert ds.unit is u.count
                # A simple test to see if the headers are 214 ordered
                assert ds.headers.colnames[0] == "SIMPLE"
                assert ds.headers.colnames[1] == "BITPIX"
            elif isinstance(ds, TiledDataset):
                assert ds[0, 0].unit is u.count

            history_entries = adf.get_history_entries()
            assert len(history_entries) == 2
            assert "dkist-inventory" in history_entries[0]["description"]
            assert history_entries[1]["description"] == test_history[0][0]
            assert history_entries[1]["software"] == test_history[0][1]

    finally:
        asdf_file.unlink()


def test_mosaic_order(simulated_dataset, dl_mosaic_tile_shape):
    ds = simulated_dataset("dlnirsp-mosaic")
    files = list(ds.glob("*.fits"))
    files.sort()
    tree = asdf_tree_from_filenames(files)
    dataset = tree["dataset"]
    dataset_small = dataset.slice_tiles[0, 0]
    assert dataset_small.shape == dl_mosaic_tile_shape
    for nindex1, nindex2 in np.ndindex(dataset_small._data.shape):
        assert nindex1 == dataset_small[nindex1, nindex2].headers["MINDEX1"] - 1
        assert nindex2 == dataset_small[nindex1, nindex2].headers["MINDEX2"] - 1


def test_asdf_tree_parameters_passthrough(header_filenames, mock_input_dataset_parts):
    """Verify parameters are parsed and stored on the dataset meta."""

    # When
    tree = asdf_tree_from_filenames(header_filenames, parameters=mock_input_dataset_parts)
    meta = tree["dataset"].meta
    params = meta["parameters"]

    # Then
    # Assert the expected metadata key is present.
    assert "parameters" in meta
    assert params is not None
    assert isinstance(params, list)
    assert all(isinstance(p, dict) for p in params)

    names = [p.get("parameterName") for p in params]
    if names:
        assert "test_param1" in names
        assert "test_param2" in names


def _assert_frames_meta_shape(frames_meta, *, expect_present: bool):
    """Assert the frame-metadata has a reasonable shape if present"""
    # If frames are not expected, allow "not provided" representations.
    if not expect_present:
        assert frames_meta in (None, [])
        return

    # When present, frames metadata should be a non-empty list of dicts.
    assert isinstance(frames_meta, list)
    assert len(frames_meta) >= 1

    first = frames_meta[0]
    assert isinstance(first, dict)
    assert "bucket" in first
    assert "object_keys" in first
    assert isinstance(first["bucket"], str)

    # If it's an np array, convert to list
    object_keys = first["object_keys"]
    assert isinstance(object_keys, (list, np.ndarray))
    if isinstance(object_keys, np.ndarray):
        object_keys = object_keys.tolist()

    assert isinstance(object_keys, list)
    assert all(isinstance(k, (str, bytes, np.bytes_)) for k in object_keys)


@pytest.mark.parametrize(
    "obs_kind,cal_kind",
    [
        ("provided", "omitted"),
        ("omitted", "provided"),
        ("provided", "provided"),
        ("empty", "empty"),
        ("omitted", "omitted"),
    ],
)
def test_asdf_tree_input_frames_variants(
    header_filenames, mock_frame_documents, obs_kind, cal_kind
):
    """Verify observation/calibration frame documents are propagated into dataset meta.
    Covers the combinations of frames being provided, omitted, or provided as empty lists.
    """

    # Given
    # Pass as kwargs based on what the test is passing in the parameters.
    kwargs = {}
    if obs_kind == "provided":
        kwargs["observation_frames"] = mock_frame_documents
    elif obs_kind == "empty":
        kwargs["observation_frames"] = []

    if cal_kind == "provided":
        kwargs["calibration_frames"] = mock_frame_documents
    elif cal_kind == "empty":
        kwargs["calibration_frames"] = []

    # When
    tree = asdf_tree_from_filenames(header_filenames, **kwargs)
    meta = tree["dataset"].meta

    # Then
    # Assert the expected metadata keys are always present.
    assert "observation_input_frames" in meta
    assert "calibration_input_frames" in meta

    # Assert each metadata value has expected shape.
    _assert_frames_meta_shape(
        meta["observation_input_frames"], expect_present=(obs_kind == "provided")
    )
    _assert_frames_meta_shape(
        meta["calibration_input_frames"], expect_present=(cal_kind == "provided")
    )

    # When observation frames are provided, assert bucket and object key content match.
    if obs_kind == "provided":
        assert meta["observation_input_frames"][0]["bucket"] == mock_frame_documents[0]["bucket"]

        obs_ok = meta["observation_input_frames"][0]["object_keys"]
        if isinstance(obs_ok, np.ndarray):
            obs_ok = obs_ok.tolist()
        obs_ok = [k.decode("utf-8") if isinstance(k, (bytes, np.bytes_)) else k for k in obs_ok]
        assert obs_ok == mock_frame_documents[0]["object_keys"]

    # When calibration frames are provided, assert bucket and object key content match.
    if cal_kind == "provided":
        assert meta["calibration_input_frames"][0]["bucket"] == mock_frame_documents[0]["bucket"]

        cal_ok = meta["calibration_input_frames"][0]["object_keys"]
        if isinstance(cal_ok, np.ndarray):
            cal_ok = cal_ok.tolist()
        cal_ok = [k.decode("utf-8") if isinstance(k, (bytes, np.bytes_)) else k for k in cal_ok]
        assert cal_ok == mock_frame_documents[0]["object_keys"]
