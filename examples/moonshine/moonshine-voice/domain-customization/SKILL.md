---
name: domain-customization
description: 'Covers adapting Moonshine speech-to-text to a specific domain: supplying a runtime context or a key-terms list to bias recognition toward jargon, names and product terms, tuning the bias strength, measuring the gain on your own data, what long lists cost in accuracy and latency, and retraining or fine-tuning a model on your own data (worked air-traffic-control and VHF examples, shipping the result, pitfalls). Use when transcripts get domain words, names or acronyms wrong, or when a task mentions set_keyterms, set_context, moonshine_transcriber_set_keyterms, moonshine_transcriber_set_context, key terms, hotwords, vocabulary biasing or fine-tuning.'
---

# Domain Customization

Make Moonshine transcribe your domain's jargon, product names, contact names and acronyms correctly. There are two tools for this:

- **Runtime context** needs no training. You pass a key-terms list, or a passage of text to pull terms from, and decoding is biased toward those words. It cuts errors on the listed words by up to 40%, adds no latency, and costs very little general accuracy. It only works for words the model can already spell.
- **Retraining** uses a LoRA adapter or a full fine-tune on your own in-domain audio. Use it to teach a new accent, dialect, acoustic environment (such as VHF radio) or domain convention (such as spelled-out digits).

The two work together: retrain for conventions, then bias toward the names. For loading models and creating transcribers, see [the root skill](../SKILL.md) and [transcription](../transcription/SKILL.md).

## Which tool to use

| Symptom | Use |
| --- | --- |
| Names, products or jargon are misspelled or replaced by common words | Key terms (`keyterms` / `set_keyterms`) |
| The relevant words are already on screen (a document, ticket or thread) but not in a list | Context (`context` / `set_context`) |
| Multi-word names, or terms containing digits (`IPv6`) | Key terms. Context only proposes single words and skips words with digits |
| Wrong accent, dialect, microphone or radio channel, or wrong formatting conventions (`4652` vs `four six five two`) | Retraining |

## Runtime context

**Streaming architectures only.** The older Tiny and Base models raise an error.

### Supply a key-terms list

```python
from moonshine_voice import Transcriber, ModelArch

transcriber = Transcriber(
    model_path,
    ModelArch.TINY_STREAMING,
    options={"keyterms": "Kubernetes,Ceph,etcd"},
)

# ...or follow whatever the user is looking at, mid-stream:
transcriber.set_keyterms(["Anushka Sharma", "Jurgen Klopp"])
```

- Write each term with the capitalization and spelling you want in the output. That is exactly what gets produced.
- Terms can be phrases. At load time the list is one comma-separated string.
- `set_keyterms` can be called while audio is streaming and takes effect on the next transcription. It takes a list, not a joined string, in the languages that have lists.
- No training step is needed, so each transcriber can have its own list.

### Supply a context passage

```python
transcriber = Transcriber(
    model_path,
    ModelArch.TINY_STREAMING,
    options={"context": open("migration-plan.md").read()},
)

# ...or follow the document as the user moves through it:
transcriber.set_context(current_page_text)
```

- Terms are chosen by the model's tokenizer. A word that needs more than one subword is picked, and everyday words are left alone. For example, given a platform-migration paragraph, Tiny Streaming picks `Migration`, `Kubernetes`, `Ceph`, `etcd` and `ingress`. This works in whatever language the loaded model was built for.
- Terms are ranked by how often they appear in the passage. Ties go to the strangest-looking word. The list is capped at **200 terms** by default. Change the cap with the `context_max_terms` load option or the second argument of `set_context()`, where `0` means the default of 200.
- Keep the cap modest. Long lists cost accuracy on every other word (see [What a long list costs](#what-a-long-list-costs)). Passing a whole book is fine, because the cap limits what gets used.
- Capitalization comes from the passage.
- Only single words are proposed, and words containing digits are skipped. Pass those terms with `keyterms` alongside `context`, and both sets are used.
- Otherwise the context behaves like a key-terms list, because that is what it becomes: it can be set mid-stream, takes effect on the next transcription, and needs a streaming model.

### Names in each binding

| Binding | Load-time options | Replace on a running transcriber |
| --- | --- | --- |
| Python | `options={"keyterms": ..., "keyterm_boost": ..., "context": ..., "context_max_terms": ...}` | `set_keyterms()`, `set_context()` |
| Swift, Java | `TranscriberOption` name/value pairs | `setKeyterms()`, `setContext()` |
| JavaScript | the `options` record | `setKeyterms()`, `setContext()` |
| C | the options array of `moonshine_load_transcriber_from_files()` / `moonshine_load_transcriber_from_memory_files()` | `moonshine_transcriber_set_keyterms()`, `moonshine_transcriber_set_context()` |

The option names are the same everywhere, because options are plain name/value strings. See [options reference](../reference/options/SKILL.md) and [C API](../reference/c-api/SKILL.md).

### How it works

Each term is split into subword tokens and stored in a prefix tree. During decoding, tokens that continue one of the stored terms get a bonus of `boost * (1 + ln(depth))`. Starting a term is cheap, and finishing one is strongly rewarded. This ramp keeps greedy decoding from emitting a term one syllable at a time on unrelated audio. The work per token is bounded by the number of terms, not by the vocabulary size.

### Tuning the strength: `keyterm_boost`

The default is **2.0**. The table below shows word error rate on the listed terms and on all other words. It was measured on LibriSpeech test-clean with 100-term lists, most of whose terms are never actually spoken:

| Boost | Tiny: terms / other | Small: terms / other | Medium: terms / other |
| --- | --- | --- | --- |
| 0 (off) | 13.02% / 6.84% | 9.69% / 4.70% | 7.89% / 3.90% |
| 1 | 10.99% / 6.76% | 8.27% / 4.74% | 6.29% / 3.89% |
| 2 (default) | 10.09% / 7.11% | 7.06% / 4.85% | 5.58% / 3.93% |
| 3 | 8.92% / 7.47% | 5.97% / 4.98% | 5.07% / 4.28% |
| 4 | 8.68% / 8.41% | 5.71% / 5.47% | 4.94% / 4.57% |
| 6 | 15.80% / 17.05% | 11.74% / 12.40% | 14.05% / 11.07% |

- **1.0** removes a sixth to a fifth of the term errors at no measurable cost elsewhere.
- **2.0** (default) removes about a quarter of the term errors and costs at most about a quarter of a point elsewhere.
- **3.0** removes about a third of the term errors and costs a quarter to six tenths of a point elsewhere. Use it when the list matters more than the surrounding words.
- **Never go above 4.0.** At 6, false alarms run 30–40× higher than at the default, and both numbers get worse.
- Strength and list length multiply. For thousands of terms, stay at or below 2.0.

These are samples of 500–700 utterances, so read the trend rather than the third digit.

### What a long list costs

Tiny Streaming, full test-clean, biased toward words the corpus never contains (so the table shows only the damage):

| Key terms | Boost 1.0 | Boost 2.0 | Boost 4.0 |
| --- | --- | --- | --- |
| none | | 4.83% | |
| 1 | | 4.84% | |
| 10 | 4.83% | 4.86% | 5.21% |
| 100 | 4.91% | 5.37% | 10.22% |
| 1,000 | 5.06% | 5.88% | 13.35% |
| 10,000 | 5.17% | 6.09% | 13.66% |

At the default boost, lists in the thousands are usable. At 4.0, anything beyond about ten terms gets expensive: substitutions grow the most, and insertions grow the fastest. A strong boost only makes sense for a **short, curated** list of terms you expect to hear.

### What it costs in time

- Per-utterance latency is essentially unchanged. 100 terms add about 1 ms on Tiny (iPad A16). 10,000 terms with the boost set to 0 add 3–4 ms.
- With 10,000 live terms at boost 4.0, Small went from 97 to 120 ms and Medium from 180 to 212 ms, because false alarms force re-decoding. Treat these as upper bounds: the current default produces far fewer revisions.
- Installing a list scales with its length: about 30 ms for 10,000 terms on a MacBook Pro, paid once when you set it. Swapping lists mid-stream is cheap.
- To measure on your own device, pass `--keyterms` to [`scripts/test-mobile-latency.sh`](https://github.com/moonshine-ai/moonshine/blob/main/scripts/test-mobile-latency.sh).

### Measure the gain on your own data

Report two numbers: error rate on the terms and on all other words. A single overall WER hides the trade-off.

```bash
python scripts/make-keyterm-testset.py --output-dir /tmp/keyterm-testset
python scripts/eval-keyterm-biasing.py \
    --manifest /tmp/keyterm-testset/manifest-100.jsonl \
    --boosts 0,1,2,4
```

- `make-keyterm-testset.py` builds a test set from any ASR corpus.
- `eval-keyterm-biasing.py` reports both error rates, term recall and the false-alarm rate.
- For your own recordings, write a manifest with one `{"audio": ..., "text": ..., "keyterms": [...]}` object per line (see [`scripts/data/keyterm-eval-example.jsonl`](https://github.com/moonshine-ai/moonshine/blob/main/scripts/data/keyterm-eval-example.jsonl)).
- **Pad the list** with `--distractors-file` to the size you will actually ship. False alarms grow with the number of live terms, so a one-term test looks unrealistically clean.
- For a general corpus, `scripts/eval-librispeech.py` accepts `--keyterms-file` and `--keyterm-boost`.

### Limits

- Biasing cannot produce a spelling the tokenizer cannot make.
- Biasing cannot fix accent, dialect or recording conditions. Retrain for those.
- All the numbers above come from single-word terms in read English speech. For multi-word or unusually spelled terms, rerun the sweep on your own audio.

## Retraining (LoRA / fine-tune)

The default is a rank-8 LoRA on the decoder's self-attention q/k/v, about 0.11% of Streaming Medium. It is folded back into the base weights, so inference is unchanged: no extra layers, no extra latency, and the same `Transcriber` load path.

A decoder LoRA teaches **conventions, not vocabulary, and not a new microphone**. Rare names still need key terms.

Install the trainer. It is an opt-in extra; `[lora]` installs the same packages, and a plain `import moonshine_voice` does not load it:

```bash
pip install 'moonshine-voice[finetune]'
```

There are three equivalent entry points:

- `python -m moonshine_voice.lora`
- `moonshine-voice finetune`, an alias of the above
- the [Colab notebook](https://github.com/moonshine-ai/moonshine/blob/main/examples/python/finetune/moonshine_lora_domain_adaptation.ipynb), which uses the same helpers (`fit_adapter`, the ATCOSIM loaders, export)

`--help` lists every flag.

### Train on your own data

Prepare a JSONL manifest with one clip per line. JSON `{"utterances": [...]}` and `path<TAB>text` TSV also work:

```json
{"audio": "clips/001.wav", "text": "lufthansa four six five two"}
{"audio": "clips/002.wav", "text": "turn right heading two one zero"}
```

Audio can be any format `soundfile` reads; it is resampled to 16 kHz mono. Match the model's transcript style (cased, punctuated English) unless the domain convention is what you want to teach.

Train, then score a held-out set plus the LibriSpeech canary:

```bash
python -m moonshine_voice.lora \
    --train-manifest domain.jsonl \
    --eval-manifest domain_test.jsonl \
    --eval --canary \
    --output-dir ./lora_out
```

| Setting | Default / choices |
| --- | --- |
| Rank | 8 |
| `--sites` | `decoder` (default; best first bet for phraseology), `encoder`, `both` (cheap adapter for radio audio) |
| `--adapt full` | Unfreezes the backbone and writes no `adapter.safetensors`. The ceiling on real radio |
| `--lr` | `1e-3` decoder-only; `1e-4` when `--sites` includes the encoder; `1e-5` for `--adapt full` |
| Batch | 8 |
| Replay | 50% general-domain from `moonshine-ai/yodas-en-replay`. `--no-replay` turns it off |
| Early stopping | On in-domain loss plus held-out general-domain loss |
| `--text-mode auto` | Lowercases a corpus that is more than 90% uppercase |
| `--prepare-only` | Indexes the corpus without training |

The output is `adapter.safetensors` plus a merged `adapted/` checkpoint.

### Worked example: air traffic control (ATCOSIM)

```bash
python -m moonshine_voice.lora --dataset atcosim --output-dir ./lora_atc
```

- Needs a GPU. Medium took about 15 minutes on an RTX 5090 and peaked under 3 GB of memory, so it fits a Colab T4.
- Trains on 2 hours of speakers that are disjoint from the test set ([`moonshine-ai/atcosim-speaker-disjoint-splits`](https://huggingface.co/datasets/moonshine-ai/atcosim-speaker-disjoint-splits)), with replay.

| | ATC WER | LibriSpeech WER |
| --- | --- | --- |
| Streaming Medium, as published | 50.7% | 2.3% |
| **+ LoRA, 2 h in-domain + replay** | **26.3%** | 2.8% |
| + LoRA, no replay | 26.0% | 3.8% |

Replay costs nothing in-domain and protects general speech. ATCOSIM is free for research and commercial development but **not redistributable**. For anything you ship, get it from [TU Graz](https://www.spsc.tugraz.at/databases-and-tools/atcosim-air-traffic-control-simulation-speech-corpus.html).

### Worked example: real VHF radio (UWB-ATCC)

ATCOSIM is close-talk headset audio, not radio, and band-limiting it does not transfer to VHF. To adapt to radio, train on real radio audio:

```bash
python -m moonshine_voice.lora --dataset uwb_atcc --sites both \
    --eval --eval-dataset atco2 --canary --output-dir ./lora_vhf

# full fine-tune (not a Colab T4 job on Medium; export with --graphs all)
python -m moonshine_voice.lora --dataset uwb_atcc --adapt full \
    --eval --eval-dataset atco2 --canary --output-dir ./ft_vhf
```

| | UWB-ATCC (in-domain) | ATCO2 (held-out VHF) | LibriSpeech |
| --- | --- | --- | --- |
| Streaming Medium, as published | 107.8% | 82.2% | 2.3% |
| + ATCOSIM decoder LoRA | — | 74.5% | 3.0% |
| **+ UWB decoder LoRA** | **73.1%** | **59.6%** | **2.7%** |

- `--dataset uwb_atcc` drops session `TWR-34720N`, which the published train split shares with its test set.
- ATCO2-test-set-1h is used for evaluation only.
- [`Jzuluaga/uwb_atcc`](https://huggingface.co/datasets/Jzuluaga/uwb_atcc) is **CC BY-NC-SA 4.0** and is a research example only. For a product, use `--train-manifest` on VHF hours you have the right to use commercially.

### Ship the result

```bash
python -m moonshine_voice.lora --export \
    --model ./lora_out/adapted --output-dir ./float \
    --tokenizer-bin /path/to/published/tokenizer.bin
bash scripts/quantize-streaming-model.sh ./float
```

- A decoder-only adapter changes only `decoder_kv`. Export with `--graphs decoder_kv` and reuse the published `.ort` files for the other four graphs.
- `--sites encoder|both` or `--adapt full` also changes the encoder, so export with `--graphs all`.
- Load the output directory with a normal `Transcriber`. No `[finetune]` extra or adapter code is needed at runtime.
- Then add the domain word list with `set_keyterms` / `set_context` to recover the names the training audio barely contained.

### Pitfalls

- **Orthography mismatch.** An ALL-CAPS corpus teaches a typography that the WER normalizer discards, so the adapter's effect vanishes silently. Use `--text-mode auto`.
- **ATCOSIM is not radio.** It teaches phraseology. For radio, use `--dataset uwb_atcc` or your own manifest.
- **Licensing.** UWB-ATCC is non-commercial. ATCOSIM is not redistributable.
- **Never train on ATCO2 mixes** such as `jlvdoorn/atco2-asr`, which overlap ATCO2-test-set-1h.
- **Hold out whole speakers or sessions**, not random utterances. Otherwise you measure speaker adaptation and mistake it for domain adaptation.
- **Always score a general-domain canary** (`--canary`). In-domain WER alone cannot tell adaptation from damage.
- **Do not use the `1e-3` learning rate on the encoder or a full fine-tune.** It produces NaNs on Medium. If the loss goes non-finite, the trainer skips the step and keeps the last finite checkpoint.
- **Transformers ≥ 5.15 is pinned by the extra.** Before 5.15, `labels=` was double-shifted. The trainer computes cross-entropy itself, which is correct on either version.

## Source docs

Verbatim copies, for details not covered above:

- [models/domain-customization.md](references/models-domain-customization.md)
