from typing import List, Optional
from datetime import datetime
from beanie import Document
from pydantic import BaseModel, Field
from .cpe_model import CVEConfiguration


class CPEEntity(BaseModel):
    """
    Represents a predicted entity related to a CPE string.
    """
    entity_group: str
    word: str
    score: float
    start: int
    end: int


class ProductWithPart(BaseModel):
    """
    Represents a product name and its corresponding CPE part (a, o, h).
    """
    name: str
    part: str


class CVEPredictions(BaseModel):
    """
    Contains predicted information for a CVE, including CVSS score,
    CWE identifiers, and CPE-related entities
    such as vendors, products, and versions.
    Used when actual data is unavailable
    or as supplementary model-generated data.
    """
    cvss: Optional[float] = None
    cwes: Optional[List[str]] = None
    cpes: List[CPEEntity] = Field(default_factory=list)
    vendors: List[str] = Field(default_factory=list)
    products: List[ProductWithPart] = Field(default_factory=list)
    versions: List[str] = Field(default_factory=list)


class CVEProcessingResults(Document):
    """
    Stores final CVE processing output, including actual
    or predicted CVSS, CWE, and CPE.
    """
    id: str
    cvss: float
    cwe: List[str]
    cpe: List[CVEConfiguration]
    predictions: CVEPredictions = Field(default_factory=CVEPredictions)
    published_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None

    class Settings:
        name = "cve-processing-results"
        use_revision = False
        id_type = str

    class Config:
        arbitrary_types_allowed = True
