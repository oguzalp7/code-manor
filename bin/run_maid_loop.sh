#!/usr/bin/env bash
# ==============================================================================
# 🏰 Code-Manor: Maid Autonomous Multi-Turn Subprocess Loop Driver
# ==============================================================================
# Drives Maid (agy CLI) across autonomous TDD iterations, awaiting full
# execution of make check and verification gates without 10-second background
# task premature termination.
#
# Adheres to the Git-Status-Aware Synchronization Protocol:
# 1. Baseline verification if working tree is uncommitted/desynchronized.
# 2. Maid performs edits in src/ and tests/.
# 3. When Maid finishes a turn and becomes idle/exits, driver checks git status.
# 4. If sync is disrupted by edits, driver runs make check at OS level (synchronous).
# 5. If make check passes (exit 0), runs gate command and pushes to GitHub.
# 6. If make check fails, feeds compiler/test errors back via agy --continue.
# ==============================================================================

set -eo pipefail

PROMPT_FILE="${1:-}"
if [ -z "$PROMPT_FILE" ] || [ ! -f "$PROMPT_FILE" ]; then
  echo "Error: Prompt file not provided or not found." >&2
  echo "Usage: $0 <path-to-prompt-file> [max_turns]" >&2
  exit 1
fi

MAX_TURNS="${2:-10}"
MODEL="${MAID_MODEL:-gemini-3.8-flash-low}"
EFFORT="${MAID_EFFORT:-low}"
FLAGS="${MAID_FLAGS:---dangerously-skip-permissions}"
GATE_COMMAND="${MAID_GATE_COMMAND:-no-mistakes axi run --skip ci}"
POLICY="${MAID_POLICY:-staged}"

# Set up dual logging to .memory/scratch/active_maid_loop.log
LOG_DIR=".memory/scratch"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/active_maid_loop.log"
exec > >(tee "$LOG_FILE") 2>&1

# Extract Ticket ID and Intent from prompt file
TICKET_ID=$(grep -E '(Task ID:|Task Assignment:)' "$PROMPT_FILE" 2>/dev/null | head -n 1 | sed -E 's/.*(Task ID:|Task Assignment:)[[:space:]]*//' | tr -d '\r' | xargs || true)
if [ -z "$TICKET_ID" ]; then
  TICKET_ID=$(basename "$PROMPT_FILE" .txt)
fi

# Extract explicit Intent line if declared by Butler (e.g. 'Intent: [agent-90]: ...')
EXPLICIT_INTENT=$(grep -E '^Intent:' "$PROMPT_FILE" 2>/dev/null | head -n 1 | sed -E 's/^Intent:[[:space:]]*//' | tr -d '\r"' | xargs || true)
if [ -n "$EXPLICIT_INTENT" ]; then
  INTENT="$EXPLICIT_INTENT"
else
  OBJECTIVE=$(grep -A 2 -E '^## Objective' "$PROMPT_FILE" 2>/dev/null | tail -n +2 | head -n 1 | tr -d '\r"' | xargs || true)
  if [ -n "$OBJECTIVE" ]; then
    INTENT="Implement $TICKET_ID: $(echo "$OBJECTIVE" | cut -c 1-100)"
  else
    INTENT="Implement $TICKET_ID"
  fi
fi

# Dynamically inject --intent if gate command invokes no-mistakes and lacks --intent
if [[ "$GATE_COMMAND" == *"no-mistakes"* ]] && [[ "$GATE_COMMAND" != *"--intent"* ]]; then
  GATE_COMMAND="$GATE_COMMAND --intent \"$INTENT\""
fi

# Extract Targeted Test from prompt file if declared (e.g. 'Target Test Files:' or 'Target Test:')
RAW_TARGET_TEST=$(grep -E 'Target Test( Files)?:' "$PROMPT_FILE" 2>/dev/null | head -n 1 | sed -E 's/.*Target Test( Files)?:[[:space:]]*//' | tr -d '\r' | xargs || true)
if [ -n "$RAW_TARGET_TEST" ]; then
  # If it is a single JS/TS test file path without commands, wrap with vitest
  if [[ "$RAW_TARGET_TEST" =~ \.(ts|tsx|js|jsx)$ ]] && [[ "$RAW_TARGET_TEST" != *" "* ]]; then
    TARGET_TEST_CMD="npx vitest run $RAW_TARGET_TEST"
  else
    TARGET_TEST_CMD="$RAW_TARGET_TEST"
  fi
else
  TARGET_TEST_CMD=""
fi

echo "🏰 [Code-Manor] Initializing Maid Autonomous Loop Driver..."
echo "   Model: $MODEL | Effort: $EFFORT | Max Turns: $MAX_TURNS"
echo "   Gate Command: $GATE_COMMAND"
if [ -n "$TARGET_TEST_CMD" ]; then
  echo "   Targeted Test (Inner Loop): $TARGET_TEST_CMD"
fi

# ------------------------------------------------------------------------------
# 1. Pre-Flight Git Synchronization Check
# ------------------------------------------------------------------------------
INITIAL_STATUS=$(git status --porcelain -- ':!backlog.md' ':!.tasks.toml' ':!.memory/**' ':!*.md')
if [ -n "$INITIAL_STATUS" ]; then
  echo "⚠️  [Code-Manor] Working tree has uncommitted code changes before ticket dispatch."
  echo "   Running baseline make check to verify pre-existing state..."
  if ! make check; then
    echo "❌ [Code-Manor] Pre-existing baseline is broken. Aborting Maid dispatch." >&2
    exit 1
  fi
  echo "✅ [Code-Manor] Baseline make check passed. Proceeding with dirty tree."
else
  echo "✅ [Code-Manor] Git working tree is clean and synchronized. Baseline verified."
fi

INITIAL_HEAD=$(git rev-parse HEAD)

# ------------------------------------------------------------------------------
# 2. First Turn Dispatch
# ------------------------------------------------------------------------------
echo "🚀 [Code-Manor] Dispatching Initial Turn to Maid via agy CLI..."
PROMPT_CONTENT=$(cat "$PROMPT_FILE")

# Run initial prompt (agy will exit when turn completes)
agy --model "$MODEL" --effort "$EFFORT" $FLAGS -p "$PROMPT_CONTENT" || true

# ------------------------------------------------------------------------------
# 3. Autonomous Post-Turn & TDD Iteration Loop
# ------------------------------------------------------------------------------
TURN=1
while [ "$TURN" -le "$MAX_TURNS" ]; do
  echo "🔍 [Code-Manor] Checking state after Turn $TURN..."
  
  CURRENT_STATUS=$(git status --porcelain -- ':!backlog.md' ':!.tasks.toml' ':!.memory/**' ':!*.md')
  CURRENT_HEAD=$(git rev-parse HEAD)
  
  # Check if Maid made edits or commits
  if [ "$CURRENT_STATUS" = "$INITIAL_STATUS" ] && [ "$CURRENT_HEAD" = "$INITIAL_HEAD" ]; then
    echo "⚠️  [Code-Manor] Turn $TURN produced no file modifications or commits."
    # If no changes were produced, prompt Maid to take action
    if [ "$TURN" -lt "$MAX_TURNS" ]; then
      echo "🔄 [Code-Manor] Prompting Maid to begin implementation..."
      agy --continue --effort "$EFFORT" $FLAGS -p "No file edits were detected. Please proceed with reading the target files and implementing the required changes in tests/ and src/." || true
      TURN=$((TURN + 1))
      continue
    else
      echo "❌ [Code-Manor] Maid stalled without producing changes across $MAX_TURNS turns." >&2
      exit 1
    fi
  fi

  # Step 3a: Inner Loop - Fast Targeted Test (< 2 seconds) if specified
  if [ -n "$TARGET_TEST_CMD" ]; then
    echo "🧪 [Code-Manor] Running fast targeted test (inner loop): $TARGET_TEST_CMD..."
    TARGET_LOG=$(mktemp)
    if eval "$TARGET_TEST_CMD" > "$TARGET_LOG" 2>&1; then
      echo "✅ [Code-Manor] Targeted test PASSED (exit 0)!"
      rm -f "$TARGET_LOG"
    else
      echo "❌ [Code-Manor] Targeted test FAILED! Capturing test error trace..."
      ERROR_TRACE=$(tail -n 50 "$TARGET_LOG")
      rm -f "$TARGET_LOG"
      
      echo "------------------------------------------------------------------------"
      echo "$ERROR_TRACE"
      echo "------------------------------------------------------------------------"
      
      NEXT_PROMPT="Targeted test ($TARGET_TEST_CMD) failed with the following errors:

\`\`\`
$ERROR_TRACE
\`\`\`

Instructions:
1. Fix the implementation in src/ to make this targeted test pass green.
2. DO NOT delete or tamper with test assertions.
3. Stay strictly within the declared scope."

      TURN=$((TURN + 1))
      if [ "$TURN" -le "$MAX_TURNS" ]; then
        echo "🔄 [Code-Manor] Dispatching Turn $TURN to Maid with targeted test feedback..."
        agy --continue --effort "$EFFORT" $FLAGS -p "$NEXT_PROMPT" || true
      fi
      continue
    fi
  fi

  # Step 3b: Outer Loop - Hermetic full make check (runs once targeted test is green)
  echo "🧪 [Code-Manor] Running hermetic exit verification: make check (OS-level)..."
  CHECK_LOG=$(mktemp)
  if make check > "$CHECK_LOG" 2>&1; then
    echo "✅ [Code-Manor] make check PASSED (exit 0)!"
    rm -f "$CHECK_LOG"
    
    # Run the designated gate command and capture its output (skip if yolo)
    if [ "$POLICY" = "yolo" ]; then
      echo "⏩ [Code-Manor] Policy is 'yolo'. Skipping verification gate ($GATE_COMMAND)..."
      GATE_PASSED=1
    else
      # Commit verified changes before running gate so tools like no-mistakes have a clean working tree
      UNCOMMITTED=$(git status --porcelain -- ':!backlog.md' ':!.tasks.toml' ':!.memory/**')
      if [ -n "$UNCOMMITTED" ]; then
        echo "📝 [Code-Manor] Creating verified implementation commit for $TICKET_ID..."
        git add -A
        git commit -m "feat($TICKET_ID): turn $TURN verified implementation" || true
      fi

      GATE_LOG=$(mktemp)
      echo "🛡️  [Code-Manor] Running verification gate: $GATE_COMMAND (Policy: $POLICY)..."
      if eval "$GATE_COMMAND" > "$GATE_LOG" 2>&1; then
        echo "✅ [Code-Manor] Verification gate PASSED (exit 0)!"
        cat "$GATE_LOG"
        rm -f "$GATE_LOG"
        GATE_PASSED=1
      else
        GATE_PASSED=0
      fi
    fi

    if [ "$GATE_PASSED" -eq 1 ]; then
      # Check if upstream branch is configured and push if safe
      UPSTREAM=$(git rev-parse --abbrev-ref --symbolic-full-name @{u} 2>/dev/null || true)
      if [ -n "$UPSTREAM" ]; then
        echo "📤 [Code-Manor] Pushing verified changes to GitHub ($UPSTREAM)..."
        git push || echo "⚠️  Push failed or requires explicit sync; leaving branch for Butler."
      fi
      
      echo "🏁 [Code-Manor] Ticket execution complete and verified successfully in $TURN turn(s)."
      exit 0
    else
      echo "⚠️  [Code-Manor] make check passed but gate command failed."
      GATE_ERROR=$(tail -n 40 "$GATE_LOG")
      echo "------------------------------------------------------------------------"
      echo "$GATE_ERROR"
      echo "------------------------------------------------------------------------"

      # Circuit Breaker: Detect infrastructure / auth / CLI syntax errors
      if echo "$GATE_ERROR" | grep -Ei "(ACCESS_TOKEN_TYPE_UNSUPPORTED|invalid authentication credentials|401 Unauthorized|unknown flag|error: \"--intent|daemon not running)" >/dev/null 2>&1; then
        echo "🚨 [Code-Manor] Circuit Breaker Tripped! Detected tooling/auth/infrastructure failure in gate command:" >&2
        echo "$GATE_ERROR" >&2
        echo "   This is NOT a code defect. Aborting loop to protect LLM quota." >&2
        rm -f "$GATE_LOG"
        exit 2
      fi

      rm -f "$GATE_LOG"
      NEXT_PROMPT="make check passed, but the verification gate ($GATE_COMMAND) failed with the following findings:

\`\`\`
$GATE_ERROR
\`\`\`

Instructions:
1. Address the verification gate findings shown above in src/ or tests/.
2. DO NOT delete existing test assertions.
3. Report your edits."
    fi
  else
    echo "❌ [Code-Manor] make check FAILED! Capturing compiler/test error trace..."
    ERROR_TRACE=$(tail -n 50 "$CHECK_LOG")
    rm -f "$CHECK_LOG"
    
    echo "------------------------------------------------------------------------"
    echo "$ERROR_TRACE"
    echo "------------------------------------------------------------------------"
    
    NEXT_PROMPT="make check failed with the following compiler/test errors:

\`\`\`
$ERROR_TRACE
\`\`\`

Instructions:
1. Fix the implementation in src/ to resolve these errors.
2. DO NOT delete or tamper with test assertions in tests/.
3. Report your edits."
  fi

  # Advance to next turn
  TURN=$((TURN + 1))
  if [ "$TURN" -le "$MAX_TURNS" ]; then
    echo "🔄 [Code-Manor] Dispatching Turn $TURN to Maid with feedback..."
    agy --continue --effort "$EFFORT" $FLAGS -p "$NEXT_PROMPT" || true
  fi
done

echo "❌ [Code-Manor] Reached MAX_TURNS ($MAX_TURNS) without passing verification. Escalating to Butler." >&2
exit 1
