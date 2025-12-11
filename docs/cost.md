## KNBS Statistical Chatbot – Cloud Deployment Options & Costs (Dec 2025)

> **Important:** All costs below are **estimates** based on current public pricing (Dec 2025) and an assumed usage of **1,000–10,000 queries per month**, with about **1,000 tokens** (question + answer) per query. Actual costs will vary with real usage and future price changes.
>
> For technical details on how token usage is calculated and how to tune it, see [`docs/architecture/token-usage-guide.md`](architecture/token-usage-guide.md).

### 1. Summary at a Glance

**Assumptions**

- Queries/month: **1,000–10,000** (still being refined).
    
- Each query uses ~**1,000 tokens** (prompt + answer). See [Token Usage Guide](architecture/token-usage-guide.md) for how this is calculated.
    
- Exchange rate: **1 USD ≈ 130 KSh** (2025 average). [Exchange Rates+1](https://www.exchange-rates.org/exchange-rate-history/usd-kes-2025?utm_source=chatgpt.com)
    

|Option|Description|Typical Monthly Cost at 1k–10k queries|Notes|
|---|---|---|---|
|**1 (Recommended)**|**Cloud API LLM + existing KNBS server** (RAG: vector search on KNBS docs + hosted LLM like GPT-4o mini / Claude Haiku / Mistral Medium)|**≈ $0.3–$11/month** (≈ **KSh 40–1,400**) in API usage, plus a small cost for the existing VM|No new hardware. Fast responses. Simple to deploy and scale.|
|**2**|**Self-hosted open-source model on cloud GPU** (e.g. Llama/Mistral on rented GPU VM)|**≈ $400–$1,000+ per GPU/month** if kept running 24/7 (≈ **KSh 50,000–130,000+**) [Vantage Instances+2lambda.ai+2](https://instances.vantage.sh/aws/ec2/g4dn.xlarge?utm_source=chatgpt.com)|Higher fixed cost, needs ML/DevOps expertise, justified only at very high usage or strict privacy requirements.|
|**3**|**On-premises GPU server(s) at KNBS**|**One-off $8,000–$20,000+** (≈ **KSh 1.0–2.6 million**) for suitable hardware, plus ongoing power & maintenance [lambda.ai+1](https://lambda.ai/pricing?utm_source=chatgpt.com)|Significant capex and IT burden; only makes sense if cloud is not allowed or if usage becomes very large and steady.|

Given KNBS’s **public data**, **modest expected usage**, and **current infrastructure**, **Option 1 (cloud API)** is by far the most practical and cost-effective.

---

## 2. Recommended: Option 1 – Cloud API LLM (Managed Service)

### How it works

- KNBS’s existing **StatsChat server** (1 vCPU, 16GB RAM, no GPU) hosts:
    
    - The **web/app layer** (chat UI or API).
        
    - The **RAG pipeline**: semantic search over KNBS PDFs, using embeddings and a local/managed vector database.
        
- For each user question:
    
    1. StatsChat retrieves the most relevant text snippets from KNBS publications.
        
    2. It sends the **question + snippets** to a **cloud-hosted LLM** (via API).
        
    3. The LLM returns an answer grounded in those snippets.
        

KNBS has already tested both approaches:

- Running **Mistral 7B locally on that VM** (no GPU) works but takes **3–5 minutes per answer** – far too slow for real users.
    
- Calling a **cloud LLM API from the same server** returns answers that are **almost instantaneous**, demonstrating that performance is excellent with Option 1 on existing hardware.
    

### Why it fits KNBS now

- **Data is public**: We are using published KNBS statistics, not confidential microdata. Sending small text snippets to a reputable LLM provider (OpenAI, Anthropic, Mistral, etc.) is acceptable under current assumptions.
    
- **Usage is modest**: 1k–10k queries/month is relatively low. At this scale, a pay-per-token model is **much cheaper** than renting or buying GPUs.
    
- **No hardware changes**: The current KNBS server is **already sufficient** for hosting the RAG layer and calling cloud APIs. Staff laptops remain unchanged.
    
- **Fast to implement**: This approach mainly requires:
    
    - Wiring the existing RAG pipeline to a cloud LLM API.
        
    - Adding monitoring/logging.
        
    - Setting sensible limits (max answer length, rate limits).
        

### Updated 2025 pricing – mid-tier models

Below are **illustrative mid-tier models** that are well-suited to StatsChat’s needs. Costs assume **~1,000 tokens per query**, split roughly between prompt and answer:

1. **OpenAI GPT-4o mini**
    
    - Pricing: **$0.15 per 1M input tokens**, **$0.60 per 1M output tokens**. [OpenAI Platform+1](https://platform.openai.com/docs/pricing?utm_source=chatgpt.com)
        
    - Rough cost at 1k queries (≈700k input, 300k output tokens):
        
        - Input: 0.7M × $0.15 ≈ **$0.11**
            
        - Output: 0.3M × $0.60 ≈ **$0.18**
            
        - **Total ≈ $0.30/month** (≈ **KSh 40**).
            
    - At 10k queries: ≈ **$3/month** (≈ **KSh 400**).
        
2. **Anthropic Claude Haiku 4.5**
    
    - Pricing: **$1 per 1M input tokens**, **$1.25 per 1M output tokens**. [Claude+1](https://platform.claude.com/docs/en/about-claude/pricing?utm_source=chatgpt.com)
        
    - 1k queries (same token assumption):
        
        - Input: 0.7M × $1 ≈ **$0.70**
            
        - Output: 0.3M × $1.25 ≈ **$0.38**
            
        - **Total ≈ $1.1/month** (≈ **KSh 140**).
            
    - At 10k queries: ≈ **$11/month** (≈ **KSh 1,400**).
        
3. **Mistral Medium 3**
    
    - Pricing: **$0.40 per 1M input tokens**, **$2.00 per 1M output tokens**. [pricepertoken.com](https://pricepertoken.com/pricing-page/model/mistral-ai-mistral-medium-3?utm_source=chatgpt.com)
        
    - 1k queries:
        
        - Input: 0.7M × $0.40 ≈ **$0.28**
            
        - Output: 0.3M × $2.00 ≈ **$0.60**
            
        - **Total ≈ $0.9/month** (≈ **KSh 120**).
            
    - 10k queries: ≈ **$9/month** (≈ **KSh 1,200**).
        

> **Overall indicative range:** Across these mid-tier options, the LLM API usage cost for **1,000–10,000 queries/month** comes out around **$0.3–$11/month** (≈ **KSh 40–1,400**). Even with buffers for variability, we can safely say **“on the order of a few dollars per month”** at the current expected traffic.


### Budget and buffer for Option 1

To avoid having to return for extra approvals if:

- actual usage is higher than expected,
- answers are slightly longer than assumed, or
- we occasionally use a more expensive model for complex queries,

we recommend KNBS **provisionally allocate a higher monthly ceiling for LLM API costs**:

> **Recommendation:** For Year 1, budget **up to USD 100 per month (≈ KSh 13,000)** for LLM API charges under Option 1.

In practice, based on current assumptions, **actual spend is expected to be well below this**, but the higher budget:

- Provides comfortable headroom for growth and experimentation.
    
- Allows occasional use of more capable (higher-priced) models if needed.
    
- Avoids repeated approvals for small increases.
    

We also recommend:

- Configuring **provider-side spending limits and alerts** so that monthly costs cannot exceed the agreed cap without explicit action.
    
- Reviewing real usage and spend after 3–6 months to decide whether to **reduce or adjust** the budget.
### Higher-tier models (for completeness)

- Providers also offer **flagship models** (e.g. OpenAI GPT-5.1, Anthropic Sonnet/Opus), typically at **$5–$25 per 1M tokens or more** depending on model and direction (input vs output). [OpenAI Platform+1](https://platform.openai.com/docs/pricing?utm_source=chatgpt.com)
    
- These can give **better reasoning** on very complex or ambiguous questions, but for factual Q&A over KNBS documents, **mid-tier models are usually sufficient** once RAG is in place.
    
- Recommendation: **start with a mid-tier model** (e.g. GPT-4o mini or Claude Haiku) and only consider upgrading to a flagship model if a later evaluation shows clear, business-critical quality gains that justify 10–20× higher token prices.
    

---

## 3. Option 2 – Self-Hosted Open-Source Model on Cloud GPU

In this model, KNBS would:

- Rent one or more **GPU instances** from a cloud provider (e.g. AWS, Azure, GPU-focused clouds).
    
- Deploy an open-source model (e.g. Llama, Mistral) on that GPU.
    
- Run the chatbot via this hosted model instead of a managed API.
    

### Cost and implications

- **GPU cost:**
    
    - Representative prices (Dec 2025):
        
        - AWS **g4dn.xlarge** (NVIDIA T4): **≈$0.53/hour**. [Vantage Instances+1](https://instances.vantage.sh/aws/ec2/g4dn.xlarge?utm_source=chatgpt.com)
            
        - AWS **g5.xlarge** (NVIDIA A10G): **≈$1.01/hour**. [Vantage Instances+1](https://instances.vantage.sh/aws/ec2/g5.xlarge?utm_source=chatgpt.com)
            
        - A100 40–80GB on specialist GPU clouds: around **$1.3–$1.8/hour**. [lambda.ai+1](https://lambda.ai/pricing?utm_source=chatgpt.com)
            
    - Running **24/7 for a month (~720 hours)** gives a ballpark of **$400–$1,000+ per GPU/month** (≈ **KSh 50,000–130,000+**), _before_ adding storage and any additional VMs.
        
- **Fixed vs variable cost:**
    
    - Unlike Option 1, this cost is **paid even if very few queries are made**.
        
    - At 1k–10k queries/month, this results in a much **higher cost per query** than the few dollars/month we’d pay for API usage.
        
- **Complexity:**
    
    - KNBS would need ML/DevOps skills to:
        
        - Deploy, monitor, and update the model.
            
        - Manage scaling, security, and uptime.
            
    - Bugs or downtime would be KNBS’s responsibility.
        

### When might this make sense?

- **Much higher usage:** If StatsChat eventually serves **hundreds of thousands or millions of queries per month**, GPU hosting could become financially attractive, especially if we fully utilize the hardware.
    
- **Stricter data/privacy needs:** If in future KNBS must ensure **all inference stays inside KNBS’s own cloud tenancy**, a self-hosted model (or Azure OpenAI in a private VNet) might become preferable.
    

Given today’s situation (public data, modest traffic, limited ML infra capacity), Option 2 is **not recommended** as the initial deployment model.

---

## 4. Option 3 – On-Premises GPU Server at KNBS

This option means purchasing a physical server with one or more high-end GPUs and running the model in KNBS’s own data centre.

Typical spec for an LLM-capable box:

- 1× or 2× data-centre GPUs (e.g. NVIDIA L40S, A100, H100).
    
- 64–128GB RAM, multi-core CPU, high-speed NVMe storage.
    

Indicative costs:

- **Capex:** Roughly **$8,000–$20,000+** (≈ **KSh 1.0–2.6 million**), depending on GPU and configuration. [lambda.ai+1](https://lambda.ai/pricing?utm_source=chatgpt.com)
    
- **Opex:** Electricity, cooling, spares, and staff time to manage the hardware.
    

As with Option 2, this only becomes attractive if **cloud is not allowed** or if we reach **very high steady usage** and have strong in-house infra capacity. For KNBS right now, on-premises would be **over-kill and high-risk**, so we keep it as a _future contingency_ rather than a realistic near-term plan.

---

## 5. Data Privacy and Future Flexibility

- **Current position:** We are using **public statistical publications**; no microdata or PII is sent to the model. This makes a cloud API approach acceptable and simple.
    
- **If privacy requirements change:**
    
    - We can switch to **enterprise offerings** like **Azure OpenAI Service**, which support:
        
        - Data residency and private networking (e.g. VNet / Private Link).
            
        - Stronger contractual and technical controls on data use. [OpenAI Platform+1](https://platform.openai.com/docs/pricing?utm_source=chatgpt.com)
            
    - Or we can revisit **Options 2/3** (self-hosted LLM in cloud or on-prem).
        

The proposed architecture (RAG + modular LLM client) keeps this flexible: changing models or deployment mode later is primarily a configuration and integration task, not a full rewrite.

---

## 6. Conclusion

- For KNBS’s **current needs** – public data, 1k–10k queries/month, existing small server – **Option 1 (cloud API LLM)** is clearly the best fit:
    
    - **Very low ongoing cost:** around **$0.3–$11/month** (≈ **KSh 40–1,400**) in LLM usage at expected volumes, plus a small cost for the existing server.
        
    - **No new hardware or GPU investment**.
        
    - **Fast and responsive** (unlike local CPU experiments).
        
    - **Simple to deploy and operate**.
        
- **Options 2 and 3** have their place in specific future scenarios (much higher traffic or stricter data policies), but they are **not cost-effective or necessary today**.
    

> **Reminder:** These figures are **estimates**, not guarantees. Final costs will depend on the chosen provider, the exact model, and real usage. However, they are sufficient to show that a cloud API approach gives KNBS a **low-risk, low-cost path** to deploying a useful statistical chatbot now, with plenty of room to adjust if needs change later.