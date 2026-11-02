# Modularity Rules

Treat these rules as structural guardrails, not optional style advice.

## Core Principle

Keep orchestration thin and push distinct responsibilities into focused modules. New functionality should make the codebase easier to reason about, not just technically complete.

## What Belongs In Main Files

Main or central files may own:

- top-level flow control
- dependency wiring
- route or command registration
- high-level sequencing
- thin parameter translation

Main or central files should not accumulate:

- business rules
- data parsing and normalization
- validation logic
- persistence details
- transport-specific adapters
- output formatting
- large conditional branches for unrelated behaviors

## Split By Responsibility

Create a new file or submodule when the change introduces a distinct job, such as:

- domain logic
- parsing or serialization
- validation
- adapter or integration code
- storage or cache access
- output shaping or rendering
- background processing

Prefer one clear responsibility per module. Small helper overlap is acceptable; mixed ownership is not.

## Directory Heuristics

Split into a subdirectory when a new feature needs multiple cooperating files, such as:

- public entrypoint
- service or domain logic
- data model or types
- adapters
- tests

Favor grouping by feature or bounded responsibility over dumping files into a generic utils bucket.

## File-Bloat Triggers

Pause and split when any of these happen:

- a file becomes the default destination for unrelated logic
- the main flow becomes hard to scan top-to-bottom
- parsing, business logic, and output all appear in the same patch
- new tests require many mocks because responsibilities are tangled
- review comments start referring to "this file does too much"

## Anti-Patterns

Avoid:

- putting the whole feature into one file because it is faster
- hiding business logic inside controller, router, CLI, or pipeline entrypoints
- mixing configuration parsing with runtime behavior
- mixing data access and presentation formatting
- creating "misc", "helpers2", or "temp" modules as the landing zone for unresolved structure

## Preferred Direction

When several structures are viable, prefer the one that:

- keeps the entrypoint easiest to read
- gives each module a clear job
- makes tests more local and focused
- allows future extensions without reopening the main file
- matches existing codebase conventions

## Review Questions

Ask during review:

- Did the main file stay mostly orchestration and wiring?
- Did each new module get a clear responsibility?
- Did any file absorb multiple new concerns?
- Did the change create a natural home for future extensions?
- Would a new engineer know where to place the next related change?
