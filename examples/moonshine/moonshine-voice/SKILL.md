---
name: moonshine-voice
description: 'Moonshine Voice is an on-device speech library for speech-to-text, text-to-speech and voice agents. This root skill covers the core concepts every task needs: what the library does, installing it, the quickstart for each language binding, the main usage pattern (load a model, create a Transcriber or MicTranscriber, listen for transcript events), and example apps. Use when starting any work with Moonshine Voice, when installing the package (for example pip install moonshine-voice), when looking for a minimal working example, or when unsure which Moonshine subskill fits a task.'
---

# Moonshine Voice

Moonshine Voice is an open source, on-device AI toolkit for real-time voice agents and applications. Use this skill to install the library on any platform, run a minimal working example, understand the main usage pattern, and pick the subskill for your task.

## What it is

- **Runs on-device.** It is fast and private. You need no account, credit card, API key or GPU.
- **Built for live streaming.** Latency stays low because most of the work happens while the user is still talking.
- **Covers many tasks.** High-level APIs handle transcription (speech-to-text), text-to-speech, voice cloning, speaker identification (diarization), command recognition and [conversational agents](voice-agent/SKILL.md).
- **Runs on many platforms.** The same library runs on Python, JavaScript/WebAssembly, iOS, Android, macOS, Linux, Windows and Raspberry Pi. It also runs on IoT devices, microcontrollers, DSPs and wearables (see [micro](https://github.com/moonshine-ai/moonshine/blob/main/micro/README.md)).
- **Languages:**
  - **Speech-to-text:** English, Spanish, German, Mandarin, Japanese, Korean, Vietnamese, Tagalog, Ukrainian, Arabic.
  - **Text-to-speech:** English, Spanish, Arabic, German, French, Hindi, Italian, Japanese, Korean, Dutch, Portuguese, Russian, Turkish, Ukrainian, Vietnamese, Mandarin.
- **Models:** sizes range from tiny 1MB models for constrained devices up to models that beat Whisper Large V3 in accuracy. To choose one, see [model-selection](model-selection/SKILL.md).

Live support: [Discord](https://discord.gg/27qp9zSRXF).

## Install

| Platform | Install |
|---|---|
| Python | `pip install moonshine-voice` |
| JavaScript (Node) | `npm install @moonshine-ai/moonshine-wasm` |
| JavaScript (web) | Import from `https://cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm/dist/index.js` |
| iOS / macOS | Add `https://github.com/moonshine-ai/moonshine-swift/` as a Swift package dependency in Xcode |
| Android | Add `ai.moonshine:moonshine-voice:0.1.6` to `build.gradle.kts` (Maven Central) |
| Linux | Prebuilt shared libraries for x86_64 and arm64 (see the C++ quickstart below) |
| Windows | Self-contained Visual Studio sample archive (see below) |
| Raspberry Pi | `sudo pip install --break-system-packages moonshine-voice` (USB microphone needed) |

For full project integration, CMake builds or new platforms, see [app-integration](app-integration/SKILL.md).

## The core usage pattern

The API takes care of capturing and transcribing live speech. It gives you a high-level API built around events you can act on, and it works the same way in every language:

1. **Create** a transcriber. Use `MicTranscriber` for live microphone input, or `Transcriber` for audio you supply.
2. **Register listeners** for transcript events:
   - `onText` gets the in-progress text of the current line.
   - `onLine` gets each completed line, as an object with `.text` and other fields.
3. **Load** the model with `load()`. On first use this downloads the model files.
4. **Start** listening with `start()`.

Method names follow each language's conventions. JavaScript, Swift and Java use `onText`/`onLine`, `modelArch(...)` and `lastTranscriptionLatencyMs`. Python uses snake_case names such as `add_audio` and `transcribe_without_streaming`. For the full event flow (line started, updated, text changed, completed), `Stream` and `TranscriptEventListener`, see [transcription](transcription/SKILL.md).

## Quickstart per language

### Python

```bash
pip install moonshine-voice
moonshine-voice mic --language en
```

This listens to the microphone and prints transcript updates as they arrive.

```bash
moonshine-voice agent
```

This runs a spoken wifi-setup conversation. It waits for a trigger phrase, asks questions and confirms the answers. Matching is semantic, so different natural wordings are recognized.

```bash
moonshine-voice tts --language en_us --text "Hello world"
```

This synthesizes the text and speaks it.

More: the [Getting Started Colab notebook](https://bit.ly/moonshine-colab) and a [video](https://www.youtube.com/watch?v=WH-AGvHmtoM).

### JavaScript (browser / Node)

```js
import { MicTranscriber, ModelArch } from 'https://cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm/dist/index.js';
 
const mic = new MicTranscriber()
  .modelArch(ModelArch.MediumStreaming)
  .onText((text) => showInProgress(text))
  .onLine((line) => appendLine(line.text, line.lastTranscriptionLatencyMs));
 
await mic.load();
await mic.start();
```

`showInProgress` and `appendLine` are your own UI functions.

### iOS and macOS (Swift)

The code is the same on both platforms:

```swift
import MoonshineVoice
 
let mic = MicTranscriber()
    .onText { [weak self] text in
        Task { @MainActor in self?.liveText = text }
    }
    .onLine { [weak self] line in
        Task { @MainActor in self?.lines.append(line.text) }
    }
 
try await mic.load()
try mic.start()
```

### Android (Java)

```java
import ai.moonshine.voice.MicTranscriber;
 
mic = new MicTranscriber(this)
        .onText(text -> transcriptText.setText(finishedLines + text))
        .onLine(line -> {
            finishedLines.append(line.text).append('\n');
            transcriptText.setText(finishedLines.toString());
        });
 
worker.execute(() -> {
    mic.load();
    mic.start();
});
```

Call `load()` and `start()` off the UI thread, as shown with `worker`.

### Linux (C++)

The portable C++ example downloads the library, an English speech-to-text model and a sample recording, then builds and runs a transcriber:

```bash
curl -O -L https://github.com/moonshine-ai/moonshine/releases/latest/download/cpp-examples.tar.gz
tar xzf cpp-examples.tar.gz
cd c++
./download-library.sh
g++ transcriber.cpp -Imoonshine-voice/include -Lmoonshine-voice/lib -lmoonshine -Wl,-rpath,'$ORIGIN/moonshine-voice/lib' -o transcriber
./transcriber
```

### Windows

1. Download [windows-cli-transcriber.tar.gz](https://github.com/moonshine-ai/moonshine/releases/latest/download/windows-cli-transcriber.tar.gz) and extract it.
2. Open `cli-transcriber\cli-transcriber.vcxproj` in Visual Studio.
3. Press Ctrl+Shift+B or F7 to build. The archive already contains the library and the model.

### Raspberry Pi

```bash
sudo pip install --break-system-packages moonshine-voice
moonshine-voice mic --language en
```

The pip package is optimized for the Pi.

- **Without `--break-system-packages`:** the [my-dalek README](https://github.com/moonshine-ai/moonshine/blob/main/examples/raspberry-pi/my-dalek/README.md) explains how to install into a virtual environment.
- **Screencast:** [YouTube](https://www.youtube.com/watch?v=NNcqx1wFxl0).

## Model downloads

The samples do not include model weights. Each engine downloads what it needs from `https://download.moonshine.ai/` on first use:

| Engine | Downloads |
|---|---|
| `Transcriber` | The speech model |
| `TextToSpeech` | Voice and G2P assets |
| `AgentFlow` | All of the above plus the embedding model |

- **Progress:** reported through the `onProgress` callback.
- **Cache:** files are cached under `filesDir` on Android and `Caches/MoonshineModels` on Apple platforms, so later launches work offline.
- **Voices:** switching to a different voice downloads whatever that voice needs, the same way.
- **Fully offline builds:** fetch the assets ahead of time and point the engine at them with `modelsFrom(path)`.

For cache locations, manifests and bundling, see [model-downloads](model-downloads/SKILL.md).

## Example apps

Live browser demos are at [moonshine.ai](https://moonshine.ai/). Downloadable archives are on [GitHub Releases](https://github.com/moonshine-ai/moonshine/releases/latest) and are mostly named `{platform}-{Project}.tar.gz`.

| Platform | Examples | How to run |
|---|---|---|
| JavaScript | [stt](https://github.com/moonshine-ai/moonshine/releases/latest/download/web-stt.tar.gz), [tts](https://github.com/moonshine-ai/moonshine/releases/latest/download/web-tts.tar.gz) (with voice cloning), [agent-flow](https://github.com/moonshine-ai/moonshine/releases/latest/download/web-agent-flow.tar.gz), [dictation](https://github.com/moonshine-ai/moonshine/releases/latest/download/web-dictation.tar.gz), [meeting-notes](https://github.com/moonshine-ai/moonshine/releases/latest/download/web-meeting-notes.tar.gz) | Extract, run `node serve.mjs`, open http://localhost:8080/ |
| Python ([`examples/python/`](https://github.com/moonshine-ai/moonshine/blob/main/examples/python/)) | [basic_transcription.py](https://github.com/moonshine-ai/moonshine/blob/main/examples/python/basic_transcription.py) (WAV file, offline or streaming), [mic_transcription.py](https://github.com/moonshine-ai/moonshine/blob/main/examples/python/mic_transcription.py), [text_to_speech.py](https://github.com/moonshine-ai/moonshine/blob/main/examples/python/text_to_speech.py), [agent_flow.py](https://github.com/moonshine-ai/moonshine/blob/main/examples/python/agent_flow.py), [ollama_voice.py](https://github.com/moonshine-ai/moonshine/blob/main/examples/python/ollama-voice/ollama_voice.py) (mic → local [Ollama](https://ollama.com/) LLM), [finetune](https://github.com/moonshine-ai/moonshine/blob/main/examples/python/finetune/) | `pip install moonshine-voice` first. Finetune needs `pip install 'moonshine-voice[finetune]'` (see [domain-customization](domain-customization/SKILL.md)) |
| iOS | [Transcriber](https://github.com/moonshine-ai/moonshine/releases/latest/download/ios-Transcriber.tar.gz), [TextToSpeech](https://github.com/moonshine-ai/moonshine/releases/latest/download/ios-TextToSpeech.tar.gz), [AgentFlow](https://github.com/moonshine-ai/moonshine/releases/latest/download/ios-AgentFlow.tar.gz) | Open the `.xcodeproj` (for example `Transcriber/Transcriber.xcodeproj`) |
| Android | [Transcriber](https://github.com/moonshine-ai/moonshine/releases/latest/download/android-Transcriber.tar.gz), [TextToSpeech](https://github.com/moonshine-ai/moonshine/releases/latest/download/android-TextToSpeech.tar.gz), [AgentFlow](https://github.com/moonshine-ai/moonshine/releases/latest/download/android-AgentFlow.tar.gz) | Open the extracted folder in Android Studio |
| macOS | [BasicTranscription](https://github.com/moonshine-ai/moonshine/releases/latest/download/macos-BasicTranscription.tar.gz), [MicTranscription](https://github.com/moonshine-ai/moonshine/releases/latest/download/macos-MicTranscription.tar.gz), [TextToSpeech](https://github.com/moonshine-ai/moonshine/releases/latest/download/macos-TextToSpeech.tar.gz), [AgentFlow](https://github.com/moonshine-ai/moonshine/releases/latest/download/macos-AgentFlow.tar.gz) (has a `--text` mode) | Open the Xcode project, or build with SwiftPM where noted |
| Linux | [cpp-examples.tar.gz](https://github.com/moonshine-ai/moonshine/releases/latest/download/cpp-examples.tar.gz), [transcriber.cpp](https://github.com/moonshine-ai/moonshine/blob/main/examples/c++/transcriber.cpp), [text-to-speech.cpp](https://github.com/moonshine-ai/moonshine/blob/main/examples/c++/text-to-speech.cpp) | Use `download-library.sh`, then build with g++ |
| Windows | [cli-transcriber](https://github.com/moonshine-ai/moonshine/releases/latest/download/windows-cli-transcriber.tar.gz) (WAV file or live mic) | Visual Studio, F7 |
| Raspberry Pi | [my-dalek](https://github.com/moonshine-ai/moonshine/releases/latest/download/raspberry-pi-my-dalek.tar.gz), [Pi Help Bot](https://github.com/moonshine-ai/pi-help-bot) | Install the pip package; a USB mic is recommended |

## Coding-agent skill

Upstream ships an Agent Skill you can add in one of two ways:

- Copy [`.agents/skills/moonshine-voice/`](https://github.com/moonshine-ai/moonshine/tree/main/.agents/skills/moonshine-voice) into your project's `.agents/skills/` folder.
- Run `npx skills add moonshine-ai/moonshine --skill moonshine-voice`.

## Which subskill for which task

| Task | Subskill |
|---|---|
| Transcribe files or live mic, captions, transcript events | [transcription](transcription/SKILL.md) |
| Domain words, names or acronyms come out wrong; key terms; fine-tuning | [domain-customization](domain-customization/SKILL.md) |
| Spoken dialogs, voice forms, assistants (`AgentFlow`) | [voice-agent](voice-agent/SKILL.md) |
| Speak text, pick or clone a voice, stream LLM output to audio, G2P | [text-to-speech](text-to-speech/SKILL.md) |
| Choose a model size or language, accuracy, speed, quantization | [model-selection](model-selection/SKILL.md) |
| Models fail to download, offline bundling, cache directory | [model-downloads](model-downloads/SKILL.md) |
| Embed in your own app, CMake, bindings, porting | [app-integration](app-integration/SKILL.md) |
| No or wrong output, logging, saving input audio | [debugging](debugging/SKILL.md) |
| Exact signatures, options, defaults, C API | [reference/classes](reference/classes/SKILL.md), [reference/options](reference/options/SKILL.md), [reference/c-api](reference/c-api/SKILL.md) |

## Subskills

Read the one that matches your task:

- [transcription](transcription/SKILL.md): Covers speech-to-text with Moonshine: transcribing files and live microphone audio, streaming audio into a Stream, and handling the transcript event flow (line started, updated, text changed, completed) through a TranscriptEventListener. Use when a task asks to transcribe audio, add live captions, build real-time speech recognition, or work with Transcriber, MicTranscriber, Stream, TranscriptEventListener, transcript lines and words, add_audio, start and stop, or transcribe_without_streaming.
- [domain-customization](domain-customization/SKILL.md): Covers adapting Moonshine speech-to-text to a specific domain: supplying a runtime context or a key-terms list to bias recognition toward jargon, names and product terms, tuning the bias strength, measuring the gain on your own data, what long lists cost in accuracy and latency, and retraining or fine-tuning a model on your own data (worked air-traffic-control and VHF examples, shipping the result, pitfalls). Use when transcripts get domain words, names or acronyms wrong, or when a task mentions set_keyterms, set_context, moonshine_transcriber_set_keyterms, moonshine_transcriber_set_context, key terms, hotwords, vocabulary biasing or fine-tuning.
- [voice-agent](voice-agent/SKILL.md): Covers building conversational voice agents with Moonshine: simple and multi-step flows, asking questions, confirmations, spelled input, error handling, speaking a reply while it is being written, and agent setup that ties transcription to text-to-speech. Use when a task asks for a voice assistant, voice-driven form, phone-style dialog, or spoken question and answer, or mentions AgentFlow, Dialog, confirmations, spelled input or streaming a reply to speech.
- [text-to-speech](text-to-speech/SKILL.md): Covers speech synthesis with Moonshine: generating audio from text, streaming text in as it is produced, voice cloning, choosing among the voice families (ZipVoice, Phonon, Kokoro, Piper TTS) and converting graphemes to phonemes. Use when a task asks to speak text aloud, synthesize speech, pick or clone a voice, stream LLM output to audio, or work with phonemes, or when it mentions TextToSpeech, GraphemeToPhonemizer, moonshine_text_to_speech, moonshine_phonemes_to_speech, moonshine_get_tts_voices or G2P.
- [model-selection](model-selection/SKILL.md): Covers choosing a Moonshine model: the current and deprecated speech-to-text models with their sizes and languages, word error rate accuracy on LibriSpeech and other languages, speed and accuracy benchmarks with Whisper comparisons, quantized variants, and where the models are published on HuggingFace. Use when a task asks which model size or language model to use, how accurate or fast Moonshine is, how to trade latency for accuracy, whether to use a quantized model, or where to find the models on HuggingFace.
- [model-downloads](model-downloads/SKILL.md): Covers getting model files onto a device: automatic downloading and where files go (cache location), the speech-to-text, embedding and text-to-speech model downloads, and the download manifests that list the files each feature needs. Use when models fail to load or download, when bundling models for offline use or app distribution, when changing the model cache directory, or when a task mentions moonshine_get_stt_dependencies, moonshine_get_tts_dependencies, moonshine_get_embedding_dependencies, moonshine_get_stt_catalog or model paths.
- [app-integration](app-integration/SKILL.md): Covers adding Moonshine Voice to your own app and building it from source: linking the library into iOS, Android, desktop and other projects, building with CMake, generating the language bindings and porting to new platforms. Use when a task asks to embed Moonshine in an existing project, set up a build, compile the C++ core, use CMake, create or fix language bindings, or port Moonshine to a new platform.
- [debugging](debugging/SKILL.md): Covers troubleshooting Moonshine Voice: enabling console logs, saving the input audio the library receives, and logging API calls to reproduce problems. Use when transcription or synthesis behaves unexpectedly, produces no output or wrong output, when audio input looks wrong, or when a task asks how to turn on logging, save input audio or trace API calls.
- [reference](reference/SKILL.md): API reference for Moonshine Voice: the high-level classes, every option accepted by the speech-to-text, text-to-speech, grapheme-to-phoneme and embedding components, and the full C API. Use when a task needs an exact signature, class member, option name, default value, constant, error code or C function rather than a how-to guide.

## Source docs

Verbatim copies, for details not covered above:

- [index.md](references/index.md)
- [quickstart.md](references/quickstart.md)
- [using/index.md](references/using-index.md)
- [examples.md](references/examples.md)
