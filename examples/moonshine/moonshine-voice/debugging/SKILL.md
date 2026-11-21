---
name: debugging
description: 'Covers troubleshooting Moonshine Voice: enabling console logs, saving the input audio the library receives, and logging API calls to reproduce problems. Use when transcription or synthesis behaves unexpectedly, produces no output or wrong output, when audio input looks wrong, or when a task asks how to turn on logging, save input audio or trace API calls.'
---

# Debugging Moonshine Voice

Use this skill to find out why Moonshine Voice is failing or giving poor results. There are three tools. Console logs explain errors. Input saving lets you check the audio the transcriber actually receives. API call logging shows the order and timing of calls into the library.

## Which tool to use

| Symptom | Start with |
|---|---|
| An exception, a failure, or no output | [Console logs](#console-logs) |
| No errors, but transcription quality is poor | [Input saving](#input-saving) (`save_input_wav_path`) |
| Errors that seem to depend on call order or timing | [API call logging](#api-call-logging) (`log_api_calls`) |

## Console logs

Check the console first. The core library logs a message at every failure point and exception, with details about what went wrong.

- The language bindings detect errors returned by the core library and raise an exception.
- The console log often has more detail than that exception. Read both.

## Input saving

Use this when nothing reports an error but transcripts are wrong or poor. It rules out bad input audio. Pass the `save_input_wav_path` option when you create a transcriber. All audio the transcriber receives is saved as `.wav` files in the folder you give.

Try it from the command line (the docs call this the Python example):

```bash
moonshine-voice transcribe --options='save_input_wav_path=.'
```

This runs test audio through a transcriber. The audio it received is written to `input_1.wav` in the current directory.

How the files behave:

- Each stream gets its own file: `input_1.wav`, `input_2.wav`, and so on.
- A file holds only the latest session. It is overwritten each time a new session starts. Copy the file before you start another session if you want to keep it.
- Listen to the file. Check that the audio is what you expect, and not distorted or corrupted.

## API call logging

Use this to see the timeline of your calls into the library. The `log_api_calls` option prints each underlying API call to the console as it happens. This helps you find ordering and timing problems.

```bash
moonshine-voice transcribe --options='log_api_calls=true'
```

## Passing these options in code

The docs only show these options with the `moonshine-voice transcribe --options=...` CLI. They are transcriber options, set when you create a transcriber. For how to pass options from each language binding, see [options reference](../reference/options/SKILL.md) and [transcription](../transcription/SKILL.md). The debugging docs do not say whether these options also apply to text-to-speech or voice agents.

## Pitfalls

- **Overwritten WAVs:** each new session replaces `input_N.wav`. Save a copy before you start the next session.
- **Exceptions with little detail:** the console log usually has the full reason. Don't rely only on the exception message from the binding.
- **Output folder:** `save_input_wav_path` takes a folder, not a file name. File names are generated as `input_N.wav`.

## Source docs

Verbatim copies, for details not covered above:

- [using/debugging.md](references/using-debugging.md)
