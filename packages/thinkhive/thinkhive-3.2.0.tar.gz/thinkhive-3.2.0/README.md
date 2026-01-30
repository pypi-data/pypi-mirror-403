# ThinkHive Python SDK

OpenTelemetry-based observability SDK for AI agents supporting 25 trace formats including LangSmith, Langfuse, Opik, Braintrust, Datadog, MLflow, and more.

## Installation

```bash
pip install thinkhive
```

## Quick Start

```python
import thinkhive

# Initialize SDK
thinkhive.init(
    api_key="your-api-key",  # or set THINKHIVE_API_KEY
    service_name="my-ai-agent"
)

# Trace LLM calls
@thinkhive.trace_llm(model_name="gpt-4", provider="openai")
def call_llm(prompt):
    response = openai.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    return response

# Trace retrieval operations
@thinkhive.trace_retrieval()
def search_documents(query):
    results = vector_db.search(query)
    return results

# Trace tool calls
@thinkhive.trace_tool(tool_name="web_search")
def search_web(query):
    return requests.get(f"https://api.example.com/search?q={query}")
```

## HTTP-Based Trace Creation

For direct trace creation with evaluation control, use the traces API:

```python
from thinkhive import traces

# Create trace with automatic evaluation
result = traces.create(
    agent_id="agent-123",
    user_message="What is the return policy?",
    agent_response="Items can be returned within 30 days.",
    outcome="success",
    run_evaluation=True  # Force evaluation on this trace
)

print(f"Trace ID: {result.id}")
if result.evaluation_queued:
    print("Evaluation will run asynchronously")

# Skip evaluation even if agent has auto_evaluate enabled
result = traces.create(
    agent_id="agent-123",
    user_message="Hello!",
    agent_response="Hi there!",
    run_evaluation=False
)

# Use agent's default auto_evaluate setting
result = traces.create(
    agent_id="agent-123",
    user_message="What are your hours?",
    agent_response="We are open 9 AM to 5 PM."
    # run_evaluation omitted - uses agent's setting
)
```

### run_evaluation Parameter

The `run_evaluation` parameter controls whether traces are automatically evaluated:

| Value | Behavior |
|-------|----------|
| `True` | Force evaluation on this trace |
| `False` | Skip evaluation even if agent has auto_evaluate |
| `None` (default) | Use agent's auto_evaluate setting |

## Environment Variables

- `THINKHIVE_API_KEY`: Your ThinkHive API key
- `THINKHIVE_AGENT_ID`: Your agent ID (alternative to API key)

## Issues API (Clustered Failure Patterns)

The Issues API provides access to clustered failure patterns:

```python
from thinkhive import issues

# List issues for an agent
all_issues = issues.list(agent_id="agent-123")

# Get a specific issue
issue = issues.get(issue_id="issue-456")

# Create a new issue
new_issue = issues.create(
    agent_id="agent-123",
    title="Refund policy confusion",
    type="hallucination",
    severity="high"
)

# Update an issue
issues.update(
    issue_id="issue-456",
    status="in_progress",
    assignee="developer@example.com"
)

# Get fixes for an issue
fixes = issues.get_fixes(issue_id="issue-456")
```

## Analyzer API (User-Selected Analysis)

The Analyzer API provides user-selected trace analysis with cost estimation:

```python
from thinkhive import analyzer

# Estimate cost before running analysis
estimate = analyzer.estimate_cost(
    trace_ids=["trace-1", "trace-2"],
    tier="standard"
)
print(f"Estimated cost: ${estimate['estimated_cost']}")

# Analyze specific traces
analysis = analyzer.analyze(
    trace_ids=["trace-1", "trace-2"],
    tier="standard",
    include_root_cause=True
)

# Get aggregated insights
summary = analyzer.summarize(
    agent_id="agent-123",
    start_date="2024-01-01",
    end_date="2024-01-31"
)
```

## Business Metrics API

The Business Metrics API provides industry-driven metrics with historical tracking and external data support:

```python
from thinkhive.api import business_metrics

# Get current metric value with status
metric = business_metrics.get_current("agent-123", metric_name="Deflection Rate")
print(f"{metric.metric_name}: {metric.value_formatted}")

if metric.status == "insufficient_data":
    needed = metric.min_trace_threshold - metric.trace_count
    print(f"Need {needed} more traces")

# Get historical data for graphing
history = business_metrics.get_history(
    "agent-123",
    "Deflection Rate",
    start_date="2024-01-01T00:00:00Z",
    end_date="2024-01-31T23:59:59Z",
    granularity="daily"
)

print(f"{len(history.data_points)} data points")
print(f"Change: {history.summary.change_percent}%")

# Record external metric values (from CRM, surveys, etc.)
result = business_metrics.record_value(
    "agent-123",
    metric_name="CSAT/NPS",
    value=4.5,
    period_start="2024-01-01T00:00:00Z",
    period_end="2024-01-07T23:59:59Z",
    unit="score",
    source="survey_system",
    source_details={"survey_id": "survey_456", "response_count": 150}
)
print(f"Recorded: {result.id}")
```

### Metric Status Types

| Status | Description |
|--------|-------------|
| `ready` | Metric calculated and ready to display |
| `insufficient_data` | Need more traces before calculation |
| `awaiting_external` | External data source not connected |
| `stale` | Data is older than expected |

### Helper Functions

```python
from thinkhive import (
    is_metric_ready,
    needs_more_traces,
    awaiting_external_data,
    is_metric_stale,
    get_metric_status_message,
    format_metric_value
)

# Check metric status
if is_metric_ready(metric):
    print(f"Value: {metric.value_formatted}")
elif needs_more_traces(metric):
    print(get_metric_status_message(metric))
```

## ROI Analytics API

```python
from thinkhive.api import roi_analytics

# Get ROI summary
summary = roi_analytics.get_summary(
    start_date="2024-01-01T00:00:00Z",
    end_date="2024-01-31T23:59:59Z",
    agent_id="agent-123"
)
print(f"Revenue protected: ${summary.revenue_protected}")

# Get trends over time
trends = roi_analytics.get_trends(agent_id="agent-123")
for day in trends:
    print(f"{day.date}: {day.success_rate}% success")

# Calculate impact for specific data
impact = roi_analytics.calculate(
    user_message="Help me cancel my subscription",
    agent_response="I can help with that...",
    industry_config={"industry": "saas", "avg_customer_ltv": 10000}
)
```

## API Reference

| Module | Description | API Version |
|--------|-------------|-------------|
| `traces` | Create and manage traces | v1 |
| `issues` | Clustered failure patterns | v2 |
| `analyzer` | User-selected trace analysis | v2 |
| `business_metrics` | Industry-driven metrics with history | v3 |
| `roi_analytics` | Business ROI and financial impact | v1 |
| `runs` | Run-centric trace management | v3 |
| `claims` | Facts vs inferences management | v3 |
| `calibration` | Prediction accuracy tracking | v3 |

## License

MIT
