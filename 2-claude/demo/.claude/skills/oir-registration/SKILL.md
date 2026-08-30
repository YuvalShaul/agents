---
name: oir-registration
description: Register a book with the Ondura Interlibrary Registry (OIR) — the sponsor rule, the oath, the probation period, and the seal request. Use when asked to register, seal, submit, or enroll a book with Ondura or the registry, or when an OIR application is stuck.
argument-hint: [book title]
allowed-tools: Bash(python3 ${CLAUDE_SKILL_DIR}/scripts/oir_cli.py *)
---

# Registering a book with Ondura

A book is not "added" to the registry. It **applies**, and the application
passes through four states. Skipping a step doesn't fail loudly — it lapses.

Client: `python3 ${CLAUDE_SKILL_DIR}/scripts/oir_cli.py <command>`.
It talks to `$OIR_URL` (default `http://127.0.0.1:8787`). The registry must
be running: `python3 ${CLAUDE_SKILL_DIR}/scripts/oir_mock.py`.

## The state machine

```
pending ──attest (within 2 ticks)──> provisional ──3 ticks──> sealed
   │                                      │
   └── 3rd tick without attest ──> lapsed (terminal — reapply from scratch)
```

## Procedure

1. **Check the registry is up:** `oir_cli.py health`. If it's unreachable,
   say so and stop — do not invent a seal.

2. **Find a sponsor.** Every application needs the seal of an *already
   sealed book by a different author*. `oir_cli.py verify <seal>` confirms
   one exists and shows its author. Never sponsor a book with another book by
   the same author — that is `SPONSOR_INVALID`, and it is a rule about the
   author, not about the book.

3. **Apply:**

   ```
   oir_cli.py apply --title "<title>" --author "<author>" --year <year> --sponsor <seal>
   ```

   Record the `application_id` (`APP-0001`). On a non-2xx, read the `code`
   field and follow [reference.md](reference.md) — several of these codes
   must **not** be retried.

4. **Attest immediately.** `oir_cli.py attest <application_id>` swears the
   oath and moves the application to `provisional`. Do this in the same turn
   as the application: the oath is only accepted while the state is
   `pending`, and `pending` expires after 2 ticks. A lapsed application
   cannot be revived.

5. **Wait out probation.** The application must sit in `provisional` for 3
   ticks. In this sandbox time only moves when you move it:
   `oir_cli.py tick` three times. Requesting the seal early returns `425
   TOO_EARLY` with `ticks_remaining` — that is not an error to work around,
   it is the countdown.

6. **Request the seal:** `oir_cli.py seal <application_id>` returns the
   permanent seal code. Report the seal, and only then describe the book as
   registered.

## Rules that are easy to get wrong

- The seal code is **issued by the registry**. Never compute one yourself and
  never write one into project code that the registry hasn't returned. To
  validate a code's shape, use [oir-codes](../oir-codes/SKILL.md).
- An author may hold at most **3** seals. The 4th application returns `409
  SHELF_FULL` at apply time, not at seal time.
- Books published before **1450** are permanently ineligible (`451
  EMBARGOED_YEAR`). There is no appeal path; report it and stop.
- `oir_cli.py tick` advances the clock for **every** open application, not
  just yours. Don't tick to hurry one application if others are pending
  their oath — you will lapse them.
