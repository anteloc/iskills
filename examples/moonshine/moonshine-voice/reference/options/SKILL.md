---
name: options
description: 'Reference for the option names and values Moonshine accepts: shared options, speech-to-text options, text-to-speech options, grapheme-to-phoneme roots, runtime, lexicon and model path overrides and language feature flags, embedding options, speech clip extraction options, and the download manifest functions. Use when a task needs to set, look up or validate a specific option passed as moonshine_option_t or as keyword options in a binding.'
---

# Moonshine Options

Use this catalog to find the option keys Moonshine constructors accept. Most constructors take a string-to-string options map: a Python dict, a `moonshine_option_t` array in C, or name/value pairs in other bindings. At the ABI, every value is a string. Bindings may accept bools and numbers and convert them to strings for you.

For constructor signatures, see [classes](../classes/SKILL.md) and the [C API](../c-api/SKILL.md).

## Where options go

| Component | Pass options to |
| --- | --- |
| Speech to text | `Transcriber(..., options=…)`, MicTranscriber `.options()`, `moonshine_load_transcriber_from_files()` / `_from_memory_files()` / deprecated `_from_memory()` |
| Text to speech | `TextToSpeech.options()`, AgentFlow `.speech_options()`, `moonshine_create_tts_synthesizer_from_files()` / `_from_memory()`, plus `moonshine_get_tts_dependencies()` and `moonshine_get_tts_voices()` |
| Grapheme to phonemes | `GraphemeToPhonemizer(..., options=…)`, `moonshine_create_grapheme_to_phonemizer_*`, `moonshine_get_g2p_dependencies()` |
| Speech clip extract | `moonshine_extract_speech_clip()` and the Python/VoiceClone capture path that wraps it |
| Embeddings | No options map at create time (see [Embeddings](#embeddings)) |
| STT download manifest | `moonshine_get_stt_dependencies()` |

MicTranscriber `.options()` passes its options to the native transcriber loader. AgentFlow `.speech_options()` passes its options to the TTS loader. The same keys apply in both places.

## Shared options

A common parser removes `log_api_calls` before API-specific parsing. `ort_providers` and `coreml_cache_dir` apply wherever ONNX Runtime sessions are created.

| Key | Accepted by | Description |
| --- | --- | --- |
| `log_api_calls` | Transcriber, TTS, G2P, speech-clip extract, other C entry points that run common parsing | When true, logs C API entry points and their arguments to stderr or the console. |
| `ort_providers` (alias `ort_provider`) | Transcriber, TTS, G2P | Comma-separated, ordered ONNX Runtime execution providers, e.g. `CoreML,CPU`. Names are case-insensitive. Short forms (`CPU`, `CoreML`, `NNAPI`) and full names both work. When unset, only the CPU is used, which is the recommended setting. Mobile libraries ship CPU-only, so asking for another provider there is an error. See [execution providers](https://github.com/moonshine-ai/moonshine/blob/main/docs/execution-providers.md). |
| `coreml_cache_dir` | Transcriber, TTS, G2P | Directory for the CoreML compiled-model cache on macOS. Used only when `ort_providers` lists `CoreML`. |
| `log_profiling` | TTS, G2P | When true, logs profiling information to the console. |
| `g2p_root` | TTS, G2P (and TTS dependency/voice listing) | Asset root for the G2P and TTS file layout. When empty, the process's current working directory is used. |
| `path_root` / `model_root` | Same as `g2p_root` | Aliases for `g2p_root`. |
| `tts_root` | TTS create / dependencies / voices | Alias for the asset root used to resolve the TTS layout. |

## Speech to Text

| Key | Default | Description |
| --- | --- | --- |
| `skip_transcription` | false | Runs only VAD and segmentation, with no STT. Use each line's audio buffer for further processing. |
| `max_tokens_per_second` | `6.5` | Cuts decoder loops short when the token rate looks pathological. Use about `13.0` for many non-Latin languages. |
| `use_speculative_decoding` | true | For streaming: checks the previous hypothesis and continues from the first mismatch. When false, decoding falls back to greedy redecode from BOS. |
| `keyterms` | (none) | Comma-separated terms to bias towards (streaming architectures only). See [Domain Customization](../../domain-customization/SKILL.md). You can also set these at runtime with `set_keyterms` / `moonshine_transcriber_set_keyterms()`. |
| `keyterm_boost` | `2.0` | Strength of key-term biasing. Raise it towards 4.0 to favor the list at the cost of surrounding words. Lower it towards 1.0 for the reverse. Biasing stops working above 4.0. |
| `context` | (none) | Free-form text that key terms are picked out of, for when you have context but no list (streaming architectures only). The terms are added to any `keyterms`. You can also set this at runtime with `set_context` / `moonshine_transcriber_set_context()`. |
| `context_max_terms` | `200` | Maximum number of terms taken from `context`. Keep it modest, because a longer list costs accuracy on the words you did not list. |
| `transcription_interval` | `0.5` | Seconds between automatic transcription passes. Related to Python's `update_interval`. |
| `vad_threshold` | `0.5` | VAD sensitivity. Lower values give longer segments and higher values give shorter chunks. `0` disables VAD; audio is still chunked by `vad_max_segment_duration`. |
| `vad_window_duration` | `0.5` | Seconds of VAD scores averaged when detecting speech. |
| `vad_hop_size` | `512` | VAD hop size in samples. |
| `vad_look_behind_sample_count` | `8192` | Samples added before the start of speech, at 16 kHz, to make up for the lag of averaged VAD. |
| `vad_max_segment_duration` | `15` | Maximum line length in seconds before the line is forced to complete. The threshold ramps down late in the segment. |
| `save_input_wav_path` | (none) | Folder path. Received audio is written there as 16 kHz mono WAVs for debugging. |
| `log_ort_run` | false | Logs ONNX Runtime inference runs and timings. |
| `word_timestamps` | false | Fills each line's `words` array. Needs the attention decoder asset. Turned on automatically by `identify_speakers`. |
| `decode_incomplete_lines` | true | Decodes lines that are still in progress, so text updates while someone is talking. Set it to false to wait until each line is complete. |
| `identify_speakers` | false | Enables diarization and `speaker_spans`. Needs the diarization models ([details](https://github.com/moonshine-ai/moonshine/blob/main/docs/diarization-models.md)). |
| `diarization_model_dir` | (none) | Directory holding `segmentation.ort` and `embedding.ort`, for when you construct a transcriber directly. |
| `diarization_cluster_cadence` | `2.0` | Minimum seconds of new audio between re-clustering passes. |
| `diarization_analyze_cadence` | `0` (the model default, `1.0`) | Sliding-window step for segmentation and embedding. Live `add_audio` / `transcribe()` runs at most one window per call. Remaining windows wait for the next call or Stop. Silent speaker classes skip embedding inference. |
| `diarization_cluster_window_sec` | `120` | Maximum recent history, in seconds, for streaming VBx. `0` means unlimited. Batch and one-shot runs always use the full history. |
| `return_audio_data` | true | Includes each line's PCM audio in transcript results. |
| `log_output_text` | false | Logs STT text to the console. |
| `spelling_model_path` | (none) | Path to a spelling-CNN `.ort` file, used for `MOONSHINE_FLAG_SPELLING_MODE`. |

The shared keys `log_api_calls`, `ort_providers` and `coreml_cache_dir` are also accepted.

## Text to Speech

| Key (aliases) | Description |
| --- | --- |
| `voice` | Catalog voice id. The prefix `kokoro_`, `piper_`, `zipvoice_` or `phonon_` selects the vocoder, e.g. `kokoro_af_heart` or `phonon_zoey`. |
| `speed` | Speaking-rate multiplier. It is the only per-call override that `say()` / `synthesize()` / `moonshine_text_to_speech()` / `moonshine_phonemes_to_speech()` honor. |
| `lang` / `language` | Language tag supplied through options. It is usually set by the constructor or the `language()` setter instead. |
| `kokoro_dir` | Overrides the Kokoro directory, which holds `prosody.model.ort`, `prosody.weights.ort`, `decoder.model.ort`, `decoder.weights.ort` and `config.json`. |
| `kokoro_model` / `kokoro_model_onnx` | Overrides the Kokoro model path. The value names the model, not a file that has to exist. The split pair next to it is preferred; otherwise a single `.ort` at exactly this path is loaded. |
| `kokoro_config` / `kokoro_config_json` | Overrides the Kokoro config JSON path. |
| `piper_onnx` / `piper_model_onnx` / `piper_model` | Overrides the Piper model path. The file must be `.ort`. |
| `piper_onnx_json` / `piper_model_json` / `piper_onnx_config` | Overrides the Piper JSON sidecar. |
| `piper_voices_dir` / `voices_dir` | Overrides the Piper voices directory. |
| `piper_voices_json_dir` / `voices_json_dir` | Overrides the directory of Piper `*.onnx.json` files. |
| `normalize_audio` / `piper_normalize_audio` | Peak-normalizes the audio, then applies gain and clipping. Default: true. |
| `output_volume` / `piper_output_volume` | Linear gain applied after normalizing. Default: `1`. |
| `piper_noise_scale` / `piper_noise_scale_override` | Piper inference noise scale. |
| `piper_noise_w` / `piper_noise_w_override` | Piper inference noise_w. |
| `zipvoice_clone_sample_rate` / `clone_sample_rate` | Sample rate of the caller-supplied `zipvoice/clone_audio`. Default: `24000`. |
| `zipvoice_clone_transcript` / `clone_transcript` | Transcript of that clone clip. |
| `zipvoice_model` / `zipvoice_model_name` | Selects `zipvoice` or the distilled model, which sets the sampling defaults. |
| `zipvoice_distill` | Uses the distilled ZipVoice sampling defaults. Default: true. |
| `zipvoice_num_step` / `num_step` | Number of diffusion steps. `<=0` uses the model default. |
| `zipvoice_guidance_scale` / `guidance_scale` | Guidance scale. `<0` uses the model default. |
| `zipvoice_t_shift` / `t_shift` | Time shift. Default: `0.5`. |
| `phonon_temperature` / `temperature` | Phonon sampling temperature. `0` is deterministic and `<0` uses the model default (`0.3`). |
| `phonon_seed` / `seed` | Seed for Phonon's sampling noise. Default: `0`. |
| `phonon_duration_delta` / `duration_delta` | Phonon duration conditioning; positive values are slower. When set, it replaces the mapping from `speed`. |
| `phonon_normalize_text` | Runs Phonon's typography and number normalization before tokenizing. Default: true. |
| `phonon_voice_file` / `phonon_voice` | A Phonon voice `.safetensors` file to speak with, used with the bare `phonon` voice. |
| `output` / `o` | Default WAV path for CLI-style tools. Default: `out.wav`. |
| `engine` / `vocoder_engine` | Accepted but ignored. The engine comes from the `voice` prefix. |

Notes:
- The shared root aliases and ORT keys are also accepted.
- Unknown TTS keys are passed on to the G2P parser, so the G2P keys below also work in TTS options.
- Creating a synthesizer from memory uses file map keys (e.g. `kokoro/prosody.model.ort`, `zipvoice/clone_audio`, `phonon/voice`, `clone_asr/...`) instead of option names. See `moonshine_create_tts_synthesizer_from_memory` in the [C API](../c-api/SKILL.md).

## Grapheme to Phonemes

### Roots and runtime

| Key | Description |
| --- | --- |
| `g2p_root` / `path_root` / `model_root` | Asset root (see Shared options). |
| `use_cuda` | Enables CUDA for G2P ORT sessions. |
| `oov_onnx_override` | Overrides the English OOV model path or bytes. |
| `oov_onnx_config` | Overrides the UTF-8 text of the English OOV `onnx-config.json`. |
| `allow_builtin_g2p_data` | Deprecated and ignored. |

`ort_providers`, `coreml_cache_dir`, `log_profiling` and `log_api_calls` are also accepted.

### Lexicon and model path overrides

| Key | Overrides |
| --- | --- |
| `english_dict_path` | `en_us/dict_filtered_heteronyms.tsv` |
| `german_dict_path` | `de/dict.tsv` |
| `french_dict_path` | `fr/dict.tsv` |
| `french_csv_dir` | `fr` (POS CSV directory) |
| `dutch_dict_path` | `nl/dict.tsv` |
| `italian_dict_path` | `it/dict.tsv` |
| `russian_dict_path` | `ru/dict.tsv` |
| `chinese_dict_path` | `zh_hans/dict.tsv` |
| `chinese_onnx_model_dir` | Chinese RoBERTa UPOS bundle directory |
| `korean_dict_path` | `ko/dict.tsv` |
| `vietnamese_dict_path` | `vi/dict.tsv` |
| `japanese_dict_path` | `ja/dict.tsv` |
| `japanese_onnx_model_dir` | Japanese tok-POS bundle directory |
| `arabic_dict_path` | `ar_msa/dict.tsv` |
| `arabic_onnx_model_dir` | Arabic diacritizer bundle directory |
| `hindi_dict_path` | `hi/dict.tsv` |
| `portuguese_dict_path` | Portuguese lexicon |

### Language feature flags

These are bools. Defaults are generally `true` unless noted; the docs do not give a per-flag default.

| Language | Keys |
| --- | --- |
| Spanish | `spanish_with_stress`, `spanish_narrow_obstruents` |
| German | `german_with_stress`, `german_vocoder_stress` |
| French | `french_with_stress`, `french_liaison`, `french_liaison_optional`, `french_oov_rules`, `french_expand_cardinal_digits` |
| Dutch | `dutch_with_stress`, `dutch_vocoder_stress`, `dutch_expand_cardinal_digits` |
| Italian | `italian_with_stress`, `italian_vocoder_stress`, `italian_expand_cardinal_digits` |
| Russian | `russian_with_stress`, `russian_vocoder_stress` |
| Korean | `korean_expand_cardinal_digits` |
| Portuguese | `portuguese_with_stress`, `portuguese_vocoder_stress`, `portuguese_expand_cardinal_digits`, `portuguese_apply_pt_pt_final_esh`; `portuguese_keep_syllable_dots` defaults to **false** |
| Turkish | `turkish_with_stress`, `turkish_expand_cardinal_digits` |
| Ukrainian | `ukrainian_with_stress`, `ukrainian_expand_cardinal_digits` |
| Hindi | `hindi_with_stress`, `hindi_expand_cardinal_digits` |

TTS-only keys, such as `voice` and the Piper/Kokoro paths, are ignored when listing G2P dependencies.

## Embeddings

- `moonshine_create_embedding_model()` takes `model_variant` as its own argument, not in an options map. The values are `q4` (the default) and `q8`. `"fp32"`, `"fp16"` and `"q4f16"` are no longer supported.
- Create-from-memory accepts an options array but currently ignores it.
- `moonshine_get_embedding_dependencies()` accepts:

| Key | Description |
| --- | --- |
| `variant` (alias `model_variant`) | Which quantized or float file to include in the download manifest. |

## Speech clip extract

| Key | Default | Description |
| --- | --- | --- |
| `clip_duration_seconds` | `4` | Length of the window to extract. |
| `minimum_speech_seconds` | `2` | Minimum seconds of speech in the window for `is_complete`. |
| `vad_threshold` | `0.5` | Speech probability threshold. |
| `tail_pad_seconds` | `0` | Extra audio kept after the VAD window. |

`log_api_calls` is also accepted.

## Download manifests

For how-to steps, see [model downloads](../../model-downloads/SKILL.md).

### Speech to Text: `moonshine_get_stt_dependencies()`

You can pass the same option list you use to load the model. Only these keys change which files are listed:

| Key | Description |
| --- | --- |
| `model_arch` | Decimal string of a `MOONSHINE_MODEL_ARCH_*` constant. When omitted, the language default is used. |
| `word_timestamps` | Includes the attention decoder in the download. |
| `include_spelling` / `spelling` | Includes the spelling-CNN group when one is published for the language. |
| `spelling_model_path` | A non-empty path has the same effect as including the spelling group. |

### TTS and G2P dependency and voice listing

Use the TTS and G2P keys above (`voice`, `g2p_root` and related) with `moonshine_get_tts_dependencies()`, `moonshine_get_tts_voices()` and `moonshine_get_g2p_dependencies()`. See the [C API](../c-api/SKILL.md).

## Pitfalls

- **Value types:** pass every value as a string in C (`"true"`, `"0.5"`). Bindings may convert bools and numbers for you.
- **Mobile builds:** setting `ort_providers` to anything other than CPU is an error on mobile.
- **Keyterms and context:** `keyterms` and `context` work only on streaming architectures. Setting `keyterm_boost` above 4.0 makes biasing stop working.
- **Word timestamps:** `word_timestamps` and `identify_speakers` need extra assets: the attention decoder and the diarization models. Include them in the download manifest, for example by passing `word_timestamps` to `moonshine_get_stt_dependencies()`.
- **Non-Latin languages:** for many non-Latin languages, raise `max_tokens_per_second` to about `13.0`, or the decoder may cut output short.
- **Phonon speed:** setting `phonon_duration_delta` replaces the speed mapping that `speed` provides.

## Source docs

Verbatim copies, for details not covered above:

- [api/options.md](references/api-options.md)
