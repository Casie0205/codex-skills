---
name: cpp-code-navigation
description: Read, trace, and change C or C++ code using semantic evidence from language services or the compiler. Use for symbol lookup, call-hierarchy analysis, signature changes, include-graph debugging, and any task where text search alone could confuse overloads, templates, macros, or conditional compilation.
---

# C++ Code Navigation

Text search locates candidates. It does not prove which C++ symbol is used.

## Evidence Rules

- Cite exact file paths and line numbers for every material conclusion.
- Inspect declarations and definitions; do not infer a function's behavior from its name.
- Check overloads, namespaces, templates, base classes, macros, and active preprocessor branches before changing a symbol.
- Before changing a function signature, find callers and function-pointer or callback uses.
- Before adding or removing an include, determine the owner of the symbol and the correct include root.
- If semantic tools disagree with text search, investigate the difference instead of choosing the more convenient result.

## Tool Order

1. Prefer a C++ language service, such as clangd or the Visual Studio C++ language service, for definitions, references, and call hierarchy.
2. Use `compile_commands.json`, project include paths, or MSVC compilation to verify include ownership and active branches.
3. Use `rg` only to locate candidate files, literals, comments, or configuration.
4. Validate with the project's actual compiler or build system. On Windows MSVC projects, use `windows-cpp-build`; on other projects, use the configured CMake, Ninja, Bazel, or native build command.

Read [references/semantic-evidence.md](references/semantic-evidence.md) when semantic tooling is unavailable or when a change crosses declarations, includes, overloads, or compile-time branches.
