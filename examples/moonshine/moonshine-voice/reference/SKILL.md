---
name: reference
description: 'API reference for Moonshine Voice: the high-level classes, every option accepted by the speech-to-text, text-to-speech, grapheme-to-phoneme and embedding components, and the full C API. Use when a task needs an exact signature, class member, option name, default value, constant, error code or C function rather than a how-to guide.'
---

# Moonshine Voice API Reference

Use this skill to look up exact API details for Moonshine Voice: class members, option names and values, constants, error codes, data structures and C functions. It does not explain concepts or walk through tasks. For installation, the quickstart and the main usage pattern (load a model, create a `Transcriber` or `MicTranscriber`, listen for transcript events), see the root skill [moonshine-voice](../SKILL.md).

The reference has three parts. Each subskill holds the full details for its part:

| Part | What it covers | Go to |
|---|---|---|
| Classes | The high-level classes in the language bindings, with their constructors, methods, events and properties | [classes](classes/SKILL.md) |
| Options | Option names and values passed as `moonshine_option_t` in C or as keyword options in a binding | [options](options/SKILL.md) |
| C API | Constants, data structures, functions, and the rules for who owns and frees memory | [c-api](c-api/SKILL.md) |

## Classes at a glance

Open [classes](classes/SKILL.md) for exact signatures. It covers these classes:

| Class | Area |
|---|---|
| `Transcriber` | Speech to text |
| `MicTranscriber` | Speech to text from the microphone |
| `Stream` | Streaming transcription input |
| `TranscriptEventListener` | Callbacks for transcript events |
| `AgentFlow` | Voice agents |
| `Dialog` | Voice agents |
| `TextToSpeech` | Speech synthesis |
| `GraphemeToPhonemizer` | Grapheme-to-phoneme conversion |
| `EmbeddingModel` | Speaker and speech embeddings |

Compute speaker or speech embeddings from a binding with `EmbeddingModel`. The details are in [classes](classes/SKILL.md).

## Option groups at a glance

Open [options](options/SKILL.md) to set, look up or validate an option. It covers these groups:

- Shared options, used by more than one component
- Speech-to-text options
- Text-to-speech options
- Grapheme-to-phoneme roots
- Runtime, lexicon and model path overrides
- Language feature flags
- Embedding options
- Speech clip extraction options
- Download manifest functions

Options are passed one of two ways:

- **In C:** as `moonshine_option_t` values. The struct is defined in [c-api](c-api/SKILL.md).
- **In the bindings:** as keyword options.

## C API at a glance

Open [c-api](c-api/SKILL.md) when writing C or C++ code, or a new binding.

| Group | Key items |
|---|---|
| Constants | Version, model architectures, error codes, flags |
| Data structures | `moonshine_option_t`, `transcript_word_t`, `speaker_span_t`, `transcript_line_t`, `transcript_t`, `moonshine_speech_clip_t` |
| Transcriber loading and streaming | `moonshine_load_transcriber_from_files`, `moonshine_create_stream`, `moonshine_transcribe_add_audio_to_stream`, `moonshine_transcribe_stream` |
| Embeddings | `moonshine_calculate_embedding`, `moonshine_calculate_embedding_distance` |
| Speech clips | Speech clip functions (see the subskill) |
| Text to speech | `moonshine_create_tts_synthesizer_from_files`, `moonshine_text_to_speech`, `moonshine_tts_split_utterances` |
| Grapheme to phonemes | See the subskill |
| Model download manifests | See the subskill |
| Memory and lifecycle | `moonshine_free_buffer`, `moonshine_free_transcriber` |

Before you use the result of any C call that returns memory, check the ownership and freeing rules in [c-api](c-api/SKILL.md). This skill does not list exact signatures, return types or error code values. Read them from the subskill instead of guessing.

## Which subskill for which lookup

| You need… | Open |
|---|---|
| A method, callback or property of a binding class | [classes](classes/SKILL.md) |
| The name, value or default of an option | [options](options/SKILL.md) |
| Which option overrides a model, lexicon or runtime path | [options](options/SKILL.md) |
| A download manifest function | [options](options/SKILL.md) |
| An error code, flag, version or model architecture constant | [c-api](c-api/SKILL.md) |
| The fields of a transcript, word, line, speaker span or speech clip struct | [c-api](c-api/SKILL.md) |
| Who frees a buffer or transcriber, and how | [c-api](c-api/SKILL.md) |

## How-to guides

For step-by-step guides rather than reference, use these skills:

- Transcription: [transcription](../transcription/SKILL.md)
- Text to speech: [text-to-speech](../text-to-speech/SKILL.md)
- Voice agents: [voice-agent](../voice-agent/SKILL.md)
- Choosing a model: [model-selection](../model-selection/SKILL.md)
- Downloading models: [model-downloads](../model-downloads/SKILL.md)
- Adding the library to an app or building from source: [app-integration](../app-integration/SKILL.md)
- Domain customization: [domain-customization](../domain-customization/SKILL.md)
- Debugging: [debugging](../debugging/SKILL.md)

## Subskills

Read the one that matches your task:

- [classes](classes/SKILL.md): Reference for the high-level Moonshine classes and their methods and events: Transcriber, MicTranscriber, Stream, TranscriptEventListener, AgentFlow, Dialog, TextToSpeech, GraphemeToPhonemizer and EmbeddingModel. Use when a task needs the exact constructor arguments, methods, callbacks or properties of one of these classes, or when computing speaker or speech embeddings with EmbeddingModel.
- [options](options/SKILL.md): Reference for the option names and values Moonshine accepts: shared options, speech-to-text options, text-to-speech options, grapheme-to-phoneme roots, runtime, lexicon and model path overrides and language feature flags, embedding options, speech clip extraction options, and the download manifest functions. Use when a task needs to set, look up or validate a specific option passed as moonshine_option_t or as keyword options in a binding.
- [c-api](c-api/SKILL.md): Reference for the Moonshine C API: constants (version, model architectures, error codes, flags), data structures (moonshine_option_t, transcript_word_t, speaker_span_t, transcript_line_t, transcript_t, moonshine_speech_clip_t), utilities, transcriber loading and streaming (moonshine_load_transcriber_from_files, moonshine_create_stream, moonshine_transcribe_add_audio_to_stream, moonshine_transcribe_stream), embeddings (moonshine_calculate_embedding, moonshine_calculate_embedding_distance), speech clips, text to speech (moonshine_create_tts_synthesizer_from_files, moonshine_text_to_speech, moonshine_tts_split_utterances), grapheme to phonemes and model download manifests. Use when writing C or C++ code or new bindings against Moonshine, or when checking ownership and freeing rules (moonshine_free_buffer, moonshine_free_transcriber).
