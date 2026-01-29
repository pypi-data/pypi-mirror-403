from evaluation_embedder.src.datasets.preprocess import TokenCounter
from evaluation_embedder.src.settings import HeuristicTokenCounterSettings


class HeuristicTokenCounter(TokenCounter[HeuristicTokenCounterSettings]):

    def __init__(self, config: HeuristicTokenCounterSettings) -> None:
        super().__init__(config)

    def count(self, text: str) -> int:
        return max(1, int(len(text) / self.config.chars_per_token))
