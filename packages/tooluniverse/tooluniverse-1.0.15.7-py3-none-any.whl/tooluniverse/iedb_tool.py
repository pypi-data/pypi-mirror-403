from typing import Dict, Any, List, Optional
import requests
from .base_tool import BaseTool
from .tool_registry import register_tool


@register_tool("IEDBTool")
class IEDBTool(BaseTool):
    """
    Tool for interacting with the Immune Epitope Database (IEDB).
    """

    QUERY_API_URL = "https://query-api.iedb.org"

    def run(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the IEDB tool action.

        Args:
            arguments (Dict[str, Any]):
                - action (str): "search_epitopes"
                - query (str, optional): Sequence fragment (e.g., "KVF") to search in linear sequence.
                - structure_type (str, optional): "Linear peptide", etc.
                - organism (str, optional): Source organism name.
                - limit (int, default 10).

        Returns:
            Dict[str, Any]: Search results.
        """
        action = arguments.get("action")

        if action == "search_epitopes":
            return self.search_epitopes(
                query=arguments.get("query"),
                structure_type=arguments.get("structure_type"),
                organism=arguments.get("organism"),
                limit=arguments.get("limit", 10),
            )
        else:
            raise ValueError(f"Unknown action: {action}")

    def search_epitopes(
        self,
        query: Optional[str] = None,
        structure_type: Optional[str] = None,
        organism: Optional[str] = None,
        limit: int = 10,
    ) -> Dict[str, Any]:
        """
        Search for epitopes.
        """
        url = f"{self.QUERY_API_URL}/epitope_search"
        params = {"limit": limit, "order": "structure_id.asc"}

        if query:
            # Using ilike on linear_sequence as confirmed working
            params["linear_sequence"] = f"ilike.*{query}*"

        if structure_type:
            params["structure_type"] = f"eq.{structure_type}"

        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            epitopes = []
            for item in data:
                epitopes.append(
                    {
                        "id": item.get("structure_id"),
                        "type": item.get("structure_type"),
                        "sequence": item.get("linear_sequence"),
                        "description": item.get("structure_descriptions"),
                        "antigens": item.get("curated_source_antigens"),
                    }
                )

            return {"count": len(epitopes), "epitopes": epitopes}
        except Exception as e:
            return {"error": str(e)}
