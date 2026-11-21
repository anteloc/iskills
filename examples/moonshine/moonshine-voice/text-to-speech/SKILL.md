---
name: text-to-speech
description: 'Covers speech synthesis with Moonshine: generating audio from text, streaming text in as it is produced, voice cloning, choosing among the voice families (ZipVoice, Phonon, Kokoro, Piper TTS) and converting graphemes to phonemes. Use when a task asks to speak text aloud, synthesize speech, pick or clone a voice, stream LLM output to audio, or work with phonemes, or when it mentions TextToSpeech, GraphemeToPhonemizer, moonshine_text_to_speech, moonshine_phonemes_to_speech, moonshine_get_tts_voices or G2P.'
---

# Text to Speech

Use Moonshine's `TextToSpeech` to speak text on the default audio device, get raw audio samples back, stream LLM output to audio as it arrives, and clone a voice from a short clip. It runs on its own, so you don't need the transcription or agent modules. You can also call the grapheme-to-phoneme (G2P) converter directly with `GraphemeToPhonemizer`. The [root skill](../SKILL.md) covers installation and general concepts.

## Quick start

1. Configure a synthesizer with chainable setters, such as `.language()` or `.voice()`.
2. Call `load()`. It blocks, because the first call may download a voice.
3. Call `say()` to play the text, or `synthesize()` to get the samples.

```python
from moonshine_voice import TextToSpeech

tts = TextToSpeech().language("fr")
tts.load()
tts.say("Bonjour, mon ami")
tts.wait()  # block until playback finishes
```

Pass a handler to `on_progress()` to show download progress during `load()`:

```python
tts = TextToSpeech().language("fr").on_progress(lambda fraction, file: print(f"{fraction:.0%}"))
tts.load()
```

### Playback queue

- `say()` returns immediately. It queues the text for synthesis and playback in the background.
- Each `say()` call queues one utterance, and utterances play in order. The next one is synthesized while the current one plays.
- `say()` also accepts a list of strings.
- `stop()` cancels the remaining utterances and stops playback.
- `is_talking()` lets you poll whether audio is still playing.
- `wait()` blocks until playback finishes.

```python
tts.say(["One.", "Two.", "Three."])
tts.stop()  # cancel remaining utterances and halt playback
```

### Get samples instead of playing them

Use `synthesize()` when the machine has no audio output or when you want to process the audio yourself:

```python
from moonshine_voice import TextToSpeech

tts = TextToSpeech().language("en-us")
tts.load()
audio_data, sample_rate = tts.synthesize("Howdy, partner")
```

## Languages and voices

```python
from moonshine_voice import list_tts_languages
list_tts_languages()

['ar-msa', 'de-de', 'en-gb', 'en-us', 'es-ar', 'es-es', 'es-mx', 'fr-fr', 'hi-in', 'it-it', 'ja-jp', 'ko-kr', 'nl-nl', 'pt-br', 'pt-pt', 'ru-ru', 'tr-tr', 'uk-ua', 'vi-vn', 'zh-hans']
```

```python
from moonshine_voice import list_tts_voices

list_tts_voices("ru")

{'present': [], 'downloadable': ['piper_ru_RU-denis-medium', 'piper_ru_RU-dmitri-medium', 'piper_ru_RU-irina-medium', 'piper_ru_RU-ruslan-medium']}
```

- `present` lists voices already on the machine.
- `downloadable` lists voices that Moonshine downloads to a cache the first time you pass them to `voice()`. After that they work offline.
- A short language code such as `"fr"` or `"ru"` also works with `language()` and `list_tts_voices()`, as the examples show.

## Choosing a voice family

Pass a voice name to `voice()`. The name's prefix tells you which engine it uses.

| Family | Prefix | Languages | Strengths | Trade-offs |
| --- | --- | --- | --- | --- |
| ZipVoice | `zipvoice_` | English accents | Most realistic speech; on-device voice cloning | Much slower to generate than Kokoro or Piper |
| Phonon | `phonon_` | English | Small (31M parameters) and fast; streaming starts after a few hundred ms; each voice is a 256 KB latent file | Random sampling by default; speed control is approximate |
| Kokoro | `kokoro_` | American and British English | 82M-parameter model with quality comparable to much larger models | — |
| Piper | `piper_` | All supported languages, 100+ voices | Lightweight | Quality varies by contributor |

### ZipVoice voices

`zipvoice_american_female`, `zipvoice_american_male`, `zipvoice_australian_male`, `zipvoice_canadian_female`, `zipvoice_canadian_male`, `zipvoice_english_female`, `zipvoice_english_male`, `zipvoice_indian_female`, `zipvoice_indian_male`, `zipvoice_irish_female`, `zipvoice_irish_male`, `zipvoice_new_zealand_female`, `zipvoice_northern_irish_female`, `zipvoice_south_african_female`, `zipvoice_south_african_male`.

Samples are at `https://cdn.jsdelivr.net/gh/moonshine-ai/moonshine@main/docs/audio/<voice>.wav`, for example [zipvoice_american_female.wav](https://cdn.jsdelivr.net/gh/moonshine-ai/moonshine@main/docs/audio/zipvoice_american_female.wav). The same URL pattern works for Kokoro voices.

### Phonon voices

Moonshine ships [phonon-31m-en](https://huggingface.co/gradium/phonon-31m-en) from [Gradium](https://gradium.ai). It is built on Kyutai's [Pocket TTS](https://github.com/kyutai-labs/pocket-tts) and is Apache 2.0, so you can use it commercially. Gradium's larger 40M models are CC BY-NC and are not included.

| American | British | Characters |
| --- | --- | --- |
| `phonon_delia`, `phonon_everly`, `phonon_hadley`, `phonon_harper`, `phonon_juniper`, `phonon_zoey` | `phonon_bryony`, `phonon_elodie-rose`, `phonon_freya`, `phonon_imogen`, `phonon_lottie`, `phonon_maeve`, `phonon_pippa` | `phonon_azgorath`, `phonon_captain_silas_blackwater`, `phonon_fairy_godmother`, `phonon_fennick_the_young_elf`, `phonon_grub_the_ogre`, `phonon_master_aldric` |
| `phonon_easton`, `phonon_micah`, `phonon_miles`, `phonon_preston`, `phonon_russell`, `phonon_trevor` | `phonon_alfie`, `phonon_edwin`, `phonon_hugh`, `phonon_spencer`, `phonon_teddy`, `phonon_toby` | `phonon_morwenna_of_the_deep`, `phonon_old_mortlake`, `phonon_sir_bramwell`, `phonon_the_snow_queen`, `phonon_the_thing_under_the_stairs`, `phonon_vyrmathrax_the_ancient` |

Behaviour to know about:

- Phonon reads text directly, so it does not use Moonshine's G2P.
- Sampling is random by default (`phonon_temperature` 0.3). Set `phonon_temperature` to `0` for the same output every time.
- Speed is a conditioning signal, not a time-stretch. The effect is approximate and saturates beyond about 0.7x–1.4x.
- **Custom or cloned Phonon voices:** you can't create these on the device, because the encoder has not been released. Gradium offers cloning (from about 10 s of clear speech) and voice design as a hosted service in [Gradium Studio](https://studio.gradium.ai/). It produces a `.safetensors` file (see the [download scripts](https://github.com/gradium-ai/xn-ptts#voices)). To load one, pass the bare voice name `phonon` and give the file in the `phonon_voice_file` option. This doc doesn't show how to pass options; see [options reference](../reference/options/SKILL.md). Gradium's terms govern these voices, not Apache 2.0.

### Kokoro voices

| American Female | American Male | British Female | British Male |
| --- | --- | --- | --- |
| `kokoro_af_alloy`, `kokoro_af_aoede`, `kokoro_af_bella`, `kokoro_af_heart`, `kokoro_af_jessica`, `kokoro_af_kore`, `kokoro_af_nicole`, `kokoro_af_nova`, `kokoro_af_river`, `kokoro_af_sarah`, `kokoro_af_sky` | `kokoro_am_adam`, `kokoro_am_echo`, `kokoro_am_eric`, `kokoro_am_fenrir`, `kokoro_am_liam`, `kokoro_am_michael`, `kokoro_am_onyx`, `kokoro_am_puck`, `kokoro_am_santa` | `kokoro_bf_alice`, `kokoro_bf_emma`, `kokoro_bf_isabella`, `kokoro_bf_lily` | `kokoro_bm_daniel`, `kokoro_bm_fable`, `kokoro_bm_george`, `kokoro_bm_lewis` |

### Piper voices

There are too many Piper voices to list here. Get them from `list_tts_voices()` (the `piper_` names), and listen to them on the [Piper voice samples page](https://rhasspy.github.io/piper-samples/).

## Streaming text in (LLM output)

When text comes from a language model, push it in as it arrives instead of waiting for the full reply:

```python
tts = TextToSpeech().language("en-us")
tts.load()

for chunk in tts.stream(llm_tokens()):
    print(f"{len(chunk.samples) / chunk.sample_rate:.2f}s: {chunk.text}")
```

Speak the chunks through the same playback queue that `say()` uses:

```python
with tts.say_stream() as speech:
    for token in llm_tokens():
        tts.push_text(token)
    tts.end_input()
    speech.wait()
```

`AgentFlow` has the same method (see [voice-agent](../voice-agent/SKILL.md)):

```python
with agent.say_stream() as push:
    for token in llm.stream(prompt):
        push(token)
```

### Streaming model

You don't open or close a stream object. Pushing text starts a reply, and ending the input finishes it.

| Call | Effect |
| --- | --- |
| `stream(iterable)` | Pushes all the text, ends the input, and yields chunks |
| `stream()` with no argument | Yields chunks as you call `push_text()` from another thread |
| `push_text(text)` | Adds text to the buffer |
| `flush()` | Synthesizes what is buffered, even mid-sentence |
| `end_input()` | Signals that no more text is coming |
| `cancel_stream()` | Abandons a reply, for example when the user interrupts |
| `say_stream()` | Context manager that plays the chunks through the `say()` queue |

Each chunk contains:

- the samples and their sample rate
- the text it covers
- an utterance id
- whether it is the last chunk of that utterance

Utterance ids start at 1 and stay comparable across flushes and refills. A chunk that covers acoustic frames rather than a known span of characters has empty text.

Other bindings have the same surface: `pushText` / `flush` / `endInput` / `cancelStream` with an `onChunk` consumer in TypeScript, Swift and Java. TypeScript also offers an async iterator, and Swift an `AsyncThrowingStream`.

### Pitfalls

- **Text is held until a sentence or phrase is complete**, because prosody depends on where a clause ends. Fed one word at a time, the synthesizer would sound like it is reading a list. Call `flush()` if you need audio sooner.
- **While a reply is active, `say()` and `synthesize()` refuse to run** until it finishes or you call `cancel_stream()`.
- **Streamed loudness is close to `say()`, not identical.** `say()` normalizes against the finished waveform, which a stream never has. Expect a difference of 1–2 dB, a little more on quiet phrases.
- First audio usually arrives well under a second after the model starts writing. Most of the gain comes from not waiting for the LLM. The first chunk can be shorter than a sentence, and later chunks get longer.
- Kokoro crossfades its sub-sentence chunks. Piper chunks match a full render exactly, sample for sample.

## Voice cloning (ZipVoice)

Cloning on the device works only with [ZipVoice](https://github.com/k2-fsa/ZipVoice).

1. Call `cloning()` before `load()`. This makes `load()` fetch ZipVoice and its clone-ASR assets.
2. Call `clone_from()` with either a `.wav` path or a `(pcm, sample_rate)` pair of mono float samples.
3. Optionally pass `transcript=` with the words spoken in the clip. If you leave it out, Moonshine transcribes the clip itself, which adds a few seconds on first use.

```python
from moonshine_voice import TextToSpeech
import importlib.resources;

clone_path = importlib.resources.files("moonshine_voice.assets").joinpath("clone-test.wav")
clone_transcript = "Ever tried. Ever failed. No matter. Try Again. Fail again. Fail better."

tts = TextToSpeech().language("en-us").cloning()
tts.load()
tts.clone_from(clone_path, transcript=clone_transcript)
tts.say("Ask not what your country can do for you, but what you can do for your country")
tts.wait()
```

Pitfalls:

- If you skip `cloning()`, `clone_from()` and `start_cloning()` raise an error.
- `voice()` and `cloning()` cancel each other: `voice()` clears cloning, and `cloning()` clears the catalog voice.
- Use a voice only with its speaker's consent.

### Clone from the microphone

```python
clone = tts.start_cloning()
clone.on_ready(lambda: print("Got it, you can stop talking."))
clone.from_microphone()
tts.clone_from(clone)
```

- `start_cloning()` returns a `VoiceClone`.
- `from_microphone()` blocks until the clip is ready, or for at most 20 s.
- `on_progress()` reports how long it has recorded and how much speech it has found.
- The voice-activity detector is built into the library, so this step downloads nothing.

### From the command line

```bash
curl -O -L 'https://github.com/moonshine-ai/moonshine/raw/refs/heads/main/language-bindings/python/src/moonshine_voice/assets/clone-test.wav'

python3 -m moonshine_voice.tts \
  --clone clone-test.wav \
  --text "I am so excited about Moonshine Voice's text to speech"
```

## Graphemes to phonemes (G2P)

Kokoro and Piper voices need phonemes (IPA) as input. Both upstream projects use the GPL-licensed espeak-ng for this, which is hard to ship on iOS or Android. Moonshine provides its own G2P module under the MIT license instead, in [core/moonshine-tts](https://github.com/moonshine-ai/moonshine/blob/main/core/moonshine-tts). Phonon doesn't use G2P.

To use G2P on its own, without speech synthesis:

```python
from moonshine_voice import GraphemeToPhonemizer

g2p = GraphemeToPhonemizer("en-us")
g2p.to_ipa("Hello world")

'həlˈoʊ wˈɝld'
```

The G2P engine is new. Intelligibility measured by character error rate (CER) is worse than the espeak-ng reference for most languages:

| Language | Moonshine CER | Reference CER |
| --- | --- | --- |
| es_mx / es_es / es_ar | 3.2% / 4.2% / 7.9% | 2.6% / 4.5% / 10.6% |
| tr_tr | 8.9% | 7.9% |
| en_us | 12.6% | 9.8% |
| fr_fr | 14.8% | 9.4% |
| nl_nl | 15.9% | 3.3% |
| ru_ru | 16.9% | 5.0% |
| de_de | 18.3% | 9.2% |
| pt_br | 19.7% | 4.9% |
| ar_msa | 20.8% | 15.3% |
| it_it | 24.2% | 11.4% |
| ko_kr | 25.0% | 18.6% |
| hi_in | 26.5% | 15.9% |
| uk_ua | 27.7% | 15.6% |
| zh_hans | 37.8% | 32.6% |
| ja_jp | 38.1% | 16.8% |
| pt_pt | 43.8% | 24.6% |
| vi_vn | 79.0% | 36.5% |

The rates were measured with [scripts/tts_g2p_intelligibility.py](https://github.com/moonshine-ai/moonshine/blob/main/scripts/tts_g2p_intelligibility.py). Model and data sources are listed in [core/moonshine-tts/data/README.md](https://github.com/moonshine-ai/moonshine/blob/main/core/moonshine-tts/data/README.md).

## C API and other bindings

This doc shows only the Python API, apart from the streaming method names above. For C functions such as `moonshine_text_to_speech`, `moonshine_phonemes_to_speech` and `moonshine_get_tts_voices`, see the [C API reference](../reference/c-api/SKILL.md). For class signatures, see the [classes reference](../reference/classes/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [using/text-to-speech.md](references/using-text-to-speech.md)
