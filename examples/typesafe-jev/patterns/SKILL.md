---
name: patterns
description: 'Architectural patterns for building with Jev: speculative fan-out (many questions, including speculative ones, in one request), screening with a Noul before an expensive step, a companion Noul that tells whether any Choice option fits, and composite scoring (atomic Scores combined with weights in code). Use when structuring requests for cost, latency and reliability, or when a single question isn''t enough.'
---

# Patterns

Architectural patterns for systems built on Jev. Every pattern splits a decision into small System One questions and leaves the decision to your code: Jev answers each question with a probability, and code decides what happens next. Assumes you know the [questions](../questions/SKILL.md) and [confidence](../confidence/SKILL.md) (which also covers routing by confidence and by probability).

| Pattern | What it does | Benefits |
| - | - | - |
| Speculative fan-out | Many questions, including speculative ones, in one request; code decides what's relevant | Cost, speed |
| Screen with a Noul first | One cheap yes/no first; the expensive step runs only on a clear yes | Cost, speed |
| Companion Noul | Pair a Choice with a Noul asking whether any option fits | Reliability |
| Composite scoring | Several atomic Scores combined with weights in code | Cost, reliability, speed |
| Routing by confidence / probability | See [confidence](../confidence/SKILL.md) | Reliability, safety |

By goal: **spend less** with fan-out and screening; **act safely** with routing and the companion Noul; **combine answers** with composite scoring.

## Speculative fan-out

Put every question your system might need in **one request**, then let code pick what's relevant. Questions run in parallel, so extra ones barely affect response time and save a round trip when they turn out to matter.

Support triage: ask `category` (Choice) plus `bug_severity` (Score) and `has_reproducible_steps` (Noul), which only matter for bug reports, `refund_requested` (Noul), which only matters for billing, and `frustration` (Score), which always matters. Then route:

```python
category = response.answers["category"]
bug_severity = response.answers["bug_severity"]
bug_repro = response.answers["has_reproducible_steps"]
refund = response.answers["refund_requested"]
frustration = response.answers["frustration"]

if category.choice == "bug_report":
    if bug_severity.score > 1.5 and bug_repro.noul > 0.6:
        escalate_to_engineering(ticket_id, severity="high")
    else:
        add_to_bug_backlog(ticket_id)

elif category.choice == "billing":
    if refund.noul > 0.7:
        route_to_billing_with_flag(ticket_id, refund_likely=True)
    else:
        route_to_billing(ticket_id)

elif category.choice == "feature_request":
    log_feature_request(ticket_id)

# Frustration is useful regardless of category
if frustration.score > 1.5:
    flag_for_priority_response(ticket_id)
```

## Screen with a Noul first

Ask one Noul with a small state (often just the input) and run the expensive step only on a clear yes. A clear no gets cheaper handling, and an unsettled answer gets its own rule, so every input is handled.

**When it's worth a second request.** Jev reads the state once per request, so if later questions would use the *same* state, use fan-out instead. Screen first when the next step costs something the first question doesn't:

- a **bigger state** (the customer record, full thread, or an attachment code must fetch),
- a **slower model** (an LLM call),
- a **person** (someone has to look).

Shared-inbox example. The screen asks whether the sender expects a reply; its `false` criterion lists messages with nothing to answer (newsletters, receipts, a note from a person that needs no reply).

| Message | `expects_reply` |
| - | - |
| Standing desk tracking hasn't updated; moving on the 30th | 0.98 |
| "Just so you know", a screw was missing but it's built now | 0.44 |
| "Thanks, the desk arrived yesterday and it's great." | 0.10 |
| "20% off every desk and chair until Sunday. Unsubscribe" | 0.02 |
| Payment receipt; replies not monitored | 0.02 |

```python
YES_ABOVE = 0.7
NO_BELOW = 0.3


def handle(message_id, screen_response):
    expects_reply = screen_response.answers["expects_reply"].noul

    if expects_reply < NO_BELOW:
        # Newsletters, receipts, notifications. Nothing to answer.
        file_away(message_id)

    elif expects_reply > YES_ABOVE:
        # A person is waiting. Fetch what triage needs and run the full request.
        customer = fetch_customer(message_id)
        triage(message_id, customer)

    else:
        # Something to look at, but maybe nothing to answer. One glance settles it.
        queue_for_quick_look(message_id)
```

Only the desk message gets full triage: a second request with the customer record in the state, asking `request` (Choice), `urgency` (Score) and `repeat_contact` (Noul reading `` `customer.previous_contacts` ``). That Noul was 0.99 with prior contacts on file and 0.05 without.

Variations:

- **Check a cheap step first:** run a cheap step, ask a Noul whether its output is right, send only failures to the expensive model (see the SDE cascade in [guardrails-and-verification](../cookbooks/guardrails-and-verification/SKILL.md)).
- **Several screens** in sequence ("written in English", then "about our product"), each removing inputs before a more expensive step.

## Companion Noul

A Choice **always picks an option**, even when none applies, sometimes with high probability. Add a Noul to the **same request** asking whether any option fits, and use the Choice only when the Noul is a clear yes.

Routing to three product teams (`desk_pro`, `chair_lite`, `monitor_arm`); both questions refer to the product list in the state as `` `products` ``, and the Noul's `false` criterion lists what counts as no (another product, a service, something you don't sell):

| Message | Choice | Top probability | Noul |
| - | - | - | - |
| Grinding noise from my standing desk's motor, the 140 cm one | `desk_pro` | 1.00 | 0.98 |
| Chair arrived but the monitor arm didn't | `monitor_arm` | 1.00 | 0.99 |
| My desk lamp stopped working after two weeks | `desk_pro` | 0.96 | 0.02 |
| A recruiter asking for a call | `desk_pro` | 0.81 | 0.02 |

The lamp message got `desk_pro` at 0.96 with confidence 0.94: nothing in the Choice answer reveals the mistake. Only the Noul does.

```python
YES = 0.7
NO = 0.3
PRODUCT_SURE = 0.7


def route(message_id, response):
    about_ours = response.answers["about_our_product"].noul
    product = response.answers["product"]
    product_probability = product.probabilities[product.choice]

    if about_ours < NO:
        # Nothing fits. The Choice's answer is noise; don't read it.
        send_to_general_inbox(message_id)

    elif about_ours > YES and product_probability > PRODUCT_SURE:
        # The Choice is answering a question that applies, and it clearly picked one product. Use it.
        send_to_product_team(message_id, product.choice)

    else:
        # Unsettled, or about our products but not clearly which one:
        # a person decides, with the Choice's top option as a hint.
        send_to_general_agent(message_id, suggested_product=product.choice)
```

**Why not an `other` option?** It competes with the real options for probability: an input partly about a product splits between `other` and that product, and neither number tells code what to do. In TypeSafe's tests the companion Noul usually works better.

Variations:

- **One Noul per option** when an input can match several (no extra "nothing fits" question needed: all come back low).
- **Box** has the same problem (always returns a location): pair it with "Is there a coffee mug in `photo`?".
- **Candidates from code:** build Choice options from values your code extracts, with a Noul asking whether the right one is among them (the value-extraction cookbook in [extraction](../cookbooks/extraction/SKILL.md) does this with a `none` option instead).

## Composite scoring

Break a complex judgment into independent dimensions, score each with its own Score question in one request, normalize, and combine with weights in code. Resume screening with four 5-level Scores (Python depth, team leadership, system design, generalist), so each is divided by 4:

```python
py      = response.answers["python_depth"].score / 4
lead    = response.answers["team_leadership"].score / 4
arch    = response.answers["system_design"].score / 4
general = response.answers["generalist"].score / 4

# Senior IC
ic_score = (0.40 * py) + (0.10 * lead) + (0.40 * arch) + (0.10 * general)

# Engineering Manager
em_score = (0.15 * py) + (0.40 * lead) + (0.20 * arch) + (0.25 * general)
```

The same answers rank candidates for two roles. The formula is visible, so when the top candidates don't match expectations, adjust the weights. Normalizing by each scale's top level (`len(criteria) - 1`) is shown in [score](../questions/score/SKILL.md).

## Source docs

Verbatim copies, for details not covered above:

- [patterns.md](references/patterns.md)
- [patterns/fan-out.md](references/patterns-fan-out.md)
- [patterns/noul-screen.md](references/patterns-noul-screen.md)
- [patterns/companion-noul.md](references/patterns-companion-noul.md)
- [patterns/composite-scoring.md](references/patterns-composite-scoring.md)
