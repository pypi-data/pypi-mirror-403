"""Application-wide constants."""

# Output
MAX_OUTPUT_LINES = 10_000
PROGRESS_BAR_WIDTH = 20

# Timeouts (seconds)
PROCESS_STOP_TIMEOUT = 5.0
PAUSE_CHECK_INTERVAL = 0.2
ITERATION_DELAY = 2.0
PTY_READ_TIMEOUT = 0.2

# Prompt handling
LARGE_PROMPT_THRESHOLD = 7000

# Cache
VERSION_CACHE_DURATION = 24 * 60 * 60  # 24 hours

# Animation
PULSE_INTERVAL = 0.5
PROGRESS_ANIMATION_INTERVAL = 0.25

# Progress file initial content
PROGRESS_INITIAL = "# Progress\n\n## Codebase Patterns\n\n---\n\n"
