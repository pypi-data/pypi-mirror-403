from typing import Any, Callable

import httpx

MakeRequestFunc = Callable[[str, str, Any], httpx.Response]
