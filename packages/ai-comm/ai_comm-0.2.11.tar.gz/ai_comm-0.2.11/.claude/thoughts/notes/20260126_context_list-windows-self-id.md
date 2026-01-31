# Context: list-ai-windows Self Window ID

## Background

When an AI assistant uses `ai-comm list-ai-windows` to discover available targets, the current implementation returns all detected AI CLI windows without indicating which one is the caller. This can lead to the AI accidentally sending messages to itself.

## Key Details

- Goal: Include the caller's window ID in `list-ai-windows` output to prevent self-messaging
- The kitten's `handle_result` function already receives `target_window_id` parameter (line 232)
- This parameter represents the window that invoked the kitten command

## Technical Context

**Files to modify:**

1. `src/ai_comm/kitten/ai_comm_kitten.py`
   - Function: `list_ai_windows(boss)` at line 182
   - Function: `handle_result()` at line 230
   - Need to pass `target_window_id` to `list_ai_windows()` and include in response

2. `src/ai_comm/commands/window.py`
   - Function: `list_ai_windows()` at line 46
   - Update display format to show self window indicator

3. `src/ai_comm/kitten_client.py`
   - Function: `list_ai_windows()` at line 169
   - Return self_window_id from response

**Response schema change:**

```python
# Current
{"status": "ok", "ai_windows": [...]}

# Proposed
{"status": "ok", "ai_windows": [...], "self_window_id": 123}
```

**Display format options:**

- Add `(self)` marker after the current window's ID
- Add separate line showing current window ID
- Filter self from list and show separately

## Next Steps

- [ ] Modify `list_ai_windows()` to accept and return `target_window_id`
- [ ] Update `handle_result()` to pass the parameter
- [ ] Update CLI display to indicate self window
- [ ] Consider adding `--exclude-self` flag for programmatic use
