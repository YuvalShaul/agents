# OIR response codes

Read this when the client exits non-zero. The registry's body always carries
a `code` field; that string, not the HTTP status, is what determines the
handling.

| HTTP | `code` | Meaning | Correct handling |
|---|---|---|---|
| 202 | — | Application opened | Record the `application_id`, attest now |
| 403 | `OATH_MISMATCH` | The oath text was wrong | The phrase is fixed and case-sensitive; the client sends it for you — don't hand-write the JSON |
| 409 | `SHELF_FULL` | The author already holds 3 seals | **Never retry.** Report it; the fix is a policy decision, not a code change |
| 409 | `WRONG_STATE` | The call doesn't apply in this state | Read `state`, resume the procedure at the matching step |
| 422 | `SPONSOR_INVALID` | Unknown seal, or a sponsor by the same author | Find a different sponsor with `verify`; do not drop the field |
| 422 | `TITLE_TOO_LONG` | Title over 64 characters | Report it. **Do not truncate the title** to get past the check |
| 425 | `TOO_EARLY` | Probation is not over | Wait `ticks_remaining` ticks, then retry `seal`. Not a failure |
| 451 | `EMBARGOED_YEAR` | Published before 1450 | **Never retry.** Terminal for that book |
| 404 | `UNKNOWN_APPLICATION` / `UNKNOWN_SEAL` | No such id or seal | Check for a typo; if the id was ours, the application lapsed |

## Retry policy

Only `TOO_EARLY` is retryable, and only after ticking. Everything else is a
decision for a human: retrying `SHELF_FULL` or `EMBARGOED_YEAR` in a loop is
treated by the registry as abuse and is the one thing that gets a project's
client blocked.

## Worked failure

```
$ oir_cli.py apply --title "Children of Dune" --author "Frank Herbert" \
      --year 1976 --sponsor OIR-HR-1965-M
HTTP 422
{ "code": "SPONSOR_INVALID" }
```

The sponsor seal exists and is valid — but `OIR-HR-1965-M` is *Dune*, by
Frank Herbert, and so is the applicant. A book cannot sponsor its own
author's work. Sponsor with a seal from another author instead
(`OIR-ST-1815-X`, *Emma*).
