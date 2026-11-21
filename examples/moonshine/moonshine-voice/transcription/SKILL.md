---
name: transcription
description: 'Covers speech-to-text with Moonshine: transcribing files and live microphone audio, streaming audio into a Stream, and handling the transcript event flow (line started, updated, text changed, completed) through a TranscriptEventListener. Use when a task asks to transcribe audio, add live captions, build real-time speech recognition, or work with Transcriber, MicTranscriber, Stream, TranscriptEventListener, transcript lines and words, add_audio, start and stop, or transcribe_without_streaming.'
---

# Transcription

Turn speech into text with Moonshine. You can transcribe a live microphone with `MicTranscriber`, or feed audio yourself (files, custom capture, several streams) into a `Transcriber`. Results come back as transcript events on a `TranscriptEventListener`. Installing the library and the basic quickstart are covered in the [root skill](../SKILL.md).

## Choose an entry point

| Need | Use |
|---|---|
| Live captions from the default microphone | `MicTranscriber` with `on_text` / `on_line` |
| Line ids, speaker spans, word timings, line-start moment (live mic) | `MicTranscriber.add_listener()` |
| Feed your own audio (WAV, custom pipeline, multiple streams) | `Transcriber` + `add_audio()` |
| Analyse a finished recording in one call | `Transcriber.transcribe_without_streaming()` |

For per-platform starting points, see the examples in the [root skill](../SKILL.md). To add the library to an app, see [app-integration](../app-integration/SKILL.md).

## Live microphone transcription

1. Create a `MicTranscriber` and chain on the callbacks you need.
2. Call `load()` to fetch and open the model.
3. Call `start()` to begin listening.
4. Call `stop()` when done. Call `close()`, or use a context manager, to release the microphone and model.

```python
from moonshine_voice import MicTranscriber

mic = (
    MicTranscriber()
    .language("en")
    .on_text(lambda text: print(text, end="\r", flush=True))
    .on_line(lambda line: print(line.text))
)
mic.load()
mic.start()
```

- `on_text()` runs whenever the in-progress line changes. Use it to refresh live captions.
- `on_line()` runs once for each finished segment and receives the final line. The underlying fields are listed under `transcript_line_t` in the [C API reference](../reference/c-api/SKILL.md).

### Model loading and progress

The first time `load()` runs, it blocks while it downloads the recommended model for the language into a local cache. Later launches reuse that cache and work offline. To drive your own progress bar, pass a handler to `on_progress()`. Attaching one also turns off the default terminal progress bars:

```python
mic = (
    MicTranscriber()
    .language("en")
    .on_progress(lambda fraction, file: print(f"{fraction:.0%} {file}"))
    .on_text(lambda text: show_in_progress(text))
    .on_line(lambda line: append_line(line.text))
)
mic.load()
mic.start()
```

### MicTranscriber builder options

| Method | Purpose |
|---|---|
| `.language("en")` | Language to transcribe. Selects the catalog's recommended model (medium streaming for English). Most languages publish only one model. |
| `.model_arch(...)` | Override the default and pick a specific model size. |
| `.models_from(...)` | Use a directory of models you already have (see [model-downloads](../model-downloads/SKILL.md)). |
| `.update_interval(...)` | How often the transcript is analysed (default 500 ms). See [Update interval](#update-interval). |
| `.on_progress(fn)` | `fn(fraction, file)` for model download progress. |
| `.on_text(fn)` | `fn(text)` each time the in-progress line changes. |
| `.on_line(fn)` | `fn(line)` once per completed line. |

The model sizes you can choose from are covered in [model-selection](../model-selection/SKILL.md).

## Feeding your own audio with Transcriber

### 1. Create the transcriber

First [download the model files](../model-downloads/SKILL.md) and put them where the app can find them. Then pass that path in:

```python
transcriber = Transcriber(model_path=model_path, model_arch=model_arch)
```

If the model isn't found, or anything else goes wrong, the constructor throws an exception that describes the problem. The core library also writes logs to `stderr` or your system's equivalent. For more troubleshooting, see [debugging](../debugging/SKILL.md).

### 2. Attach a listener

Subclass `TranscriptEventListener`, override only the events you need, and register it:

```python
class TestListener(TranscriptEventListener):
    def on_line_started(self, event):
        print(f"Line started: {event.line.text}")

    def on_line_text_changed(self, event):
        print(f"Line text changed: {event.line.text}")

    def on_line_completed(self, event):
        print(f"Line completed: {event.line.text}")

listener = TestListener()
transcriber.add_listener(listener)
```

Each handler gets an `event`, and the line is on `event.line` (for example `event.line.text`).

### 3. Start, add audio, stop

This example streams a WAV file in chunks to simulate live input:

```python
    audio_data, sample_rate = load_wav_file(wav_path)

    transcriber.start()

    # Loop through the audio data in chunks to simulate live streaming
    # from a microphone or other source.
    chunk_duration = 0.1
    chunk_size = int(chunk_duration * sample_rate)
    for i in range(0, len(audio_data), chunk_size):
        chunk = audio_data[i: i + chunk_size]
        transcriber.add_audio(chunk, sample_rate)

    transcriber.stop()
```

- `load_wav_file()` is a convenience function in the Moonshine library. It returns mono audio data and its sample rate.
- `start()` turns on processing. Call it before `add_audio()`.
- `add_audio(chunk, sample_rate)` accepts chunks of **any length and any sample rate**. The audio must be **mono**. Otherwise, pass it in as it is.
- Listener callbacks fire while audio is being added.

In a real app, call `add_audio()` from the audio handler that receives data from your source.

The docs only show the import for `MicTranscriber` (`from moonshine_voice import MicTranscriber`). They don't show where `Transcriber`, `TranscriptEventListener` or `load_wav_file` are imported from. Check the [classes reference](../reference/classes/SKILL.md).

### Non-streaming transcription

If you already have a complete array of past audio, such as a file or recording, call `transcribe_without_streaming()` on the transcriber instead of the start/add_audio/stop loop. This doc doesn't give its exact signature or return value. See the [classes reference](../reference/classes/SKILL.md).

## Sessions and the transcript

- `start()` begins a session and `stop()` ends it. This applies to a transcriber or a stream.
- Each session has one transcript document. **It is reset on every `start()`**, so copy any data you need before you restart.
- You usually don't need to read the transcript structure yourself, because events tell you when something changes.
- To check the current state, call `update_transcription()`. It triggers an update by hand and returns a transcript object with everything about the current session.

## Update interval

- By default, the transcriber analyses speech every 500 ms of input.
- To change it, pass the `update_interval` argument to the `Transcriber` constructor, or call `MicTranscriber.update_interval()`.
- With streaming models, most of the work happens as audio is added, and it runs automatically at the end of a phrase. Changing the interval usually doesn't change workload or latency much.
- The interval is a minimum, not a fixed schedule. Each pass must cover at least as much audio as the previous pass took to compute, up to ten intervals' worth. A slow machine therefore transcribes in bigger batches instead of falling further behind. When there is spare processing time, the interval works as set.
- Setting a very large `update_interval` effectively turns off the `LineUpdated` / `LineTextChanged` events.

## Transcript event flow

Events are the main way the library talks to your app. A `TranscriptEventListener` can receive five event types:

| Event | Listener method (Python) | When it fires |
|---|---|---|
| `LineStarted` | `on_line_started` | A new speech segment is detected. It may have no text yet, and its text is likely to change. |
| `LineUpdated` | not shown in docs | Any line info changes: duration, audio data or text. |
| `LineTextChanged` | `on_line_text_changed` | Only the line's text changed. This is a subset of `LineUpdated`; use it to refresh the text shown to users. |
| `LineSpeakersChanged` | not shown in docs | Only when the opt-in `identify_speakers` option is on. The line's speaker spans changed. It can fire for lines that are already completed. |
| `LineCompleted` | `on_line_completed` | The speaker paused and the segment ended. The line now holds its final text and duration. |

The docs only show the Python method names for the three events in the listener example above.

### Guarantees

- `LineStarted` fires exactly once per segment.
- `LineCompleted` fires exactly once per segment, after `LineStarted`.
- `LineUpdated` and `LineTextChanged` only fire between that segment's `LineStarted` and `LineCompleted`.
- Update events are **not guaranteed** to fire at all.
- Each stream has only one active line at a time.
- After `LineCompleted`, the line's text, timing and audio never change again. The one exception is speaker spans when `identify_speakers` is on. Diarization re-clusters a sliding window of recent speech, so assignments can be revised (signaled by `LineSpeakersChanged`). Audio older than `diarization_cluster_window_sec` is frozen.
- `stop()` on a transcriber or stream fires `LineCompleted` for any active line.
- Each line has a 64-bit `lineId` that is unique enough to avoid collisions. It stays the same from `LineStarted` onwards, so you can use it as a key to update UI rows.

## Pitfalls

- **Audio must be mono.** Sample rate and chunk size don't matter, but channel count does.
- **Call `start()` before `add_audio()`.** Otherwise processing isn't active.
- **Copy transcript data before `start()` again.** A new session clears the previous transcript.
- **Don't count on update events.** Do any final processing in `LineCompleted` / `on_line`, not in `LineTextChanged`.
- **The first `load()` needs the network.** It blocks while the model downloads. Show progress with `on_progress()`, or point `models_from()` at bundled models.
- **Release resources.** Call `close()` on `MicTranscriber`, or use a context manager.
- **Customizing vocabulary or domain** is covered in [domain-customization](../domain-customization/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [using/transcription.md](references/using-transcription.md)
