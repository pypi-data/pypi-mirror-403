from tellimer.types import MakeRequestFunc


class NewsClient:
    """
    A client for the Tellimer API's news endpoints.
    """

    def __init__(self, make_request: MakeRequestFunc):
        """
        Initialize the client.

        Args:
            make_request: The function to use to make the request.
        """
        self._make_request = make_request

    def get_news(self): ...

    def search_news(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for news.

        Args:
            query: The query to search for.
            limit: The number of results to return.

        Returns:
            A list of news.
        """

        url = "api/v1/news/search"
        payload = {"query": query, "limit": limit}
        response = self._make_request("post", url, json=payload)
        response.raise_for_status()
        return response.json()
