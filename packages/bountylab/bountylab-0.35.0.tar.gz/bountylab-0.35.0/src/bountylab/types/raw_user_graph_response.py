# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Union, Optional
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "RawUserGraphResponse",
    "FollowersResponse",
    "FollowersResponsePageInfo",
    "FollowersResponseUser",
    "FollowersResponseUserContributes",
    "FollowersResponseUserContributesEdge",
    "FollowersResponseUserContributesEdgeContributors",
    "FollowersResponseUserContributesEdgeContributorsEdge",
    "FollowersResponseUserContributesEdgeContributorsEdgeSocialAccount",
    "FollowersResponseUserContributesEdgeContributorsPageInfo",
    "FollowersResponseUserContributesEdgeOwner",
    "FollowersResponseUserContributesEdgeOwnerSocialAccount",
    "FollowersResponseUserContributesEdgeOwnerDevrank",
    "FollowersResponseUserContributesEdgeOwnerProfessional",
    "FollowersResponseUserContributesEdgeOwnerProfessionalEducation",
    "FollowersResponseUserContributesEdgeOwnerProfessionalExperience",
    "FollowersResponseUserContributesEdgeStarrers",
    "FollowersResponseUserContributesEdgeStarrersEdge",
    "FollowersResponseUserContributesEdgeStarrersEdgeSocialAccount",
    "FollowersResponseUserContributesEdgeStarrersPageInfo",
    "FollowersResponseUserContributesPageInfo",
    "FollowersResponseUserDevrank",
    "FollowersResponseUserFollowers",
    "FollowersResponseUserFollowersEdge",
    "FollowersResponseUserFollowersEdgeSocialAccount",
    "FollowersResponseUserFollowersPageInfo",
    "FollowersResponseUserFollowing",
    "FollowersResponseUserFollowingEdge",
    "FollowersResponseUserFollowingEdgeSocialAccount",
    "FollowersResponseUserFollowingPageInfo",
    "FollowersResponseUserOwns",
    "FollowersResponseUserOwnsEdge",
    "FollowersResponseUserOwnsEdgeContributors",
    "FollowersResponseUserOwnsEdgeContributorsEdge",
    "FollowersResponseUserOwnsEdgeContributorsEdgeSocialAccount",
    "FollowersResponseUserOwnsEdgeContributorsPageInfo",
    "FollowersResponseUserOwnsEdgeOwner",
    "FollowersResponseUserOwnsEdgeOwnerSocialAccount",
    "FollowersResponseUserOwnsEdgeOwnerDevrank",
    "FollowersResponseUserOwnsEdgeOwnerProfessional",
    "FollowersResponseUserOwnsEdgeOwnerProfessionalEducation",
    "FollowersResponseUserOwnsEdgeOwnerProfessionalExperience",
    "FollowersResponseUserOwnsEdgeStarrers",
    "FollowersResponseUserOwnsEdgeStarrersEdge",
    "FollowersResponseUserOwnsEdgeStarrersEdgeSocialAccount",
    "FollowersResponseUserOwnsEdgeStarrersPageInfo",
    "FollowersResponseUserOwnsPageInfo",
    "FollowersResponseUserProfessional",
    "FollowersResponseUserProfessionalEducation",
    "FollowersResponseUserProfessionalExperience",
    "FollowersResponseUserSocialAccount",
    "FollowersResponseUserStars",
    "FollowersResponseUserStarsEdge",
    "FollowersResponseUserStarsEdgeContributors",
    "FollowersResponseUserStarsEdgeContributorsEdge",
    "FollowersResponseUserStarsEdgeContributorsEdgeSocialAccount",
    "FollowersResponseUserStarsEdgeContributorsPageInfo",
    "FollowersResponseUserStarsEdgeOwner",
    "FollowersResponseUserStarsEdgeOwnerSocialAccount",
    "FollowersResponseUserStarsEdgeOwnerDevrank",
    "FollowersResponseUserStarsEdgeOwnerProfessional",
    "FollowersResponseUserStarsEdgeOwnerProfessionalEducation",
    "FollowersResponseUserStarsEdgeOwnerProfessionalExperience",
    "FollowersResponseUserStarsEdgeStarrers",
    "FollowersResponseUserStarsEdgeStarrersEdge",
    "FollowersResponseUserStarsEdgeStarrersEdgeSocialAccount",
    "FollowersResponseUserStarsEdgeStarrersPageInfo",
    "FollowersResponseUserStarsPageInfo",
    "FollowingResponse",
    "FollowingResponsePageInfo",
    "FollowingResponseUser",
    "FollowingResponseUserContributes",
    "FollowingResponseUserContributesEdge",
    "FollowingResponseUserContributesEdgeContributors",
    "FollowingResponseUserContributesEdgeContributorsEdge",
    "FollowingResponseUserContributesEdgeContributorsEdgeSocialAccount",
    "FollowingResponseUserContributesEdgeContributorsPageInfo",
    "FollowingResponseUserContributesEdgeOwner",
    "FollowingResponseUserContributesEdgeOwnerSocialAccount",
    "FollowingResponseUserContributesEdgeOwnerDevrank",
    "FollowingResponseUserContributesEdgeOwnerProfessional",
    "FollowingResponseUserContributesEdgeOwnerProfessionalEducation",
    "FollowingResponseUserContributesEdgeOwnerProfessionalExperience",
    "FollowingResponseUserContributesEdgeStarrers",
    "FollowingResponseUserContributesEdgeStarrersEdge",
    "FollowingResponseUserContributesEdgeStarrersEdgeSocialAccount",
    "FollowingResponseUserContributesEdgeStarrersPageInfo",
    "FollowingResponseUserContributesPageInfo",
    "FollowingResponseUserDevrank",
    "FollowingResponseUserFollowers",
    "FollowingResponseUserFollowersEdge",
    "FollowingResponseUserFollowersEdgeSocialAccount",
    "FollowingResponseUserFollowersPageInfo",
    "FollowingResponseUserFollowing",
    "FollowingResponseUserFollowingEdge",
    "FollowingResponseUserFollowingEdgeSocialAccount",
    "FollowingResponseUserFollowingPageInfo",
    "FollowingResponseUserOwns",
    "FollowingResponseUserOwnsEdge",
    "FollowingResponseUserOwnsEdgeContributors",
    "FollowingResponseUserOwnsEdgeContributorsEdge",
    "FollowingResponseUserOwnsEdgeContributorsEdgeSocialAccount",
    "FollowingResponseUserOwnsEdgeContributorsPageInfo",
    "FollowingResponseUserOwnsEdgeOwner",
    "FollowingResponseUserOwnsEdgeOwnerSocialAccount",
    "FollowingResponseUserOwnsEdgeOwnerDevrank",
    "FollowingResponseUserOwnsEdgeOwnerProfessional",
    "FollowingResponseUserOwnsEdgeOwnerProfessionalEducation",
    "FollowingResponseUserOwnsEdgeOwnerProfessionalExperience",
    "FollowingResponseUserOwnsEdgeStarrers",
    "FollowingResponseUserOwnsEdgeStarrersEdge",
    "FollowingResponseUserOwnsEdgeStarrersEdgeSocialAccount",
    "FollowingResponseUserOwnsEdgeStarrersPageInfo",
    "FollowingResponseUserOwnsPageInfo",
    "FollowingResponseUserProfessional",
    "FollowingResponseUserProfessionalEducation",
    "FollowingResponseUserProfessionalExperience",
    "FollowingResponseUserSocialAccount",
    "FollowingResponseUserStars",
    "FollowingResponseUserStarsEdge",
    "FollowingResponseUserStarsEdgeContributors",
    "FollowingResponseUserStarsEdgeContributorsEdge",
    "FollowingResponseUserStarsEdgeContributorsEdgeSocialAccount",
    "FollowingResponseUserStarsEdgeContributorsPageInfo",
    "FollowingResponseUserStarsEdgeOwner",
    "FollowingResponseUserStarsEdgeOwnerSocialAccount",
    "FollowingResponseUserStarsEdgeOwnerDevrank",
    "FollowingResponseUserStarsEdgeOwnerProfessional",
    "FollowingResponseUserStarsEdgeOwnerProfessionalEducation",
    "FollowingResponseUserStarsEdgeOwnerProfessionalExperience",
    "FollowingResponseUserStarsEdgeStarrers",
    "FollowingResponseUserStarsEdgeStarrersEdge",
    "FollowingResponseUserStarsEdgeStarrersEdgeSocialAccount",
    "FollowingResponseUserStarsEdgeStarrersPageInfo",
    "FollowingResponseUserStarsPageInfo",
    "UserOwnsResponse",
    "UserOwnsResponsePageInfo",
    "UserOwnsResponseRepository",
    "UserOwnsResponseRepositoryContributors",
    "UserOwnsResponseRepositoryContributorsEdge",
    "UserOwnsResponseRepositoryContributorsEdgeSocialAccount",
    "UserOwnsResponseRepositoryContributorsPageInfo",
    "UserOwnsResponseRepositoryOwner",
    "UserOwnsResponseRepositoryOwnerSocialAccount",
    "UserOwnsResponseRepositoryOwnerDevrank",
    "UserOwnsResponseRepositoryOwnerProfessional",
    "UserOwnsResponseRepositoryOwnerProfessionalEducation",
    "UserOwnsResponseRepositoryOwnerProfessionalExperience",
    "UserOwnsResponseRepositoryStarrers",
    "UserOwnsResponseRepositoryStarrersEdge",
    "UserOwnsResponseRepositoryStarrersEdgeSocialAccount",
    "UserOwnsResponseRepositoryStarrersPageInfo",
    "UserStarsResponse",
    "UserStarsResponsePageInfo",
    "UserStarsResponseRepository",
    "UserStarsResponseRepositoryContributors",
    "UserStarsResponseRepositoryContributorsEdge",
    "UserStarsResponseRepositoryContributorsEdgeSocialAccount",
    "UserStarsResponseRepositoryContributorsPageInfo",
    "UserStarsResponseRepositoryOwner",
    "UserStarsResponseRepositoryOwnerSocialAccount",
    "UserStarsResponseRepositoryOwnerDevrank",
    "UserStarsResponseRepositoryOwnerProfessional",
    "UserStarsResponseRepositoryOwnerProfessionalEducation",
    "UserStarsResponseRepositoryOwnerProfessionalExperience",
    "UserStarsResponseRepositoryStarrers",
    "UserStarsResponseRepositoryStarrersEdge",
    "UserStarsResponseRepositoryStarrersEdgeSocialAccount",
    "UserStarsResponseRepositoryStarrersPageInfo",
    "UserContributesResponse",
    "UserContributesResponsePageInfo",
    "UserContributesResponseRepository",
    "UserContributesResponseRepositoryContributors",
    "UserContributesResponseRepositoryContributorsEdge",
    "UserContributesResponseRepositoryContributorsEdgeSocialAccount",
    "UserContributesResponseRepositoryContributorsPageInfo",
    "UserContributesResponseRepositoryOwner",
    "UserContributesResponseRepositoryOwnerSocialAccount",
    "UserContributesResponseRepositoryOwnerDevrank",
    "UserContributesResponseRepositoryOwnerProfessional",
    "UserContributesResponseRepositoryOwnerProfessionalEducation",
    "UserContributesResponseRepositoryOwnerProfessionalExperience",
    "UserContributesResponseRepositoryStarrers",
    "UserContributesResponseRepositoryStarrersEdge",
    "UserContributesResponseRepositoryStarrersEdgeSocialAccount",
    "UserContributesResponseRepositoryStarrersPageInfo",
]


class FollowersResponsePageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserContributesEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserContributesEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserContributesEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserContributesEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserContributesEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowersResponseUserContributesEdgeContributorsEdge]
    """Array of user objects"""

    page_info: FollowersResponseUserContributesEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserContributesEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserContributesEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserContributesEdgeOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserContributesEdgeOwnerDevrank(BaseModel):
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


class FollowersResponseUserContributesEdgeOwnerProfessionalEducation(BaseModel):
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


class FollowersResponseUserContributesEdgeOwnerProfessionalExperience(BaseModel):
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


class FollowersResponseUserContributesEdgeOwnerProfessional(BaseModel):
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

    education: List[FollowersResponseUserContributesEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[FollowersResponseUserContributesEdgeOwnerProfessionalExperience]
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


class FollowersResponseUserContributesEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserContributesEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserContributesEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserContributesEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserContributesEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowersResponseUserContributesEdgeStarrersEdge]
    """Array of user objects"""

    page_info: FollowersResponseUserContributesEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserContributesEdge(BaseModel):
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

    contributors: Optional[FollowersResponseUserContributesEdgeContributors] = None
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

    owner: Optional[FollowersResponseUserContributesEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[FollowersResponseUserContributesEdgeOwnerDevrank] = FieldInfo(
        alias="ownerDevrank", default=None
    )
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[FollowersResponseUserContributesEdgeOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[FollowersResponseUserContributesEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class FollowersResponseUserContributesPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserContributes(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[FollowersResponseUserContributesEdge]
    """Array of repository objects"""

    page_info: FollowersResponseUserContributesPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserDevrank(BaseModel):
    """Developer ranking data (only present when includeAttributes.devrank = true)"""

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


class FollowersResponseUserFollowersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserFollowersEdge(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserFollowersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserFollowersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserFollowers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowersResponseUserFollowersEdge]
    """Array of user objects"""

    page_info: FollowersResponseUserFollowersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserFollowingEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserFollowingEdge(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserFollowingEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserFollowingPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserFollowing(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowersResponseUserFollowingEdge]
    """Array of user objects"""

    page_info: FollowersResponseUserFollowingPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserOwnsEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserOwnsEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserOwnsEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserOwnsEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserOwnsEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowersResponseUserOwnsEdgeContributorsEdge]
    """Array of user objects"""

    page_info: FollowersResponseUserOwnsEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserOwnsEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserOwnsEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserOwnsEdgeOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserOwnsEdgeOwnerDevrank(BaseModel):
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


class FollowersResponseUserOwnsEdgeOwnerProfessionalEducation(BaseModel):
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


class FollowersResponseUserOwnsEdgeOwnerProfessionalExperience(BaseModel):
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


class FollowersResponseUserOwnsEdgeOwnerProfessional(BaseModel):
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

    education: List[FollowersResponseUserOwnsEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[FollowersResponseUserOwnsEdgeOwnerProfessionalExperience]
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


class FollowersResponseUserOwnsEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserOwnsEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserOwnsEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserOwnsEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserOwnsEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowersResponseUserOwnsEdgeStarrersEdge]
    """Array of user objects"""

    page_info: FollowersResponseUserOwnsEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserOwnsEdge(BaseModel):
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

    contributors: Optional[FollowersResponseUserOwnsEdgeContributors] = None
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

    owner: Optional[FollowersResponseUserOwnsEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[FollowersResponseUserOwnsEdgeOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[FollowersResponseUserOwnsEdgeOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[FollowersResponseUserOwnsEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class FollowersResponseUserOwnsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserOwns(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[FollowersResponseUserOwnsEdge]
    """Array of repository objects"""

    page_info: FollowersResponseUserOwnsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserProfessionalEducation(BaseModel):
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


class FollowersResponseUserProfessionalExperience(BaseModel):
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


class FollowersResponseUserProfessional(BaseModel):
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

    education: List[FollowersResponseUserProfessionalEducation]
    """Education history"""

    experience: List[FollowersResponseUserProfessionalExperience]
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


class FollowersResponseUserSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserStarsEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserStarsEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserStarsEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserStarsEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserStarsEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowersResponseUserStarsEdgeContributorsEdge]
    """Array of user objects"""

    page_info: FollowersResponseUserStarsEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserStarsEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserStarsEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserStarsEdgeOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserStarsEdgeOwnerDevrank(BaseModel):
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


class FollowersResponseUserStarsEdgeOwnerProfessionalEducation(BaseModel):
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


class FollowersResponseUserStarsEdgeOwnerProfessionalExperience(BaseModel):
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


class FollowersResponseUserStarsEdgeOwnerProfessional(BaseModel):
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

    education: List[FollowersResponseUserStarsEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[FollowersResponseUserStarsEdgeOwnerProfessionalExperience]
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


class FollowersResponseUserStarsEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowersResponseUserStarsEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[FollowersResponseUserStarsEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponseUserStarsEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserStarsEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowersResponseUserStarsEdgeStarrersEdge]
    """Array of user objects"""

    page_info: FollowersResponseUserStarsEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUserStarsEdge(BaseModel):
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

    contributors: Optional[FollowersResponseUserStarsEdgeContributors] = None
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

    owner: Optional[FollowersResponseUserStarsEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[FollowersResponseUserStarsEdgeOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[FollowersResponseUserStarsEdgeOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[FollowersResponseUserStarsEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class FollowersResponseUserStarsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowersResponseUserStars(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[FollowersResponseUserStarsEdge]
    """Array of repository objects"""

    page_info: FollowersResponseUserStarsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowersResponseUser(BaseModel):
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

    contributes: Optional[FollowersResponseUserContributes] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)
    """ISO 8601 timestamp when user account was created"""

    devrank: Optional[FollowersResponseUserDevrank] = None
    """Developer ranking data (only present when includeAttributes.devrank = true)"""

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

    followers: Optional[FollowersResponseUserFollowers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    following: Optional[FollowersResponseUserFollowing] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    location: Optional[str] = None
    """User location"""

    owns: Optional[FollowersResponseUserOwns] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    professional: Optional[FollowersResponseUserProfessional] = None
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    resolved_city: Optional[str] = FieldInfo(alias="resolvedCity", default=None)
    """Resolved city from location"""

    resolved_country: Optional[str] = FieldInfo(alias="resolvedCountry", default=None)
    """Resolved country from location"""

    resolved_state: Optional[str] = FieldInfo(alias="resolvedState", default=None)
    """Resolved state/region from location"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for distance metrics)"""

    social_accounts: Optional[List[FollowersResponseUserSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    stars: Optional[FollowersResponseUserStars] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowersResponse(BaseModel):
    page_info: FollowersResponsePageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""

    users: List[FollowersResponseUser]
    """Array of users who follow this user (with optional graph relationships)"""


class FollowingResponsePageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserContributesEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserContributesEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserContributesEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserContributesEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserContributesEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowingResponseUserContributesEdgeContributorsEdge]
    """Array of user objects"""

    page_info: FollowingResponseUserContributesEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserContributesEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserContributesEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserContributesEdgeOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserContributesEdgeOwnerDevrank(BaseModel):
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


class FollowingResponseUserContributesEdgeOwnerProfessionalEducation(BaseModel):
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


class FollowingResponseUserContributesEdgeOwnerProfessionalExperience(BaseModel):
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


class FollowingResponseUserContributesEdgeOwnerProfessional(BaseModel):
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

    education: List[FollowingResponseUserContributesEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[FollowingResponseUserContributesEdgeOwnerProfessionalExperience]
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


class FollowingResponseUserContributesEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserContributesEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserContributesEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserContributesEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserContributesEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowingResponseUserContributesEdgeStarrersEdge]
    """Array of user objects"""

    page_info: FollowingResponseUserContributesEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserContributesEdge(BaseModel):
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

    contributors: Optional[FollowingResponseUserContributesEdgeContributors] = None
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

    owner: Optional[FollowingResponseUserContributesEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[FollowingResponseUserContributesEdgeOwnerDevrank] = FieldInfo(
        alias="ownerDevrank", default=None
    )
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[FollowingResponseUserContributesEdgeOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[FollowingResponseUserContributesEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class FollowingResponseUserContributesPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserContributes(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[FollowingResponseUserContributesEdge]
    """Array of repository objects"""

    page_info: FollowingResponseUserContributesPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserDevrank(BaseModel):
    """Developer ranking data (only present when includeAttributes.devrank = true)"""

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


class FollowingResponseUserFollowersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserFollowersEdge(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserFollowersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserFollowersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserFollowers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowingResponseUserFollowersEdge]
    """Array of user objects"""

    page_info: FollowingResponseUserFollowersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserFollowingEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserFollowingEdge(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserFollowingEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserFollowingPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserFollowing(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowingResponseUserFollowingEdge]
    """Array of user objects"""

    page_info: FollowingResponseUserFollowingPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserOwnsEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserOwnsEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserOwnsEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserOwnsEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserOwnsEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowingResponseUserOwnsEdgeContributorsEdge]
    """Array of user objects"""

    page_info: FollowingResponseUserOwnsEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserOwnsEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserOwnsEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserOwnsEdgeOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserOwnsEdgeOwnerDevrank(BaseModel):
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


class FollowingResponseUserOwnsEdgeOwnerProfessionalEducation(BaseModel):
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


class FollowingResponseUserOwnsEdgeOwnerProfessionalExperience(BaseModel):
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


class FollowingResponseUserOwnsEdgeOwnerProfessional(BaseModel):
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

    education: List[FollowingResponseUserOwnsEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[FollowingResponseUserOwnsEdgeOwnerProfessionalExperience]
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


class FollowingResponseUserOwnsEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserOwnsEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserOwnsEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserOwnsEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserOwnsEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowingResponseUserOwnsEdgeStarrersEdge]
    """Array of user objects"""

    page_info: FollowingResponseUserOwnsEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserOwnsEdge(BaseModel):
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

    contributors: Optional[FollowingResponseUserOwnsEdgeContributors] = None
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

    owner: Optional[FollowingResponseUserOwnsEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[FollowingResponseUserOwnsEdgeOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[FollowingResponseUserOwnsEdgeOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[FollowingResponseUserOwnsEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class FollowingResponseUserOwnsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserOwns(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[FollowingResponseUserOwnsEdge]
    """Array of repository objects"""

    page_info: FollowingResponseUserOwnsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserProfessionalEducation(BaseModel):
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


class FollowingResponseUserProfessionalExperience(BaseModel):
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


class FollowingResponseUserProfessional(BaseModel):
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

    education: List[FollowingResponseUserProfessionalEducation]
    """Education history"""

    experience: List[FollowingResponseUserProfessionalExperience]
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


class FollowingResponseUserSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserStarsEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserStarsEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserStarsEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserStarsEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserStarsEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowingResponseUserStarsEdgeContributorsEdge]
    """Array of user objects"""

    page_info: FollowingResponseUserStarsEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserStarsEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserStarsEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserStarsEdgeOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserStarsEdgeOwnerDevrank(BaseModel):
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


class FollowingResponseUserStarsEdgeOwnerProfessionalEducation(BaseModel):
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


class FollowingResponseUserStarsEdgeOwnerProfessionalExperience(BaseModel):
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


class FollowingResponseUserStarsEdgeOwnerProfessional(BaseModel):
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

    education: List[FollowingResponseUserStarsEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[FollowingResponseUserStarsEdgeOwnerProfessionalExperience]
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


class FollowingResponseUserStarsEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class FollowingResponseUserStarsEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[FollowingResponseUserStarsEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponseUserStarsEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserStarsEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[FollowingResponseUserStarsEdgeStarrersEdge]
    """Array of user objects"""

    page_info: FollowingResponseUserStarsEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUserStarsEdge(BaseModel):
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

    contributors: Optional[FollowingResponseUserStarsEdgeContributors] = None
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

    owner: Optional[FollowingResponseUserStarsEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[FollowingResponseUserStarsEdgeOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[FollowingResponseUserStarsEdgeOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[FollowingResponseUserStarsEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class FollowingResponseUserStarsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class FollowingResponseUserStars(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[FollowingResponseUserStarsEdge]
    """Array of repository objects"""

    page_info: FollowingResponseUserStarsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class FollowingResponseUser(BaseModel):
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

    contributes: Optional[FollowingResponseUserContributes] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)
    """ISO 8601 timestamp when user account was created"""

    devrank: Optional[FollowingResponseUserDevrank] = None
    """Developer ranking data (only present when includeAttributes.devrank = true)"""

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

    followers: Optional[FollowingResponseUserFollowers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    following: Optional[FollowingResponseUserFollowing] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    location: Optional[str] = None
    """User location"""

    owns: Optional[FollowingResponseUserOwns] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    professional: Optional[FollowingResponseUserProfessional] = None
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    resolved_city: Optional[str] = FieldInfo(alias="resolvedCity", default=None)
    """Resolved city from location"""

    resolved_country: Optional[str] = FieldInfo(alias="resolvedCountry", default=None)
    """Resolved country from location"""

    resolved_state: Optional[str] = FieldInfo(alias="resolvedState", default=None)
    """Resolved state/region from location"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for distance metrics)"""

    social_accounts: Optional[List[FollowingResponseUserSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    stars: Optional[FollowingResponseUserStars] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class FollowingResponse(BaseModel):
    page_info: FollowingResponsePageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""

    users: List[FollowingResponseUser]
    """Array of users this user follows (with optional graph relationships)"""


class UserOwnsResponsePageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserOwnsResponseRepositoryContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserOwnsResponseRepositoryContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[UserOwnsResponseRepositoryContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserOwnsResponseRepositoryContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserOwnsResponseRepositoryContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserOwnsResponseRepositoryContributorsEdge]
    """Array of user objects"""

    page_info: UserOwnsResponseRepositoryContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserOwnsResponseRepositoryOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class UserOwnsResponseRepositoryOwner(BaseModel):
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

    social_accounts: Optional[List[UserOwnsResponseRepositoryOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserOwnsResponseRepositoryOwnerDevrank(BaseModel):
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


class UserOwnsResponseRepositoryOwnerProfessionalEducation(BaseModel):
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


class UserOwnsResponseRepositoryOwnerProfessionalExperience(BaseModel):
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


class UserOwnsResponseRepositoryOwnerProfessional(BaseModel):
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

    education: List[UserOwnsResponseRepositoryOwnerProfessionalEducation]
    """Education history"""

    experience: List[UserOwnsResponseRepositoryOwnerProfessionalExperience]
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


class UserOwnsResponseRepositoryStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserOwnsResponseRepositoryStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[UserOwnsResponseRepositoryStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserOwnsResponseRepositoryStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserOwnsResponseRepositoryStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserOwnsResponseRepositoryStarrersEdge]
    """Array of user objects"""

    page_info: UserOwnsResponseRepositoryStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserOwnsResponseRepository(BaseModel):
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

    contributors: Optional[UserOwnsResponseRepositoryContributors] = None
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

    owner: Optional[UserOwnsResponseRepositoryOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[UserOwnsResponseRepositoryOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[UserOwnsResponseRepositoryOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[UserOwnsResponseRepositoryStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class UserOwnsResponse(BaseModel):
    page_info: UserOwnsResponsePageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""

    repositories: List[UserOwnsResponseRepository]
    """Array of repositories owned by this user (with optional graph relationships)"""


class UserStarsResponsePageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserStarsResponseRepositoryContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserStarsResponseRepositoryContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[UserStarsResponseRepositoryContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserStarsResponseRepositoryContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserStarsResponseRepositoryContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserStarsResponseRepositoryContributorsEdge]
    """Array of user objects"""

    page_info: UserStarsResponseRepositoryContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserStarsResponseRepositoryOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class UserStarsResponseRepositoryOwner(BaseModel):
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

    social_accounts: Optional[List[UserStarsResponseRepositoryOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserStarsResponseRepositoryOwnerDevrank(BaseModel):
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


class UserStarsResponseRepositoryOwnerProfessionalEducation(BaseModel):
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


class UserStarsResponseRepositoryOwnerProfessionalExperience(BaseModel):
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


class UserStarsResponseRepositoryOwnerProfessional(BaseModel):
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

    education: List[UserStarsResponseRepositoryOwnerProfessionalEducation]
    """Education history"""

    experience: List[UserStarsResponseRepositoryOwnerProfessionalExperience]
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


class UserStarsResponseRepositoryStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserStarsResponseRepositoryStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[UserStarsResponseRepositoryStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserStarsResponseRepositoryStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserStarsResponseRepositoryStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserStarsResponseRepositoryStarrersEdge]
    """Array of user objects"""

    page_info: UserStarsResponseRepositoryStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserStarsResponseRepository(BaseModel):
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

    contributors: Optional[UserStarsResponseRepositoryContributors] = None
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

    owner: Optional[UserStarsResponseRepositoryOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[UserStarsResponseRepositoryOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[UserStarsResponseRepositoryOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[UserStarsResponseRepositoryStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class UserStarsResponse(BaseModel):
    page_info: UserStarsResponsePageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""

    repositories: List[UserStarsResponseRepository]
    """Array of repositories starred by this user (with optional graph relationships)"""


class UserContributesResponsePageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserContributesResponseRepositoryContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserContributesResponseRepositoryContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[UserContributesResponseRepositoryContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserContributesResponseRepositoryContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserContributesResponseRepositoryContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserContributesResponseRepositoryContributorsEdge]
    """Array of user objects"""

    page_info: UserContributesResponseRepositoryContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserContributesResponseRepositoryOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class UserContributesResponseRepositoryOwner(BaseModel):
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

    social_accounts: Optional[List[UserContributesResponseRepositoryOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserContributesResponseRepositoryOwnerDevrank(BaseModel):
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


class UserContributesResponseRepositoryOwnerProfessionalEducation(BaseModel):
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


class UserContributesResponseRepositoryOwnerProfessionalExperience(BaseModel):
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


class UserContributesResponseRepositoryOwnerProfessional(BaseModel):
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

    education: List[UserContributesResponseRepositoryOwnerProfessionalEducation]
    """Education history"""

    experience: List[UserContributesResponseRepositoryOwnerProfessionalExperience]
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


class UserContributesResponseRepositoryStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserContributesResponseRepositoryStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[UserContributesResponseRepositoryStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserContributesResponseRepositoryStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserContributesResponseRepositoryStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserContributesResponseRepositoryStarrersEdge]
    """Array of user objects"""

    page_info: UserContributesResponseRepositoryStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserContributesResponseRepository(BaseModel):
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

    contributors: Optional[UserContributesResponseRepositoryContributors] = None
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

    owner: Optional[UserContributesResponseRepositoryOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[UserContributesResponseRepositoryOwnerDevrank] = FieldInfo(
        alias="ownerDevrank", default=None
    )
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[UserContributesResponseRepositoryOwnerProfessional] = FieldInfo(
        alias="ownerProfessional", default=None
    )
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[UserContributesResponseRepositoryStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class UserContributesResponse(BaseModel):
    page_info: UserContributesResponsePageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""

    repositories: List[UserContributesResponseRepository]
    """
    Array of repositories this user contributes to (with optional graph
    relationships)
    """


RawUserGraphResponse: TypeAlias = Union[
    FollowersResponse, FollowingResponse, UserOwnsResponse, UserStarsResponse, UserContributesResponse
]
