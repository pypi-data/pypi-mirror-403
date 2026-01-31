# SDKRouter

Unified Python SDK for AI services with OpenAI compatibility. Access 300+ LLM models through a single interface, plus vision analysis, image generation, audio (TTS/STT with real-time analysis), CDN, URL shortening, and HTML cleaning tools.

## Installation

```bash
pip install sdkrouter
```

## Quick Start

```python
from sdkrouter import SDKRouter, Model

client = SDKRouter(api_key="your-api-key")

# OpenAI-compatible chat completions with Model builder
response = client.chat.completions.create(
    model=Model.cheap(),  # or "openai/gpt-4o-mini" for direct ID
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## Features

### Chat Completions (OpenAI-Compatible)

```python
from sdkrouter import Model

# Non-streaming with smart model
response = client.chat.completions.create(
    model=Model.smart(),
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    max_tokens=500,
)

# Streaming with fast model
for chunk in client.chat.completions.create(
    model=Model.fast(streaming=True),
    messages=[{"role": "user", "content": "Count to 5"}],
    stream=True,
):
    print(chunk.choices[0].delta.content or "", end="")

# Direct model ID still works
response = client.chat.completions.create(
    model="anthropic/claude-sonnet-4",
    messages=[{"role": "user", "content": "Hello!"}],
)
```

### Intent-Based Model Routing

Use the `Model` builder for IDE autocomplete and validation, or raw alias strings:

```python
from sdkrouter import Model

# Model builder (recommended) — IDE autocomplete on methods and kwargs
response = client.chat.completions.create(
    model=Model.cheap(),  # Cheapest available model
    messages=[{"role": "user", "content": "Hello!"}]
)

response = client.chat.completions.create(
    model=Model.smart(),  # Highest quality model
    messages=[{"role": "user", "content": "Write a poem"}]
)

response = client.chat.completions.create(
    model=Model.balanced(),  # Best value (quality/price ratio)
    messages=[{"role": "user", "content": "Summarize this article"}]
)

# Raw string syntax also works
response = client.chat.completions.create(
    model="@cheap",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

#### Available Presets

| Preset | Model Builder | Description |
|--------|---------------|-------------|
| `@cheap` | `Model.cheap()` | Lowest cost models |
| `@budget` | `Model.budget()` | Budget-friendly with decent quality |
| `@standard` | `Model.standard()` | Standard tier |
| `@balanced` | `Model.balanced()` | Best value models |
| `@smart` | `Model.smart()` | Highest quality models |
| `@fast` | `Model.fast()` | Fastest response times |
| `@premium` | `Model.premium()` | Top-tier premium models |

#### Capability Modifiers

Add capabilities with `+modifier` syntax or boolean kwargs:

```python
from sdkrouter import Model

# Cheapest model with vision support
response = client.chat.completions.create(
    model=Model.cheap(vision=True),  # or "@cheap+vision"
    messages=[...]
)

# Best quality model with tool use and long context
response = client.chat.completions.create(
    model=Model.smart(tools=True, long=True),  # or "@smart+tools+long"
    messages=[...]
)

# Balanced model with JSON mode
response = client.chat.completions.create(
    model=Model.balanced(json=True),  # or "@balanced+json"
    messages=[...]
)
```

| Modifier | Kwarg | Description |
|----------|-------|-------------|
| `+vision` | `vision=True` | Requires image input support |
| `+tools` | `tools=True` | Requires function/tool calling |
| `+json` | `json=True` | Requires JSON output mode |
| `+streaming` | `streaming=True` | Requires streaming support |
| `+long` | `long=True` | Requires 100k+ context window |

#### Category Modifiers

Filter by use case categories:

```python
from sdkrouter import Model

# Best coding model
response = client.chat.completions.create(
    model=Model.smart(code=True),  # or "@smart+code"
    messages=[...]
)

# Cheapest reasoning model with vision
response = client.chat.completions.create(
    model=Model.cheap(reasoning=True, vision=True),  # or "@cheap+reasoning+vision"
    messages=[...]
)

# Best value creative model with tools
response = client.chat.completions.create(
    model=Model.balanced(creative=True, tools=True),
    messages=[...]
)
```

| Category | Kwarg | Models optimized for |
|----------|-------|---------------------|
| `+code` | `code=True` | Programming and code generation |
| `+reasoning` | `reasoning=True` | Complex problem solving |
| `+creative` | `creative=True` | Creative writing, storytelling |
| `+analysis` | `analysis=True` | Data analysis, research |
| `+chat` | `chat=True` | Conversational interactions |
| `+agents` | `agents=True` | Tool use and autonomous agents |

#### Escape Hatch

Build aliases from raw strings when needed:

```python
from sdkrouter import Model

# For custom or dynamic combinations
alias = Model.alias("cheap", "vision", "code")  # "@cheap+vision+code"
```

### Structured Output (Pydantic)

Get type-safe responses with automatic JSON schema generation:

```python
from pydantic import BaseModel, Field
from sdkrouter import SDKRouter, Model

class Step(BaseModel):
    explanation: str = Field(description="Explanation of the step")
    result: str = Field(description="Result of this step")

class MathSolution(BaseModel):
    steps: list[Step] = Field(description="Solution steps")
    final_answer: float = Field(description="The final answer")

client = SDKRouter()
result = client.parse(
    model=Model.smart(json=True),
    messages=[
        {"role": "system", "content": "You are a math tutor. Show your work."},
        {"role": "user", "content": "Solve: 3x + 7 = 22"},
    ],
    response_format=MathSolution,
)

solution = result.choices[0].message.parsed
for i, step in enumerate(solution.steps, 1):
    print(f"{i}. {step.explanation} → {step.result}")
print(f"Answer: x = {solution.final_answer}")
```

### Vision Analysis

```python
from pathlib import Path
from sdkrouter import Model

# Analyze from URL
result = client.vision.analyze(
    image_url="https://example.com/image.jpg",
    prompt="Describe this image",
)
print(result.description)
print(f"Cost: ${result.cost_usd:.6f}")

# Analyze with model alias
result = client.vision.analyze(
    image_url="https://example.com/image.jpg",
    prompt="Describe this image",
    model=Model.smart(vision=True),
)

# Analyze from local file (auto-converts to base64)
result = client.vision.analyze(
    image_path=Path("./photo.jpg"),
    prompt="Describe this image",
)
```

#### Quality Tiers

| Tier | Model | Use Case |
|------|-------|----------|
| `fast` | gpt-4o-mini | Quick analysis, lower cost |
| `balanced` | gpt-4o | Default, good quality/cost ratio |
| `best` | claude-sonnet-4 | Highest accuracy |

```python
result = client.vision.analyze(
    image_url="https://example.com/image.jpg",
    model_quality="best",  # fast | balanced | best
)
```

### OCR (Text Extraction)

```python
from pathlib import Path

# OCR from URL
result = client.vision.ocr(
    image_url="https://example.com/document.jpg",
    language_hint="en",  # optional
)
print(result.text)

# OCR from local file (auto-converts to base64)
result = client.vision.ocr(
    image_path=Path("./document.jpg"),
)
```

#### OCR Modes

| Mode | Speed | Accuracy | Use Case |
|------|-------|----------|----------|
| `tiny` | Fastest | Basic | Simple text, receipts |
| `small` | Fast | Good | Standard documents |
| `base` | Medium | High | Default, balanced |
| `maximum` | Slow | Best | Complex layouts, handwriting |

```python
result = client.vision.ocr(
    image_url="https://example.com/document.jpg",
    mode="maximum",  # tiny | small | base | maximum
)
```

### Image Generation

Generate images with AI models:

```python
# Basic generation
result = client.image_gen.generate(
    prompt="A serene mountain landscape at sunset",
)
print(result.image_cdn_url)
print(f"Cost: ${result.cost_usd}")

# With model alias and options
result = client.image_gen.generate(
    prompt="A cute robot playing with a kitten",
    model="@balanced",  # @cheap, @balanced, @smart, @fast
    quality="hd",       # standard, hd
    style="vivid",      # natural, vivid
    size="1024x1024",   # 256x256, 512x512, 1024x1024, 1792x1024, 1024x1792
)

# With negative prompt
result = client.image_gen.generate(
    prompt="A beautiful forest path in autumn",
    negative_prompt="people, buildings, cars, text, watermarks",
)
```

#### Async Generation with Polling

For long-running generation jobs:

```python
# Start async generation
job = client.image_gen.generate_async(
    prompt="A detailed fantasy castle on a floating island",
    model="@balanced",
    quality="hd",
)
print(f"Job queued: {job.job_id}")

# Wait for completion
result = client.image_gen.wait_for_completion(
    job.id,
    timeout=300.0,
    poll_interval=2.0,
)
print(f"Image URL: {result.image_cdn_url}")
```

#### Model Aliases

| Alias | Description |
|-------|-------------|
| `@cheap` | Lowest cost model |
| `@balanced` | Best quality/price ratio |
| `@smart` | Highest quality |
| `@fast` | Fastest generation |

#### Generation History

```python
# List generations
generations = client.image_gen.list()
for gen in generations:
    print(f"{gen.id}: {gen.status} - ${gen.cost_usd}")

# Get generation details
detail = client.image_gen.get(generation_id)
print(detail.image_cdn_url)

# Get available options
options = client.image_gen.options()
print(options.model_aliases)
print(options.quality)
print(options.style)
```

### Audio (TTS & STT)

Text-to-Speech and Speech-to-Text with real-time audio analysis:

```python
from sdkrouter import AudioModel

# Text-to-Speech (buffered, with analysis)
response = client.audio.speech(
    input="Hello! Welcome to SDKRouter.",
    model=AudioModel.cheap(),
    voice="nova",
)
Path("output.mp3").write_bytes(response.audio_bytes)
print(f"Duration: {response.analysis.duration_s}s")
print(f"Frames: {len(response.analysis.frames)}")

# Access per-frame analysis for visualization
for frame in response.analysis.frames[:5]:
    print(f"t={frame.t:.2f}s rms={frame.rms:.3f} db={frame.db:.1f} bands={frame.bands}")
```

#### SSE Streaming TTS (MP3 + Real-time Analysis)

Stream audio with per-chunk analysis frames for real-time playback and visualization:

```python
from sdkrouter import SpeechStreamChunk, SpeechStreamDone

# Default: MP3 chunks + analysis frames
mp3_data = b""
for item in client.audio.speech_stream(
    input="This audio is streamed with real-time analysis.",
    voice="nova",
):
    if isinstance(item, SpeechStreamChunk):
        mp3_data += item.audio_bytes
        for frame in item.analysis:
            print(f"rms={frame.rms:.3f} db={frame.db:.1f}")
    elif isinstance(item, SpeechStreamDone):
        print(f"Done: {item.duration_s}s, format={item.format}")

Path("streamed.mp3").write_bytes(mp3_data)

# Raw PCM streaming (24kHz 16-bit mono)
for item in client.audio.speech_stream(
    input="Raw PCM stream.",
    voice="nova",
    response_format="pcm",
):
    ...
```

#### Speech-to-Text (Transcription)

```python
# Transcribe from bytes or file path
result = client.audio.transcribe(
    file=audio_bytes,           # or Path("audio.mp3")
    model=AudioModel.cheap(),
)
print(result.text)

# Verbose with timing segments
result = client.audio.transcribe(
    file=audio_bytes,
    response_format="verbose_json",
)
print(f"Language: {result.language}, Duration: {result.duration}s")
for seg in result.segments:
    print(f"  [{seg['start']:.1f}s - {seg['end']:.1f}s] {seg['text']}")
```

#### Audio Model Aliases

| Alias | Builder | Description |
|-------|---------|-------------|
| `@audio:cheap` | `AudioModel.cheap()` | Cheapest model |
| `@audio:balanced` | `AudioModel.balanced()` | Best value |
| `@audio:quality` | `AudioModel.quality()` | Highest quality |
| `@audio:fast` | `AudioModel.fast()` | Lowest latency |

Modifiers: `streaming=True`, `instructions=True`

```python
AudioModel.cheap(streaming=True)       # streaming support
AudioModel.quality(instructions=True)  # custom voice instructions (gpt-4o-mini-tts)
```

#### Voices

`alloy`, `ash`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`

### CDN File Storage

```python
from pathlib import Path

# Upload from file path
file = client.cdn.upload(
    Path("./image.png"),
    is_public=True,
)
print(file.url)

# Upload bytes directly
file = client.cdn.upload(
    b"file content",
    filename="document.txt",
    is_public=True,
)

# Upload from URL (server downloads)
file = client.cdn.upload(
    url="https://example.com/image.png",
    filename="image.png",
)

# List files
files = client.cdn.list(page=1, page_size=20)
for f in files.results:
    print(f"{f.filename}: {f.size_bytes} bytes")

# Get file details
file = client.cdn.get("file-uuid")

# Delete file
client.cdn.delete("file-uuid")

# Statistics
stats = client.cdn.stats()
print(f"Total files: {stats.total_files}")
print(f"Total size: {stats.total_size_bytes} bytes")
```

### URL Shortener

```python
# Create short link
link = client.shortlinks.create(
    target_url="https://example.com/very-long-url-here",
    custom_slug="my-link",  # optional
    max_hits=1000,  # optional limit
)
print(link.short_url)
print(link.code)

# List links
links = client.shortlinks.list()
for link in links.results:
    print(f"{link.code}: {link.hit_count} hits")

# Statistics
stats = client.shortlinks.stats()
print(f"Total links: {stats.total_links}")
print(f"Total hits: {stats.total_hits}")
```

#### Async Cleaning with Agent

For complex HTML or when you need extraction patterns:

```python
# Submit and wait for results (recommended)
result = client.api_cleaner.clean_async(
    html_content,
    url="https://example.com/article",
    task_prompt="Extract main article content, ignore navigation",
    output_format="markdown",
    wait=True,
)
print(result.cleaned_html)

# Or submit without waiting (for manual polling)
job = client.api_cleaner.clean_async(
    html_content,
    task_prompt="Extract product details",
)
print(f"Job queued: {job.request_uuid}")

# Poll job status manually
status = client.api_cleaner.job_status(job.request_uuid)
print(f"Status: {status.status}")

# Get extraction patterns (reusable for similar pages)
patterns = client.api_cleaner.patterns(job.request_uuid)
for p in patterns.patterns:
    print(f"Selector: {p['selector']} ({p['type']})")

# Get full result
result = client.api_cleaner.get(job.request_uuid)
print(result.cleaned_html)
```

### Web Search

Search the web using Anthropic's `web_search` tool:

```python
from sdkrouter import SDKRouter, UserLocation

client = SDKRouter()

# Basic web search
result = client.search.query("latest AI developments 2026", model="claude-haiku-4-5-20251001")
print(result.content)
print(f"Cost: ${result.cost_usd}")

# View citations
for citation in result.citations:
    print(f"- {citation.title}: {citation.url}")

# Search with domain filtering and explicit model
result = client.search.query(
    "Python tutorials",
    model="claude-haiku-4-5-20251001",
    allowed_domains=["python.org", "realpython.com"],
    blocked_domains=["spam-site.com"],
)

# Localized search
result = client.search.query(
    "weather forecast",
    model="claude-haiku-4-5-20251001",
    user_location=UserLocation(country="US", city="San Francisco"),
)

# Fetch and analyze specific URL
result = client.search.fetch(
    "https://example.com/article",
    prompt="Extract the main points from this article",
    model="claude-haiku-4-5-20251001",
)
```

#### Mode-Based Search

Use progressive search modes for different levels of analysis:

```python
from sdkrouter import SDKRouter, SearchMode

client = SDKRouter()

# Research mode: LLM ranking + summary
results = client.search.query_async(
    "best Python web frameworks 2026",
    mode=SearchMode.RESEARCH,
    model="claude-haiku-4-5-20251001",  # Cost-efficient model
    task_prompt="Rank by popularity and documentation quality",
    max_results=20,
    wait=True,
)
for item in results.ranked_results:
    print(f"- {item.title} (relevance: {item.relevance}, score: {item.relevance_score})")
print(f"Summary: {results.summary}")

# Get full results with metrics
result = client.search.results(str(results.uuid))
if result.agent_metrics:
    m = result.agent_metrics
    print(f"Duration: {m.total_duration_ms}ms")
    print(f"Cost: ${m.cost_usd}")
```

#### Analyze Mode: Entity Extraction

```python
# Analyze mode adds entity extraction
results = client.search.query_async(
    "latest AI startup funding rounds 2026",
    mode=SearchMode.ANALYZE,
    model="claude-haiku-4-5-20251001",
    task_prompt="Focus on funding news",
    wait=True,
)

# Get full results with entities
result = client.search.results(str(results.uuid))
if result.entities:
    for company in result.entities.companies or []:
        print(f"Company: {company.value} - {company.entity_context}")
    for amount in result.entities.amounts or []:
        print(f"Amount: {amount.value}")
```

#### Comprehensive Mode: Deep Analysis

```python
# Comprehensive mode: fetches URL content for synthesis
results = client.search.query_async(
    "climate change policy updates 2026",
    mode=SearchMode.COMPREHENSIVE,
    model="claude-haiku-4-5-20251001",
    task_prompt="Compare policy approaches across countries",
    wait=True,
    timeout=600.0,
)

result = client.search.results(str(results.uuid))
print(f"Synthesis: {result.synthesis}")
print(f"Detailed analysis: {len(result.detailed_analysis or [])} sources")
```

#### Search Modes

| Mode | Capabilities | Use Case |
|------|-------------|----------|
| `search` | Direct web search | Fast, simple queries |
| `research` | + LLM ranking, summary | Ranked results with insights |
| `analyze` | + Entity extraction | Extract companies, people, amounts |
| `comprehensive` | + URL fetch, synthesis | Deep content analysis |
| `investigate` | + Multi-query, cross-analysis | Complex investigations |

### Embeddings

Create text embeddings for semantic search and similarity:

```python
# Single text embedding
result = client.embeddings.create("Hello, world!")
embedding = result.data[0].embedding
print(f"Dimensions: {len(embedding)}")

# Batch embeddings
texts = ["Python programming", "JavaScript coding", "Machine learning"]
result = client.embeddings.create(texts)
for i, item in enumerate(result.data):
    print(f"[{i}] {len(item.embedding)} dimensions")

# Custom model (larger dimensions)
result = client.embeddings.create(
    "Hello, world!",
    model="openai/text-embedding-3-large",  # 3072 dimensions
)
```

#### Available Models

| Model | Dimensions | Use Case |
|-------|-----------|----------|
| `openai/text-embedding-3-small` | 1536 | Fast, cheap, default |
| `openai/text-embedding-3-large` | 3072 | Higher quality |
| `openai/text-embedding-ada-002` | 1536 | Legacy |

### Payments (Crypto)

Accept cryptocurrency payments and manage withdrawals:

```python
# Get current balance
balance = client.payments.get_balance()
print(f"Balance: ${balance.balance_usd}")
print(f"Total deposited: ${balance.total_deposited}")

# List available currencies
currencies = client.payments.list_currencies()
for c in currencies.results:
    print(f"{c.code}: {c.name} ({c.network})")

# Get deposit estimate
estimate = client.payments.get_deposit_estimate(
    currency_code="USDTTRC20",
    amount_usd=100.00,
)
print(f"Crypto amount: {estimate.crypto_amount}")
```

#### Create Payment Invoice

```python
# Create a payment invoice
result = client.payments.create(
    amount_usd="25.00",
    currency_code="USDTTRC20",
    description="Premium subscription",
    client_reference_id="order_12345",
)

if result.success:
    payment = result.payment
    print(f"Pay {payment.pay_amount} to: {payment.pay_address}")
    print(f"Payment URL: {payment.payment_url}")
    print(f"Expires: {payment.expires_at}")

# Check payment status
status = client.payments.check_status(payment.id, refresh=True)
print(f"Status: {status.status}")
if status.transaction_hash:
    print(f"Transaction: {status.transaction_hash}")

# List all payments
payments = client.payments.list(page=1, page_size=10)
for p in payments.results:
    print(f"{p.internal_payment_id}: ${p.amount_usd} - {p.status}")
```

#### Transaction History

```python
# List transactions
transactions = client.payments.list_transactions(page=1, page_size=10)
for tx in transactions.results:
    sign = "+" if float(tx.amount_usd) > 0 else ""
    print(f"{tx.transaction_type}: {sign}${tx.amount_usd}")
    print(f"Balance after: ${tx.balance_after}")
```

#### Withdrawals

```python
# Get withdrawal estimate
estimate = client.payments.get_withdrawal_estimate(
    currency_code="USDTTRC20",
    amount_usd=50.00,
)
print(f"Network fee: ${estimate.network_fee_usd}")
print(f"Final amount: ${estimate.final_amount_usd}")

# Create withdrawal request
result = client.payments.create_withdrawal(
    amount_usd="50.00",
    currency_code="USDTTRC20",
    wallet_address="TYourWalletAddress123",
)
if result.success:
    print(f"Withdrawal ID: {result.withdrawal.internal_withdrawal_id}")
    print(f"Status: {result.withdrawal.status}")  # pending (requires admin approval)

# List withdrawals
withdrawals = client.payments.list_withdrawals()
for w in withdrawals.results:
    print(f"{w.internal_withdrawal_id}: ${w.amount_usd} - {w.status}")
```

#### Provider Credentials

```python
# List provider credentials
credentials = client.payments.list_credentials()
for cred in credentials.results:
    print(f"{cred.name}: {cred.provider.name}")
    print(f"Total payments: {cred.total_payments}")
    print(f"Total volume: ${cred.total_volume_usd}")

# Test credential connection
test = client.payments.test_credential(cred.id)
print(f"Connection: {'OK' if test.success else 'Failed'}")
```

#### Payments API Summary

| Method | Description |
|--------|-------------|
| `get_balance()` | Current balance and totals |
| `list_currencies()` | Available cryptocurrencies |
| `get_deposit_estimate(...)` | Estimate crypto amount for USD |
| `create(...)` | Create payment invoice |
| `check_status(id)` | Check payment status |
| `list()` | List all payments |
| `list_transactions()` | Transaction history |
| `get_withdrawal_estimate(...)` | Estimate withdrawal fees |
| `create_withdrawal(...)` | Request withdrawal |
| `list_withdrawals()` | List withdrawals |
| `list_credentials()` | Provider credentials |
| `test_credential(id)` | Test provider connection |

### Proxies

Manage proxies with rotation, assignments, and health monitoring:

```python
# List all proxies
proxies = client.proxies.list(page=1, page_size=10)
for p in proxies.results:
    print(f"{p.host}:{p.port} - {p.country} - {p.status}")
    print(f"Success rate: {p.success_rate}%")

# Get healthy proxies (active, good success rate, fast response)
healthy = client.proxies.get_healthy()
for p in healthy:
    print(f"{p.host}:{p.port}")

# Get Korean proxies
korean = client.proxies.get_korean()

# Get performance statistics
stats = client.proxies.get_performance_stats()
print(f"Stats: {stats}")
```

#### Create and Update Proxies

```python
# Create a new proxy
proxy = client.proxies.create(
    host="192.168.1.100",
    port=8080,
    proxy_type="http",      # http, https, socks4, socks5
    proxy_mode="static",    # static, rotating, mobile
    country="KR",
    username="user",
    password="pass",
    is_active=True,
)
print(f"Created: {proxy.id}")

# Update proxy
updated = client.proxies.update(
    proxy.id,
    status="active",
    max_concurrent_requests=100,
)

# Delete proxy
client.proxies.delete(proxy.id)
```

#### Rotation Configurations

Configure automatic proxy rotation based on criteria:

```python
# List rotation configurations
rotations = client.proxies.list_rotations()
for r in rotations.results:
    print(f"{r.name}: {r.allowed_countries}")

# Create rotation configuration
rotation = client.proxies.create_rotation(
    name="Korean Fast Proxies",
    allowed_countries=["KR"],
    min_success_rate=95.0,
    max_response_time_ms=1000,
    rotation_interval_minutes=30,
    is_active=True,
)

# Get available proxies matching rotation criteria
available = client.proxies.get_available_proxies_for_rotation(rotation.id)
print(f"Available: {len(available)} proxies")

# Update rotation
client.proxies.update_rotation(rotation.id, is_active=False)

# Delete rotation
client.proxies.delete_rotation(rotation.id)
```

#### Proxy Assignments

Track proxy usage by parser:

```python
# List assignments
assignments = client.proxies.list_assignments()
for a in assignments.results:
    print(f"{a.parser_id} -> {a.proxy.host}:{a.proxy.port}")

# Get active assignments
active = client.proxies.get_active_assignments()

# Create assignment
assignment = client.proxies.create_assignment(
    proxy=proxy.id,
    parser_id="encar_parser",
    is_active=True,
    priority=5,
)

# Update assignment
client.proxies.update_assignment(assignment.id, priority=10)

# Delete assignment
client.proxies.delete_assignment(assignment.id)
```

#### Proxy Tests

Test proxy connectivity and performance:

```python
# List recent tests
tests = client.proxies.list_tests()
for t in tests.results:
    status = "PASS" if t.is_successful else "FAIL"
    print(f"[{status}] {t.proxy.host} - {t.response_time_ms}ms")

# Run a test
test = client.proxies.create_test(
    proxy=proxy.id,
    test_type="connectivity",  # connectivity, speed, anonymity, geolocation
)
print(f"Test {'passed' if test.is_successful else 'failed'}")
print(f"Response time: {test.response_time_ms}ms")
```

#### Proxies API Summary

| Method | Description |
|--------|-------------|
| `list()` | List all proxies |
| `get(id)` | Get proxy details |
| `create(...)` | Create new proxy |
| `update(id, ...)` | Update proxy |
| `delete(id)` | Delete proxy |
| `get_healthy()` | Get healthy proxies |
| `get_korean()` | Get Korean proxies |
| `get_by_country(code)` | Get by country |
| `get_performance_stats()` | Overall stats |
| `list_rotations()` | List rotation configs |
| `create_rotation(...)` | Create rotation |
| `update_rotation(id, ...)` | Update rotation |
| `delete_rotation(id)` | Delete rotation |
| `get_available_proxies_for_rotation(id)` | Matching proxies |
| `list_assignments()` | List assignments |
| `create_assignment(...)` | Create assignment |
| `update_assignment(id, ...)` | Update assignment |
| `delete_assignment(id)` | Delete assignment |
| `get_active_assignments()` | Active assignments |
| `list_tests()` | List tests |
| `create_test(...)` | Run proxy test |

### LLM Models API

```python
# List available models with pagination
models = client.llm_models.list(page=1, page_size=50)
for m in models.results:
    print(f"{m.model_id}: context={m.context_length}")

# Get model details
model = client.llm_models.get("openai/gpt-4o-mini")
print(f"Context: {model.context_length} tokens")
print(f"Vision: {model.supports_vision}")
print(f"Price: ${model.pricing.prompt}/M input")

# List providers
providers = client.llm_models.providers()
for p in providers.providers:
    print(f"{p.name}: {p.model_count} models")

# Calculate cost
cost = client.llm_models.calculate_cost(
    "openai/gpt-4o-mini",
    input_tokens=1000,
    output_tokens=500,
)
print(f"Input: ${cost.input_cost_usd:.6f}")
print(f"Output: ${cost.output_cost_usd:.6f}")
print(f"Total: ${cost.total_cost_usd:.6f}")

# Statistics
stats = client.llm_models.stats()
print(f"Total models: {stats.total_models}")
print(f"Vision models: {stats.vision_models}")
```

### Token Utilities

```python
from sdkrouter.utils import count_tokens, count_messages_tokens

# Count tokens in text
tokens = count_tokens("Hello, world!")
print(f"Tokens: {tokens}")

# Count tokens in messages
messages = [
    {"role": "system", "content": "You are helpful."},
    {"role": "user", "content": "Hello!"},
]
tokens = count_messages_tokens(messages)
print(f"Message tokens: {tokens}")
```

### Logging

Built-in logging with Rich console output and file persistence:

```python
from sdkrouter import get_logger

# Get a configured logger
log = get_logger(__name__)
log.info("Processing request")
log.debug("Debug details: %s", data)
log.error("Something failed", exc_info=True)

# With custom settings
log = get_logger(__name__, level="DEBUG", log_to_file=True)
```

#### Features

- Rich console output with colors and formatted tracebacks
- Automatic file logging with date-based rotation
- Auto-detection of project root for log directory
- Cross-platform log paths (macOS, Windows, Linux)
- Fallback to standard logging if Rich not installed

```python
from sdkrouter import setup_logging, get_log_dir, find_project_root

# Configure logging globally
setup_logging(
    level="DEBUG",        # DEBUG | INFO | WARNING | ERROR | CRITICAL
    log_to_file=True,     # Write to file
    log_to_console=True,  # Output to console
    app_name="myapp",     # Log file prefix
    rich_tracebacks=True, # Rich exception formatting
)

# Get log directory path
log_dir = get_log_dir()  # e.g., /project/logs or ~/Library/Logs/sdkrouter

# Find project root
root = find_project_root()  # Searches for pyproject.toml, .git, etc.
```

## Async Support

All features support async operations:

```python
from sdkrouter import AsyncSDKRouter, Model
import asyncio

async def main():
    client = AsyncSDKRouter(api_key="your-api-key")

    # Async chat with Model builder
    response = await client.chat.completions.create(
        model=Model.cheap(),
        messages=[{"role": "user", "content": "Hello!"}]
    )

    # Async structured output
    result = await client.parse(
        model=Model.smart(json=True),
        messages=[...],
        response_format=MyModel,
    )

    # Async audio
    response = await client.audio.speech(input="Hello!", voice="nova")
    result = await client.audio.transcribe(file=audio_bytes)

    # Async streaming TTS
    async for item in client.audio.speech_stream(input="Stream me!", voice="nova"):
        ...

    # Parallel requests
    results = await asyncio.gather(
        client.vision.analyze(image_url="..."),
        client.cdn.list(),
        client.llm_models.stats(),
    )

asyncio.run(main())
```

## Configuration

```python
from sdkrouter import SDKRouter

# Environment variables (auto-loaded)
# SDKROUTER_API_KEY - API key
# SDKROUTER_BASE_URL - Custom base URL

# Direct configuration
client = SDKRouter(
    api_key="your-key",
    base_url="https://your-server.com",
    timeout=60.0,
    max_retries=3,
)

# Use OpenRouter directly
client = SDKRouter(
    openrouter_api_key="your-openrouter-key",
    use_self_hosted=False,
)
```

## Type Safety

All responses are fully typed with Pydantic models:

```python
from sdkrouter import Model
from sdkrouter.tools import (
    VisionAnalyzeResponse,
    OCRResponse,
    CDNFileDetail,
    ShortLinkDetail,
    CleanResponse,
    LLMModelDetail,
    ImageGenerateResponse,
    ImageGenerationDetail,
)

# IDE autocomplete works
result: VisionAnalyzeResponse = client.vision.analyze(...)
result.description  # str
result.cost_usd     # float
result.usage.total_tokens  # int

# Image generation types
gen: ImageGenerateResponse = client.image_gen.generate(...)
gen.image_cdn_url  # str
gen.cost_usd       # str (decimal)
gen.duration_ms    # int
```

### Helpers

Re-exported parsing utilities from `sdkrouter_cleaner`:

```python
from sdkrouter import json_to_toon, JsonCleaner, html_to_text, extract_links, extract_images

# Convert JSON/dict to TOON format
toon_str = json_to_toon({"name": "Product", "price": 29.99})

# Clean and normalize messy JSON strings
cleaner = JsonCleaner()
cleaned = cleaner.clean(messy_json_string)

# Extract plain text from HTML
text = html_to_text("<p>Hello <b>world</b></p>")
# "Hello world"

# Extract all links from HTML
links = extract_links("<a href='/page'>Link</a>", base_url="https://example.com")

# Extract all image URLs from HTML
images = extract_images("<img src='/img.png'>", base_url="https://example.com")
```

## Exports

```python
from sdkrouter import (
    # Clients
    SDKRouter,
    AsyncSDKRouter,
    # Model alias builders
    Model,        # LLM model aliases
    AudioModel,   # Audio model aliases
    # Enums for advanced use
    Tier,       # PresetSlug enum
    Category,   # CategorySlug enum
    Capability, # Capability enum
    # Types
    ModelInfo,
    ModelPricing,
    # Search
    SearchMode,
    UserLocation,
    # Image Generation
    ImageGenerateResponse,
    ImageGenerationDetail,
    ImageGenOptions,
    ImageGenerateResponseStatus,
    # Audio
    SpeechResponse,
    SpeechStreamChunk,
    SpeechStreamDone,
    AudioAnalysis,
    AudioAnalysisFrame,
    TranscriptionResponse,
    VerboseTranscriptionResponse,
    # Helpers
    json_to_toon,
    JsonCleaner,
    html_to_text,
    extract_links,
    extract_images,
    # And more...
)
```

## Supported Models

Access 300+ models from providers:

- **OpenAI**: GPT-4.5, GPT-4o, o3, o3-mini, o1, o1-mini
- **Anthropic**: Claude Opus 4.5, Claude Sonnet 4, Claude 3.5 Sonnet
- **Google**: Gemini 2.5 Pro, Gemini 2.0 Flash
- **Meta**: Llama 4, Llama 3.3, Llama 3.2
- **Mistral**: Mistral Large, Mixtral, Codestral
- **DeepSeek**: DeepSeek V3, DeepSeek R1
- And many more via OpenRouter

## License

MIT
