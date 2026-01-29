""" REST views for the semantic search package
"""

from drf_spectacular.utils import (
    extend_schema,
    OpenApiExample,
    OpenApiResponse,
)
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from core_main_app.commons.constants import DATA_JSON_FIELD
from core_main_app.components.data import api as data_api
from core_main_app.utils.boolean import to_bool
from core_main_app.utils.query.mongo.query_builder import QueryBuilder
from core_semantic_search_app.components.model_settings.models import (
    ModelSettings,
)
from core_semantic_search_app.utils.model_utils import model_api
from core_semantic_search_app.utils.model_utils.response import (
    build_doc_list,
    build_doc_data_list,
)


@extend_schema(
    tags=["Semantic Search"],
    description="Search",
)
class SearchView(APIView):
    """Search view"""

    permission_classes = (IsAuthenticated,)

    @extend_schema(
        summary="Execute a search query",
        description="""Execute a search query with optional filtering.""",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "threshold": {"type": "number"},
                    "top_k": {"type": "integer"},
                    "snippets_only": {"type": "boolean"},
                    "filters": {"type": "object"},
                },
            }
        },
        responses={
            200: OpenApiResponse(description="Search results"),
            400: OpenApiResponse(description="Bad Request"),
            500: OpenApiResponse(description="Internal server error"),
        },
        examples=[
            OpenApiExample(
                name="Simple search query",
                description="Execute a simple search query",
                value={"query": "search_term", "top_k": 10, "threshold": 0.8},
                request_only=True,
                response_only=False,
            ),
            OpenApiExample(
                name="Search query with filters",
                description="Execute a search query with filters",
                value={"query": "search_term", "filters": {"field": "value"}},
                request_only=True,
                response_only=False,
            ),
        ],
    )
    def post(self, request):
        """Execute query
        Args:
            request: HTTP request
        Returns:
            - code: 200
              content:
            - code: 500
              content: Internal server error
        """
        try:
            query = request.data.get("query", None)
            threshold = float(request.data.get("threshold", 0.8))
            top_k = int(request.data.get("top_k", 10))
            snippets_only = to_bool(request.data.get("snippets_only", True))
            filter_query = request.data.get("filters", None)

            if not query or not len(query):
                return Response(
                    {"'query' parameter is missing or empty."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            model_settings = ModelSettings.get()
            if (
                not model_settings
                or not model_settings.embedding_models.keys()
            ):
                content = {"message": "An embedding model has not been set."}
                return Response(
                    content, status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            filters = None
            if filter_query:
                filters = data_api.execute_json_query(
                    QueryBuilder(
                        filter_query, DATA_JSON_FIELD
                    ).get_raw_query(),
                    request.user,
                ).values("id")

            documents = model_api.semantic_search(
                query, threshold=threshold, top_k=top_k, filters=filters
            )

            if snippets_only:
                return Response(
                    build_doc_list(documents), status=status.HTTP_200_OK
                )
            data_ids = set(
                [document.meta["data_id"] for document in documents]
            )
            data_pids = {
                str(document.meta["data_id"]): document.meta["data_pid"]
                for document in documents
            }
            return Response(
                build_doc_data_list(
                    data_api.get_by_id_list(data_ids, request.user), data_pids
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as api_exception:
            content = {"message": str(api_exception)}
            return Response(
                content, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
