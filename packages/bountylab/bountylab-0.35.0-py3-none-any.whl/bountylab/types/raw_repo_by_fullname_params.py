# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = [
    "RawRepoByFullnameParams",
    "IncludeAttributes",
    "IncludeAttributesContributors",
    "IncludeAttributesContributorsFilters",
    "IncludeAttributesContributorsFiltersUnionMember0",
    "IncludeAttributesContributorsFiltersUnionMember1",
    "IncludeAttributesContributorsFiltersUnionMember1Filter",
    "IncludeAttributesContributorsFiltersUnionMember2",
    "IncludeAttributesContributorsFiltersUnionMember2Filter",
    "IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember0",
    "IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember1",
    "IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember1Filter",
    "IncludeAttributesStarrers",
    "IncludeAttributesStarrersFilters",
    "IncludeAttributesStarrersFiltersUnionMember0",
    "IncludeAttributesStarrersFiltersUnionMember1",
    "IncludeAttributesStarrersFiltersUnionMember1Filter",
    "IncludeAttributesStarrersFiltersUnionMember2",
    "IncludeAttributesStarrersFiltersUnionMember2Filter",
    "IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember0",
    "IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember1",
    "IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember1Filter",
]


class RawRepoByFullnameParams(TypedDict, total=False):
    full_names: Required[Annotated[SequenceNotStr[str], PropertyInfo(alias="fullNames")]]
    """Array of repository full names in "owner/name" format (1-100)"""

    include_attributes: Annotated[IncludeAttributes, PropertyInfo(alias="includeAttributes")]
    """Optional graph relationships to include (owner, contributors, starrers)"""


class IncludeAttributesContributorsFiltersUnionMember0(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[
        Literal[
            "Eq",
            "NotEq",
            "In",
            "NotIn",
            "Lt",
            "Lte",
            "Gt",
            "Gte",
            "Glob",
            "NotGlob",
            "IGlob",
            "NotIGlob",
            "Regex",
            "Contains",
            "NotContains",
            "ContainsAny",
            "NotContainsAny",
            "AnyLt",
            "AnyLte",
            "AnyGt",
            "AnyGte",
            "ContainsAllTokens",
        ]
    ]
    """Filter operator"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value (type depends on field and operator)"""


class IncludeAttributesContributorsFiltersUnionMember1Filter(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[
        Literal[
            "Eq",
            "NotEq",
            "In",
            "NotIn",
            "Lt",
            "Lte",
            "Gt",
            "Gte",
            "Glob",
            "NotGlob",
            "IGlob",
            "NotIGlob",
            "Regex",
            "Contains",
            "NotContains",
            "ContainsAny",
            "NotContainsAny",
            "AnyLt",
            "AnyLte",
            "AnyGt",
            "AnyGte",
            "ContainsAllTokens",
        ]
    ]
    """Filter operator"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value (type depends on field and operator)"""


class IncludeAttributesContributorsFiltersUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesContributorsFiltersUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


class IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember0(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[
        Literal[
            "Eq",
            "NotEq",
            "In",
            "NotIn",
            "Lt",
            "Lte",
            "Gt",
            "Gte",
            "Glob",
            "NotGlob",
            "IGlob",
            "NotIGlob",
            "Regex",
            "Contains",
            "NotContains",
            "ContainsAny",
            "NotContainsAny",
            "AnyLt",
            "AnyLte",
            "AnyGt",
            "AnyGte",
            "ContainsAllTokens",
        ]
    ]
    """Filter operator"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value (type depends on field and operator)"""


class IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember1Filter(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[
        Literal[
            "Eq",
            "NotEq",
            "In",
            "NotIn",
            "Lt",
            "Lte",
            "Gt",
            "Gte",
            "Glob",
            "NotGlob",
            "IGlob",
            "NotIGlob",
            "Regex",
            "Contains",
            "NotContains",
            "ContainsAny",
            "NotContainsAny",
            "AnyLt",
            "AnyLte",
            "AnyGt",
            "AnyGte",
            "ContainsAllTokens",
        ]
    ]
    """Filter operator"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value (type depends on field and operator)"""


class IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesContributorsFiltersUnionMember2Filter: TypeAlias = Union[
    IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember0,
    IncludeAttributesContributorsFiltersUnionMember2FilterUnionMember1,
]


class IncludeAttributesContributorsFiltersUnionMember2(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesContributorsFiltersUnionMember2Filter]]
    """Array of filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesContributorsFilters: TypeAlias = Union[
    IncludeAttributesContributorsFiltersUnionMember0,
    IncludeAttributesContributorsFiltersUnionMember1,
    IncludeAttributesContributorsFiltersUnionMember2,
]


class IncludeAttributesContributors(TypedDict, total=False):
    """Include repository contributors with cursor pagination"""

    first: Required[int]
    """Number of items to return (max: 100)"""

    after: str
    """Cursor for pagination (opaque base64-encoded)"""

    filters: IncludeAttributesContributorsFilters
    """Optional filters for users.

    Supports fields like login, company, location, resolvedCountry, resolvedState,
    resolvedCity. Operators: Eq, NotEq, In, NotIn, Lt, Lte, Gt, Gte.
    """


class IncludeAttributesStarrersFiltersUnionMember0(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[
        Literal[
            "Eq",
            "NotEq",
            "In",
            "NotIn",
            "Lt",
            "Lte",
            "Gt",
            "Gte",
            "Glob",
            "NotGlob",
            "IGlob",
            "NotIGlob",
            "Regex",
            "Contains",
            "NotContains",
            "ContainsAny",
            "NotContainsAny",
            "AnyLt",
            "AnyLte",
            "AnyGt",
            "AnyGte",
            "ContainsAllTokens",
        ]
    ]
    """Filter operator"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value (type depends on field and operator)"""


class IncludeAttributesStarrersFiltersUnionMember1Filter(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[
        Literal[
            "Eq",
            "NotEq",
            "In",
            "NotIn",
            "Lt",
            "Lte",
            "Gt",
            "Gte",
            "Glob",
            "NotGlob",
            "IGlob",
            "NotIGlob",
            "Regex",
            "Contains",
            "NotContains",
            "ContainsAny",
            "NotContainsAny",
            "AnyLt",
            "AnyLte",
            "AnyGt",
            "AnyGte",
            "ContainsAllTokens",
        ]
    ]
    """Filter operator"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value (type depends on field and operator)"""


class IncludeAttributesStarrersFiltersUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesStarrersFiltersUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


class IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember0(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[
        Literal[
            "Eq",
            "NotEq",
            "In",
            "NotIn",
            "Lt",
            "Lte",
            "Gt",
            "Gte",
            "Glob",
            "NotGlob",
            "IGlob",
            "NotIGlob",
            "Regex",
            "Contains",
            "NotContains",
            "ContainsAny",
            "NotContainsAny",
            "AnyLt",
            "AnyLte",
            "AnyGt",
            "AnyGte",
            "ContainsAllTokens",
        ]
    ]
    """Filter operator"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value (type depends on field and operator)"""


class IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember1Filter(TypedDict, total=False):
    field: Required[str]
    """Field name to filter on"""

    op: Required[
        Literal[
            "Eq",
            "NotEq",
            "In",
            "NotIn",
            "Lt",
            "Lte",
            "Gt",
            "Gte",
            "Glob",
            "NotGlob",
            "IGlob",
            "NotIGlob",
            "Regex",
            "Contains",
            "NotContains",
            "ContainsAny",
            "NotContainsAny",
            "AnyLt",
            "AnyLte",
            "AnyGt",
            "AnyGte",
            "ContainsAllTokens",
        ]
    ]
    """Filter operator"""

    value: Required[Union[str, float, SequenceNotStr[str], Iterable[float]]]
    """Filter value (type depends on field and operator)"""


class IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesStarrersFiltersUnionMember2Filter: TypeAlias = Union[
    IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember0,
    IncludeAttributesStarrersFiltersUnionMember2FilterUnionMember1,
]


class IncludeAttributesStarrersFiltersUnionMember2(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesStarrersFiltersUnionMember2Filter]]
    """Array of filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesStarrersFilters: TypeAlias = Union[
    IncludeAttributesStarrersFiltersUnionMember0,
    IncludeAttributesStarrersFiltersUnionMember1,
    IncludeAttributesStarrersFiltersUnionMember2,
]


class IncludeAttributesStarrers(TypedDict, total=False):
    """Include users who starred the repository with cursor pagination"""

    first: Required[int]
    """Number of items to return (max: 100)"""

    after: str
    """Cursor for pagination (opaque base64-encoded)"""

    filters: IncludeAttributesStarrersFilters
    """Optional filters for users.

    Supports fields like login, company, location, resolvedCountry, resolvedState,
    resolvedCity. Operators: Eq, NotEq, In, NotIn, Lt, Lte, Gt, Gte.
    """


class IncludeAttributes(TypedDict, total=False):
    """Optional graph relationships to include (owner, contributors, starrers)"""

    contributors: IncludeAttributesContributors
    """Include repository contributors with cursor pagination"""

    owner: bool
    """Include repository owner information"""

    owner_devrank: Annotated[bool, PropertyInfo(alias="ownerDevrank")]
    """Include devrank data for the repository owner"""

    owner_professional: Annotated[bool, PropertyInfo(alias="ownerProfessional")]
    """
    Include LinkedIn professional profile for the repository owner (requires
    PROFESSIONAL service)
    """

    starrers: IncludeAttributesStarrers
    """Include users who starred the repository with cursor pagination"""
