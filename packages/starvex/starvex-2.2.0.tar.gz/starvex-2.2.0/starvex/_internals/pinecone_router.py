"""
Starvex Pinecone Router - Cloud-based semantic routing with Pinecone.

Uses Pinecone's integrated inference for high-accuracy semantic routing
without requiring local embedding models.

This provides:
- Scalable cloud-based semantic matching
- No local GPU/CPU overhead for embeddings
- Built-in reranking for higher accuracy
- Easy management of routes via Pinecone console
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class PineconeRouteMatch:
    """Result of a Pinecone route match"""

    route: Optional[str]
    score: float
    matched: bool
    details: Dict[str, Any] = field(default_factory=dict)


class PineconeRouter:
    """
    Semantic router using Pinecone for cloud-based topic detection.

    This is an alternative to the local SemanticRouter that uses
    Pinecone's integrated embedding and search capabilities.

    Example:
        router = PineconeRouter(
            api_key="pc-xxx",
            index_name="starvex-semantic-routes"
        )

        result = router.route("what cryptocurrency should I buy?")
        # result.route == "investment_advice"
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        index_name: str = "starvex-semantic-routes",
        namespace: str = "default-routes",
        default_sensitivity: float = 0.7,
    ):
        """
        Initialize the Pinecone Router.

        Args:
            api_key: Pinecone API key (or set PINECONE_API_KEY env var)
            index_name: Name of the Pinecone index
            namespace: Namespace within the index
            default_sensitivity: Default threshold for matching
        """
        self.api_key = api_key
        self.index_name = index_name
        self.namespace = namespace
        self.default_sensitivity = default_sensitivity

        self._client = None
        self._index = None
        self._initialized = False

    def _ensure_initialized(self):
        """Lazy initialization of Pinecone client"""
        if self._initialized:
            return

        try:
            from pinecone import Pinecone
            import os

            api_key = self.api_key or os.environ.get("PINECONE_API_KEY")
            if not api_key:
                raise ValueError(
                    "Pinecone API key required. "
                    "Set PINECONE_API_KEY env var or pass api_key parameter."
                )

            self._client = Pinecone(api_key=api_key)
            self._index = self._client.Index(self.index_name)
            self._initialized = True

            logger.info(f"PineconeRouter initialized with index: {self.index_name}")

        except ImportError:
            logger.error("pinecone-client not installed. Install with: pip install starvex[vector]")
            raise

    def route(
        self,
        text: str,
        top_k: int = 5,
        rerank: bool = True,
    ) -> PineconeRouteMatch:
        """
        Route text to the best matching route using Pinecone.

        Args:
            text: Input text to classify
            top_k: Number of candidates to retrieve
            rerank: Whether to use reranking for higher accuracy

        Returns:
            PineconeRouteMatch with route name and score
        """
        self._ensure_initialized()

        try:
            # Query Pinecone with integrated inference
            if rerank:
                results = self._index.search(
                    namespace=self.namespace,
                    query={
                        "inputs": {"text": text},
                        "top_k": top_k * 2,  # Get more for reranking
                    },
                    rerank={
                        "model": "bge-reranker-v2-m3",
                        "top_n": top_k,
                        "rank_fields": ["utterance"],
                    },
                )
            else:
                results = self._index.search(
                    namespace=self.namespace,
                    query={
                        "inputs": {"text": text},
                        "top_k": top_k,
                    },
                )

            # Extract matches
            matches = results.get("result", {}).get("hits", [])

            if not matches:
                return PineconeRouteMatch(
                    route=None,
                    score=0.0,
                    matched=False,
                )

            # Get the best match
            best_match = matches[0]
            fields = best_match.get("fields", {})
            route = fields.get("route")
            score = best_match.get("_score", 0.0)
            sensitivity = fields.get("sensitivity", self.default_sensitivity)

            # Check if score exceeds sensitivity threshold
            matched = score >= sensitivity

            return PineconeRouteMatch(
                route=route if matched else None,
                score=score,
                matched=matched,
                details={
                    "all_matches": [
                        {
                            "route": m.get("fields", {}).get("route"),
                            "score": m.get("_score"),
                            "utterance": m.get("fields", {}).get("utterance"),
                        }
                        for m in matches[:3]
                    ]
                },
            )

        except Exception as e:
            logger.error(f"Pinecone query error: {e}")
            return PineconeRouteMatch(
                route=None,
                score=0.0,
                matched=False,
                details={"error": str(e)},
            )

    def add_route(
        self,
        route_name: str,
        utterances: List[str],
        sensitivity: float = 0.75,
    ) -> bool:
        """
        Add a new route with example utterances.

        Args:
            route_name: Name of the route (e.g., "competitors")
            utterances: List of example phrases
            sensitivity: Threshold for matching

        Returns:
            True if successful
        """
        self._ensure_initialized()

        try:
            records = [
                {
                    "id": f"{route_name}-{i}",
                    "route": route_name,
                    "sensitivity": sensitivity,
                    "utterance": utterance,
                }
                for i, utterance in enumerate(utterances)
            ]

            self._index.upsert_records(
                namespace=self.namespace,
                records=records,
            )

            logger.info(f"Added route '{route_name}' with {len(utterances)} utterances")
            return True

        except Exception as e:
            logger.error(f"Failed to add route: {e}")
            return False

    def remove_route(self, route_name: str) -> bool:
        """Remove a route by deleting all its records"""
        self._ensure_initialized()

        try:
            # Delete by filter on route metadata
            self._index.delete(
                namespace=self.namespace,
                filter={"route": {"$eq": route_name}},
            )

            logger.info(f"Removed route: {route_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove route: {e}")
            return False

    def check_intent(self, text: str) -> Dict[str, Any]:
        """
        Check if text matches any forbidden intents.

        Compatible API with AccuracyEngine.

        Returns:
            Dict with 'safe' boolean and 'reason' if unsafe
        """
        result = self.route(text)

        if result.matched:
            return {
                "safe": False,
                "reason": f"Triggered {result.route} guardrail",
                "route": result.route,
                "confidence": result.score,
                "details": result.details,
            }

        return {"safe": True, "confidence": 1.0 - result.score}

    @property
    def stats(self) -> Dict[str, Any]:
        """Get router statistics"""
        if not self._initialized:
            return {"initialized": False}

        try:
            index_stats = self._index.describe_index_stats()
            return {
                "initialized": True,
                "index_name": self.index_name,
                "namespace": self.namespace,
                "total_vectors": index_stats.get("total_vector_count", 0),
                "namespaces": list(index_stats.get("namespaces", {}).keys()),
            }
        except:
            return {"initialized": True, "error": "Could not fetch stats"}


class CloudAccuracyEngine:
    """
    Cloud-based AccuracyEngine using Pinecone.

    Drop-in replacement for the local AccuracyEngine that uses
    Pinecone for semantic routing. Useful for production deployments
    where you don't want to run local embedding models.
    """

    def __init__(
        self,
        pinecone_api_key: Optional[str] = None,
        index_name: str = "starvex-semantic-routes",
    ):
        self.router = PineconeRouter(
            api_key=pinecone_api_key,
            index_name=index_name,
        )

    def check_intent(self, text: str) -> Dict[str, Any]:
        """Check if text matches forbidden intents"""
        return self.router.check_intent(text)

    def add_custom_route(
        self,
        name: str,
        utterances: List[str],
        sensitivity: float = 0.75,
    ) -> bool:
        """Add a custom route"""
        return self.router.add_route(name, utterances, sensitivity)

    @property
    def stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return self.router.stats
