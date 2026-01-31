"""Client for Probability of Default data."""

import pandas as pd
from tellimer._models import Result
from tellimer.types import MakeRequestFunc


class ProbabilityDefaultClient:
    """
    A client for the Tellimer API's probability of default endpoints.
    """

    def __init__(self, make_request: MakeRequestFunc):
        """
        Initialize the client.

        Args:
            make_request: The function to use to make the request.
        """
        self._make_request = make_request

    def available_countries(self) -> list[str]:
        """
        List all available countries for probability of default data.

        Returns:
            A list of country codes.
        """
        url = "api/v1/probability-default/list-countries"
        response = self._make_request("get", url)
        return response.json()

    def get(
        self,
        countries: list[str] | str | None = None,
        include_contributions: bool = False,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Result:
        """
        Get probability of default data.

        Args:
            countries: Optional country or list of countries to get data for.
                      If not provided, fetches data for all available countries.
            include_contributions: Whether to include contribution breakdowns.
            start_date: Optional start date filter (ISO format).
            end_date: Optional end date filter (ISO format).

        Returns:
            A Result containing a pandas DataFrame and metadata.
        """
        if isinstance(countries, str):
            countries = [countries]

        if countries:
            available = self.available_countries()
            for country in countries:
                if country not in available:
                    raise ValueError(
                        f"Country {country} is not available for probability of default data"
                    )

        url = "api/v1/probability-default"
        payload = {
            "countries": countries,
            "include_contributions": include_contributions,
            "start_date": start_date,
            "end_date": end_date,
        }
        response = self._make_request("post", url, json=payload)
        data = response.json()
        df = pd.DataFrame(data)
        metadata = None
        return Result(metadata=metadata, data=df)
