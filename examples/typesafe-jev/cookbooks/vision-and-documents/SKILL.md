---
name: vision-and-documents
description: 'Cookbooks that use Jev on images: reading a scanned vaccination record with Noul, Box and Choice questions, checking OCR-extracted invoice values with Box and Score against a crop, and a bird feeder camera visit log with a Box per frame. Use when processing scans, photos, OCR output or video frames.'
---

# Vision and Documents Cookbooks

Three worked recipes that point Jev at images: reading a scanned record, checking OCR output against the page, and logging events from camera frames. All need **Jev 1.14** and the `TypeSafe-Danger-Zone-Images: true` header on every request with an image or Box question; images and Box are "dreamer-ready" (not yet production-ready, format may change). Runnable notebooks and `.py` files are in [typesafe-ai/typesafe-public-examples](https://github.com/typesafe-ai/typesafe-public-examples/tree/main/cookbooks). The verbatim pages are in `references/`. Background: [images](../../questions/images/SKILL.md), [box](../../questions/box/SKILL.md).

Recurring moves: put the image in the state (`{"page": Image(PAGE)}`, `{"frame": Image(...)}`) and refer to it by path in backticks; give closed answer sets an `unreadable` / `none` option; pair every Box with a Noul for presence; and do date/coverage logic in code or in a separate text-only request.

## Reading a scanned vaccination record (`reading_scanned_documents`)

Check a scanned travel vaccination record (no text layer) before a trip, with three requests:

1. **Find:** per known vaccine, a Noul ("Is X recorded in the vaccines table in `page`, with exactly this name?") and a Box ("the whole X row of the vaccines table in `page`"), plus one Noul for unlisted vaccines with the list in structured instructions.
2. **Read:** per found row, a Choice over possible years (with `unreadable`), and a Noul for whether the date is fully legible.
3. **Check:** a **text-only** request asks whether each dose still covers the trip date.

```python
def find_questions() -> dict:
    questions = {"unlisted": {
        "type": "noul",
        "instructions": {
            "question": "Does the vaccines table in `page` record any vaccine that is not "
                        "in this list?",
            "list": VACCINES,
        },
    }}
    for i, vaccine in enumerate(VACCINES):
        questions[f"vac_{i:02d}"] = {
            "type": "noul",
            "instructions": f"Is {vaccine} recorded in the vaccines table in `page`, with "
                            "exactly this name?",
        }
        questions[f"vac_{i:02d}|box"] = {
            "type": "box",
            "instructions": f"the whole {vaccine} row of the vaccines table in `page`",
        }
    return questions


def read_questions(row: dict) -> dict:
    where = f"the DATE GIVEN cell of the {row['vaccine']} row of the vaccines table in `page`"
    i = row["id"]
    return {
        f"{i}|year": {
            "type": "choice", "criteria": YEAR,
            "instructions": "Dates on this record are written day/month/year, so the year "
                            f"is the last part. What year is written in {where}?",
        },
        f"{i}|legible": {
            "type": "noul",
            "instructions": f"Is the date in {where} fully legible, with nothing covering, "
                            "staining, smudging or blurring any of it?",
        },
    }
```

Requests pass the image with `extra_headers=IMAGES_ON`. Result: two rows flagged for the nurse: rabies (date under a batch sticker: Jev answered `unreadable`, legibility 0.05) and typhoid (a clear 2021 date, but a typhoid dose protects about three years, so coverage scored 0.38 for a November 2026 trip). Flagged rows are cropped from their Box for review.

## OCR confidence and bounding boxes (`ocr_confidence_bounding_boxes`)

Check values an OCR + LLM extractor read from invoice photos (supplier, invoice number, date, amount due, bank details), so a reviewer looks only at doubtful ones. Each value is checked twice:

1. **Page check:** per field, a Box ("{field}, printed as “{value}” in `page`") and a Noul ("Is “{value}” {field} on `page`?"), all in one request.
2. **Zoom:** crop a region around each box, upscale it, and Box the field again in the crop for a tight box. Each field's crop goes into its own question's instructions via `client.attach_assets(...)`.
3. **Crop check:** a Noul per field on a crop of its box: "Does this cropped image clearly show {field} as “{value}”? ... Answer no if it is cut off, unreadable or different."

```python
def page_questions(values: dict) -> dict:
    questions = {}
    for field, value in sorted(values.items()):
        questions[f"box_{field}"] = Box(
            instructions=f"{FIELDS[field]}, printed as “{value}” in `page`"
        )
        questions[f"fits_{field}"] = Noul(
            instructions=f"Is “{value}” {FIELDS[field]} on `page`? {SAME_VALUE}"
        )
    return questions


def ask_with_images(task: str, questions: dict, images: dict, model: str) -> SystemOneResponse:
    """Put each field's image into its question, and send all the questions in one request."""
    for field, question in questions.items():
        question["instructions"] = question["instructions"].replace(IMAGE, str(images[field]))
    with client.attach_assets(list(images.values())):  # resolves the references in the text
        return client.system_one(state={"task": task}, questions=questions, model=model)
```

A value scoring **below 0.25 on either check** goes to review. All three extractor errors were caught:

| Invoice | Field | Extracted | Printed | Page check | Crop check |
| - | - | - | - | - | - |
| Milkwood | invoice number | `AN400074` | `IN400074` | 0.88 | 0.18 |
| Siyakhula | invoice number | `INV03070` | `INV03079` | 0.02 | 0.04 |
| Siyakhula | date | `16/09/2028` | `16/09/2026` | 0.17 | 0.66 |

Note the first row: the page check missed the one-letter error and only the crop caught it, which is why both checks run.

## Feeder-cam visit log (`feeder_watch`)

Send one frame per second of bird-feeder footage with five questions, then turn the answers into a visit log per species in plain code:

```python
QUESTIONS = {
    "bird_present": Noul(instructions="Is there at least one bird in `frame`?"),
    "how_many": Choice(
        instructions="How many birds are in `frame`?",
        criteria={
            "none": "No bird at all.",
            "one": "Exactly one bird.",
            "several": "Two or more birds.",
        },
    ),
    "bird": Box(instructions="The most prominent bird in `frame`"),
    "species_left": Choice(
        instructions="What species is the leftmost bird in `frame`?", criteria=SPECIES
    ),
    "species_right": Choice(
        instructions="What species is the rightmost bird in `frame`?", criteria=SPECIES
    ),
}
```

`SPECIES` maps ids (`blue_jay`, `cardinal_male`, `grackle`, ..., `other`) to visual descriptions written for what the camera actually sees (e.g. "on a close-up feeder camera it often fills the frame, so only the glossy dark head, pale eye and beak may be visible"). A Box returns one box, so when two species share the feeder a second request boxes each by name or position (`"The leftmost bird in `frame`"`). On a 101-second clip, Jev matched hand labels on bird presence in all 101 frames and named the correct species in 132 of 133 labeled sightings. The same approach applies to door and street cameras.

## Related

- Image limits, preparation (resize to ≤ 1568 px, rotate upright) and patterns such as tiling large images: [images](../../questions/images/SKILL.md).
- Reading values with regex candidates instead of images: [extraction](../extraction/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [cookbooks/reading_scanned_documents.md](references/cookbooks-reading_scanned_documents.md)
- [cookbooks/ocr_confidence_bounding_boxes.md](references/cookbooks-ocr_confidence_bounding_boxes.md)
- [cookbooks/feeder_watch.md](references/cookbooks-feeder_watch.md)
