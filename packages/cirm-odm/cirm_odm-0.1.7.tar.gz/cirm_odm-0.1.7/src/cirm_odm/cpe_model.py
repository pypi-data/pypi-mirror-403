from typing import List, Optional, Literal
from pydantic import BaseModel
from pydantic import Field


class CPEMatch(BaseModel):
    """
    Represents a single CPE match condition.

    A CPEMatch may refer either to:
    - a specific CPE 2.3 string, or
    - a version range expressed through start/end constraints.

    When the match represents a version range, the field `expanded_cpes`
    contains the list of concrete CPE 2.3 identifiers obtained by expanding
    the range via the NVD CPE Match API (matchCriteriaId).

    Attributes:
        vulnerable:
            Indicates whether the matched CPE is affected by the vulnerability.

        criteria:
            The original CPE 2.3 match criteria string as provided by NVD.
            This string may include wildcards or version ranges.

        match_criteria_id:
            Identifier of the match criteria in the NVD database.
            It can be used to resolve version ranges into concrete CPEs.

        version_start_including:
            Lower bound of the affected version range (inclusive).

        version_start_excluding:
            Lower bound of the affected version range (exclusive).

        version_end_including:
            Upper bound of the affected version range (inclusive).

        version_end_excluding:
            Upper bound of the affected version range (exclusive).

        expanded_cpes:
            List of concrete CPE 2.3 strings derived from the version range.
            This field is populated only when a version range is present;
            otherwise it may be empty.
    """
    vulnerable: bool
    criteria: str
    match_criteria_id: str
    version_start_including: Optional[str] = None
    version_start_excluding: Optional[str] = None
    version_end_excluding: Optional[str] = None
    version_end_including: Optional[str] = None
    expanded_cpes: List[str] = Field(default_factory=list)


class CPENode(BaseModel):
    """
    Represents a logical node in the CVE CPE configuration tree.

    A CPENode combines one or more CPEMatch elements using a logical operator
    (AND / OR) and may recursively contain child nodes, forming a tree
    structure equivalent to the one defined by the NVD CVE configuration model.

    Attributes:
        operator:
            Logical operator used to combine CPE matches and/or child nodes.

        negate:
            If True, the logical result of this node is negated.

        cpe_match:
            List of CPEMatch conditions associated with this node.

        children:
            Optional list of child CPENodes, allowing recursive logical
            expressions.
    """
    operator: Literal['AND', 'OR']
    negate: bool = False
    cpe_match: Optional[List[CPEMatch]] = None
    children: Optional[List["CPENode"]] = None


CPENode.model_rebuild()


class CVEConfiguration(BaseModel):
    """
    Represents a top-level CPE configuration for a CVE entry.

    A configuration consists of one or more logical nodes that describe
    the affected platforms and software combinations for the vulnerability,
    following the structure defined by the NVD.
    """
    operator: Optional[Literal['AND', 'OR']] = None
    nodes: List[CPENode] = Field(default_factory=list)
