---
name: box
description: 'The Box question type (Jev 1.14+): locating something in an image, returning `box` with `top`, `bottom`, `left` and `right` edges as fractions of the image''s height and width, plus confidence. Covers asking for a location, converting to pixels, cropping, and pairing a Box with a Noul that checks the target is present. Use when finding where an object, field or value is in a photo or scan, and when using `Box(...)` in Python or `box(...)` in JavaScript.'
---

# Box

Ask Jev where something is in an image (the mug on the counter, the signature on a scanned form, the person at the door) and get a bounding box: the smallest rectangle around the target, as four edges. Box questions need **Jev 1.14** and an image in the request. How to send images is in [images](../images/SKILL.md); general question rules in [questions](../SKILL.md).

**Status: "dreamer-ready".** TypeSafe says images and Box are not yet production-ready: good for prototypes, but the request format, answers and limits can change between releases, and accuracy will change as models update.

**Required header:** send `TypeSafe-Danger-Zone-Images: true` with every request that contains an image or a Box question.

## Request

- `type`: always `"box"`.
- `instructions`: what to find, and in which image. A phrase is enough: "the coffee mug in `photo`".
- No `criteria`.

A kitchen photo sent as a multipart file part:

```bash
curl https://api.typesafe.ai/v1/systemone \
  -H "Authorization: Bearer $TYPESAFE_API_KEY" \
  -H "TypeSafe-Danger-Zone-Images: true" \
  -F 'request={
    "model": "jev-latest",
    "state": {"photo": "6e1d0b7c-kitchen"},
    "assets": {"6e1d0b7c-kitchen": {"type": "image", "part": "kitchen-photo"}},
    "questions": {
      "mug": {"type": "box", "instructions": "the coffee mug in `photo`"}
    }
  };type=application/json' \
  -F 'kitchen-photo=@kitchen.jpg;type=image/jpeg'
```

Base64 in a JSON body and the SDK helpers (`box()` in JavaScript, `Box` in Python) are in [images](../images/SKILL.md). Box questions mix freely with Choice, Score and Noul in one request.

## Response

```json
{
  "model": "jev-1.14.0",
  "answers": {
    "mug": {
      "type": "box",
      "box": {"top": 0.25, "bottom": 0.82, "left": 0.44, "right": 0.84},
      "confidence": 0.92
    }
  },
  "usage": {"input_tokens": 290, "output_tokens": 21}
}
```

- `box`: edges from the top-left corner, each 0 to 1. `left` / `right` are fractions of the width, `top` / `bottom` of the height; `left < right`, `top < bottom`. The same answer works at any image size.
- `confidence`: 0 to 1, higher = more sure.

## Convert to pixels and crop

```python
from PIL import Image

image = Image.open("kitchen.jpg")
width, height = image.size
mug = response["answers"]["mug"]
edges = mug["box"]

box = (
    round(edges["left"] * width),
    round(edges["top"] * height),
    round(edges["right"] * width),
    round(edges["bottom"] * height),
)
image.crop(box).save("mug.jpg")
```

## Using confidence

There is **no recommended threshold yet**: tune one on your own images. Below it you can:

- **Ask again on a better image:** a larger version, or a higher-resolution crop around the box.
- **Pad the box** before cropping, so the crop doesn't cut off the target:

```python
PAD = 0.05  # Fraction of the image to add on each side. Tune for your images.
MIN_CONFIDENCE = 0.6  # Example threshold. Tune it on your own images.

if mug["confidence"] < MIN_CONFIDENCE:
    edges = {
        "left": max(0.0, edges["left"] - PAD),
        "top": max(0.0, edges["top"] - PAD),
        "right": min(1.0, edges["right"] + PAD),
        "bottom": min(1.0, edges["bottom"] + PAD),
    }
```

## Writing Box questions

- **Name the target and the image.** With several images, the backtick path (`` `photo` ``) says which one to search.
- **The target can be a picture:** put the image reference in the instructions, e.g. `"the person in `photo` who matches this badge photo: 9a21c7d3-badge"`.
- **A Box always returns a box.** There is no "not found". Ask a Noul in the same request and ignore the box when it is low:

  ```json
  "questions": {
    "mug_visible": {"type": "noul", "instructions": "Is there a coffee mug in `photo`?"},
    "mug": {"type": "box", "instructions": "the coffee mug in `photo`"}
  }
  ```

- **One target per question.** Ask one Box per thing. If the image may hold several of the same thing, describe the one you want ("the mug nearest the sink in `photo`"). If you can't, add a Choice with options `none`, `one`, `several`; on `several`, split the image into regions and ask again on each.
- **Crop large images first.** A target a few dozen pixels wide in a very large image can be missed. Find the region first (e.g. a Choice whose options are tiles of the image), Box within that tile, then convert the edges back to fractions of the full image.

Worked examples (scanned records, OCR checks, camera frames) are in [vision-and-documents](../../cookbooks/vision-and-documents/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [primitives/box.md](references/primitives-box.md)
