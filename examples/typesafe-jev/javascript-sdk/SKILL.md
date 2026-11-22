---
name: javascript-sdk
description: 'Using the TypeSafe JavaScript/TypeScript SDK (`@typesafe-ai/sdk`): `new TypeSafeClient()`, `client.systemOne({ state, questions })`, the `choice()`, `score()`, `noul()`, `box()` and `image()` helpers, `withAssets` and `assets` for images, type inference of answers from questions, request compression, and the changelog. Use when writing or debugging Node.js, browser or TypeScript code that calls Jev.'
---

# JavaScript / TypeScript SDK

Call Jev from Node.js, the browser or TypeScript with `@typesafe-ai/sdk`: `new TypeSafeClient()`, `client.systemOne({ state, questions })`, the `choice` / `score` / `noul` / `box` helpers, images, compression, retries and errors. Answer types are inferred from your questions. What to ask is covered in [questions](../questions/SKILL.md); every export is in [javascript-api](../reference/javascript-api/SKILL.md). Source: [github.com/typesafe-ai/typesafe-sdk-js](https://github.com/typesafe-ai/typesafe-sdk-js).

## Install

```sh
npm install @typesafe-ai/sdk
```

Node.js **22 or newer** (since v0.7.0). The package ships ESM, CommonJS and TypeScript declarations. Set `TYPESAFE_API_KEY`.

## First request

```ts
import { choice, TypeSafeClient } from "@typesafe-ai/sdk";

const client = new TypeSafeClient();
const response = await client.systemOne({
  state: { ticket: "I was charged twice. Please fix this ASAP." },
  questions: {
    category: choice("What is this ticket about?", {
      billing: null,
      technical: null,
      other: null,
    }),
  },
});

console.log(response.answers.category.choice);
```

Question helpers (instructions can be a string, JSON object/array, an image, or `withAssets` text):

| Helper | Shape |
| --- | --- |
| `choice(instructions, { label: description \| null, ... })` | Answer: `.choice` (typed as the union of your labels), `.probabilities`, `.confidence` |
| `score(instructions, [level0, level1, ...])` | At least two levels; lists built at runtime (e.g. `string[]`) are accepted and validated at call time. Answer: `.score`, `.legend`, `.probabilities`, `.confidence` |
| `noul(instructions, { true?, false? })` | Answer: `.noul` |
| `box(instructions)` | Answer: `.box` (`top`, `bottom`, `left`, `right`), `.confidence` (`null` if not reported) |

The result is `{ answers, model, usage }`. In TypeScript, `answers.category.choice` has type `"billing" | "technical" | "other"`. Plain question objects (`{ type: "noul", instructions: "..." }`) also work.

`systemOne()` **never throws synchronously**: invalid requests (null state, empty questions, fewer than two score levels, empty choice map, a Noul with neither instructions nor criteria, an unknown asset reference, an unused name in `assets`, an unreadable `Blob`) reject the returned promise.

## Client configuration

```ts
const client = new TypeSafeClient({
  apiKey: process.env.TYPESAFE_API_KEY,   // default: TYPESAFE_API_KEY
  baseURL: "https://api.typesafe.ai",     // default: TYPESAFE_BASE_URL, then this
  defaultModel: "jev-latest",             // default: TYPESAFE_DEFAULT_MODEL, then jev-latest
  timeout: 10000,                         // ms per attempt (no total retry budget)
  retry: { maxRetries: 2 },               // partial RetryPolicy overrides
  defaultHeaders: {},                     // per-call headers take precedence
  compression: "zstd",                    // or false
  logLevel: "warn",                       // TYPESAFE_LOG_LEVEL; debug|info|warn|error|off
});
```

Explicit options beat environment variables, which beat SDK defaults (empty env values are ignored). The constructor throws if the API key is missing, the config is invalid, or the runtime is unsupported. Browser use requires `dangerouslyAllowBrowser: true` and **exposes the API key to page users**. Other options: `fetch` (custom transport), `logger` (console-compatible).

Per call, the second argument overrides `headers`, `retry`, `timeout`, and adds an `AbortSignal`:

```ts
await client.systemOne(request, { timeout: 2000, signal: controller.signal });
```

Override the model per request with `model` in the request object. List models with `await client.models.list()` (array of `{ name, description, release_date }`).

## Retries and errors

Default retry policy: `maxRetries` 2; retries HTTP 408, 429 and 500–599, connection failures and timeouts; exponential backoff from 500 ms to 5000 ms with 0.25 jitter; honors `Retry-After` / `retry-after-ms` up to 60 s.

Errors (all extend `TypeSafeError`):

| Class | When |
| --- | --- |
| `APIError` (`.status`, `.body`, `.headers`, `.requestId`) | Non-2xx response after retries. Subclasses: `BadRequestError` 400, `AuthenticationError` 401, `PermissionDeniedError` 403, `NotFoundError` 404, `UnprocessableEntityError` 422, `RateLimitError` 429, `InternalServerError` 5xx |
| `APIConnectionError` | DNS, TLS, closed connection, interrupted body |
| `APITimeoutError` | No full response within the timeout (a kind of `APIConnectionError`) |
| `APIUserAbortError` | Cancelled through an `AbortSignal` |

```ts
import { APIError } from "@typesafe-ai/sdk";

try {
  await client.systemOne(request);
} catch (error) {
  if (error instanceof APIError) console.log(error.status, error.requestId);
}
```

`systemOne()` returns an `APIPromise`: `await p.withResponse()` gives `{ data, response, requestId }`; `p.asResponse()` gives the raw `Response`; `p.map(fn)` transforms the parsed result.

## Images

Experimental ("dreamer-ready"). Opt in with the header, on the client or per call:

```ts
const client = new TypeSafeClient({
  defaultHeaders: { "TypeSafe-Danger-Zone-Images": "true" },
});
```

Create images with `image(bytes | Blob | File)` or `Image.fromBase64(text)`. Only PNG and JPEG: the API detects the format from the bytes and rejects others (WebP, GIF) with `BadRequestError`. Requests with images are sent as `multipart/form-data`, each image once however often it's used. Three ways to use an image, combinable:

**1. Place it in the content** (state, instructions or criteria):

```ts
import { openAsBlob } from "node:fs";
import { image, noul, score, TypeSafeClient } from "@typesafe-ai/sdk";

const client = new TypeSafeClient();
const photo = image(await openAsBlob("returns/RMA-1042.jpg"));

const { answers } = await client.systemOne({
  state: { claim: "The mug arrived with a chipped rim.", photo },
  questions: {
    damaged: noul("Is the product in the photo damaged?"),
    severity: score("How severe is the damage?", ["none", "cosmetic", "unusable"]),
  },
});
console.log(answers.damaged.noul, answers.severity.score);
```

**2. Write it into text with the `withAssets` tag:**

```ts
const { answers } = await client.systemOne({
  state: withAssets`A seller uploaded ${upload} for a listing whose catalog photo is ${catalog}.`,
  questions: {
    sameProduct: noul(withAssets`Does ${upload} show the same product as ${catalog}?`),
    quality: choice(withAssets`Is ${upload} usable as a listing photo?`, {
      usable: null,
      blurry: null,
      cropped: null,
      notAProduct: null,
    }),
  },
});
```

An image in an **untagged** template literal (`` `Compare ${upload}` ``) rejects the call with `TypeSafeError` before sending. Join lists with `withAssets.join(uploads, ", ")`.

**3. Choose your own references with `assets`** (e.g. prompts stored in config):

```ts
import { readFile } from "node:fs/promises";
import { image, noul, TypeSafeClient } from "@typesafe-ai/sdk";

const client = new TypeSafeClient();

const { answers } = await client.systemOne({
  state: "A customer returned <delivered>. The catalog photo is <catalog>.",
  questions: { matches: noul("Is <delivered> the product shown in <catalog>?") },
  assets: {
    "<delivered>": image(await readFile("returns/RMA-1042.jpg")),
    "<catalog>": image(await readFile("catalog/mug.png")),
  },
});
console.log(answers.matches.noul);
```

Use distinct delimiters like `<delivered>`. Every name in `assets` must appear in the request, or the call rejects before sending.

**Locate something with `box`:**

```ts
import { openAsBlob } from "node:fs";
import { box, image, TypeSafeClient } from "@typesafe-ai/sdk";

const client = new TypeSafeClient();

const { answers } = await client.systemOne({
  state: image(await openAsBlob("returns/RMA-1042.jpg")),
  questions: { damage: box("The damaged area of the product") },
  model: "jev-preview",
});
const { top, bottom, left, right } = answers.damage.box;
```

The SDK docs say to use `jev-preview` for Box; the Models page says Box needs Jev 1.14, which `jev-latest` and `jev-preview` both point to today. Image rules and limits are in [images](../questions/images/SKILL.md).

## Compression

Bodies of 1 KiB or more are zstd-compressed (Node.js 22.15+; other runtimes send uncompressed). Pass `compression: false` for APIs that don't accept compressed requests.

## Changelog highlights

- **v0.7.0 (2026-10-14):** requires Node.js 22+; stops exporting request payload types; experimental images (`image()`, `Image.fromBase64()`, `withAssets`, `withAssets.join`, `assets`); `box` questions; zstd compression. Fixes: null token counts allowed in `usage`, invalid requests reject instead of throwing, runtime-built score criteria accepted, no unhandled rejection on Node 22 timeouts/aborts mid-body.
- **v0.6.0:** `score` criteria are an ordered sequence, not a dict keyed by integers (breaking).
- **v0.5.7:** initial public release.

## Source docs

Verbatim copies, for details not covered above:

- [sdk/javascript.md](references/sdk-javascript.md)
- [sdk/javascript/changelog.md](references/sdk-javascript-changelog.md)
