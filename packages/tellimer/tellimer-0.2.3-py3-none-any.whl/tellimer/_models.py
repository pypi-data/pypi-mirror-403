from dataclasses import dataclass

import pandas as pd

DATASETS: dict[str, str] = {
    "macro_data": "macro-data-v2",
    "parallel_fx": "parallel-fx-data",
    "probability_default": "probability-default",
    # "imf_arrangements": "imf-arrangements",
    # "debt_composition": "debt-comp",
    # "event_calendar": "calendar",
}


@dataclass
class Result:
    data: pd.DataFrame
    metadata: list[dict] | None = None
