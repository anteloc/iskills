---
name: app-integration
description: 'Covers adding Moonshine Voice to your own app and building it from source: linking the library into iOS, Android, desktop and other projects, building with CMake, generating the language bindings and porting to new platforms. Use when a task asks to embed Moonshine in an existing project, set up a build, compile the C++ core, use CMake, create or fix language bindings, or port Moonshine to a new platform.'
---

# Adding Moonshine to Your App and Building from Source

Use this skill to add Moonshine Voice to an existing project on each supported platform, to build the C++ core yourself with CMake, to work on the language bindings, or to port the library to a new platform or language. For installation basics and quickstarts, see the [root skill](../SKILL.md).

## Add the library with a package manager

| Platform | Distribution | Import / include |
| --- | --- | --- |
| JavaScript (Node, bundler, browser) | npm: [`@moonshine-ai/moonshine-wasm`](https://www.npmjs.com/package/@moonshine-ai/moonshine-wasm) | `import { MicTranscriber, ModelArch } from '@moonshine-ai/moonshine-wasm';` |
| Python (desktop, Raspberry Pi) | PyPI: [`moonshine-voice`](https://pypi.org/project/moonshine-voice/) | `import moonshine_voice` |
| iOS / macOS | Swift Package Manager: [`moonshine-swift`](https://github.com/moonshine-ai/moonshine-swift/) | `import MoonshineVoice` |
| Android | Maven: [`ai.moonshine:moonshine-voice`](https://mvnrepository.com/artifact/ai.moonshine/moonshine-voice) | Gradle dependency |
| Linux (x86_64, arm64) | Prebuilt `.so` on [GitHub Releases](https://github.com/moonshine-ai/moonshine/releases/latest) | `#include "moonshine-cpp.h"` |
| Windows | Raw library and headers download | `#include "moonshine-cpp.h"` |

### JavaScript

```bash
npm install @moonshine-ai/moonshine-wasm
```

```js
import { MicTranscriber, ModelArch } from '@moonshine-ai/moonshine-wasm';
```

In the browser you can skip the install and import from a CDN:

```js
import { MicTranscriber, ModelArch } from 'https://cdn.jsdelivr.net/npm/@moonshine-ai/moonshine-wasm/dist/index.js';
```

For a full working tree, see the web examples in the [root skill](../SKILL.md).

### Python

```bash
pip install moonshine-voice
```

The package also installs a `moonshine-voice` CLI (alias `moonshine`):

| Command | Description |
| --- | --- |
| `moonshine-voice mic` | Transcribe live microphone input to the terminal. |
| `moonshine-voice transcribe` | Transcribe a WAV file (optionally with speaker IDs / word timestamps). |
| `moonshine-voice tts` | Synthesize speech from text to a WAV file or audio device. |
| `moonshine-voice agent` | Run a spoken agent flow (wifi setup) from the microphone. |
| `moonshine-voice download` | Download STT, TTS, G2P, or embedding model assets. |
| `moonshine-voice g2p` | Convert text to phonemes (IPA). |

Run `moonshine-voice <command> --help` to see each command's options. Each subcommand does the same thing as running its module directly. For example, `moonshine-voice mic --language en` is the same as `python -m moonshine_voice.mic_transcriber --language en`. The CLI suits one-off jobs. If a task makes several calls, load the models once from Python instead, which is more efficient.

**Raspberry Pi:** use the same pip package with a USB microphone. If pip warns about system packages, use a virtual environment or run `pip install --break-system-packages moonshine-voice`.

### iOS and macOS (Swift Package Manager)

1. In Xcode, right-click the file view sidebar and choose **Add Package Dependencies...**.
2. Paste `https://github.com/moonshine-ai/moonshine-swift/` into the search box.
3. Select `moonshine-swift` and choose **Add Package**.
4. Write `import MoonshineVoice` in your code.
5. Add every model file you use to the app bundle, and make sure it is copied during the deployment phase so the app can read it on the device.

Reference projects: [`examples/ios/Transcriber`](https://github.com/moonshine-ai/moonshine/blob/main/examples/ios/Transcriber) and [`examples/macos/BasicTranscription`](https://github.com/moonshine-ai/moonshine/blob/main/examples/macos/BasicTranscription/).

### Android (Gradle)

1. In `gradle/libs.versions.toml`, add the version under `[versions]`:
   `moonshineVoice = "0.1.6"`
2. In the same file, add the library under `[libraries]`:
   `moonshine-voice = { group = "ai.moonshine", name = "moonshine-voice", version.ref = "moonshineVoice" }`
3. In `app/build.gradle.kts`, add it to `dependencies`:
   `implementation(libs.moonshine.voice)`

Reference projects: [`examples/android/Transcriber`](https://github.com/moonshine-ai/moonshine/blob/main/examples/android/Transcriber/) and [`examples/android/TextToSpeech`](https://github.com/moonshine-ai/moonshine/blob/main/examples/android/TextToSpeech/). Both use `moonshineVoice = "0.1.6"`.

### Linux (C++)

Fetch the prebuilt library with the helper script in [`examples/c++`](https://github.com/moonshine-ai/moonshine/blob/main/examples/c++/README.md):

```bash
cd examples/c++
./download-library.sh
```

The script creates a `moonshine-voice/` folder. Headers go in `include/`. `libmoonshine.so` and its ONNX Runtime dependency go in `lib/`. Compile and link against them:

```bash
g++ your_app.cpp \
  -Imoonshine-voice/include \
  -Lmoonshine-voice/lib \
  -lmoonshine \
  -Wl,-rpath,'$ORIGIN/moonshine-voice/lib' \
  -o your_app
```

```cpp
#include "moonshine-cpp.h"
```

For a minimal end-to-end program, see [`examples/c++/transcriber.cpp`](https://github.com/moonshine-ai/moonshine/blob/main/examples/c++/transcriber.cpp).

### Windows (C++)

Windows has no package manager. Download the raw library instead:

1. Run [`examples/windows/cli-transcriber/download-lib.bat`](https://github.com/moonshine-ai/moonshine/blob/main/examples/windows/cli-transcriber/download-lib.bat).
2. Add the `include` folder to your project's include search paths.
3. Add the `lib` folder to the library search paths.
4. Add every library file in `lib` to the linker dependencies.
5. Use the header-only C++ binding, which is the recommended interface on Windows: `#include "moonshine-cpp.h"`.

Full example: [`examples/windows/cli-transcriber`](https://github.com/moonshine-ai/moonshine/blob/main/examples/windows/cli-transcriber).

## Build from source

Build from source when you need to debug the library internals, add instrumentation, or make your own changes.

### Before you build: assets and Git LFS

Large model and TTS binaries are **not** stored in git. Before you run the tests or do offline TTS work, fetch them from the CDN or the [Hugging Face mirror](https://huggingface.co/moonshine-ai/moonshine-voice-assets):

```bash
scripts/fetch-voice-assets.sh all
```

Some compile-time embeds and the ONNX Runtime prebuilts are stored in Git LFS. Install git-lfs and run `git lfs install` before you clone. In an existing clone, run `git lfs pull`.

### Build the C++ core with CMake

The core engine is in `core/`. It is written in C++ and exposes a C interface. CMake is the build system on every platform:

```bash
cd core
mkdir -p build
cd build
cmake ..
cmake --build .
```

The build produces unit test executables. Run them from the `test-assets` folder. To build and run the tests in one step, use [`scripts/test-core.sh`](https://github.com/moonshine-ai/moonshine/blob/main/scripts/test-core.sh), or [`scripts/test-core.bat`](https://github.com/moonshine-ai/moonshine/blob/main/scripts/test-core.bat) on Windows. Every test should compile and pass.

### Language bindings

- [`scripts/build-all-platforms.sh`](https://github.com/moonshine-ai/moonshine/blob/main/scripts/build-all-platforms.sh) builds every release artifact for every supported platform. It is the reference for how to build each target.
- Each binding is a layer over the C interface that gives it an idiomatic API and handles the platform's event system. The bindings live under [`language-bindings/`](https://github.com/moonshine-ai/moonshine/tree/main/language-bindings), for example:
  - [`language-bindings/python`](https://github.com/moonshine-ai/moonshine/blob/main/language-bindings/python/)
  - [`language-bindings/android`](https://github.com/moonshine-ai/moonshine/blob/main/language-bindings/android/)
  - [`language-bindings/swift`](https://github.com/moonshine-ai/moonshine/blob/main/language-bindings/swift/) (iOS and macOS)
- Branching: `main` always matches the most recently published binaries. Development happens on a `dev-v<version>` candidate branch. For details, see [`docs/release-process.md`](https://github.com/moonshine-ai/moonshine/blob/main/docs/release-process.md).

### Port to a new platform

1. Build the core with CMake on the target system, as described above.
2. ONNX Runtime is the core's only major dependency. [Prebuilt libraries](https://github.com/moonshine-ai/moonshine/blob/main/core/third-party/onnxruntime/lib/) are included for the supported systems. For any other target, find or build your own [ONNX Runtime](https://github.com/microsoft/onnxruntime).

### Bind a new language

Start from [`core/moonshine-c-api.h`](https://github.com/moonshine-ai/moonshine/blob/main/core/moonshine-c-api.h). Most languages can call C functions, so wrap that API and use the existing bindings in `language-bindings/` as models. For a summary of the C API, see the [C API reference](../reference/c-api/SKILL.md).

## Common pitfalls

| Symptom | Cause | Fix |
| --- | --- | --- |
| `'version' does not name a type` when compiling embedded sources such as `community1_cpp_annote_embedded.cpp` | The repo was cloned without Git LFS, so LFS pointer text files are being compiled in place of the real sources | Install git-lfs, then run `git lfs pull` |
| Tests or offline TTS can't find models | The asset binaries are not in git | Run `scripts/fetch-voice-assets.sh all` |
| Unit tests fail to find files | The tests are run from the wrong directory | Run them from `test-assets`, or use `scripts/test-core.sh` |
| iOS/macOS app can't load a model on the device | The model files are not in the app bundle | Add them to the bundle and copy them during deployment |
| Linux binary can't find `libmoonshine.so` at runtime | No rpath is set | Link with `-Wl,-rpath,'$ORIGIN/moonshine-voice/lib'` or ship the `lib/` folder alongside the binary |
| `pip` refuses to install on Raspberry Pi OS | The system Python is externally managed | Use a venv or `--break-system-packages` |

For runtime problems after integration, see the [debugging skill](../debugging/SKILL.md). To fetch models for your app, see [model downloads](../model-downloads/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [using/adding-the-library.md](references/using-adding-the-library.md)
- [using/building-from-source.md](references/using-building-from-source.md)
