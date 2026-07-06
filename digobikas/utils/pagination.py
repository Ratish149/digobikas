from rest_framework.pagination import PageNumberPagination


class CustomPagination(PageNumberPagination):
    """
    Default pagination class for list endpoints.

    Query params:
      - page      : page number (default 1)
      - page_size : number of results per page (default 10, max 100)
    """

    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100
