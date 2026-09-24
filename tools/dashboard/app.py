# Code-Manor Telemetry Dashboard (feat-agent-telemetry-dashboard)
import streamlit as st
import os
import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime

# Configure page layout and title
st.set_page_config(page_title="Code-Manor Telemetry", page_icon="🏰", layout="wide")

# Custom Styling
st.markdown("""
<style>
    .reportview-container {
        background: #0d1117;
    }
    .main .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }
    .stMetric {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 10px 16px;
        border-radius: 8px;
    }
    .session-badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: bold;
    }
    .tool-card {
        border-left: 3px solid #58a6ff;
        background-color: #161b22;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------------------------
# Helper Functions: SQLite & Transcript Resolution
# ------------------------------------------------------------------------------

def find_db_paths():
    """Discover conversation_summaries.db across WSL and Windows paths."""
    candidates = [
        Path.home() / ".gemini" / "antigravity" / "conversation_summaries.db",
        Path.home() / ".gemini" / "antigravity-cli" / "conversation_summaries.db",
        Path("/mnt/c/Users/oguz_/.gemini/antigravity/conversation_summaries.db"),
    ]
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        candidates.append(Path(userprofile) / ".gemini" / "antigravity" / "conversation_summaries.db")
    if Path("/mnt/c/Users").exists():
        for u in Path("/mnt/c/Users").iterdir():
            candidates.append(u / ".gemini" / "antigravity" / "conversation_summaries.db")

    existing = []
    seen = set()
    for c in candidates:
        try:
            if c.exists():
                res = str(c.resolve())
                if res not in seen:
                    seen.add(res)
                    existing.append(c)
        except Exception:
            pass
    return existing


def get_recent_sessions(limit=3, workspace_path=None, filter_workspace=False):
    """Query recent conversations across Antigravity SQLite databases."""
    sessions = {}
    for db_path in find_db_paths():
        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            c = conn.cursor()
            query = """
                SELECT conversation_id, title, preview, step_count, last_modified_time, workspace_uris, agent_name, status
                FROM conversation_summaries
                ORDER BY last_modified_time DESC
            """
            for row in c.execute(query):
                cid, title, preview, step_count, last_mod, w_uris, agent_name, status = row
                if not cid:
                    continue
                if filter_workspace and workspace_path and w_uris:
                    norm_w = workspace_path.lower().replace("\\", "/").strip("/")
                    norm_w_uri = w_uris.lower().replace("%3a", ":").replace("%20", " ")
                    if norm_w not in norm_w_uri:
                        continue
                if cid not in sessions or str(last_mod) > str(sessions[cid]["last_modified_time"]):
                    clean_title = title or preview or "Untitled Session"
                    sessions[cid] = {
                        "conversation_id": cid,
                        "title": clean_title.strip(),
                        "preview": preview,
                        "step_count": step_count or 0,
                        "last_modified_time": str(last_mod)[:19] if last_mod else "Unknown",
                        "raw_time": str(last_mod),
                        "workspace_uris": w_uris or "",
                        "agent_name": agent_name or "antigravity",
                        "status": status or "unknown",
                        "db_path": str(db_path)
                    }
            conn.close()
        except Exception:
            pass

    sorted_sessions = sorted(sessions.values(), key=lambda s: s["raw_time"], reverse=True)
    return sorted_sessions[:limit]


def find_transcript_file(conversation_id):
    """Find transcript.jsonl or transcript_full.jsonl for a conversation."""
    bases = [
        Path.home() / ".gemini" / "antigravity" / "brain",
        Path.home() / ".gemini" / "antigravity-cli" / "brain",
        Path("/mnt/c/Users/oguz_/.gemini/antigravity/brain"),
    ]
    userprofile = os.environ.get("USERPROFILE")
    if userprofile:
        bases.append(Path(userprofile) / ".gemini" / "antigravity" / "brain")
    if Path("/mnt/c/Users").exists():
        for u in Path("/mnt/c/Users").iterdir():
            bases.append(u / ".gemini" / "antigravity" / "brain")

    for base in bases:
        full = base / conversation_id / ".system_generated" / "logs" / "transcript_full.jsonl"
        norm = base / conversation_id / ".system_generated" / "logs" / "transcript.jsonl"
        if full.exists():
            return full
        if norm.exists():
            return norm
    return None


def clean_tool_args(args):
    """Unquote stringified JSON values inside tool arguments."""
    if not isinstance(args, dict):
        return args
    cleaned = {}
    for k, v in args.items():
        if isinstance(v, str) and (v.startswith('"') and v.endswith('"')):
            try:
                cleaned[k] = json.loads(v)
            except Exception:
                cleaned[k] = v
        else:
            cleaned[k] = v
    return cleaned


def parse_transcript_events(transcript_path):
    """Parse transcript JSONL and group steps into structured conversation events."""
    events = []
    if not transcript_path or not Path(transcript_path).exists():
        return events

    raw_steps = []
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                if line.strip():
                    raw_steps.append(json.loads(line))
    except Exception as e:
        return events

    i = 0
    while i < len(raw_steps):
        step = raw_steps[i]
        stype = step.get("type")
        sindex = step.get("step_index", i)
        stime = step.get("created_at", "")
        if stime and len(stime) >= 19:
            stime = stime[:19].replace("T", " ")

        if stype == "USER_INPUT":
            events.append({
                "kind": "user",
                "step_index": sindex,
                "time": stime,
                "content": step.get("content", "")
            })
            i += 1
        elif stype == "PLANNER_RESPONSE":
            tool_calls = step.get("tool_calls", [])
            tool_results = []
            j = i + 1
            while j < len(raw_steps) and raw_steps[j].get("type") == "GENERIC":
                tool_results.append(raw_steps[j].get("content", ""))
                j += 1

            events.append({
                "kind": "assistant",
                "step_index": sindex,
                "time": stime,
                "thinking": step.get("thinking", ""),
                "content": step.get("content", ""),
                "tool_calls": tool_calls,
                "tool_results": tool_results
            })
            i = j
        elif stype == "SYSTEM_MESSAGE":
            events.append({
                "kind": "system",
                "step_index": sindex,
                "time": stime,
                "content": step.get("content", "")
            })
            i += 1
        else:
            i += 1

    return events


# ------------------------------------------------------------------------------
# Helper Functions: Tasks & Driver Logs
# ------------------------------------------------------------------------------

def parse_tasks(workspace_path):
    """Parse tasks from .tasks.toml, backlog.md, or tasks-axi list."""
    tasks = []
    w_path = Path(workspace_path)
    
    # 1. Try tasks-axi list command first
    try:
        res = subprocess.run(
            ["tasks-axi", "list"],
            cwd=workspace_path,
            capture_output=True,
            text=True,
            timeout=3
        )
        if res.returncode == 0:
            lines = res.stdout.splitlines()
            for line in lines:
                line_str = line.strip()
                if not line_str or line_str.startswith("count:") or line_str.startswith("tasks[") or line_str.startswith("help[") or line_str.startswith("-"):
                    continue
                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) >= 5:
                    tasks.append({
                        "id": parts[0],
                        "state": parts[1],
                        "kind": parts[2],
                        "repo": parts[3],
                        "title": ",".join(parts[4:]),
                    })
            if tasks:
                return tasks
    except Exception:
        pass

    # 2. Try .tasks.toml parsing if present
    tasks_toml = w_path / ".tasks.toml"
    if tasks_toml.exists():
        try:
            import tomllib
            with open(tasks_toml, "rb") as f:
                data = tomllib.load(f)
                raw_tasks = data.get("tasks", [])
                for t in raw_tasks:
                    tasks.append({
                        "id": t.get("id", "unknown"),
                        "state": t.get("state", "queued"),
                        "kind": t.get("kind", "task"),
                        "repo": t.get("repo", "-"),
                        "title": t.get("title", t.get("name", "")),
                    })
                if tasks:
                    return tasks
        except Exception:
            pass

    # 3. Fallback to backlog.md parsing
    backlog_file = w_path / "backlog.md"
    if backlog_file.exists():
        try:
            current_state = "queued"
            with open(backlog_file, "r", encoding="utf-8") as f:
                for line in f:
                    stripped = line.strip()
                    if stripped.startswith("## In flight"):
                        current_state = "in_flight"
                    elif stripped.startswith("## Queued"):
                        current_state = "queued"
                    elif stripped.startswith("## Done"):
                        current_state = "done"
                    elif stripped.startswith("- [ ]") or stripped.startswith("- [x]"):
                        is_checked = stripped.startswith("- [x]")
                        content = stripped[5:].strip()
                        state = "done" if is_checked else current_state
                        task_id = content.split(" - ")[0].strip() if " - " in content else content.split(" ")[0].strip()
                        title = content[len(task_id):].lstrip(" -").strip()
                        tasks.append({
                            "id": task_id,
                            "state": state,
                            "kind": "task",
                            "repo": "-",
                            "title": title or task_id
                        })
        except Exception:
            pass

    return tasks


def get_driver_status(workspace_path):
    """Parse driver status from .memory/scratch/active_maid_loop.log or latest log."""
    w_path = Path(workspace_path)
    scratch_dir = w_path / ".memory" / "scratch"
    
    active_log = scratch_dir / "active_maid_loop.log"
    log_file = None

    if active_log.exists():
        log_file = active_log
    elif scratch_dir.exists():
        log_files = sorted(scratch_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
        if log_files:
            log_file = log_files[0]

    if not log_file or not log_file.exists():
        return {
            "status": "idle",
            "log_path": None,
            "snippet": "No active or historical Maid driver logs found in .memory/scratch/.",
            "color": "gray"
        }

    try:
        with open(log_file, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()

        tail_content = "\n".join(content.splitlines()[-30:]) if content else ""

        if "Circuit Breaker Tripped" in content or "circuit breaker" in content.lower():
            status = "circuit-breaker"
            color = "red"
        elif "Ticket execution complete and verified successfully" in content or "PASSED (exit 0)" in content:
            status = "green"
            color = "green"
        elif "Running verification gate" in content or "Dispatching Turn" in content or "Checking state after Turn" in content:
            status = "running"
            color = "blue"
        elif "make check FAILED" in content or "Targeted test FAILED" in content:
            status = "retrying"
            color = "orange"
        else:
            status = "idle"
            color = "gray"

        return {
            "status": status,
            "log_path": str(log_file),
            "snippet": tail_content,
            "full_content": content,
            "color": color
        }
    except Exception as e:
        return {
            "status": "unknown",
            "log_path": str(log_file),
            "snippet": f"Error reading log file: {e}",
            "color": "red"
        }


def get_latest_review_findings(workspace_path):
    """Parse latest review.log from /home/oguz/.no-mistakes/logs/ or local .memory/."""
    candidates = []
    local_memory = Path(workspace_path) / ".memory"
    if local_memory.exists():
        candidates.extend(local_memory.glob("**/review*.log"))

    global_logs_dir = Path.home() / ".no-mistakes" / "logs"
    if global_logs_dir.exists():
        candidates.extend(global_logs_dir.glob("**/review*.log"))

    if not candidates:
        return None

    candidates = sorted(candidates, key=lambda p: p.stat().st_mtime, reverse=True)
    latest_review = candidates[0]

    try:
        with open(latest_review, "r", encoding="utf-8", errors="replace") as f:
            raw_text = f.read()

        parsed_json = None
        for line in raw_text.splitlines():
            line_str = line.strip()
            if line_str.startswith("{") and line_str.endswith("}"):
                try:
                    data = json.loads(line_str)
                    if "findings" in data or "risk_level" in data:
                        parsed_json = data
                        break
                except Exception:
                    continue

        return {
            "file": str(latest_review),
            "data": parsed_json,
            "raw_text": raw_text
        }
    except Exception as e:
        return {
            "file": str(latest_review),
            "error": str(e),
            "raw_text": ""
        }


# ------------------------------------------------------------------------------
# Sidebar Controls
# ------------------------------------------------------------------------------

st.sidebar.title("🏰 Code-Manor")
st.sidebar.caption("Agent Fleet & Telemetry Control Center")

# Load projects from ~/.gemini/antigravity/projects.json
home_dir = Path.home()
projects_file = home_dir / ".gemini" / "antigravity" / "projects.json"
projects = []

if projects_file.exists():
    try:
        with open(projects_file, "r", encoding="utf-8") as f:
            projects = json.load(f)
    except Exception as e:
        st.sidebar.error(f"Failed to load projects.json: {e}")

workspace_options = {}
default_idx = 0

if projects:
    for idx, p in enumerate(projects):
        name = p.get("name", p.get("id", f"repo-{idx}"))
        path = p.get("wsl_path", p.get("windows_path", ""))
        label = f"{name} ({p.get('policy', 'staged')}) - {path}"
        workspace_options[label] = path
        if "code-manor" in name.lower():
            default_idx = idx

selected_label = st.sidebar.selectbox(
    "Active Workspace",
    options=list(workspace_options.keys()) if workspace_options else ["Current Directory"],
    index=default_idx if workspace_options else 0,
)

workspace_dir = workspace_options[selected_label] if workspace_options else os.getcwd()

st.sidebar.divider()
st.sidebar.subheader("📡 Agent Session Filters")

# Configurable Last N Sessions (Default: 3, user-specified)
num_sessions = st.sidebar.slider(
    "Last N Sessions",
    min_value=1,
    max_value=25,
    value=3,
    help="Configurable depth for retrieved Antigravity CLI and IDE sessions."
)

filter_workspace = st.sidebar.checkbox("Filter by Active Workspace", value=False)

# Fetch sessions
recent_sessions = get_recent_sessions(
    limit=num_sessions,
    workspace_path=workspace_dir,
    filter_workspace=filter_workspace
)

session_labels = []
for idx, s in enumerate(recent_sessions):
    prefix = "🟢 (agy -c / Latest)" if idx == 0 else f"[{idx+1}]"
    title_snippet = s["title"][:38] + ("..." if len(s["title"]) > 38 else "")
    session_labels.append(f"{prefix} {title_snippet} ({s['step_count']} steps)")

if session_labels:
    selected_session_idx = st.sidebar.selectbox(
        "Active CLI Session",
        options=list(range(len(session_labels))),
        format_func=lambda i: session_labels[i],
        index=0,  # Default to index 0: the session resumed by agy -c
        help="Defaults to index 0, which corresponds to 'agy -c' (agy --continue)."
    )
    current_session = recent_sessions[selected_session_idx]
else:
    current_session = None

st.sidebar.divider()

# Auto-refresh or manual refresh controls
col_ref1, col_ref2 = st.sidebar.columns([1, 1])
with col_ref1:
    refresh_clicked = st.button("🔄 Refresh", use_container_width=True)
with col_ref2:
    auto_refresh = st.checkbox("Live Poll", value=False)

if auto_refresh:
    poll_interval = st.sidebar.slider("Interval (sec)", min_value=2, max_value=30, value=5)
    try:
        import time
        time.sleep(poll_interval)
        st.rerun()
    except Exception:
        pass

st.sidebar.caption(f"📁 Workspace: `{workspace_dir}`")


# ------------------------------------------------------------------------------
# Top Metrics & Header
# ------------------------------------------------------------------------------

st.title("🏰 Code-Manor Telemetry Dashboard")

tasks = parse_tasks(workspace_dir)
driver_info = get_driver_status(workspace_dir)

in_flight_tasks = [t for t in tasks if t["state"] in ("in_flight", "started", "running")]
done_tasks = [t for t in tasks if t["state"] == "done"]
queued_tasks = [t for t in tasks if t["state"] in ("queued", "ready", "open")]

col1, col2, col3, col4 = st.columns(4)

with col1:
    sess_title = current_session["title"][:22] + "..." if current_session and len(current_session["title"]) > 22 else (current_session["title"] if current_session else "None")
    st.metric(
        label="Active Session (agy -c)",
        value=sess_title,
        delta=f"{current_session['step_count']} steps" if current_session else "No session"
    )

with col2:
    st.metric(
        label="Driver Status",
        value=driver_info["status"].upper(),
        delta="Active" if driver_info["status"] in ("running", "retrying") else "Stable"
    )

with col3:
    active_title = in_flight_tasks[0]["id"] if in_flight_tasks else "None"
    st.metric(
        label="In-Flight Task",
        value=active_title,
        delta=f"{len(in_flight_tasks)} in flight"
    )

with col4:
    st.metric(
        label="Completed Tasks",
        value=len(done_tasks),
        delta=f"{len(queued_tasks)} queued"
    )

st.divider()


# ------------------------------------------------------------------------------
# Main Tabs
# ------------------------------------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "🤖 Antigravity Session Telemetry",
    "🖥️ Live Maid Terminal Stream",
    "🛡️ AI Code Review (no-mistakes)",
    "📋 Tasks-AXI Backlog"
])

# --- Tab 1: Antigravity Session Telemetry ---
with tab1:
    if current_session:
        # Session Metadata & Quick Command Bar
        cid = current_session["conversation_id"]
        col_m1, col_m2 = st.columns([3, 1])
        with col_m1:
            st.subheader(f"Session: {current_session['title']}")
            st.caption(f"ID: `{cid}` | Agent: **{current_session['agent_name']}** | Modified: `{current_session['last_modified_time']}` | Steps: **{current_session['step_count']}**")
        with col_m2:
            st.markdown("**CLI Resume Command:**")
            st.code(f"agy --conversation {cid}" if selected_session_idx != 0 else "agy -c", language="bash")

        transcript_file = find_transcript_file(cid)
        if transcript_file:
            events = parse_transcript_events(transcript_file)
            st.caption(f"Loaded {len(events)} conversation events from `{transcript_file}`")

            # Feed Display Controls
            col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1.5, 1, 1])
            with col_ctrl1:
                display_order = st.radio(
                    "Akış Yönü",
                    ["Kronolojik (Eskiden Yeniye ⬇️)", "Ters Kronolojik (Yeniden Eskiye ⬆️)"],
                    index=0,
                    horizontal=True,
                    help="Varsayılan: Konuşmanın başlangıcından sonuna doğru doğal akış (Yukarıdan aşağıya)."
                )
            with col_ctrl2:
                show_thinking = st.checkbox("Show Thinking Process", value=True)
            with col_ctrl3:
                show_tool_outputs = st.checkbox("Show Tool Execution Outputs", value=True)

            ordered_events = events if "Eskiden Yeniye" in display_order else list(reversed(events))

            # Render Events Feed
            for ev in ordered_events:
                kind = ev["kind"]
                s_idx = ev["step_index"]
                s_time = ev.get("time", "")

                if kind == "user":
                    with st.chat_message("user"):
                        st.markdown(f"**User Prompt** (Step `{s_idx}` — `{s_time}`)")
                        st.markdown(ev.get("content", ""))

                elif kind == "assistant":
                    with st.chat_message("assistant"):
                        st.markdown(f"**Agent Response** (Step `{s_idx}` — `{s_time}`)")

                        # Thinking Trace
                        thinking = ev.get("thinking", "")
                        if thinking and show_thinking:
                            with st.expander(f"💭 Thinking Trace ({len(thinking)} chars)", expanded=False):
                                st.markdown(thinking)

                        # Tool Calls & Paired Results
                        tool_calls = ev.get("tool_calls", [])
                        tool_results = ev.get("tool_results", [])
                        if tool_calls:
                            for t_idx, tc in enumerate(tool_calls):
                                t_name = tc.get("name", tc.get("toolName", "tool"))
                                t_summary = tc.get("toolSummary", tc.get("toolAction", ""))
                                t_args = clean_tool_args(tc.get("args", tc.get("arguments", {})))

                                with st.expander(f"🔧 Tool: `{t_name}` — *{t_summary}*", expanded=False):
                                    st.markdown("**Arguments:**")
                                    st.json(t_args)

                                    if show_tool_outputs and t_idx < len(tool_results):
                                        res_content = tool_results[t_idx]
                                        st.markdown("**Output:**")
                                        if res_content and res_content.strip():
                                            st.code(res_content[:5000], language="text")
                                        else:
                                            st.caption("(Empty tool output)")

                        # Main Assistant Text Content
                        content = ev.get("content", "")
                        if content and content.strip():
                            st.markdown(content)

                elif kind == "system":
                    with st.chat_message("system"):
                        st.markdown(f"ℹ️ **System Notification** (Step `{s_idx}` — `{s_time}`)")
                        st.markdown(ev.get("content", ""))

        else:
            st.warning(f"Could not locate transcript file for session `{cid}`.")
            st.info("Ensure the session logs exist in `~/.gemini/antigravity/brain/<id>/`.")
    else:
        st.info("No Antigravity sessions found. Start a session via `agy` CLI or select another workspace.")


# --- Tab 2: Live Maid Terminal Stream ---
with tab2:
    st.subheader("Live Maid Terminal Stream")
    if driver_info.get("log_path"):
        st.caption(f"Source: `{driver_info['log_path']}`")
        full_log = driver_info.get("full_content", driver_info.get("snippet", ""))
        st.markdown(
            f"""
            <div style="background-color: #0e1117; color: #00ff66; padding: 16px; border-radius: 8px; font-family: monospace; font-size: 13px; max-height: 550px; overflow-y: scroll; white-space: pre-wrap; border: 1px solid #30363d;">
{full_log if full_log.strip() else "(Log file is empty)"}
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.info("No active maid loop log found in `.memory/scratch/` for this workspace.")


# --- Tab 3: AI Code Review Findings ---
with tab3:
    st.subheader("AI Code Review Findings (no-mistakes)")
    review_info = get_latest_review_findings(workspace_dir)

    if not review_info:
        st.info("No `review.log` found in local `.memory/` or `~/.no-mistakes/logs/`.")
    elif "error" in review_info:
        st.error(f"Error loading review log: {review_info['error']}")
    else:
        st.caption(f"Log source: `{review_info['file']}`")
        review_data = review_info.get("data")

        if review_data:
            risk_level = str(review_data.get("risk_level", "unknown")).upper()
            risk_rationale = review_data.get("risk_rationale", "No rationale provided.")
            
            badge_color = "red" if risk_level == "HIGH" else "orange" if risk_level == "MEDIUM" else "green"
            st.markdown(f"**Overall Risk Level:** :{badge_color}[{risk_level}]")
            st.markdown(f"**Rationale:** {risk_rationale}")

            findings = review_data.get("findings", [])
            st.write(f"### Findings ({len(findings)})")
            
            if findings:
                for idx, finding in enumerate(findings):
                    severity = finding.get("severity", "info").lower()
                    fid = finding.get("id", f"finding-{idx+1}")
                    file_path = finding.get("file", "unknown")
                    line_no = finding.get("line", "")
                    desc = finding.get("description", "")
                    action = finding.get("action", "")

                    box_type = st.warning if severity == "warning" else st.error if severity in ("critical", "high", "error") else st.info
                    with box_type(f"**[{severity.upper()}] {fid}** — `{file_path}:{line_no}`"):
                        st.write(desc)
                        if action:
                            st.caption(f"Recommended Action: `{action}`")
            else:
                st.success("🎉 Zero code review findings! Verified clean.")

            if "tested" in review_data:
                st.caption(f"Tested Suites: {', '.join(review_data.get('tested', []))}")
            if "testing_summary" in review_data:
                st.info(f"**Testing Summary:** {review_data.get('testing_summary')}")
        else:
            st.warning("Found `review.log` but could not locate structured JSON findings. Raw content preview:")
            st.code(review_info["raw_text"][-2000:], language="text")


# --- Tab 4: Tasks-AXI Backlog ---
with tab4:
    st.subheader("Tasks-AXI Backlog & Execution Graph")
    if tasks:
        task_data = []
        for t in tasks:
            status_emoji = "🟢" if t["state"] == "done" else "🟡" if t["state"] in ("in_flight", "started", "running") else "⚪"
            task_data.append({
                "Status": f"{status_emoji} {t['state']}",
                "Task ID": t["id"],
                "Title / Objective": t["title"],
                "Kind": t["kind"],
                "Repo": t["repo"]
            })
        st.dataframe(task_data, use_container_width=True)
    else:
        st.info("No tasks discovered from `tasks-axi list`, `.tasks.toml`, or `backlog.md`.")
