# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = [
    "SearchUserSearchParams",
    "Filters",
    "FiltersUnionMember0",
    "FiltersUnionMember1",
    "FiltersUnionMember1Filter",
    "FiltersUnionMember2",
    "FiltersUnionMember2Filter",
    "FiltersUnionMember2FilterUnionMember0",
    "FiltersUnionMember2FilterUnionMember1",
    "FiltersUnionMember2FilterUnionMember1Filter",
    "IncludeAttributes",
    "IncludeAttributesContributes",
    "IncludeAttributesContributesFilters",
    "IncludeAttributesContributesFiltersUnionMember0",
    "IncludeAttributesContributesFiltersUnionMember1",
    "IncludeAttributesContributesFiltersUnionMember1Filter",
    "IncludeAttributesContributesFiltersUnionMember2",
    "IncludeAttributesContributesFiltersUnionMember2Filter",
    "IncludeAttributesContributesFiltersUnionMember2FilterUnionMember0",
    "IncludeAttributesContributesFiltersUnionMember2FilterUnionMember1",
    "IncludeAttributesContributesFiltersUnionMember2FilterUnionMember1Filter",
    "IncludeAttributesFollowers",
    "IncludeAttributesFollowersFilters",
    "IncludeAttributesFollowersFiltersUnionMember0",
    "IncludeAttributesFollowersFiltersUnionMember1",
    "IncludeAttributesFollowersFiltersUnionMember1Filter",
    "IncludeAttributesFollowersFiltersUnionMember2",
    "IncludeAttributesFollowersFiltersUnionMember2Filter",
    "IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember0",
    "IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember1",
    "IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember1Filter",
    "IncludeAttributesFollowing",
    "IncludeAttributesFollowingFilters",
    "IncludeAttributesFollowingFiltersUnionMember0",
    "IncludeAttributesFollowingFiltersUnionMember1",
    "IncludeAttributesFollowingFiltersUnionMember1Filter",
    "IncludeAttributesFollowingFiltersUnionMember2",
    "IncludeAttributesFollowingFiltersUnionMember2Filter",
    "IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember0",
    "IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember1",
    "IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember1Filter",
    "IncludeAttributesOwns",
    "IncludeAttributesOwnsFilters",
    "IncludeAttributesOwnsFiltersUnionMember0",
    "IncludeAttributesOwnsFiltersUnionMember1",
    "IncludeAttributesOwnsFiltersUnionMember1Filter",
    "IncludeAttributesOwnsFiltersUnionMember2",
    "IncludeAttributesOwnsFiltersUnionMember2Filter",
    "IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember0",
    "IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember1",
    "IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember1Filter",
    "IncludeAttributesStars",
    "IncludeAttributesStarsFilters",
    "IncludeAttributesStarsFiltersUnionMember0",
    "IncludeAttributesStarsFiltersUnionMember1",
    "IncludeAttributesStarsFiltersUnionMember1Filter",
    "IncludeAttributesStarsFiltersUnionMember2",
    "IncludeAttributesStarsFiltersUnionMember2Filter",
    "IncludeAttributesStarsFiltersUnionMember2FilterUnionMember0",
    "IncludeAttributesStarsFiltersUnionMember2FilterUnionMember1",
    "IncludeAttributesStarsFiltersUnionMember2FilterUnionMember1Filter",
]


class SearchUserSearchParams(TypedDict, total=False):
    query: Required[Union[str, SequenceNotStr[str], None]]
    """Full-text search query across user fields.

    Searches: login, displayName, bio, company, location, emails, resolvedCountry,
    resolvedState, resolvedCity (with login weighted 2x). Supports: string (single
    query), string[] (RRF fusion), null (filter-only)
    """

    after: str
    """Cursor for pagination (from previous response pageInfo.endCursor)"""

    enable_pagination: Annotated[bool, PropertyInfo(alias="enablePagination")]
    """Enable cursor-based pagination to fetch results across multiple requests"""

    filters: Filters
    """Optional filters for users.

    Supports fields like login, company, location, resolvedCountry, resolvedState,
    resolvedCity. Operators: Eq, NotEq, In, NotIn, Lt, Lte, Gt, Gte.
    """

    first: int
    """Alias for maxResults (takes precedence if both provided)"""

    include_attributes: Annotated[IncludeAttributes, PropertyInfo(alias="includeAttributes")]
    """
    Optional graph relationships to include (followers, following, stars, owns,
    contributes)
    """

    max_results: Annotated[int, PropertyInfo(alias="maxResults")]
    """Maximum number of results to return (default: 100, max: 1000)"""


class FiltersUnionMember0(TypedDict, total=False):
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


class FiltersUnionMember1Filter(TypedDict, total=False):
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


class FiltersUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[FiltersUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


class FiltersUnionMember2FilterUnionMember0(TypedDict, total=False):
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


class FiltersUnionMember2FilterUnionMember1Filter(TypedDict, total=False):
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


class FiltersUnionMember2FilterUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[FiltersUnionMember2FilterUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


FiltersUnionMember2Filter: TypeAlias = Union[
    FiltersUnionMember2FilterUnionMember0, FiltersUnionMember2FilterUnionMember1
]


class FiltersUnionMember2(TypedDict, total=False):
    filters: Required[Iterable[FiltersUnionMember2Filter]]
    """Array of filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


Filters: TypeAlias = Union[FiltersUnionMember0, FiltersUnionMember1, FiltersUnionMember2]


class IncludeAttributesContributesFiltersUnionMember0(TypedDict, total=False):
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


class IncludeAttributesContributesFiltersUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesContributesFiltersUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesContributesFiltersUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


class IncludeAttributesContributesFiltersUnionMember2FilterUnionMember0(TypedDict, total=False):
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


class IncludeAttributesContributesFiltersUnionMember2FilterUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesContributesFiltersUnionMember2FilterUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesContributesFiltersUnionMember2FilterUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesContributesFiltersUnionMember2Filter: TypeAlias = Union[
    IncludeAttributesContributesFiltersUnionMember2FilterUnionMember0,
    IncludeAttributesContributesFiltersUnionMember2FilterUnionMember1,
]


class IncludeAttributesContributesFiltersUnionMember2(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesContributesFiltersUnionMember2Filter]]
    """Array of filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesContributesFilters: TypeAlias = Union[
    IncludeAttributesContributesFiltersUnionMember0,
    IncludeAttributesContributesFiltersUnionMember1,
    IncludeAttributesContributesFiltersUnionMember2,
]


class IncludeAttributesContributes(TypedDict, total=False):
    """Include contributed repositories with cursor pagination"""

    first: Required[int]
    """Number of items to return (max: 100)"""

    after: str
    """Cursor for pagination (opaque base64-encoded)"""

    filters: IncludeAttributesContributesFilters
    """Optional filters for users.

    Supports fields like login, company, location, resolvedCountry, resolvedState,
    resolvedCity. Operators: Eq, NotEq, In, NotIn, Lt, Lte, Gt, Gte.
    """


class IncludeAttributesFollowersFiltersUnionMember0(TypedDict, total=False):
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


class IncludeAttributesFollowersFiltersUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesFollowersFiltersUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesFollowersFiltersUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


class IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember0(TypedDict, total=False):
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


class IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesFollowersFiltersUnionMember2Filter: TypeAlias = Union[
    IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember0,
    IncludeAttributesFollowersFiltersUnionMember2FilterUnionMember1,
]


class IncludeAttributesFollowersFiltersUnionMember2(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesFollowersFiltersUnionMember2Filter]]
    """Array of filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesFollowersFilters: TypeAlias = Union[
    IncludeAttributesFollowersFiltersUnionMember0,
    IncludeAttributesFollowersFiltersUnionMember1,
    IncludeAttributesFollowersFiltersUnionMember2,
]


class IncludeAttributesFollowers(TypedDict, total=False):
    """Include followers with cursor pagination"""

    first: Required[int]
    """Number of items to return (max: 100)"""

    after: str
    """Cursor for pagination (opaque base64-encoded)"""

    filters: IncludeAttributesFollowersFilters
    """Optional filters for users.

    Supports fields like login, company, location, resolvedCountry, resolvedState,
    resolvedCity. Operators: Eq, NotEq, In, NotIn, Lt, Lte, Gt, Gte.
    """


class IncludeAttributesFollowingFiltersUnionMember0(TypedDict, total=False):
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


class IncludeAttributesFollowingFiltersUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesFollowingFiltersUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesFollowingFiltersUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


class IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember0(TypedDict, total=False):
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


class IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesFollowingFiltersUnionMember2Filter: TypeAlias = Union[
    IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember0,
    IncludeAttributesFollowingFiltersUnionMember2FilterUnionMember1,
]


class IncludeAttributesFollowingFiltersUnionMember2(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesFollowingFiltersUnionMember2Filter]]
    """Array of filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesFollowingFilters: TypeAlias = Union[
    IncludeAttributesFollowingFiltersUnionMember0,
    IncludeAttributesFollowingFiltersUnionMember1,
    IncludeAttributesFollowingFiltersUnionMember2,
]


class IncludeAttributesFollowing(TypedDict, total=False):
    """Include users this user follows with cursor pagination"""

    first: Required[int]
    """Number of items to return (max: 100)"""

    after: str
    """Cursor for pagination (opaque base64-encoded)"""

    filters: IncludeAttributesFollowingFilters
    """Optional filters for users.

    Supports fields like login, company, location, resolvedCountry, resolvedState,
    resolvedCity. Operators: Eq, NotEq, In, NotIn, Lt, Lte, Gt, Gte.
    """


class IncludeAttributesOwnsFiltersUnionMember0(TypedDict, total=False):
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


class IncludeAttributesOwnsFiltersUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesOwnsFiltersUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesOwnsFiltersUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


class IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember0(TypedDict, total=False):
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


class IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesOwnsFiltersUnionMember2Filter: TypeAlias = Union[
    IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember0,
    IncludeAttributesOwnsFiltersUnionMember2FilterUnionMember1,
]


class IncludeAttributesOwnsFiltersUnionMember2(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesOwnsFiltersUnionMember2Filter]]
    """Array of filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesOwnsFilters: TypeAlias = Union[
    IncludeAttributesOwnsFiltersUnionMember0,
    IncludeAttributesOwnsFiltersUnionMember1,
    IncludeAttributesOwnsFiltersUnionMember2,
]


class IncludeAttributesOwns(TypedDict, total=False):
    """Include owned repositories with cursor pagination"""

    first: Required[int]
    """Number of items to return (max: 100)"""

    after: str
    """Cursor for pagination (opaque base64-encoded)"""

    filters: IncludeAttributesOwnsFilters
    """Optional filters for users.

    Supports fields like login, company, location, resolvedCountry, resolvedState,
    resolvedCity. Operators: Eq, NotEq, In, NotIn, Lt, Lte, Gt, Gte.
    """


class IncludeAttributesStarsFiltersUnionMember0(TypedDict, total=False):
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


class IncludeAttributesStarsFiltersUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesStarsFiltersUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesStarsFiltersUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


class IncludeAttributesStarsFiltersUnionMember2FilterUnionMember0(TypedDict, total=False):
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


class IncludeAttributesStarsFiltersUnionMember2FilterUnionMember1Filter(TypedDict, total=False):
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


class IncludeAttributesStarsFiltersUnionMember2FilterUnionMember1(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesStarsFiltersUnionMember2FilterUnionMember1Filter]]
    """Array of field filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesStarsFiltersUnionMember2Filter: TypeAlias = Union[
    IncludeAttributesStarsFiltersUnionMember2FilterUnionMember0,
    IncludeAttributesStarsFiltersUnionMember2FilterUnionMember1,
]


class IncludeAttributesStarsFiltersUnionMember2(TypedDict, total=False):
    filters: Required[Iterable[IncludeAttributesStarsFiltersUnionMember2Filter]]
    """Array of filters"""

    op: Required[Literal["And", "Or"]]
    """Composite operator"""


IncludeAttributesStarsFilters: TypeAlias = Union[
    IncludeAttributesStarsFiltersUnionMember0,
    IncludeAttributesStarsFiltersUnionMember1,
    IncludeAttributesStarsFiltersUnionMember2,
]


class IncludeAttributesStars(TypedDict, total=False):
    """Include starred repositories with cursor pagination"""

    first: Required[int]
    """Number of items to return (max: 100)"""

    after: str
    """Cursor for pagination (opaque base64-encoded)"""

    filters: IncludeAttributesStarsFilters
    """Optional filters for users.

    Supports fields like login, company, location, resolvedCountry, resolvedState,
    resolvedCity. Operators: Eq, NotEq, In, NotIn, Lt, Lte, Gt, Gte.
    """


class IncludeAttributes(TypedDict, total=False):
    """
    Optional graph relationships to include (followers, following, stars, owns, contributes)
    """

    contributes: IncludeAttributesContributes
    """Include contributed repositories with cursor pagination"""

    devrank: bool
    """Include devrank data for the user"""

    followers: IncludeAttributesFollowers
    """Include followers with cursor pagination"""

    following: IncludeAttributesFollowing
    """Include users this user follows with cursor pagination"""

    owns: IncludeAttributesOwns
    """Include owned repositories with cursor pagination"""

    professional: bool
    """Include LinkedIn professional profile data (requires PROFESSIONAL service)"""

    stars: IncludeAttributesStars
    """Include starred repositories with cursor pagination"""
