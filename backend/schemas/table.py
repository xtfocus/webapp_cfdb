from typing import Any, Dict, List

from pydantic import BaseModel


class TableModel(BaseModel):
    """
    The Response model for table summary
    """

    name: str
    n_rows: int
    columns: List[str]
    primary_key: List[str]
    foreign_key: List[Dict[str, Any]]
    columns: List[Dict[str, Any]]
