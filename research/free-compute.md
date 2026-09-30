**Bottom line:** No single platform covers this workload for free. Without a card, the best setup is Cloudflare Workers AI plus a Hugging Face ZeroGPU Space and Gemini's free TTS. With a card on file, Modal's recurring $30/month is by far the most powerful option and the only one that realistically covers Wan 2.2 video. NVIDIA, AMD, Colab, and GitHub Actions are ruled out for a monetized, automated channel, and Lightning needs written consent first.

**Main platforms**

- **Modal** ([pricing](https://modal.com/pricing), [billing](https://modal.com/docs/guide/billing), [terms](https://modal.com/legal/terms))
  - Starter plan: "$30 / month free compute", 10 GPU concurrency, 5 deployed crons.
  - **Card: yes.** "you must have a payment method on file in order to use Modal".
  - Price per second: T4 $0.000164, L4 $0.000222, A10 $0.000306, L40S $0.000542, A100-80GB $0.000694, H100 $0.001097, H200 $0.001261, B200 $0.001736, B300 $0.001972. CPU is $0.0000131 per core.
  - Commercial use: "Input and Output shall be considered Customer Data". The only relevant prohibited use is "general file-hosting or media-serving".
  - Automation: Python SDK and `modal.Cron`. $1/day buys about 15 H100-minutes or 31 L40S-minutes.
- **Cloudflare Workers AI** ([pricing](https://developers.cloudflare.com/workers-ai/platform/pricing/), [terms](https://www.cloudflare.com/service-specific-terms-developer-platform/))
  - "10,000 Neurons per day at no charge", resetting at 00:00 UTC.
  - **Card: no.** The Workers Free plan is the default.
  - Commercial use: "you retain all applicable intellectual property… in Inputs and Outputs". Each model licensor's terms also apply.
  - Automation: REST API.
  - Daily capacity if the whole allowance goes to one model:
    - FLUX.1-schnell (57.6 Neurons per image at 4 steps): about 173 images.
    - FLUX.2-klein-4B: about 64–96 images at roughly 1 megapixel.
    - Leonardo Phoenix/Lucid Origin: 1–4 images.
    - MeloTTS: about 536 audio-minutes. Deepgram Aura-1: about 7,300 characters, or roughly 10 voiceovers. Aura-2-en: about 5 voiceovers.
    - Whisper-large-v3-turbo: about 214 minutes.
- **Hugging Face ZeroGPU** ([docs](https://huggingface.co/docs/hub/spaces-zerogpu), [API](https://huggingface.co/docs/hub/spaces-api-endpoints), [Spaces](https://huggingface.co/docs/hub/spaces-overview))
  - Daily GPU time: unauthenticated 2 minutes, free account 5, PRO ($9/month) 40. The GPU is half of an RTX Pro 6000 Blackwell (48 GB).
  - **Card: no.**
  - Programmatic calls are documented: "When you authenticate with your token, your account's GPU quota is consumed."
  - Free accounts may host 2 ZeroGPU Spaces, but CPU-only Gradio or Docker Spaces "require a paid plan".
  - Hugging Face doesn't restrict outputs. FLUX.1-schnell "can be used for personal, scientific, and commercial purposes."
  - Estimate: about 50–100 FLUX-schnell images/day. Video isn't practical.
- **Google** ([trial](https://cloud.google.com/free/docs/free-cloud-features), [Vertex](https://cloud.google.com/vertex-ai/generative-ai/pricing), [Gemini](https://ai.google.dev/gemini-api/docs/pricing), [terms](https://ai.google.dev/gemini-api/terms))
  - Cloud trial: "$300 Welcome credit to spend over 90 days". **Card: yes.** Trial accounts can't "Add GPUs to your VM instances".
  - Vertex AI: Imagen 4 Fast is $0.02 per image. Veo 3.1 Fast is $0.10–0.12/s, and standard Veo 3.1 is $0.40/s.
  - $300 covers about 15,000 Imagen Fast images or about 500 five-second Veo Fast clips, one time only.
  - Gemini API free tier (**card: no**): Imagen is "shut down", and the image models and Veo are "Not available". Gemini 3.8 Flash TTS is "Free of charge".
  - Free-tier data is used "to provide, improve, and develop Google products", but "Google won't claim ownership over that content."
- **Lightning AI** ([pricing](https://lightning.ai/pricing), [ToS](https://lightning.ai/legal/terms-and-conditions))
  - One free 4-CPU Studio that must restart "every 4 hours".
  - Credits: "5 free Lightning credits upon registration. Add a card for 25 more."
  - **Card: no** for the base tier.
  - The ToS bars anything that "involves commercial activities and/or sales without Lightning AI's prior written consent, such as… advertising".
- **Oracle Always Free** ([resources](https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm), [FAQ](https://www.oracle.com/cloud/free/))
  - Ampere A1, "equivalent to 2 OCPUs and 12 GB". No GPU.
  - **Card: yes**, for identity verification.
  - Instances idle for 7 days "may be reclaimed".
  - Enough for FFmpeg and Kokoro at 5 Shorts/day (estimate).

**Not free, or not allowed for this use**

- **Colab** ([FAQ](https://research.google.com/colaboratory/faq.html)): "Colab prioritizes users who are actively programming in a notebook", and "Runtimes will time out if you are idle".
- **NVIDIA build** ([terms](https://assets.ngc.nvidia.com/products/api-catalog/legal/NVIDIA%20API%20Trial%20Terms%20of%20Service.pdf)): no card needed, but use is "without use of the API Service or Generated Content in production".
- **GitHub Actions** ([terms](https://docs.github.com/en/site-policy/github-terms/github-terms-for-additional-products-and-features)): Actions may not be used for, "If using GitHub-hosted runners, any other activity unrelated to the production, testing, deployment, or publication of the software project associated with the repository where GitHub Actions are used."
- **AMD Developer Cloud** ([credits](https://docs.digitalocean.com/products/amd/details/credits/)): $100 of MI300X credit, valid for 30 days. A card is required, and it can't be used for "production workloads".
- **Together** ([billing](https://docs.together.ai/docs/billing-credits)): "does not currently offer free trials". Its free FLUX endpoint was removed on 2025-12-23.
- **Replicate** ([billing](https://replicate.com/docs/topics/billing)): some models are free briefly, "but after a bit you'll be asked to set up billing".
- **fal.ai** ([ToS](https://fal.ai/legal/terms-of-service)): credits must be purchased "in advance".
- **DeepInfra** ([pricing](https://deepinfra.com/pricing)): no free tier is listed.
- **Fireworks** ([pricing](https://fireworks.ai/pricing)): "$1 in free credits".
- **Pollinations** ([MIT repo](https://github.com/pollinations/pollinations), [terms](https://pollinations.ai/terms)): free Pollen comes from Quests with no card. FLUX-schnell costs 0.002 Pollen per image, and all TTS and video models are "paid-only". Terms: "verify before commercial use."
- **Intel Tiber** ([learning](https://console.cloud.intel.com/docs/tutorials/jupyter_learning.html)): JupyterLab is free but interactive only.
- **Saturn Cloud** ([plans](https://saturncloud.io/plans/)): only "Pay-as-you-go, hourly" is listed.
- **Paperspace** ([docs](https://docs.digitalocean.com/products/paperspace/pricing/)): the 2026 docs list only hourly-billed machines.

**Model licenses**

- Apache-2.0: FLUX.1-schnell, FLUX.2-klein-4B (the 9B version is non-commercial), Z-Image-Turbo, Qwen-Image, Wan2.2-TI2V-5B, and Kokoro.
- MIT: Chatterbox.
- LTX-2: a paid license is needed only at "annual revenues of at least $10,000,000" ([license](https://github.com/Lightricks/LTX-2/blob/main/LICENSE-2)).
- HunyuanVideo 1.5: the licensed territory excludes the "European Union, United Kingdom and South Korea" ([license](https://github.com/Tencent-Hunyuan/HunyuanVideo-1.5/blob/master/LICENSE)).
- Step-Audio-EditX: only the code is stated as Apache-2.0.

**Recommendation**

*No card: about 5 Shorts/day, still images only*
1. Images: Cloudflare FLUX.1-schnell or FLUX.2-klein-4B, with your own ZeroGPU Space for overflow.
2. Voice: Gemini 3.8 Flash TTS, falling back to Cloudflare Aura-1 or Kokoro on the Mac.
3. Captions: Cloudflare Whisper turbo.
4. Rendering: FFmpeg on the Mac.

The daily budget works out to 40 images (2,304 Neurons), plus 5 minutes of Whisper (233), plus 3,500 characters of Aura-1 (4,773), for about 7,300 of 10,000 Neurons. There's no reliable AI video option without a card.

*With a card: still $0 within the credits*
1. Modal is the main engine: FLUX at about $0.10/day for 50 images, Chatterbox or Kokoro, FFmpeg at about $0.01 per Short, and about 2 five-second 720p Wan2.2-TI2V-5B clips/day. Set a Workspace budget so usage can't go past the free credit.
2. An Oracle A1 instance as an always-on renderer.
3. The Google $300 trial as a one-time, 90-day Veo/Imagen boost.

**Unverified:**
- Cloudflare's FLUX-schnell output size.
- The ZeroGPU and Modal throughput figures, which are my estimates.
- Gemini's free TTS quotas, which appear only inside AI Studio.
- Whether the $300 trial covers Veo and Imagen.
- How much Pollen Quests pay.
- Oracle's commercial-use terms.
