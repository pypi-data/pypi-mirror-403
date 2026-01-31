# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "SearchRepoNaturalLanguageResponse",
    "Repository",
    "RepositoryContributors",
    "RepositoryContributorsEdge",
    "RepositoryContributorsEdgeSocialAccount",
    "RepositoryContributorsPageInfo",
    "RepositoryOwner",
    "RepositoryOwnerSocialAccount",
    "RepositoryOwnerDevrank",
    "RepositoryOwnerProfessional",
    "RepositoryOwnerProfessionalEducation",
    "RepositoryOwnerProfessionalExperience",
    "RepositoryStarrers",
    "RepositoryStarrersEdge",
    "RepositoryStarrersEdgeSocialAccount",
    "RepositoryStarrersPageInfo",
    "PageInfo",
]


class RepositoryContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class RepositoryContributorsEdge(BaseModel):
    id: str
    """BountyLab internal ID"""

    github_id: str = FieldInfo(alias="githubId")
    """GitHub node ID"""

    login: str
    """GitHub username"""

    bio: Optional[str] = None
    """User biography"""

    company: Optional[str] = None
    """Company name"""

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)
    """ISO 8601 timestamp when user account was created"""

    display_name: Optional[str] = FieldInfo(alias="displayName", default=None)
    """User display name"""

    emails: Optional[List[str]] = None
    """
    Obfuscated email addresses showing only the last 2 characters of the local part
    and full domain (e.g., "\\**\\**\\**oe@gmail.com"). Use /api/users/best-email endpoint
    for unobfuscated email access with intelligent selection.
    """

    embedded_at: Optional[str] = FieldInfo(alias="embeddedAt", default=None)
    """ISO 8601 timestamp when metadata was extracted"""

    location: Optional[str] = None
    """User location"""

    resolved_city: Optional[str] = FieldInfo(alias="resolvedCity", default=None)
    """Resolved city from location"""

    resolved_country: Optional[str] = FieldInfo(alias="resolvedCountry", default=None)
    """Resolved country from location"""

    resolved_state: Optional[str] = FieldInfo(alias="resolvedState", default=None)
    """Resolved state/region from location"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for distance metrics)"""

    social_accounts: Optional[List[RepositoryContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class RepositoryContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class RepositoryContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[RepositoryContributorsEdge]
    """Array of user objects"""

    page_info: RepositoryContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class RepositoryOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class RepositoryOwner(BaseModel):
    """Repository owner (when includeAttributes.owner = true)"""

    id: str
    """BountyLab internal ID"""

    github_id: str = FieldInfo(alias="githubId")
    """GitHub node ID"""

    login: str
    """GitHub username"""

    bio: Optional[str] = None
    """User biography"""

    company: Optional[str] = None
    """Company name"""

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)
    """ISO 8601 timestamp when user account was created"""

    display_name: Optional[str] = FieldInfo(alias="displayName", default=None)
    """User display name"""

    emails: Optional[List[str]] = None
    """
    Obfuscated email addresses showing only the last 2 characters of the local part
    and full domain (e.g., "\\**\\**\\**oe@gmail.com"). Use /api/users/best-email endpoint
    for unobfuscated email access with intelligent selection.
    """

    embedded_at: Optional[str] = FieldInfo(alias="embeddedAt", default=None)
    """ISO 8601 timestamp when metadata was extracted"""

    location: Optional[str] = None
    """User location"""

    resolved_city: Optional[str] = FieldInfo(alias="resolvedCity", default=None)
    """Resolved city from location"""

    resolved_country: Optional[str] = FieldInfo(alias="resolvedCountry", default=None)
    """Resolved country from location"""

    resolved_state: Optional[str] = FieldInfo(alias="resolvedState", default=None)
    """Resolved state/region from location"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for distance metrics)"""

    social_accounts: Optional[List[RepositoryOwnerSocialAccount]] = FieldInfo(alias="socialAccounts", default=None)
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class RepositoryOwnerDevrank(BaseModel):
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank = true)
    """

    community: int

    cracked_score: float = FieldInfo(alias="crackedScore")

    created_at: str = FieldInfo(alias="createdAt")

    followers_in: float = FieldInfo(alias="followersIn")

    following_out: float = FieldInfo(alias="followingOut")

    pc: float

    raw_score: float = FieldInfo(alias="rawScore")

    tier: str

    trust: float

    updated_at: str = FieldInfo(alias="updatedAt")


class RepositoryOwnerProfessionalEducation(BaseModel):
    campus: Optional[str] = None
    """Name of the educational institution"""

    end_date: Optional[str] = FieldInfo(alias="endDate", default=None)
    """End date (YYYY-MM-DD format)"""

    major: Optional[str] = None
    """Field of study or degree program"""

    specialization: Optional[str] = None
    """Area of specialization"""

    start_date: Optional[str] = FieldInfo(alias="startDate", default=None)
    """Start date (YYYY-MM-DD format)"""


class RepositoryOwnerProfessionalExperience(BaseModel):
    company: Optional[str] = None
    """Company or organization name"""

    end_date: Optional[str] = FieldInfo(alias="endDate", default=None)
    """End date (YYYY-MM-DD format, null if current)"""

    industry: Optional[str] = None
    """Industry sector"""

    is_current: Optional[bool] = FieldInfo(alias="isCurrent", default=None)
    """Whether this is the current position"""

    location: Optional[str] = None
    """Work location"""

    start_date: Optional[str] = FieldInfo(alias="startDate", default=None)
    """Start date (YYYY-MM-DD format)"""

    summary: Optional[str] = None
    """Description of role and responsibilities"""

    title: Optional[str] = None
    """Job title or position"""


class RepositoryOwnerProfessional(BaseModel):
    """
    LinkedIn professional profile data (only present when includeAttributes.professional = true)
    """

    awards: Optional[List[str]] = None
    """Professional awards"""

    certifications: Optional[List[str]] = None
    """Professional certifications"""

    city: Optional[str] = None
    """City"""

    connections_count: Optional[float] = FieldInfo(alias="connectionsCount", default=None)
    """Number of LinkedIn connections"""

    country: Optional[str] = None
    """Country"""

    current_industry: Optional[str] = FieldInfo(alias="currentIndustry", default=None)
    """Current industry sector"""

    departments: Optional[List[str]] = None
    """Departments worked in"""

    education: List[RepositoryOwnerProfessionalEducation]
    """Education history"""

    experience: List[RepositoryOwnerProfessionalExperience]
    """Work experience history"""

    expertise: Optional[List[str]] = None
    """Areas of expertise"""

    first_name: Optional[str] = FieldInfo(alias="firstName", default=None)
    """First name"""

    follower_count: Optional[float] = FieldInfo(alias="followerCount", default=None)
    """Number of LinkedIn followers"""

    functional_area: Optional[str] = FieldInfo(alias="functionalArea", default=None)
    """Functional area (e.g., Engineering, Product)"""

    headline: Optional[str] = None
    """Professional headline"""

    languages: Optional[List[str]] = None
    """Languages spoken"""

    last_name: Optional[str] = FieldInfo(alias="lastName", default=None)
    """Last name"""

    linkedin_url: str = FieldInfo(alias="linkedinUrl")
    """LinkedIn profile URL"""

    location: Optional[str] = None
    """Full location string"""

    memberships: Optional[List[str]] = None
    """Professional organization memberships"""

    organization: Optional[str] = None
    """Current organization/company"""

    patents: Optional[List[str]] = None
    """Patents held"""

    prior_industries: Optional[List[str]] = FieldInfo(alias="priorIndustries", default=None)
    """Previous industries worked in"""

    publications: Optional[List[str]] = None
    """Publications authored"""

    seniority: Optional[str] = None
    """Seniority classification"""

    seniority_level: Optional[str] = FieldInfo(alias="seniorityLevel", default=None)
    """Seniority level (e.g., Senior, Manager)"""

    state: Optional[str] = None
    """State or province"""

    title: Optional[str] = None
    """Current job title"""


class RepositoryStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class RepositoryStarrersEdge(BaseModel):
    id: str
    """BountyLab internal ID"""

    github_id: str = FieldInfo(alias="githubId")
    """GitHub node ID"""

    login: str
    """GitHub username"""

    bio: Optional[str] = None
    """User biography"""

    company: Optional[str] = None
    """Company name"""

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)
    """ISO 8601 timestamp when user account was created"""

    display_name: Optional[str] = FieldInfo(alias="displayName", default=None)
    """User display name"""

    emails: Optional[List[str]] = None
    """
    Obfuscated email addresses showing only the last 2 characters of the local part
    and full domain (e.g., "\\**\\**\\**oe@gmail.com"). Use /api/users/best-email endpoint
    for unobfuscated email access with intelligent selection.
    """

    embedded_at: Optional[str] = FieldInfo(alias="embeddedAt", default=None)
    """ISO 8601 timestamp when metadata was extracted"""

    location: Optional[str] = None
    """User location"""

    resolved_city: Optional[str] = FieldInfo(alias="resolvedCity", default=None)
    """Resolved city from location"""

    resolved_country: Optional[str] = FieldInfo(alias="resolvedCountry", default=None)
    """Resolved country from location"""

    resolved_state: Optional[str] = FieldInfo(alias="resolvedState", default=None)
    """Resolved state/region from location"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for distance metrics)"""

    social_accounts: Optional[List[RepositoryStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class RepositoryStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class RepositoryStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[RepositoryStarrersEdge]
    """Array of user objects"""

    page_info: RepositoryStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class Repository(BaseModel):
    id: str
    """BountyLab internal ID"""

    github_id: str = FieldInfo(alias="githubId")
    """GitHub node ID"""

    name: str
    """Repository name"""

    owner_login: str = FieldInfo(alias="ownerLogin")
    """Repository owner username"""

    stargazer_count: float = FieldInfo(alias="stargazerCount")
    """Number of stars"""

    total_issues_closed: float = FieldInfo(alias="totalIssuesClosed")
    """Number of closed issues"""

    total_issues_count: float = FieldInfo(alias="totalIssuesCount")
    """Total number of issues (open + closed)"""

    total_issues_open: float = FieldInfo(alias="totalIssuesOpen")
    """Number of open issues"""

    contributors: Optional[RepositoryContributors] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)
    """ISO 8601 timestamp when repository was created"""

    description: Optional[str] = None
    """Repository description"""

    embedded_at: Optional[str] = FieldInfo(alias="embeddedAt", default=None)
    """ISO 8601 timestamp when embedding was created"""

    language: Optional[str] = None
    """Primary programming language"""

    last_contributor_locations: Optional[List[str]] = FieldInfo(alias="lastContributorLocations", default=None)
    """Locations of last contributors to this repository"""

    owner: Optional[RepositoryOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[RepositoryOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[RepositoryOwnerProfessional] = FieldInfo(alias="ownerProfessional", default=None)
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[RepositoryStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class PageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class SearchRepoNaturalLanguageResponse(BaseModel):
    count: float
    """Number of repositories returned"""

    repositories: List[Repository]
    """
    Array of repository search results with relevance scores and optional graph
    relationships
    """

    search_query: str = FieldInfo(alias="searchQuery")
    """The generated search query used for semantic search"""

    page_info: Optional[PageInfo] = FieldInfo(alias="pageInfo", default=None)
    """Pagination information"""
