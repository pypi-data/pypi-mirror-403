from typing import List, Literal
from app.odm.cpe_model import CVEConfiguration
from beanie import Document


class CVEModel(Document):
    """
    Represents a Common Vulnerabilities and Exposures (CVE) entry
    as stored within the CIRM data model.

    This document aggregates the core information provided by the NVD,
    including descriptive metadata, severity scoring, associated weaknesses,
    and the logical CPE configurations that describe the affected platforms.

    Attributes:
        id:
            Unique identifier of the CVE (e.g., "CVE-2024-12345").

        description:
            Official textual description of the vulnerability.

        status:
            Current status of the CVE.
            Possible values are:
            - "Rejected": the CVE has been rejected by the issuing authority.
            - "noRejected": the CVE is valid and active.

        published_date:
            Timestamp indicating when the CVE was initially published.

        last_modified_date:
            Timestamp indicating the last update of the CVE record.

        cvss:
            Base CVSS score associated with the vulnerability, as provided
            by the NVD.

        cwe:
            List of Common Weakness Enumeration (CWE) identifiers
            associated with the CVE.

        cpe:
            List of CPE configurations describing the affected platforms.
            Each configuration encodes logical conditions (AND / OR)
            over CPE matches, following the NVD data model.
    """
    id: str
    description: str
    status: Literal['Rejected', 'noRejected']
    published_date: str
    last_modified_date: str
    cvss: float
    cwe: List[str]
    cpe: List[CVEConfiguration]


    class Settings:
        """
        Beanie document settings for the CVEModel.

        Attributes:
            name:
                Name of the MongoDB collection used to store CVE documents.

            use_revision:
                Indicates whether document revisioning is enabled.

            id_type:
                Data type of the document identifier.
        """
        name = 'cves'
        use_revision = False
        id_type = str

    class Config:
        """
        Pydantic configuration for the CVEModel.

        Attributes:
            arbitrary_types_allowed:
                Allows the use of arbitrary (non-Pydantic) types
                within the model fields.
        """
        arbitrary_types_allowed = True