# Narration voice: candidates checked 2026-09-26

Rule: the license of the model weights decides commercial use, not the code license.
Quality numbers are Elo from the Artificial Analysis speech arena (Aug-Sep 2026): the
provider-voice board for built-in voices and the controlled-voice board for cloning.
ElevenLabs Eleven v3 scores 1177 on the provider-voice board for reference.

## Usable for a monetized channel

| Model | Repo stars / last push | Weights license | Quality | Cloning | Runs on 4-core CPU |
|---|---|---|---|---|---|
| Step Audio EditX | stepfun-ai/Step-Audio-EditX, 979 / 2026-04 | Apache-2.0 (per code and roundups; HF tag unlisted) | 1094, best commercial-OK score | Yes | No, needs GPU |
| NVIDIA Magpie Multilingual 357M | HF nvidia/magpie_tts_multilingual_357m | NVIDIA Open Model License | 1063 | Zero-shot variant exists | Maybe, via magpie-tts.cpp GGUF |
| Kokoro-82M v1.0 | hexgrad/kokoro 9.0k / 2025-08; Kokoro-FastAPI 5.5k / 2026-09 | Apache-2.0 | 1061 | No, fixed voices | Yes, faster than real time |
| Maya1 | HF maya-research/maya1 | Apache-2.0 | 1045 | Voice design | No, 3B model |
| Chatterbox (Resemble AI) | resemble-ai/chatterbox 26.6k / 2026-07 | MIT | 1021; 927 on cloning board | Yes, from ~5 s | Slow but workable |
| Qwen3-TTS 0.6B / 1.7B | QwenLM/Qwen3-TTS 13.5k / 2026-03 | Apache-2.0 | Not on board | Yes (Base), presets (CustomVoice) | 0.6B possible, slow |
| VoxCPM2 | OpenBMB/VoxCPM 38.0k / 2026-09 | Apache-2.0 | Not on board | Yes | Via llama.cpp builds |
| NeuTTS Air | neuphonic/neutts 6.3k / 2026-07 | Apache-2.0 | Not on board | Yes | Yes, built for on-device |

Apps that wrap these engines:

- Voicebox (jamiepine/voicebox, 55.7k stars, MIT), built on Qwen3-TTS, so commercial use is fine.
- VoiceStudio (debpalash/VoiceStudio, 35.4k stars, AGPL-3.0, has an MCP server). Its default
  engine is OmniVoice, so it must be switched to a commercial-OK engine before use.

## Excluded: weights are non-commercial or withdrawn

- OmniVoice (k2-fsa/OmniVoice, 13.9k stars). Code is Apache-2.0, but the model card says the
  pre-trained model is CC-BY-NC because of its training data (Emilia).
- Breeze TTS 2 (1204, above ElevenLabs v3): research license.
- Fish Audio S2 Pro / fish-speech: research license.
- Voxtral TTS (Mistral): CC-BY-NC-4.0.
- Higgs Audio V3 (Boson AI): research license.
- XTTS v2 (Coqui): CPML, non-commercial.
- ChatTTS: CC-BY-NC weights. F5-TTS: CC-BY-NC weights.
- VibeVoice (Microsoft): weights withdrawn.
- IndexTTS: custom license, not confirmed for commercial use.

## Decision process

Blind bake-off on the channel's first real script, rendered on the Lightning Studio:
Kokoro (3 voices), Chatterbox, Qwen3-TTS, VoxCPM2, NeuTTS Air, plus Step Audio EditX and
Magpie if free GPU credits allow. Pick on blind listening first, CPU render time second.
Clone only voices we have consent for (the owner's own voice), never a real person's
voice without permission.
