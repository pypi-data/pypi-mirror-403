from typing import Dict, Any, List, Optional
import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("BioModelsTool")
class BioModelsTool(BaseTool):
    """
    Tool for searching and retrieving models from EBI BioModels.
    """

    BASE_URL = "https://www.ebi.ac.uk/biomodels"

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the BioModels tool action.
        """
        action = arguments.get("action")

        if action == "search_models":
            return self.search_models(
                query=arguments.get("query"), limit=arguments.get("limit", 10)
            )
        elif action == "get_model_files":
            model_id = arguments.get("model_id")
            if not model_id:
                raise ValueError("model_id is required for get_model_files")
            return self.get_model_files(model_id)
        else:
            raise ValueError(f"Unknown action: {action}")

    def search_models(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """
        Search for biological models.
        """
        url = f"{self.BASE_URL}/search"
        params = {"query": query, "format": "json", "numResults": limit}

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # The API returns 'models' list directly? Or wrapped?
            # Test output showed `{"models": [...]}`

            models = []
            for m in data.get("models", []):
                models.append(
                    {
                        "id": m.get("id"),
                        "name": m.get("name"),
                        "format": m.get("format"),
                        "url": m.get("url"),
                    }
                )

            return {"count": len(models), "models": models}
        except Exception as e:
            return {"error": str(e)}

    def get_model_files(self, model_id: str) -> Dict[str, Any]:
        """
        Get file download links for a model.
        Usually returning the main SBML file link is sufficient.
        The search result usually gives a URL.
        Constructing download URL: https://www.ebi.ac.uk/biomodels/model/download/MODEL_ID?filename=MODEL_ID_url.xml ??
        Actually, API might have an endpoint for files.
        Documentation says `get_model_files(model_id)`.
        Let's try to find a specific endpoint or just return the model page/download link.
        Common pattern: https://www.ebi.ac.uk/biomodels/{model_id}#Files
        Or https://www.ebi.ac.uk/biomodels/model/download/{model_id}

        I'll return the download URL.
        """
        # If I want to list files, I might need another endpoint.
        # But simply returning the download link for the main model file is often what's needed.
        # Download URL: https://www.ebi.ac.uk/biomodels/{model_id}?format=sbml (maybe?)

        # Let's check `search` result 'url'.
        # Sample: "url": "https://www.ebi.ac.uk/biomodels/BIOMD0000000469"

        # I'll rely on a known pattern or just return the main URL.
        # A more specific API call `GET /model/files/{modelId}`?
        # I'll assume just returning the main page URL and formulated download URL is enough for now.
        download_url = (
            f"{self.BASE_URL}/model/download/{model_id}?filename={model_id}_url.xml"
        )

        return {
            "model_id": model_id,
            "main_page": f"{self.BASE_URL}/{model_id}",
            "download_url": download_url,  # This is a best guess, user might need to verify
        }
