from typing import List, Optional
from pydantic import BaseModel
from beanie import Document


class Detection(BaseModel):
    """
    Represents a detection method associated with a Common Weakness Enumeration (CWE).

    Attributes:
        detection_id (Optional[str]):
            Optional identifier used internally by the CWE team to uniquely
            identify the detection method.

        method (Optional[str]):
            The technique or approach used to detect the weakness.

        description (Optional[str]):
            A textual description of how the detection method works.

        effectiveness (Optional[str]):
            An assessment of how effective the detection method may be in
            identifying the associated weakness.

        effectiveness_notes (Optional[str]):
            Additional notes describing the strengths and limitations of the
            detection method.
    """
    detection_id: Optional[str] = None
    method: Optional[str] = None
    description: Optional[str] = None
    effectiveness: Optional[str] = None
    effectiveness_notes: Optional[str] = None


class Mitigation(BaseModel):
    """
    Represents a potential mitigation associated with a CWE weakness.

    This model corresponds to an individual mitigation entry defined in the CWE
    specification and describes a possible action that can reduce or prevent
    the exploitation of a weakness.

    Attributes:
        phase (Optional[str]):
            The software development life cycle phase during which this
            mitigation may be applied (e.g., Architecture and Design,
            Implementation).

        description (Optional[str]):
            A detailed description of the mitigation, including its strengths,
            limitations, and relevant considerations.

        effectiveness (Optional[str]):
            A qualitative summary of how effective the mitigation may be in
            preventing or reducing the impact of the weakness.

        effectiveness_notes (Optional[str]):
            Additional notes providing further context on the effectiveness of
            the mitigation.
    """
    phase: Optional[str] = None
    description: Optional[str] = None
    effectiveness: Optional[str] = None
    effectiveness_notes: Optional[str] = None
    
    
class CWEModel(Document):
    """
    Represents a Common Weakness Enumeration (CWE) document stored in MongoDB.

    Attributes:
        id (str):
            Unique identifier of the CWE (e.g., CWE-79).

        name (str):
            Human-readable name of the CWE.

        usage (Optional[str]):
            Usage information or mapping notes associated with the CWE.

        status (str):
            Current status of the CWE (e.g., Draft, Incomplete, Stable).

        description (Optional[str]):
            A detailed textual description of the weakness.

        related_cwe_ids (List[str]):
            List of identifiers of CWEs related to this weakness.

        detection (Optional[List[Detection]]):
            Detection methods that can be used to identify the weakness.

        mitigation (Optional[List[Mitigation]]):
            Potential mitigations applicable to the weakness.

        created_at (Optional[str]):
            Date when the CWE was initially submitted.

        last_update (Optional[str]):
            Date of the most recent modification to the CWE.
    """
    id: str
    name: str
    usage: Optional[str] = None
    status: str
    description: Optional[str] = None
    related_cwe_ids: List[str]
    detection: Optional[List[Detection]] = None
    mitigation: Optional[List[Mitigation]] = None
    created_at: Optional[str] = None
    last_update: Optional[str] = None

    class Settings:
        """
        Configuration settings for the CWEModel document.

        Attributes:
            name : Name of the MongoDB collection.
            use_revision : Flag indicating whether to use revisioning.
            id_type : Type of the document's ID field.
        """
        name = "cwes"
        use_revision = False
        id_type = str

    class Config:
        """
        Pydantic configuration for the CWEModel.

        Attributes:
            arbitrary_types_allowed: Flag indicating whether to allow types.
        """
        arbitrary_types_allowed = True
