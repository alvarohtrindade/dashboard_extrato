from dataclasses import dataclass
from typing import List, Optional
from datetime import date

@dataclass
class FilterParams:
    start_date: date
    end_date: date
    funds: Optional[List[str]] = None
    custodians: Optional[List[str]] = None
    limit: Optional[int] = None