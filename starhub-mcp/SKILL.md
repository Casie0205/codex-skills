---
name: starhub-mcp
description: Operate CHC StarHub through its MCP server, including checking runtime state, reusing GUI-owned serial connections, sending device commands, managing raw saves, reading logs, and handling firmware-upgrade status. Use for StarHub-mediated hardware work; do not use a separate serial client while StarHub owns the port.
---

# StarHub MCP

Use the StarHub MCP before falling back to GUI automation or a standalone
serial client. StarHub can own a serial port while allowing MCP and the GUI to
operate concurrently.

Read [references/tool-contract.md](references/tool-contract.md) when choosing
tools, sending commands, diagnosing errors, managing files, or upgrading
firmware.

## Mandatory Startup

Before claiming that StarHub MCP is unavailable or deciding which capability to
use:

1. Search for the exact MCP tool by name when it is not visible in the current
   tool subset. In particular, search for `send_command` before saying command
   sending is unsupported.
2. Call `get_status`.
3. Call `list_connections` and reuse the matching `handleKey`.
4. If capture matters, call `get_save_status` before starting or stopping a
   save.

`list_serial_ports` is not proof that MCP cannot use a port. A port marked
`busy` and owned by `starhub` is normally usable through the existing StarHub
connection.

## Connection Rules

- Prefer a connection already shown by `list_connections`, including one opened
  manually in StarHub.
- Do not call `connect_serial` with a different baud rate for an existing port.
  Resolve the intended baud and request user direction before disconnecting.
- Do not disconnect an active StarHub connection unless the user asks or the
  operation cannot be completed safely otherwise.
- Treat `BUSY` as an active command/response window. Observe, wait, and retry
  once the current operation has finished.
- Treat `NOT_CONNECTED` as a StarHub or connection-state issue. Recheck
  `get_status` and `list_connections` before retrying.

## Sending Commands

- Use `send_command` with the existing `handleKey`.
- Send the complete command body. Prefer commands containing `*FF` with
  `add_checksum: false`.
- Set `add_crlf: true` unless the command already contains CR/LF.
- If omitting the checksum, set `add_checksum: true` instead.
- Verify the returned `text`/`hex`, `size`, and `timed_out`; do not equate
  `RESPONSE,OK` with successful data output.
- Send commands sequentially when the device is streaming or changing baud.
  Do not bulk-paste an unverified configuration sequence.

When changing message output:

- `OUTMSG ... A` and `OUTMSG ... B` are independent requests. Adding B does not
  remove A.
- To guarantee a clean format transition, use `OFFMSG,<port>*FF`, start a fresh
  save file, then add only the desired `OUTMSG` requests.
- Per-message `OFFMSG` requires the exact requested message name. Compatibility
  aliases may not match native names, so avoid relying on alias-specific
  cleanup when a whole-port clear is acceptable.

## Capture Rules

- Configure commands first, then start a fresh save so startup responses and
  stale output do not contaminate the dataset.
- Save temporary captures under `D:\DataDownload` by default. Copy a capture to
  `D:\Dataset` only when the user explicitly requests processing, analysis, or
  longer-term retention.
- Use `start_save` without timestamps for raw protocol logs unless the user
  explicitly requests timestamp injection.
- Use `stop_save` before treating the saved file as complete.
- Use `read_message_file` only for bounded tails or keyword-filtered inspection.
  Do not dump large binary files into chat.
- GMF Binary can start with `AA 44 72`; compatible Binary can start with
  `AA 44 12`. Text beginning with `#` is ASCII. Do not classify message format
  from a display label alone.

## Mutation Boundaries

- Do not send `SAVECONFIG`, `RESET`, `FRESET`, or upgrade commands unless the
  user explicitly requests persistence, restart, erasure, or firmware work.
- Require explicit confirmation immediately before firmware upgrade or version
  downgrade.
- Do not replace StarHub MCP with Computer Use merely because a tool was not in
  the initial search result. Use GUI automation only when the required MCP
  capability is genuinely absent or the user asks for it.

## Reporting

Report:

- the exact `handleKey`, baud, and save path;
- each command outcome without hiding non-OK responses;
- whether data was configured, not merely whether `RESPONSE,OK` appeared;
- message IDs or sync bytes used for binary verification;
- any BUSY, disconnect, timeout, or mixed-format risk.
