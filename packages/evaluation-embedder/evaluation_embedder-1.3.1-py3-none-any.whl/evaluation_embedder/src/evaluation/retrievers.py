from evaluation_embedder.src.evaluation import Retriever
from evaluation_embedder.src.settings import (
    FaissVectorStoreSettings,
    NomicProcessorSettings,
    QdrantVectorStoreSettings,
    RetrieverSettings,
    VLLMEmbedderSettings,
)


class VLLMFAISSRetriever(
    Retriever[RetrieverSettings[VLLMEmbedderSettings, FaissVectorStoreSettings, NomicProcessorSettings]]
):
    def __init__(
        self, config: RetrieverSettings[VLLMEmbedderSettings, FaissVectorStoreSettings, NomicProcessorSettings]
    ):
        super().__init__(config)


class VLLMQdrantRetriever(
    Retriever[RetrieverSettings[VLLMEmbedderSettings, QdrantVectorStoreSettings, NomicProcessorSettings]]
):
    def __init__(
        self, config: RetrieverSettings[VLLMEmbedderSettings, QdrantVectorStoreSettings, NomicProcessorSettings]
    ):
        super().__init__(config)
