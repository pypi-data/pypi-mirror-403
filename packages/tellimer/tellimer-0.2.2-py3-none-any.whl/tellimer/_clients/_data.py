import re
from datetime import date, datetime
from typing import Any

import pandas as pd

from tellimer._clients._probability_default import ProbabilityDefaultClient
from tellimer._models import DATASETS, Result
from tellimer.types import MakeRequestFunc


class Filter:
    def __init__(self, field: str):
        self.field = field
        self.filter = None

    def equals(self, value: str):
        value = self._format_date(value)
        self.filter = f"{self.field}:{value}"
        return self

    def not_equals(self, value: str):
        value = self._format_date(value)
        self.filter = f"NOT {self.field}:{value}"
        return self

    def greater_than(self, value: str):
        value = self._format_date(value)
        self.filter = f"{self.field} > {value}"
        return self

    def greater_than_or_equal_to(self, value: str):
        value = self._format_date(value)
        self.filter = f"{self.field} >= {value}"
        return self

    def less_than(self, value: str):
        value = self._format_date(value)
        self.filter = f"{self.field} < {value}"
        return self

    def less_than_or_equal_to(self, value: str):
        value = self._format_date(value)
        self.filter = f"{self.field} <= {value}"
        return self

    def _format_date(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return int(value.timestamp())
        elif isinstance(value, date):
            return int(datetime.combine(value, datetime.min.time()).timestamp())
        elif isinstance(value, str):
            if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
                return int(datetime.strptime(value, "%Y-%m-%d").timestamp())
            elif re.match(r"^\d{4}/\d{2}/\d{2}$", value):
                return int(datetime.strptime(value, "%Y/%m/%d").timestamp())
            elif " " in value or ":" in value:
                return f"'{value}'"
        return value


class DataClient:
    """
    A client for the Tellimer API's data endpoints. This client is used to interact with the Tellimer API's data endpoints.
    """

    def __init__(self, make_request: MakeRequestFunc):
        """
        Initialize the client.

        Args:
            make_request: The function to use to make the request.
        """
        self._make_request = make_request
        self._datasets = [k for k in DATASETS.keys()]

        self.macro_data = _BaseSearchableDataset(self._make_request, "macro_data")

        self.parallel_fx = _BaseDataset(self._make_request, "parallel_fx")
        self.probability_default = ProbabilityDefaultClient(self._make_request)
        # self.imf_arrangements = _BaseDataset(self._make_request, "imf_arrangements")
        # self.debt_composition = _BaseDataset(self._make_request, "debt_composition")
        # self.event_calendar = _BaseDataset(self._make_request, "event_calendar")

    def list_datasets(self) -> list[str]:
        """
        List all available datasets.
        """
        return self._datasets


class _BaseDataset:
    def __init__(self, make_request: MakeRequestFunc, dataset: str):
        """
        Initialize the client.

        Args:
            make_request: The function to use to make the request.
            dataset: The dataset to use for the client.
        """
        self._make_request = make_request
        self._dataset = dataset

    def available_countries(self) -> list[str]:
        """
        List all available countries for a given dataset.

        Returns:
            A list of countries.
        """
        url = "api/v1/data/list-countries"
        payload = {"dataset": DATASETS[self._dataset]}
        response = self._make_request("post", url, json=payload)
        return response.json()

    def get(
        self,
        countries: list[str] | str,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Result:
        """
        Get data for a given dataset.

        Args:
            countries: The countries to get data for.
            start_date: The start date to get data for.
            end_date: The end date to get data for.
        Returns:
            A pandas DataFrame containing the data.
        """
        if isinstance(countries, str):
            countries = [countries]

        for country in countries:
            if country not in self.available_countries():
                raise ValueError(
                    f"Country {country} is not available for dataset {self._dataset}"
                )

        url = "api/v1/data/dataset"
        payload = {
            "countries": countries,
            "dataset": DATASETS[self._dataset],
            "start_date": start_date,
            "end_date": end_date,
        }
        response = self._make_request("post", url, json=payload)
        data = response.json()
        metadata, values = _extract_metadata(data, self._dataset)
        values = _create_multiindex_dataframe(values, self._dataset)
        return Result(metadata=metadata, data=values)


class _BaseSearchableDataset:
    def __init__(self, make_request: MakeRequestFunc, dataset: str):
        """
        Initialize the client.
        """
        self._make_request = make_request
        self._dataset = dataset

    def search(
        self,
        query: str,
        limit: int | None = 5,
        filters: list[Filter] | None = None,
    ) -> list[dict]:
        """
        Search for indicators.

        Args:
            query: The query to search for.
            limit: The number of results to return.
            filters: The filters to apply to the search.
        Returns:
            A list of dictionaries containing the indicators or a pandas DataFrame containing the indicators.
        """
        if filters:
            filters = " AND ".join(
                [filter.filter for filter in filters if filter.filter]
            )

        url = "api/v1/data/search-indicators"
        payload = {"query": query, "limit": limit, "filters": filters}
        response = self._make_request("post", url, json=payload)
        return response.json()

    def get(
        self,
        countries: list[str] | str,
        indicators: list[str] | str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> Result:
        """
        Get data for a given indicator.

        Args:
            indicators: The indicators to get data for.
            countries: The countries to get data for.
            start_date: The start date to get data for.
            end_date: The end date to get data for.
        Returns:
            A pandas DataFrame containing the data.
        """
        if not indicators and not countries:
            raise ValueError("At least one of indicators or countries must be provided")

        if isinstance(indicators, str):
            indicators = [indicators]
        elif not indicators:
            indicators = []

        if isinstance(countries, str):
            countries = [countries]
        elif not countries:
            raise ValueError("countries must be provided")

        url = "api/v1/data/indicators"
        payload = {
            "indicators": indicators,
            "countries": countries,
            "start_date": start_date,
            "end_date": end_date,
        }
        response = self._make_request("post", url, json=payload)
        data = response.json()
        metadata, values = _extract_metadata(data, self._dataset)
        values = _create_multiindex_dataframe(values, self._dataset)
        return Result(metadata=metadata, data=values)


def _extract_metadata(data: dict, dataset: str) -> tuple[list[dict], list[dict]]:
    """
    Extract the metadata from the JSON data.
    """
    metadata = []
    values = []

    if dataset == "macro_data":
        for d in data:
            metadata.append({k: v for k, v in d.items() if k != "data"})
            values.extend(
                [
                    val | {"indicator": d["indicator"], "country": d["country"]}
                    for val in d["data"]
                ]
            )
        return metadata, values

    elif dataset == "parallel_fx":
        for d in data:
            if d["data"]:
                metadata.append(
                    {"country": d["country"], "currency": d["data"][0]["currency"]}
                )
                values.extend([val | {"country": d["country"]} for val in d["data"]])
        return metadata, values


def _create_multiindex_dataframe(data: list[dict], dataset: str) -> pd.DataFrame:
    """
    Create a DataFrame with multi-level columns from macroeconomic data

    Expected JSON structure:
    [
        {"date": "1991-02-20", "indicator": "GDP", "country": "ARG", "value": 123.45},
        {"date": "1991-02-20", "indicator": "GDP", "country": "PAK", "value": 67.89},
        ...
    ]
    """
    # Convert JSON to DataFrame
    df = pd.DataFrame(data)

    # Handle empty data case
    if df.empty:
        return df

    # Convert date to datetime and set as index
    df["date"] = pd.to_datetime(df["date"])

    if dataset == "macro_data":
        columns = ["indicator", "country"]

    elif dataset == "parallel_fx":
        columns = ["country"]

    else:
        raise ValueError(f"Unsupported dataset: {dataset}")

    # Pivot to create multi-level columns
    pivot_df = df.pivot_table(
        index="date",
        columns=columns,
        values="value",
        aggfunc="first",  # Use 'first' in case of duplicates
    )

    return pivot_df
