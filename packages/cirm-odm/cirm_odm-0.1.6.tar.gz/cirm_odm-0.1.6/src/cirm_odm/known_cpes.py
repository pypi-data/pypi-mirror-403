from beanie import Document
from typing import Optional
from datetime import datetime


class KnownCPE(Document):
    """
    Stores known vendor-product pairs extracted from existing CPEs.
    Useful for validation, matching, or suggestions during CVE processing.

    Attributes:
        vendor : Vendor name.
        product : Product name.
        published_date : published date.
        last_modified_date : last modified date.
    """
    vendor: str
    product: str
    published_date: Optional[datetime] = None
    last_modified_date: Optional[datetime] = None

    class Settings:
        name = "known-cpes"
