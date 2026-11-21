---
name: model-downloads
description: 'Covers getting model files onto a device: automatic downloading and where files go (cache location), the speech-to-text, embedding and text-to-speech model downloads, and the download manifests that list the files each feature needs. Use when models fail to load or download, when bundling models for offline use or app distribution, when changing the model cache directory, or when a task mentions moonshine_get_stt_dependencies, moonshine_get_tts_dependencies, moonshine_get_embedding_dependencies, moonshine_get_stt_catalog or model paths.'
---

# Downloading Models

Use this skill to get Moonshine model files onto a device. It covers automatic download on first `load()`, the opt-in `AssetDownloader`, the `moonshine-voice download` CLI, where files are stored, and the download manifests that list the files each feature needs. Installing the library and the basic load/listen pattern are in the [root skill](../SKILL.md).

## Pick an approach

| Situation | Do this |
| --- | --- |
| Normal app using `MicTranscriber`, `TextToSpeech` or `AgentFlow` | Do nothing. `load()` downloads what is missing on first use. |
| Warm a cache before a device goes offline (Python, Linux, Windows, Raspberry Pi) | Run `moonshine-voice download ...` (see [CLI](#cli-downloads)). |
| C++ app that builds a `Transcriber` from a path | Run `moonshine-voice download`, then pass that directory to the engine. |
| You want to pick the directory yourself (iOS, macOS, Android) | Call `AssetDownloader.ensureModelPresent`. |
| Android downloads that must survive process death, wait for Wi-Fi and retry | Use `MoonshineDownloadWorker` (WorkManager). |
| Models shipped inside the app | Load them with the usual `from files` / `from assets` / `from memory` paths. These never touch the network. |

The downloader is **opt-in** for the low-level path. It gets the file list from the native catalog, so you never hardcode filenames. It also:
- writes each file atomically through a `.part` file
- resumes interrupted transfers with HTTP `Range`
- checks free space before large writes
- reports progress per file

## Automatic download on `load()`

### Python

Files go into the user cache. Set `MOONSHINE_VOICE_CACHE` to use a different location. If you attach `on_progress()`, the default terminal progress bars are turned off.

```python
from moonshine_voice import MicTranscriber

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

Use `models_from(path)` when the files are already in a directory on disk, for example after running the CLI.

### JavaScript (browser)

`MicTranscriber.load()`, `TextToSpeech.load()` and `AgentFlow.load()` download through an internal `AssetDownloader` into the Cache Storage bucket `moonshine-models-v1`. Later visits reuse that cache and work offline.

```js
import { MicTranscriber } from 'https://cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm/dist/index.js';

const mic = new MicTranscriber()
  .onProgress((fraction, file) => {
    console.log(`${(fraction * 100).toFixed(0)}% ${file}`);
  })
  .onText((text) => showInProgress(text))
  .onLine((line) => appendLine(line.text));

await mic.load();
await mic.start();
```

- During development, add `?fresh=1` to a demo URL. This clears the model cache and forces a new download.
- To host the assets yourself instead of using the CDN, pass `modelsFrom` or a custom `baseUrl`.

## Explicit download: iOS and macOS (Swift)

`ensureModelPresent` downloads whatever is missing under a directory you choose. It returns that directory, which you then pass to `Transcriber`, `MicTranscriber` or `TextToSpeech`. The call is `async`, so run it off the main actor.

```swift
import MoonshineVoice

let modelDir = URL.cachesDirectory.appending(path: "moonshine/tiny-en")

// Speech-to-text: download the default English model (add includeSpelling: true for the
// alphanumeric spelling model, or pass modelArch: to pick a specific architecture).
let downloader = AssetDownloader(allowsCellularAccess: false)  // Wi-Fi only
try await downloader.ensureModelPresent(root: modelDir, spec: .stt(language: "en")) { progress in
    print("\(progress.relativePath): \(progress.bytesDownloaded)/\(progress.bytesTotal)")
}
let transcriber = try Transcriber(modelPath: modelDir.path, modelArch: .tiny)

// Text embeddings (the embeddinggemma-300m model is large — a few hundred MB even at q4):
try await downloader.ensureModelPresent(root: embeddingDir, spec: .embedding(variant: "q4"))

// Text to speech (files land under the directory you pass as g2p_root):
try await downloader.ensureModelPresent(root: ttsRoot, spec: .tts(language: "en_us", voice: "kokoro_af_heart"))
```

- `isModelPresent(root:spec:)` is a cheap synchronous check. Use it to skip the download UI when the files are already on disk.
- Download failures throw `AssetDownloadError`, for example for an HTTP status, insufficient space or cancellation. This lets you tell "couldn't fetch" apart from a later load failure.
- HTTPS downloads need no `Info.plist` entries or extra permissions.

## Explicit download: Android (Java)

The Android `AssetDownloader` mirrors the Swift API, but it does blocking network I/O. Run it off the main thread.

```java
File modelDir = new File(context.getFilesDir(), "moonshine/tiny-en");

// Direct (call from a background thread / coroutine):
File root = new AssetDownloader().ensureModelPresent(
        modelDir, ModelSpec.stt("en"),
        (path, index, total, done, size) -> Log.i("dl", path + " " + done + "/" + size));
Transcriber transcriber = new Transcriber();
transcriber.loadFromFiles(root.getAbsolutePath(), JNI.MOONSHINE_MODEL_ARCH_TINY);

// Or via WorkManager, downloading only over unmetered (e.g. Wi-Fi) connections:
OneTimeWorkRequest request =
        MoonshineDownloadWorker.buildRequest(modelDir, ModelSpec.stt("en"), /*requireUnmetered=*/ true);
WorkManager.getInstance(context).enqueue(request);
```

- `ModelSpec` factories: `stt(language)`, `tts(language, voice)`, `embedding(modelName, variant)`, `g2p(language)`. They match the Swift specs.
- The library manifest declares the `INTERNET` and `ACCESS_NETWORK_STATE` permissions. These merge into your app automatically.
- To track worker progress, read `WorkInfo.getProgress()` using the worker's `PROGRESS_*` data keys.
- The downloader brings in OkHttp and WorkManager as dependencies. Apps that bundle their models still ship these libraries but never use the network path.

## CLI downloads

The Python package installs the `moonshine-voice download` command. Use it to warm the cache, or to stage files for C++ apps, Linux, Windows and Raspberry Pi. For C++, you can also use `./download-library.sh` in [`examples/c++`](https://github.com/moonshine-ai/moonshine/blob/main/examples/c++/README.md), which also fetches a sample English model. Windows C++ apps can instead use the models bundled in the release archive.

### Speech to text

```bash
moonshine-voice download --stt --language en
```

- `--language` takes either the two-letter code or the English name.
- To see the supported languages, pass an invalid one, for example `--language foo`. The command errors and lists them. The list is also in [model-selection](../model-selection/SKILL.md).
- `--model-arch` picks a specific architecture, using the numbers in [moonshine-c-api.h](https://github.com/moonshine-ai/moonshine/blob/main/core/moonshine-c-api.h). If you leave it out, you get the highest-quality model for the language. For English that is Medium Streaming, arch `5`.
- The command also fetches the alphanumeric spelling model (`spelling_cnn.ort`, `spelling_cnn_meta.json`) when one is published for the language.

The last lines of the output tell you what to pass to the loader:

```text
Model arch: 5
Downloaded model path: /Users/petewarden/Library/Caches/moonshine_voice/download.moonshine.ai/model/medium-streaming-en/quantized_26_11_02
```

### Embeddings

`AgentFlow` downloads the embedding model on first use. You only need this command to warm the cache ahead of time. To use the vectors yourself, pass the downloaded directory to [`EmbeddingModel`](../reference/classes/SKILL.md).

```bash
moonshine-voice download --embedding
```

This downloads `model_q4.ort` (about 189 MB) and `tokenizer.bin` into `.../download.moonshine.ai/model/embeddinggemma-300m`.

### Text to speech

```bash
moonshine-voice download --tts --root /tmp/tts-files/
```

The output ends with `TTS assets root (use as g2p_root): /private/tmp/tts-files`. You can request a specific language, and optionally a voice. The docs only show the `--root` flag, so check `moonshine-voice download --help` for the exact language and voice flag names.

## Where files go

| Path | Location |
| --- | --- |
| Python and CLI | User cache directory, e.g. `~/Library/Caches/moonshine_voice` on macOS, with files under `download.moonshine.ai/model/<name>/...`. Override with `MOONSHINE_VOICE_CACHE`. |
| Browser | Cache Storage bucket `moonshine-models-v1`, not a filesystem path. |
| `AssetDownloader` / `ensureModelPresent` | The directory you pass. Choose one that fits the platform's storage policy, e.g. `URL.cachesDirectory` on Apple platforms, or `context.getFilesDir()` / `context.getCacheDir()` on Android. |

Files are laid out the way the loaders expect them:
- STT and embedding files keep their bare filenames, e.g. `encoder.ort`, `tokenizer.bin`.
- TTS and G2P assets keep their relative paths under the root, e.g. `en_us/dict.tsv`. The engine finds them given only the root, which you pass as `g2p_root`.

### Moving TTS files

- **Files in other locations:** before `load()`, call `TextToSpeech.options()` with one entry per file. The key is the usual relative path and the value is the file's actual path.
- **App installed at an unknown location:** pass the `tts_root` option at runtime to point at the TTS data root. The aliases `g2p_root`, `path_root` and `model_root` work too. An empty root means the current working directory.

## Download manifests (C API)

The native catalog that the downloaders use is exposed in the C API, so you can list the files a feature needs, for example to bundle them with an app. Signatures are in [reference/c-api](../reference/c-api/SKILL.md), and the full option catalog is in [reference/options](../reference/options/SKILL.md).

| Function | Options that change the file list |
| --- | --- |
| `moonshine_get_stt_dependencies()` | You can pass the same options you use to load the model. Only these change the list: `model_arch` (decimal string of a `MOONSHINE_MODEL_ARCH_*` constant; if omitted, the language default is used), `word_timestamps` (adds the attention decoder), `include_spelling` / `spelling` (adds the spelling-CNN group when one is published for the language), and `spelling_model_path` (a non-empty value has the same effect as including the spelling group). |
| `moonshine_get_embedding_dependencies()` | `variant` (alias `model_variant`): which quantized/float file to include. `moonshine_create_embedding_model()` accepts `q4` (the default) and `q8`. `fp32`, `fp16` and `q4f16` are no longer supported. |
| `moonshine_get_tts_dependencies()`, `moonshine_get_tts_voices()` | TTS keys such as `voice` (e.g. `kokoro_af_heart`; the `kokoro_` / `piper_` / `zipvoice_` / `phonon_` prefix selects the vocoder), `lang` / `language`, and the root keys `g2p_root` / `tts_root`. |
| `moonshine_get_g2p_dependencies()` | G2P keys such as `g2p_root` and the language flags. TTS-only keys like `voice` are ignored. |

`moonshine_get_stt_catalog` is not described in these source docs. Check [reference/c-api](../reference/c-api/SKILL.md) or `moonshine-c-api.h` for its signature.

## Troubleshooting

- **Model not found after a CLI download:** pass the exact `Downloaded model path` and `Model arch` from the CLI output. A mismatched architecture will not load.
- **TTS can't find files after you moved them:** set `g2p_root` / `tts_root` to the new root, or map each relative path through `options()` before `load()`.
- **Need to tell a download failure from a load failure (Swift):** catch `AssetDownloadError` separately.
- **Stale or corrupt browser cache:** use `?fresh=1` during development.
- **Downloads run on cellular:** create the Swift downloader with `AssetDownloader(allowsCellularAccess: false)`. On Android, build the worker with `requireUnmetered = true`.
- **Testing:**
  - `MOONSHINE_DOWNLOAD_TESTS=1 swift test --filter AssetDownloaderNetworkTests` runs the opt-in Swift network tests.
  - On Android, run `./gradlew connectedAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=ai.moonshine.voice.AssetDownloaderTest -Pandroid.testInstrumentationRunnerArguments.moonshineDownloadTests=1`. It needs a connected device or emulator.
  - `scripts/test-model-downloads.sh` runs the catalog samples and then both of those network suites. It skips a platform when its toolchain or a device isn't available.
  - The offline, mocked `AssetDownloaderTests` run with the default `swift test`.

## Source docs

Verbatim copies, for details not covered above:

- [using/downloading-models.md](references/using-downloading-models.md)
- [api/options.md](references/api-options.md)
