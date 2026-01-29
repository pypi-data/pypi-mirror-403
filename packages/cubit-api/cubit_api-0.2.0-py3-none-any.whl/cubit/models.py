"""
Cubit API Response Types.

TypedDict definitions for API responses. These provide IDE autocompletion
and type checking without adding runtime dependencies.
"""

from typing import TypedDict, List, Optional, Literal


# =============================================================================
# COMMON TYPES
# =============================================================================

QuadrantType = Literal["automation", "augmentation", "protected", "status_quo"]
RequirementType = Literal["skills", "abilities", "knowledge"]
AggregationType = Literal["weighted_mean", "weighted_sum", "max"]
TransitionDifficulty = Literal["low", "medium", "high"]


# =============================================================================
# HEALTH / UTILITY MODELS
# =============================================================================

class HealthResponse(TypedDict):
    """Response for /health endpoint."""
    status: str
    version: str
    timestamp: str


class RootResponse(TypedDict):
    """Response for / endpoint."""
    status: str
    service: str
    version: str


class RateLimitInfo(TypedDict):
    """Rate limit information."""
    remaining: int


class Permissions(TypedDict):
    """API key permissions by tier."""
    semantic_search: bool
    task_data: bool
    regional_data: bool
    custom_scoring: bool
    batch_operations: bool


class MeResponse(TypedDict):
    """Response for /me endpoint."""
    tier: str
    org_name: Optional[str]
    rate_limit: RateLimitInfo
    permissions: Permissions


class DimensionSchema(TypedDict):
    """Schema for a dimension."""
    range: List[int]
    description: str


class PillarSchema(TypedDict, total=False):
    """Schema for a pillar."""
    formula: str
    source: str


class CompositeScoreSchema(TypedDict):
    """Schema for composite scores."""
    range: List[int]


class SchemaResponse(TypedDict):
    """Response for /schema endpoint."""
    version: str
    dimensions: dict
    pillars: dict
    composite_scores: dict
    quadrants: dict


# =============================================================================
# JOB MODELS
# =============================================================================

class JobScores(TypedDict):
    """Composite risk/resilience scores."""
    automation_susceptibility_score: float
    human_centric_resilience_score: float
    balanced_impact_score: float
    automation_susceptibility_quantile: Optional[float]
    human_centric_resilience_quantile: Optional[float]


class JobPillars(TypedDict):
    """Pillar scores that feed into composite scores."""
    ai_exposure_potential: float
    human_imperative: float
    dispositional_resilience: float


class JobClassification(TypedDict, total=False):
    """SOC classification and labor market data."""
    quadrant: QuadrantType
    major_group: str
    major_group_label: str
    minor_group: str
    minor_group_label: str
    broad_group: str
    broad_group_label: str
    projected_growth: float
    projected_job_openings: float


class KeystoneSkill(TypedDict):
    """High-impact skill for a job."""
    name: str
    type: str
    job_relevance: float
    ai_resilience: float
    combined_impact: float


class Industry(TypedDict):
    """Industry distribution for a job."""
    industry: str
    percentage: float


class JobProfile(TypedDict, total=False):
    """Full job profile response."""
    soc_code: str
    title: str
    scores: JobScores
    pillars: JobPillars
    classification: JobClassification
    keystone_skills: List[KeystoneSkill]
    industries: List[Industry]
    upgrade_notice: str


class JobSearchResult(TypedDict, total=False):
    """Single job in search results."""
    soc_code: str
    title: str
    automation_susceptibility_score: float
    human_centric_resilience_score: float
    balanced_impact_score: float
    quadrant: QuadrantType


class JobSearchResponse(TypedDict):
    """Response for keyword job search."""
    query: str
    count: int
    jobs: List[JobSearchResult]


class SemanticSearchResult(TypedDict, total=False):
    """Single job in semantic search results."""
    soc_code: str
    title: str
    relevance_score: float
    automation_susceptibility_score: float
    human_centric_resilience_score: float
    balanced_impact_score: float


class SemanticSearchResponse(TypedDict):
    """Response for semantic job search."""
    query: str
    count: int
    search_scope: str
    jobs: List[SemanticSearchResult]


# =============================================================================
# TASK MODELS
# =============================================================================

class TaskDimensions(TypedDict):
    """Four-dimension scores for a task (0-10 scale)."""
    procedural: float
    digitization: float
    physicality: float
    socio_emotional: float


class TaskPillars(TypedDict):
    """Pillar scores for a task (0-1 scale)."""
    structural_exposure: float
    human_imperative: float
    capability_task: float
    ai_exposure_potential: float


class TaskExplanations(TypedDict, total=False):
    """Natural language explanations for dimension scores."""
    procedural: str
    digitization: str
    physicality: str
    socio_emotional: str


class Task(TypedDict, total=False):
    """Single task in task list."""
    task_id: str
    task: str
    importance: float
    relevance: float
    dimensions: TaskDimensions
    pillars: TaskPillars
    explanations: TaskExplanations
    quadrant: QuadrantType


class TaskListResponse(TypedDict):
    """Response for job tasks endpoint."""
    soc_code: str
    title: str
    task_count: int
    tasks: List[Task]


# =============================================================================
# SKILL/REQUIREMENT MODELS
# =============================================================================

class Requirement(TypedDict, total=False):
    """Single skill/ability/knowledge item."""
    element_id: str
    name: str
    type: str
    description: str
    ai_resilience_score: float


class RequirementListResponse(TypedDict):
    """Response for skills list endpoint."""
    count: int
    requirements: List[Requirement]


class SkillSearchResult(TypedDict, total=False):
    """Single skill in semantic search results."""
    element_id: str
    name: str
    type: str
    similarity: float
    ai_resilience_score: float


class SkillSearchResponse(TypedDict):
    """Response for semantic skill search."""
    query: str
    count: int
    requirements: List[SkillSearchResult]


class RequirementDiagnostic(TypedDict, total=False):
    """Requirement with job-specific diagnostics."""
    name: str
    element_id: str
    type: str
    job_relevance: float
    ai_resilience_score: float
    benchmark_match_count: int
    benchmark_avg_relevance: float
    interpretation: str


class RequirementDiagnosticsResponse(TypedDict):
    """Response for job requirements endpoint."""
    soc_code: str
    title: str
    requirements: List[RequirementDiagnostic]


class BenchmarkCoverage(TypedDict):
    """AI benchmark coverage for a skill."""
    total_benchmarks: int
    top_benchmarks: List[str]
    avg_relevance: float


class JobPrevalence(TypedDict, total=False):
    """Job prevalence for a skill."""
    total_jobs: int
    avg_relevance: float
    top_jobs: List[dict]


class SkillProfile(TypedDict, total=False):
    """Detailed skill profile."""
    element_id: str
    name: str
    type: str
    description: str
    ai_resilience_score: float
    benchmark_coverage: BenchmarkCoverage
    job_prevalence: JobPrevalence


# =============================================================================
# REGION MODELS
# =============================================================================

class RegionSummary(TypedDict, total=False):
    """Region in list response."""
    msa_code: str
    msa_name: str
    total_employment: float
    total_at_risk_wages: float
    total_at_risk_jobs: float
    mean_automation_score: float
    mean_resilience_score: float


class RegionListResponse(TypedDict):
    """Response for regions list endpoint."""
    count: int
    regions: List[RegionSummary]


class RegionJobRisk(TypedDict, total=False):
    """Job risk data within a region."""
    soc_code: str
    title: str
    employment: float
    mean_annual_wage: float
    at_risk_wages: float
    at_risk_jobs: float
    automation_susceptibility_score: float
    human_centric_resilience_score: float
    balanced_impact_score: float


class RegionSummaryDetail(TypedDict, total=False):
    """Detailed summary statistics for a region."""
    total_employment: float
    total_at_risk_wages: float
    total_at_risk_jobs: float
    total_high_risk_jobs: float
    mean_automation_score: float
    mean_resilience_score: float


class RegionDetail(TypedDict, total=False):
    """Detailed region profile."""
    msa_code: str
    msa_name: str
    summary: RegionSummaryDetail
    top_exposed_jobs: List[RegionJobRisk]
    top_resilient_jobs: List[RegionJobRisk]


# =============================================================================
# ENTERPRISE ASSESSMENT MODELS
# =============================================================================

class CustomScoreResult(TypedDict):
    """Result for a single job with custom scoring."""
    soc_code: str
    title: str
    custom_score: float
    rank: int
    standard_score: float
    delta_from_standard: float
    task_count: int


class CustomScoreMethodology(TypedDict):
    """Methodology info for custom scoring."""
    weights_applied: dict
    aggregation: str
    interpretation: str


class CustomScoreResponse(TypedDict):
    """Response for custom score calculation."""
    methodology: CustomScoreMethodology
    results: List[CustomScoreResult]


class BatchLookupResponse(TypedDict):
    """Response for batch job lookup."""
    job_count: int
    fields_included: List[str]
    jobs: List[dict]


class TransitionTarget(TypedDict, total=False):
    """Potential career transition target."""
    target_soc: str
    target_title: str
    skill_similarity: float
    resilience_gain: float
    target_resilience_score: float
    target_automation_score: float
    projected_growth: float
    overlapping_skills: List[str]
    gap_skills: List[str]
    transition_difficulty: TransitionDifficulty


class TransitionSourceJob(TypedDict):
    """Source job info for transition response."""
    soc_code: str
    title: str
    automation_susceptibility_score: float
    human_centric_resilience_score: float


class TransitionResponse(TypedDict):
    """Response for career transitions."""
    source_job: TransitionSourceJob
    transitions: List[TransitionTarget]


# =============================================================================
# JOB EXPLAIN RESPONSE
# =============================================================================

class ScoreBreakdownItem(TypedDict, total=False):
    """Single score breakdown."""
    value: float
    formula: str
    source: str
    components: dict


class TaskAnalysisSummary(TypedDict):
    """Summary of task-level analysis."""
    task_count: int
    high_exposure_tasks: int
    protected_tasks: int


class DataSources(TypedDict):
    """Data provenance information."""
    tasks: str
    benchmarks: str
    annotations: str


class JobExplainResponse(TypedDict):
    """Methodology explanation for a job's scores."""
    soc_code: str
    title: str
    methodology_version: str
    score_breakdown: dict
    task_analysis: TaskAnalysisSummary
    data_sources: DataSources


# =============================================================================
# STATS OVERVIEW
# =============================================================================

class MethodologyInfo(TypedDict):
    """Data provenance for stats."""
    occupation_source: str
    benchmark_source: str
    annotations: str


class StatsOverviewResponse(TypedDict):
    """Response for /stats/overview endpoint."""
    data_version: str
    total_occupations: int
    total_tasks: int
    total_requirements: int
    total_benchmarks: int
    total_regions: int
    quadrant_distribution: dict
    methodology: MethodologyInfo


# =============================================================================
# JOB COMPARE
# =============================================================================

class JobCompareItem(TypedDict, total=False):
    """Single job in compare response."""
    soc_code: str
    title: str
    automation_susceptibility_score: float
    human_centric_resilience_score: float
    balanced_impact_score: float
    ai_exposure_potential: float
    human_imperative: float
    dispositional_resilience: float
    keystone_skills: List[KeystoneSkill]
    projected_growth: str
    quadrant: QuadrantType


class JobCompareResponse(TypedDict):
    """Response for /jobs/compare endpoint."""
    comparison: List[JobCompareItem]
    skill_overlap_matrix: dict


# =============================================================================
# SKILL GAP ANALYSIS
# =============================================================================

class SkillGapTargetJob(TypedDict):
    """Target job in skill gap response."""
    soc_code: str
    title: str
    resilience_score: Optional[float]


class GapSkill(TypedDict):
    """A skill that needs development."""
    name: str
    type: Optional[str]
    priority: str
    job_relevance: float
    ai_resilience: float
    interpretation: str


class TransferableSkill(TypedDict):
    """A skill that transfers to the target job."""
    name: str
    type: Optional[str]
    job_relevance: float
    ai_resilience: float
    value: str


class SkillGapResponse(TypedDict):
    """Response for /skills/gap endpoint."""
    target_job: SkillGapTargetJob
    skill_coverage: float
    skills_matched: int
    skills_required: int
    gap_skills: List[GapSkill]
    transferable_skills: List[TransferableSkill]
    summary: str


# =============================================================================
# BENCHMARKS
# =============================================================================

class BenchmarkSummary(TypedDict):
    """Single benchmark in list response."""
    input_id: str
    benchmark_name: str
    task_description: str


class BenchmarkListResponse(TypedDict):
    """Response for /benchmarks endpoint."""
    count: int
    page_size: int
    skill_filter: Optional[str]
    benchmarks: List[BenchmarkSummary]


class SkillTested(TypedDict, total=False):
    """Skill tested by a benchmark."""
    element_id: str
    name: str
    type: str
    relevance_score: float
    explanation: str


class BenchmarkDetailResponse(TypedDict):
    """Response for /benchmarks/{input_id} endpoint."""
    input_id: str
    benchmark_name: str
    task_description: str
    skills_tested: List[SkillTested]
