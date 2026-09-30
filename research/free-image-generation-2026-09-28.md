# Free image generation for "Days of Odd" Shorts

**Decision (2026-09-28): no AI-generated pictures for now.** Beats that archives can't illustrate get a
designed title card (a date, a number, or a quote the script cites) or a reframed earlier picture instead
(`pipeline/src/ytc/plates.py`). For a history channel, a generated "photo" of a real event needs YouTube's
synthetic-media disclosure and invites "this is fake" comments, while cards need neither and cost nothing.
If a later test shows cards hurting retention, the options below are ready, best first.

All facts checked **2026-09-28** against the pages linked in each section. Pages were read with
`curl` or web search. No accounts were created, no API calls were made, and no browser or work
account was touched, so nothing here has been tested live. Anything I could not confirm from a
primary source is marked **UNVERIFIED**.

## Short answer

- **Gemini API free tier: no image models.** Every Nano Banana model is listed as "Not available" on
  the free tier, and Imagen has been shut down.
- **The work (Salesforce) Gemini account is not an option.** The Workspace Gemini app has no API. The
  enterprise APIs that do exist run inside the employer's own Google Cloud project and billing. Google's
  Workspace terms also make anything generated there the employer's "Customer Data", and Salesforce's
  public Code of Conduct requires approval before any outside business activity.
- **Cloudflare Workers AI `flux-2-klein-4b` is the best free option.** It renders native 9:16 up to
  1080×1920, fits about 31–48 full-HD images a day (or 63–97 at 768×1344) in the 10,000 free neurons,
  and allows commercial use of outputs.
- **Best backup: self-host FLUX.2 klein 4B (Apache-2.0) on a Modal L4.** Estimated cost is about
  $0.01 per image including a cold start, so roughly $0.6–$2.6 a month from the $30 free credit.

---

## Question 1: Gemini API free tier (AI Studio key)

Checked 2026-09-28.

### Verdict

No image-generation model is on the free tier. The free tier has no image RPD or RPM, because the
models themselves are not available on it. Google AI Studio's web playground is free, but it is not an
API a server can call unattended.

### Image models and free-tier status

Source: [Gemini API pricing](https://ai.google.dev/gemini-api/docs/pricing), "Last updated 2026-09-24 UTC".

| Model (API id) | Free tier | Paid price (quoted) |
|---|---|---|
| Nano Banana 2 (`gemini-3.1-flash-image`) | "Not available" | "$60.00 (images) Equivalent to $0.045 per 0.5K image\*, $0.067 per 1K image\*, $0.101 per 2K image\*, and $0.151 per 4K image\*" |
| Nano Banana 2 Lite (`gemini-3.1-flash-lite-image`) | "Not available" | "$30.00 (images) Equivalent to $0.0336 per 1K resolution image\*" (batch: $0.0168) |
| Nano Banana Pro (`gemini-3-pro-image`) | "Not available" | "$0.134 per 1K/2K image", "$0.24 per 4K image" |
| Nano Banana (`gemini-2.5-flash-image`) | "Not available" | $0.039 per image. Warning on the page: "deprecated and will be shut down on October 2, 2026." |
| Imagen 4 (`imagen-4.0-generate`) | n/a | [Imagen page](https://ai.google.dev/gemini-api/docs/imagen) (updated 2026-09-17): "Imagen models are shut down. Use Nano Banana for image generation." |

- The pricing page also says "Google AI Studio usage is free of charge in all available regions".
  That refers to the web UI, not API calls.
- The [models page](https://ai.google.dev/gemini-api/docs/models) lists no other image-output model.
  Gemini Omni Flash is video only, and Imagen 4 is marked "(Shut down)".
- Independent 2026 write-ups agree: "every Nano Banana image model … is marked `Free Tier: Not
  available`" ([modellix](https://www.modellix.ai/blog/nano-banana-api-free/)). One of them states a
  $10 prepay, but Google's billing page says $5 (see below).

### Rate limits

Source: [rate limits page](https://ai.google.dev/gemini-api/docs/rate-limits), updated 2026-09-02.

- The page no longer publishes a per-model table: "View your active rate limits in AI Studio".
- "Rate limits are applied per project, not per API key. Requests per day (RPD) quotas reset at midnight Pacific time."
- "Images per minute, or IPM, is only calculated for models capable of generating images (Nano Banana)".
- "Specified rate limits are not guaranteed and actual capacity may vary."
- **UNVERIFIED:** what the AI Studio quota screen shows for image models on a free project. I did not
  log in.

### Billing (why "cheap" is still not "free")

Source: [billing page](https://ai.google.dev/gemini-api/docs/billing), updated 2026-09-20.

- Tier qualification: Free = "Active project or free trial"; Tier 1 = "Set up and link an active
  billing account".
- Paid setup requires "prepaying to add a minimum of $5".
- "No, the Google Cloud Welcome credit or free trial credit can't be used towards the Gemini API or AI Studio."
- "No, starting March 2026, Gemini API usage costs are specifically excluded from the $300 Google Cloud Free Trial program."

### Watermark

Source: [image generation page](https://ai.google.dev/gemini-api/docs/image-generation), updated 2026-09-23.

- "All generated images include a SynthID watermark."
- **UNVERIFIED:** whether API images also carry C2PA metadata. This matters because YouTube
  auto-labels C2PA content (see the YouTube section).

### Terms relevant to commercial use

Source: [Gemini API Additional Terms](https://ai.google.dev/gemini-api/terms), "Effective March 23, 2026".

- Ownership: "Google won't claim ownership over that content. You acknowledge that Google may generate
  the same or similar content for others"; "You're responsible for your use of generated content".
- Audience: "Use of Google AI Studio and Gemini API is for developers building with Google AI models
  for professional or business purposes, not for consumer use." Also: "You must be 18 years of age or
  older".
- Unpaid Services: content is "used to provide, improve, and develop Google products", "human
  reviewers may read, annotate, and process your API input and output", and "Do not submit sensitive,
  confidential, or personal information".
- Region: "You may use only Paid Services when making API Clients available to users in the European
  Economic Area, Switzerland, or the United Kingdom."
- [Generative AI Prohibited Use Policy](https://policies.google.com/terms/generative-ai/use-policy)
  (last modified December 17, 2024): "Misrepresenting the provenance of generated content by claiming
  it was created solely by a human, in order to deceive." It also allows exceptions for "educational,
  documentary, scientific, or artistic considerations".

---

## Question 2: using the employer's (Salesforce) Workspace Gemini

Checked 2026-09-28.

### Verdict

The expected answer holds, with one nuance. The Workspace Gemini app (gemini.google.com with a work
account) is web and mobile only, and there is no supported way to call it from a server. Google does
sell enterprise APIs that can generate images, but they run inside the employer's own Google Cloud
project, under its IAM and billing, so they are company resources and not a personal route. Using a
work account for a personal monetized channel is a real acceptable-use and IP risk, backed by both
Google's terms and Salesforce's public Code of Conduct.

### Is there an API?

**The Workspace Gemini app: no.**
- The work-account help page [Gemini for work](https://support.google.com/gemini/answer/14620100?hl=en)
  describes web and mobile apps with per-day UI quotas. For example, "Image generation & editing with
  Nano Banana 2 \*\* | Up to 20 images / day | Up to 100 images / day", with the footnote "\*\* Image
  generation & editing is in high demand. Limits may change frequently and will reset daily."
- The page says nothing about API access.
- The [Gemini Enterprise FAQ](https://cloud.google.com/gemini-enterprise/faq) says the app is "centrally
  managed from the Workspace admin console".
- Driving the web app from a headless browser is unsupported. It would also stall at Salesforce's
  Okta/SSO re-authentication, which cannot be completed unattended.

**AI Studio with the work account: technically reachable, but not usable.**
- [Workspace access page](https://ai.google.dev/gemini-api/docs/workspace): "All Google Workspace users
  have access to AI Studio by default", and admins can turn it off.
- Image models still need a billed project, since the free tier has none. That means either the
  employer's billing or the employer's cloud organization.

**Gemini Enterprise (Google Cloud): an API exists, but it is employer-owned.**
- The Discovery Engine
  [`streamAssist`](https://docs.cloud.google.com/gemini/enterprise/docs/reference/rest/v1alpha/projects.locations.collections.engines.assistants/streamAssist)
  method has a `toolsSpec.imageGenerationSpec` field.
- [Its prerequisites](https://docs.cloud.google.com/gemini/enterprise/docs/get-answers-from-streamassist):
  "The Discovery Engine API enabled for your Google Cloud", "A Discovery Engine role that has the
  `discoveryengine.assistants.assist` permission", and "An existing Gemini Enterprise app".
- The same applies to paid `generateContent` image generation on
  [Gemini Enterprise Agent Platform](https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/image-generation),
  formerly Vertex AI.
- All of these need the employer's project, identity and billing.

### What Google's Workspace terms say

Source: [Workspace Service Specific Terms](https://workspace.google.com/terms/service-terms/?hl=en), section 12.

- §12.12: "Generated Output means the data or content generated or received by the Customer or its End
  Users via Workspace Generative AI Services under the Customer's Workspace Account … **Generated Output
  is Customer Data.**" The "Customer" here is the employer. So images made with the work account
  belong in Salesforce's data estate, under its admin control and retention.
- §12.3 incorporates the Generative AI Prohibited Use Policy into the Workspace acceptable use policy.
- §12.5: the Customer "will not allow End Users to use Workspace Generative AI Services in a manner
  that exceeds the limits specified by Google".
- The help page adds: "Keep Activity is on by default and can only be turned off by your account's
  Workspace administrator". It also says history is kept 18 months by default, and "If your
  administrator turns on Gemini history retention, you won't be able to change your activity
  settings". In other words, the employer can retain and review what was generated.

### Employer policy

Source: [Salesforce Code of Conduct, "Building Trust with Our Company and Investors"](https://www.salesforce.com/company/legal/compliance/code-of-conduct/building-trust-company/), public page.

- "Unless noted otherwise, side jobs or personal business activities need to be disclosed to the
  Salesforce Legal team for review and approval, before we engage in them, as established by the
  Conflict of Interest Policy."
- "Not engaging in any outside business activities before obtaining complete approval for them".
- "Outside business activities of all types require disclosure and approval using the Conflict of
  Interest Submission Portal before you can engage in them."
- "Employees are generally prohibited from taking personal advantage of business or investment
  opportunities discovered through the use of company property, business, or information."

**UNVERIFIED:** Salesforce's internal acceptable-use policy for company AI tools, and the owner's
invention-assignment agreement. Both are internal, and I deliberately did not access work systems.
Typical employer policies limit company tools to business use, let the employer monitor and retain
the data, and can reach IP created with company resources.

**Practical note:** the monetized channel itself likely needs a conflict-of-interest disclosure under
the Code, whichever image tool it uses.

---

## Question 3: Cloudflare Workers AI (10,000 free neurons/day)

Checked 2026-09-28.

### Free allocation

Source: [Workers AI pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/), updated Sep 17, 2026.

- "Our free allocation allows anyone to use a total of 10,000 Neurons per day at no charge."
- Overage is charged at "$0.011 / 1,000 Neurons", but on the Free plan the overage row reads "N/A -
  Upgrade to Workers Paid". Requests fail with error 3036 instead of billing.
- "All limits reset daily at 00:00 UTC".
- Models that need a paid plan are only kimi-k2.6, kimi-k2.7-code, glm-5.2, glm-5.3, glm-5.3-flash,
  deepseek-v4-flash-0731 and deepseek-v4-pro-0813. No image model is on that list.
- The [limits page](https://developers.cloudflare.com/workers-ai/platform/limits/) gives Text-to-Image
  720 requests per minute.

### Current text-to-image models

Source: [model catalog](https://developers.cloudflare.com/workers-ai/models/). The `@cf/deepgram/flux`
entry is speech recognition, not an image model.

| Model | Max output size | Neuron price (pricing table) | Weights license / terms link |
|---|---|---|---|
| `@cf/black-forest-labs/flux-2-klein-4b` (launched 2026-01-15, Partner) | width and height 256–1920, "steps parameter is fixed at 4" | "5.37 neurons per input 512x512 tile", 26.05 per output tile ($0.000287) | Apache-2.0 weights; terms link is the [BFL ToS](https://bfl.ai/legal/terms-of-service) |
| `@cf/black-forest-labs/flux-2-klein-9b` (2026-01-28) | 256–1920 | $0.015 (1363.64 neurons) for the first MP (1024×1024), $0.002 per extra MP or input MP | FLUX non-commercial weights; the hosted API falls under the BFL ToS |
| `@cf/black-forest-labs/flux-2-dev` (2025-11-25) | 256–1920; takes `steps` | 18.75 neurons per input tile per step, 37.50 per output tile per step | Non-commercial weights; BFL ToS for the hosted API |
| `@cf/black-forest-labs/flux-1-schnell` | schema has only `prompt` and `steps` (max 8, default 4), so output is 1024×1024 (from community reports; **UNVERIFIED** in the docs) | 4.80 neurons per tile + 9.60 per step | Apache-2.0; BFL ToS |
| `@cf/leonardo/lucid-origin` | 0–2500, default 1120; steps 1–40 | 636 per tile + 12 per step | [Leonardo ToS](https://leonardo.ai/terms-of-service) |
| `@cf/leonardo/phoenix-1.0` | up to 2048, default 1024; default 25 steps | 530 per tile + 10 per step | Leonardo ToS |
| `@cf/bytedance/stable-diffusion-xl-lightning` (Beta) | 256–2048 | model page: "$0.00 per step" | openrail++ |
| `@cf/stabilityai/stable-diffusion-xl-base-1.0` (Beta) | 256–2048; up to 20 steps | "$0.00 per step" | openrail++ |
| `@cf/lykon/dreamshaper-8-lcm` | **UNVERIFIED** | no price shown (**UNVERIFIED**) | creativeml-openrail-m |
| `@cf/runwayml/stable-diffusion-v1-5-inpainting` (Beta) | inpainting, needs a mask | **UNVERIFIED** | n/a |

### Portrait capacity per day

Cloudflare does not document two things:

- **Tile counting.** A tile may be counted by area (768×1344 = 3.94 tiles) or by rounding each side
  up (2 × 3 = 6 tiles).
- **Step billing.** For flux-1-schnell and the Leonardo models, the step fee may be charged once per
  image or once per tile. One community answer says "The steps are applied to each tile".

The table shows both readings. Paid-equivalent cost is neurons × $0.011 / 1,000.

| Model and setting | Neurons per image | Images per 10,000 neurons/day |
|---|---|---|
| **klein-4b, 768×1344** | 102.6 by area / 156.3 rounded up | **97 / 63** |
| **klein-4b, 1080×1920 (full-HD Shorts frame)** | 206.1 / 312.6 | **48 / 31** |
| klein-4b, 720×1280 | 91.6 / 156.3 | 109 / 63 |
| klein-4b with one style reference image under 512×512 | +5.37 | about 1–5% fewer |
| flux-1-schnell, 1024² at 4 steps (crop to 9:16 gives 576×1024) | 57.6 (step fee per image) / 172.8 (per tile) | 173 / 57 |
| flux-1-schnell, 1024² at 8 steps | 96 / 326.4 | 104 / 30 |
| klein-9b, 768×1344 (under 1 MP) | 1363.6 | 7 |
| flux-2-dev, 768×1344 at 20 / 25 steps | 2953 / 3691 by area (4500 / 5625 rounded) | 3 / 2 (2 / 1) |
| phoenix-1.0, 768×1344 at 25 steps | 2337 / 3430 | 4 / 2 |
| lucid-origin, 768×1344 at 25 steps (steps assumed) | 2804 / 4116 | 3 / 2 |
| SDXL base or Lightning (Beta) | 0 | limited only by 720 requests/min |

One test call would settle which reading is right: run a single 768×1344 klein-4b request and read the
neuron count in the Workers AI dashboard.

### How to call klein-4b

Source: [Cloudflare changelog, 2026-01-15](https://developers.cloudflare.com/changelog/post/2026-01-15-flux-2-klein-4b-workers-ai/).

- Input is multipart form data even for a text-only prompt ("uses multipart form data inputs, even if
  you just have a prompt").
- Output is "Generated image as Base64 string".
- Reference images: "The model supports up to 4 input images", named `input_image_0` to
  `input_image_3`, and "All input images must be smaller than 512x512". A public-domain engraving
  from the channel's own Wikimedia Commons sources can be passed as `input_image_0` with a prompt
  like "… in the style of image 0" to keep a consistent period look.

```bash
curl --request POST \
  --url "https://api.cloudflare.com/client/v4/accounts/$CF_ACCOUNT_ID/ai/run/@cf/black-forest-labs/flux-2-klein-4b" \
  --header "Authorization: Bearer $CF_API_TOKEN" \
  --header 'Content-Type: multipart/form-data' \
  --form 'prompt=19th-century steel engraving, crosshatched, of ...' \
  --form width=1080 --form height=1920 --form seed=42
```

### Output rights and terms

**Cloudflare** ([Service-Specific Terms](https://www.cloudflare.com/service-specific-terms-developer-platform/), "Last updated: September 28, 2026"):
- "… outputs received from the Services based on your Input ("Outputs") constitute Customer Content.
  For clarity, you retain all applicable intellectual property or other proprietary rights in Inputs
  and Outputs".
- "Cloudflare does not use any Customer Content to train generative AI tools".
- Models "constitute Third-Party Products … you agree to the applicable third-party terms".

**BFL** ([Terms of Service](https://bfl.ai/legal/terms-of-service), last revised August 1, 2026). This is
what Cloudflare links for every FLUX model.
- 1.2(a): "We claim no ownership rights in and to Your Content, and you may use Your Content … for your own purposes".
- 1.3(e): commercial exploitation of the Services is barred "except for your use of your Output".
- 1.3(m): you may not represent "that the Output is entirely human-generated or that the Output
  depicts an actual photograph of a real event".
- 1.3(p): you may not remove "AI content marking or labelling or transparency metadata".
- 18+ only.
- 1.2(e): BFL gets a licence to train on your content, with opt-out via legal@blackforestlabs.ai.
  **UNVERIFIED:** whether 1.2(e) applies to inference hosted by Cloudflare, since BFL may never receive
  the data.

**Weights licenses** (Hugging Face API, checked 2026-09-28): FLUX.1 schnell and FLUX.2 klein 4B are
`apache-2.0`. The klein 4B card says: "Open weights available for commercial use under the Apache 2.0
license". FLUX.2 dev and klein 9B use the `flux-non-commercial-license`. That only rules out
self-hosting them; hosted outputs fall under the BFL ToS above.

**Leonardo** ([ToS](https://leonardo.ai/terms-of-service), last updated 19 January 2026):
- 8.7: for free subscribers, "ownership of all Intellectual Property Rights in any Output … will vest
  in us upon creation".
- 8.3: paid subscribers own their outputs.
- **UNVERIFIED:** which rule applies to Cloudflare-hosted calls, where the caller is not a Leonardo
  subscriber at all. With that ambiguity plus only 2–4 images a day, avoid Leonardo models for a
  monetized channel.

**Watermarks:** Cloudflare documents none. **UNVERIFIED:** whether FLUX outputs on Cloudflare carry
invisible or C2PA marks.

---

## Question 4: other free options usable unattended with commercial rights

Checked 2026-09-28.

| Option | Free allowance now | Output rights | Verdict |
|---|---|---|---|
| Hugging Face Inference Providers | "$0.10, subject to change" per month for free users ([pricing](https://huggingface.co/docs/inference-providers/pricing)). HF's own example: FLUX.1-dev for 10 s at $0.00012/s "will be billed $0.0012". | depends on model and provider | Only a few dozen schnell-class images a month (**UNVERIFIED** provider prices). Not enough. |
| Hugging Face ZeroGPU Space | "Free account \| 5 minutes" of GPU per day on a "Half NVIDIA RTX Pro 6000 Blackwell \| 48GB"; free accounts "can host up to 2 ZeroGPU Spaces"; "exclusively compatible with the Gradio SDK" ([docs](https://huggingface.co/docs/hub/spaces-zerogpu)) | the model's license (klein 4B and Z-Image-Turbo are Apache-2.0) | Workable fallback in theory. **UNVERIFIED** whether HF accepts it as a production backend; queues and quota make it unreliable. |
| Pollinations | Paid Pollen now. Free Pollen only through Quests ("complete eligible Quests, and claim the rewards"). The legacy raw `pk_` key is "limited to 1 Pollen per IP per hour. Do not create new integrations around this flow." ([Pollen FAQ](https://github.com/pollinations/pollinations/blob/main/enter.pollinations.ai/POLLEN_FAQ.md)). Prices: flux.1-schnell 0.002 Pollen per image, klein-4b 0.005. | [Terms](https://pollinations.ai/terms): operated by "Myceli.AI OÜ"; "Model licences vary; verify before commercial use." | Not a stable free source. Watermark or logo status **UNVERIFIED**. |
| Together AI | "does not currently offer free trials. Access to the Together platform requires a minimum $5 credit purchase" ([billing](https://docs.together.ai/docs/billing)) | n/a | Not free. The current price list has no FLUX.1 schnell. |
| AI Horde | Free, run by volunteers; "no way to buy priority" ([mission](https://aihorde.net/mission)); queue order depends on kudos ([FAQ](https://github.com/Haidra-Org/AI-Horde/blob/main/FAQ.md)) | [Terms](https://aihorde.net/terms/): "The website claims no rights on the outputs you generate, you are free to use them" (CreativeML Open RAIL-M) | Emergency fallback only. Anonymous text-to-image generations are "always" shared "with the LAION non-profit", including prompts. The FAQ says profit-making integrations "**must** give back to the AI horde at least as much as you take out to make a profit". Speed varies with volunteer workers. |
| Replicate | "You can run select models on Replicate for free, but after a bit you'll be asked to set up billing." ([billing](https://replicate.com/docs/topics/billing)) | n/a | Not a recurring free tier. |
| NVIDIA build.nvidia.com | Trial API | [Trial ToS §1.2](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf): "for limited trial purposes only and without use of the API Service or Generated Content in production" | Not allowed. |
| **Modal, self-hosted open weights** | "$30 / month free compute" on Starter; "Volumes … includes 1 TiB / mo free" ([pricing](https://modal.com/pricing)) | Apache-2.0 (klein 4B, schnell, Z-Image-Turbo) | **Best backup.** See the estimate below. |

### Modal estimate: FLUX at 768×1344, 4 steps, including cold start

Prices from [modal.com/pricing](https://modal.com/pricing), checked 2026-09-28:
- L4 "$0.000222 / sec", A10 "$0.000306 / sec", L40S $0.000542, H100 $0.001097.
- CPU "$0.0000131 / core / sec"; memory "$0.00000222 / GiB / sec".
- The brief's $0.000164/s figure is the **T4** price, not the L4.

Scaling behaviour ([cold start guide](https://modal.com/docs/guide/cold-start)): by default "the
maximum idle time is 60 seconds", configurable "between two seconds and twenty minutes". Idle time
inside that window is billed.

Memory fit:
- FLUX.1 schnell's bf16 transformer (about 23.8 GB) plus T5 (about 9.5 GB) does not fit a 24 GB L4,
  so it needs FP8 weights, which the L4 (Ada) supports.
- FLUX.2 klein 4B "fits in ~13GB VRAM" (model card), so it runs natively on an L4.
- Z-Image-Turbo (Apache-2.0, 6B, 8 steps) "fits comfortably within 16G VRAM consumer devices".

**Assumptions (UNVERIFIED, not benchmarked):**
- 4 CPU cores and 32 GiB RAM reserved.
- Weights already on a Modal Volume.
- `scaledown_window=2`.
- Cold start 45–60 s.
- Per-image time: 10 s for schnell FP8 on L4, about 4 s for klein 4B on L4.
- For reference: Modal's own H100 example reports "clients received images in about 1.2 seconds".

| Setup | Warm cost per image | One Short (cold start + 2 images) | Per month at 1 / 3 Shorts a day | Shorts covered by $30 |
|---|---|---|---|---|
| **FLUX.2 klein 4B bf16 on L4** | $0.0014 | **$0.019** ($0.0095 per image) | $0.57 / $1.71 | about 1,580 |
| FLUX.1 schnell FP8 on L4 | $0.0035 | $0.028 ($0.014 per image) | $0.85 / $2.55 | about 1,060 |
| FLUX.1 schnell 8-bit/NF4 on A10 (no native FP8) | $0.0060 | $0.039 | $1.16 / $3.48 | about 780 |
| FLUX.1 schnell bf16 on L40S | $0.0020 | $0.039 | $1.16 / $3.47 | about 780 |
| FLUX.1 schnell bf16 on H100 | $0.0015 | $0.060 | $1.81 / $5.43 | about 500 |

- The cold start dominates, so the cheapest GPU wins.
- Generating the whole day's images in one container run cuts this further. For 6 images a day on an
  L4, that is about $0.74 a month with klein 4B.
- FLUX.1 schnell's Hugging Face repo is gated (a one-time click to accept). klein 4B and Z-Image-Turbo
  are not gated.

---

## YouTube disclosure (for the pipeline)

Checked 2026-09-28. Source: [YouTube Help, disclosing altered or synthetic content](https://support.google.com/youtube/answer/14328491).

- Disclosure is required when content "Generates a realistic scene that didn't actually occur", among
  other cases.
- "Creators don't need to disclose non-realistic content that's made with AI". Clearly engraving-style
  illustrations likely fall here, but the planned on-screen label is still wise.
- "Disclosing AI content won't limit a video's audience or impact its eligibility to earn money."
- Content carrying C2PA metadata can be labelled automatically.
- For unattended uploads, the flag is `status.containsSyntheticMedia` on `videos.insert` /
  `videos.update` ([YouTube Data API](https://developers.google.com/youtube/v3/docs/videos)). It was
  added on October 30, 2024.
- Never present an illustration as an archival photo. BFL ToS 1.3(m) and Google's Prohibited Use
  Policy both forbid misrepresenting AI provenance.

---

## Ranked recommendation

The channel needs 1–2 engraving-style illustrations per Short, so about 2–6 images a day at 1–3 Shorts
a day.

1. **Cloudflare Workers AI `@cf/black-forest-labs/flux-2-klein-4b`.**
   - Capacity: about 31–48 images a day at native 1080×1920, or 63–97 at 768×1344, inside the free
     10,000 neurons. That leaves room for 5–15 candidates per slot, picked by a judge step.
   - Cost: $0 on the Free plan, which stops rather than billing.
   - Rights: Apache-2.0 weights, commercial output rights under the BFL ToS, and Cloudflare says "you
     retain all applicable intellectual property" in outputs.
   - Style: add a small public-domain engraving as `input_image_0` for a consistent look.
   - Watch-outs: an undocumented tile formula (check with one call), a single free allowance shared
     across all Workers AI models, and a new third-party-terms layer.
2. **Modal, self-hosted FLUX.2 klein 4B on an L4** (Apache-2.0, same model family, so the look matches
   when failing over).
   - Cost: about $0.01 per image including the cold start, so $0.6–$1.7 a month from the $30 credit.
   - No provider terms beyond Apache-2.0 and no provider watermark.
   - Use FLUX.1 schnell FP8 or Z-Image-Turbo as alternatives if the style suits better.
3. **Cloudflare `flux-1-schnell`** (fixed 1024², so crop or upscale; 57–173 a day) or the **SDXL Beta
   models** ($0 per step) as secondary models in the same Cloudflare account. SDXL quality is lower,
   and Beta models can change.
4. **AI Horde** as a last-resort fallback. It is free, but speed is unpredictable, anonymous prompts
   are shared with LAION, and profit-making use is expected to give back.

**Not viable:**
- Gemini API free tier: no image models.
- Work Gemini: no API, the output is the employer's Customer Data, and Salesforce's conflict-of-interest
  rules apply.
- Together (no free tier), Replicate (not recurring), NVIDIA trial (no production use).
- Hugging Face credits ($0.10 a month) and Pollinations (quest-only free credits, legacy flow
  deprecated).
- Leonardo models on Cloudflare (unclear ownership, 2–4 images a day).
- Self-hosting FLUX.2 dev or klein 9B (non-commercial weights).
