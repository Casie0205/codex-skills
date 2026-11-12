# Study Result Schema

## Contents

- [Purpose](#purpose)
- [Top-Level Shape](#top-level-shape)
- [Required Fields](#required-fields)
- [Optional Sections](#optional-sections)
- [Confidence Values](#confidence-values)
- [Example](#example)
- [Rendering Rule](#rendering-rule)

## Purpose

`study-result.json` is the single evidence source for the HTML, Markdown, CSV, and
question list. Do not hand-edit generated outputs. Correct the JSON and render again.

## Top-Level Shape

```json
{
  "meta": {},
  "summary": {},
  "reading_path": [],
  "flow": [],
  "symbols": [],
  "data_structures": [],
  "config_map": [],
  "evidence": [],
  "questions": {},
  "next_reading": [],
  "sources": []
}
```

## Required Fields

| Field | Meaning |
| --- | --- |
| `meta.project` | Project identifier such as `ctclib`. |
| `meta.topic_id` | Stable identifier for one flow or subsystem. |
| `meta.title` | Human-readable study topic. |
| `summary.one_sentence` | One sentence that states what the flow does. |
| `summary.what_it_does` | Array of short factual statements. |
| `reading_path` | Ordered places the user should open. |
| `flow` | Ordered execution steps with source evidence. |

Each `reading_path` item requires:

| Field | Meaning |
| --- | --- |
| `order` | Positive integer. |
| `name` | Function, file, or stage to read. |
| `source` | Repository-relative `path:line`. |
| `why` | Why the user should read it. |

Each `flow` item requires:

| Field | Meaning |
| --- | --- |
| `step` | Positive integer. |
| `name` | Short step name. |
| `source` | Repository-relative `path:line`. |
| `purpose` | What this step accomplishes. |

Recommended `flow` fields:

- `caller`
- `callee`
- `input`
- `output`
- `state`
- `normal`
- `error`
- `next`
- `confidence`

## Optional Sections

| Section | Item fields |
| --- | --- |
| `summary.key_findings` | String |
| `summary.reading_strategy` | String |
| `symbols` | `name`, `kind`, `defined_at`, `role`, `confidence` |
| `data_structures` | `name`, `defined_at`, `purpose`, `fields`, `ownership`, `confidence` |
| `config_map` | `key`, `source`, `consumed_at`, `meaning`, `default` |
| `evidence` | `claim`, `source`, `confidence` |
| `questions` | Arrays `confirmed`, `inferred`, `open` |
| `next_reading` | String |
| `sources` | Input document or source file used |

`meta.source_commit`, `meta.repository`, `meta.generated_at`, and `meta.purpose` are
recommended. Use `unavailable` rather than guessing a revision.

## Confidence Values

Only these values are valid:

- `confirmed`: current source proves the statement.
- `inferred`: evidence supports the statement but the exact path is incomplete.
- `open`: the required evidence is missing.

The renderer rejects other values.

## Example

```json
{
  "meta": {
    "project": "example",
    "topic_id": "request-main-flow",
    "title": "Request main flow",
    "repository": "D:\\Code\\example",
    "source_commit": "abc1234",
    "generated_at": "2026-11-12 15:00 +08:00",
    "purpose": "Understand how one request reaches the output stage."
  },
  "summary": {
    "one_sentence": "A request is parsed, dispatched, and written by three separate layers.",
    "what_it_does": [
      "The entrypoint parses configuration.",
      "The dispatcher selects one processing path.",
      "The output layer serializes the result."
    ],
    "key_findings": [
      "The entrypoint does not own business logic."
    ],
    "reading_strategy": [
      "Read the entrypoint, then follow the dispatcher call."
    ]
  },
  "reading_path": [
    {
      "order": 1,
      "name": "Run",
      "source": "src/main.c:20",
      "why": "Starts the request flow."
    }
  ],
  "flow": [
    {
      "step": 1,
      "name": "Parse input",
      "source": "src/main.c:20",
      "purpose": "Build the runtime configuration.",
      "caller": "Run",
      "callee": "ParseConfig",
      "input": "Configuration file path",
      "output": "Config structure",
      "state": "Config is owned by the caller",
      "normal": "Parsing succeeds",
      "error": "Invalid config stops the flow",
      "next": "src/dispatch.c:42",
      "confidence": "confirmed"
    }
  ],
  "symbols": [
    {
      "name": "Run",
      "kind": "function",
      "defined_at": "src/main.c:20",
      "role": "Main entrypoint",
      "confidence": "confirmed"
    }
  ],
  "data_structures": [],
  "config_map": [],
  "evidence": [
    {
      "claim": "Run starts the flow.",
      "source": "src/main.c:20",
      "confidence": "confirmed"
    }
  ],
  "questions": {
    "confirmed": [],
    "inferred": [],
    "open": []
  },
  "next_reading": [
    "Read ParseConfig in src/config.c."
  ],
  "sources": [
    "src/main.c",
    "src/dispatch.c"
  ]
}
```

## Rendering Rule

The JSON is authoritative. The renderer must keep HTML, Markdown, CSV, and questions
consistent. If one output cannot be written, report `PARTIAL` and name the missing file.
