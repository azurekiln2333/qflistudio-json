# Herdr Pi request monitoring

This monitor observes the four existing Pi panes in workspace w29.
It retries terminal connection failures in their original panes.
It preserves retry delivery state across monitor restarts.
Fresh output plus a terminal pane completes a task before stale errors are read.
A failed retry delivery remains eligible after backoff.
Five attempts per pane cap duplicate prompts and emit an explicit limit event.
Observation failures are logged and polled again.
Working panes are never interrupted by this monitor.

Ten pure decision controls passed. They cover active-pane protection, fresh
completion, initial retry, successful-delivery deduplication, failed-delivery
backoff and retry, the retry limit, clean idle, blocked state and fast completion.
No fake control sends a real Pi prompt.

This is a dated monitor for the final review tasks started at
2026-10-25T21:02:45Z. Its pane IDs and output paths are specific to that batch.
A later batch must use a new state path and output freshness boundary.
This tool does not authorize SDK, Flutter or device actions.
