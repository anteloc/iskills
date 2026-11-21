---
name: model-selection
description: 'Covers choosing a Moonshine model: the current and deprecated speech-to-text models with their sizes and languages, word error rate accuracy on LibriSpeech and other languages, speed and accuracy benchmarks with Whisper comparisons, quantized variants, and where the models are published on HuggingFace. Use when a task asks which model size or language model to use, how accurate or fast Moonshine is, how to trade latency for accuracy, whether to use a quantized model, or where to find the models on HuggingFace.'
---

# Choosing a Moonshine Model

Use this skill to pick a Moonshine speech-to-text model by language, size, accuracy, latency and license. It also covers how to read and reproduce the accuracy figures, what quantization does to the shipped models, and where the models are published on HuggingFace. To download a model once you have chosen one, see [model-downloads](../model-downloads/SKILL.md). For basic setup, see the [root skill](../SKILL.md).

## Quick decision guide

- **Default choice:** name only the language (`"en"`, `"de"`, `"ar"`, ...). You get the first architecture listed for that language below, which is the streaming model wherever one exists.
- **Best English accuracy:** Medium Streaming (245M parameters, 6.65% Open ASR average WER).
- **Smallest or fastest English model:** Tiny Streaming (34M, 12.00%).
- **Balance of size and accuracy:** Small Streaming (123M, 7.84%).
- **Korean or Ukrainian:** only the non-streaming Community-licensed models exist (Korean Tiny, Ukrainian Base).
- **Commercial use:** every current model is MIT except Korean and Ukrainian, which use the non-commercial Moonshine Community License.
- **Languages without Latin script** (Arabic, Japanese, Korean, Mandarin, Ukrainian): set `max_tokens_per_second` to `13.0`. See the pitfall below.

## Model format

- The library uses ONNX models converted to the memory-mappable OnnxRuntime flatbuffer encoding (`.ort`).
- The shipped models are 8-bit quantized.
- For floating-point `safetensors` checkpoints, see [HuggingFace](#huggingface).

## Current models

| Language   | Architecture     | # Parameters | WER/CER | License   |
| ---------- | ---------------- | ------------ | ------- | --------- |
| English    | Medium Streaming | 245 million  | 6.65%   | MIT       |
| English    | Small Streaming  | 123 million  | 7.84%   | MIT       |
| English    | Tiny Streaming   | 34 million   | 12.00%  | MIT       |
| Arabic     | Tiny Streaming   | 34 million   | 15.5%   | MIT       |
| German     | Small Streaming  | 123 million  | 7.5%    | MIT       |
| German     | Tiny Streaming   | 34 million   | 12.0%   | MIT       |
| Japanese   | Small Streaming  | 123 million  | 17.2%†  | MIT       |
| Japanese   | Tiny Streaming   | 34 million   | 19.7%†  | MIT       |
| Mandarin   | Tiny Streaming   | 34 million   | 16.1%†  | MIT       |
| Spanish    | Small Streaming  | 123 million  | 4.9%    | MIT       |
| Spanish    | Tiny Streaming   | 34 million   | 6.2%    | MIT       |
| Tagalog    | Tiny Streaming   | 34 million   | 14.9%   | MIT       |
| Vietnamese | Tiny Streaming   | 34 million   | 9.4%    | MIT       |
| English    | Base             | 58 million   | 10.07%  | MIT       |
| English    | Tiny             | 26 million   | 12.66%  | MIT       |
| Korean     | Tiny             | 26 million   | 6.46%   | Community |
| Ukrainian  | Base             | 58 million   | 14.55%  | Community |

† No-space character error rate (CER), not word error rate.

- The first architecture listed for each language is the one that a language code such as `"en"` downloads.
- Korean and Ukrainian default to their non-streaming Community models because they have no published streaming checkpoint yet.
- English WER here is the [Open ASR Leaderboard](https://huggingface.co/spaces/hf-audio/open_asr_leaderboard) **average across eight datasets**, measured on the floating-point reference. Quantized scores are a little higher, especially at Tiny.
- Non-English streaming scores are 400-clip macro averages on the panels listed under [Other languages](#other-languages).
- Korean and Ukrainian figures are older full-FLEURS scores. Do not compare them with the streaming rows.

## Deprecated models

These Community-licensed non-streaming models have a streaming replacement in the table above. They still load if you name the architecture explicitly, but new integrations should use the streaming model.

| Language   | Architecture | # Parameters | WER/CER | License   |
| ---------- | ------------ | ------------ | ------- | --------- |
| Arabic     | Base         | 58 million   | 5.63%   | Community |
| Japanese   | Base         | 58 million   | 13.62%  | Community |
| Japanese   | Tiny         | 26 million   | —       | Community |
| Mandarin   | Base         | 58 million   | 25.76%  | Community |
| Spanish    | Base         | 58 million   | 4.33%   | Community |
| Vietnamese | Base         | 58 million   | 8.82%   | Community |

These scores come from `scripts/eval-model-accuracy.py`, which uses a character-weighted average over the full FLEURS test set. They are **not comparable** to the streaming 400-clip figures. Japanese Tiny has never been scored.

## Pitfall: languages without Latin script

The most common hallucination is endlessly repeating the last few words. The library catches it by flagging segments with an unusually high number of tokens per second. Languages without Latin script produce many more tokens per second, so the default threshold cuts off valid output.

For Arabic, Japanese, Korean, Mandarin and Ukrainian, set the [`max_tokens_per_second` transcriber option](../reference/classes/SKILL.md) to `13.0` when you create the transcriber. English, Spanish, German, Vietnamese and Tagalog do not need this.

## Accuracy

### English (LibriSpeech `test-clean`)

These are whole-utterance results with the VAD disabled.

| Model            | Paper (float) | Reproduced float (HF Transformers) | Shipped quantized model |
| ---------------- | ------------- | ---------------------------------- | ----------------------- |
| Tiny Streaming   | 4.49%         | 4.52%                              | 4.83%                   |
| Small Streaming  | 2.49%         | 2.55%                              | 2.61%                   |
| Medium Streaming | 2.08%         | 2.16%                              | 2.17%                   |

The paper ([Moonshine v2](https://arxiv.org/abs/2602.12241)) measured accuracy with floating-point models in HF Transformers, not with the quantized `.ort` files this library ships.

### Other languages

These are the shipped quantized streaming models, scored as deployed (batch 1, VAD off) on a seeded 400-clip sample.

| Language   | Model           | Panel                                | Metric | Quantized |
| ---------- | --------------- | ------------------------------------ | ------ | --------- |
| Arabic     | Tiny Streaming  | Common Voice + FLEURS                | WER    | 15.5%     |
| German     | Small Streaming | FLEURS + MLS                         | WER    | 7.5%      |
| German     | Tiny Streaming  | FLEURS + MLS                         | WER    | 12.0%     |
| Spanish    | Small Streaming | FLEURS + MLS                         | WER    | 4.9%      |
| Spanish    | Tiny Streaming  | FLEURS + MLS                         | WER    | 6.2%      |
| Japanese   | Small Streaming | FLEURS + ReazonSpeech                | CER    | 17.2%     |
| Japanese   | Tiny Streaming  | FLEURS + ReazonSpeech                | CER    | 19.7%     |
| Mandarin   | Tiny Streaming  | FLEURS + WenetSpeech                 | CER    | 16.1%     |
| Tagalog    | Tiny Streaming  | FLEURS                               | WER    | 14.9%     |
| Vietnamese | Tiny Streaming  | FLEURS + LSVSC                       | WER    | 9.4%      |
| Korean     | Tiny            | FLEURS (full, `eval-model-accuracy`) | WER    | 6.46%     |
| Ukrainian  | Base            | FLEURS (full, `eval-model-accuracy`) | WER    | 14.55%    |

Tagalog is a snapshot taken before training finished, and it is the only language whose panel is a single read-speech set.

### Compare like with like

These are three different measurements. Do not compare across them:

1. English Open ASR averages (the model table).
2. English LibriSpeech-clean (the English table above).
3. Non-English 400-clip panels.

The deprecated Community scores are a fourth measurement and are not comparable with any of these.

### Reproduce the numbers

`scripts/eval-librispeech.py` measures corpus-level error rate with the VAD disabled. It downloads the datasets and models for you. It is a manual check and is not part of CI or the release build.

```bash
pip install moonshine-voice datasets soundfile scipy jiwer openai-whisper

python scripts/eval-librispeech.py --backend moonshine_c --model-arch tiny_streaming
python scripts/eval-librispeech.py --language ar --model-arch tiny_streaming --quick
python scripts/eval-librispeech.py --all-streaming --quick
```

| Flag | Effect |
| ---- | ------ |
| `--model-arch` | Model to evaluate, e.g. `tiny_streaming`, `small_streaming`, `medium_streaming` |
| `--language` | Non-English language code. It also sets the `max_tokens_per_second` guard automatically. |
| `--quick` | 400-clip FLEURS-only (or LibriSpeech-only) slice. It will not reproduce the two-set panels. |
| `--all-streaming` | Evaluates every published streaming model |
| `--backend hf` | Floating-point reference via Transformers. Needs `pip install "transformers>=5.13" torch`. |
| `--backend moonshine_c_streaming` | Measures the chunked real-time streaming path instead of whole-utterance transcription |
| `--enable-vad` | Turns the segmenter on (it is off by default) |
| `--limit N` | Shorter smoke test |

Keep the VAD disabled when you evaluate pre-segmented clips. On LibriSpeech or FLEURS, the default VAD adds roughly 1.5–2% WER on Tiny, mostly from insertions at segment boundaries.

## Speed and latency benchmarks

### C++ benchmark (any platform)

```bash
cd core
mkdir -p build
cd build
cmake ..
cmake --build . --config Release
./benchmark
```

The benchmark reports three figures:

- **Absolute time** taken to process the audio.
- **Percentage of audio duration.** This approximates the compute load. For example, 20% leaves 80% of the CPU for the rest of your app.
- **Average latency.** This is the time from when the library decides the user stopped talking to when the final transcript arrives. Aim for under 200ms. Streaming models do most of their work while speech is still happening, so this is where they help most.

| Argument | Purpose |
| -------- | ------- |
| `--model-path`, `--model-arch` | Use a [downloaded model](../model-downloads/SKILL.md). The default is Tiny English. |
| `--wav-path` | Different recording. The default is `test-assets/two_cities.wav`. |
| `--transcription-interval` | How often the transcript updates. The default is 0.5 seconds. Longer intervals save a little compute but update more slowly. |

Mobile latency (MacBook Pro, Pixel 10a, iPad A16) is measured with `scripts/test-mobile-latency.sh` (`--update-readme` refreshes the published cells). Published cells are medians of three runs, so expect a single run to differ a little. For example, Medium Streaming varied between 56 and 83ms on the Mac and between 383 and 432ms on the Pixel. The Linux x86 and Raspberry Pi 5 columns predate a build optimization and read pessimistically.

### Whisper comparison (Python)

Run `scripts/run-benchmarks.py`. It downloads the models itself, and `--wav_path` swaps in your own audio. Its setup:

- Moonshine models tested: Tiny, Base, Tiny Streaming, Small Streaming and Medium Streaming.
- Whisper models tested: Tiny, Base, Small and Large v3, run with faster-whisper on CPU. Each Moonshine model is compared with its namesake. Medium Streaming is compared with Whisper Large v3 because it achieves lower WER than Large v3.
- The Moonshine VAD splits the audio into phrases, and each phrase is fed to both model families.
- Latency is the time from the end of a phrase to the returned text. Whisper does all its work after the phrase ends, while streaming Moonshine models work during speech.
- Compute cost is total processing time as a percentage of the audio duration, which is the inverse of RTF.

The benchmark targets live use: phrases of 1–10 seconds that need fast responses. It does not measure batch offline throughput, where Whisper's batching optimizations apply.

## Quantization

- Shipped models use 8-bit weights, and 8-bit calculations for heavy operations such as MatMul. This is post-training quantization done with OnnxRuntime tools and [Onnx Shrink Ray](https://pypi.org/project/onnx-shrink-ray/).
- The convolutional frontend stays in at least B16 float precision for compute. Its inputs correspond to raw 16-bit audio samples.
- Weights use **per-output-channel scale factors**. This change took the LibriSpeech WER of Tiny Streaming from 7.57% to 4.83%, Small from 3.03% to 2.61%, and Medium from 2.37% to 2.17%, for 0.5% more download size. About 90% of the gain came from the frontend. Models published before 2026-07-30 used a single scale per tensor.
- Quantization now costs +0.31% WER on Tiny, +0.06% on Small and +0.01% on Medium. You gain little accuracy by running the float checkpoint in Transformers.
- The frontend ships as two files: `frontend.model.ort` (the float compute graph) and `frontend.weights.ort` (the int8 weights plus dequantization), which are dequantized once at load. A legacy single-file `frontend.ort` still loads.
- Re-quantized models go to a new dated CDN directory (currently `quantized_26_11_02`), so each library version resolves the exact weights it was tested with.
- **If you quantize your own Moonshine-style model:** use per-channel scales first. Do not fold weight normalization out of the graph unless you also use per-channel scales, because folding makes the per-channel magnitudes more extreme. Conversion options are in [scripts/quantize-streaming-model.sh](https://github.com/moonshine-ai/moonshine/blob/main/scripts/quantize-streaming-model.sh).

## HuggingFace

| Location | Contents |
| -------- | -------- |
| [huggingface.co/moonshine-ai/models](https://huggingface.co/moonshine-ai/models) | Floating-point `safetensors` checkpoints exported from training |
| [huggingface.co/moonshine-ai/moonshine-voice-assets](https://huggingface.co/moonshine-ai/moonshine-voice-assets) | A mirror of every downloadable asset: `.ort` STT and embedding models, TTS voices and grapheme-to-phoneme data |

- The organization used to be called `UsefulSensors`. Links under that name no longer resolve.
- The assets repo uses the same paths as `download.moonshine.ai`. Its `FILES.tsv` lists each file's size and checksum, which makes it the authoritative list of files a release uses.
- Each library version is tagged on the assets repo as `v<version>`, matching the GitHub release tag.
- The library still downloads from the CDN at runtime. The mirror exists for archiving and verification.
- To populate local trees for tests or offline TTS work, use [`scripts/fetch-voice-assets.sh`](https://github.com/moonshine-ai/moonshine/blob/main/scripts/fetch-voice-assets.sh).

## Source docs

Verbatim copies, for details not covered above:

- [models/index.md](references/models-index.md)
- [models/available-models.md](references/models-available-models.md)
- [models/accuracy.md](references/models-accuracy.md)
- [using/benchmarks.md](references/using-benchmarks.md)
- [models/quantization.md](references/models-quantization.md)
- [models/huggingface.md](references/models-huggingface.md)
