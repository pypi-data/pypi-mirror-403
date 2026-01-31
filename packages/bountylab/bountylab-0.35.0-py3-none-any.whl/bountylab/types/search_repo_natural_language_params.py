# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing import Union, Iterable
from typing_extensions import Literal, Required, Annotated, TypeAlias, TypedDict

from .._types import SequenceNotStr
from .._utils import PropertyInfo

__all__ = [
    "SearchRepoNaturalLanguageParams",
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
    "RankBy",
    "RankByAttr",
    "RankByConst",
    "RankBySum",
    "RankBySumExpr",
    "RankBySumExprUnionMember0",
    "RankBySumExprUnionMember1",
    "RankBySumExprUnionMember2",
    "RankBySumExprUnionMember2Expr",
    "RankBySumExprUnionMember2ExprUnionMember0",
    "RankBySumExprUnionMember2ExprUnionMember1",
    "RankBySumExprUnionMember2ExprUnionMember2",
    "RankBySumExprUnionMember2ExprUnionMember2Expr",
    "RankBySumExprUnionMember2ExprUnionMember2ExprUnionMember0",
    "RankBySumExprUnionMember2ExprUnionMember2ExprUnionMember1",
    "RankBySumExprUnionMember2ExprUnionMember3",
    "RankBySumExprUnionMember2ExprUnionMember4",
    "RankBySumExprUnionMember2ExprUnionMember5",
    "RankBySumExprUnionMember2ExprUnionMember5Expr",
    "RankBySumExprUnionMember2ExprUnionMember5ExprUnionMember0",
    "RankBySumExprUnionMember2ExprUnionMember5ExprUnionMember1",
    "RankBySumExprUnionMember2ExprUnionMember6",
    "RankBySumExprUnionMember2ExprUnionMember6Expr",
    "RankBySumExprUnionMember2ExprUnionMember6ExprUnionMember0",
    "RankBySumExprUnionMember2ExprUnionMember6ExprUnionMember1",
    "RankBySumExprUnionMember2ExprUnionMember7",
    "RankBySumExprUnionMember2ExprUnionMember7Expr",
    "RankBySumExprUnionMember2ExprUnionMember7ExprUnionMember0",
    "RankBySumExprUnionMember2ExprUnionMember7ExprUnionMember1",
    "RankBySumExprUnionMember3",
    "RankBySumExprUnionMember4",
    "RankBySumExprUnionMember5",
    "RankBySumExprUnionMember5Expr",
    "RankBySumExprUnionMember5ExprUnionMember0",
    "RankBySumExprUnionMember5ExprUnionMember1",
    "RankBySumExprUnionMember5ExprUnionMember2",
    "RankBySumExprUnionMember5ExprUnionMember2Expr",
    "RankBySumExprUnionMember5ExprUnionMember2ExprUnionMember0",
    "RankBySumExprUnionMember5ExprUnionMember2ExprUnionMember1",
    "RankBySumExprUnionMember5ExprUnionMember3",
    "RankBySumExprUnionMember5ExprUnionMember4",
    "RankBySumExprUnionMember5ExprUnionMember5",
    "RankBySumExprUnionMember5ExprUnionMember5Expr",
    "RankBySumExprUnionMember5ExprUnionMember5ExprUnionMember0",
    "RankBySumExprUnionMember5ExprUnionMember5ExprUnionMember1",
    "RankBySumExprUnionMember5ExprUnionMember6",
    "RankBySumExprUnionMember5ExprUnionMember6Expr",
    "RankBySumExprUnionMember5ExprUnionMember6ExprUnionMember0",
    "RankBySumExprUnionMember5ExprUnionMember6ExprUnionMember1",
    "RankBySumExprUnionMember5ExprUnionMember7",
    "RankBySumExprUnionMember5ExprUnionMember7Expr",
    "RankBySumExprUnionMember5ExprUnionMember7ExprUnionMember0",
    "RankBySumExprUnionMember5ExprUnionMember7ExprUnionMember1",
    "RankBySumExprUnionMember6",
    "RankBySumExprUnionMember6Expr",
    "RankBySumExprUnionMember6ExprUnionMember0",
    "RankBySumExprUnionMember6ExprUnionMember1",
    "RankBySumExprUnionMember6ExprUnionMember2",
    "RankBySumExprUnionMember6ExprUnionMember2Expr",
    "RankBySumExprUnionMember6ExprUnionMember2ExprUnionMember0",
    "RankBySumExprUnionMember6ExprUnionMember2ExprUnionMember1",
    "RankBySumExprUnionMember6ExprUnionMember3",
    "RankBySumExprUnionMember6ExprUnionMember4",
    "RankBySumExprUnionMember6ExprUnionMember5",
    "RankBySumExprUnionMember6ExprUnionMember5Expr",
    "RankBySumExprUnionMember6ExprUnionMember5ExprUnionMember0",
    "RankBySumExprUnionMember6ExprUnionMember5ExprUnionMember1",
    "RankBySumExprUnionMember6ExprUnionMember6",
    "RankBySumExprUnionMember6ExprUnionMember6Expr",
    "RankBySumExprUnionMember6ExprUnionMember6ExprUnionMember0",
    "RankBySumExprUnionMember6ExprUnionMember6ExprUnionMember1",
    "RankBySumExprUnionMember6ExprUnionMember7",
    "RankBySumExprUnionMember6ExprUnionMember7Expr",
    "RankBySumExprUnionMember6ExprUnionMember7ExprUnionMember0",
    "RankBySumExprUnionMember6ExprUnionMember7ExprUnionMember1",
    "RankBySumExprUnionMember7",
    "RankBySumExprUnionMember7Expr",
    "RankBySumExprUnionMember7ExprUnionMember0",
    "RankBySumExprUnionMember7ExprUnionMember1",
    "RankBySumExprUnionMember7ExprUnionMember2",
    "RankBySumExprUnionMember7ExprUnionMember2Expr",
    "RankBySumExprUnionMember7ExprUnionMember2ExprUnionMember0",
    "RankBySumExprUnionMember7ExprUnionMember2ExprUnionMember1",
    "RankBySumExprUnionMember7ExprUnionMember3",
    "RankBySumExprUnionMember7ExprUnionMember4",
    "RankBySumExprUnionMember7ExprUnionMember5",
    "RankBySumExprUnionMember7ExprUnionMember5Expr",
    "RankBySumExprUnionMember7ExprUnionMember5ExprUnionMember0",
    "RankBySumExprUnionMember7ExprUnionMember5ExprUnionMember1",
    "RankBySumExprUnionMember7ExprUnionMember6",
    "RankBySumExprUnionMember7ExprUnionMember6Expr",
    "RankBySumExprUnionMember7ExprUnionMember6ExprUnionMember0",
    "RankBySumExprUnionMember7ExprUnionMember6ExprUnionMember1",
    "RankBySumExprUnionMember7ExprUnionMember7",
    "RankBySumExprUnionMember7ExprUnionMember7Expr",
    "RankBySumExprUnionMember7ExprUnionMember7ExprUnionMember0",
    "RankBySumExprUnionMember7ExprUnionMember7ExprUnionMember1",
    "RankByMult",
    "RankByDiv",
    "RankByMax",
    "RankByMaxExpr",
    "RankByMaxExprUnionMember0",
    "RankByMaxExprUnionMember1",
    "RankByMaxExprUnionMember2",
    "RankByMaxExprUnionMember2Expr",
    "RankByMaxExprUnionMember2ExprUnionMember0",
    "RankByMaxExprUnionMember2ExprUnionMember1",
    "RankByMaxExprUnionMember2ExprUnionMember2",
    "RankByMaxExprUnionMember2ExprUnionMember2Expr",
    "RankByMaxExprUnionMember2ExprUnionMember2ExprUnionMember0",
    "RankByMaxExprUnionMember2ExprUnionMember2ExprUnionMember1",
    "RankByMaxExprUnionMember2ExprUnionMember3",
    "RankByMaxExprUnionMember2ExprUnionMember4",
    "RankByMaxExprUnionMember2ExprUnionMember5",
    "RankByMaxExprUnionMember2ExprUnionMember5Expr",
    "RankByMaxExprUnionMember2ExprUnionMember5ExprUnionMember0",
    "RankByMaxExprUnionMember2ExprUnionMember5ExprUnionMember1",
    "RankByMaxExprUnionMember2ExprUnionMember6",
    "RankByMaxExprUnionMember2ExprUnionMember6Expr",
    "RankByMaxExprUnionMember2ExprUnionMember6ExprUnionMember0",
    "RankByMaxExprUnionMember2ExprUnionMember6ExprUnionMember1",
    "RankByMaxExprUnionMember2ExprUnionMember7",
    "RankByMaxExprUnionMember2ExprUnionMember7Expr",
    "RankByMaxExprUnionMember2ExprUnionMember7ExprUnionMember0",
    "RankByMaxExprUnionMember2ExprUnionMember7ExprUnionMember1",
    "RankByMaxExprUnionMember3",
    "RankByMaxExprUnionMember4",
    "RankByMaxExprUnionMember5",
    "RankByMaxExprUnionMember5Expr",
    "RankByMaxExprUnionMember5ExprUnionMember0",
    "RankByMaxExprUnionMember5ExprUnionMember1",
    "RankByMaxExprUnionMember5ExprUnionMember2",
    "RankByMaxExprUnionMember5ExprUnionMember2Expr",
    "RankByMaxExprUnionMember5ExprUnionMember2ExprUnionMember0",
    "RankByMaxExprUnionMember5ExprUnionMember2ExprUnionMember1",
    "RankByMaxExprUnionMember5ExprUnionMember3",
    "RankByMaxExprUnionMember5ExprUnionMember4",
    "RankByMaxExprUnionMember5ExprUnionMember5",
    "RankByMaxExprUnionMember5ExprUnionMember5Expr",
    "RankByMaxExprUnionMember5ExprUnionMember5ExprUnionMember0",
    "RankByMaxExprUnionMember5ExprUnionMember5ExprUnionMember1",
    "RankByMaxExprUnionMember5ExprUnionMember6",
    "RankByMaxExprUnionMember5ExprUnionMember6Expr",
    "RankByMaxExprUnionMember5ExprUnionMember6ExprUnionMember0",
    "RankByMaxExprUnionMember5ExprUnionMember6ExprUnionMember1",
    "RankByMaxExprUnionMember5ExprUnionMember7",
    "RankByMaxExprUnionMember5ExprUnionMember7Expr",
    "RankByMaxExprUnionMember5ExprUnionMember7ExprUnionMember0",
    "RankByMaxExprUnionMember5ExprUnionMember7ExprUnionMember1",
    "RankByMaxExprUnionMember6",
    "RankByMaxExprUnionMember6Expr",
    "RankByMaxExprUnionMember6ExprUnionMember0",
    "RankByMaxExprUnionMember6ExprUnionMember1",
    "RankByMaxExprUnionMember6ExprUnionMember2",
    "RankByMaxExprUnionMember6ExprUnionMember2Expr",
    "RankByMaxExprUnionMember6ExprUnionMember2ExprUnionMember0",
    "RankByMaxExprUnionMember6ExprUnionMember2ExprUnionMember1",
    "RankByMaxExprUnionMember6ExprUnionMember3",
    "RankByMaxExprUnionMember6ExprUnionMember4",
    "RankByMaxExprUnionMember6ExprUnionMember5",
    "RankByMaxExprUnionMember6ExprUnionMember5Expr",
    "RankByMaxExprUnionMember6ExprUnionMember5ExprUnionMember0",
    "RankByMaxExprUnionMember6ExprUnionMember5ExprUnionMember1",
    "RankByMaxExprUnionMember6ExprUnionMember6",
    "RankByMaxExprUnionMember6ExprUnionMember6Expr",
    "RankByMaxExprUnionMember6ExprUnionMember6ExprUnionMember0",
    "RankByMaxExprUnionMember6ExprUnionMember6ExprUnionMember1",
    "RankByMaxExprUnionMember6ExprUnionMember7",
    "RankByMaxExprUnionMember6ExprUnionMember7Expr",
    "RankByMaxExprUnionMember6ExprUnionMember7ExprUnionMember0",
    "RankByMaxExprUnionMember6ExprUnionMember7ExprUnionMember1",
    "RankByMaxExprUnionMember7",
    "RankByMaxExprUnionMember7Expr",
    "RankByMaxExprUnionMember7ExprUnionMember0",
    "RankByMaxExprUnionMember7ExprUnionMember1",
    "RankByMaxExprUnionMember7ExprUnionMember2",
    "RankByMaxExprUnionMember7ExprUnionMember2Expr",
    "RankByMaxExprUnionMember7ExprUnionMember2ExprUnionMember0",
    "RankByMaxExprUnionMember7ExprUnionMember2ExprUnionMember1",
    "RankByMaxExprUnionMember7ExprUnionMember3",
    "RankByMaxExprUnionMember7ExprUnionMember4",
    "RankByMaxExprUnionMember7ExprUnionMember5",
    "RankByMaxExprUnionMember7ExprUnionMember5Expr",
    "RankByMaxExprUnionMember7ExprUnionMember5ExprUnionMember0",
    "RankByMaxExprUnionMember7ExprUnionMember5ExprUnionMember1",
    "RankByMaxExprUnionMember7ExprUnionMember6",
    "RankByMaxExprUnionMember7ExprUnionMember6Expr",
    "RankByMaxExprUnionMember7ExprUnionMember6ExprUnionMember0",
    "RankByMaxExprUnionMember7ExprUnionMember6ExprUnionMember1",
    "RankByMaxExprUnionMember7ExprUnionMember7",
    "RankByMaxExprUnionMember7ExprUnionMember7Expr",
    "RankByMaxExprUnionMember7ExprUnionMember7ExprUnionMember0",
    "RankByMaxExprUnionMember7ExprUnionMember7ExprUnionMember1",
    "RankByMin",
    "RankByMinExpr",
    "RankByMinExprUnionMember0",
    "RankByMinExprUnionMember1",
    "RankByMinExprUnionMember2",
    "RankByMinExprUnionMember2Expr",
    "RankByMinExprUnionMember2ExprUnionMember0",
    "RankByMinExprUnionMember2ExprUnionMember1",
    "RankByMinExprUnionMember2ExprUnionMember2",
    "RankByMinExprUnionMember2ExprUnionMember2Expr",
    "RankByMinExprUnionMember2ExprUnionMember2ExprUnionMember0",
    "RankByMinExprUnionMember2ExprUnionMember2ExprUnionMember1",
    "RankByMinExprUnionMember2ExprUnionMember3",
    "RankByMinExprUnionMember2ExprUnionMember4",
    "RankByMinExprUnionMember2ExprUnionMember5",
    "RankByMinExprUnionMember2ExprUnionMember5Expr",
    "RankByMinExprUnionMember2ExprUnionMember5ExprUnionMember0",
    "RankByMinExprUnionMember2ExprUnionMember5ExprUnionMember1",
    "RankByMinExprUnionMember2ExprUnionMember6",
    "RankByMinExprUnionMember2ExprUnionMember6Expr",
    "RankByMinExprUnionMember2ExprUnionMember6ExprUnionMember0",
    "RankByMinExprUnionMember2ExprUnionMember6ExprUnionMember1",
    "RankByMinExprUnionMember2ExprUnionMember7",
    "RankByMinExprUnionMember2ExprUnionMember7Expr",
    "RankByMinExprUnionMember2ExprUnionMember7ExprUnionMember0",
    "RankByMinExprUnionMember2ExprUnionMember7ExprUnionMember1",
    "RankByMinExprUnionMember3",
    "RankByMinExprUnionMember4",
    "RankByMinExprUnionMember5",
    "RankByMinExprUnionMember5Expr",
    "RankByMinExprUnionMember5ExprUnionMember0",
    "RankByMinExprUnionMember5ExprUnionMember1",
    "RankByMinExprUnionMember5ExprUnionMember2",
    "RankByMinExprUnionMember5ExprUnionMember2Expr",
    "RankByMinExprUnionMember5ExprUnionMember2ExprUnionMember0",
    "RankByMinExprUnionMember5ExprUnionMember2ExprUnionMember1",
    "RankByMinExprUnionMember5ExprUnionMember3",
    "RankByMinExprUnionMember5ExprUnionMember4",
    "RankByMinExprUnionMember5ExprUnionMember5",
    "RankByMinExprUnionMember5ExprUnionMember5Expr",
    "RankByMinExprUnionMember5ExprUnionMember5ExprUnionMember0",
    "RankByMinExprUnionMember5ExprUnionMember5ExprUnionMember1",
    "RankByMinExprUnionMember5ExprUnionMember6",
    "RankByMinExprUnionMember5ExprUnionMember6Expr",
    "RankByMinExprUnionMember5ExprUnionMember6ExprUnionMember0",
    "RankByMinExprUnionMember5ExprUnionMember6ExprUnionMember1",
    "RankByMinExprUnionMember5ExprUnionMember7",
    "RankByMinExprUnionMember5ExprUnionMember7Expr",
    "RankByMinExprUnionMember5ExprUnionMember7ExprUnionMember0",
    "RankByMinExprUnionMember5ExprUnionMember7ExprUnionMember1",
    "RankByMinExprUnionMember6",
    "RankByMinExprUnionMember6Expr",
    "RankByMinExprUnionMember6ExprUnionMember0",
    "RankByMinExprUnionMember6ExprUnionMember1",
    "RankByMinExprUnionMember6ExprUnionMember2",
    "RankByMinExprUnionMember6ExprUnionMember2Expr",
    "RankByMinExprUnionMember6ExprUnionMember2ExprUnionMember0",
    "RankByMinExprUnionMember6ExprUnionMember2ExprUnionMember1",
    "RankByMinExprUnionMember6ExprUnionMember3",
    "RankByMinExprUnionMember6ExprUnionMember4",
    "RankByMinExprUnionMember6ExprUnionMember5",
    "RankByMinExprUnionMember6ExprUnionMember5Expr",
    "RankByMinExprUnionMember6ExprUnionMember5ExprUnionMember0",
    "RankByMinExprUnionMember6ExprUnionMember5ExprUnionMember1",
    "RankByMinExprUnionMember6ExprUnionMember6",
    "RankByMinExprUnionMember6ExprUnionMember6Expr",
    "RankByMinExprUnionMember6ExprUnionMember6ExprUnionMember0",
    "RankByMinExprUnionMember6ExprUnionMember6ExprUnionMember1",
    "RankByMinExprUnionMember6ExprUnionMember7",
    "RankByMinExprUnionMember6ExprUnionMember7Expr",
    "RankByMinExprUnionMember6ExprUnionMember7ExprUnionMember0",
    "RankByMinExprUnionMember6ExprUnionMember7ExprUnionMember1",
    "RankByMinExprUnionMember7",
    "RankByMinExprUnionMember7Expr",
    "RankByMinExprUnionMember7ExprUnionMember0",
    "RankByMinExprUnionMember7ExprUnionMember1",
    "RankByMinExprUnionMember7ExprUnionMember2",
    "RankByMinExprUnionMember7ExprUnionMember2Expr",
    "RankByMinExprUnionMember7ExprUnionMember2ExprUnionMember0",
    "RankByMinExprUnionMember7ExprUnionMember2ExprUnionMember1",
    "RankByMinExprUnionMember7ExprUnionMember3",
    "RankByMinExprUnionMember7ExprUnionMember4",
    "RankByMinExprUnionMember7ExprUnionMember5",
    "RankByMinExprUnionMember7ExprUnionMember5Expr",
    "RankByMinExprUnionMember7ExprUnionMember5ExprUnionMember0",
    "RankByMinExprUnionMember7ExprUnionMember5ExprUnionMember1",
    "RankByMinExprUnionMember7ExprUnionMember6",
    "RankByMinExprUnionMember7ExprUnionMember6Expr",
    "RankByMinExprUnionMember7ExprUnionMember6ExprUnionMember0",
    "RankByMinExprUnionMember7ExprUnionMember6ExprUnionMember1",
    "RankByMinExprUnionMember7ExprUnionMember7",
    "RankByMinExprUnionMember7ExprUnionMember7Expr",
    "RankByMinExprUnionMember7ExprUnionMember7ExprUnionMember0",
    "RankByMinExprUnionMember7ExprUnionMember7ExprUnionMember1",
    "RankByLog",
    "RankByLogExpr",
    "RankByLogExprUnionMember0",
    "RankByLogExprUnionMember1",
    "RankByLogExprUnionMember2",
    "RankByLogExprUnionMember2Expr",
    "RankByLogExprUnionMember2ExprUnionMember0",
    "RankByLogExprUnionMember2ExprUnionMember1",
    "RankByLogExprUnionMember2ExprUnionMember2",
    "RankByLogExprUnionMember2ExprUnionMember2Expr",
    "RankByLogExprUnionMember2ExprUnionMember2ExprUnionMember0",
    "RankByLogExprUnionMember2ExprUnionMember2ExprUnionMember1",
    "RankByLogExprUnionMember2ExprUnionMember3",
    "RankByLogExprUnionMember2ExprUnionMember4",
    "RankByLogExprUnionMember2ExprUnionMember5",
    "RankByLogExprUnionMember2ExprUnionMember5Expr",
    "RankByLogExprUnionMember2ExprUnionMember5ExprUnionMember0",
    "RankByLogExprUnionMember2ExprUnionMember5ExprUnionMember1",
    "RankByLogExprUnionMember2ExprUnionMember6",
    "RankByLogExprUnionMember2ExprUnionMember6Expr",
    "RankByLogExprUnionMember2ExprUnionMember6ExprUnionMember0",
    "RankByLogExprUnionMember2ExprUnionMember6ExprUnionMember1",
    "RankByLogExprUnionMember2ExprUnionMember7",
    "RankByLogExprUnionMember2ExprUnionMember7Expr",
    "RankByLogExprUnionMember2ExprUnionMember7ExprUnionMember0",
    "RankByLogExprUnionMember2ExprUnionMember7ExprUnionMember1",
    "RankByLogExprUnionMember3",
    "RankByLogExprUnionMember4",
    "RankByLogExprUnionMember5",
    "RankByLogExprUnionMember5Expr",
    "RankByLogExprUnionMember5ExprUnionMember0",
    "RankByLogExprUnionMember5ExprUnionMember1",
    "RankByLogExprUnionMember5ExprUnionMember2",
    "RankByLogExprUnionMember5ExprUnionMember2Expr",
    "RankByLogExprUnionMember5ExprUnionMember2ExprUnionMember0",
    "RankByLogExprUnionMember5ExprUnionMember2ExprUnionMember1",
    "RankByLogExprUnionMember5ExprUnionMember3",
    "RankByLogExprUnionMember5ExprUnionMember4",
    "RankByLogExprUnionMember5ExprUnionMember5",
    "RankByLogExprUnionMember5ExprUnionMember5Expr",
    "RankByLogExprUnionMember5ExprUnionMember5ExprUnionMember0",
    "RankByLogExprUnionMember5ExprUnionMember5ExprUnionMember1",
    "RankByLogExprUnionMember5ExprUnionMember6",
    "RankByLogExprUnionMember5ExprUnionMember6Expr",
    "RankByLogExprUnionMember5ExprUnionMember6ExprUnionMember0",
    "RankByLogExprUnionMember5ExprUnionMember6ExprUnionMember1",
    "RankByLogExprUnionMember5ExprUnionMember7",
    "RankByLogExprUnionMember5ExprUnionMember7Expr",
    "RankByLogExprUnionMember5ExprUnionMember7ExprUnionMember0",
    "RankByLogExprUnionMember5ExprUnionMember7ExprUnionMember1",
    "RankByLogExprUnionMember6",
    "RankByLogExprUnionMember6Expr",
    "RankByLogExprUnionMember6ExprUnionMember0",
    "RankByLogExprUnionMember6ExprUnionMember1",
    "RankByLogExprUnionMember6ExprUnionMember2",
    "RankByLogExprUnionMember6ExprUnionMember2Expr",
    "RankByLogExprUnionMember6ExprUnionMember2ExprUnionMember0",
    "RankByLogExprUnionMember6ExprUnionMember2ExprUnionMember1",
    "RankByLogExprUnionMember6ExprUnionMember3",
    "RankByLogExprUnionMember6ExprUnionMember4",
    "RankByLogExprUnionMember6ExprUnionMember5",
    "RankByLogExprUnionMember6ExprUnionMember5Expr",
    "RankByLogExprUnionMember6ExprUnionMember5ExprUnionMember0",
    "RankByLogExprUnionMember6ExprUnionMember5ExprUnionMember1",
    "RankByLogExprUnionMember6ExprUnionMember6",
    "RankByLogExprUnionMember6ExprUnionMember6Expr",
    "RankByLogExprUnionMember6ExprUnionMember6ExprUnionMember0",
    "RankByLogExprUnionMember6ExprUnionMember6ExprUnionMember1",
    "RankByLogExprUnionMember6ExprUnionMember7",
    "RankByLogExprUnionMember6ExprUnionMember7Expr",
    "RankByLogExprUnionMember6ExprUnionMember7ExprUnionMember0",
    "RankByLogExprUnionMember6ExprUnionMember7ExprUnionMember1",
    "RankByLogExprUnionMember7",
    "RankByLogExprUnionMember7Expr",
    "RankByLogExprUnionMember7ExprUnionMember0",
    "RankByLogExprUnionMember7ExprUnionMember1",
    "RankByLogExprUnionMember7ExprUnionMember2",
    "RankByLogExprUnionMember7ExprUnionMember2Expr",
    "RankByLogExprUnionMember7ExprUnionMember2ExprUnionMember0",
    "RankByLogExprUnionMember7ExprUnionMember2ExprUnionMember1",
    "RankByLogExprUnionMember7ExprUnionMember3",
    "RankByLogExprUnionMember7ExprUnionMember4",
    "RankByLogExprUnionMember7ExprUnionMember5",
    "RankByLogExprUnionMember7ExprUnionMember5Expr",
    "RankByLogExprUnionMember7ExprUnionMember5ExprUnionMember0",
    "RankByLogExprUnionMember7ExprUnionMember5ExprUnionMember1",
    "RankByLogExprUnionMember7ExprUnionMember6",
    "RankByLogExprUnionMember7ExprUnionMember6Expr",
    "RankByLogExprUnionMember7ExprUnionMember6ExprUnionMember0",
    "RankByLogExprUnionMember7ExprUnionMember6ExprUnionMember1",
    "RankByLogExprUnionMember7ExprUnionMember7",
    "RankByLogExprUnionMember7ExprUnionMember7Expr",
    "RankByLogExprUnionMember7ExprUnionMember7ExprUnionMember0",
    "RankByLogExprUnionMember7ExprUnionMember7ExprUnionMember1",
]


class SearchRepoNaturalLanguageParams(TypedDict, total=False):
    query: Required[str]
    """Natural language query describing the repositories you want to find"""

    after: str
    """Cursor for pagination (from previous response pageInfo.endCursor)"""

    apply_filters_to_include_attributes: Annotated[bool, PropertyInfo(alias="applyFiltersToIncludeAttributes")]
    """
    When true, applies the LLM-generated filter to all user-returning
    includeAttributes (contributors, starrers). Alias for
    filterUserIncludeAttributes.
    """

    enable_pagination: Annotated[bool, PropertyInfo(alias="enablePagination")]
    """Enable cursor-based pagination to fetch results across multiple requests"""

    filter_user_include_attributes: Annotated[bool, PropertyInfo(alias="filterUserIncludeAttributes")]
    """
    [Deprecated: Use applyFiltersToIncludeAttributes] When true, applies the
    LLM-generated filter to all user-returning includeAttributes (contributors,
    starrers).
    """

    first: int
    """Alias for maxResults (takes precedence if both provided)"""

    include_attributes: Annotated[IncludeAttributes, PropertyInfo(alias="includeAttributes")]
    """Optional graph relationships to include (owner, contributors, starrers)"""

    max_results: Annotated[int, PropertyInfo(alias="maxResults")]
    """Maximum number of results to return (default: 100, max: 1000)"""

    rank_by: Annotated[RankBy, PropertyInfo(alias="rankBy")]
    """Custom ranking formula (AST expression).

    If not provided, uses default log-normalized 70/20/10 formula (70% semantic
    similarity, 20% popularity, 10% activity).
    """


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


class RankByAttr(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByConst(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankBySumExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankBySumExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankBySumExprUnionMember2ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember2ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember2ExprUnionMember2Expr: TypeAlias = Union[
    RankBySumExprUnionMember2ExprUnionMember2ExprUnionMember0, RankBySumExprUnionMember2ExprUnionMember2ExprUnionMember1
]


class RankBySumExprUnionMember2ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember2ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankBySumExprUnionMember2ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankBySumExprUnionMember2ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankBySumExprUnionMember2ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember2ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember2ExprUnionMember5Expr: TypeAlias = Union[
    RankBySumExprUnionMember2ExprUnionMember5ExprUnionMember0, RankBySumExprUnionMember2ExprUnionMember5ExprUnionMember1
]


class RankBySumExprUnionMember2ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember2ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankBySumExprUnionMember2ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember2ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember2ExprUnionMember6Expr: TypeAlias = Union[
    RankBySumExprUnionMember2ExprUnionMember6ExprUnionMember0, RankBySumExprUnionMember2ExprUnionMember6ExprUnionMember1
]


class RankBySumExprUnionMember2ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember2ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankBySumExprUnionMember2ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember2ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember2ExprUnionMember7Expr: TypeAlias = Union[
    RankBySumExprUnionMember2ExprUnionMember7ExprUnionMember0, RankBySumExprUnionMember2ExprUnionMember7ExprUnionMember1
]


class RankBySumExprUnionMember2ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankBySumExprUnionMember2ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankBySumExprUnionMember2Expr: TypeAlias = Union[
    RankBySumExprUnionMember2ExprUnionMember0,
    RankBySumExprUnionMember2ExprUnionMember1,
    RankBySumExprUnionMember2ExprUnionMember2,
    RankBySumExprUnionMember2ExprUnionMember3,
    RankBySumExprUnionMember2ExprUnionMember4,
    RankBySumExprUnionMember2ExprUnionMember5,
    RankBySumExprUnionMember2ExprUnionMember6,
    RankBySumExprUnionMember2ExprUnionMember7,
]


class RankBySumExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankBySumExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankBySumExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankBySumExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankBySumExprUnionMember5ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember5ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember5ExprUnionMember2Expr: TypeAlias = Union[
    RankBySumExprUnionMember5ExprUnionMember2ExprUnionMember0, RankBySumExprUnionMember5ExprUnionMember2ExprUnionMember1
]


class RankBySumExprUnionMember5ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember5ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankBySumExprUnionMember5ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankBySumExprUnionMember5ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankBySumExprUnionMember5ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember5ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember5ExprUnionMember5Expr: TypeAlias = Union[
    RankBySumExprUnionMember5ExprUnionMember5ExprUnionMember0, RankBySumExprUnionMember5ExprUnionMember5ExprUnionMember1
]


class RankBySumExprUnionMember5ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember5ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankBySumExprUnionMember5ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember5ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember5ExprUnionMember6Expr: TypeAlias = Union[
    RankBySumExprUnionMember5ExprUnionMember6ExprUnionMember0, RankBySumExprUnionMember5ExprUnionMember6ExprUnionMember1
]


class RankBySumExprUnionMember5ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember5ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankBySumExprUnionMember5ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember5ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember5ExprUnionMember7Expr: TypeAlias = Union[
    RankBySumExprUnionMember5ExprUnionMember7ExprUnionMember0, RankBySumExprUnionMember5ExprUnionMember7ExprUnionMember1
]


class RankBySumExprUnionMember5ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankBySumExprUnionMember5ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankBySumExprUnionMember5Expr: TypeAlias = Union[
    RankBySumExprUnionMember5ExprUnionMember0,
    RankBySumExprUnionMember5ExprUnionMember1,
    RankBySumExprUnionMember5ExprUnionMember2,
    RankBySumExprUnionMember5ExprUnionMember3,
    RankBySumExprUnionMember5ExprUnionMember4,
    RankBySumExprUnionMember5ExprUnionMember5,
    RankBySumExprUnionMember5ExprUnionMember6,
    RankBySumExprUnionMember5ExprUnionMember7,
]


class RankBySumExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankBySumExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankBySumExprUnionMember6ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember6ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember6ExprUnionMember2Expr: TypeAlias = Union[
    RankBySumExprUnionMember6ExprUnionMember2ExprUnionMember0, RankBySumExprUnionMember6ExprUnionMember2ExprUnionMember1
]


class RankBySumExprUnionMember6ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember6ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankBySumExprUnionMember6ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankBySumExprUnionMember6ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankBySumExprUnionMember6ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember6ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember6ExprUnionMember5Expr: TypeAlias = Union[
    RankBySumExprUnionMember6ExprUnionMember5ExprUnionMember0, RankBySumExprUnionMember6ExprUnionMember5ExprUnionMember1
]


class RankBySumExprUnionMember6ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember6ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankBySumExprUnionMember6ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember6ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember6ExprUnionMember6Expr: TypeAlias = Union[
    RankBySumExprUnionMember6ExprUnionMember6ExprUnionMember0, RankBySumExprUnionMember6ExprUnionMember6ExprUnionMember1
]


class RankBySumExprUnionMember6ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember6ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankBySumExprUnionMember6ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember6ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember6ExprUnionMember7Expr: TypeAlias = Union[
    RankBySumExprUnionMember6ExprUnionMember7ExprUnionMember0, RankBySumExprUnionMember6ExprUnionMember7ExprUnionMember1
]


class RankBySumExprUnionMember6ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankBySumExprUnionMember6ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankBySumExprUnionMember6Expr: TypeAlias = Union[
    RankBySumExprUnionMember6ExprUnionMember0,
    RankBySumExprUnionMember6ExprUnionMember1,
    RankBySumExprUnionMember6ExprUnionMember2,
    RankBySumExprUnionMember6ExprUnionMember3,
    RankBySumExprUnionMember6ExprUnionMember4,
    RankBySumExprUnionMember6ExprUnionMember5,
    RankBySumExprUnionMember6ExprUnionMember6,
    RankBySumExprUnionMember6ExprUnionMember7,
]


class RankBySumExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankBySumExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankBySumExprUnionMember7ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember7ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember7ExprUnionMember2Expr: TypeAlias = Union[
    RankBySumExprUnionMember7ExprUnionMember2ExprUnionMember0, RankBySumExprUnionMember7ExprUnionMember2ExprUnionMember1
]


class RankBySumExprUnionMember7ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember7ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankBySumExprUnionMember7ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankBySumExprUnionMember7ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankBySumExprUnionMember7ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember7ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember7ExprUnionMember5Expr: TypeAlias = Union[
    RankBySumExprUnionMember7ExprUnionMember5ExprUnionMember0, RankBySumExprUnionMember7ExprUnionMember5ExprUnionMember1
]


class RankBySumExprUnionMember7ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember7ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankBySumExprUnionMember7ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember7ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember7ExprUnionMember6Expr: TypeAlias = Union[
    RankBySumExprUnionMember7ExprUnionMember6ExprUnionMember0, RankBySumExprUnionMember7ExprUnionMember6ExprUnionMember1
]


class RankBySumExprUnionMember7ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExprUnionMember7ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankBySumExprUnionMember7ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankBySumExprUnionMember7ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankBySumExprUnionMember7ExprUnionMember7Expr: TypeAlias = Union[
    RankBySumExprUnionMember7ExprUnionMember7ExprUnionMember0, RankBySumExprUnionMember7ExprUnionMember7ExprUnionMember1
]


class RankBySumExprUnionMember7ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankBySumExprUnionMember7ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankBySumExprUnionMember7Expr: TypeAlias = Union[
    RankBySumExprUnionMember7ExprUnionMember0,
    RankBySumExprUnionMember7ExprUnionMember1,
    RankBySumExprUnionMember7ExprUnionMember2,
    RankBySumExprUnionMember7ExprUnionMember3,
    RankBySumExprUnionMember7ExprUnionMember4,
    RankBySumExprUnionMember7ExprUnionMember5,
    RankBySumExprUnionMember7ExprUnionMember6,
    RankBySumExprUnionMember7ExprUnionMember7,
]


class RankBySumExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankBySumExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankBySumExpr: TypeAlias = Union[
    RankBySumExprUnionMember0,
    RankBySumExprUnionMember1,
    RankBySumExprUnionMember2,
    RankBySumExprUnionMember3,
    RankBySumExprUnionMember4,
    RankBySumExprUnionMember5,
    RankBySumExprUnionMember6,
    RankBySumExprUnionMember7,
]


class RankBySum(TypedDict, total=False):
    exprs: Required[Iterable[RankBySumExpr]]

    type: Required[Literal["Sum"]]


class RankByMult(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByDiv(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMaxExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMaxExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMaxExprUnionMember2ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember2ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember2ExprUnionMember2Expr: TypeAlias = Union[
    RankByMaxExprUnionMember2ExprUnionMember2ExprUnionMember0, RankByMaxExprUnionMember2ExprUnionMember2ExprUnionMember1
]


class RankByMaxExprUnionMember2ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember2ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMaxExprUnionMember2ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMaxExprUnionMember2ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMaxExprUnionMember2ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember2ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember2ExprUnionMember5Expr: TypeAlias = Union[
    RankByMaxExprUnionMember2ExprUnionMember5ExprUnionMember0, RankByMaxExprUnionMember2ExprUnionMember5ExprUnionMember1
]


class RankByMaxExprUnionMember2ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember2ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMaxExprUnionMember2ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember2ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember2ExprUnionMember6Expr: TypeAlias = Union[
    RankByMaxExprUnionMember2ExprUnionMember6ExprUnionMember0, RankByMaxExprUnionMember2ExprUnionMember6ExprUnionMember1
]


class RankByMaxExprUnionMember2ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember2ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMaxExprUnionMember2ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember2ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember2ExprUnionMember7Expr: TypeAlias = Union[
    RankByMaxExprUnionMember2ExprUnionMember7ExprUnionMember0, RankByMaxExprUnionMember2ExprUnionMember7ExprUnionMember1
]


class RankByMaxExprUnionMember2ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMaxExprUnionMember2ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMaxExprUnionMember2Expr: TypeAlias = Union[
    RankByMaxExprUnionMember2ExprUnionMember0,
    RankByMaxExprUnionMember2ExprUnionMember1,
    RankByMaxExprUnionMember2ExprUnionMember2,
    RankByMaxExprUnionMember2ExprUnionMember3,
    RankByMaxExprUnionMember2ExprUnionMember4,
    RankByMaxExprUnionMember2ExprUnionMember5,
    RankByMaxExprUnionMember2ExprUnionMember6,
    RankByMaxExprUnionMember2ExprUnionMember7,
]


class RankByMaxExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMaxExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMaxExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMaxExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMaxExprUnionMember5ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember5ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember5ExprUnionMember2Expr: TypeAlias = Union[
    RankByMaxExprUnionMember5ExprUnionMember2ExprUnionMember0, RankByMaxExprUnionMember5ExprUnionMember2ExprUnionMember1
]


class RankByMaxExprUnionMember5ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember5ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMaxExprUnionMember5ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMaxExprUnionMember5ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMaxExprUnionMember5ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember5ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember5ExprUnionMember5Expr: TypeAlias = Union[
    RankByMaxExprUnionMember5ExprUnionMember5ExprUnionMember0, RankByMaxExprUnionMember5ExprUnionMember5ExprUnionMember1
]


class RankByMaxExprUnionMember5ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember5ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMaxExprUnionMember5ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember5ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember5ExprUnionMember6Expr: TypeAlias = Union[
    RankByMaxExprUnionMember5ExprUnionMember6ExprUnionMember0, RankByMaxExprUnionMember5ExprUnionMember6ExprUnionMember1
]


class RankByMaxExprUnionMember5ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember5ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMaxExprUnionMember5ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember5ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember5ExprUnionMember7Expr: TypeAlias = Union[
    RankByMaxExprUnionMember5ExprUnionMember7ExprUnionMember0, RankByMaxExprUnionMember5ExprUnionMember7ExprUnionMember1
]


class RankByMaxExprUnionMember5ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMaxExprUnionMember5ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMaxExprUnionMember5Expr: TypeAlias = Union[
    RankByMaxExprUnionMember5ExprUnionMember0,
    RankByMaxExprUnionMember5ExprUnionMember1,
    RankByMaxExprUnionMember5ExprUnionMember2,
    RankByMaxExprUnionMember5ExprUnionMember3,
    RankByMaxExprUnionMember5ExprUnionMember4,
    RankByMaxExprUnionMember5ExprUnionMember5,
    RankByMaxExprUnionMember5ExprUnionMember6,
    RankByMaxExprUnionMember5ExprUnionMember7,
]


class RankByMaxExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMaxExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMaxExprUnionMember6ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember6ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember6ExprUnionMember2Expr: TypeAlias = Union[
    RankByMaxExprUnionMember6ExprUnionMember2ExprUnionMember0, RankByMaxExprUnionMember6ExprUnionMember2ExprUnionMember1
]


class RankByMaxExprUnionMember6ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember6ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMaxExprUnionMember6ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMaxExprUnionMember6ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMaxExprUnionMember6ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember6ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember6ExprUnionMember5Expr: TypeAlias = Union[
    RankByMaxExprUnionMember6ExprUnionMember5ExprUnionMember0, RankByMaxExprUnionMember6ExprUnionMember5ExprUnionMember1
]


class RankByMaxExprUnionMember6ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember6ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMaxExprUnionMember6ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember6ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember6ExprUnionMember6Expr: TypeAlias = Union[
    RankByMaxExprUnionMember6ExprUnionMember6ExprUnionMember0, RankByMaxExprUnionMember6ExprUnionMember6ExprUnionMember1
]


class RankByMaxExprUnionMember6ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember6ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMaxExprUnionMember6ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember6ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember6ExprUnionMember7Expr: TypeAlias = Union[
    RankByMaxExprUnionMember6ExprUnionMember7ExprUnionMember0, RankByMaxExprUnionMember6ExprUnionMember7ExprUnionMember1
]


class RankByMaxExprUnionMember6ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMaxExprUnionMember6ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMaxExprUnionMember6Expr: TypeAlias = Union[
    RankByMaxExprUnionMember6ExprUnionMember0,
    RankByMaxExprUnionMember6ExprUnionMember1,
    RankByMaxExprUnionMember6ExprUnionMember2,
    RankByMaxExprUnionMember6ExprUnionMember3,
    RankByMaxExprUnionMember6ExprUnionMember4,
    RankByMaxExprUnionMember6ExprUnionMember5,
    RankByMaxExprUnionMember6ExprUnionMember6,
    RankByMaxExprUnionMember6ExprUnionMember7,
]


class RankByMaxExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMaxExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMaxExprUnionMember7ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember7ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember7ExprUnionMember2Expr: TypeAlias = Union[
    RankByMaxExprUnionMember7ExprUnionMember2ExprUnionMember0, RankByMaxExprUnionMember7ExprUnionMember2ExprUnionMember1
]


class RankByMaxExprUnionMember7ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember7ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMaxExprUnionMember7ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMaxExprUnionMember7ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMaxExprUnionMember7ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember7ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember7ExprUnionMember5Expr: TypeAlias = Union[
    RankByMaxExprUnionMember7ExprUnionMember5ExprUnionMember0, RankByMaxExprUnionMember7ExprUnionMember5ExprUnionMember1
]


class RankByMaxExprUnionMember7ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember7ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMaxExprUnionMember7ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember7ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember7ExprUnionMember6Expr: TypeAlias = Union[
    RankByMaxExprUnionMember7ExprUnionMember6ExprUnionMember0, RankByMaxExprUnionMember7ExprUnionMember6ExprUnionMember1
]


class RankByMaxExprUnionMember7ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExprUnionMember7ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMaxExprUnionMember7ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMaxExprUnionMember7ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMaxExprUnionMember7ExprUnionMember7Expr: TypeAlias = Union[
    RankByMaxExprUnionMember7ExprUnionMember7ExprUnionMember0, RankByMaxExprUnionMember7ExprUnionMember7ExprUnionMember1
]


class RankByMaxExprUnionMember7ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMaxExprUnionMember7ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMaxExprUnionMember7Expr: TypeAlias = Union[
    RankByMaxExprUnionMember7ExprUnionMember0,
    RankByMaxExprUnionMember7ExprUnionMember1,
    RankByMaxExprUnionMember7ExprUnionMember2,
    RankByMaxExprUnionMember7ExprUnionMember3,
    RankByMaxExprUnionMember7ExprUnionMember4,
    RankByMaxExprUnionMember7ExprUnionMember5,
    RankByMaxExprUnionMember7ExprUnionMember6,
    RankByMaxExprUnionMember7ExprUnionMember7,
]


class RankByMaxExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMaxExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMaxExpr: TypeAlias = Union[
    RankByMaxExprUnionMember0,
    RankByMaxExprUnionMember1,
    RankByMaxExprUnionMember2,
    RankByMaxExprUnionMember3,
    RankByMaxExprUnionMember4,
    RankByMaxExprUnionMember5,
    RankByMaxExprUnionMember6,
    RankByMaxExprUnionMember7,
]


class RankByMax(TypedDict, total=False):
    exprs: Required[Iterable[RankByMaxExpr]]

    type: Required[Literal["Max"]]


class RankByMinExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMinExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMinExprUnionMember2ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember2ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember2ExprUnionMember2Expr: TypeAlias = Union[
    RankByMinExprUnionMember2ExprUnionMember2ExprUnionMember0, RankByMinExprUnionMember2ExprUnionMember2ExprUnionMember1
]


class RankByMinExprUnionMember2ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember2ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMinExprUnionMember2ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMinExprUnionMember2ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMinExprUnionMember2ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember2ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember2ExprUnionMember5Expr: TypeAlias = Union[
    RankByMinExprUnionMember2ExprUnionMember5ExprUnionMember0, RankByMinExprUnionMember2ExprUnionMember5ExprUnionMember1
]


class RankByMinExprUnionMember2ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember2ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMinExprUnionMember2ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember2ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember2ExprUnionMember6Expr: TypeAlias = Union[
    RankByMinExprUnionMember2ExprUnionMember6ExprUnionMember0, RankByMinExprUnionMember2ExprUnionMember6ExprUnionMember1
]


class RankByMinExprUnionMember2ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember2ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMinExprUnionMember2ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember2ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember2ExprUnionMember7Expr: TypeAlias = Union[
    RankByMinExprUnionMember2ExprUnionMember7ExprUnionMember0, RankByMinExprUnionMember2ExprUnionMember7ExprUnionMember1
]


class RankByMinExprUnionMember2ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMinExprUnionMember2ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMinExprUnionMember2Expr: TypeAlias = Union[
    RankByMinExprUnionMember2ExprUnionMember0,
    RankByMinExprUnionMember2ExprUnionMember1,
    RankByMinExprUnionMember2ExprUnionMember2,
    RankByMinExprUnionMember2ExprUnionMember3,
    RankByMinExprUnionMember2ExprUnionMember4,
    RankByMinExprUnionMember2ExprUnionMember5,
    RankByMinExprUnionMember2ExprUnionMember6,
    RankByMinExprUnionMember2ExprUnionMember7,
]


class RankByMinExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMinExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMinExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMinExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMinExprUnionMember5ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember5ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember5ExprUnionMember2Expr: TypeAlias = Union[
    RankByMinExprUnionMember5ExprUnionMember2ExprUnionMember0, RankByMinExprUnionMember5ExprUnionMember2ExprUnionMember1
]


class RankByMinExprUnionMember5ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember5ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMinExprUnionMember5ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMinExprUnionMember5ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMinExprUnionMember5ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember5ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember5ExprUnionMember5Expr: TypeAlias = Union[
    RankByMinExprUnionMember5ExprUnionMember5ExprUnionMember0, RankByMinExprUnionMember5ExprUnionMember5ExprUnionMember1
]


class RankByMinExprUnionMember5ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember5ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMinExprUnionMember5ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember5ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember5ExprUnionMember6Expr: TypeAlias = Union[
    RankByMinExprUnionMember5ExprUnionMember6ExprUnionMember0, RankByMinExprUnionMember5ExprUnionMember6ExprUnionMember1
]


class RankByMinExprUnionMember5ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember5ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMinExprUnionMember5ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember5ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember5ExprUnionMember7Expr: TypeAlias = Union[
    RankByMinExprUnionMember5ExprUnionMember7ExprUnionMember0, RankByMinExprUnionMember5ExprUnionMember7ExprUnionMember1
]


class RankByMinExprUnionMember5ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMinExprUnionMember5ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMinExprUnionMember5Expr: TypeAlias = Union[
    RankByMinExprUnionMember5ExprUnionMember0,
    RankByMinExprUnionMember5ExprUnionMember1,
    RankByMinExprUnionMember5ExprUnionMember2,
    RankByMinExprUnionMember5ExprUnionMember3,
    RankByMinExprUnionMember5ExprUnionMember4,
    RankByMinExprUnionMember5ExprUnionMember5,
    RankByMinExprUnionMember5ExprUnionMember6,
    RankByMinExprUnionMember5ExprUnionMember7,
]


class RankByMinExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMinExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMinExprUnionMember6ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember6ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember6ExprUnionMember2Expr: TypeAlias = Union[
    RankByMinExprUnionMember6ExprUnionMember2ExprUnionMember0, RankByMinExprUnionMember6ExprUnionMember2ExprUnionMember1
]


class RankByMinExprUnionMember6ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember6ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMinExprUnionMember6ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMinExprUnionMember6ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMinExprUnionMember6ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember6ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember6ExprUnionMember5Expr: TypeAlias = Union[
    RankByMinExprUnionMember6ExprUnionMember5ExprUnionMember0, RankByMinExprUnionMember6ExprUnionMember5ExprUnionMember1
]


class RankByMinExprUnionMember6ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember6ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMinExprUnionMember6ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember6ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember6ExprUnionMember6Expr: TypeAlias = Union[
    RankByMinExprUnionMember6ExprUnionMember6ExprUnionMember0, RankByMinExprUnionMember6ExprUnionMember6ExprUnionMember1
]


class RankByMinExprUnionMember6ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember6ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMinExprUnionMember6ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember6ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember6ExprUnionMember7Expr: TypeAlias = Union[
    RankByMinExprUnionMember6ExprUnionMember7ExprUnionMember0, RankByMinExprUnionMember6ExprUnionMember7ExprUnionMember1
]


class RankByMinExprUnionMember6ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMinExprUnionMember6ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMinExprUnionMember6Expr: TypeAlias = Union[
    RankByMinExprUnionMember6ExprUnionMember0,
    RankByMinExprUnionMember6ExprUnionMember1,
    RankByMinExprUnionMember6ExprUnionMember2,
    RankByMinExprUnionMember6ExprUnionMember3,
    RankByMinExprUnionMember6ExprUnionMember4,
    RankByMinExprUnionMember6ExprUnionMember5,
    RankByMinExprUnionMember6ExprUnionMember6,
    RankByMinExprUnionMember6ExprUnionMember7,
]


class RankByMinExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMinExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByMinExprUnionMember7ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember7ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember7ExprUnionMember2Expr: TypeAlias = Union[
    RankByMinExprUnionMember7ExprUnionMember2ExprUnionMember0, RankByMinExprUnionMember7ExprUnionMember2ExprUnionMember1
]


class RankByMinExprUnionMember7ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember7ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByMinExprUnionMember7ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByMinExprUnionMember7ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByMinExprUnionMember7ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember7ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember7ExprUnionMember5Expr: TypeAlias = Union[
    RankByMinExprUnionMember7ExprUnionMember5ExprUnionMember0, RankByMinExprUnionMember7ExprUnionMember5ExprUnionMember1
]


class RankByMinExprUnionMember7ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember7ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByMinExprUnionMember7ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember7ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember7ExprUnionMember6Expr: TypeAlias = Union[
    RankByMinExprUnionMember7ExprUnionMember6ExprUnionMember0, RankByMinExprUnionMember7ExprUnionMember6ExprUnionMember1
]


class RankByMinExprUnionMember7ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExprUnionMember7ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByMinExprUnionMember7ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByMinExprUnionMember7ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByMinExprUnionMember7ExprUnionMember7Expr: TypeAlias = Union[
    RankByMinExprUnionMember7ExprUnionMember7ExprUnionMember0, RankByMinExprUnionMember7ExprUnionMember7ExprUnionMember1
]


class RankByMinExprUnionMember7ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMinExprUnionMember7ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMinExprUnionMember7Expr: TypeAlias = Union[
    RankByMinExprUnionMember7ExprUnionMember0,
    RankByMinExprUnionMember7ExprUnionMember1,
    RankByMinExprUnionMember7ExprUnionMember2,
    RankByMinExprUnionMember7ExprUnionMember3,
    RankByMinExprUnionMember7ExprUnionMember4,
    RankByMinExprUnionMember7ExprUnionMember5,
    RankByMinExprUnionMember7ExprUnionMember6,
    RankByMinExprUnionMember7ExprUnionMember7,
]


class RankByMinExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByMinExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByMinExpr: TypeAlias = Union[
    RankByMinExprUnionMember0,
    RankByMinExprUnionMember1,
    RankByMinExprUnionMember2,
    RankByMinExprUnionMember3,
    RankByMinExprUnionMember4,
    RankByMinExprUnionMember5,
    RankByMinExprUnionMember6,
    RankByMinExprUnionMember7,
]


class RankByMin(TypedDict, total=False):
    exprs: Required[Iterable[RankByMinExpr]]

    type: Required[Literal["Min"]]


class RankByLogExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByLogExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByLogExprUnionMember2ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember2ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember2ExprUnionMember2Expr: TypeAlias = Union[
    RankByLogExprUnionMember2ExprUnionMember2ExprUnionMember0, RankByLogExprUnionMember2ExprUnionMember2ExprUnionMember1
]


class RankByLogExprUnionMember2ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember2ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByLogExprUnionMember2ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByLogExprUnionMember2ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByLogExprUnionMember2ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember2ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember2ExprUnionMember5Expr: TypeAlias = Union[
    RankByLogExprUnionMember2ExprUnionMember5ExprUnionMember0, RankByLogExprUnionMember2ExprUnionMember5ExprUnionMember1
]


class RankByLogExprUnionMember2ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember2ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByLogExprUnionMember2ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember2ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember2ExprUnionMember6Expr: TypeAlias = Union[
    RankByLogExprUnionMember2ExprUnionMember6ExprUnionMember0, RankByLogExprUnionMember2ExprUnionMember6ExprUnionMember1
]


class RankByLogExprUnionMember2ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember2ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByLogExprUnionMember2ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember2ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember2ExprUnionMember7Expr: TypeAlias = Union[
    RankByLogExprUnionMember2ExprUnionMember7ExprUnionMember0, RankByLogExprUnionMember2ExprUnionMember7ExprUnionMember1
]


class RankByLogExprUnionMember2ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByLogExprUnionMember2ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByLogExprUnionMember2Expr: TypeAlias = Union[
    RankByLogExprUnionMember2ExprUnionMember0,
    RankByLogExprUnionMember2ExprUnionMember1,
    RankByLogExprUnionMember2ExprUnionMember2,
    RankByLogExprUnionMember2ExprUnionMember3,
    RankByLogExprUnionMember2ExprUnionMember4,
    RankByLogExprUnionMember2ExprUnionMember5,
    RankByLogExprUnionMember2ExprUnionMember6,
    RankByLogExprUnionMember2ExprUnionMember7,
]


class RankByLogExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByLogExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByLogExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByLogExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByLogExprUnionMember5ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember5ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember5ExprUnionMember2Expr: TypeAlias = Union[
    RankByLogExprUnionMember5ExprUnionMember2ExprUnionMember0, RankByLogExprUnionMember5ExprUnionMember2ExprUnionMember1
]


class RankByLogExprUnionMember5ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember5ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByLogExprUnionMember5ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByLogExprUnionMember5ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByLogExprUnionMember5ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember5ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember5ExprUnionMember5Expr: TypeAlias = Union[
    RankByLogExprUnionMember5ExprUnionMember5ExprUnionMember0, RankByLogExprUnionMember5ExprUnionMember5ExprUnionMember1
]


class RankByLogExprUnionMember5ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember5ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByLogExprUnionMember5ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember5ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember5ExprUnionMember6Expr: TypeAlias = Union[
    RankByLogExprUnionMember5ExprUnionMember6ExprUnionMember0, RankByLogExprUnionMember5ExprUnionMember6ExprUnionMember1
]


class RankByLogExprUnionMember5ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember5ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByLogExprUnionMember5ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember5ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember5ExprUnionMember7Expr: TypeAlias = Union[
    RankByLogExprUnionMember5ExprUnionMember7ExprUnionMember0, RankByLogExprUnionMember5ExprUnionMember7ExprUnionMember1
]


class RankByLogExprUnionMember5ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByLogExprUnionMember5ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByLogExprUnionMember5Expr: TypeAlias = Union[
    RankByLogExprUnionMember5ExprUnionMember0,
    RankByLogExprUnionMember5ExprUnionMember1,
    RankByLogExprUnionMember5ExprUnionMember2,
    RankByLogExprUnionMember5ExprUnionMember3,
    RankByLogExprUnionMember5ExprUnionMember4,
    RankByLogExprUnionMember5ExprUnionMember5,
    RankByLogExprUnionMember5ExprUnionMember6,
    RankByLogExprUnionMember5ExprUnionMember7,
]


class RankByLogExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByLogExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByLogExprUnionMember6ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember6ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember6ExprUnionMember2Expr: TypeAlias = Union[
    RankByLogExprUnionMember6ExprUnionMember2ExprUnionMember0, RankByLogExprUnionMember6ExprUnionMember2ExprUnionMember1
]


class RankByLogExprUnionMember6ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember6ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByLogExprUnionMember6ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByLogExprUnionMember6ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByLogExprUnionMember6ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember6ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember6ExprUnionMember5Expr: TypeAlias = Union[
    RankByLogExprUnionMember6ExprUnionMember5ExprUnionMember0, RankByLogExprUnionMember6ExprUnionMember5ExprUnionMember1
]


class RankByLogExprUnionMember6ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember6ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByLogExprUnionMember6ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember6ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember6ExprUnionMember6Expr: TypeAlias = Union[
    RankByLogExprUnionMember6ExprUnionMember6ExprUnionMember0, RankByLogExprUnionMember6ExprUnionMember6ExprUnionMember1
]


class RankByLogExprUnionMember6ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember6ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByLogExprUnionMember6ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember6ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember6ExprUnionMember7Expr: TypeAlias = Union[
    RankByLogExprUnionMember6ExprUnionMember7ExprUnionMember0, RankByLogExprUnionMember6ExprUnionMember7ExprUnionMember1
]


class RankByLogExprUnionMember6ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByLogExprUnionMember6ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByLogExprUnionMember6Expr: TypeAlias = Union[
    RankByLogExprUnionMember6ExprUnionMember0,
    RankByLogExprUnionMember6ExprUnionMember1,
    RankByLogExprUnionMember6ExprUnionMember2,
    RankByLogExprUnionMember6ExprUnionMember3,
    RankByLogExprUnionMember6ExprUnionMember4,
    RankByLogExprUnionMember6ExprUnionMember5,
    RankByLogExprUnionMember6ExprUnionMember6,
    RankByLogExprUnionMember6ExprUnionMember7,
]


class RankByLogExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByLogExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


class RankByLogExprUnionMember7ExprUnionMember2ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember7ExprUnionMember2ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember7ExprUnionMember2Expr: TypeAlias = Union[
    RankByLogExprUnionMember7ExprUnionMember2ExprUnionMember0, RankByLogExprUnionMember7ExprUnionMember2ExprUnionMember1
]


class RankByLogExprUnionMember7ExprUnionMember2(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember7ExprUnionMember2Expr]]

    type: Required[Literal["Sum"]]


class RankByLogExprUnionMember7ExprUnionMember3(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Mult"]]


class RankByLogExprUnionMember7ExprUnionMember4(TypedDict, total=False):
    exprs: Required[Iterable[object]]

    type: Required[Literal["Div"]]


class RankByLogExprUnionMember7ExprUnionMember5ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember7ExprUnionMember5ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember7ExprUnionMember5Expr: TypeAlias = Union[
    RankByLogExprUnionMember7ExprUnionMember5ExprUnionMember0, RankByLogExprUnionMember7ExprUnionMember5ExprUnionMember1
]


class RankByLogExprUnionMember7ExprUnionMember5(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember7ExprUnionMember5Expr]]

    type: Required[Literal["Max"]]


class RankByLogExprUnionMember7ExprUnionMember6ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember7ExprUnionMember6ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember7ExprUnionMember6Expr: TypeAlias = Union[
    RankByLogExprUnionMember7ExprUnionMember6ExprUnionMember0, RankByLogExprUnionMember7ExprUnionMember6ExprUnionMember1
]


class RankByLogExprUnionMember7ExprUnionMember6(TypedDict, total=False):
    exprs: Required[Iterable[RankByLogExprUnionMember7ExprUnionMember6Expr]]

    type: Required[Literal["Min"]]


class RankByLogExprUnionMember7ExprUnionMember7ExprUnionMember0(TypedDict, total=False):
    name: Required[Literal["ann", "stars", "issues_closed", "age", "recency"]]

    type: Required[Literal["Attr"]]


class RankByLogExprUnionMember7ExprUnionMember7ExprUnionMember1(TypedDict, total=False):
    type: Required[Literal["Const"]]

    value: Required[float]


RankByLogExprUnionMember7ExprUnionMember7Expr: TypeAlias = Union[
    RankByLogExprUnionMember7ExprUnionMember7ExprUnionMember0, RankByLogExprUnionMember7ExprUnionMember7ExprUnionMember1
]


class RankByLogExprUnionMember7ExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByLogExprUnionMember7ExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByLogExprUnionMember7Expr: TypeAlias = Union[
    RankByLogExprUnionMember7ExprUnionMember0,
    RankByLogExprUnionMember7ExprUnionMember1,
    RankByLogExprUnionMember7ExprUnionMember2,
    RankByLogExprUnionMember7ExprUnionMember3,
    RankByLogExprUnionMember7ExprUnionMember4,
    RankByLogExprUnionMember7ExprUnionMember5,
    RankByLogExprUnionMember7ExprUnionMember6,
    RankByLogExprUnionMember7ExprUnionMember7,
]


class RankByLogExprUnionMember7(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByLogExprUnionMember7Expr]

    type: Required[Literal["Log"]]


RankByLogExpr: TypeAlias = Union[
    RankByLogExprUnionMember0,
    RankByLogExprUnionMember1,
    RankByLogExprUnionMember2,
    RankByLogExprUnionMember3,
    RankByLogExprUnionMember4,
    RankByLogExprUnionMember5,
    RankByLogExprUnionMember6,
    RankByLogExprUnionMember7,
]


class RankByLog(TypedDict, total=False):
    base: Required[float]

    expr: Required[RankByLogExpr]

    type: Required[Literal["Log"]]


RankBy: TypeAlias = Union[RankByAttr, RankByConst, RankBySum, RankByMult, RankByDiv, RankByMax, RankByMin, RankByLog]
