# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = [
    "SearchUserSearchResponse",
    "User",
    "UserContributes",
    "UserContributesEdge",
    "UserContributesEdgeContributors",
    "UserContributesEdgeContributorsEdge",
    "UserContributesEdgeContributorsEdgeSocialAccount",
    "UserContributesEdgeContributorsPageInfo",
    "UserContributesEdgeOwner",
    "UserContributesEdgeOwnerSocialAccount",
    "UserContributesEdgeOwnerDevrank",
    "UserContributesEdgeOwnerProfessional",
    "UserContributesEdgeOwnerProfessionalEducation",
    "UserContributesEdgeOwnerProfessionalExperience",
    "UserContributesEdgeStarrers",
    "UserContributesEdgeStarrersEdge",
    "UserContributesEdgeStarrersEdgeSocialAccount",
    "UserContributesEdgeStarrersPageInfo",
    "UserContributesPageInfo",
    "UserDevrank",
    "UserFollowers",
    "UserFollowersEdge",
    "UserFollowersEdgeSocialAccount",
    "UserFollowersPageInfo",
    "UserFollowing",
    "UserFollowingEdge",
    "UserFollowingEdgeSocialAccount",
    "UserFollowingPageInfo",
    "UserOwns",
    "UserOwnsEdge",
    "UserOwnsEdgeContributors",
    "UserOwnsEdgeContributorsEdge",
    "UserOwnsEdgeContributorsEdgeSocialAccount",
    "UserOwnsEdgeContributorsPageInfo",
    "UserOwnsEdgeOwner",
    "UserOwnsEdgeOwnerSocialAccount",
    "UserOwnsEdgeOwnerDevrank",
    "UserOwnsEdgeOwnerProfessional",
    "UserOwnsEdgeOwnerProfessionalEducation",
    "UserOwnsEdgeOwnerProfessionalExperience",
    "UserOwnsEdgeStarrers",
    "UserOwnsEdgeStarrersEdge",
    "UserOwnsEdgeStarrersEdgeSocialAccount",
    "UserOwnsEdgeStarrersPageInfo",
    "UserOwnsPageInfo",
    "UserProfessional",
    "UserProfessionalEducation",
    "UserProfessionalExperience",
    "UserSocialAccount",
    "UserStars",
    "UserStarsEdge",
    "UserStarsEdgeContributors",
    "UserStarsEdgeContributorsEdge",
    "UserStarsEdgeContributorsEdgeSocialAccount",
    "UserStarsEdgeContributorsPageInfo",
    "UserStarsEdgeOwner",
    "UserStarsEdgeOwnerSocialAccount",
    "UserStarsEdgeOwnerDevrank",
    "UserStarsEdgeOwnerProfessional",
    "UserStarsEdgeOwnerProfessionalEducation",
    "UserStarsEdgeOwnerProfessionalExperience",
    "UserStarsEdgeStarrers",
    "UserStarsEdgeStarrersEdge",
    "UserStarsEdgeStarrersEdgeSocialAccount",
    "UserStarsEdgeStarrersPageInfo",
    "UserStarsPageInfo",
    "PageInfo",
]


class UserContributesEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserContributesEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[UserContributesEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserContributesEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserContributesEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserContributesEdgeContributorsEdge]
    """Array of user objects"""

    page_info: UserContributesEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserContributesEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class UserContributesEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[UserContributesEdgeOwnerSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserContributesEdgeOwnerDevrank(BaseModel):
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


class UserContributesEdgeOwnerProfessionalEducation(BaseModel):
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


class UserContributesEdgeOwnerProfessionalExperience(BaseModel):
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


class UserContributesEdgeOwnerProfessional(BaseModel):
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

    education: List[UserContributesEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[UserContributesEdgeOwnerProfessionalExperience]
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


class UserContributesEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserContributesEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[UserContributesEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserContributesEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserContributesEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserContributesEdgeStarrersEdge]
    """Array of user objects"""

    page_info: UserContributesEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserContributesEdge(BaseModel):
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

    contributors: Optional[UserContributesEdgeContributors] = None
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

    owner: Optional[UserContributesEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[UserContributesEdgeOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[UserContributesEdgeOwnerProfessional] = FieldInfo(
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

    starrers: Optional[UserContributesEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class UserContributesPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserContributes(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[UserContributesEdge]
    """Array of repository objects"""

    page_info: UserContributesPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserDevrank(BaseModel):
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


class UserFollowersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserFollowersEdge(BaseModel):
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

    social_accounts: Optional[List[UserFollowersEdgeSocialAccount]] = FieldInfo(alias="socialAccounts", default=None)
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserFollowersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserFollowers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserFollowersEdge]
    """Array of user objects"""

    page_info: UserFollowersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserFollowingEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserFollowingEdge(BaseModel):
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

    social_accounts: Optional[List[UserFollowingEdgeSocialAccount]] = FieldInfo(alias="socialAccounts", default=None)
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserFollowingPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserFollowing(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserFollowingEdge]
    """Array of user objects"""

    page_info: UserFollowingPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserOwnsEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserOwnsEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[UserOwnsEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserOwnsEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserOwnsEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserOwnsEdgeContributorsEdge]
    """Array of user objects"""

    page_info: UserOwnsEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserOwnsEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class UserOwnsEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[UserOwnsEdgeOwnerSocialAccount]] = FieldInfo(alias="socialAccounts", default=None)
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserOwnsEdgeOwnerDevrank(BaseModel):
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


class UserOwnsEdgeOwnerProfessionalEducation(BaseModel):
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


class UserOwnsEdgeOwnerProfessionalExperience(BaseModel):
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


class UserOwnsEdgeOwnerProfessional(BaseModel):
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

    education: List[UserOwnsEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[UserOwnsEdgeOwnerProfessionalExperience]
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


class UserOwnsEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserOwnsEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[UserOwnsEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserOwnsEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserOwnsEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserOwnsEdgeStarrersEdge]
    """Array of user objects"""

    page_info: UserOwnsEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserOwnsEdge(BaseModel):
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

    contributors: Optional[UserOwnsEdgeContributors] = None
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

    owner: Optional[UserOwnsEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[UserOwnsEdgeOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[UserOwnsEdgeOwnerProfessional] = FieldInfo(alias="ownerProfessional", default=None)
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[UserOwnsEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class UserOwnsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserOwns(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[UserOwnsEdge]
    """Array of repository objects"""

    page_info: UserOwnsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserProfessionalEducation(BaseModel):
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


class UserProfessionalExperience(BaseModel):
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


class UserProfessional(BaseModel):
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

    education: List[UserProfessionalEducation]
    """Education history"""

    experience: List[UserProfessionalExperience]
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


class UserSocialAccount(BaseModel):
    provider: str

    url: str


class UserStarsEdgeContributorsEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserStarsEdgeContributorsEdge(BaseModel):
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

    social_accounts: Optional[List[UserStarsEdgeContributorsEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserStarsEdgeContributorsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserStarsEdgeContributors(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserStarsEdgeContributorsEdge]
    """Array of user objects"""

    page_info: UserStarsEdgeContributorsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserStarsEdgeOwnerSocialAccount(BaseModel):
    provider: str

    url: str


class UserStarsEdgeOwner(BaseModel):
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

    social_accounts: Optional[List[UserStarsEdgeOwnerSocialAccount]] = FieldInfo(alias="socialAccounts", default=None)
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserStarsEdgeOwnerDevrank(BaseModel):
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


class UserStarsEdgeOwnerProfessionalEducation(BaseModel):
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


class UserStarsEdgeOwnerProfessionalExperience(BaseModel):
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


class UserStarsEdgeOwnerProfessional(BaseModel):
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

    education: List[UserStarsEdgeOwnerProfessionalEducation]
    """Education history"""

    experience: List[UserStarsEdgeOwnerProfessionalExperience]
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


class UserStarsEdgeStarrersEdgeSocialAccount(BaseModel):
    provider: str

    url: str


class UserStarsEdgeStarrersEdge(BaseModel):
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

    social_accounts: Optional[List[UserStarsEdgeStarrersEdgeSocialAccount]] = FieldInfo(
        alias="socialAccounts", default=None
    )
    """Social media accounts"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class UserStarsEdgeStarrersPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserStarsEdgeStarrers(BaseModel):
    """Users who follow this user (when includeAttributes.followers is specified)"""

    edges: List[UserStarsEdgeStarrersEdge]
    """Array of user objects"""

    page_info: UserStarsEdgeStarrersPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class UserStarsEdge(BaseModel):
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

    contributors: Optional[UserStarsEdgeContributors] = None
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

    owner: Optional[UserStarsEdgeOwner] = None
    """Repository owner (when includeAttributes.owner = true)"""

    owner_devrank: Optional[UserStarsEdgeOwnerDevrank] = FieldInfo(alias="ownerDevrank", default=None)
    """
    Devrank data for the repository owner (when includeAttributes.ownerDevrank =
    true)
    """

    owner_professional: Optional[UserStarsEdgeOwnerProfessional] = FieldInfo(alias="ownerProfessional", default=None)
    """
    LinkedIn professional profile data (only present when
    includeAttributes.professional = true)
    """

    readme_preview: Optional[str] = FieldInfo(alias="readmePreview", default=None)
    """Preview of repository README (first ~500 chars)"""

    score: Optional[float] = None
    """Relevance score from search (0-1, lower is more relevant for cosine distance)"""

    starrers: Optional[UserStarsEdgeStarrers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when repository was last updated"""


class UserStarsPageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class UserStars(BaseModel):
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    edges: List[UserStarsEdge]
    """Array of repository objects"""

    page_info: UserStarsPageInfo = FieldInfo(alias="pageInfo")
    """Pagination information"""


class User(BaseModel):
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

    contributes: Optional[UserContributes] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    created_at: Optional[str] = FieldInfo(alias="createdAt", default=None)
    """ISO 8601 timestamp when user account was created"""

    devrank: Optional[UserDevrank] = None
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

    followers: Optional[UserFollowers] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    following: Optional[UserFollowing] = None
    """Users who follow this user (when includeAttributes.followers is specified)"""

    location: Optional[str] = None
    """User location"""

    owns: Optional[UserOwns] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    professional: Optional[UserProfessional] = None
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

    social_accounts: Optional[List[UserSocialAccount]] = FieldInfo(alias="socialAccounts", default=None)
    """Social media accounts"""

    stars: Optional[UserStars] = None
    """Repositories this user starred (when includeAttributes.stars is specified)"""

    updated_at: Optional[str] = FieldInfo(alias="updatedAt", default=None)
    """ISO 8601 timestamp when user was last updated"""

    website_url: Optional[str] = FieldInfo(alias="websiteUrl", default=None)
    """User website URL"""


class PageInfo(BaseModel):
    """Pagination information"""

    end_cursor: Optional[str] = FieldInfo(alias="endCursor", default=None)
    """Cursor to fetch next page (null if no more items)"""

    has_next_page: bool = FieldInfo(alias="hasNextPage")
    """Whether there are more items available"""


class SearchUserSearchResponse(BaseModel):
    count: float
    """Number of users returned"""

    users: List[User]
    """Array of user search results with relevance scores"""

    page_info: Optional[PageInfo] = FieldInfo(alias="pageInfo", default=None)
    """Pagination information"""
