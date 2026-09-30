# Free LLM API backups for "Days of Odd": research notes

Checked on 2026-09-28 against official provider pages, unless a line is marked **UNVERIFIED**.

## Live tests on the channel's own key (2026-09-28)

Gemma 4 on the Gemini API, same `days-of-odd` project and key, no new sign-up:

- Both `gemma-4-31b-it` and `gemma-4-26b-a4b-it` read a photo (named Arthur Conan Doyle from his portrait)
  and answer with JSON when given `responseJsonSchema`. The 31B model sometimes adds a stray code fence
  after the JSON, so replies are parsed leniently.
- The free tier allows **16,000 input tokens a minute per model** (the 429 names
  `GenerateContentInputTokensPerModelPerMinute-FreeTier`, `quotaValue` 16000). A bigger single request can
  never go through, so Gemma can take scripts, picture checks, and reviews, but not research (about 100K
  tokens) or the main picture pick (about 60 pictures). A picture costs Gemma about 280 tokens.
- `thinkingConfig.thinkingLevel` "low" is refused (400 "Thinking level is not supported for this model");
  "high" is accepted but produced no thought tokens. The studio sends Gemma no thinking level.
- Speed: 26B-A4B answers in about 2 s; 31B in 26 to 37 s, and it returned a 503 once and a 500 once.
- Accuracy: asked the Great Emu War's start year, 26B-A4B once answered 2014 (it was 1932); 31B was right
  every time. Only the 31B model is used.
- Daily request limits aren't shown by the API or the public docs (UNVERIFIED); a spent model is detected
  from its 429 like any other.

Decision: `gemma-4-31b-it` ends both Gemini ladders in `pipeline/src/ytc/llm.py`, before Cursor, for
prompts under its 16,000-token cap. Cloudflare Workers AI, Mistral, and Groq below would each need the owner
to sign up and add a key; they are the next backups if Gemini's free tier shrinks.

License check (CHANNEL.md rule), 2026-09-28: `google/gemma-4-31B-it` on Hugging Face is `apache-2.0`, not
gated, last modified 2026-07-20, about 9.5 million downloads
(<https://huggingface.co/google/gemma-4-31B-it>). On the Gemini API it runs under the same Gemini API terms
as the Flash models.

Requirements applied to every provider:
- It must be genuinely free: no card charges and no paid credits.
- Its terms must allow commercial or production use of outputs.

How the pages were read:
- `ai.google.dev` rate-limits this machine (it returns HTTP 429 and redirects to `google.com/sorry`), so Google's Gemini docs were read two other ways:
  - The live rate-limits page, through the `r.jina.ai` reader.
  - The Internet Archive's latest snapshots. Each Google source below gives its snapshot date; the oldest is 2 Sep 2026 and most are 20–27 Sep 2026.
- Every other provider's pages were fetched live on 2026-09-28.
- Raw copies are saved in `.scratch/research2/pages/`.

---

## Bottom line (ranked)

### (i) Long-context text to JSON (about 100K tokens in, claims table out)

First, before adding any provider, fall back to the other free models in the same Gemini project. Google applies quotas per model ("Each model variation has an associated rate limit"), so switching models is legitimate; spreading load across projects is not.
- `gemini-3.5-flash-lite` and `gemini-3.1-flash-lite`: 1,048,576-token input, structured outputs, image input.
- `gemma-4-31b-it` and `gemma-4-26b-a4b-it`: separate quota; limits UNVERIFIED.

Then, in order:

1. **Cloudflare Workers AI, `@cf/google/gemma-4-26b-a4b-it`**
   - Context: 256,000. JSON through `response_format` (schema adherence is not guaranteed).
   - The free 10,000 neurons/day covers about **10 calls per day** of 100K in + 2K out (about 964 neurons each).
   - 300 requests per minute.
   - You keep rights to inputs and outputs, and Cloudflare does not train on them. The model is Apache-2.0.
   - On Workers Free, going over the cap returns an error, never a charge.
2. **Mistral Free mode, `mistral-small-2603` (Mistral Small 4)**
   - Context: 256K. Structured outputs.
   - No card is needed, and the Free plan includes "$10 /mo in API credits".
   - At $0.15/$0.60 per million tokens, $10 covers about **600 calls a month** of 100K in + 2K out. `mistral-large-2512` covers about 190.
   - Rate limits are not published; they appear only in the console.
   - Free-mode data is used for training by default; you can opt out.
3. **Z.ai, `glm-4.7-flash`** ("Completely Free": 200K context, 128K max output, `json_object` mode).
   - Limits are unpublished.
   - Z.ai's terms require AI-generated outputs to be "prominently marked".
   - Alternative: OpenRouter `nvidia/nemotron-3-super-120b-a12b:free` (262,144 context, structured outputs). OpenRouter allows only **50 free requests per day in total** unless you buy credits.

### (ii) Vision: picking and checking pictures

1. **Cloudflare, `@cf/google/gemma-4-26b-a4b-it`** (vision; input costs 9,091 neurons per million tokens).
   - Shares the same 10,000-neuron daily budget as the text work.
   - Alternative: `@cf/meta/llama-4-scout-17b-16e-instruct` (131,000 context, vision; 24,545 in / 77,273 out neurons per million tokens).
2. **Mistral, `mistral-small-2603`** (vision) or `ministral-14b-2512` ($0.20/$0.20 per million tokens), drawing on the same $10/month credit.
3. **Z.ai, `glm-4.6v-flash`** (free; image, video, text and file input; 128K), or **OpenRouter `google/gemma-4-31b-it:free`** (image and video input; 262,144 context; the 50/day cap is shared).

Not recommended for production vision:
- Groq `qwen/qwen3.8-27b`: Preview tier, "evaluation purposes only". Maximum 3 images per request, and each image counts as 2,048 tokens against an 8K tokens-per-minute cap.
- SambaNova `gemma-4-31B-it`: Preview tier, "should not be used in production environments".

### Bonus: the 45-second script JSON (short prompts)

**Groq `openai/gpt-oss-120b`** is a good fit for this step:
- Production tier, with strict `json_schema`.
- Free plan: 30 RPM, 1,000 RPD, 8,000 TPM, 200,000 TPD.
- Groq does not train on inputs or outputs.

It **cannot** take the 100K-token claims prompt: a single request larger than the 8K tokens-per-minute limit cannot go through.

### Rough daily budget on Cloudflare (estimate, not measured)

One video comes to roughly 2,000 neurons, so about 4–5 videos fit into the free 10,000 neurons/day:

| Step | Estimate |
|---|---|
| Claims extraction | ≈ 964 |
| Script | ≈ 100 |
| Picture selection, about 60 images | ≈ 300–600 (depends on per-image token cost, UNVERIFIED) |
| Frame review | ≈ 300 |

Measure the real cost from the `usage` field before relying on this.

---

## At a glance

| Provider | Genuinely free? | Card needed? | Commercial/production use of outputs? | Verdict |
|---|---|---|---|---|
| Google Gemini API | Yes | No (paid only with an active billing account) | Yes ("professional or business purposes"), but free-tier data is used by Google | Keep as primary; fall back across models, never across projects |
| Groq | Yes | UNVERIFIED (widely reported: no) | Yes (Services Agreement) | Short JSON only; Preview models are not for production |
| Cerebras | **No**: $5 trial credit after "a verified payment method", expires in 30 days | Yes | n/a | **Excluded** |
| Mistral | Yes, plus $10/month credit | No ("no credit card required") | Yes ("owns all Output"); training on by default | Backup |
| OpenRouter `:free` | Yes; 50 requests/day without buying credits | No | Depends on each model's own terms | Low-volume backup |
| Cloudflare Workers AI | Yes, 10,000 neurons/day | No (card only for paid services) | Yes (you retain rights; no training) | **Top backup** |
| GitHub Models | **Retired 30 Jul 2026** | n/a | n/a | **Excluded** |
| NVIDIA build.nvidia.com | Trial | n/a | **No** ("not in production") | **Excluded** |
| SambaNova Cloud | Yes (Free Tier = no payment method linked) | No | Yes (you retain Customer Content) | Small backup (20 RPD per model) |
| Z.ai | Yes (the Flash models are "Completely Free") | UNVERIFIED | Yes, but outputs must be marked as AI | Backup |
| Hugging Face / Together / Chutes / Kluster / Cohere | No, or negligible | n/a | n/a | **Excluded** |

---

## 1. Google Gemini API (free tier), including Gemma

Checked 2026-09-28. Sources:
- Rate limits: https://ai.google.dev/gemini-api/docs/rate-limits (live via reader; "Last updated 2026-09-02 UTC").
- Pricing: https://ai.google.dev/gemini-api/docs/pricing (snapshot 2026-09-26).
- Models: https://ai.google.dev/gemini-api/docs/models (snapshot 2026-09-26).
- Model pages: `.../models/gemini-3.8-flash` (snapshot 2026-09-20); `.../gemini-3.5-flash-lite` and `.../gemini-3.1-flash-lite` (snapshots 2026-09-24).
- Gemma: https://ai.google.dev/gemma/docs/core/gemma_on_gemini_api (snapshot 2026-09-02).
- OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai (snapshot 2026-09-27).
- Gemini API Additional Terms: https://ai.google.dev/gemini-api/terms (snapshot 2026-09-27; "Effective March 23, 2026").
- Google APIs Terms of Service: https://developers.google.com/terms (live; "Last modified: November 9, 2021").

**Free-tier models.** On the pricing page, the Free Tier column reads "Free of charge" for Standard input and output on all of these.

| Model ID | Inputs | Input / output token limit | Structured outputs |
|---|---|---|---|
| `gemini-3.8-flash` (newest, Stable) | Text, Image, Video, Audio, PDF | 1,048,576 / 65,536 | Supported |
| `gemini-3.7-flash`, `gemini-3.6-flash`, `gemini-3.5-flash` | free on pricing page; model pages not fetched (UNVERIFIED specs) | UNVERIFIED | UNVERIFIED |
| `gemini-3.5-flash-lite` | Text, Image, Video, Audio, PDF | 1,048,576 / 65,536 | Supported |
| `gemini-3.1-flash-lite` | Text, Image, Video, Audio, PDF | 1,048,576 / 65,536 | Supported |
| `gemma-4-31b-it`, `gemma-4-26b-a4b-it` | Text + images ("Gemma 4 models can process images"); "up to 256K context window" | 256K | Not documented on Google's Gemma page (UNVERIFIED) |
| `gemini-2.5-pro`, `gemini-2.5-flash`, `gemini-2.5-flash-lite` | free on the pricing page, **but** "we are limiting access to the 2.5 models to users who have actively used them in the past" | | |

The Gemma page lists only Gemma 4 models. Gemma 3 on the Gemini API is not listed; its status is UNVERIFIED. The pricing page has no Gemma entry, which fits Gemma being free-only; the third-party claim "Gemma 4 has no paid tier at all" (klymentiev.com, 11 Sep 2026) is UNVERIFIED.

**Limits.**
- "Rate limits are applied per project, not per API key. Requests per day (**RPD**) quotas reset at midnight Pacific time."
- "Each model variation has an associated rate limit."
- "Rate limits are more restricted for experimental and preview models."
- "Specified rate limits are not guaranteed and actual capacity may vary."
- The docs no longer publish free-tier RPM/RPD/TPM numbers; they are shown only at https://aistudio.google.com/rate-limit. Your observed figures (Flash 5 RPM / 20 RPD; Flash-Lite 15 RPM / 500 RPD) are the authority for your project. Gemma 4 free-tier limits: UNVERIFIED.

**JSON.** Structured outputs are supported on the Gemini models above.

**OpenAI-compatible endpoint (verified):** `https://generativelanguage.googleapis.com/v1beta/openai/`

**Card.** Not needed. The Gemini API Additional Terms say: "Your access to Gemini API is a 'Paid Service' only when accessing the API through a Cloud Project associated with an active billing account."

**Commercial use.** Gemini API Additional Terms:
> "Use of Google AI Studio and Gemini API is for developers building with Google AI models for professional or business purposes, not for consumer use."
> "Google won't claim ownership over that content."

**Data use on the free tier.** Gemini API Additional Terms:
> "When you use Unpaid Services, including, for example, Google AI Studio and the unpaid quota on Gemini API, Google uses the content you submit to the Services and any generated responses to provide, improve, and develop Google products and services and machine learning technologies..."
> "human reviewers may read, annotate, and process your API input and output."

The pricing page's "Used to improve our products" row reads **Yes** for the Free Tier and No for Paid.

**Region clause.** Gemini API Additional Terms:
> "You may use only Paid Services when making API Clients available to users in the European Economic Area, Switzerland, or the United Kingdom."

This is aimed at apps served to users in those regions. A pipeline that publishes videos is probably not an "API Client made available to users", but check this if you operate from, or serve users in, the EEA, UK or Switzerland.

**Multiple projects or API keys to exceed quota.**
- Google APIs Terms of Service §2(d):
  > "Google sets and enforces limits on your use of the APIs (e.g. limiting the number of API requests that you may make or the number of users you may serve), in our sole discretion. You agree to, and will not attempt to circumvent, such limitations documented with each API. If you would like to use any API beyond these limits, you must obtain Google's express consent to do so."
- Google APIs Terms of Service §2(c): "You will not misrepresent or mask either your identity or your API Client's identity when using the APIs or developer accounts."
- The Gemini Additional Terms (effective 23 Mar 2026) contain **no sentence that explicitly mentions multiple projects**. The §2(d) anti-circumvention clause is what governs.
- Google does enforce it. On Google's official developer forum (24 Jul 2026, https://discuss.ai.google.dev/t/175958), a user quotes a Google policy notice saying their project was "allegedly involved in attempts to circumvent quota restrictions by operating multiple projects as a single project". That is a user's report of Google's notice, not a policy page. Another thread reports automated, account-wide Google Cloud restrictions.
- Conclusion: multiple **keys** in one project do nothing (the quota is per project), and multiple **projects or accounts** to raise quota risk a ban. Switching between **different models** in one project is fine.

**Verdict.** Keep as the primary provider and add model fallback inside the one project. Don't rely on it alone: one enforcement action takes every Gemini model offline at once.

---

## 2. Groq (free plan)

Checked 2026-09-28. Sources:
- https://console.groq.com/docs/rate-limits (the free-plan table is embedded as JSON in the page)
- https://console.groq.com/docs/models
- https://console.groq.com/docs/vision
- https://console.groq.com/docs/structured-outputs
- https://console.groq.com/docs/legal/services-agreement

**Free-plan limits** (per organization):

| Model ID | RPM | RPD | TPM | TPD | Context / max output | Tier |
|---|---|---|---|---|---|---|
| `openai/gpt-oss-120b` | 30 | 1K | 8K | 200K | 131,072 / 65,536 | Production |
| `openai/gpt-oss-20b` | 30 | 1K | 8K | 200K | 131,072 / 65,536 | Production |
| `openai/gpt-oss-safeguard-20b` | 30 | 1K | 8K | 200K | — | — |
| `qwen/qwen3.8-27b` (only vision model) | 30 | 1K | 8K | 200K | 131,072 / 16,384 | **Preview** |

- Llama 3.1 8B and 3.3 70B are now Enterprise / Contact Sales.
- Models page: "Preview models are intended for evaluation purposes only and should not be used in production environments as they may be discontinued at short notice."

**Vision** (`qwen/qwen3.8-27b` only): "You can process a maximum of 3 images." "Each image counts as 2048 input tokens." Image URL requests are limited to 20MB.

**JSON.** Strict `json_schema` on `gpt-oss-20b`, `gpt-oss-120b` and `qwen3.8-27b`; JSON object mode is also available.

**Endpoint:** `https://api.groq.com/openai/v1`

**Card.** Not stated on the official pages (UNVERIFIED); widely reported as not required.

**Terms** (Services Agreement):
- §3.1: "...including the right to use Groq's APIs to integrate the Cloud Services and AI Model Services into your Customer Application and to make the Cloud Services and AI Model Services available to End Users through your Customer Applications."
- §8.1: "As between the parties, Customer retains all Intellectual Property Rights in Customer Data (including in Inputs and Outputs)..."
- §5.1: "Certain Cloud Services and AI Model Services may be designated as fee-free or otherwise available without triggering a payment for a limited time or based on usage limits."
- Training: "For clarity, Groq is not permitted to use Inputs or Outputs for training or fine-tuning any AI Model Services or other models, unless explicitly granted permission or instructed by Customer."
- §6.3(d)(iii) forbids use "in a manner intended to avoid incurring Fees". Don't multiply accounts.

**Verdict.** The 8K tokens-per-minute cap rules out the 100K claims step. Excellent for the short script JSON using `openai/gpt-oss-120b`. Vision is only on a Preview model, so not for production.

---

## 3. Cerebras (EXCLUDED)

Checked 2026-09-28. Source: https://inference-docs.cerebras.ai/support/rate-limits
- "Is there a permanently free tier? No. The Free Trial is time- and credit-bounded: $5 in credits that expire 30 days after they're granted."
- "New accounts receive $5 in free credits after adding a verified payment method."
- Trial limits, for reference: `gpt-oss-120b` and `qwen-3.8-27b` at 5 RPM, 30K uncached TPM, 1M TPD; context 65k / 64k.

A card is required and the credit is time-limited, so this fails the "genuinely free" test.

---

## 4. Mistral (Free mode, formerly "Experiment")

Checked 2026-09-28. Sources:
- https://docs.mistral.ai/getting-started/quickstarts/studio/activate-and-generate-api-key.md
- https://mistral.ai/pricing
- https://docs.mistral.ai/admin/billing-usage/usage-limits.md
- Mistral help centre articles on rate limits and training (help.mistral.ai, articles 698531 and 347617)
- https://docs.mistral.ai/models plus the individual model pages
- https://legal.mistral.ai/terms/commercial-terms-of-service ("Effective: September 25, 2026")

**Free mode:**
- "**Free mode**: API access is enabled by default with no credit card required. Usage and rate limits apply."
- The Free column of the pricing page lists "Test Mistral models in Studio." and "$10 /mo in API credits."
- Usage-limits doc: "Free mode lets you create API keys and use included monthly usage within the limits shown on the Limits page."
- Help centre: "Free mode (the default) has the lowest limits, intended for evaluation and prototyping." This describes the tier; it does not forbid production use.
- Actual requests-per-second and token-per-minute/month limits are shown only at admin.mistral.ai → Limits; they are not published (UNVERIFIED).
- Which models the $10 credit can be spent on is not stated (UNVERIFIED).

**Models (current).** Prices are per million tokens, input / output.

| Model | API ID | Context | Vision | Price |
|---|---|---|---|---|
| Mistral Small 4 | `mistral-small-2603` (`mistral-small-latest`) | 256k | Yes | $0.15 / $0.60 |
| Mistral Large 3 | `mistral-large-2512` | 256k | Yes | $0.50 / $1.50 |
| Mistral Medium 3.5 | `mistral-medium-3-5` | 256k | Yes | $1.50 / $7.50 |
| Ministral 3 14B | `ministral-14b-2512` | 256k | Yes | $0.20 / $0.20 |

- `mistral-small-2506` (retired 31 Jul 2026) and `mistral-medium-2508` (retired 31 Aug 2026) are gone. The vision doc still lists them, so it is stale.
- Structured outputs are supported.

**Endpoint:** `https://api.mistral.ai/v1` (chat at `/v1/chat/completions`; OpenAI-style request format).

**Training on free data:**
- "Free mode: As stated during subscription, we may use your data (input and output) to train our artificial intelligence models. You have the right to opt out of this program at any time."
- Opt out under Admin → Privacy → "Anonymous improvement data".
- Commercial Terms §4.3: Labs and Preview models are used for training.

**Terms** (Commercial Terms of Service, effective 25 Sep 2026):
- §3.1: "To the extent permitted by applicable law, Customer (i) retains all ownership rights in Customer Data and (ii) owns all Output."
- §3.2: you may not present Output as human-generated.

**Verdict.** A good second backup for both text and vision. Opt out of training, and read your real limits in the console before relying on it.

---

## 5. OpenRouter (`:free` models)

Checked 2026-09-28. Sources:
- https://openrouter.ai/docs/api_reference/limits.md
- https://openrouter.ai/api/v1/models
- https://openrouter.ai/terms ("Last Updated: August 31, 2026")
- https://openrouter.ai/docs/guides/privacy/provider-logging.md

**Limits.** For free model variants (IDs ending `:free`): **20 RPM**, and **50 RPD** if you have bought fewer than 10 credits ever (1,000 RPD at 10 or more). Buying credits is not allowed under your constraints, so the real cap is **50 requests per day across all free models**.

"Making additional accounts or API keys will not affect your rate limits, as we govern capacity globally."

**Relevant free models** (from `/api/v1/models`, 2026-09-28):

| Model ID | Context | Inputs | JSON parameters |
|---|---|---|---|
| `google/gemma-4-31b-it:free` | 262,144 | image, text, video | `response_format` |
| `google/gemma-4-26b-a4b-it:free` | 262,144 | image, text, video | `response_format` |
| `nvidia/nemotron-3-super-120b-a12b:free` | 262,144 | text | `response_format`, `structured_outputs` |
| `qwen/qwen3.8-27b:free` | 262,144 | text, image, video | `structured_outputs` (endpoint status was degraded) |
| `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free` | 256,000 | text, audio, image, video | none listed |
| `dots-studio/dots-3-note-preview:free` | 512,000 | text, image | both (Preview) |
| `nvidia/nemotron-3-ultra-550b-a55b:free`, `nvidia/nemotron-3.5-lightning:free` | 1,000,000 | text | none listed |
| `openrouter/free` (router across free models) | 200,000 | text, image | both |

- The Gemma 4 `:free` endpoints are served by the "Google AI Studio" provider.
- Ignore zero-priced entries that are not `:free` text models (`google/lyria-3-*` music models, `stealth/*`).

**Endpoint:** `https://openrouter.ai/api/v1`

**Card.** Not needed for `:free` models; credits are optional.

**Terms:**
- "Your ownership rights in the Output are set forth in the Model Terms for each Model you use."
- "Some Models may store or train on your Inputs for improving their own large language models and may allow you to opt-out of model training, as described in their Model Terms."
- Provider logging: "There are separate settings for paid and free models."
- Gemma 4 is Apache-2.0 (verified: Google's Gemma 4 licence link resolves to its Apache 2.0 page). NVIDIA Nemotron and Qwen 3.8 licences: UNVERIFIED.

**Verdict.** A good emergency fallback for both jobs, but 50 requests a day is thin. Use it for vision checks or as a last resort.

---

## 6. Cloudflare Workers AI

Checked 2026-09-28. Sources:
- https://developers.cloudflare.com/workers-ai/platform/pricing/ ("Last updated Sep 17, 2026")
- https://developers.cloudflare.com/workers-ai/platform/limits/
- https://developers.cloudflare.com/workers-ai/features/json-mode/
- https://developers.cloudflare.com/workers-ai/configuration/open-ai-compatibility/
- Individual model pages under https://developers.cloudflare.com/workers-ai/models/
- https://www.cloudflare.com/service-specific-terms-developer-platform/ ("Last updated: September 28, 2026")
- https://www.cloudflare.com/terms/

**Free allocation:**
- "Our free allocation allows anyone to use a total of **10,000 Neurons per day at no charge**."
- "All limits reset daily at 00:00 UTC. If you exceed any one of the above limits, further operations will fail with an error."
- Workers Free: "10,000 Neurons per day | N/A - Upgrade to Workers Paid". There is no overage billing.
- Some models are paid-only: kimi-k2.6, kimi-k2.7-code, glm-5.2, glm-5.3, glm-5.3-flash, deepseek-v4-*.

**Rate limit:** Text Generation "300 requests per minute, unless the model requires the Workers Paid plan".

**Models.** Neurons per million tokens, input / output. The last column is the cost of one 100K-in + 2K-out call and how many fit in the free daily budget.

| Model ID | Context | Vision | Input / output | 100K + 2K call (calls/day) |
|---|---|---|---|---|
| `@cf/google/gemma-4-26b-a4b-it` | 256,000 | Yes | 9,091 / 27,273 | ≈ 964 (≈ 10/day) |
| `@cf/zai-org/glm-4.7-flash` | 131,072 | No | 5,500 / 36,400 | ≈ 623 (≈ 16/day; reasoning tokens add output) |
| `@cf/meta/llama-4-scout-17b-16e-instruct` | 131,000 | Yes | 24,545 / 77,273 | ≈ 2,609 (≈ 3/day) |
| `@cf/openai/gpt-oss-120b` | 128K | No | 31,818 / 68,182 | ≈ 3,318 (≈ 3/day) |
| `@cf/qwen/qwen3.8-27b` | 262,144 | Yes | 40,909 / 290,909 | ≈ 4,673 (≈ 2/day) |
| `@cf/nvidia/nemotron-3-120b-a12b` | 256K | No | 45,455 / 136,364 | ≈ 4,818 (≈ 2/day) |
| `@cf/mistralai/mistral-small-3.1-24b-instruct` | 128K | Yes | 31,876 / 50,488 | ≈ 3,289 (uses `guided_json`) |
| `@cf/meta/llama-3.2-11b-vision-instruct` | UNVERIFIED | Yes | 4,410 / 61,493 | — |

Per-image token cost for vision models on Cloudflare: UNVERIFIED. Measure it from `usage`.

**JSON.**
- `response_format` is supported on Gemma 4 (per its model page).
- The JSON-mode doc says: "Note that Workers AI can't guarantee that the model responds according to the requested JSON Schema." and "JSON Mode currently doesn't support streaming."
- Validate the output and retry on failure.

**Endpoint:** `https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1` (`/chat/completions`)

**Card.** Not needed. The Self-Serve Subscription Agreement says: "In order to access those Services for which we require a fee ('Paid Services') you will be required to provide Cloudflare with your credit card information."

**Terms** (Service-Specific Terms, Developer Platform):
> "For clarity, you retain all applicable intellectual property or other proprietary rights in Inputs and Outputs to or from the Services."
> "Unless otherwise agreed, Cloudflare does not use any Customer Content to train generative AI tools."

Each model's own licence applies as a Third-Party Product. Free Services can be terminated "in our sole discretion".

**Verdict.** The best fit for your constraints: clean commercial terms, no training, 256K context and vision on one model, and a hard cap with no billing surprises. The daily budget is the constraint, so spend neurons on the claims and vision steps.

---

## 7. GitHub Models (EXCLUDED)

Checked 2026-09-28. Source: https://docs.github.com/en/github-models/use-github-models/prototyping-with-ai-models

> "As of July 30, 2026, GitHub Models has been fully retired. The playground, model catalog, inference API, and bring your own key (BYOK) are no longer available to any customer."

---

## 8. NVIDIA NIM / build.nvidia.com (EXCLUDED)

Checked 2026-09-28. Source: NVIDIA API Trial Terms of Service, "v. September 19, 2025": https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf
- §1.2: "Subject to this Agreement, NVIDIA will provide you access to the API Service for limited trial purposes only and without use of the API Service or Generated Content in production."
- §1.4: "Unless you purchase a Subscription from NVIDIA or a Service Provider (as applicable), you may only use the API Service for internal testing and evaluation purposes, not in production."

Production use is forbidden.

---

## 9. SambaNova Cloud

Checked 2026-09-28. Sources:
- https://docs.sambanova.ai/docs/en/models/rate-limits.md
- https://docs.sambanova.ai/docs/en/models/sambacloud-models.md
- https://docs.sambanova.ai/docs/en/get-started/api-keys-urls.md
- https://docs.sambanova.ai/docs/en/features/function-calling.md
- https://sambanova.ai/cloud-end-user-license-agreement

**Free tier:**
- "**Free Tier**: Applied when there is no payment method linked with your account". So no card.
- Free Tier limits per model: 20 RPM, 20 RPD, 200,000 TPD.

| Model ID | Context | Inputs | Tier |
|---|---|---|---|
| `gpt-oss-120b` | 128k | text | Production |
| `DeepSeek-V3.1` | 128k | text | Production |
| `Meta-Llama-3.3-70B-Instruct` | 128k | text | Production |
| `DeepSeek-V3.2` | 32k | text | Preview |
| `gemma-4-31B-it` | 128k | text, image, video | Preview |

"Preview models are intended for evaluation purposes and developer experimentation only, and should not be used in production environments."

**JSON.** `response_format` with `json_schema` is documented for function-calling models, including `gpt-oss-120b`, DeepSeek V3.1/V3.2 and Llama 3.3 70B. Gemma 4 is not listed.

**Endpoint (verified):** `https://api.sambanova.ai/v1`

**Terms** (SambaCloud End User License Agreement):
- "Customer Content" includes "any computational results that you or your Users derive from the foregoing through their use of the Service".
- §2.1: "As between the parties, Customer or its licensors retain all right, title and interest in and to the Customer Content."
- §1.5(g): no publishing benchmarks without consent.

**Conflict.** A third-party site (freellmapi.co) says the free tier was retired; the official docs checked today still describe it.

**Verdict.** Usable as a tertiary text backup: `gpt-oss-120b`, 128k. 200K TPD allows only about 2 calls of 100K tokens a day. Its only vision model is Preview.

---

## 10. Others

### Z.ai (Zhipu), included as a backup

Checked 2026-09-28. Sources:
- https://docs.z.ai/guides/overview/pricing.md
- https://docs.z.ai/guides/llm/glm-4.7.md
- https://docs.z.ai/guides/vlm/glm-4.6v.md
- https://docs.z.ai/guides/capabilities/struct-output.md
- https://docs.z.ai/openapi.json
- https://docs.z.ai/legal-agreement/terms-of-use.md ("Last Update: April 14, 2026")

**Free models** (the pricing table shows Free / Free / Free / Free for input, cached input, storage and output):
- `glm-4.7-flash`: "Lightweight, Completely Free", 200K context, 128K max output.
- `glm-4.5-flash`
- `glm-4.6v-flash` (vision): "Lightweight, Completely Free", input "Video / Image / Text / File", 128K context.

**JSON:** `response_format={"type":"json_object"}`.

**Endpoint:** `https://api.z.ai/api/paas/v4/` (OpenAI-style `/chat/completions`)

**Unknowns.** Rate and concurrency limits are only in the logged-in console (the docs link redirects to `z.ai/manage-apikey/rate-limits`), so UNVERIFIED. Card requirement: UNVERIFIED.

**Terms:**
- Scope: "...governing your access and use of Z.ai for services or tools for your own purposes, internal organizational use, or for the benefit of end users."
- Ownership: "you retain all rights, title, and interest in the Prompts you submit and the Outputs generated specifically at your request..."
- AI labelling, relevant to YouTube: "AI-generated Outputs shall be prominently marked at reasonable locations to indicate that it is generated by AI." Also, no "falsely claiming that AI generated content ('Outputs') is human-created". YouTube's altered/synthetic-content disclosure plus a line in the description should cover this, but it is an obligation you take on.
- Data: "For individual users, we may use User Content to provide, maintain, develop, and improve our Services..."
- The provider is JINGSHENG HENGXING TECHNOLOGY PTE. LTD. (Singapore).

### Excluded

- **Hugging Face Inference Providers:** Free Users get "$0.10, subject to change" of monthly credits (https://huggingface.co/docs/inference-providers/pricing). Negligible.
- **Together AI:** "Together AI does not currently offer free trials. Access to the Together platform requires a minimum $5 credit purchase." (https://docs.together.ai/docs/billing)
- **Chutes:** "We do not offer a free tier at this time." (https://chutes.ai/pricing, FAQ)
- **Kluster.ai:** the domain does not resolve (DNS failure on 2026-09-28). Treat as defunct (UNVERIFIED).
- **Cohere:** "evaluation keys (free but limited in usage), and production keys (paid and much less limited in usage)"; "Trial keys ... are limited to 1,000 API calls a month." (https://docs.cohere.com/docs/rate-limits). Free keys are for evaluation.
- **Alibaba Model Studio** and **Fireworks:** one-time trial credits only (third-party reports; UNVERIFIED). Not recurring-free.

---

## Caveats that matter

1. **Free tiers churn fast.** GitHub Models was retired, Cerebras dropped its permanent free tier, Gemini 2.5 was closed to new users, and Mistral retired models in July and August. Keep the pipeline provider-agnostic (OpenAI-compatible clients, model IDs in config) and re-check monthly.
2. **Do not multiply accounts, projects or keys.**
   - Google's §2(d) anti-circumvention clause is enforced, and Google has restricted projects for "operating multiple projects as a single project".
   - OpenRouter says extra accounts or keys don't raise limits.
   - Groq bans use "intended to avoid incurring Fees".
   - Spreading work across **different providers** and **different models** under one account each is fine.
3. **Preview and beta models are not for production:** Groq Preview (`qwen/qwen3.8-27b`), SambaNova Preview (`gemma-4-31B-it`, `DeepSeek-V3.2`), and Mistral Labs/Preview models (which are also trained on). Gemini preview models have tighter limits.
4. **Training on free-tier data:**
   - Gemini free tier: yes, including human review.
   - Mistral Free: yes, with an opt-out.
   - Z.ai: may use.
   - OpenRouter: depends on the upstream provider.
   - Cloudflare and Groq: no.
   - Your sources are public history texts, so the risk is low. Never send keys or private data.
5. **JSON reliability differs.** Cloudflare doesn't guarantee schema adherence. Always validate against your JSON Schema and retry or repair. Use strict `json_schema` where offered (Groq, SambaNova, Gemini, Mistral).
6. **Model licences flow through.** Gemma 4 is Apache-2.0 (verified). The Llama 4 Community License (Scout), NVIDIA Nemotron and Qwen licences were not checked (UNVERIFIED); read them before depending on those models.
7. **Vision cost is unmeasured.** Tokens per image for Gemma 4 and Llama 4 Scout on Cloudflare and OpenRouter are UNVERIFIED. Log `usage` on a test batch of 60 images before sizing the neuron budget.
8. **How Google was read.** Google pages came through a reader proxy and Internet Archive snapshots (1–26 days old) because `ai.google.dev` blocks this IP. The terms snapshot is from 27 Sep 2026; the effective date is unchanged since 23 Mar 2026.

---

## 11. Sign-ups and live tests (evening of 2026-09-28)

The owner asked for Shorts to be made around the clock without the free quota stopping them, to today's standard or
better. What was tried, on the channel's own accounts (Chrome profile of <owner-email>):

| Provider | Result | Used? |
|---|---|---|
| OVHcloud AI Endpoints, anonymous | Works with no account (limits and terms in the next section). From Modal, a Qwen3.5-397B call succeeded 1 time in 9, gpt-oss-120b 0 in 9, Qwen3.8-27B 3 in 6 and Qwen3.6-27B 3 in 4: the 2-a-minute limit is shared by everyone on the same address. From the Mac (a shared office address), Qwen3.5-397B and gpt-oss-120b got 429 on every try for several minutes. OVH rejects `chat_template_kwargs` (400); without `reasoning_effort: "low"` Qwen3.8-27B spent all 16,384 output tokens reasoning and returned no content | Yes, best effort: Qwen3.5-397B ahead of Gemma, the 27B models after it |
| Mistral, free plan | Signed up with Google. Training on the account's API calls is turned off (Admin, Privacy). The Limits page allows the Ministral models 30 requests a minute and 937,500 tokens a minute each; `mistral-small-2603` and `mistral-medium-3-5` show 0 requests a minute, and `mistral-large-2512` and the GLM models answer 403 `tier_not_allowed`. Mistral Pro ($14.99 a month) was not taken. Live: `ministral-14b-2512` keeps to a JSON schema and read two drawn pictures correctly in 2 s, but its ep036 script broke the hook (18 words for 12) and word-count (102 for 105 to 135) rules through both fix rounds | Yes: research, picture picks and checks, never scripts (`YTC_MISTRAL_API_KEY`) |
| Groq | Google sign-in completes, then `console.groq.com/authenticate` says the address "does not belong to any organizations" and offers the sign-in again; no account was made | No |
| SambaNova Cloud | Signed up (profile: name, India, "Other", company "Days of Odd"; payment skipped). The console and plans page now read "Add a payment method and purchase credits to run your first requests", so the free tier described in section 9 is gone (that section's conflict is settled). No key was made | No |
| OpenRouter | The owner passed the human check and signed in later that evening. Key "days-of-odd studio": free tier, 50 free requests a day in total, a $1 limit. Of the free models only Dots3-Note Preview passed (section below) | Yes: Dots3 writes and researches after Qwen3.5-397B, and doesn't judge (`YTC_OPENROUTER_API_KEY`) |
| Cloudflare Workers AI | Not tried: it needs an account and an API token | No |

Writer comparison on ep036's stored research, with every Flash model left out:

- `gemini-3.1-flash-lite` wrote a script that met every rule in one call (8 s) and kept the facts, including
  "about 60 pounds, roughly 11,000 pounds today". Weaker than Flash's final script on detail (no 1668 banquet,
  no Old Bailey case), and one line was muddled.
- `gemma-4-31b-it` needed a fix round, changed "11,000 pounds" to "11,000 dollars", and its last line repeated
  the hook word for word.
- `ministral-14b-2512` failed the rules after both fix rounds (above).
- `gemini-3.5-flash-lite` returned 503 "high demand" twice in a row on 2026-09-28 at 18:45 IST, which is why
  every ladder keeps several models from different providers.

Result in `pipeline/src/ytc/llm.py`: scripts go Flash, Flash-Lite, Qwen3.5-397B (OVH), Gemma, then the OVH 27B
models; research, picks and topics go Flash, Flash-Lite, Qwen3.5-397B, Gemma, then the OVH 27B models and Ministral.
The review stays on Flash while 9 or more Shorts are ready.

### Kilo gateway and Requesty (checked later the same evening, not used)

- **Kilo AI Gateway** (`https://api.kilo.ai/api/gateway`, OpenAI-compatible). Its docs
  (`kilo.ai/docs/llms.txt`) say "The gateway allows unauthenticated access for free models only ... (200 requests
  per hour per IP)" and that it works with "any OpenAI-compatible client in any language". Its terms
  (`kilo.ai/terms`, updated 2026-01-29) don't forbid commercial use, but they ban scrapers and getting around access
  controls, and give Kilo "a perpetual, irrevocable ... license to use such Customer Data to provide and improve the
  Service". The `:free` models come from OpenRouter's shared free pool:
  - `qwen/qwen3.8-27b:free` answered 1 try in 17: 1 in 5 from the Mac, and 0 in 12 from Modal over five minutes.
    Every failure was a 429 "temporarily rate-limited upstream" (`limit_source: upstream_provider_shared_pool`).
  - `thinkingmachines/inkling-small:free` had used its shared daily cap of 1,000.
  - `kilo-auto/free` routed to `nvidia/nemotron-3-ultra-550b-a55b:free`, which falls under NVIDIA's trial terms.
  - `stepfun/step-3.7-flash:free` answered but ignored the JSON schema.
  - `dots-studio/dots-3-note-preview:free` answered correctly, but it is a preview model.

  Not used: the pool is too busy to add capacity, and the models that did answer are untested previews.
- **Requesty.** The research pass reported a free plan of 200 requests a day that includes `google/gemma-4-31b-it`
  (262K context, reads pictures, not trained on). This was not re-checked and no account was made, because:
  - it needs another account on the owner's Google sign-in;
  - its free model is the Gemma that trailed Flash-Lite as a writer (above);
  - the models already in place made ep042 end to end.

  Worth adding only if those models stop answering.

### OpenRouter with the channel's key (later the same evening)

The owner signed in. Onboarding was answered "Individual" and its address step skipped. One key was made ("days-of-odd
studio", no expiry, a $1 limit); the two keys onboarding made by itself were deleted. `GET /api/v1/key` reports
`is_free_tier: true` and a `free_model_daily_requests` limit of 50. Twenty models are priced at zero
(`/api/v1/models`); apart from the four below, they are coding, tiny, safety, "stealth" or NVIDIA trial models.
Data policies are from each model page's `dataPolicy`.

| Model (provider) | Data policy | Result |
|---|---|---|
| `dots-studio/dots-3-note-preview:free` (AtlasCloud, fp8) | No training; prompts retained | Kept the JSON schema. The ship question right (16:32) in 20 s, two drawn pictures right in 10 s, and, through `ytc.llm`, a 53,545-token prompt right in 11 s. Wrote ep036's script to every rule in one call (142 s) |
| `google/gemma-4-31b-it:free` (Google AI Studio) | No training; retained 55 days | Right answers but its own field names, then 429 "rate-limited" on 8 tries in 8 over 9 minutes |
| `qwen/qwen3.8-27b:free` (ModelRun) | No training, not retained | 429 "temporarily rate-limited upstream" on 4 tries in 4 |
| `thinkingmachines/inkling:free` (Thinking Machines) | Trains on prompts and outputs ("TML Free Research API Tier" terms) | 403 "only available on agentic harnesses" |

Dots3's ep036 draft kept the 1668 banquet for the French ambassador, the 1675 painting, the pineries, the 1807
sentence for stealing seven pineapples, and the Dunmore Pineapple; Flash-Lite's draft had neither the banquet, the
painting, nor the trial. It reads less smoothly aloud than Flash's reviewed script ("£60", "returned to the lessor").
It hasn't been tried as a judge, so it doesn't judge. These tests used 12 of the day's 50 requests: OpenRouter didn't
count every rate-limited try.

### codecraftapi.com (not used)

The owner made an account on it and asked for a sign-in from a cloud machine, since the site doesn't open on the Mac.
Not done:

- The domain was registered on 2026-08-22 through Nameslink, a Hong Kong registrar, and sits behind Cloudflare
  (`https://rdap.verisign.com/com/v1/domain/codecraftapi.com`). The Mac's network filter blocks it.
- It is spread through a freebie forum with a promo code for "100M tokens per month, free for a year" of the
  Claude, Gemini and GPT families ([NodeLoc, 2026-09-10](https://www.nodeloc.com/t/topic/108127)); the same poster's
  next thread sells "30M Tokens for $1.20" or "unlimited for $50/month"
  ([NodeLoc, 2026-09-12](https://www.nodeloc.com/t/topic/108337)).
- An independent relay probe flagged "Model substitution detected": `kimi-k3`, `grok-4.6` and `gemini-3.7-flash`
  answered as Anthropic models, and `deepseek-v4-pro-max` and `grok-4.5` were also flagged
  ([BazaarLink](https://bazaarlink.ai/en/probe/relay/codecraftapi.com), probes from 2026-09-09 to 2026-09-22). The
  same site notes that "much of the cheap Claude capacity on the market is reverse-proxied out of products like Kiro,
  Antigravity or GitHub Copilot" (<https://bazaarlink.ai/en/probe>), the source rejected in the next section.
- Every prompt would pass through an operator nobody can check, and a Google sign-in automated from a data centre
  can make Google lock <owner-email>, which owns the channel.

### Gateways that pool free sign-ins (rejected)

OmniRoute ([diegosouzapw/OmniRoute](https://github.com/diegosouzapw/OmniRoute): about 70,900 stars, pushed
2026-09-27, MIT, not archived; checked 2026-09-28) and similar gateways (9router, CLIProxyAPI, AIClient2API) were
checked in `.scratch/research3/` (github-survey.md, oauth-risk.md). Their "unlimited" free models come from three
things: consumer OAuth sessions (Gemini CLI, Antigravity, Kiro, Claude, Cursor) proxied against those products'
terms, scraped web chat apps, and many accounts rotated to stretch free tiers. Google's Antigravity terms call
third-party access "a breach of this Agreement"; there was a ban wave in February 2026 and bans are still reported;
OmniRoute's own issues report banned Gemini credentials (#11763) and suspensions from its health checks (#14780), and
its terms flags are advisory, not a routing gate. Running it would put the owner's Google account, which also holds
the YouTube channel, at risk. The official free APIs above give the same effect within their terms.
