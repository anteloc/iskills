---
name: voice-agent
description: 'Covers building conversational voice agents with Moonshine: simple and multi-step flows, asking questions, confirmations, spelled input, error handling, speaking a reply while it is being written, and agent setup that ties transcription to text-to-speech. Use when a task asks for a voice assistant, voice-driven form, phone-style dialog, or spoken question and answer, or mentions AgentFlow, Dialog, confirmations, spelled input or streaming a reply to speech.'
---

# Voice Agent

Build conversational voice agents with `AgentFlow`. You write each conversation as a Python generator function that takes a `Dialog`. The runner handles speech recognition, the microphone, semantic intent matching and text-to-speech. This skill covers simple and multi-step flows, questions, confirmations, spelled input, error handling, streaming a language-model reply to speech, and starting the agent.

For installation and the basic transcription pattern, see [moonshine-voice](../SKILL.md).

## Quick start

Try the built-in example first:

```bash
python -m moonshine_voice.agent_flow
```

A minimal agent has three parts: flow functions, `listen_for()` registrations, and `start_listening()`:

```python
    def report_ip_address(d: Dialog):
        ip = _find_local_ip()
        if ip is None:
            yield d.say("Sorry, I couldn't find a local IP address.")
            return
        speech_ip = re.sub(r"(\d)", r"\1 ", ip.replace(".", " dot "))
        yield d.say([
            f"Okay. Your local IP address is {speech_ip}. ",
            f"To repeat, that's {speech_ip}."
        ])

    agent_flow = (
        AgentFlow()
        .language("en")
        .listen_for("What is my IP address?", report_ip_address)
    )

    agent_flow.start_listening()
```

The docs do not show the import lines for `AgentFlow`, `Dialog` or `SPELLED`. Check the `moonshine_voice` package, or see [reference/classes](../reference/classes/SKILL.md).

## Core concepts

| Concept | What it is |
|---|---|
| `AgentFlow` | The runner. It opens the STT model, the microphone and the synthesizer, and routes speech to flows. |
| Flow function | A generator `def f(d: Dialog)` that `yield`s each dialog step. |
| `Dialog` | The current conversational exchange. Use it to `say`, `ask`, `confirm` and `say_stream`. |
| `listen_for(phrase, fn)` | Registers a top-level conversation starter. Matching is **semantic**. |
| `yield` | Hands control back while the agent speaks or waits for the user, so nothing blocks. |

### The `yield` rule

Put `yield` in front of every `Dialog` call. When the call waits for user input, `yield` also returns the result:

```python
input_ssid = yield d.ask("What's the name of your Wi-Fi network?...")
```

Without `yield`, the step never runs.

## Dialog methods

| Call | Returns (via `yield`) | Notes |
|---|---|---|
| `d.say(text)` | — | `text` can be a string or a list of strings. |
| `d.ask(question)` | `str`: what the user said | Waits for the user's reply. |
| `d.ask(question, mode=SPELLED)` | `str`: the spelled characters | Character-by-character input. See below. |
| `d.confirm(question)` | truthy/falsy | Semantic yes or no. |
| `d.say_stream(iterable)` | — | Speaks the text fragments as they arrive. |

## Semantic matching

`listen_for("What is my IP address?", fn)` also fires on phrasings like "Tell me your IP address" or "Can you tell me the local IP address?". You can register as many starters as you want. The runner routes each utterance to the closest one in meaning.

`confirm()` is semantic too: "okay", "affirmative" and "go ahead" count as "yes".

## Multi-step flows

Write branching conversations as normal Python. Loops, `if`/`elif`, early `return` and `try`/`except` all work inside a flow:

```python
    def connect_to_wifi(d: Dialog):
        input_ssid = yield d.ask("What's the name of your Wi-Fi network? Say list if you want to pick from a list or spell if you want to spell out the start of the name")
        input_ssid = input_ssid.strip()

        networks = _scan_wifi_networks()

        if input_ssid.lower().strip(string.punctuation) == "list":
            yield d.say("Say yes to the network you want to connect to.")
            for network in networks:
                if (yield d.confirm(f"{network}?")):
                    input_ssid = network
                    break
        elif input_ssid.lower().strip(string.punctuation) == "spell":
            input_ssid = yield d.ask("Spell out the start of the network name.", mode=SPELLED)

        found_ssid = fuzzy_match_network(input_ssid, networks)
        if found_ssid is None:
            yield d.say(f"Sorry, I couldn't find a matching network for {input_ssid}.")
            return

        password = yield d.ask(
            f"Please spell the Wi-Fi password for {found_ssid} one character at a time, and say done when finished.",
            mode=SPELLED,
        )

        yield d.say(f"Connecting to {found_ssid}.")

        try:
            result = subprocess.run(
                ["sudo", "nmcli", "device", "wifi",
                    "connect", found_ssid, "password", password],
                capture_output=True, text=True, timeout=30,
            )
        except FileNotFoundError:
            yield d.say("Sorry, network manager was not found on this system.")
            return
        except subprocess.TimeoutExpired:
            yield d.say("Sorry, the connection attempt timed out.")
            return

        if result.returncode == 0:
            yield d.say(f"Connected to {found_ssid}.")
        else:
            yield d.say(
                f"Sorry, I wasn't able to connect to {found_ssid}. "
                "Please check the network name and password and try again."
            )

    agent_flow.listen_for("Connect to Wi-Fi", connect_to_wifi)
```

Patterns in this example:

- **Keyword branches:** normalize the `ask()` result with `.lower().strip(string.punctuation)` before you compare it.
- **Pick from a list:** loop over the options with `yield d.confirm(...)` and `break` on the first yes.
- **Error recovery:** catch exceptions, then `yield d.say(...)` an apology and `return`.

## Spelled input

Use `mode=SPELLED` for passwords, codes and names that ordinary transcription cannot capture:

```python
        password = yield d.ask(
            f"Please spell the Wi-Fi password for {found_ssid} one character at a time, and say done when finished.",
            mode=SPELLED,
        )
```

- A fine-tuned model recognizes each character.
- It accepts letter names ("aitch", "capital zee"), the NATO alphabet ("alpha", "bravo") and phrases like "E as in elephant".
- It repeats back what it heard and lets the user delete mistakes.
- In your prompt, tell the user to say "done" when finished, as the example does.

## Speaking a reply while it is written

Use `say_stream()` to speak a language-model reply as it is generated. Playback starts as soon as the first sentence is complete. With Kokoro, it starts before that sentence has finished decoding.

**Inside a flow**, yield an iterable of text fragments:

```python
    def answer_question(d):
        question = yield d.ask("What would you like to know?")
        yield d.say_stream(llm.stream(question))
```

The flow resumes after the last fragment has been spoken, just as after `d.say()`.

**Outside a flow**, use the runner's context manager and push the fragments:

```python
    with flow.say_stream() as push:
        for token in llm.stream(question):
            push(token)
```

The block does not exit until playback has finished.

How it behaves:

- The microphone stays muted and self-capture stays suppressed for the whole passage, as with `say()`.
- If the text source raises partway through, the agent speaks what it already received and reports the error to `on_error()`. The flow keeps running. The docs do not give the signature of `on_error()`.

## Agent setup

Every configuration method returns the runner, so you can chain them. Each one has a working default:

```python
    agent_flow = (
        AgentFlow()
        .language("en")
        .listen_for("What is my IP address?", report_ip_address)
        .listen_for("Connect to Wi-Fi", connect_to_wifi)
    )

    agent_flow.start_listening()
```

| Method | Purpose |
|---|---|
| `.language(code)` | Sets the language. It selects the STT model, e.g. `"en"`. |
| `.listen_for(phrase, fn)` | Registers a conversation starter. |
| `.always(phrase, ...)` | Registers your own phrase that stays live at all times, whether or not a flow is running. The docs do not give its exact arguments. |
| `.load()` | Opens and downloads models now instead of on the first `start_listening()` call. |
| `.on_progress(callback)` | Reports download progress during loading. |
| `.on_error(...)` | Receives errors, such as a stream source that fails. |
| `.start_listening()` | Loads anything still missing, then returns once the microphone is live. |
| `.close()` | Releases everything the runner opened. |

Lifecycle:

1. On first use, `start_listening()` downloads the embedding model used for matching, the speech-to-text model for your language and a synthesizer. For control over downloads, see [model-downloads](../model-downloads/SKILL.md).
2. `start_listening()` returns right away. Speech arrives on the audio thread and drives the flows from there, so your main thread is free to sleep, run a UI or do other work.
3. Call `close()` when you are done.

### Built-in phrases

- **"Cancel"** and **"start over"** work at any point inside a flow without registration.
- Outside a flow they count as ordinary speech, so a dictation interface keeps them.

## Pitfalls

- **Missing `yield`:** each `d.say/ask/confirm/say_stream` call must be yielded, or it does nothing.
- **Unnormalized answers:** `ask()` returns raw transcribed text, which can have punctuation and capital letters. Strip and lowercase it before you compare.
- **Text that reads well but sounds wrong:** rewrite it for speech before calling `say()`. For example, "192.178.4.72" becomes "1 9 2 dot 1 7 8 dot 4 dot 7 2". The sample does this with `re.sub(r"(\d)", r"\1 ", ip.replace(".", " dot "))`.
- **Main thread exits:** `start_listening()` does not block. Keep your program alive, for example with a sleep loop or a UI loop.
- **Slow first start:** the models download on the first run. Call `load()` with `on_progress()` at startup to show progress.

## Related

- Full sample app: https://github.com/moonshine-ai/pi-help-bot
- Choosing voices and the synthesizer: [text-to-speech](../text-to-speech/SKILL.md)
- Recognition models and languages: [model-selection](../model-selection/SKILL.md)
- Improving recognition of domain terms: [domain-customization](../domain-customization/SKILL.md)
- `AgentFlow` and `Dialog` class details: [reference/classes](../reference/classes/SKILL.md)

## Source docs

Verbatim copies, for details not covered above:

- [using/conversational-agent.md](references/using-conversational-agent.md)
