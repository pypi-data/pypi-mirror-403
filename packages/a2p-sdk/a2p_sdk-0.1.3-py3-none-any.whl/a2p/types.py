"""
a2p Protocol Type Definitions

This module exports all Python types for the a2p protocol using Pydantic models.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field

# ============================================================================
# Enums
# ============================================================================


class ProfileType(str, Enum):
    """Profile types supported by the protocol"""

    HUMAN = "human"
    AGENT = "agent"
    ENTITY = "entity"


class MemorySourceType(str, Enum):
    """Memory source types"""

    USER_MANUAL = "user_manual"
    USER_IMPORT = "user_import"
    AGENT_PROPOSAL = "agent_proposal"
    AGENT_DIRECT = "agent_direct"
    SYSTEM_DERIVED = "system_derived"


class MemoryStatus(str, Enum):
    """Memory status values"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"
    EXPIRED = "expired"


class SensitivityLevel(str, Enum):
    """Sensitivity levels for memories"""

    PUBLIC = "public"
    STANDARD = "standard"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"


class PermissionLevel(str, Enum):
    """Permission levels for consent"""

    NONE = "none"
    READ_PUBLIC = "read_public"
    READ_SCOPED = "read_scoped"
    READ_FULL = "read_full"
    PROPOSE = "propose"
    WRITE = "write"


class ProposalStatus(str, Enum):
    """Proposal status values"""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


class ProposalAction(str, Enum):
    """Proposal resolution actions"""

    APPROVED = "approved"
    APPROVED_WITH_EDITS = "approved_with_edits"
    REJECTED = "rejected"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


# ============================================================================
# Identity Types
# ============================================================================


class PublicKey(BaseModel):
    """Public key information"""

    id: str
    type: Literal["Ed25519", "secp256k1", "P-256"]
    public_key_multibase: str = Field(alias="publicKeyMultibase")

    class Config:
        populate_by_name = True


class Identity(BaseModel):
    """Identity section of a profile"""

    did: str
    display_name: str | None = Field(default=None, alias="displayName")
    pronouns: str | None = None
    public_keys: list[PublicKey] | None = Field(default=None, alias="publicKeys")
    recovery_methods: list[str] | None = Field(default=None, alias="recoveryMethods")
    age_context: "AgeContext | None" = Field(default=None, alias="ageContext")

    class Config:
        populate_by_name = True


# ============================================================================
# Preference Types
# ============================================================================


class CommunicationPreferences(BaseModel):
    """Communication preferences"""

    style: Literal["concise", "detailed", "balanced"] | None = None
    formality: Literal["formal", "casual", "adaptive"] | None = None
    humor: bool | None = None
    verbosity: str | None = None


class ContentPreferences(BaseModel):
    """Content preferences"""

    format: Literal["markdown", "plain", "rich"] | None = None
    code_style: Literal["commented", "minimal", "verbose"] | None = Field(
        default=None, alias="codeStyle"
    )
    example_language: str | None = Field(default=None, alias="exampleLanguage")
    language: str | None = None

    class Config:
        populate_by_name = True


# ============================================================================
# Accessibility Types
# ============================================================================


class ColorVision(BaseModel):
    """Color vision deficiency information"""

    type: (
        Literal[
            "none",
            "protanopia",
            "deuteranopia",
            "tritanopia",
            "achromatopsia",
            "protanomaly",
            "deuteranomaly",
            "tritanomaly",
        ]
        | None
    ) = None
    severity: Literal["none", "mild", "moderate", "severe"] | None = None


class VisionAccessibility(BaseModel):
    """Vision accessibility preferences"""

    screen_reader: bool = Field(default=False, alias="screenReader")
    magnification: float | None = None
    high_contrast: Literal["none", "more", "less", "custom"] | None = Field(
        default=None, alias="highContrast"
    )
    reduced_motion: bool = Field(default=False, alias="reducedMotion")
    color_vision: ColorVision | None = Field(default=None, alias="colorVision")
    prefers_dark_mode: bool = Field(default=False, alias="prefersDarkMode")
    font_size: Literal["default", "large", "larger", "largest"] | None = Field(
        default=None, alias="fontSize"
    )

    class Config:
        populate_by_name = True


class CaptionSettings(BaseModel):
    """Caption settings"""

    enabled: bool = False
    style: Literal["default", "large", "high-contrast"] | None = None
    background: Literal["none", "solid", "translucent"] | None = None


class HearingAccessibility(BaseModel):
    """Hearing accessibility preferences"""

    deaf: bool = False
    hard_of_hearing: bool = Field(default=False, alias="hardOfHearing")
    prefers_visual_alerts: bool = Field(default=False, alias="prefersVisualAlerts")
    captions: CaptionSettings | None = None
    sign_language: str | None = Field(default=None, alias="signLanguage")
    mono_audio: bool = Field(default=False, alias="monoAudio")

    class Config:
        populate_by_name = True


class MotorAccessibility(BaseModel):
    """Motor accessibility preferences"""

    reduced_motion: bool = Field(default=False, alias="reducedMotion")
    keyboard_only: bool = Field(default=False, alias="keyboardOnly")
    switch_access: bool = Field(default=False, alias="switchAccess")
    voice_control: bool = Field(default=False, alias="voiceControl")
    large_click_targets: bool = Field(default=False, alias="largeClickTargets")
    extended_timeouts: bool = Field(default=False, alias="extendedTimeouts")

    class Config:
        populate_by_name = True


class ReadingAssistance(BaseModel):
    """Reading assistance preferences"""

    dyslexia_font: bool = Field(default=False, alias="dyslexiaFont")
    line_spacing: Literal["default", "wide", "wider"] | None = Field(
        default=None, alias="lineSpacing"
    )
    letter_spacing: Literal["default", "wide", "wider"] | None = Field(
        default=None, alias="letterSpacing"
    )
    focus_mode: bool = Field(default=False, alias="focusMode")
    reading_guide: bool = Field(default=False, alias="readingGuide")

    class Config:
        populate_by_name = True


class CognitiveAccessibility(BaseModel):
    """Cognitive accessibility preferences"""

    simplified_ui: bool = Field(default=False, alias="simplifiedUI")
    reduced_animations: bool = Field(default=False, alias="reducedAnimations")
    reading_assistance: ReadingAssistance | None = Field(default=None, alias="readingAssistance")
    memory_aids: bool = Field(default=False, alias="memoryAids")
    clear_navigation: bool = Field(default=False, alias="clearNavigation")
    plain_language: bool = Field(default=False, alias="plainLanguage")

    class Config:
        populate_by_name = True


class SensoryAccessibility(BaseModel):
    """Sensory accessibility preferences"""

    reduce_flashing: bool = Field(default=False, alias="reduceFlashing")
    reduce_autoplay: bool = Field(default=False, alias="reduceAutoplay")
    quiet_mode: bool = Field(default=False, alias="quietMode")
    haptic_feedback: bool = Field(default=True, alias="hapticFeedback")

    class Config:
        populate_by_name = True


class MobilityAccessibility(BaseModel):
    """Mobility accessibility needs"""

    wheelchair: bool = False
    wheelchair_type: Literal["manual", "electric", "scooter"] | None = Field(
        default=None, alias="wheelchairType"
    )
    walker: bool = False
    crutches: bool = False
    cane: bool = False
    requires_accessible_entrance: bool = Field(default=False, alias="requiresAccessibleEntrance")
    requires_elevator: bool = Field(default=False, alias="requiresElevator")
    requires_accessible_bathroom: bool = Field(default=False, alias="requiresAccessibleBathroom")

    class Config:
        populate_by_name = True


class ServiceAnimal(BaseModel):
    """Service animal information"""

    has: bool = False
    type: (
        Literal[
            "guide_dog",
            "hearing_dog",
            "mobility_dog",
            "psychiatric_dog",
            "seizure_alert_dog",
            "other",
        ]
        | None
    ) = None
    name: str | None = None
    breed: str | None = None


class MedicalDevices(BaseModel):
    """Medical devices information"""

    pacemaker: bool = False
    insulin_pump: bool = Field(default=False, alias="insulinPump")
    oxygen_supply: bool = Field(default=False, alias="oxygenSupply")
    hearing_aid: bool = Field(default=False, alias="hearingAid")
    cochlear_implant: bool = Field(default=False, alias="cochlearImplant")
    cpap_machine: bool = Field(default=False, alias="cpapMachine")
    prosthetic: bool = False
    other: list[str] | None = None

    class Config:
        populate_by_name = True


class Allergies(BaseModel):
    """Allergies information"""

    food: list[str] | None = None
    medication: list[str] | None = None
    environmental: list[str] | None = None
    severity: dict[str, Literal["mild", "moderate", "severe", "anaphylactic"]] | None = None
    epi_pen_carrier: bool = Field(default=False, alias="epiPenCarrier")

    class Config:
        populate_by_name = True


class DietaryRequirements(BaseModel):
    """Dietary requirements"""

    restrictions: list[str] | None = None
    intolerances: list[str] | None = None
    medical_diets: list[str] | None = Field(default=None, alias="medicalDiets")
    preferences: list[str] | None = None

    class Config:
        populate_by_name = True


class EmergencyContact(BaseModel):
    """Emergency contact information"""

    name: str | None = None
    relationship: str | None = None
    phone: str | None = None


class SpecialAssistance(BaseModel):
    """Special assistance needs"""

    interpreter: str | None = None
    companion: bool = False
    early_boarding: bool = Field(default=False, alias="earlyBoarding")
    extra_time: bool = Field(default=False, alias="extraTime")
    preferred_seating: (
        Literal[
            "aisle", "window", "front", "near_exit", "near_bathroom", "extra_legroom", "accessible"
        ]
        | None
    ) = Field(default=None, alias="preferredSeating")
    quiet_environment: bool = Field(default=False, alias="quietEnvironment")

    class Config:
        populate_by_name = True


class EmergencyInfo(BaseModel):
    """Emergency information"""

    emergency_contact: EmergencyContact | None = Field(default=None, alias="emergencyContact")
    medical_conditions: list[str] | None = Field(default=None, alias="medicalConditions")
    blood_type: Literal["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"] | None = Field(
        default=None, alias="bloodType"
    )
    do_not_resuscitate: bool = Field(default=False, alias="doNotResuscitate")

    class Config:
        populate_by_name = True


class PhysicalAccessibility(BaseModel):
    """Physical accessibility needs"""

    mobility: MobilityAccessibility | None = None
    service_animal: ServiceAnimal | None = Field(default=None, alias="serviceAnimal")
    medical_devices: MedicalDevices | None = Field(default=None, alias="medicalDevices")
    allergies: Allergies | None = None
    dietary: DietaryRequirements | None = None
    special_assistance: SpecialAssistance | None = Field(default=None, alias="specialAssistance")
    emergency_info: EmergencyInfo | None = Field(default=None, alias="emergencyInfo")

    class Config:
        populate_by_name = True


class AccessibilityPreferences(BaseModel):
    """Complete accessibility preferences"""

    vision: VisionAccessibility | None = None
    hearing: HearingAccessibility | None = None
    motor: MotorAccessibility | None = None
    cognitive: CognitiveAccessibility | None = None
    sensory: SensoryAccessibility | None = None
    physical: PhysicalAccessibility | None = None

    class Config:
        populate_by_name = True


# ============================================================================
# Guardianship Types
# ============================================================================


class AgeContext(BaseModel):
    """Age context for a profile"""

    age_group: Literal["adult", "minor", "child", "teen"] | None = Field(
        default=None, alias="ageGroup"
    )
    age_range: str | None = Field(default=None, alias="ageRange")
    jurisdiction: str | None = None
    digital_age_of_consent: int | None = Field(default=None, alias="digitalAgeOfConsent")
    consent_status: Literal["self_consent", "parental_consent", "no_consent"] | None = Field(
        default=None, alias="consentStatus"
    )

    class Config:
        populate_by_name = True


class Guardian(BaseModel):
    """Guardian information"""

    did: str
    relationship: Literal["parent", "legal_guardian", "custodian"]
    permissions: list[
        Literal["manage_profile", "approve_proposals", "set_policies", "view_activity"]
    ]
    consent_given: datetime = Field(alias="consentGiven")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")

    class Config:
        populate_by_name = True


class ChatRestrictions(BaseModel):
    """Chat restrictions for children"""

    allow_strangers: bool = Field(default=False, alias="allowStrangers")
    moderated_chats: bool = Field(default=True, alias="moderatedChats")
    predefined_phrases_only: bool = Field(default=False, alias="predefinedPhrasesOnly")

    class Config:
        populate_by_name = True


class PurchaseControls(BaseModel):
    """Purchase controls for children"""

    require_approval: bool = Field(default=True, alias="requireApproval")
    spending_limit: float = Field(default=0, alias="spendingLimit")

    class Config:
        populate_by_name = True


class ScreenTime(BaseModel):
    """Screen time settings"""

    enabled: bool = False
    daily_limit: str | None = Field(default=None, alias="dailyLimit")
    bedtime: str | None = None
    break_reminders: bool = Field(default=True, alias="breakReminders")

    class Config:
        populate_by_name = True


class ContentSafety(BaseModel):
    """Content safety settings for children"""

    age_group: Literal["toddler", "child", "preteen", "teen", "adult"] | None = Field(
        default=None, alias="ageGroup"
    )
    maturity_rating: Literal["G", "PG", "PG-13", "R", "NC-17", "AO"] | None = Field(
        default=None, alias="maturityRating"
    )
    filter_explicit_content: bool = Field(default=True, alias="filterExplicitContent")
    filter_violence: bool = Field(default=True, alias="filterViolence")
    filter_scary_content: bool = Field(default=False, alias="filterScaryContent")
    safe_search: Literal["off", "moderate", "strict"] = Field(default="strict", alias="safeSearch")
    chat_restrictions: ChatRestrictions | None = Field(default=None, alias="chatRestrictions")
    purchase_controls: PurchaseControls | None = Field(default=None, alias="purchaseControls")
    screen_time: ScreenTime | None = Field(default=None, alias="screenTime")

    class Config:
        populate_by_name = True


class Guardianship(BaseModel):
    """Guardianship settings for minor profiles"""

    guardians: list[Guardian] | None = None
    managed_by: str | None = Field(default=None, alias="managedBy")
    content_safety: ContentSafety | None = Field(default=None, alias="contentSafety")

    class Config:
        populate_by_name = True


class CommonPreferences(BaseModel):
    """Common preferences shared across sub-profiles"""

    language: str | None = None
    timezone: str | None = None
    communication: CommunicationPreferences | None = None
    content: ContentPreferences | None = None
    accessibility: AccessibilityPreferences | None = None


class Common(BaseModel):
    """Common section of a profile"""

    preferences: CommonPreferences | None = None


# ============================================================================
# Memory Category Types
# ============================================================================


class CategoryIdentity(BaseModel):
    """Identity category"""

    name: dict[str, str | None] | None = None
    birth_year: int | None = Field(default=None, alias="birthYear")
    location: dict[str, str | None] | None = None

    class Config:
        populate_by_name = True


class CategoryPreferences(BaseModel):
    """Preferences category"""

    communication: CommunicationPreferences | None = None
    content: ContentPreferences | None = None
    ui: dict[str, str | None] | None = None


class CategoryProfessional(BaseModel):
    """Professional category"""

    occupation: str | None = None
    title: str | None = None
    employer: str | None = None
    industry: str | None = None
    skills: list[str] | None = None
    experience: dict[str, int | str | None] | None = None
    work_style: Literal["remote", "hybrid", "office", "flexible"] | None = Field(
        default=None, alias="workStyle"
    )

    class Config:
        populate_by_name = True


class CategoryInterests(BaseModel):
    """Interests category"""

    topics: list[str] | None = None
    hobbies: list[str] | None = None
    music: dict[str, list[str]] | None = None
    reading: dict[str, list[str]] | None = None
    sports: list[str] | None = None
    travel: dict[str, list[str]] | None = None


class CategoryContext(BaseModel):
    """Context category"""

    current_projects: list[str] | None = Field(default=None, alias="currentProjects")
    recent_topics: list[str] | None = Field(default=None, alias="recentTopics")
    ongoing_goals: list[str] | None = Field(default=None, alias="ongoingGoals")
    current_focus: str | None = Field(default=None, alias="currentFocus")

    class Config:
        populate_by_name = True


class CategoryHealth(BaseModel):
    """Health category (sensitive)"""

    allergies: list[str] | None = None
    dietary: Literal["omnivore", "vegetarian", "vegan", "pescatarian", "keto", "other"] | None = (
        None
    )
    conditions: list[str] | None = None
    medications: list[str] | None = None


class CategoryRelationships(BaseModel):
    """Relationships category (sensitive)"""

    family: dict[str, str] | None = None
    pets: list[dict[str, str]] | None = None


# ============================================================================
# Memory Types
# ============================================================================


class MemorySource(BaseModel):
    """Source information for a memory"""

    type: MemorySourceType
    agent_did: str | None = Field(default=None, alias="agentDid")
    agent_name: str | None = Field(default=None, alias="agentName")
    session_id: str | None = Field(default=None, alias="sessionId")
    timestamp: datetime
    context: str | None = None
    import_source: str | None = Field(default=None, alias="importSource")

    class Config:
        populate_by_name = True


class MemoryMetadata(BaseModel):
    """Memory metadata"""

    approved_at: datetime | None = Field(default=None, alias="approvedAt")
    rejected_at: datetime | None = Field(default=None, alias="rejectedAt")
    archived_at: datetime | None = Field(default=None, alias="archivedAt")
    last_used: datetime | None = Field(default=None, alias="lastUsed")
    use_count: int = Field(default=0, alias="useCount")
    last_confirmed: datetime | None = Field(default=None, alias="lastConfirmed")
    initial_confidence: float | None = Field(default=None, alias="initialConfidence")
    merged_from: list[str] | None = Field(default=None, alias="mergedFrom")
    supersedes: str | None = None
    superseded_by: str | None = Field(default=None, alias="supersededBy")

    class Config:
        populate_by_name = True


class Memory(BaseModel):
    """A discrete piece of information about a user"""

    id: str
    content: str
    category: str | None = None
    source: MemorySource
    confidence: float = 0.8
    status: MemoryStatus
    sensitivity: SensitivityLevel = SensitivityLevel.STANDARD
    scope: list[str] | None = None
    metadata: MemoryMetadata | None = None
    tags: list[str] | None = None


class Memories(BaseModel):
    """Memories section of a profile"""

    identity: CategoryIdentity | None = Field(default=None, alias="a2p:identity")
    preferences: CategoryPreferences | None = Field(default=None, alias="a2p:preferences")
    professional: CategoryProfessional | None = Field(default=None, alias="a2p:professional")
    interests: CategoryInterests | None = Field(default=None, alias="a2p:interests")
    context: CategoryContext | None = Field(default=None, alias="a2p:context")
    health: CategoryHealth | None = Field(default=None, alias="a2p:health")
    relationships: CategoryRelationships | None = Field(default=None, alias="a2p:relationships")

    # Memory types
    episodic: list[Memory] | None = Field(default=None, alias="a2p:episodic")
    semantic: list[Memory] | None = Field(default=None, alias="a2p:semantic")
    procedural: list[Memory] | None = Field(default=None, alias="a2p:procedural")

    class Config:
        populate_by_name = True
        extra = "allow"


# ============================================================================
# Sub-Profile Types
# ============================================================================


class SubProfile(BaseModel):
    """Context-specific sub-profile"""

    id: str
    name: str
    description: str | None = None
    inherits_from: list[str] | None = Field(default=None, alias="inheritsFrom")
    overrides: dict[str, Any] | None = None
    specialized: dict[str, Any] | None = None
    share_with: list[str] | None = Field(default=None, alias="shareWith")

    class Config:
        populate_by_name = True


# ============================================================================
# Consent Types
# ============================================================================


class PolicyConditions(BaseModel):
    """Conditions for a consent policy to apply"""

    require_verified_operator: bool | None = Field(default=None, alias="requireVerifiedOperator")
    min_trust_score: float | None = Field(default=None, alias="minTrustScore")
    require_audit: bool | None = Field(default=None, alias="requireAudit")
    allowed_jurisdictions: list[str] | None = Field(default=None, alias="allowedJurisdictions")
    blocked_jurisdictions: list[str] | None = Field(default=None, alias="blockedJurisdictions")
    require_https: bool | None = Field(default=True, alias="requireHttps")
    max_data_retention: str | None = Field(default=None, alias="maxDataRetention")

    class Config:
        populate_by_name = True


class ConsentPolicy(BaseModel):
    """Access control policy"""

    id: str
    name: str | None = None
    description: str | None = None
    priority: int = 100
    enabled: bool = True
    agent_pattern: str = Field(alias="agentPattern")
    agent_dids: list[str] | None = Field(default=None, alias="agentDids")
    agent_tags: list[str] | None = Field(default=None, alias="agentTags")
    operator_dids: list[str] | None = Field(default=None, alias="operatorDids")
    allow: list[str] | None = None
    deny: list[str] | None = None
    permissions: list[PermissionLevel]
    conditions: PolicyConditions | None = None
    sub_profile: str | None = Field(default=None, alias="subProfile")
    expiry: datetime | None = None
    created: datetime | None = None
    updated: datetime | None = None

    class Config:
        populate_by_name = True


class ConsentProof(BaseModel):
    """Proof of consent for audit"""

    type: Literal["signature", "hash", "blockchain", "none"]
    algorithm: str | None = None
    hash: str | None = None
    signature: str | None = None
    signed_by: str | None = Field(default=None, alias="signedBy")
    location: str | None = None
    blockchain_ref: dict[str, Any] | None = Field(default=None, alias="blockchainRef")

    class Config:
        populate_by_name = True


class ConsentReceipt(BaseModel):
    """Consent receipt"""

    receipt_id: str = Field(alias="receiptId")
    user_did: str = Field(alias="userDid")
    agent_did: str = Field(alias="agentDid")
    operator_did: str | None = Field(default=None, alias="operatorDid")
    policy_id: str | None = Field(default=None, alias="policyId")
    granted_scopes: list[str] = Field(alias="grantedScopes")
    denied_scopes: list[str] | None = Field(default=None, alias="deniedScopes")
    permissions: list[PermissionLevel]
    sub_profile: str | None = Field(default=None, alias="subProfile")
    granted_at: datetime = Field(alias="grantedAt")
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    revoked_at: datetime | None = Field(default=None, alias="revokedAt")
    revoked_reason: str | None = Field(default=None, alias="revokedReason")
    consent_method: Literal["policy_match", "explicit_grant", "one_time", "session"] | None = Field(
        default=None, alias="consentMethod"
    )
    purpose: str | None = None
    legal_basis: (
        Literal[
            "consent",
            "contract",
            "legal_obligation",
            "vital_interests",
            "public_task",
            "legitimate_interests",
        ]
        | None
    ) = Field(default=None, alias="legalBasis")
    proof: ConsentProof | None = None

    class Config:
        populate_by_name = True


# ============================================================================
# Proposal Types
# ============================================================================


class ProposalEvidence(BaseModel):
    """Evidence supporting a memory proposal"""

    type: Literal["user_statement", "inferred", "confirmed", "external"]
    quote: str | None = None
    timestamp: datetime | None = None


class ProposedMemory(BaseModel):
    """Proposed memory content"""

    content: str
    category: str | None = None
    confidence: float | None = None
    suggested_sensitivity: SensitivityLevel | None = Field(
        default=None, alias="suggestedSensitivity"
    )
    suggested_scope: list[str] | None = Field(default=None, alias="suggestedScope")
    suggested_tags: list[str] | None = Field(default=None, alias="suggestedTags")

    class Config:
        populate_by_name = True


class ProposalResolution(BaseModel):
    """Proposal resolution"""

    resolved_at: datetime = Field(alias="resolvedAt")
    action: ProposalAction
    edited_content: str | None = Field(default=None, alias="editedContent")
    edited_category: str | None = Field(default=None, alias="editedCategory")
    reason: str | None = None
    created_memory_id: str | None = Field(default=None, alias="createdMemoryId")

    class Config:
        populate_by_name = True


class Proposal(BaseModel):
    """Memory proposal from an agent"""

    id: str
    proposed_by: dict[str, str | None] = Field(alias="proposedBy")
    proposed_at: datetime = Field(alias="proposedAt")
    memory: ProposedMemory
    context: str | None = None
    evidence: list[ProposalEvidence] | None = None
    status: ProposalStatus
    resolution: ProposalResolution | None = None
    expires_at: datetime | None = Field(default=None, alias="expiresAt")
    priority: Literal["low", "normal", "high"] = "normal"
    similar_to: list[str] | None = Field(default=None, alias="similarTo")

    class Config:
        populate_by_name = True


# ============================================================================
# Settings Types
# ============================================================================


class MemorySettings(BaseModel):
    """Memory settings"""

    decay_enabled: bool = Field(default=True, alias="decayEnabled")
    decay_rate: float = Field(default=0.1, alias="decayRate")
    decay_interval: str = Field(default="30d", alias="decayInterval")
    review_threshold: float = Field(default=0.5, alias="reviewThreshold")
    archive_threshold: float = Field(default=0.3, alias="archiveThreshold")

    class Config:
        populate_by_name = True


class NotificationSettings(BaseModel):
    """Notification settings"""

    proposal_notifications: bool = Field(default=True, alias="proposalNotifications")
    access_notifications: bool = Field(default=False, alias="accessNotifications")
    consolidation_reminders: bool = Field(default=True, alias="consolidationReminders")

    class Config:
        populate_by_name = True


class PrivacySettings(BaseModel):
    """Privacy settings"""

    default_sensitivity: SensitivityLevel = Field(
        default=SensitivityLevel.STANDARD, alias="defaultSensitivity"
    )
    allow_anonymous_access: bool = Field(default=False, alias="allowAnonymousAccess")

    class Config:
        populate_by_name = True


class ProfileSettings(BaseModel):
    """Profile settings"""

    memory_settings: MemorySettings | None = Field(default=None, alias="memorySettings")
    notification_settings: NotificationSettings | None = Field(
        default=None, alias="notificationSettings"
    )
    privacy_settings: PrivacySettings | None = Field(default=None, alias="privacySettings")

    class Config:
        populate_by_name = True


# ============================================================================
# Profile Types
# ============================================================================


class Profile(BaseModel):
    """Complete user profile"""

    id: str
    version: str = "0.1.0-alpha"
    profile_type: ProfileType = Field(alias="profileType")
    created: datetime | None = None
    updated: datetime | None = None
    identity: Identity
    common: Common | None = None
    memories: Memories | None = None
    sub_profiles: list[SubProfile] | None = Field(default=None, alias="subProfiles")
    pending_proposals: list[Proposal] | None = Field(default=None, alias="pendingProposals")
    access_policies: list[ConsentPolicy] | None = Field(default=None, alias="accessPolicies")
    settings: ProfileSettings | None = None
    guardianship: Guardianship | None = None

    class Config:
        populate_by_name = True


# ============================================================================
# Agent Profile Types
# ============================================================================


class AgentIdentity(BaseModel):
    """Agent identity"""

    name: str
    description: str | None = None
    short_description: str | None = Field(default=None, alias="shortDescription")
    version: str | None = None
    icon: str | None = None
    banner: str | None = None
    homepage: str | None = None
    documentation: str | None = None
    a2a_card: str | None = Field(default=None, alias="a2aCard")
    tags: list[str] | None = None

    class Config:
        populate_by_name = True


class AgentOperator(BaseModel):
    """Agent operator information"""

    name: str
    did: str | None = None
    jurisdiction: str | None = None
    address: dict[str, str | None] | None = None
    contact: str | None = None
    dpo: str | None = None
    privacy_policy: str | None = Field(default=None, alias="privacyPolicy")
    terms_of_service: str | None = Field(default=None, alias="termsOfService")
    verified: bool | None = None
    verified_by: str | None = Field(default=None, alias="verifiedBy")

    class Config:
        populate_by_name = True


class AgentA2PSupport(BaseModel):
    """Agent a2p support declaration"""

    protocol_version: str = Field(alias="protocolVersion")
    capabilities: dict[str, bool] | None = None
    requested_scopes: list[str] | None = Field(default=None, alias="requestedScopes")
    required_scopes: list[str] | None = Field(default=None, alias="requiredScopes")
    supported_categories: list[str] | None = Field(default=None, alias="supportedCategories")
    data_retention: dict[str, str] | None = Field(default=None, alias="dataRetention")
    endpoints: dict[str, str] | None = None

    class Config:
        populate_by_name = True


class AgentTrustMetrics(BaseModel):
    """Agent trust metrics"""

    verified_operator: bool | None = Field(default=None, alias="verifiedOperator")
    security_audit: dict[str, Any] | None = Field(default=None, alias="securityAudit")
    privacy_audit: dict[str, Any] | None = Field(default=None, alias="privacyAudit")
    community_score: float | None = Field(default=None, alias="communityScore")
    community_reviews: int | None = Field(default=None, alias="communityReviews")
    certifications: list[str] | None = None
    incident_history: list[dict[str, Any]] | None = Field(default=None, alias="incidentHistory")

    class Config:
        populate_by_name = True


class AgentCapabilities(BaseModel):
    """Agent capabilities"""

    domains: list[str] | None = None
    languages: list[str] | None = None
    modalities: list[Literal["text", "voice", "image", "video", "code"]] | None = None
    integrations: list[str] | None = None


class AgentProfile(BaseModel):
    """Complete agent profile"""

    id: str
    profile_type: Literal["agent"] = Field(default="agent", alias="profileType")
    version: str | None = None
    created: datetime | None = None
    updated: datetime | None = None
    identity: AgentIdentity
    operator: AgentOperator
    a2p_support: AgentA2PSupport = Field(alias="a2pSupport")
    trust_metrics: AgentTrustMetrics | None = Field(default=None, alias="trustMetrics")
    capabilities: AgentCapabilities | None = None

    class Config:
        populate_by_name = True
