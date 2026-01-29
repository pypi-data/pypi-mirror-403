# Reliably using Gemini's 1M token context through LiteLLM

Google's 503 "model overloaded" errors on large-context Gemini requests stem from **shared infrastructure contention**, not hard quota violations—the error indicates temporary resource scarcity rather than exceeding stated limits. The most effective solutions combine context caching (90% cost reduction and fewer errors), multiple API key rotation, the global Vertex AI endpoint, and aggressive retry configuration with fallbacks to Google AI Studio.

**Gemini 3 Pro** launched November 18, 2025, and remains in **preview status** with the model string `gemini-3-pro-preview`. The preview designation means limited compute resources and more susceptibility to capacity constraints than GA models like Gemini 2.5 Pro.

## Understanding why 503 errors occur below stated limits

The 1M token context window is a **model capability limit**, not a capacity guarantee. Vertex AI uses a dynamic shared quota system where actual available capacity varies based on real-time demand across all customers. Large context requests consume disproportionately more compute resources, making them the first to be rejected when infrastructure is under load.

Three factors compound the problem for large contexts. First, **processing time correlation**: requests exceeding ~500K tokens take significantly longer to process, increasing the probability of hitting resource constraints mid-execution. Second, **preview model limitations**: Gemini 3 Pro's preview cluster has reduced scale and priority scheduling that favors paying customers on GA models. Third, **token bucket rate limiting**: even single large requests can deplete the instantaneous capacity allocation regardless of per-minute averages.

Google's internal data, shared in a Gemini CLI GitHub discussion, revealed that their tools perform better when using a **smaller share of the overall context window**—they reduced their compression threshold from 70% to 20% of context capacity to improve reliability.

## Vertex AI versus Google AI Studio for large contexts

**Vertex AI is the correct choice for production** large-context workloads, despite both platforms accessing identical models. The key differentiator is Provisioned Throughput—dedicated capacity with SLA guarantees that eliminates shared resource contention entirely.

| Feature | Google AI Studio | Vertex AI |
|---------|-----------------|-----------|
| SLA guarantee | None | **99.5% uptime** |
| Provisioned Throughput | Not available | **Available** |
| Free tier | Very limited (5 RPM for Pro) | $300 credit |
| Data privacy | Free tier data trains models | Data never used for training |
| Quota increases | Limited options | Request increases + custom tiers |
| Enterprise security | Basic | VPC-SC, CMEK, compliance |

Standard PayGo rate limits scale by spending tier. Gemini Pro models get **500K TPM at Tier 1** ($10-250/30 days), **1M TPM at Tier 2** ($250-2000), and **2M TPM at Tier 3** (>$2000). The system limit of 30,000 RPM per model per region is fixed.

**Critical recommendation**: Use the **global endpoint** (`location=global`) for large context requests. It routes to the region with most available capacity and accesses a larger multi-region shared pool, significantly reducing 503 errors.

## Correct LiteLLM model strings and configuration

For Gemini 3 Pro, use these model strings:

```python
# Vertex AI (enterprise, SLA-backed)
model = "vertex_ai/gemini-3-pro-preview"

# Google AI Studio (simpler auth, no SLA)  
model = "gemini/gemini-3-pro-preview"
```

The `vertex_ai/` prefix requires GCP credentials with `vertex_project` and `vertex_location` parameters. The `gemini/` prefix requires only a `GEMINI_API_KEY` environment variable.

**Essential configuration for large context reliability**:

```yaml
model_list:
  - model_name: gemini-3-pro
    litellm_params:
      model: vertex_ai/gemini-3-pro-preview
      vertex_project: "your-project-id"
      vertex_location: "global"  # Critical: use global endpoint
      timeout: 900               # 15 minutes for large contexts
      stream_timeout: 60         # 1 minute for first chunk
      
  - model_name: gemini-3-pro-fallback
    litellm_params:
      model: gemini/gemini-3-pro-preview  # Different infrastructure
      api_key: os.environ/GEMINI_API_KEY
      timeout: 900

litellm_settings:
  num_retries: 5
  request_timeout: 900
  fallbacks: [{"gemini-3-pro": ["gemini-3-pro-fallback"]}]
  allowed_fails: 3
  cooldown_time: 30

router_settings:
  enable_pre_call_checks: true  # Validates context window before sending
  retry_policy:
    ServiceUnavailableErrorRetries: 6  # Key for 503 errors
    TimeoutErrorRetries: 5
    RateLimitErrorRetries: 5
```

The fallback from Vertex AI to Google AI Studio is particularly effective because they run on **separate infrastructure**—when Vertex is overloaded, AI Studio may have capacity.

## Working solutions developers report for production

**Context caching** is the highest-impact solution. It reduces compute load per request dramatically and cuts costs by 90% on cached tokens. The minimum cache size is 32,768 tokens, with TTL from 1 minute to 7 days:

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])

# Cache large document once
cache = client.caches.create(
    model="models/gemini-2.5-pro",  # Use versioned model
    config=types.CreateCachedContentConfig(
        display_name="knowledge_base",
        contents=[large_document],
        ttl="3600s"
    )
)

# Subsequent requests reference cache
response = client.models.generate_content(
    model="models/gemini-2.5-pro",
    contents="Query about the document",
    config=types.GenerateContentConfig(cached_content=cache.name)
)
```

**Multi-API-key rotation** multiplies your effective rate limits. LiteLLM supports this natively:

```yaml
model_list:
  - model_name: gemini/*
    litellm_params:
      model: gemini/*
      api_key: os.environ/GEMINI_API_KEY_1
  - model_name: gemini/*
    litellm_params:
      model: gemini/*
      api_key: os.environ/GEMINI_API_KEY_2
  - model_name: gemini/*
    litellm_params:
      model: gemini/*
      api_key: os.environ/GEMINI_API_KEY_3

router_settings:
  routing_strategy: usage-based-routing-v2
```

**Multi-region routing** for Vertex AI distributes load across regional quotas:

```python
VERTEX_REGIONS = ["us-central1", "us-east1", "us-west1", "europe-west4"]

response = completion(
    model="vertex_ai/gemini-3-pro-preview",
    vertex_project="your-project",
    vertex_location=VERTEX_REGIONS[request_count % len(VERTEX_REGIONS)],
    messages=[...]
)
```

## Regional considerations and quotas

Quotas are **identical across all regions** for Standard PayGo, but actual available capacity varies by region and time. **us-central1** typically has highest capacity in the US; **europe-west4** is the primary European region.

For Gemini 3 Pro specifically, only the **global endpoint** is supported—there's no regional endpoint option during preview. This is actually advantageous since global routing automatically finds available capacity.

To request quota increases: navigate to **IAM & Admin > Quotas** in Google Cloud Console, filter for `aiplatform.googleapis.com/generate_content_requests_per_minute_per_project_per_base_model`, and submit an increase request.

For mission-critical workloads, **Provisioned Throughput** eliminates 503 errors entirely within your provisioned allocation. Commitment terms range from 1 week to 1 year, with throughput measured in GSUs (tokens per second). This is the only way to guarantee capacity for large-context production workloads.

## Conclusion

The path to reliable million-token context usage requires accepting that 503 errors are **inherent to shared infrastructure**, not bugs to eliminate. The winning strategy combines multiple defenses: use the global Vertex AI endpoint, configure aggressive retries with Vertex-to-AI-Studio fallbacks, implement context caching for repeated large documents, rotate multiple API keys, and consider Provisioned Throughput for guaranteed capacity. Gemini 3 Pro's preview status makes it more susceptible to capacity issues than Gemini 2.5 Pro, so production systems should use 2.5 Pro as a fallback until 3 Pro reaches GA.
