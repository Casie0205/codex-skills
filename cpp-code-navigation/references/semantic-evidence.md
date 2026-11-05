# C++ Semantic Evidence Guide

## 目录

- [1. Evidence levels](#1-evidence-levels)
- [2. Symbol investigation](#2-symbol-investigation)
- [3. Signature changes](#3-signature-changes)
- [4. Include diagnosis](#4-include-diagnosis)
- [5. Fallback without a language service](#5-fallback-without-a-language-service)

## 1. Evidence levels

| Level | Evidence | Allowed conclusion |
| --- | --- | --- |
| Weak | `rg` match | The text occurs here |
| Medium | Declaration plus definition read in full | The symbol has this declared and implemented contract |
| Strong | Language-service definition, references, or call hierarchy | The compiler-aware relationship is confirmed |
| Build | Fresh compiler or linker output | The change builds, or the exact diagnostic remains |

Do not promote a weak observation into a medium or strong conclusion without reading the associated code.

## 2. Symbol investigation

Record:

- qualified name
- declaration path and line
- definition path and line
- namespace, class, and owning header
- overload or template alternatives
- direct callers and callback/function-pointer uses

If a language service is unavailable, inspect every candidate declaration and definition. Report unresolved ambiguity instead of silently choosing one.

## 3. Signature changes

Before editing:

1. Find the declaration and definition.
2. Find direct and indirect callers.
3. Find address-taken uses and callback registrations.
4. Check virtual overrides and interface implementations.
5. Check template specializations and conditional compilation.

After editing, build the owning target and any dependent targets.

## 4. Include diagnosis

For a missing-header or incomplete-type error:

1. Read the diagnostic and the requesting source line.
2. Identify the declaration that requires the type.
3. Determine whether a forward declaration is sufficient.
4. Find the canonical header that defines the type.
5. Verify the project include root or package that owns that header.
6. Prefer the narrowest correct include or project dependency.

Do not add a recursive include directory or an unrelated umbrella header merely to make one error disappear.

## 5. Fallback without a language service

Use this sequence:

1. Locate candidates with `rg`.
2. Read complete surrounding scopes and the nearest preprocessor guards.
3. Search for qualified and unqualified names separately.
4. Use compiler output or a compile-only check to validate the selected interpretation.
5. State which semantic step could not be verified and what evidence is missing.
