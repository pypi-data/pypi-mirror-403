import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from evaluation_embedder.src.connectors.minio import MinioDatasetConnector
    from evaluation_embedder.src.connectors.parquet import ParquetDatasetConnector


def load_class(path: str) -> Any:
    module_path, class_name = path.rsplit(".", 1)
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


def _get_minio_connector(
    bucket: str, key: str, endpoint: str, access_key: str, secret_key: str
) -> "MinioDatasetConnector":
    from evaluation_embedder.src.connectors.minio import MinioDatasetConnector
    from evaluation_embedder.src.settings import MinioDatasetConnectorSettings

    kwargs = {
        "bucket": bucket,
        "key": key,
        "endpoint": endpoint,
        "access_key": access_key,
        "secret_key": secret_key,
    }
    config = MinioDatasetConnectorSettings(module_path='', **kwargs)
    return MinioDatasetConnector(config)


def _get_parquet_connector(path: str, *, lazy: bool) -> "ParquetDatasetConnector":
    from evaluation_embedder.src.connectors.parquet import ParquetDatasetConnector
    from evaluation_embedder.src.settings import ParquetDatasetConnectorSettings

    config = ParquetDatasetConnectorSettings(module_path='', path=path, lazy=lazy)
    return ParquetDatasetConnector(config)
