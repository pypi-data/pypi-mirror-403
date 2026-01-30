"""
Cubit API Asynchronous Client.

An async interface to the Cubit AI Job Vulnerability API.
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


class CubitAsyncClient:
    """
    Asynchronous client for the Cubit API.
    
    Example:
        >>> from cubit import CubitAsyncClient
        >>> async with CubitAsyncClient("cubit_xxxxxxxxxxxx") as client:
        ...     jobs = await client.search_jobs("software developer")
        ...     print(jobs["jobs"][0]["title"])
    """
    
    DEFAULT_BASE_URL = "https://api.maidenlabs.tools"
    
    def __init__(
        self,
        api_key: str,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the async Cubit API client.
        
        Args:
            api_key: Your Cubit API key (starts with 'cubit_')
            base_url: Override the default API URL (for testing/staging)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        
        self._client = httpx.AsyncClient(
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
    
    async def close(self) -> None:
        """Close the HTTP client connection."""
        await self._client.aclose()
    
    async def __aenter__(self) -> "CubitAsyncClient":
        return self
    
    async def __aexit__(self, *args) -> None:
        await self.close()
    
    # =========================================================================
    # HEALTH & UTILITY
    # =========================================================================
    
    async def health(self) -> HealthResponse:
        """Check API health status."""
        response = await self._client.get("/health")
        return self._handle_response(response)
    
    async def root(self) -> RootResponse:
        """Root endpoint health check."""
        response = await self._client.get("/")
        return self._handle_response(response)
    
    async def me(self) -> MeResponse:
        """Get information about the current API key."""
        response = await self._client.get("/me")
        return self._handle_response(response)
    
    async def schema(self) -> SchemaResponse:
        """Get data schema and field definitions."""
        response = await self._client.get("/schema")
        return self._handle_response(response)
    
    async def stats_overview(self) -> StatsOverviewResponse:
        """Get aggregate statistics about the dataset."""
        response = await self._client.get("/stats/overview")
        return self._handle_response(response)
    
    # =========================================================================
    # JOBS - Search
    # =========================================================================
    
    async def search_jobs(
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
        """
        params = {"q": query, "limit": limit}
        if exposure_threshold is not None:
            params["exposure_threshold"] = exposure_threshold
        if imperative_threshold is not None:
            params["imperative_threshold"] = imperative_threshold
        
        response = await self._client.get("/jobs/search", params=params)
        return self._handle_response(response)
    
    async def search_jobs_semantic(
        self,
        query: str,
        limit: int = 10,
        search_scope: str = "jobs",
    ) -> SemanticSearchResponse:
        """
        Search for jobs using semantic similarity.
        
        Requires Builder or Enterprise tier.
        
        Args:
            query: Natural language query
            limit: Max number of results (1-50)
            search_scope: "jobs", "tasks", or "both"
        
        Returns:
            SemanticSearchResponse with relevance-scored jobs
        """
        response = await self._client.get(
            "/jobs/search/semantic",
            params={"q": query, "limit": limit, "search_scope": search_scope},
        )
        return self._handle_response(response)
    
    # =========================================================================
    # JOBS - Profile
    # =========================================================================
    
    async def get_job(
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
            JobProfile with scores and classification
        """
        params = {}
        if exposure_threshold is not None:
            params["exposure_threshold"] = exposure_threshold
        if imperative_threshold is not None:
            params["imperative_threshold"] = imperative_threshold
        
        response = await self._client.get(f"/jobs/{soc_code}", params=params if params else None)
        return self._handle_response(response)
    
    async def get_job_tasks(
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
        
        response = await self._client.get(f"/jobs/{soc_code}/tasks", params=params)
        return self._handle_response(response)
    
    async def get_job_requirements(
        self,
        soc_code: str,
        type: str = "all",
        source: str = "diagnostics",
        limit: int = 20,
    ) -> RequirementDiagnosticsResponse:
        """
        Get requirement diagnostics for a job.
        
        Requires Builder or Enterprise tier.
        """
        response = await self._client.get(
            f"/jobs/{soc_code}/requirements",
            params={"type": type, "source": source, "limit": limit},
        )
        return self._handle_response(response)
    
    async def explain_job(self, soc_code: str) -> JobExplainResponse:
        """
        Get methodology explanation for a job's scores.
        
        Requires Builder or Enterprise tier.
        """
        response = await self._client.get(f"/jobs/{soc_code}/explain")
        return self._handle_response(response)
    
    async def compare_jobs(
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
        """
        socs_str = ",".join(soc_codes)
        params = {"socs": socs_str}
        if exposure_threshold is not None:
            params["exposure_threshold"] = exposure_threshold
        if imperative_threshold is not None:
            params["imperative_threshold"] = imperative_threshold
        
        response = await self._client.get("/jobs/compare", params=params)
        return self._handle_response(response)
    
    # =========================================================================
    # SKILLS
    # =========================================================================
    
    async def list_skills(
        self,
        type: str = "all",
        sort_by: str = "ai_resilience_score",
        limit: int = 50,
    ) -> RequirementListResponse:
        """List all skills/abilities/knowledge with AI resilience scores."""
        response = await self._client.get(
            "/skills",
            params={"type": type, "sort_by": sort_by, "limit": limit},
        )
        return self._handle_response(response)
    
    async def search_skills_semantic(
        self,
        query: str,
        limit: int = 10,
    ) -> SkillSearchResponse:
        """
        Search for skills using semantic similarity.
        
        Requires Builder or Enterprise tier.
        """
        response = await self._client.get(
            "/skills/search/semantic",
            params={"q": query, "limit": limit},
        )
        return self._handle_response(response)
    
    async def get_skill(self, element_id: str) -> SkillProfile:
        """
        Get detailed profile for a skill.
        
        Requires Builder or Enterprise tier.
        """
        response = await self._client.get(f"/skills/{element_id}")
        return self._handle_response(response)
    
    async def analyze_skill_gap(
        self,
        current_skills: List[str],
        target_job: str,
    ) -> SkillGapResponse:
        """
        Analyze skill gaps for career transition to a target job.
        
        Requires Builder or Enterprise tier.
        """
        response = await self._client.post(
            "/skills/gap",
            json={"current_skills": current_skills, "target_job": target_job},
        )
        return self._handle_response(response)
    
    # =========================================================================
    # REGIONS
    # =========================================================================
    
    async def list_regions(
        self,
        state: Optional[str] = None,
        min_employment: int = 0,
        sort_by: str = "employment",
        limit: int = 50,
    ) -> RegionListResponse:
        """
        List all MSA regions with headline risk metrics.
        
        Requires Builder or Enterprise tier.
        """
        params: Dict[str, Any] = {
            "min_employment": min_employment,
            "sort_by": sort_by,
            "limit": limit,
        }
        if state:
            params["state"] = state
        
        response = await self._client.get("/regions", params=params)
        return self._handle_response(response)
    
    async def get_region(
        self,
        msa_code: str,
        include_jobs: bool = False,
        job_limit: int = 20,
    ) -> RegionDetail:
        """
        Get detailed risk profile for a region.
        
        Requires Builder or Enterprise tier.
        """
        response = await self._client.get(
            f"/regions/{msa_code}",
            params={"include_jobs": include_jobs, "job_limit": job_limit},
        )
        return self._handle_response(response)
    
    # =========================================================================
    # ENTERPRISE - Assessments
    # =========================================================================
    
    async def calculate_custom_score(
        self,
        weights: Dict[str, float],
        jobs: List[str],
        aggregation: str = "weighted_mean",
    ) -> CustomScoreResponse:
        """
        Calculate custom risk scores with your own dimension weights.
        
        Enterprise tier only.
        """
        response = await self._client.post(
            "/assessments/custom-score",
            json={"weights": weights, "jobs": jobs, "aggregation": aggregation},
        )
        return self._handle_response(response)
    
    async def batch_lookup(
        self,
        soc_codes: List[str],
        fields: Optional[List[str]] = None,
        format: str = "json",
    ) -> BatchLookupResponse:
        """
        Retrieve profiles for multiple jobs in a single request.
        
        Enterprise tier only.
        """
        payload: Dict[str, Any] = {"soc_codes": soc_codes, "format": format}
        if fields:
            payload["fields"] = fields
        
        response = await self._client.post("/jobs/batch", json=payload)
        return self._handle_response(response)
    
    async def find_transitions(
        self,
        source_soc: str,
        similarity_threshold: float = 0.7,
        max_results: int = 20,
        filters: Optional[Dict[str, Any]] = None,
    ) -> TransitionResponse:
        """
        Find career transition pathways using skill-based similarity.
        
        Enterprise tier only.
        """
        payload: Dict[str, Any] = {
            "source_soc": source_soc,
            "similarity_threshold": similarity_threshold,
            "max_results": max_results,
        }
        if filters:
            payload["filters"] = filters
        
        response = await self._client.post("/jobs/transitions", json=payload)
        return self._handle_response(response)
    
    # =========================================================================
    # ENTERPRISE - Benchmarks
    # =========================================================================
    
    async def list_benchmarks(
        self,
        skill: Optional[str] = None,
        benchmark: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> BenchmarkListResponse:
        """
        List AI benchmark evaluations with optional filtering.
        
        Enterprise tier only.
        """
        params: Dict[str, Any] = {"limit": limit, "offset": offset}
        if skill:
            params["skill"] = skill
        if benchmark:
            params["benchmark"] = benchmark
        
        response = await self._client.get("/benchmarks", params=params)
        return self._handle_response(response)
    
    async def get_benchmark(self, input_id: str) -> BenchmarkDetailResponse:
        """
        Get detailed information about a specific benchmark.
        
        Enterprise tier only.
        """
        response = await self._client.get(f"/benchmarks/{input_id}")
        return self._handle_response(response)
