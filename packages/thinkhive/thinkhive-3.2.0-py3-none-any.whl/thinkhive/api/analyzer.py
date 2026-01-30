"""
Analyzer API Client
User-selected trace analysis with cost estimation and smart sampling

Key features:
- User-selected trace analysis
- Cost estimation before execution
- Smart sampling strategies
- Root cause analysis by layer
- Pattern aggregation across traces
"""

from typing import Optional, List, Dict, Any, Literal
from datetime import datetime
from ..client import api_request


class AnalyzerClient:
    """
    Analyzer API client

    User-selected trace analysis with cost estimation and smart sampling.
    """

    def analyze(
        self,
        trace_ids: List[str],
        tier: Optional[Literal["fast", "standard", "deep"]] = None,
        include_root_cause: bool = True,
        include_layers: bool = True,
    ) -> Dict[str, Any]:
        """
        Analyze specific traces (user-selected)

        Args:
            trace_ids: List of trace IDs to analyze (max 100)
            tier: Analysis tier (fast, standard, deep)
            include_root_cause: Include root cause analysis
            include_layers: Include layer classification

        Returns:
            Analysis results with summary
        """
        data = {
            "traceIds": trace_ids,
            "options": {
                "tier": tier,
                "includeRootCause": include_root_cause,
                "includeLayers": include_layers,
            },
        }

        response = api_request("POST", "/analyzer/analyze", body=data, api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response

    def analyze_window(
        self,
        agent_id: str,
        start_date: datetime,
        end_date: datetime,
        outcomes: Optional[List[Literal["failure", "error", "success"]]] = None,
        min_severity: Optional[Literal["low", "medium", "high", "critical"]] = None,
        sampling_strategy: Literal["all", "failures_only", "smart", "random"] = "smart",
        sample_percent: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Analyze traces by time window with optional sampling

        Args:
            agent_id: The agent ID
            start_date: Start of time window
            end_date: End of time window
            outcomes: Filter by outcomes
            min_severity: Minimum severity to include
            sampling_strategy: How to sample traces
            sample_percent: Percentage of traces to sample (for random strategy)

        Returns:
            Analysis results with summary
        """
        data = {
            "agentId": agent_id,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
        }

        if outcomes or min_severity:
            data["filters"] = {}
            if outcomes:
                data["filters"]["outcomes"] = outcomes
            if min_severity:
                data["filters"]["minSeverity"] = min_severity

        data["sampling"] = {"strategy": sampling_strategy}
        if sample_percent:
            data["sampling"]["samplePercent"] = sample_percent

        response = api_request("POST", "/analyzer/analyze-window", body=data, api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response

    def estimate_cost(
        self,
        tier: Literal["fast", "standard", "deep"],
        trace_ids: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Estimate cost before running analysis

        Args:
            tier: Analysis tier
            trace_ids: Specific traces to estimate
            agent_id: Agent ID (with date range)
            start_date: Start of time window
            end_date: End of time window

        Returns:
            Cost estimate including tokens, cost, and credits
        """
        data = {"tier": tier}
        if trace_ids:
            data["traceIds"] = trace_ids
        if agent_id:
            data["agentId"] = agent_id
        if start_date:
            data["startDate"] = start_date.isoformat()
        if end_date:
            data["endDate"] = end_date.isoformat()

        response = api_request("POST", "/analyzer/estimate-cost", body=data, api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response

    def get(self, trace_id: str) -> Dict[str, Any]:
        """
        Get analysis results for a specific trace

        Args:
            trace_id: The trace ID

        Returns:
            Analysis results
        """
        response = api_request("GET", f"/analyzer/{trace_id}", api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response

    def summarize(
        self,
        analysis_ids: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        Aggregate insights across multiple analyzed traces

        Args:
            analysis_ids: List of analysis IDs to aggregate
            agent_id: Agent ID (with date range)
            start_date: Start of time window
            end_date: End of time window

        Returns:
            Aggregated insights including patterns and recommendations
        """
        data = {}
        if analysis_ids:
            data["analysisIds"] = analysis_ids
        if agent_id:
            data["agentId"] = agent_id
        if start_date:
            data["startDate"] = start_date.isoformat()
        if end_date:
            data["endDate"] = end_date.isoformat()

        response = api_request("POST", "/analyzer/summarize", body=data, api_version="v2")
        return response.get("data", response) if isinstance(response, dict) else response


# Singleton instance
analyzer = AnalyzerClient()
