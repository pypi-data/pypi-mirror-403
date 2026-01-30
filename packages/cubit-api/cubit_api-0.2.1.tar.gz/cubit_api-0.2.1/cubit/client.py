"""
Cubit API Synchronous Client.

A Pythonic interface to the Cubit AI Job Vulnerability API.
"""

from typing import Optional, List, Dict, Any
import httpx

from .exceptions import (
    CubitError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
    ServerError,
)
from .models import (
    HealthResponse,
    RootResponse,
    MeResponse,
    SchemaResponse,
    JobProfile,
    JobSearchResponse,
    SemanticSearchResponse,
    TaskListResponse,
    RequirementDiagnosticsResponse,
    RequirementListResponse,
    SkillSearchResponse,
    SkillProfile,
    RegionListResponse,
    RegionDetail,
    CustomScoreResponse,
    BatchLookupResponse,
    TransitionResponse,
    JobExplainResponse,
    StatsOverviewResponse,
    JobCompareResponse,
    SkillGapResponse,
    BenchmarkListResponse,
    BenchmarkDetailResponse,
)


class CubitClient:
    """
    Synchronous client for the Cubit API.
    
    Example:
        >>> from cubit import CubitClient
        >>> client = CubitClient("cubit_xxxxxxxxxxxx")
        >>> jobs = client.search_jobs("software developer")
        >>> print(jobs["jobs"][0]["title"])
        'Software Developers'
    """
    
    DEFAULT_BASE_URL = "https://api.maidenlabs.tools"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the Cubit API client.
        
        Args:
            api_key: Your Cubit API key (starts with 'cubit_')
            base_url: Override the default API URL (for testing/staging)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "cubit-python/0.2.1",
                "Accept": "application/json",
            },
            timeout=timeout,
        )
    
    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Process response and raise appropriate exceptions for errors."""
        try:
            body = response.json() if response.content else {}
        except Exception:
            body = {"detail": response.text}
        
        if response.is_success:
            return body
        
        message = body.get("detail", f"HTTP {response.status_code}")
        
        if response.status_code == 401:
            raise AuthenticationError(message, response.status_code, body)
        elif response.status_code == 403:
            raise AuthorizationError(message, response.status_code, body)
        elif response.status_code == 404:
            raise NotFoundError(message, response.status_code, body)
        elif response.status_code == 422:
            raise ValidationError(message, response.status_code, body)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message,
                response.status_code,
                body,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif response.status_code >= 500:
            raise ServerError(message, response.status_code, body)
        else:
            raise CubitError(message, response.status_code, body)
    
    def close(self) -> None:
        """Close the HTTP client connection."""
        self._client.close()
    
    def __enter__(self) -> "CubitClient":
        return self
    
    def __exit__(self, *args) -> None:
        self.close()
    
    # =========================================================================
    # HEALTH & UTILITY
    # =========================================================================
    
    def health(self) -> HealthResponse:
        """
        Check API health status.
        
        Returns:
            HealthResponse with status, version, and timestamp
        """
        response = self._client.get("/health")
        return self._handle_response(response)
    
    def root(self) -> RootResponse:
        """
        Root endpoint health check.
        
        Returns:
            RootResponse with status, service name, and version
        """
        response = self._client.get("/")
        return self._handle_response(response)
    
    def me(self) -> MeResponse:
        """
        Get information about the current API key.
        
        Returns:
            MeResponse with tier, org name, rate limits, and permissions
        """
        response = self._client.get("/me")
        return self._handle_response(response)
    
    def schema(self) -> SchemaResponse:
        """
        Get data schema and field definitions.
        
        Returns:
            SchemaResponse with dimension, pillar, and score definitions
        """
        response = self._client.get("/schema")
        return self._handle_response(response)
    
    def stats_overview(self) -> StatsOverviewResponse:
        """
        Get aggregate statistics about the dataset.
        
        Returns:
            StatsOverviewResponse with counts, quadrant distribution, and methodology info
        
        Example:
            >>> stats = client.stats_overview()
            >>> print(f"Occupations: {stats['total_occupations']}")
            >>> print(f"Benchmarks: {stats['total_benchmarks']}")
        """
        response = self._client.get("/stats/overview")
        return self._handle_response(response)
    
    # =========================================================================
    # JOBS - Search
    # =========================================================================
    
    def search_jobs(
        self,
        query: str,
        limit: int = 10,
        exposure_threshold: Optional[float] = None,
        imperative_threshold: Optional[float] = None,
    ) -> JobSearchResponse:
        """
        Search for jobs by title using keyword matching.
        
        Args:
            query: Search query for job title
            limit: Max number of results (1-50)
            exposure_threshold: Threshold for "high exposure" quadrant (0.0-1.0, default 0.5)
            imperative_threshold: Threshold for "high imperative" quadrant (0.0-1.0, default 0.5)
        
        Returns:
            JobSearchResponse with matching jobs
        
        Example:
            >>> results = client.search_jobs("nurse", limit=5)
            >>> for job in results["jobs"]:
            ...     print(f"{job['title']}: {job['balanced_impact_score']}")
            
            >>> # With custom thresholds
            >>> results = client.search_jobs("clerk", exposure_threshold=0.45)
        """
        params = {"q": query, "limit": limit}
        if exposure_threshold is not None:
            params["exposure_threshold"] = exposure_threshold
        if imperative_threshold is not None:
            params["imperative_threshold"] = imperative_threshold
        
        response = self._client.get("/jobs/search", params=params)
        return self._handle_response(response)
    
    def search_jobs_semantic(
        self,
        query: str,
        limit: int = 10,
        search_scope: str = "jobs",
    ) -> SemanticSearchResponse:
        """
        Search for jobs using semantic similarity.
        
        Requires Builder or Enterprise tier.
        
        Args:
            query: Natural language query (e.g., "jobs for people who like to argue")
            limit: Max number of results (1-50)
            search_scope: "jobs", "tasks", or "both"
        
        Returns:
            SemanticSearchResponse with relevance-scored jobs
        
        Example:
            >>> results = client.search_jobs_semantic("careers working with animals outdoors")
            >>> for job in results["jobs"]:
            ...     print(f"{job['title']} ({job['relevance_score']:.2f})")
        """
        response = self._client.get(
            "/jobs/search/semantic",
            params={"q": query, "limit": limit, "search_scope": search_scope},
        )
        return self._handle_response(response)
    
    # =========================================================================
    # JOBS - Profile
    # =========================================================================
    
    def get_job(
        self, 
        soc_code: str,
        exposure_threshold: Optional[float] = None,
        imperative_threshold: Optional[float] = None,
    ) -> JobProfile:
        """
        Get the complete profile for a single job.
        
        Args:
            soc_code: O*NET SOC code (e.g., "15-1252.00")
            exposure_threshold: Threshold for "high exposure" quadrant (0.0-1.0, default 0.5)
            imperative_threshold: Threshold for "high imperative" quadrant (0.0-1.0, default 0.5)
        
        Returns:
            JobProfile with scores, classification, and (for Builder+) keystone skills
        
        Example:
            >>> job = client.get_job("15-1252.00")
            >>> print(f"{job['title']}: {job['scores']['balanced_impact_score']}")
            
            >>> # With custom thresholds
            >>> job = client.get_job("43-3031.00", exposure_threshold=0.45)
            >>> print(job["classification"]["quadrant"])  # May now be "automation"
        """
        params = {}
        if exposure_threshold is not None:
            params["exposure_threshold"] = exposure_threshold
        if imperative_threshold is not None:
            params["imperative_threshold"] = imperative_threshold
        
        response = self._client.get(f"/jobs/{soc_code}", params=params if params else None)
        return self._handle_response(response)
    
    def get_job_tasks(
        self,
        soc_code: str,
        sort_by: str = "ai_exposure_potential",
        sort_order: str = "desc",
        limit: int = 50,
        include_explanations: bool = True,
        exposure_threshold: Optional[float] = None,
        imperative_threshold: Optional[float] = None,
    ) -> TaskListResponse:
        """
        Get all tasks for a job with dimension scores.
        
        Requires Builder or Enterprise tier.
        
        Args:
            soc_code: O*NET SOC code
            sort_by: Sort field (default: ai_exposure_potential)
            sort_order: "asc" or "desc"
            limit: Max tasks to return (1-100)
            include_explanations: Include dimension explanations
            exposure_threshold: Threshold for "high exposure" quadrant (0.0-1.0, default 0.5)
            imperative_threshold: Threshold for "high imperative" quadrant (0.0-1.0, default 0.5)
        
        Returns:
            TaskListResponse with scored tasks
        """
        params = {
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "include_explanations": include_explanations,
        }
        if exposure_threshold is not None:
            params["exposure_threshold"] = exposure_threshold
        if imperative_threshold is not None:
            params["imperative_threshold"] = imperative_threshold
        
        response = self._client.get(f"/jobs/{soc_code}/tasks", params=params)
        return self._handle_response(response)
    
    def get_job_requirements(
        self,
        soc_code: str,
        type: str = "all",
        source: str = "diagnostics",
        limit: int = 20,
    ) -> RequirementDiagnosticsResponse:
        """
        Get requirement diagnostics for a job.
        
        Requires Builder or Enterprise tier.
        
        Args:
            soc_code: O*NET SOC code
            type: Filter by "all", "skills", "abilities", or "knowledge"
            source: "diagnostics" (full data) or "keystone" (top 10)
            limit: Max requirements (1-120)
        
        Returns:
            RequirementDiagnosticsResponse with skill importance and AI resilience
        """
        response = self._client.get(
            f"/jobs/{soc_code}/requirements",
            params={"type": type, "source": source, "limit": limit},
        )
        return self._handle_response(response)
    
    def explain_job(self, soc_code: str) -> JobExplainResponse:
        """
        Get methodology explanation for a job's scores.
        
        Requires Builder or Enterprise tier.
        
        Args:
            soc_code: O*NET SOC code
        
        Returns:
            JobExplainResponse with score breakdown and data sources
        """
        response = self._client.get(f"/jobs/{soc_code}/explain")
        return self._handle_response(response)
    
    def compare_jobs(
        self, 
        soc_codes: List[str],
        exposure_threshold: Optional[float] = None,
        imperative_threshold: Optional[float] = None,
    ) -> JobCompareResponse:
        """
        Compare multiple jobs side-by-side.
        
        Requires Builder or Enterprise tier.
        
        Args:
            soc_codes: List of SOC codes to compare (2-10 jobs)
            exposure_threshold: Threshold for "high exposure" quadrant (0.0-1.0, default 0.5)
            imperative_threshold: Threshold for "high imperative" quadrant (0.0-1.0, default 0.5)
        
        Returns:
            JobCompareResponse with job data and skill overlap matrix
        
        Example:
            >>> result = client.compare_jobs(["15-1252.00", "13-2011.00"])
            >>> for job in result["comparison"]:
            ...     print(f"{job['title']}: {job['human_centric_resilience_score']}")
            >>> print(f"Skill overlap: {result['skill_overlap_matrix']}")
        """
        socs_str = ",".join(soc_codes)
        params = {"socs": socs_str}
        if exposure_threshold is not None:
            params["exposure_threshold"] = exposure_threshold
        if imperative_threshold is not None:
            params["imperative_threshold"] = imperative_threshold
        
        response = self._client.get("/jobs/compare", params=params)
        return self._handle_response(response)
    
    # =========================================================================
    # SKILLS
    # =========================================================================
    
    def list_skills(
        self,
        type: str = "all",
        sort_by: str = "ai_resilience_score",
        limit: int = 50,
    ) -> RequirementListResponse:
        """
        List all skills/abilities/knowledge with AI resilience scores.
        
        Args:
            type: Filter by "all", "skills", "abilities", or "knowledge"
            sort_by: Sort field
            limit: Max results (1-120)
        
        Returns:
            RequirementListResponse with 120 total requirements
        """
        response = self._client.get(
            "/skills",
            params={"type": type, "sort_by": sort_by, "limit": limit},
        )
        return self._handle_response(response)
    
    def search_skills_semantic(
        self,
        query: str,
        limit: int = 10,
    ) -> SkillSearchResponse:
        """
        Search for skills using semantic similarity.
        
        Requires Builder or Enterprise tier.
        
        Args:
            query: Natural language query
            limit: Max results (1-50)
        
        Returns:
            SkillSearchResponse with matching skills
        """
        response = self._client.get(
            "/skills/search/semantic",
            params={"q": query, "limit": limit},
        )
        return self._handle_response(response)
    
    def get_skill(self, element_id: str) -> SkillProfile:
        """
        Get detailed profile for a skill.
        
        Requires Builder or Enterprise tier.
        
        Args:
            element_id: O*NET element ID (e.g., "2.A.1.a")
        
        Returns:
            SkillProfile with AI resilience and job prevalence
        """
        response = self._client.get(f"/skills/{element_id}")
        return self._handle_response(response)
    
    def analyze_skill_gap(
        self,
        current_skills: List[str],
        target_job: str,
    ) -> SkillGapResponse:
        """
        Analyze skill gaps for career transition to a target job.
        
        Requires Builder or Enterprise tier.
        
        Args:
            current_skills: List of skill names you currently have
            target_job: Target job SOC code
        
        Returns:
            SkillGapResponse with coverage ratio, gap skills, and transferable skills
        
        Example:
            >>> result = client.analyze_skill_gap(
            ...     current_skills=["Programming", "Critical Thinking"],
            ...     target_job="13-2011.00"
            ... )
            >>> print(f"Coverage: {result['skill_coverage']:.1%}")
            >>> for gap in result["gap_skills"][:3]:
            ...     print(f"Need: {gap['name']} ({gap['priority']})")
        """
        response = self._client.post(
            "/skills/gap",
            json={"current_skills": current_skills, "target_job": target_job},
        )
        return self._handle_response(response)
    
    # =========================================================================
    # REGIONS
    # =========================================================================
    
    def list_regions(
        self,
        state: Optional[str] = None,
        min_employment: int = 0,
        sort_by: str = "employment",
        limit: int = 50,
    ) -> RegionListResponse:
        """
        List all MSA regions with headline risk metrics.
        
        Requires Builder or Enterprise tier.
        
        Args:
            state: Filter by state code (e.g., "CA", "TX")
            min_employment: Minimum total employment
            sort_by: Sort field
            limit: Max results (1-500)
        
        Returns:
            RegionListResponse with metropolitan area risk data
        """
        params: Dict[str, Any] = {
            "min_employment": min_employment,
            "sort_by": sort_by,
            "limit": limit,
        }
        if state:
            params["state"] = state
        
        response = self._client.get("/regions", params=params)
        return self._handle_response(response)
    
    def get_region(
        self,
        msa_code: str,
        include_jobs: bool = False,
        job_limit: int = 20,
    ) -> RegionDetail:
        """
        Get detailed risk profile for a region.
        
        Requires Builder or Enterprise tier.
        
        Args:
            msa_code: MSA code (e.g., "31080" for Los Angeles)
            include_jobs: Include job-level breakdown
            job_limit: Max jobs to include (1-100)
        
        Returns:
            RegionDetail with employment and wage risk data
        """
        response = self._client.get(
            f"/regions/{msa_code}",
            params={"include_jobs": include_jobs, "job_limit": job_limit},
        )
        return self._handle_response(response)
    
    # =========================================================================
    # ENTERPRISE - Assessments
    # =========================================================================
    
    def calculate_custom_score(
        self,
        weights: Dict[str, float],
        jobs: List[str],
        aggregation: str = "weighted_mean",
    ) -> CustomScoreResponse:
        """
        Calculate custom risk scores with your own dimension weights.
        
        Enterprise tier only.
        
        Args:
            weights: Dict mapping dimension names to weights (procedural, digitization, 
                     physicality, socio_emotional). Values typically -1.0 to 1.0.
            jobs: List of SOC codes to score (max 100)
            aggregation: Aggregation method ("weighted_mean", "weighted_sum", "max")
        
        Returns:
            CustomScoreResponse with methodology and recalculated scores
        """
        response = self._client.post(
            "/assessments/custom-score",
            json={"weights": weights, "jobs": jobs, "aggregation": aggregation},
        )
        return self._handle_response(response)
    
    def batch_lookup(
        self,
        soc_codes: List[str],
        fields: Optional[List[str]] = None,
        format: str = "json",
    ) -> BatchLookupResponse:
        """
        Retrieve profiles for multiple jobs in a single request.
        
        Enterprise tier only.
        
        Args:
            soc_codes: List of SOC codes (up to 500)
            fields: Fields to include (default: ["scores", "pillars", "classification"])
            format: Response format ("json" only currently supported)
        
        Returns:
            BatchLookupResponse with job profiles
        """
        payload: Dict[str, Any] = {"soc_codes": soc_codes, "format": format}
        if fields:
            payload["fields"] = fields
        
        response = self._client.post("/jobs/batch", json=payload)
        return self._handle_response(response)
    
    def find_transitions(
        self,
        source_soc: str,
        similarity_threshold: float = 0.7,
        max_results: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> TransitionResponse:
        """
        Find career transition pathways using skill-based similarity.
        
        Enterprise tier only.
        
        Args:
            source_soc: Starting job SOC code
            similarity_threshold: Minimum skill similarity (0-1)
            max_results: Max transitions to return (1-100)
            filters: Optional filters:
                - min_resilience_gain: Minimum resilience score improvement
                - max_resilience_loss: Maximum resilience score decrease
                - require_positive_growth: Only include growing occupations
                - min_projected_growth: Minimum projected growth rate
                - exclude_soc_codes: SOC codes to exclude
        
        Returns:
            TransitionResponse with source job and potential career paths
        """
        payload: Dict[str, Any] = {
            "source_soc": source_soc,
            "similarity_threshold": similarity_threshold,
            "max_results": max_results,
        }
        if filters:
            payload["filters"] = filters
        
        response = self._client.post("/jobs/transitions", json=payload)
        return self._handle_response(response)
    
    # =========================================================================
    # ENTERPRISE - Benchmarks
    # =========================================================================
    
    def list_benchmarks(
        self,
        skill: Optional[str] = None,
        benchmark: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> BenchmarkListResponse:
        """
        List AI benchmark evaluations with optional filtering.
        
        Enterprise tier only.
        
        Args:
            skill: Filter by skill name (partial match)
            benchmark: Filter by benchmark suite (e.g., 'mmlu')
            limit: Max results per page (1-100)
            offset: Pagination offset
        
        Returns:
            BenchmarkListResponse with 182,000+ AI evaluation tasks
        
        Example:
            >>> benchmarks = client.list_benchmarks(skill="Programming", limit=10)
            >>> for b in benchmarks["benchmarks"]:
            ...     print(f"[{b['benchmark_name']}] {b['task_description'][:60]}...")
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if skill:
            params["skill"] = skill
        if benchmark:
            params["benchmark"] = benchmark
        
        response = self._client.get("/benchmarks", params=params)
        return self._handle_response(response)
    
    def get_benchmark(self, input_id: str) -> BenchmarkDetailResponse:
        """
        Get detailed information about a specific benchmark.
        
        Enterprise tier only.
        
        Args:
            input_id: Benchmark input ID
        
        Returns:
            BenchmarkDetailResponse with task description and skills tested
        
        Example:
            >>> benchmark = client.get_benchmark("0")
            >>> print(f"Task: {benchmark['task_description']}")
            >>> for skill in benchmark["skills_tested"][:3]:
            ...     print(f"  - {skill['name']}: {skill['relevance_score']}")
        """
        response = self._client.get(f"/benchmarks/{input_id}")
        return self._handle_response(response)
