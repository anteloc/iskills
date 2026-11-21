---
name: c-api
description: 'Reference for the Moonshine C API: constants (version, model architectures, error codes, flags), data structures (moonshine_option_t, transcript_word_t, speaker_span_t, transcript_line_t, transcript_t, moonshine_speech_clip_t), utilities, transcriber loading and streaming (moonshine_load_transcriber_from_files, moonshine_create_stream, moonshine_transcribe_add_audio_to_stream, moonshine_transcribe_stream), embeddings (moonshine_calculate_embedding, moonshine_calculate_embedding_distance), speech clips, text to speech (moonshine_create_tts_synthesizer_from_files, moonshine_text_to_speech, moonshine_tts_split_utterances), grapheme to phonemes and model download manifests. Use when writing C or C++ code or new bindings against Moonshine, or when checking ownership and freeing rules (moonshine_free_buffer, moonshine_free_transcriber).'
---

# Moonshine C API Reference

This is a compact reference for `core/moonshine-c-api.h`, the portable ABI underneath every Moonshine binding (Python, Swift, Java/Android, JavaScript/WASM, C++). Use it to write C or C++ code against Moonshine, to build a new binding, or to check who owns a buffer and how to free it. For application code, prefer the higher-level bindings (see [classes](../classes/SKILL.md)). Option keys passed through `moonshine_option_t` are listed in [options](../options/SKILL.md).

## Core conventions

- **Thread safety:** every call is thread-safe. Work on one transcriber is serialized, so concurrent calls on the same handle wait in a queue.
- **Handles:** handles are opaque `int32_t` values. A non-negative value means success and a negative value is an error code. Turn any code into text with `moonshine_error_to_string()`.
- **Status returns:** most calls return `0` (`MOONSHINE_ERROR_NONE`) on success and a non-zero code on failure.
- **Versioning:** always pass `MOONSHINE_HEADER_VERSION` as `moonshine_version`. A newer shared library then emulates the header you compiled against.
- **Freeing:** release every buffer the docs call "allocated with malloc" with `moonshine_free_buffer()`, never with the CRT `free`. On Windows the library and its host can use different C runtimes with separate heaps. `moonshine_free_buffer()` is safe to call on `NULL`.
- **Handle reuse:** after you free a handle, a later create call may hand out the same ID. Drop every reference to a handle once it is freed.
- **Option values:** options are name/value string pairs. Values are always strings, even for numbers and booleans.

## Ownership and freeing rules

| Data | Owner | How to release / lifetime |
| --- | --- | --- |
| `transcript_t *` from `moonshine_transcribe_stream()` / `moonshine_transcribe_without_streaming()` (lines, words, spans, audio) | Transcriber | Do not free. Valid until the next call on that transcriber, or until it is freed. Copy anything you need to keep. |
| String from `moonshine_transcript_to_string()` | Library | Do not free. Valid until the next call to `moonshine_transcript_to_string()`. |
| `tts_chunk_t *` from `moonshine_tts_next_chunk()` | Synthesizer | Do not free. Valid until the next call on that synthesizer. |
| `out_audio_data` from `moonshine_text_to_speech()` / `moonshine_phonemes_to_speech()` | Caller | `moonshine_free_buffer()` |
| `out_phonemes` from `moonshine_text_to_phonemes()` | Caller | `moonshine_free_buffer()` |
| JSON/CSV strings from `moonshine_get_*_dependencies()`, `moonshine_get_tts_voices()`, `moonshine_get_*_catalog()`, `moonshine_tts_split_utterances()` | Caller | `moonshine_free_buffer()` |
| `moonshine_speech_clip_t.audio_data` and `.transcript` | Caller | `moonshine_free_buffer()` on each |
| `out_embedding` from `moonshine_calculate_embedding()` | Caller | `moonshine_free_embedding()` |
| Input buffers to `moonshine_load_transcriber_from_memory_files()` (and the deprecated `_from_memory`) | Caller | Not copied. Keep them alive until the transcriber is freed. |
| Input buffers to `moonshine_create_tts_synthesizer_from_memory()` | Caller | Not copied. Keep them alive until `moonshine_free_tts_synthesizer()`. |
| Input buffers to `moonshine_create_grapheme_to_phonemizer_from_memory()` | Caller | Not copied. Keep them alive until the phonemizer is freed. |
| Input buffers to `moonshine_create_embedding_model_from_memory()` | Caller | Copied. They only need to stay valid for the duration of the call. |

| Handle kind | Free with |
| --- | --- |
| Transcriber | `moonshine_free_transcriber()` |
| Stream | `moonshine_free_stream(transcriber, stream)` |
| Embedding model | `moonshine_free_embedding_model()` |
| TTS synthesizer | `moonshine_free_tts_synthesizer()` |
| Grapheme-to-phonemizer | `moonshine_free_grapheme_to_phonemizer()` |

TTS streaming has no stream object, so there is nothing to create or free for it.

## Constants

**Version.** Both version constants use the format `MAJOR * 10000 + MINOR * 100 + PATCH`.

| Constant | Value | Meaning |
| --- | --- | --- |
| `MOONSHINE_HEADER_VERSION` | `30000` (3.0.0) | Pass this to loaders. |
| `MOONSHINE_FROM_MEMORY_REMOVED_VERSION` | `30000` | The deprecated `moonshine_load_transcriber_from_memory()` refuses callers that pass this version or newer. |

**Model architectures**

| Constant | Value |
| --- | --- |
| `MOONSHINE_MODEL_ARCH_TINY` | `0` |
| `MOONSHINE_MODEL_ARCH_BASE` | `1` |
| `MOONSHINE_MODEL_ARCH_TINY_STREAMING` | `2` |
| `MOONSHINE_MODEL_ARCH_BASE_STREAMING` | `3` |
| `MOONSHINE_MODEL_ARCH_SMALL_STREAMING` | `4` |
| `MOONSHINE_MODEL_ARCH_MEDIUM_STREAMING` | `5` |
| `MOONSHINE_EMBEDDING_MODEL_ARCH_GEMMA_300M` | `0` |

**Error and status codes**

| Constant | Value | Notes |
| --- | --- | --- |
| `MOONSHINE_ERROR_NONE` | `0` | |
| `MOONSHINE_ERROR_UNKNOWN` | `-1` | |
| `MOONSHINE_ERROR_INVALID_HANDLE` | `-2` | |
| `MOONSHINE_ERROR_INVALID_ARGUMENT` | `-3` | |
| `MOONSHINE_ERROR_BUSY` | `-4` | Returned by `moonshine_text_to_speech()` while a streaming generation is running. |
| `MOONSHINE_TTS_NEED_TEXT` | `1` | TTS streaming status. Positive, so it is not an error. |
| `MOONSHINE_TTS_END_OF_STREAM` | `2` | TTS streaming status. |
| `MOONSHINE_TTS_CANCELLED` | `3` | TTS streaming status. |

**Flags**

| Constant | Used by | Meaning |
| --- | --- | --- |
| `MOONSHINE_FLAG_FORCE_UPDATE` | `moonshine_transcribe_stream()` | Skips the ~200ms caching window and forces a full analysis. |
| `MOONSHINE_FLAG_SPELLING_MODE` | `moonshine_transcribe_stream()`, `moonshine_transcribe_without_streaming()` | Applies alphanumeric-spelling fusion to completed lines, replacing the line `text` with the resolved character (for example `"a"` or `"$"`). Needs a spelling model at load time; otherwise it is ignored. |

## Data structures

**`moonshine_option_t`**

| Member | Type |
| --- | --- |
| `name` | `const char *` |
| `value` | `const char *` |

**`transcript_t`**

| Member | Type |
| --- | --- |
| `lines` | `struct transcript_line_t *` |
| `line_count` | `uint64_t` |

The transcript is reset whenever a stream starts fresh or a new one-shot transcription runs.

**`transcript_line_t`**

| Member | Type | Notes |
| --- | --- | --- |
| `text` | `const char *` | UTF-8. `""` means speech was detected but nothing was transcribed. |
| `audio_data` / `audio_data_count` | `const float *` / `size_t` | 16 kHz mono PCM in [-1.0, 1.0]. |
| `start_time` / `duration` | `float` | Seconds. |
| `id` | `uint64_t` | Random and stable for the line's lifetime. Do not rely on ids ascending. |
| `is_complete` | `int8_t` | Once set, text and timing never change again. |
| `is_updated` | `int8_t` | Any change since the previous `moonshine_transcribe_stream()` call. |
| `is_new` | `int8_t` | The line was added by the last update. |
| `has_text_changed` | `int8_t` | Implies `is_updated`. |
| `have_speakers_changed` | `int8_t` | Can be set on lines that are already complete (diarization). |
| `speaker_spans` / `speaker_span_count` | `const struct speaker_span_t *` / `uint64_t` | `NULL` unless `identify_speakers` is set. |
| `last_transcription_latency_ms` | `uint32_t` | Time from detected end of speech to the final text. |
| `words` / `word_count` | `const struct transcript_word_t *` / `uint64_t` | `NULL` / `0` unless `word_timestamps` is set. |

Streaming guarantees:

- Lines are only added, never removed.
- Only the last line can be incomplete.
- Line indexes stay stable across calls.
- Speaker spans inside `diarization_cluster_window_sec` (default 120 s) can still move, merge, split or change speaker. Older spans are frozen.

Bindings turn these flags into events such as `LineStarted`, `LineUpdated`, `LineTextChanged`, `LineSpeakersChanged` and `LineCompleted` (see [transcription](../../transcription/SKILL.md)).

**`transcript_word_t`**

| Member | Type | Notes |
| --- | --- | --- |
| `text` | `const char *` | |
| `start` | `float` | Seconds. |
| `end` | `float` | Seconds. |
| `confidence` | `float` | 0.0 to 1.0. |

**`speaker_span_t`**

| Member | Type | Notes |
| --- | --- | --- |
| `start_time` / `duration` | `float` | Seconds. |
| `speaker_id` | `uint64_t` | Stable for a speaker within a stream. |
| `speaker_index` | `uint32_t` | Order of first appearance, starting at 0. |
| `start_char` / `end_char` | `uint64_t` | UTF-8 byte offsets into the line text, end exclusive. Both are `0` when the span is not yet aligned to words. |

**`moonshine_speech_clip_t`**

| Member | Type | Notes |
| --- | --- | --- |
| `audio_data` | `float *` | 16 kHz mono. `NULL` unless `is_complete` is set. Free with `moonshine_free_buffer()`. |
| `audio_length` | `uint64_t` | Sample count. |
| `start_time` / `speech_duration` | `float` | Seconds. |
| `is_complete` | `int32_t` | Non-zero once a window with enough speech was found. |
| `transcript` | `char *` | Set only when clone ASR refined the clip, otherwise `NULL`. Free with `moonshine_free_buffer()`. |

**`tts_chunk_t`**

```c
struct tts_chunk_t {
  const float *audio_data;
  uint64_t     audio_data_count;
  int32_t      sample_rate;
  const char  *text;
  uint64_t     utterance_id;
  int8_t       is_final;
};
```

`utterance_id` counts from 1. `is_final` marks the last chunk of each utterance.

## Utilities

```c
int32_t moonshine_get_version(void);                 // loaded library version; may exceed MOONSHINE_HEADER_VERSION
const char *moonshine_error_to_string(int32_t error);
void moonshine_free_buffer(void *ptr);               // NULL-safe
const char *moonshine_transcript_to_string(const struct transcript_t *transcript);  // debugging only
```

## Speech to text

```c
int32_t moonshine_load_transcriber_from_files(
    const char *path, uint32_t model_arch,
    const struct moonshine_option_t *options, uint64_t options_count,
    int32_t moonshine_version);

int32_t moonshine_load_transcriber_from_memory_files(
    const char **filenames, const uint8_t **memory, const uint64_t *memory_sizes,
    uint64_t file_count, uint32_t model_arch,
    const struct moonshine_option_t *options, uint64_t options_count,
    int32_t moonshine_version);

void moonshine_free_transcriber(int32_t transcriber_handle);
int32_t moonshine_transcriber_set_keyterms(int32_t transcriber_handle, const char *keyterms);
int32_t moonshine_transcriber_set_context(int32_t transcriber_handle, const char *context, int32_t max_terms);

int32_t moonshine_transcribe_without_streaming(
    int32_t transcriber_handle, float *audio_data, uint64_t audio_length,
    int32_t sample_rate, uint32_t flags, struct transcript_t **out_transcript);
```

**Model files.** A non-streaming directory needs `encoder_model.ort`, `decoder_model_merged.ort` and `tokenizer.bin`. A streaming architecture needs:

- `frontend.ort`, or the split pair `frontend.model.ort` + `frontend.weights.ort`
- `encoder.ort`
- `adapter.ort`
- `cross_kv.ort`
- `decoder_kv.ort`
- `streaming_config.json`
- `tokenizer.bin`

Optional files:

- `decoder_with_attention.ort` or `alignment_model.ort` (non-streaming) for `word_timestamps`
- `decoder_kv_with_attention.ort` (streaming) for `word_timestamps`
- `spelling_cnn.ort` (`spelling_cnn_meta.json` is also accepted) for spelling mode
- `segmentation.ort` + `embedding.ort`, required when `identify_speakers` is set

Get the model files with `python scripts/download-moonshine-model.py --model-type base --model-language en`, or use the manifest calls below.

**`_from_memory_files` rules:**

- A filename outside the recognized set fails with `MOONSHINE_ERROR_INVALID_ARGUMENT`.
- Extra names that are recognized but not needed are fine, so you can pass a whole model directory.
- A `NULL` `memory[i]` or a size of `0` loads `filenames[i]` from disk, relative to the current working directory unless the path is absolute.

**Keyterms and context:**

- `moonshine_transcriber_set_keyterms()` takes a comma-separated list. Pass `NULL` or `""` to turn biasing off.
- `moonshine_transcriber_set_context()` picks out the unusual words of a passage by itself. A `max_terms` of `0` means the default of 200.
- Both work only on streaming architectures, and both take effect on the next transcribe call.

**Deprecated:** `moonshine_load_transcriber_from_memory()` refuses callers that pass `moonshine_version >= MOONSHINE_FROM_MEMORY_REMOVED_VERSION` and rejects streaming architectures. Use `moonshine_load_transcriber_from_memory_files()`.

**Sample rate:** audio is mono float PCM in [-1.0, 1.0] at `sample_rate` Hz. The library works at 16 kHz internally, so capture at 16 kHz to avoid resampling.

## Streaming speech to text

```c
int32_t moonshine_create_stream(int32_t transcriber_handle, uint32_t flags);   // flags: pass 0
int32_t moonshine_free_stream(int32_t transcriber_handle, int32_t stream_handle);
int32_t moonshine_start_stream(int32_t transcriber_handle, int32_t stream_handle);
int32_t moonshine_stop_stream(int32_t transcriber_handle, int32_t stream_handle);
int32_t moonshine_transcribe_add_audio_to_stream(
    int32_t transcriber_handle, int32_t stream_handle,
    const float *new_audio_data, uint64_t audio_length,
    int32_t sample_rate, uint32_t flags);                                       // flags: pass 0
int32_t moonshine_transcribe_stream(
    int32_t transcriber_handle, int32_t stream_handle,
    uint32_t flags, struct transcript_t **out_transcript);
```

```c
int32_t transcriber_handle = moonshine_load_transcriber_from_files(
    "path/to/models", MOONSHINE_MODEL_ARCH_BASE, NULL, 0,
    MOONSHINE_HEADER_VERSION);
int32_t stream_handle = moonshine_create_stream(transcriber_handle, 0);
moonshine_start_stream(transcriber_handle, stream_handle);

float *latest_audio_data;
size_t latest_audio_data_length;
while (get_audio_from_microphone(&latest_audio_data, &latest_audio_data_length)) {
  moonshine_transcribe_add_audio_to_stream(
      transcriber_handle, stream_handle, latest_audio_data,
      latest_audio_data_length, microphone_sample_rate, 0);
  transcript_t *partial_transcript = NULL;
  moonshine_transcribe_stream(
      transcriber_handle, stream_handle, 0, &partial_transcript);
  print_transcript(partial_transcript);
}
moonshine_stop_stream(transcriber_handle, stream_handle);

transcript_t *final_transcript = NULL;
moonshine_transcribe_stream(
    transcriber_handle, stream_handle, 0, &final_transcript);
print_transcript(final_transcript);

moonshine_free_stream(transcriber_handle, stream_handle);
moonshine_free_transcriber(transcriber_handle);
```

- `add_audio_to_stream` only buffers the audio, so it is safe to call from time-critical capture threads. Chunk size does not affect performance.
- `transcribe_stream` only runs a full analysis after more than 200ms of new audio, unless you pass `MOONSHINE_FLAG_FORCE_UPDATE`.
- After `stop_stream`, further audio is rejected. The next `transcribe_stream` call drains the leftover audio and marks every line complete, with no flag needed.
- Call `start_stream` before `transcribe_stream`. Use stop and start again to begin fresh after a break, such as a muted microphone.
- One transcriber can own several streams, one per audio source.

## Embeddings

```c
int32_t moonshine_create_embedding_model(const char *model_path, uint32_t model_arch, const char *model_variant);
int32_t moonshine_create_embedding_model_from_memory(
    uint32_t model_arch, const char *model_variant,
    const char **filenames, uint64_t filenames_count,
    const uint8_t **memory, const uint64_t *memory_sizes,
    const struct moonshine_option_t *options, uint64_t options_count,
    int32_t moonshine_version);
void moonshine_free_embedding_model(int32_t embedding_model_handle);
int32_t moonshine_calculate_embedding(
    int32_t embedding_model_handle, const char *sentence,
    float **out_embedding, uint64_t *out_embedding_size, const char *model_name);
void moonshine_free_embedding(float *embedding);
int32_t moonshine_calculate_embedding_distance(
    int32_t embedding_model_handle, const float *embedding_a, const float *embedding_b,
    uint64_t embedding_size, float *out_similarity);
```

- **Variants:** `model_variant` is `"q4"` (the default, also used for `NULL`) or `"q8"`. `"fp32"`, `"fp16"` and `"q4f16"` are no longer supported.
- **Files:** a variant's files are `model_<variant>.ort` (one self-contained file) and `tokenizer.bin`.
- **Prompt template:** `model_name` selects the prompt template. `NULL` means the default.
- **Distance:** `moonshine_calculate_embedding_distance()` returns cosine similarity in [-1, 1].

## Speech clips (voice-cloning reference)

```c
int32_t moonshine_extract_speech_clip(
    const float *audio_data, uint64_t audio_length, int32_t sample_rate,
    int32_t tts_synthesizer_handle,
    const struct moonshine_option_t *options, uint64_t options_count,
    struct moonshine_speech_clip_t *out_clip);
```

- **Cost:** the call uses voice activity detection only, so it is cheap enough for a capture loop.
- **Output format:** the clip is always 16 kHz mono.
- **Success without a clip:** a return of `0` does not guarantee a clip. If no window holds `minimum_speech_seconds` of speech, `out_clip->is_complete` is `0`. Record more audio and call again.

## Text to speech

```c
int32_t moonshine_create_tts_synthesizer_from_files(
    const char *language, const char **filenames, uint64_t filenames_count,
    const struct moonshine_option_t *options, uint64_t options_count,
    int32_t moonshine_version);
int32_t moonshine_create_tts_synthesizer_from_memory(
    const char *language, const char **filenames, const uint64_t filenames_count,
    const uint8_t **memory, const uint64_t *memory_sizes,
    const struct moonshine_option_t *options, uint64_t options_count,
    int32_t moonshine_version);
void moonshine_free_tts_synthesizer(int32_t tts_synthesizer_handle);
int32_t moonshine_text_to_speech(
    int32_t tts_synthesizer_handle, const char *text,
    const struct moonshine_option_t *options, uint64_t options_count,
    float **out_audio_data, uint64_t *out_audio_data_size, int32_t *out_sample_rate);
int32_t moonshine_phonemes_to_speech(
    int32_t tts_synthesizer_handle, const char *phonemes,
    const struct moonshine_option_t *options, uint64_t options_count,
    float **out_audio_data, uint64_t *out_audio_data_size, int32_t *out_sample_rate);
int32_t moonshine_get_tts_dependencies(
    const char *languages, const struct moonshine_option_t *options,
    uint64_t options_count, char **out_dependencies_json);
int32_t moonshine_get_tts_voices(
    const char *languages, const struct moonshine_option_t *options,
    uint64_t options_count, char **out_voices_json);
int32_t moonshine_tts_split_utterances(
    const char *text, const struct moonshine_option_t *options,
    uint64_t options_count, char **out_utterances_json);
```

**Language and asset keys:**

- `language` is a tag such as `"en_us"`.
- `filenames` are canonical keys resolved relative to `g2p_root`, for example `kokoro/decoder.model.ort`, `kokoro/voices/af_heart.kokorovoice`, `piper/onnx` and `zipvoice/vocoder.ort`.
- In `_from_memory`, a `NULL` entry or a size of `0` loads that key from disk.

**ZipVoice cloning:**

- Pass the reference clip under the key `zipvoice/clone_audio` as raw little-endian float32 mono PCM, and set `zipvoice_clone_sample_rate`.
- Either set `zipvoice_clone_transcript` or supply `clone_asr/<stt-filename>` keys so the library can transcribe the clip itself.

**Per-call options:** only `speed` is honored by `text_to_speech` and `phonemes_to_speech`. Pass `NULL` / `0` to use the construction defaults.

**Phonemes:** `phonemes_to_speech` takes IPA in the format `moonshine_text_to_phonemes()` produces for the same language.

**Voice list (`moonshine_get_tts_voices()`):**

- It returns JSON that maps each language to an array of `{"id":"kokoro_...|piper_...","state":"found"|"missing"}`.
- Set `g2p_root` (or its aliases `path_root`, `tts_root`, `model_root`) so the found/missing state is accurate.
- The `voice` option does not filter the list.

**Dependency manifest:**

- `moonshine_get_tts_dependencies()` returns `{"groups":[...]}` in the same shape as the STT manifest.
- When ZipVoice is selected, it adds a `"role":"clone_asr"` group. Download those files under `g2p_root/clone_asr/`.

**Utterance splitting:**

- `moonshine_tts_split_utterances()` returns a JSON array of strings.
- It accepts the options `language`, `split_on_colon` and `min_codepoints`.
- It keeps `Dr. Smith`, `J. R. R. Tolkien` and `3.14` whole, handles terminators such as `。！？`, and never splits inside quotes or brackets.

### Streaming synthesis

```c
int32_t moonshine_tts_push_text(int32_t tts_synthesizer_handle, const char *text);
int32_t moonshine_tts_flush(int32_t tts_synthesizer_handle);
int32_t moonshine_tts_end_input(int32_t tts_synthesizer_handle);
int32_t moonshine_tts_cancel(int32_t tts_synthesizer_handle);
int32_t moonshine_tts_is_streaming(int32_t tts_synthesizer_handle);
int32_t moonshine_tts_next_chunk(int32_t tts_synthesizer_handle, uint32_t flags,
                                 const struct tts_chunk_t **out_chunk);
```

Streaming is synchronous and pull-based. Each call does the following:

- **`moonshine_tts_push_text()`** buffers text until it forms a complete utterance.
- **`moonshine_tts_flush()`** makes partial text synthesizable.
- **`moonshine_tts_end_input()`** flushes and closes the generation.
- **`moonshine_tts_cancel()`** discards buffered text and pending audio. It is safe to call when nothing is streaming.
- **`moonshine_tts_next_chunk()`** blocks only while it computes, and returns one of:

| Return | Meaning |
| --- | --- |
| `MOONSHINE_ERROR_NONE` | A chunk is available. |
| `MOONSHINE_TTS_NEED_TEXT` | Push more text or flush. |
| `MOONSHINE_TTS_END_OF_STREAM` | Input has ended and the queue is drained. |
| `MOONSHINE_TTS_CANCELLED` | Sent once, and only if a cancel actually discarded something. |

While a generation is running, `moonshine_text_to_speech()` returns `MOONSHINE_ERROR_BUSY`.

## Grapheme to phonemes

```c
int32_t moonshine_create_grapheme_to_phonemizer_from_files(
    const char *language, const char **filenames, uint64_t filenames_count,
    const struct moonshine_option_t *options, uint64_t options_count,
    int32_t moonshine_version);
int32_t moonshine_create_grapheme_to_phonemizer_from_memory(
    const char *language, const char **filenames, const uint64_t filenames_count,
    const uint8_t **memory, const uint64_t *memory_sizes,
    const struct moonshine_option_t *options, uint64_t options_count,
    int32_t moonshine_version);
void moonshine_free_grapheme_to_phonemizer(int32_t grapheme_to_phonemizer_handle);
int32_t moonshine_text_to_phonemes(
    int32_t grapheme_to_phonemizer_handle, const char *text,
    const struct moonshine_option_t *options, uint64_t options_count,
    const char **out_phonemes, uint64_t *out_phonemes_count);
int32_t moonshine_get_g2p_dependencies(
    const char *languages, const struct moonshine_option_t *options,
    uint64_t options_count, char **out_dependencies_json);
```

- **ORT only:** every model must be in ORT format, because `.onnx` files cannot be loaded. Convert them with `scripts/convert-models-to-ort.py`. In-memory buffers must be self-contained, with no sidecar weights file.
- **Asset keys:** keys look like `en_us/dict_filtered_heteronyms.tsv`, `en_us/g2p-config.json` and `en_us/oov/model.ort`. Korean uses only `ko/dict.tsv`.
- **English OOV overrides:** use the memory keys `oov_onnx_override` and `oov_onnx_config`.
- **Dependency list:** despite its name, `moonshine_get_g2p_dependencies()` writes a **comma-separated list**, not JSON, and sets the output to `NULL` on failure.

## Model download manifests

```c
int32_t moonshine_get_stt_dependencies(
    const char *language, const struct moonshine_option_t *options,
    uint64_t options_count, char **out_dependencies_json);
int32_t moonshine_get_embedding_dependencies(
    const char *model_name, const struct moonshine_option_t *options,
    uint64_t options_count, char **out_dependencies_json);
int32_t moonshine_get_diarization_dependencies(char **out_dependencies_json);
int32_t moonshine_get_stt_catalog(char **out_catalog_json);
int32_t moonshine_get_embedding_catalog(char **out_catalog_json);
```

**Manifest shape:**

```
{"groups":[{"base_url":"...","files":[{"name":"encoder_model.ort","url":"...","size":12345,"checksum":"abc==","checksum_type":"crc32c"}]}]}
```

`size` can be `null`, and `checksum` / `checksum_type` can be `""`. All outputs are freed with `moonshine_free_buffer()`, and are set to `NULL` on failure.

| Call | Notes |
| --- | --- |
| `moonshine_get_stt_dependencies()` | `language` is a code (`"en"`) or English name (`"English"`) and must not be empty. Returns one group, plus an optional spelling-model group. Only options that change the file set are honored (see [options](../options/SKILL.md)). |
| `moonshine_get_embedding_dependencies()` | `model_name` such as `"embeddinggemma-300m"`; `NULL` means the default model. Accepts `variant` / `model_variant`. |
| `moonshine_get_diarization_dependencies()` | Two files, about 8.2 MB. Needed for `identify_speakers=true` since 26.8: without them the transcriber now fails to load. Point the `diarization_model_dir` option at them, or pass them to `moonshine_load_transcriber_from_memory_files()`. |
| `moonshine_get_stt_catalog()` | `{"languages":[{"code","english_name","models":[{"model_arch","download_url","is_default"}]}]}` |
| `moonshine_get_embedding_catalog()` | `{"models":[{"name","english_name","download_url","variants","default_variant"}]}` |

How to drive downloads from these manifests is covered in [model-downloads](../../model-downloads/SKILL.md).

## Common pitfalls

- **Freeing with CRT `free`.** Release library buffers with `moonshine_free_buffer()`, embeddings with `moonshine_free_embedding()`, and never free transcripts or TTS chunks.
- **Keeping a `transcript_t` across calls.** Its memory becomes invalid on the next call on that transcriber. Copy what you need.
- **Freeing model buffers too early.** Transcriber, TTS and G2P memory loaders do not copy their input buffers. Only the embedding loader does.
- **Calling `set_keyterms` / `set_context` on a non-streaming model.** Both return an error.
- **Enabling `identify_speakers` without diarization models.** The load fails.
- **Passing `.onnx` models.** Only ORT format loads.

The long tail, including full prose for every argument, is in the verbatim `api/c-api.md` source doc linked below.

## Source docs

Verbatim copies, for details not covered above:

- [api/c-api.md](references/api-c-api.md)
