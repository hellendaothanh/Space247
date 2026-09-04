import logging
import math
from typing import Any
from src.core.config import settings

logger = logging.getLogger(__name__)

# Fallback mapping for models in FastEmbed when specific HF names are requested
FASTEMBED_MODEL_ALIASES: dict[str, str] = {
    "multilingual-e5-base": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
    "intfloat/multilingual-e5-base": "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
}

PROPERTY_TYPE_VI_LABELS: dict[str, str] = {
    "apartment": "Căn hộ",
    "house": "Nhà phố",
    "villa": "Biệt thự",
    "land": "Đất nền",
    "commercial": "Mặt bằng thương mại",
}


def _l2_normalize(vec: list[float]) -> list[float]:
    norm = math.sqrt(sum(x * x for x in vec))
    if norm > 0:
        return [float(x / norm) for x in vec]
    return vec


class EmbeddingService:
    """
    Service for generating dense 768-dimensional text embeddings optimized for Vietnamese.
    Supports FastEmbed and sentence-transformers with multilingual models
    (e.g., multilingual-e5-base, sentence-transformers/paraphrase-multilingual-mpnet-base-v2).
    """

    def __init__(self, model_name: str | None = None, vector_dim: int | None = None):
        self.model_name = model_name or settings.EMBEDDING_MODEL
        self.vector_dim = vector_dim or settings.VECTOR_DIM
        self._model: Any = None
        self._engine: str = "fastembed"  # 'fastembed' or 'sentence_transformers'
        self._active_model_name: str = self.model_name

    def _get_model(self) -> Any:
        if self._model is not None:
            return self._model

        # 1. Check if sentence_transformers is available
        try:
            import sentence_transformers
            from sentence_transformers import SentenceTransformer

            logger.info("Initializing SentenceTransformer with model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
            self._engine = "sentence_transformers"
            self._active_model_name = self.model_name
            return self._model
        except (ImportError, Exception) as exc:
            logger.debug(
                "sentence_transformers unavailable or failed to load (%s), falling back to FastEmbed",
                exc,
            )

        # 2. Use FastEmbed with alias resolution
        from fastembed import TextEmbedding

        fastembed_model = FASTEMBED_MODEL_ALIASES.get(self.model_name, self.model_name)
        # Check supported models in FastEmbed
        supported_names = {m["model"] for m in TextEmbedding.list_supported_models()}
        if fastembed_model not in supported_names:
            logger.warning(
                "Model '%s' not in FastEmbed supported registry. Falling back to '%s'",
                fastembed_model,
                "sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
            )
            fastembed_model = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"

        logger.info("Initializing FastEmbed TextEmbedding model: %s", fastembed_model)
        self._model = TextEmbedding(model_name=fastembed_model)
        self._engine = "fastembed"
        self._active_model_name = fastembed_model
        return self._model

    def build_property_text(
        self,
        title: str,
        description: str,
        address: str,
        ward: str | None = None,
        district: str | None = None,
        city: str | None = None,
        property_type: str | None = None,
        listing_type: str | None = None,
        num_bedrooms: int | None = None,
        num_bathrooms: int | None = None,
        area_sqm: float | None = None,
        price: float | None = None,
        currency: str = "VND",
    ) -> str:
        """
        Construct a consolidated semantic text string from property title, description,
        type, bedroom/bathroom count, area, price, and location.
        """
        parts: list[str] = []
        if title and title.strip():
            parts.append(title.strip())

        type_details: list[str] = []
        if property_type:
            label = PROPERTY_TYPE_VI_LABELS.get(property_type, property_type)
            type_details.append(f"Loại hình: {label}")
        if listing_type:
            type_details.append(f"Hình thức: {'Cho thuê' if listing_type == 'rent' else 'Bán'}")
        if num_bedrooms is not None:
            type_details.append(f"{num_bedrooms} phòng ngủ")
        if num_bathrooms is not None:
            type_details.append(f"{num_bathrooms} phòng vệ sinh")
        if area_sqm is not None and area_sqm > 0:
            type_details.append(f"Diện tích: {area_sqm} m²")
        if price is not None and price > 0:
            type_details.append(f"Giá: {price:,.0f} {currency}")
        if type_details:
            parts.append(", ".join(type_details))

        if description and description.strip():
            parts.append(description.strip())

        location_components = [
            item.strip() for item in [address, ward, district, city] if item and item.strip()
        ]
        if location_components:
            parts.append(f"Địa chỉ: {', '.join(location_components)}")

        return ". ".join(parts)

    def _prepare_text(self, text: str, is_query: bool = False) -> str:
        text = text.strip()
        # E5 model family requires query: or passage: prefix for optimal representation
        model_check = self._active_model_name.lower()
        if "e5" in model_check:
            if is_query and not text.startswith("query: "):
                return f"query: {text}"
            elif not is_query and not text.startswith("passage: "):
                return f"passage: {text}"
        return text

    def generate_embedding(self, text: str, is_query: bool = False) -> list[float]:
        """
        Generate a single 768-dimensional vector embedding for the input text.
        """
        if not text or not text.strip():
            return [0.0] * self.vector_dim

        prepared = self._prepare_text(text, is_query=is_query)
        model = self._get_model()

        if self._engine == "sentence_transformers":
            vector = model.encode(prepared, normalize_embeddings=True).tolist()
        else:
            embeddings_iter = model.embed([prepared])
            vector = next(iter(embeddings_iter)).tolist()
            vector = _l2_normalize(vector)

        if len(vector) != self.vector_dim:
            logger.warning(
                "Embedding dimension mismatch: expected %d, got %d",
                self.vector_dim,
                len(vector),
            )

        return [float(x) for x in vector]

    def generate_embeddings(
        self, texts: list[str], is_query: bool = False
    ) -> list[list[float]]:
        """
        Generate 768-dimensional vector embeddings for a batch of texts.
        """
        if not texts:
            return []

        results: list[list[float]] = []
        valid_indices: list[int] = []
        valid_texts: list[str] = []

        for idx, t in enumerate(texts):
            if not t or not t.strip():
                results.append([0.0] * self.vector_dim)
            else:
                results.append([])  # placeholder
                valid_indices.append(idx)
                valid_texts.append(self._prepare_text(t, is_query=is_query))

        if not valid_texts:
            return results

        model = self._get_model()
        if self._engine == "sentence_transformers":
            vectors = model.encode(valid_texts, normalize_embeddings=True).tolist()
            for idx, vec in zip(valid_indices, vectors):
                results[idx] = [float(x) for x in vec]
        else:
            embeddings_iter = model.embed(valid_texts)
            for idx, vec in zip(valid_indices, embeddings_iter):
                results[idx] = _l2_normalize([float(x) for x in vec.tolist()])

        return results


_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """FastAPI dependency to retrieve or initialize the singleton EmbeddingService instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service
