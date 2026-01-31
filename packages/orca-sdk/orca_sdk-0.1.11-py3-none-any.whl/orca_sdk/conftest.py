import logging
import os
from typing import Generator
from uuid import uuid4

import pytest
import pytest_asyncio
from datasets import ClassLabel, Dataset, Features, Value

from ._utils.auth import _create_api_key, _delete_org
from .async_client import OrcaAsyncClient
from .classification_model import ClassificationModel
from .client import OrcaClient
from .credentials import OrcaCredentials
from .datasource import Datasource
from .embedding_model import PretrainedEmbeddingModel
from .memoryset import LabeledMemoryset, ScoredMemoryset
from .regression_model import RegressionModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

os.environ["ORCA_API_URL"] = os.environ.get("ORCA_API_URL", "http://localhost:1584/")

os.environ["ORCA_SAVE_TELEMETRY_SYNCHRONOUSLY"] = "true"


def skip_in_prod(reason: str):
    """Custom decorator to skip tests when running against production API"""
    PROD_API_URLs = ["https://api.orcadb.ai", "https://api.staging.orcadb.ai"]
    return pytest.mark.skipif(
        os.environ["ORCA_API_URL"] in PROD_API_URLs,
        reason=reason,
    )


def skip_in_ci(reason: str):
    """Custom decorator to skip tests when running in CI"""
    return pytest.mark.skipif(
        os.environ.get("GITHUB_ACTIONS", "false") == "true",
        reason=reason,
    )


def _create_org_id():
    # UUID start to identify test data (0xtest...)
    return "10e50000-0000-4000-a000-" + str(uuid4())[24:]


@pytest.fixture(scope="session")
def org_id():
    return _create_org_id()


@pytest.fixture(scope="session")
def other_org_id():
    return _create_org_id()


@pytest.fixture(autouse=True, scope="session")
def api_key(org_id) -> Generator[str, None, None]:
    api_key = _create_api_key(org_id=org_id, name="orca_sdk_test")
    with OrcaClient(api_key=api_key).use():
        yield api_key
    _delete_org(org_id)


# We cannot use a session scoped fixture because async pytest tears down the client after each test
@pytest.fixture(autouse=True)
def authenticate_async_client(api_key) -> Generator[None, None, None]:
    with OrcaAsyncClient(api_key=api_key).use():
        yield


@pytest.fixture(scope="session")
def unauthenticated_client() -> OrcaClient:
    return OrcaClient(api_key=str(uuid4()))


@pytest_asyncio.fixture()
def unauthenticated_async_client() -> OrcaAsyncClient:
    return OrcaAsyncClient(api_key=str(uuid4()))


@pytest.fixture(scope="session")
def unauthorized_client(other_org_id):
    different_api_key = _create_api_key(org_id=other_org_id, name="orca_sdk_test_other_org")
    return OrcaClient(api_key=different_api_key)


@pytest.fixture(scope="session")
def predict_only_client() -> OrcaClient:
    predict_api_key = OrcaCredentials.create_api_key("orca_sdk_test_predict", scopes={"PREDICT"})
    return OrcaClient(api_key=predict_api_key)


@pytest.fixture(scope="session")
def label_names():
    return ["soup", "cats"]


SAMPLE_DATA = [
    {"value": "i love soup", "label": 0, "key": "g1", "score": 0.1, "source_id": "s1", "partition_id": "p1"},
    {"value": "cats are cute", "label": 1, "key": "g1", "score": 0.9, "source_id": "s2", "partition_id": "p1"},
    {"value": "soup is good", "label": 0, "key": "g1", "score": 0.1, "source_id": "s3", "partition_id": "p1"},
    {"value": "i love cats", "label": 1, "key": "g1", "score": 0.9, "source_id": "s4", "partition_id": "p1"},
    {"value": "everyone loves cats", "label": 1, "key": "g1", "score": 0.9, "source_id": "s5", "partition_id": "p1"},
    {
        "value": "soup is great for the winter",
        "label": 0,
        "key": "g1",
        "score": 0.1,
        "source_id": "s6",
        "partition_id": "p1",
    },
    {
        "value": "hot soup on a rainy day!",
        "label": 0,
        "key": "g1",
        "score": 0.1,
        "source_id": "s7",
        "partition_id": "p1",
    },
    {"value": "cats sleep all day", "label": 1, "key": "g1", "score": 0.9, "source_id": "s8", "partition_id": "p1"},
    {"value": "homemade soup recipes", "label": 0, "key": "g1", "score": 0.1, "source_id": "s9", "partition_id": "p2"},
    {"value": "cats purr when happy", "label": 1, "key": "g2", "score": 0.9, "source_id": "s10", "partition_id": "p2"},
    {
        "value": "chicken noodle soup is classic",
        "label": 0,
        "key": "g1",
        "score": 0.1,
        "source_id": "s11",
        "partition_id": "p2",
    },
    {"value": "kittens are baby cats", "label": 1, "key": "g2", "score": 0.9, "source_id": "s12", "partition_id": "p2"},
    {
        "value": "soup can be served cold too",
        "label": 0,
        "key": "g1",
        "score": 0.1,
        "source_id": "s13",
        "partition_id": "p2",
    },
    {"value": "cats have nine lives", "label": 1, "key": "g2", "score": 0.9, "source_id": "s14", "partition_id": "p2"},
    {
        "value": "tomato soup with grilled cheese",
        "label": 0,
        "key": "g1",
        "score": 0.1,
        "source_id": "s15",
        "partition_id": "p2",
    },
    {
        "value": "cats are independent animals",
        "label": 1,
        "key": "g2",
        "score": 0.9,
        "source_id": "s16",
        "partition_id": None,
    },
    {
        "value": "the beach is always fun",
        "label": None,
        "key": "g3",
        "score": None,
        "source_id": "s17",
        "partition_id": None,
    },
    {"value": "i love the beach", "label": None, "key": "g3", "score": None, "source_id": "s18", "partition_id": None},
    {
        "value": "the ocean is healing",
        "label": None,
        "key": "g3",
        "score": None,
        "source_id": "s19",
        "partition_id": None,
    },
    {
        "value": "sandy feet, sand between my toes at the beach",
        "label": None,
        "key": "g3",
        "score": None,
        "source_id": "s20",
        "partition_id": None,
    },
    {
        "value": "i am such a beach bum",
        "label": None,
        "key": "g3",
        "score": None,
        "source_id": "s21",
        "partition_id": None,
    },
    {
        "value": "i will always want to be at the beach",
        "label": None,
        "key": "g3",
        "score": None,
        "source_id": "s22",
        "partition_id": None,
    },
]


@pytest.fixture(scope="session")
def hf_dataset(label_names: list[str]) -> Dataset:
    return Dataset.from_list(
        SAMPLE_DATA,
        features=Features(
            {
                "value": Value("string"),
                "label": ClassLabel(names=label_names),
                "key": Value("string"),
                "score": Value("float"),
                "source_id": Value("string"),
                "partition_id": Value("string"),
            }
        ),
    )


@pytest.fixture(scope="session")
def datasource(hf_dataset: Dataset) -> Datasource:
    datasource = Datasource.from_hf_dataset("test_datasource", hf_dataset)
    return datasource


EVAL_DATASET = [
    {"value": "chicken noodle soup is the best", "label": 1, "score": 0.9},  # mislabeled
    {"value": "cats are cute", "label": 0, "score": 0.1},  # mislabeled
    {"value": "soup is great for the winter", "label": 0, "score": 0.1},
    {"value": "i love cats", "label": 1, "score": 0.9},
]


@pytest.fixture(scope="session")
def eval_datasource() -> Datasource:
    eval_datasource = Datasource.from_list("eval_datasource", EVAL_DATASET)
    return eval_datasource


@pytest.fixture(scope="session")
def eval_dataset() -> Dataset:
    eval_dataset = Dataset.from_list(EVAL_DATASET)
    return eval_dataset


@pytest.fixture(scope="session")
def readonly_memoryset(datasource: Datasource) -> LabeledMemoryset:
    memoryset = LabeledMemoryset.create(
        "test_readonly_memoryset",
        datasource=datasource,
        embedding_model=PretrainedEmbeddingModel.GTE_BASE,
        source_id_column="source_id",
        max_seq_length_override=32,
        index_type="IVF_FLAT",
        index_params={"n_lists": 100},
    )
    return memoryset


@pytest.fixture(scope="session")
def readonly_partitioned_memoryset(datasource: Datasource) -> LabeledMemoryset:
    memoryset = LabeledMemoryset.create(
        "test_readonly_partitioned_memoryset",
        datasource=datasource,
        embedding_model=PretrainedEmbeddingModel.GTE_BASE,
        source_id_column="source_id",
        partition_id_column="partition_id",
    )
    return memoryset


@pytest.fixture(scope="function")
def writable_memoryset(datasource: Datasource, api_key: str) -> Generator[LabeledMemoryset, None, None]:
    """
    Function-scoped fixture that provides a writable memoryset for tests that mutate state.

    This fixture creates a fresh `LabeledMemoryset` named 'test_writable_memoryset' before each test.
    After the test, it attempts to restore the memoryset to its initial state by deleting any added entries
    and reinserting sample data — unless the memoryset has been dropped by the test itself, in which case
    it will be recreated on the next invocation.

    Note: Re-creating the memoryset from scratch is surprisingly more expensive than cleaning it up.
    """
    # It shouldn't be possible for this memoryset to already exist
    memoryset = LabeledMemoryset.create(
        "test_writable_memoryset",
        datasource=datasource,
        embedding_model=PretrainedEmbeddingModel.GTE_BASE,
        source_id_column="source_id",
        partition_id_column="partition_id",
        max_seq_length_override=32,
        if_exists="open",
    )
    try:
        yield memoryset
    finally:
        # Restore the memoryset to a clean state for the next test.
        with OrcaClient(api_key=api_key).use():
            if LabeledMemoryset.exists("test_writable_memoryset"):
                memoryset.truncate()
                assert len(memoryset) == 0
                memoryset.insert(SAMPLE_DATA)
        # If the test dropped the memoryset, do nothing — it will be recreated on the next use.


@pytest.fixture(scope="session")
def classification_model(readonly_memoryset: LabeledMemoryset) -> ClassificationModel:
    model = ClassificationModel.create(
        "test_classification_model",
        readonly_memoryset,
        num_classes=2,
        memory_lookup_count=3,
        description="test_description",
    )
    return model


@pytest.fixture(scope="session")
def partitioned_classification_model(readonly_partitioned_memoryset: LabeledMemoryset) -> ClassificationModel:
    model = ClassificationModel.create(
        "test_partitioned_classification_model",
        readonly_partitioned_memoryset,
        num_classes=2,
        memory_lookup_count=3,
        description="test_partitioned_description",
    )
    return model


# Add scored memoryset and regression model fixtures
@pytest.fixture(scope="session")
def scored_memoryset(datasource: Datasource) -> ScoredMemoryset:
    memoryset = ScoredMemoryset.create(
        "test_scored_memoryset",
        datasource=datasource,
        embedding_model=PretrainedEmbeddingModel.GTE_BASE,
        source_id_column="source_id",
        max_seq_length_override=32,
        index_type="IVF_FLAT",
        index_params={"n_lists": 100},
    )
    return memoryset


@pytest.fixture(scope="session")
def regression_model(scored_memoryset: ScoredMemoryset) -> RegressionModel:
    model = RegressionModel.create(
        "test_regression_model",
        scored_memoryset,
        memory_lookup_count=3,
        description="test_regression_description",
    )
    return model


@pytest.fixture(scope="session")
def readonly_partitioned_scored_memoryset(datasource: Datasource) -> ScoredMemoryset:
    memoryset = ScoredMemoryset.create(
        "test_readonly_partitioned_scored_memoryset",
        datasource=datasource,
        embedding_model=PretrainedEmbeddingModel.GTE_BASE,
        source_id_column="source_id",
        partition_id_column="partition_id",
    )
    return memoryset


@pytest.fixture(scope="session")
def partitioned_regression_model(readonly_partitioned_scored_memoryset: ScoredMemoryset) -> RegressionModel:
    model = RegressionModel.create(
        "test_partitioned_regression_model",
        readonly_partitioned_scored_memoryset,
        memory_lookup_count=3,
        description="test_partitioned_regression_description",
    )
    return model


@pytest.fixture(scope="function")
def fully_partitioned_classification_resources() -> (
    Generator[tuple[Datasource, LabeledMemoryset, ClassificationModel], None, None]
):
    data = [
        {"value": "i love soup", "label": 0, "partition_id": "p1"},
        {"value": "cats are cute", "label": 1, "partition_id": "p1"},
        {"value": "soup is good", "label": 0, "partition_id": "p1"},
        {"value": "i love cats", "label": 1, "partition_id": "p2"},
        {"value": "everyone loves cats", "label": 1, "partition_id": "p2"},
        {"value": "soup is good", "label": 0, "partition_id": "p1"},
        {"value": "cats are amazing animals", "label": 1, "partition_id": "p2"},
        {"value": "tomato soup is delicious", "label": 0, "partition_id": "p1"},
        {"value": "cats love to play", "label": 1, "partition_id": "p2"},
        {"value": "i enjoy eating soup", "label": 0, "partition_id": "p1"},
        {"value": "my cat is fluffy", "label": 1, "partition_id": "p2"},
        {"value": "chicken soup is tasty", "label": 0, "partition_id": "p1"},
        {"value": "cats are playful pets", "label": 1, "partition_id": "p2"},
        {"value": "soup warms the soul", "label": 0, "partition_id": "p1"},
        {"value": "cats have soft fur", "label": 1, "partition_id": "p2"},
        {"value": "vegetable soup is healthy", "label": 0, "partition_id": "p1"},
    ]

    datasource = None
    memoryset = None
    classification_model = None
    try:
        datasource = Datasource.from_list("fully_partitioned_classification_datasource", data)
        memoryset = LabeledMemoryset.create(
            "fully_partitioned_classification_memoryset",
            datasource=datasource,
            label_names=["soup", "cats"],
            partition_id_column="partition_id",
        )
        classification_model = ClassificationModel.create("fully_partitioned_classification_model", memoryset=memoryset)
        yield (datasource, memoryset, classification_model)
    finally:
        # Clean up in reverse order of creation
        ClassificationModel.drop("fully_partitioned_classification_model", if_not_exists="ignore")
        LabeledMemoryset.drop("fully_partitioned_classification_memoryset", if_not_exists="ignore")
        Datasource.drop("fully_partitioned_classification_datasource", if_not_exists="ignore")


@pytest.fixture(scope="function")
def fully_partitioned_regression_resources() -> (
    Generator[tuple[Datasource, ScoredMemoryset, RegressionModel], None, None]
):
    data = [
        {"value": "i love soup", "score": 0.1, "partition_id": "p1"},
        {"value": "cats are cute", "score": 0.9, "partition_id": "p1"},
        {"value": "soup is good", "score": 0.1, "partition_id": "p1"},
        {"value": "i love cats", "score": 0.9, "partition_id": "p2"},
        {"value": "everyone loves cats", "score": 0.9, "partition_id": "p2"},
        {"value": "soup is good", "score": 0.1, "partition_id": "p1"},
        {"value": "cats are amazing animals", "score": 0.9, "partition_id": "p2"},
        {"value": "tomato soup is delicious", "score": 0.1, "partition_id": "p1"},
        {"value": "cats love to play", "score": 0.9, "partition_id": "p2"},
        {"value": "i enjoy eating soup", "score": 0.1, "partition_id": "p1"},
        {"value": "my cat is fluffy", "score": 0.9, "partition_id": "p2"},
        {"value": "chicken soup is tasty", "score": 0.1, "partition_id": "p1"},
        {"value": "cats are playful pets", "score": 0.9, "partition_id": "p2"},
        {"value": "soup warms the soul", "score": 0.1, "partition_id": "p1"},
        {"value": "cats have soft fur", "score": 0.9, "partition_id": "p2"},
        {"value": "vegetable soup is healthy", "score": 0.1, "partition_id": "p1"},
    ]

    datasource = None
    memoryset = None
    regression_model = None
    try:
        datasource = Datasource.from_list("fully_partitioned_regression_datasource", data)
        memoryset = ScoredMemoryset.create(
            "fully_partitioned_regression_memoryset",
            datasource=datasource,
            partition_id_column="partition_id",
        )
        regression_model = RegressionModel.create("fully_partitioned_regression_model", memoryset=memoryset)
        yield (datasource, memoryset, regression_model)
    finally:
        # Clean up in reverse order of creation
        RegressionModel.drop("fully_partitioned_regression_model", if_not_exists="ignore")
        ScoredMemoryset.drop("fully_partitioned_regression_memoryset", if_not_exists="ignore")
        Datasource.drop("fully_partitioned_regression_datasource", if_not_exists="ignore")
