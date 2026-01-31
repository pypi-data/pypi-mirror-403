import json
import pickle
import tempfile

from datasets import Dataset

from .data_parsing import hf_dataset_from_disk


def test_hf_dataset_from_disk_pickle_list():
    with tempfile.NamedTemporaryFile(suffix=".pkl") as temp_file:
        # Given a pickle file with test data that is a list
        test_data = [{"value": f"test_{i}", "label": i % 2} for i in range(30)]
        with open(temp_file.name, "wb") as f:
            pickle.dump(test_data, f)
        dataset = hf_dataset_from_disk(temp_file.name)
        # Then the HF dataset should be created successfully
        assert isinstance(dataset, Dataset)
        assert len(dataset) == 30
        assert dataset.column_names == ["value", "label"]


def test_hf_dataset_from_disk_pickle_dict():
    with tempfile.NamedTemporaryFile(suffix=".pkl") as temp_file:
        # Given a pickle file with test data that is a dict
        test_data = {"value": [f"test_{i}" for i in range(30)], "label": [i % 2 for i in range(30)]}
        with open(temp_file.name, "wb") as f:
            pickle.dump(test_data, f)
        dataset = hf_dataset_from_disk(temp_file.name)
        # Then the HF dataset should be created successfully
        assert isinstance(dataset, Dataset)
        assert len(dataset) == 30
        assert dataset.column_names == ["value", "label"]


def test_hf_dataset_from_disk_json():
    with tempfile.NamedTemporaryFile(suffix=".json") as temp_file:
        # Given a JSON file with test data
        test_data = [{"value": f"test_{i}", "label": i % 2} for i in range(30)]
        with open(temp_file.name, "w") as f:
            json.dump(test_data, f)
        dataset = hf_dataset_from_disk(temp_file.name)
        # Then the HF dataset should be created successfully
        assert isinstance(dataset, Dataset)
        assert len(dataset) == 30
        assert dataset.column_names == ["value", "label"]


def test_hf_dataset_from_disk_jsonl():
    with tempfile.NamedTemporaryFile(suffix=".jsonl") as temp_file:
        # Given a JSONL file with test data
        test_data = [{"value": f"test_{i}", "label": i % 2} for i in range(30)]
        with open(temp_file.name, "w") as f:
            for item in test_data:
                f.write(json.dumps(item) + "\n")
        dataset = hf_dataset_from_disk(temp_file.name)
        # Then the HF dataset should be created successfully
        assert isinstance(dataset, Dataset)
        assert len(dataset) == 30
        assert dataset.column_names == ["value", "label"]


def test_hf_dataset_from_disk_csv():
    with tempfile.NamedTemporaryFile(suffix=".csv") as temp_file:
        # Given a CSV file with test data
        test_data = [{"value": f"test_{i}", "label": i % 2} for i in range(30)]
        with open(temp_file.name, "w") as f:
            f.write("value,label\n")
            for item in test_data:
                f.write(f"{item['value']},{item['label']}\n")
        dataset = hf_dataset_from_disk(temp_file.name)
        # Then the HF dataset should be created successfully
        assert isinstance(dataset, Dataset)
        assert len(dataset) == 30
        assert dataset.column_names == ["value", "label"]


def test_hf_dataset_from_disk_parquet():
    with tempfile.NamedTemporaryFile(suffix=".parquet") as temp_file:
        # Given a Parquet file with test data
        data = {
            "value": [f"test_{i}" for i in range(30)],
            "label": [i % 2 for i in range(30)],
        }
        dataset = Dataset.from_dict(data)
        dataset.to_parquet(temp_file.name)
        dataset = hf_dataset_from_disk(temp_file.name)
        # Then the HF dataset should be created successfully
        assert isinstance(dataset, Dataset)
        assert len(dataset) == 30
        assert dataset.column_names == ["value", "label"]
