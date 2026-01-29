import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, Iterator, List, Optional

from evaluation_embedder.src.constants import (
    EmbeddingPurposeEnum,
    TCEmbedder,
    TCEvaluator,
    TCProcessor,
    TCRetriever,
    TCScore,
    TCVectorStore,
)
from evaluation_embedder.src.datasets import TextDataset
from evaluation_embedder.src.evaluation.async_batcher import AsyncBatcher
from evaluation_embedder.src.mixins import FromConfigMixin
from evaluation_embedder.src.utils import load_class
from langchain_core.documents import (
    Document,  # or: from langchain.schema import Document
)
from pydantic import BaseModel, Field

_logger = logging.getLogger(__name__)


class Score(ABC, Generic[TCScore]):

    class ScoreResult(BaseModel):
        name: str
        value: float

    def __init__(self, config: TCScore) -> None:
        self.config = config
        _logger.info(f"Initialized Score | class={self.__class__.__name__} | config={config}")

    @abstractmethod
    def __call__(self, hits: List[bool]) -> ScoreResult:
        raise NotImplementedError()


class Processor(FromConfigMixin[TCProcessor], ABC, Generic[TCProcessor]):

    def __init__(self, config: TCProcessor) -> None:
        self.config = config

    @abstractmethod
    def __call__(self, text: str, purpose: EmbeddingPurposeEnum) -> str:
        raise NotImplementedError()


class Embedder(FromConfigMixin[TCEmbedder], ABC, Generic[TCEmbedder]):
    MAX_BATCH_SIZE: int = 15
    BATCH_TIMEOUT_MS: float = 4.921875

    def __init__(self, config: TCEmbedder) -> None:
        self.config = config
        self._batcher = AsyncBatcher[str, List[float]](
            batch_fn=self._aembed,
            max_batch_size=self.__class__.MAX_BATCH_SIZE,
            batch_timeout_ms=self.__class__.BATCH_TIMEOUT_MS,
        )
        _logger.info(f"Initialized Embedder | class={self.__class__.__name__}")

    # ---------------- ABSTRACT ----------------

    @abstractmethod
    async def _aembed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError()

    # ---------------- LIFECYCLE ----------------
    async def aclose(self) -> None:
        return None

    # ---------------- PUBLIC API ----------------

    async def aembed(self, texts: List[str]) -> List[List[float]]:
        return await self._batcher.submit(texts)

    async def aembed_queries(
        self,
        queries: List[str],
        processor: Optional[Processor[Any]] = None,
    ) -> List[List[float]]:
        if processor:
            queries = [processor(text=query, purpose=EmbeddingPurposeEnum.QUERY) for query in queries]  # type: ignore[arg-type]
        return await self.aembed(queries)

    async def aembed_query(
        self,
        query: str,
        processor: Optional[Processor[Any]] = None,
    ) -> List[float]:
        return (await self.aembed_queries([query], processor))[0]

    async def aembed_documents(
        self,
        docs: List[str],
        processor: Optional[Processor[Any]] = None,
    ) -> List[List[float]]:
        if processor:
            docs = [processor(text=doc, purpose=EmbeddingPurposeEnum.DOCUMENT) for doc in docs]  # type: ignore[arg-type]
        return await self.aembed(docs)


class VectorStore(FromConfigMixin[TCVectorStore], ABC, Generic[TCVectorStore]):
    MAX_BATCH_SIZE: int = 3
    BATCH_TIMEOUT_MS: float = 0.984

    class VectorQuery(BaseModel):
        vector: List[float]
        limit: int

    class ScoredPoint(BaseModel):
        score: float = Field(..., description="Points vector distance to the query vector")
        document: Document

    class QueryResponse(BaseModel):
        points: List["VectorStore.ScoredPoint"]

    def __init__(self, config: TCVectorStore) -> None:
        self.config = config
        self._batcher = AsyncBatcher[
            VectorStore.VectorQuery,
            VectorStore.QueryResponse,
        ](
            batch_fn=self._abatch_query_points,
            max_batch_size=self.__class__.MAX_BATCH_SIZE,
            batch_timeout_ms=self.__class__.BATCH_TIMEOUT_MS,
        )
        _logger.info(f"Initialized VectorStore | class={self.__class__.__name__} | config={config}")

    # -------- batching boundary --------

    @abstractmethod
    async def _abatch_query_points(
        self,
        requests: List["VectorStore.VectorQuery"],
    ) -> List["VectorStore.QueryResponse"]:
        """
        Backend-native batch query.
        Must return results in the same order as requests.
        """
        raise NotImplementedError()

    async def abatch_query_points(
        self,
        queries: List[List[float]],
        limit: int,
    ) -> List["VectorStore.QueryResponse"]:
        return await self._batcher.submit([self.VectorQuery(vector=q, limit=limit) for q in queries])

    async def aquery_points(
        self,
        query: List[float],
        limit: int,
    ) -> "VectorStore.QueryResponse":
        return (await self.abatch_query_points([query], limit))[0]

    # ---------------- LIFECYCLE ----------------
    async def aclose(self) -> None:
        """
        Close underlying async resources (HTTP clients, sockets, etc.).
        Default: no-op.
        """
        return None


class Retriever(FromConfigMixin[TCRetriever], ABC, Generic[TCRetriever]):

    def __init__(self, config: TCRetriever) -> None:
        self.config = config

        _logger.info(f"Initializing Retriever | class={self.__class__.__name__}")

        self.embedder: Embedder[Any] = load_class(self.config.embedder.module_path).from_config(self.config.embedder)

        self.vector_store: VectorStore[Any] = load_class(self.config.vector_store.module_path).from_config(
            self.config.vector_store
        )

        self.processor: Processor[Any] = load_class(self.config.processor.module_path).from_config(
            self.config.processor
        )

        _logger.info(
            f"Retriever initialized | embedder={type(self.embedder).__name__} | "
            f"vector_store={type(self.vector_store).__name__}"
        )

    async def retrieve_batch(self, queries: List[str], limit: int) -> List[VectorStore.QueryResponse]:
        embedding = await self.embedder.aembed_queries(queries, self.processor)
        return await self.vector_store.abatch_query_points(embedding, limit)

    async def retrieve(self, query: str, limit: int) -> VectorStore.QueryResponse:
        embedding = await self.embedder.aembed_query(query, self.processor)
        return await self.vector_store.aquery_points(embedding, limit)

    async def aclose(self) -> None:
        await self.embedder.aclose()
        await self.vector_store.aclose()


class Evaluator(FromConfigMixin[TCEvaluator], ABC, Generic[TCEvaluator]):

    NB_LOGS_PER_QUERIES = 100
    BATCH_SIZE = 96

    def __init__(self, config: TCEvaluator) -> None:
        super().__init__(config)
        _logger.info(f"Initializing Evaluator | class={self.__class__.__name__}")

        self.dataset: TextDataset[Any] = self._load_dataset()
        self.retriever: Retriever[Any] = load_class(self.config.retriever.module_path).from_config(
            self.config.retriever
        )
        self.scores: List[Score[Any]] = [load_class(s.module_path)(s) for s in self.config.scores]

        _logger.info(
            f"Evaluator ready | dataset_size={len(self.dataset)} | " f"scores={[type(s).__name__ for s in self.scores]}"
        )

    def _load_dataset(self) -> TextDataset[Any]:
        dataset: TextDataset[Any] = (
            load_class(self.config.dataset_connector.module_path).from_config(self.config.dataset_connector).load_text()
        )
        _logger.info(f"Instantiating dataset | class={dataset.__class__.__name__}")
        _logger.info(f"Dataset loaded | type={type(dataset).__name__} | " f"size={len(dataset)}")
        return dataset

    def batch_iter(self) -> Iterator[List[Dict[str, Any]]]:
        batch: list[dict[str, Any]] = []
        for row in self.dataset.iter_rows(named=True):
            batch.append(row)
            if len(batch) == self.BATCH_SIZE:
                yield batch
                batch = []
        if batch:
            yield batch

    async def eval(self) -> List[List[Score.ScoreResult]]:
        scores_all: List[List[Score.ScoreResult]] = []
        max_k = max(getattr(score.config, "k", 0) for score in self.scores)
        _logger.info(f"Starting evaluation | max_k={max_k}")
        tasks: list[asyncio.Task[list[VectorStore.QueryResponse]]] = []
        batches: list[list[dict[str, Any]]] = []
        # ---------- create batch tasks ----------
        for batch in self.batch_iter():
            queries = [sample["metadata"]["query"] for sample in batch]

            task = asyncio.create_task(
                self.retriever.retrieve_batch(
                    queries=queries,
                    limit=max_k,
                )
            )
            tasks.append(task)
            batches.append(batch)
        # ---------- await all batch tasks ----------
        all_responses = await asyncio.gather(*tasks)
        # ---------- scoring ----------
        processed = 0
        for batch, responses in zip(batches, all_responses):
            for sample, response in zip(batch, responses):
                hits = [p.document.page_content == sample["page_content"] for p in response.points]
                scores = [score(hits) for score in self.scores]
                scores_all.append(scores)
                processed += 1
                if processed % self.__class__.NB_LOGS_PER_QUERIES == 0 or processed == len(self.dataset):
                    _logger.info(f"Eval progress | processed={processed}/{len(self.dataset)}")
        _logger.info("Evaluation completed")
        return scores_all
