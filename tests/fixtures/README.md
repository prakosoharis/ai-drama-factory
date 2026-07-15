# Test Fixtures

Tests copy the synthetic V2.1 project into a temporary directory and mutate
only that copy. This keeps fixtures small, deterministic, and free of V1
assets; file-mode cases use tiny text files rather than media.
