# StarHub MCP Tool Contract

Source: company Wiki page `dev_cc:test:testtools:starhub_mcpserver`.

## Tool Inventory

The current StarHub MCP exposes:

| Tool | Purpose |
| --- | --- |
| `get_status` | Probe MCP-to-StarHub IPC and StarHub process state. |
| `list_serial_ports` | List serial ports, type, busy state, and owner. |
| `connect_serial` | Open or reuse a connection; baud `0` auto-detects. |
| `disconnect` | Close a GUI- or MCP-opened connection. |
| `list_connections` | List active serial/USB/TCP connections and handles. |
| `get_device_version` | Read device firmware version. |
| `send_command` | Send ASCII or hex bytes and wait for a response window. |
| `start_upgrade` | Start `.pkg` firmware upgrade. |
| `get_upgrade_status` | Poll upgrade state and progress. |
| `cancel_upgrade` | Cancel an upgrade task. |
| `start_save` | Save the raw receive stream. |
| `stop_save` | Stop saving. |
| `get_save_status` | Return save state and current path. |
| `read_message_file` | Read a bounded file tail, optionally filtered. |

If deferred tool discovery omits a known tool, search its exact name before
changing strategy.

## send_command

Required:

- `handleKey`: value returned by `connect_serial` or `list_connections`.
- `data`: ASCII command or hex byte string.

Useful parameters:

- `format`: `ascii` or `hex`.
- `add_crlf`: usually `true` for ASCII commands.
- `add_checksum`: adds the command prefix and XOR checksum for ASCII.
- `timeout_ms`: 100-8000 ms response window.

Command conventions:

```text
>OUTMSG,COM2,GPSEPHB,ONCHANGED*FF
>OFFMSG,COM2*FF
```

With `*FF` present in `data`, set `add_checksum: false`. If the command omits
the checksum field, use `add_checksum: true` instead.

The response is returned as:

```text
{ hex, text, size, timed_out }
```

`timed_out: true` means no data arrived in the response window; it is not proof
that the command was rejected. Recheck connection state and command effects.

## Save and File Handling

- `start_save` fields: `handleKey`, absolute `dir`, optional `fileName`,
  `split_hours` or `split_mb`, and `with_timestamp`.
- Do not set both split modes.
- Get the actual path with `get_save_status`.
- `read_message_file` defaults to the last 64 KB and caps output at 1 MB.
- For binary logs, request bounded `hex` output only when byte-level inspection
  is necessary.

## Common Failure Modes

| Symptom | Correct response |
| --- | --- |
| `NOT_CONNECTED` | Check `get_status` and `list_connections`; do not assume the MCP server is absent. |
| `BUSY` | Another response window is active. Wait and retry once the current window closes. |
| `CONFLICT` | Baud mismatch or upgrade lock. Do not disconnect/upgrade without user direction. |
| Port listed busy by StarHub | Reuse the StarHub `handleKey`; do not open a competing serial client. |
| `RESPONSE,OK` but no data | Check trigger, requested format, old subscriptions, port, and whether the save started after the message was emitted. |
| ASCII A remains after requesting B | A and B coexist. Clear the whole output port and start a new capture. |
| Version empty after connect | Wait briefly and retry `get_device_version`. |

## Safety

- Never persist configuration or change firmware without an explicit request.
- Confirm the exact target port before destructive or persistent operations.
- Preserve enough raw evidence to distinguish command acceptance from actual
  data output.
