"""AI Models resource."""

from __future__ import annotations

from planvantage.models.aimodel import AIModelResponse
from planvantage.resources.base import BaseResource


class AIModelsResource(BaseResource):
    """Resource for AI model configuration."""

    def list(self) -> list[AIModelResponse]:
        """List available AI models.

        Returns AI model configurations available for extraction tasks,
        including quality/speed rankings and active status.

        Returns:
            List of AI model configurations.

        Example:
            >>> models = client.ai_models.list()
            >>> for model in models:
            ...     print(f"{model.display_name}: {model.quality_ranking}")
        """
        data = self._http.get("/ai-models")
        models = data.get("models", []) if isinstance(data, dict) else []
        return [AIModelResponse.model_validate(item) for item in models]

    def get_active(self) -> list[AIModelResponse]:
        """List only active AI models.

        Returns:
            List of active AI model configurations.

        Example:
            >>> active_models = client.ai_models.get_active()
        """
        return [m for m in self.list() if m.is_active]
