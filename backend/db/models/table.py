from enum import Enum
from typing import Literal

from pydantic import BaseModel


class TableName(str, Enum):
    TRANSLATION = "CID_LCIN_DICTIONARY"
    EN_UMLS = "CID_LCIN_EN_UMLS"
    EN_DO = "CID_LCIN_EN_DO"
    VN_SYNONYM = "CID_LCIN_VN_SYNONYM"
    CID_LCIN_EN_SYNONYM = "CID_LCIN_EN_SYNONYM"
    UMLS_SYNONYM = "CID_LCIN_EN_UMLS_SYNONYM"
    DO_SYNONYM = "CID_LCIN_EN_DO_SYNONYM"
    EDITOR = "CID_LCIN_EDITOR"
    VSOURCE = "CID_LCIN_VALIDATION_SOURCE"


class StandardName(str, Enum):
    EN_UMLS = TableName.EN_UMLS.value
    EN_DO = TableName.EN_DO.value
