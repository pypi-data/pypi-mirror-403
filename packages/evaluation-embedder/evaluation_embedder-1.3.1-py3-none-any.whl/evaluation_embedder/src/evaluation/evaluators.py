from typing import Generic, List, Self, cast

import numpy as np
from evaluation_embedder.src.constants import TCFaissEvaluator
from evaluation_embedder.src.datasets.polars import PolarsTextDataset
from evaluation_embedder.src.evaluation import Evaluator
from evaluation_embedder.src.evaluation.vector_stores import FaissVectorStore
from evaluation_embedder.src.settings import (
    FaissEvaluatorSettings,
    HuggingFaceEmbedderSettings,
    QdrantEvaluatorSettings,
)
from langchain_core.documents import Document


class QdrantEvaluator(Evaluator[QdrantEvaluatorSettings]):
    def __init__(self, config: QdrantEvaluatorSettings):
        super().__init__(config)


class FaissEvaluator(Evaluator[TCFaissEvaluator], Generic[TCFaissEvaluator]):
    def __init__(self, config: TCFaissEvaluator):
        super().__init__(config)

    @classmethod
    async def create(cls, config: TCFaissEvaluator) -> Self:
        self = cls(config)
        docs = self.get_docs()
        texts = [d.page_content for d in docs]
        embeddings = np.asarray(
            await self.retriever.embedder.aembed_documents(texts, processor=self.retriever.processor),
            dtype="float32",
        )
        vector_store = cast(FaissVectorStore, self.retriever.vector_store)
        vector_store.index = vector_store.build_faiss_index(embeddings.shape[-1])
        vector_store.add_documents(docs, embeddings)
        return self

    def get_docs(self) -> List[Document]:
        docs_idx = []
        seen = set()
        for i, row in enumerate(self.dataset.iter_rows(named=True)):
            doc_id = row["metadata"]["doc_id"]
            if doc_id not in seen:
                seen.add(doc_id)
                docs_idx.append(i)
        return PolarsTextDataset(self.dataset.polars[docs_idx]).to_langchain_documents()


class HuggingFaceFaissEvaluator(FaissEvaluator[FaissEvaluatorSettings[HuggingFaceEmbedderSettings]]):
    pass
