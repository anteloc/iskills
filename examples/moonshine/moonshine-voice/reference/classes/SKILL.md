---
name: classes
description: 'Reference for the high-level Moonshine classes and their methods and events: Transcriber, MicTranscriber, Stream, TranscriptEventListener, AgentFlow, Dialog, TextToSpeech, GraphemeToPhonemizer and EmbeddingModel. Use when a task needs the exact constructor arguments, methods, callbacks or properties of one of these classes, or when computing speaker or speech embeddings with EmbeddingModel.'
---

# Moonshine Classes Reference

Use this reference for the exact constructor arguments, setters, methods, callbacks and properties of the high-level Moonshine classes: `Transcriber`, `Stream`, `TranscriptEventListener`, `MicTranscriber`, `AgentFlow`, `Dialog`, `TextToSpeech`, `GraphemeToPhonemizer` and `EmbeddingModel`. Names below are the Python ones. Where the docs give a name for another language, it is noted, for example `push_text()` → `pushText()`. Option keys passed through `options` are listed in [Options](../options/SKILL.md). The underlying C structs are in [C API](../c-api/SKILL.md).

## Shared conventions

- **Builder classes** (`MicTranscriber`, `AgentFlow`, `TextToSpeech`): the constructor takes no arguments and cannot fail. Every setter returns the object, so you can chain them, and every setter has a working default. Call setters **before** `load()`. `load()` blocks, may download models, and returns the object.
- **Low-level classes** (`Transcriber`, `EmbeddingModel`, `GraphemeToPhonemizer`): the constructor opens the model straight from a directory.
- **Cleanup**: `close()` frees native handles. A context manager also works (`with TextToSpeech() as tts:`). Objects you pass in with `use_*()` stay yours to close.

## Transcriber

The speech-to-text pipeline. You feed it audio yourself.

### `__init__()`

| Arg | Meaning |
|---|---|
| `model_path` | Path to the **folder** of model files, not a single file. Get a cached copy with `download_model()` (see [Model Downloads](../../model-downloads/SKILL.md)). |
| `model_arch` | A value from `ModelArch`. |
| `update_interval` | How often the speech-to-text model runs while audio arrives, which drives update events. A large value suppresses mid-line updates but may not cut latency by much. |
| `options` | A string-keyed map of advanced options (Python also accepts bools and numbers). See [Options → Speech to Text](../options/SKILL.md). |

### Methods

| Method | Args | Notes |
|---|---|---|
| `start()` | — | Call after creating the transcriber and before adding audio. |
| `add_audio()` | `audio_data`, `sample_rate` | A mono float32 PCM chunk. Use whatever size and rate your source produces; the library converts. |
| `stop()` | — | Ends the session. An active segment is marked complete and its events fire. |
| `update_transcription` | `flags` | Triggers a transcription manually. `MOONSHINE_FLAG_FORCE_UPDATE` skips the cache, which is otherwise returned when less than 200 ms of new audio has arrived. |
| `transcribe_without_streaming()` | `audio_data`, `sample_rate`, `flags` | For non-live audio such as files. Registered listeners still fire. The only flag is `MOONSHINE_FLAG_SPELLING_MODE`, which applies spelling fusion if a spelling model was loaded. |
| `create_stream()` | `flags` (reserved), `update_interval` (seconds) | Returns a `Stream`. Use it for several inputs (for example mic plus system audio) on one loaded model. |
| `add_listener()` | `listener` | A `TranscriptEventListener` subclass or a plain function. |
| `remove_listener()` | `listener` | The object you passed to `add_listener()`. |
| `remove_all_listeners()` | — | |
| `set_keyterms()` | `keyterms` | Biases decoding towards these terms and replaces the previous list. Terms must not contain commas. `None` or `[]` turns biasing off. Applies to the next transcription and does not rewrite emitted text. Strength comes from the `keyterm_boost` option at load time. **Streaming architectures only.** |
| `set_context()` | `context`, `max_terms` (default 200) | Extracts key terms from a passage, then behaves like `set_keyterms()`. `None` or `""` turns biasing off. **Streaming architectures only.** |

For keyterm guidance, see [Domain Customization](../../domain-customization/SKILL.md).

## Stream

Returned by `Transcriber.create_stream()`. It has its own transcript, and its line events are tagged with the stream handle. It supports `start()`, `stop()`, `add_audio()`, `update_transcription()`, `add_listener()`, `remove_listener()` and `remove_all_listeners()`, with the same semantics as on `Transcriber`. With a single input, use the `Transcriber` methods directly.

## TranscriptEventListener

Subclass this and override only the methods you need. All of them default to no-ops:

`on_line_started()`, `on_line_updated()`, `on_line_text_changed()`, `on_line_speakers_changed()`, `on_line_completed()`, `on_error()`.

For the line fields (ids, speakers, word timings), see `transcript_line_t` in [C API](../c-api/SKILL.md).

## MicTranscriber

Transcribes from the system microphone, so you never call `add_audio()`. Python uses [`sounddevice`](https://python-sounddevice.readthedocs.io/); other languages use the native audio API.

```python
mic = (
    MicTranscriber()
    .on_text(lambda text: show_in_progress(text))
    .on_line(lambda line: append_line(line.text))
)
mic.load()
mic.start()
```

### Setters (call before `load()`)

| Setter | Default / notes |
|---|---|
| `language()` | `"en"` |
| `model_arch()` | The catalog's recommended model (medium streaming for English). Most languages publish only one model. |
| `models_from()` | Loads the model from your directory instead of downloading it. |
| `use_transcriber()` | Reuses an existing `Transcriber`. You still close it. |
| `update_interval()` | `0.5` seconds |
| `options()` | A dict of [transcriber options](../options/SKILL.md), for anything the setters don't cover. |
| `spelling_model()` | Uses your own spelling model. `load()` finds the published one by itself. `None` means no spelling model. |
| `transcribe_flags()` | Flags for every streaming update, for example `MOONSHINE_FLAG_SPELLING_MODE`. Takes effect immediately even after load. |
| `device()` | Input device by index or name. Defaults to the system default. |
| `samplerate()` | `16000`. `start()` falls back to the device's own rate if the device refuses. |
| `channels()` | `1` |
| `blocksize()` | `1024` frames per callback |

### Callbacks

| Callback | Receives |
|---|---|
| `on_text()` | The in-progress text of the current line, each time it changes. |
| `on_line()` | One finished line object. |
| `on_error()` | Errors raised by the audio or transcription pipeline. |
| `on_progress()` | Download progress as a `0..1` fraction plus the file name. Attaching it also silences the default terminal progress bars. |

For line starts, ids, speakers or word timings, attach a `TranscriptEventListener` with `add_listener()`. Listeners added before `load()` are held until the stream exists.

### Lifecycle methods

| Method | Notes |
|---|---|
| `load()` | Downloads (possibly several hundred MB) and opens the model. Blocks. Safe to call twice. |
| `set_keyterms()` / `set_context()` | Same as on `Transcriber`; call after `load()`. To start with biasing already on, pass `keyterms` / `context` via `options()`. |
| `start()` | Opens the mic and starts transcribing. Raises if `load()` was not called. |
| `mute()` | Drops incoming audio but keeps the mic open, for example so the app doesn't transcribe its own TTS. |
| `stop()` | Stops listening and flushes in-flight audio so the final line is complete. |
| `close()` | Releases the mic, the stream and the model. Also works as a context manager. |

## AgentFlow

Runs generator-based voice flows. You register flows against trigger phrases. When no flow is active, each completed line is matched against the triggers semantically, using an embedding model that is downloaded on first use. When a flow is active, the line goes to the suspended generator via `.send()`. `load()` creates the mic transcriber and the synthesizer for you. For usage, see [Voice Agent](../../voice-agent/SKILL.md).

### Setters (call before `load()`)

| Setter | Default / notes |
|---|---|
| `language()` | `"en"`, used for both recognition and speech. |
| `model_arch()` | The ASR model size. |
| `voice()` | The synthesis voice. |
| `speech_options()` | A dict of [TTS options](../options/SKILL.md) passed to `TextToSpeech`. |
| `models_from()` | Model cache directory. |
| `microphone()` | `True`. Set `False` to drive the runner from text with `handle_utterance()`. |
| `speech()` | `True`. Set `False` for a silent runner: prompts are logged and flows still advance. |
| `output_device()` | Pins the playback device. |
| `trigger_threshold()` | `0.7` similarity (0–1). Raise it for false fires, lower it for missed triggers. |
| `use_embeddings()` | `True`. With `False`, matching is case-insensitive substring and no model is loaded, which suits offline tests. |
| `beeps()` | `True`. Plays "got it" / "didn't get that" cue tones. |
| `spell_feedback()` | `True`. Echoes each spelled character ("haitch", "deleting …"). |
| `barge_in()` | Off. Enable only with reliable echo cancellation. |
| `log_io()` | Off. Logs `user: ...` / `assistant: ...` lines to stderr. |
| `debug()` | Traces internal stage transitions with timings to stderr. |
| `on_progress()` | Called with `(fraction, name)` for download and load. |
| `on_heard()` | Every utterance received, including triggers and answers. |
| `on_said()` | Every prompt spoken. |
| `on_error()` | Errors from flows or audio. Without a handler, errors print to stderr. A flow that raises is torn down either way. |
| `speak_with()` | Your own speak callable. It must block until playback ends. Setting it stops `load()` from creating a synthesizer. |
| `use_text_to_speech()` | Reuses an existing `TextToSpeech`. |
| `use_mic_transcriber()` | Reuses a `MicTranscriber`, or any object with `add_listener` / `start` / `stop`. A file-fed `Transcriber` works for tests. |

The runner never closes a synthesizer or transcriber it didn't create.

### Registration and control

| Method | Args / returns |
|---|---|
| `listen_for(trigger_phrase, flow)` | `flow` takes a `Dialog` and returns a generator of prompts. The phrase is embedded once, at registration. |
| `unregister_flow(trigger_phrase)` | Returns `True` if a flow was removed. |
| `always(trigger_phrase, handler)` | Registers a phrase that is live at all times. `handler(dialog)` returns a prompt or `None` and may call `d.cancel()` / `d.restart()`. "Cancel" and "start over" are built in, but they only apply during a flow unless you register them here. |
| `otherwise(handler)` | `handler(utterance: str)` receives only lines nothing else claimed, which is the hook for dictation. Registering it silences the "didn't get that" cue. It never fires while a flow is running. |
| `load()` | Opens the embedding model, synthesizer and mic, skipping anything supplied or turned off. Blocks. Returns the runner. |
| `start_listening()` | Calls `load()` if needed and returns once the mic is live. Flows then run on the audio thread. |
| `stop_listening()` | Safe to call when already stopped. |
| `handle_utterance(utterance)` | Routes text manually. Returns `True` if a flow or global handler consumed it. |
| `cancel()` | Abandons the active flow. Returns `True` if one was cancelled. |
| `say(text)` | Speaks outside a flow and blocks until playback ends. Mic muting still applies. |
| `say_stream()` | A context manager that yields `push(text)`. Each sentence plays as it completes, and the block exits when playback ends. |
| `close()` | Releases only what the runner created. Safe to call repeatedly or without a prior load. |

**Read-only properties:** `is_active` (bool), `active_trigger` (phrase or `None`), `registered_flows` (list of phrases).

## Dialog

The argument passed to every flow. Each method returns a prompt that the flow `yield`s. `Dialog` performs no I/O, so you can unit-test a flow by driving its generator by hand.

**Attributes:** `trigger_phrase`, and `state` (a dict that starts empty).

| Method | Args (defaults) | Flow receives |
|---|---|---|
| `say()` | `text`, `barge_in` (reserved) | `None` once playback ends |
| `say_stream()` | `pieces` (any iterable of fragments), `barge_in` (reserved) | resumes after the last piece. If the source raises, what arrived is spoken and the error goes to `on_error()`. |
| `ask()` | `prompt`, `mode` (`FREE` default, `SPELLED`, `DIGITS`, `PHRASE`), `bias_terms` (currently ignored), `timeout` (8 s), `no_input_reprompt` (template with `{prompt}`, or `None`), `max_retries` (2), after which `NoInputError` is raised | the next utterance as `str` |
| `confirm()` | `prompt`, `timeout` (6 s), `max_retries` (1), after which `NoMatchError` is raised | `bool`, matched semantically |
| `choose()` | `prompt`, `options` (key → list of phrases), `timeout` (8 s), `max_retries` (2), after which `NoMatchError` is raised | the matched key as `str` |
| `cancel()` | — | raises `DialogCancelled` into the generator |
| `restart()` | — | raises `DialogRestart` into the generator |
| `replay_last_prompt()` | — | returns a `Say` prompt for the last question, or `None` |

The `mode` constants are exported from `moonshine_voice`. `SPELLED` ends on "done"/"stop"/"finish", accepts NATO-style words, and supports "delete"/"undo". For runtime ASR biasing, use `set_keyterms()` on the transcriber, not `bias_terms`.

## TextToSpeech

On-device TTS using Kokoro, Piper and ZipVoice vocoders. See [Text to Speech](../../text-to-speech/SKILL.md) for guides.

```python
tts = TextToSpeech().language("en_us").voice("kokoro_af_heart")
tts.load()
tts.say("Hello from Moonshine.")
tts.wait()
```

**Errors:** `MoonshineTtsLanguageError` (bad language tag), `MoonshineTtsVoiceError` (missing or unknown voice), `MoonshineAudioOutputError` (playback failure from `say()`; includes the output devices when they can be listed).

**Discovery functions:** `list_tts_languages()`, `list_tts_voices()`, `get_tts_voice_catalog()`. Asset layout and licences are in [core/moonshine-tts/data/README.md](https://github.com/moonshine-ai/moonshine/blob/main/core/moonshine-tts/data/README.md).

### Setters (call before `load()`)

| Setter | Notes |
|---|---|
| `language()` | A tag such as `en_us`, `de` or `fr`. Aliases like `en-us` are normalized. Defaults to `"en"`. |
| `voice()` | A catalog id whose prefix picks the vocoder: `kokoro_`, `piper_` or `zipvoice_`. Clears `cloning()`. |
| `models_from()` | Asset directory. `download=False` (the default here) requires it to be populated already; `download=True` uses it as the cache root. |
| `cloning()` | Makes this a ZipVoice cloning engine and fetches the clone assets at load. Clears `voice()`. |
| `options()` | Native [TTS options](../options/SKILL.md). |
| `output_device()` | A PortAudio index or name substring. |
| `volume()` | Playback gain for `say()`. |
| `on_progress()` | Called with a `0..1` fraction plus the file name. |
| `debug()` | Traces synthesis and playback to stderr. |

### Methods

| Method | Args / behaviour |
|---|---|
| `load()` | Fetches assets (possibly a few hundred MB). Blocks. Calling it again is a no-op. |
| `synthesize(text, options=)` | Returns `(samples, sample_rate)` as a float list. Only `speed` is honoured per call. |
| `say(text, device=, options=)` | **Non-blocking and queued.** `text` is a string or a list of strings. `device` is `None`, an index, a decimal string or a name substring; on Android it is a `Context` (required) plus an optional `AudioDeviceInfo`. Python needs `pip install numpy sounddevice`. |
| `wait()` | Blocks until everything queued has played. Android: `waitUntilDone()`. |
| `is_talking()` | `True` while anything is queued or playing. Swift/Android: `isTalking()`. |
| `stop()` | Clears the queue and halts playback. You can call `say()` afterwards. |
| `close()` | Stops playback and frees the handle. Called automatically by `with` or garbage collection. |
| `clone_from(source, transcript=)` | `source` is a `.wav` path, `(pcm, sample_rate)` or a `VoiceClone`. Without a transcript the clip is auto-transcribed. Requires `cloning()`. |
| `start_cloning(clip_duration_seconds=4.0, minimum_speech_seconds=2.0)` | Captures a voice from the mic and returns a `VoiceClone`. Requires `cloning()`. |

**Streaming text in** (for LLM replies; see the [Text to Speech](../../text-to-speech/SKILL.md) skill):

| Member | Notes |
|---|---|
| `say_stream(device=, options=)` | Plays chunks as they are synthesized. The returned handle can wait, stop, or report `finished`. Swift/Android: `sayStream()`. |
| `stream(text=None)` | Iterates chunks instead of playing them. Each chunk carries its samples, sample rate, text, utterance id and an end-of-utterance flag. With no text, drive `push_text()` from another thread. |
| `push_text(text)` | Appends a fragment. Only complete sentences are synthesized. Other languages: `pushText()`. |
| `flush()` | Queues the buffered fragment even without a terminator. |
| `end_input()` | Marks the end of input. Other languages: `endInput()`. |
| `cancel_stream()` | Drops the reply, for barge-in. Safe when idle. Other languages: `cancelStream()`. |
| `is_streaming` | While `True`, `synthesize()` and `say()` refuse. Other languages: `isStreaming`. |
| `next_chunk()` | Synthesizes the next chunk on the calling thread, or returns nothing. Other languages: `nextChunk()`. |

**Read-only properties:** `language_tag`, `asset_root` (`pathlib.Path`; raises before `load()`), `is_cloned`.

## GraphemeToPhonemizer

Produces IPA strings without synthesizing speech. It uses the TTS assets reported by `moonshine_get_g2p_dependencies()` for the language.

| Member | Notes |
|---|---|
| `__init__(language, options=, asset_root=, download=True)` | `language` is normalized as for TTS. `options` takes [G2P options](../options/SKILL.md); `g2p_root` is set for you. With `download=False`, `asset_root` is required and must already be populated. |
| `to_ipa(text, options=)` | Returns one IPA string. |
| `close()` | Frees the handle. Also called on context-manager exit and by `__del__`. |
| `language`, `asset_root` | Read-only (the normalized tag, and a `pathlib.Path`). |

## EmbeddingModel

Turns text into vectors and scores them against each other. It is a low-level type. For phrase matching in an app, use `AgentFlow`, which owns its own model. Use `EmbeddingModel` when you need the vectors themselves.

| Member | Notes |
|---|---|
| `__init__(model_path, model_arch, model_variant="q4")` | Python, Swift and Java. `model_path` is the directory holding the embedding `.ort` file and `tokenizer.bin`; Python usually gets it from `get_embedding_model()` (see [Model Downloads](../../model-downloads/SKILL.md)). `model_arch` comes from `EmbeddingModelArch` and is currently only Gemma 300M. `model_variant` is `"q4"` or `"q8"`. |
| `load(model_name=, variant="q4")` | Downloads the model if needed and returns a ready instance (JavaScript and Swift). `model_name` is an id such as `embeddinggemma-300m`; leave it empty for the default. Java instead uses `getEmbeddingDependencies()` plus the Android `AssetDownloader`, then the constructor. |
| `calculate_embedding()` | Returns the embedding vector for a sentence. Other languages: `calculateEmbedding()`. |
| `distance()` | Cosine similarity of two equal-length embeddings, in `[-1, 1]`: `1` identical, `0` orthogonal, `-1` opposite. |
| `close()` | Frees the handle. Also called on context-manager exit and garbage collection. |

To compare two sentences: open the model, call `calculate_embedding()` on each, then pass both vectors to `distance()`. The docs give no full code example and do not spell out the exact argument lists of `calculate_embedding()` or `distance()`, so check the binding before relying on keyword names. The docs describe embeddings of **text** only; they document no API for embedding audio or speaker voices.

## Source docs

Verbatim copies, for details not covered above:

- [api/classes.md](references/api-classes.md)
