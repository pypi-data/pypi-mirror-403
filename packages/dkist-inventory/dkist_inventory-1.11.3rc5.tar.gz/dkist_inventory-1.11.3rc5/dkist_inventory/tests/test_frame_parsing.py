import numpy as np
import pytest

from dkist_inventory.frame_parsing import InputFrameMetadata
from dkist_inventory.frame_parsing import InputFramesParser


@pytest.fixture
def simple_frame_doc():
    return {
        "bucket": "raw",
        "object_keys": [
            "pid_1_118/eid_1_118_opAvoqBr_R001.82591.13964206/2a726c8921fc43cf970dfcedc3ec3ec5.fits",
            "pid_1_118/eid_1_118_opAvoqBr_R001.82591.13964206/6ee53e057f8a46419366abc7dc077edc.fits",
        ],
    }


@pytest.fixture
def empty_frame_doc():
    return {
        "bucket": "raw",
        "object_keys": [],
    }


def test_input_frame_metadata_to_asdf_converts_list_to_ndarray(simple_frame_doc):
    """
    Ensure to_asdf() converts object_keys (list[str]) into a NumPy ndarray and
    preserves values.
    """
    # Given
    model = InputFrameMetadata(**simple_frame_doc)

    # When
    asdf_repr = model.to_asdf_friendly_structure()

    # Then
    assert asdf_repr["bucket"] == simple_frame_doc["bucket"]
    obj_keys_arr = asdf_repr["object_keys"]
    assert isinstance(obj_keys_arr, np.ndarray)
    assert obj_keys_arr.shape == (len(simple_frame_doc["object_keys"]),)
    assert obj_keys_arr.dtype.kind == "S"
    decoded_keys = [v.decode("ascii") for v in obj_keys_arr.tolist()]
    assert decoded_keys == simple_frame_doc["object_keys"]


def test_input_frame_metadata_to_asdf_handles_empty_object_keys(empty_frame_doc):
    """
    Ensure an empty object_keys list is converted into an empty ndarray without error.
    """
    model = InputFrameMetadata(**empty_frame_doc)

    asdf_repr = model.to_asdf_friendly_structure()
    obj_keys_arr = asdf_repr["object_keys"]

    assert isinstance(obj_keys_arr, np.ndarray)
    assert obj_keys_arr.shape == (0,)


def test_input_frame_metadata_rejects_missing_bucket():
    """
    If bucket is missing, constructing InputFrameMetadata should fail.
    """
    bad_doc = {
        # "bucket" missing on purpose
        "object_keys": ["foo.fits"],
    }

    with pytest.raises(Exception):
        InputFrameMetadata(**bad_doc)


def test_input_frames_parser_from_none_is_empty():
    """Ensure from_documents(None) produces an empty parser."""
    parser = InputFramesParser.from_documents(None)
    assert parser.frames == []
    assert parser.asdf_frame_metadata == []


def test_input_frames_parser_from_empty_list_is_empty():
    """Ensure from_documents([]) produces an empty parser."""
    parser = InputFramesParser.from_documents([])
    assert parser.frames == []
    assert parser.asdf_frame_metadata == []


def test_input_frames_parser_asdf_frame_metadata_matches_input(simple_frame_doc):
    """Ensure parser converts documents into ASDF-ready metadata with ndarray object_keys."""
    parser = InputFramesParser.from_documents([simple_frame_doc])

    # The parser should validate into models
    assert len(parser.frames) == 1
    assert isinstance(parser.frames[0], InputFrameMetadata)

    # The ASDF representation should be a list of mappings
    asdf_meta = parser.asdf_frame_metadata
    assert isinstance(asdf_meta, list)
    assert len(asdf_meta) == 1

    item = asdf_meta[0]
    assert item["bucket"] == simple_frame_doc["bucket"]

    obj_keys_arr = item["object_keys"]
    assert isinstance(obj_keys_arr, np.ndarray)
    assert obj_keys_arr.dtype.kind == "S"

    decoded_keys = [v.decode("ascii") for v in obj_keys_arr.tolist()]
    assert decoded_keys == simple_frame_doc["object_keys"]
