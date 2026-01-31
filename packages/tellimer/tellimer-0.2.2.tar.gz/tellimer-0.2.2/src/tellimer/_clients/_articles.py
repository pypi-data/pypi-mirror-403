from tellimer.types import MakeRequestFunc


class ArticlesClient:
    """
    A client for the Tellimer API's articles endpoints.
    """

    def __init__(self, make_request: MakeRequestFunc):
        """
        Initialize the client.

        Args:
            make_request: The function to use to make the request.
        """
        self._make_request = make_request

    def get_articles(self): ...

    def search_articles(self, query: str, limit: int = 10) -> list[dict]:
        """
        Search for articles.

        Args:
            query: The query to search for.
            limit: The number of results to return.

        Returns:
            A list of articles.
        """

        url = "api/v1/articles/search"
        payload = {"query": query, "limit": limit}
        response = self._make_request("post", url, json=payload)
        response.raise_for_status()
        return response.json()
