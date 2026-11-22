---
name: images
description: 'Sending images to Jev: turning images on, attaching PNG and JPEG assets to a request, referencing them from the `state`, from a question''s `instructions`, or from `criteria` (an image per option or level), uploading images over HTTP, and image placement. Covers the Python `Image` / assets helpers and the JavaScript `image()`, `withAssets` and `assets` helpers. Use when a request needs to evaluate photos, screenshots, scans or other images.'
---

# Images

Send images to Jev: in the `state`, inside one question's `instructions`, or in `criteria` (an option, level or yes/no definition shown by example). Every question type accepts images, and the [box](../box/SKILL.md) type finds where something is. Jev 1.13 and 1.14 both accept images; Box needs 1.14. Question basics are in [questions](../SKILL.md).

**Status: "dreamer-ready".** Not yet production-ready per TypeSafe: format, answers and limits can change between releases, and accuracy will change as models update. Use for prototypes.

## Turn images on

Images and Box are **off by default**. Send the header **`TypeSafe-Danger-Zone-Images: true`** with every request that contains an image or a Box question. Without it: `400`.

## SDKs (easiest)

Put an image object anywhere text can go; the SDK creates the reference and uploads the file.

```python
from pathlib import Path

from typesafe_sdk import Choice, Image, Noul, TypeSafeClient

with TypeSafeClient() as client:
    result = client.system_one(
        state={"door": Image(Path("door-camera.jpg"))},
        questions={
            "person_present": Noul(instructions="Is there a person in `door`?"),
            "carrying": Choice(
                instructions="What is the person in `door` carrying?",
                criteria={
                    "package": "A box or parcel.",
                    "bag": "A bag of groceries or shopping.",
                    "nothing": "Empty hands.",
                },
            ),
        },
        extra_headers={"TypeSafe-Danger-Zone-Images": "true"},
    )
    print(result.answers)
```

```typescript
import { openAsBlob } from "node:fs";
import { choice, image, noul, TypeSafeClient } from "@typesafe-ai/sdk";

const client = new TypeSafeClient();
const door = image(await openAsBlob("door-camera.jpg"));

const { answers } = await client.systemOne(
  {
    state: { door },
    questions: {
      person_present: noul("Is there a person in `door`?"),
      carrying: choice("What is the person in `door` carrying?", {
        package: "A box or parcel.",
        bag: "A bag of groceries or shopping.",
        nothing: "Empty hands.",
      }),
    },
  },
  { headers: { "TypeSafe-Danger-Zone-Images": "true" } },
);
console.log(answers);
```

Images inside a sentence and your own references: Python in [python-sdk](../../python-sdk/SKILL.md) (assets, automatic and named references), JavaScript in [javascript-sdk](../../javascript-sdk/SKILL.md) (`withAssets`, `assets`).

## Raw requests: `assets` and references

Each image is listed once in the top-level `assets` map, keyed by a **reference string**. Write the reference wherever the image belongs (as a whole value or mid-sentence) and the model receives the image there:

```json
{
  "model": "jev-latest",
  "state": {
    "photo": "a3f1c2e8-found"
  },
  "assets": {
    "a3f1c2e8-found": {"type": "image", "format": "jpg", "data_base64": "/9j/4AAQSkZJRg..."},
    "77b0d4a1-poster": {"type": "image", "format": "jpg", "data_base64": "/9j/4AAQSkZJRg..."}
  },
  "questions": {
    "same_dog": {
      "type": "noul",
      "instructions": "Is the dog in `photo` the same dog as in this picture: 77b0d4a1-poster?"
    },
    "has_collar": {
      "type": "noul",
      "instructions": "Is the dog in `photo` wearing a collar?"
    }
  }
}
```

Asset fields:

| Field | Notes |
| --- | --- |
| `type` | Optional; if sent, `"image"`. |
| `part` | Multipart: name of the file part holding the image. Wins if both `part` and `data_base64` are set. |
| `data_base64` | Base64 file (standard alphabet, `=` padding, no whitespace, no `data:` prefix). Required unless `part`. |
| `format` | `"png"`, `"jpg"` or `"jpeg"` (lowercase). Required with `data_base64`. |

Reference rules:

- References match as **plain text anywhere** in the request's strings: a short one like `cat` could match inside `category`. **Use a new UUID per image per request.**
- **Every asset must be referenced**, or `400`.
- A string that is exactly a reference becomes that image; in longer strings, replacement runs left to right without overlaps.
- **Each use adds the image again** (uploaded once, but every occurrence is another copy the model reads and counts toward limits).
- **Object keys are never replaced:** to define a Choice option by picture, put the reference in its description.
- Answers contain the reference, not the image (e.g. in a Score `legend`).
- Each reference ≤ 1,024 bytes; all references together ≤ 65,536 bytes; not empty or whitespace.

### Multipart (recommended over base64)

Base64 inflates each image by about a third, and that counts toward the 32 MiB body limit.

```bash
curl https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "TypeSafe-Danger-Zone-Images: true" \
  -F 'request={
    "model": "jev-latest",
    "state": {"door": "a3f1c2e8-door"},
    "assets": {"a3f1c2e8-door": {"type": "image", "part": "door-photo"}},
    "questions": {
      "person_present": {"type": "noul", "instructions": "Is there a person in `door`?"}
    }
  };type=application/json' \
  -F 'door-photo=@door-camera.jpg;type=image/jpeg'
```

- The first part is named `request` (reserved) and holds the JSON body.
- Part names are unique and non-empty. Image parts are `image/png`, `image/jpeg`, `image/jpg`, `application/octet-stream`, or untyped; anything else is `400`.
- Each file part belongs to exactly one asset (an unnamed part, a shared part, or a missing part is `400`). To reuse an image, write its reference in several places.

For base64 in JSON, `base64.b64encode(...)` in Python produces the right encoding; set `format`.

## Where to put an image

| Placement | Behavior |
| --- | --- |
| `state` | Part of the state; every question sees it. Can hold several images, labeled or nested, e.g. `{"frames": [{"seconds_ago": 2, "frame": "5c0e9a12-f1"}, ...]}`, referenced as `` `frames[2].frame` ``. |
| `instructions` | Sent only with that question, **once per question that includes it**. If several questions use the same image, put it in the state once and refer to it by path (fewer tokens, less of the limits). |
| `criteria` | Define options, levels or yes/no by example pictures. |

Choice options defined by pictures (option names are what your code receives; `description` / `examples` are names chosen for the example, not required fields):

```json
"gesture": {
  "type": "choice",
  "instructions": "Which gesture is the hand in `camera` making?",
  "criteria": {
    "thumbs_up": "0b6c51aa-thumb",
    "open_palm": {
      "description": "A hand held up with the palm facing the camera.",
      "examples": ["4fd2e7b9-palm1", "c83a0e15-palm2"]
    },
    "fist": "a7e94d02-fist",
    "none": "No hand, or a hand that matches none of the examples."
  }
}
```

Score levels can each have an example picture; Noul criteria can too: `{"true": {"description": "Correctly assembled", "examples": ["<reference>"]}, "false": "Parts missing or in the wrong place."}`.

## Image patterns

| Pattern | How | Where the image goes |
| - | - | - |
| Compare against a known picture | Same person/product/place as a reference? | Known picture in `instructions`, photo in `state` |
| Define options by example | One or a few example pictures per Choice option | `criteria` |
| What changed | Previous frame or short frame history; ask about motion or differences | `state` |
| Look closer when needed | Small copy first; larger copy or full-res crop only when needed | `state` |
| Search a large image | Tiles as Choice options; repeat on the chosen tile | `criteria` |
| Find where it is | A Box question | `state` (optionally a target picture in `instructions`) |

## Limits

| Limit | Value |
| - | - |
| Format | PNG or JPEG stills. Animated PNGs rejected. |
| File size | 16 MiB per image (after base64 decoding). |
| Width and height | 280 to 1568 px each. |
| Total pixels | 78,400 to 2,458,624. |
| Request body | 32 MiB including JSON, base64 and multipart framing. Compression doesn't raise it. |
| All images | 32 MiB after processing (re-encoding can make images larger than sent). |
| Expanded request | 32 MiB after every reference is replaced by its image. |

Images outside the limits are **rejected, never resized**. One rejected image fails the whole request (no partial answers). Images count against normal rate limits and context length.

## Prepare images before sending

- Scale the longest side to at most 1568 px (a 12 MP phone photo → 1568 × 1176); upscale or pad images under the minimum.
- **Rotate the pixels upright:** the API strips all metadata and does **not** apply EXIF orientation.
- Convert GIF, WebP, HEIC, animations and video frames to PNG/JPEG stills. Prefer 8-bit baseline JPEG (re-save progressive JPEGs).
- If a file that opens fine is rejected, re-export it.

```python
from PIL import Image, ImageOps

with Image.open("photo.jpg") as original:
    img = ImageOps.exif_transpose(original)  # rotate the pixels upright
    img.thumbnail((1568, 1568))  # longest side at most 1568, same aspect ratio
    # thumbnail only shrinks: upscale or pad an image under the minimum separately
    img.convert("RGB").save("photo-ready.jpg", "JPEG", quality=90)  # baseline JPEG
```

## Tokens and errors

Images are billed as input tokens at the normal price (included in `usage.input_tokens`); no separate image charge. TypeSafe has not yet published guidance for estimating image tokens.

| Status | Cause |
| - | - |
| `400` | Missing `TypeSafe-Danger-Zone-Images: true` header. |
| `400` | Image or asset rejected: not PNG/JPEG, damaged, animated, below minimum size, unreferenced asset, invalid base64 or `format`, empty reference, or a broken multipart rule. |
| `400` | `max_tokens_exceeded`: images plus text exceed the context length. Send fewer/smaller images or move images from `instructions` into the `state`. |
| `413` | Over a size limit (file, dimensions, pixels, body, all images, expanded request, reference lengths). |

With several problems, the error reports only one.

## Source docs

Verbatim copies, for details not covered above:

- [images.md](references/images.md)
