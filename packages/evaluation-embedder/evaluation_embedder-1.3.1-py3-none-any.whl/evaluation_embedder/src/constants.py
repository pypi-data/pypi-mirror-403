from typing import TYPE_CHECKING, Any, Literal, TypeAlias, TypeVar

from polars import Enum

if TYPE_CHECKING:
    from evaluation_embedder.src.settings import (
        DatasetConnectorSettings,
        EmbedderSettings,
        EvaluatorSettings,
        FaissEvaluatorSettings,
        FromConfigMixinSettings,
        ProcessorSettings,
        RetrieverSettings,
        ScoreSettings,
        TextIngestionPipelineSettings,
        TextPreprocessorSettings,
        TokenCounterSettings,
        VectorStoreSettings,
    )

CONFIG_PATH = "/config/config.yaml"

TDataset = TypeVar("TDataset")
ParquetCompression: TypeAlias = Literal["lz4", "uncompressed", "snappy", "gzip", "brotli", "zstd"]
TCFromConfigMixin = TypeVar("TCFromConfigMixin", bound="FromConfigMixinSettings")
TCEmbedder = TypeVar("TCEmbedder", bound="EmbedderSettings")
TCEvaluator = TypeVar("TCEvaluator", bound="EvaluatorSettings")
TCProcessor = TypeVar("TCProcessor", bound="ProcessorSettings")
TCRetriever = TypeVar("TCRetriever", bound="RetrieverSettings")
TCFaissEvaluator = TypeVar("TCFaissEvaluator", bound="FaissEvaluatorSettings[Any]")
TCScore = TypeVar("TCScore", bound="ScoreSettings")
TCVectorStore = TypeVar("TCVectorStore", bound="VectorStoreSettings")
TCTextPreprocessor = TypeVar("TCTextPreprocessor", bound="TextPreprocessorSettings")
TCTokenCounter = TypeVar("TCTokenCounter", bound="TokenCounterSettings")
TCDatasetConnector = TypeVar("TCDatasetConnector", bound="DatasetConnectorSettings")
TCTextIngestionPipeline = TypeVar("TCTextIngestionPipeline", bound="TextIngestionPipelineSettings")

InputT = TypeVar("InputT")
OutputT = TypeVar("OutputT")


class EmbeddingPurposeEnum(Enum):
    DOCUMENT = "document"
    QUERY = "query"


class FAISSIndexType(Enum):
    FLAT_IP = "flat_ip"
    FLAT_L2 = "flat_l2"
