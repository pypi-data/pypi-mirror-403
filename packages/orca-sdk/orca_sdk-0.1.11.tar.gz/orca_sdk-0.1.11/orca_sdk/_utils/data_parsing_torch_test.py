from collections import namedtuple
from dataclasses import dataclass

import pytest
from datasets import Dataset
from datasets.exceptions import DatasetGenerationError

from ..conftest import SAMPLE_DATA
from .data_parsing import hf_dataset_from_torch

pytest.importorskip("torch")

from torch.utils.data import DataLoader as TorchDataLoader  # noqa: E402
from torch.utils.data import Dataset as TorchDataset  # noqa: E402


class PytorchDictDataset(TorchDataset):
    def __init__(self):
        self.data = SAMPLE_DATA

    def __getitem__(self, i):
        return self.data[i]

    def __len__(self):
        return len(self.data)


class PytorchTupleDataset(TorchDataset):
    def __init__(self):
        self.data = SAMPLE_DATA

    def __getitem__(self, i):
        return self.data[i]["value"], self.data[i]["label"]

    def __len__(self):
        return len(self.data)


DatasetTuple = namedtuple("DatasetTuple", ["value", "label"])


class PytorchNamedTupleDataset(TorchDataset):
    def __init__(self):
        self.data = SAMPLE_DATA

    def __getitem__(self, i):
        return DatasetTuple(self.data[i]["value"], self.data[i]["label"])

    def __len__(self):
        return len(self.data)


@dataclass
class DatasetItem:
    text: str
    label: int


class PytorchDataclassDataset(TorchDataset):
    def __init__(self):
        self.data = SAMPLE_DATA

    def __getitem__(self, i):
        return DatasetItem(text=self.data[i]["value"], label=self.data[i]["label"])

    def __len__(self):
        return len(self.data)


class PytorchInvalidDataset(TorchDataset):
    def __init__(self):
        self.data = SAMPLE_DATA

    def __getitem__(self, i):
        return [self.data[i]["value"], self.data[i]["label"]]

    def __len__(self):
        return len(self.data)


def test_hf_dataset_from_torch_dict():
    # Given a Pytorch dataset that returns a dictionary for each item
    dataset = PytorchDictDataset()
    hf_dataset = hf_dataset_from_torch(dataset)
    # Then the HF dataset should be created successfully
    assert isinstance(hf_dataset, Dataset)
    assert len(hf_dataset) == len(dataset)
    assert set(hf_dataset.column_names) == {"value", "label", "key", "score", "source_id", "partition_id"}


def test_hf_dataset_from_torch_tuple():
    # Given a Pytorch dataset that returns a tuple for each item
    dataset = PytorchTupleDataset()
    # And the correct number of column names passed in
    hf_dataset = hf_dataset_from_torch(dataset, column_names=["value", "label"])
    # Then the HF dataset should be created successfully
    assert isinstance(hf_dataset, Dataset)
    assert len(hf_dataset) == len(dataset)
    assert hf_dataset.column_names == ["value", "label"]


def test_hf_dataset_from_torch_tuple_error():
    # Given a Pytorch dataset that returns a tuple for each item
    dataset = PytorchTupleDataset()
    # Then the HF dataset should raise an error if no column names are passed in
    with pytest.raises(DatasetGenerationError):
        hf_dataset_from_torch(dataset)


def test_hf_dataset_from_torch_tuple_error_not_enough_columns():
    # Given a Pytorch dataset that returns a tuple for each item
    dataset = PytorchTupleDataset()
    # Then the HF dataset should raise an error if not enough column names are passed in
    with pytest.raises(DatasetGenerationError):
        hf_dataset_from_torch(dataset, column_names=["value"])


def test_hf_dataset_from_torch_named_tuple():
    # Given a Pytorch dataset that returns a namedtuple for each item
    dataset = PytorchNamedTupleDataset()
    # And no column names are passed in
    hf_dataset = hf_dataset_from_torch(dataset)
    # Then the HF dataset should be created successfully
    assert isinstance(hf_dataset, Dataset)
    assert len(hf_dataset) == len(dataset)
    assert hf_dataset.column_names == ["value", "label"]


def test_hf_dataset_from_torch_dataclass():
    # Given a Pytorch dataset that returns a dataclass for each item
    dataset = PytorchDataclassDataset()
    hf_dataset = hf_dataset_from_torch(dataset)
    # Then the HF dataset should be created successfully
    assert isinstance(hf_dataset, Dataset)
    assert len(hf_dataset) == len(dataset)
    assert hf_dataset.column_names == ["text", "label"]


def test_hf_dataset_from_torch_invalid_dataset():
    # Given a Pytorch dataset that returns a list for each item
    dataset = PytorchInvalidDataset()
    # Then the HF dataset should raise an error
    with pytest.raises(DatasetGenerationError):
        hf_dataset_from_torch(dataset)


def test_hf_dataset_from_torchdataloader():
    # Given a Pytorch dataloader that returns a column-oriented batch of items
    dataset = PytorchDictDataset()

    def collate_fn(x: list[dict]):
        return {"value": [item["value"] for item in x], "label": [item["label"] for item in x]}

    dataloader = TorchDataLoader(dataset, batch_size=3, collate_fn=collate_fn)
    hf_dataset = hf_dataset_from_torch(dataloader)
    # Then the HF dataset should be created successfully
    assert isinstance(hf_dataset, Dataset)
    assert len(hf_dataset) == len(dataset)
    assert hf_dataset.column_names == ["value", "label"]
