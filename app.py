import streamlit as st
import uuid
from datetime import datetime
from utils.transcript import get_transcript, InvalidYouTubeURLError, TranscriptNotAvailableError
from utils.summarizer import summarize, APIError

st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎥",
    layout="wide"
)

st.markdown("""
<style>
    /* Import font */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f0f1a 0%, #1a1a2e 100%);
        border-right: 1px solid rgba(255,255,255,0.08);
    }

    /* Active session highlight */
    .session-active {
        background: linear-gradient(135deg, rgba(99,102,241,0.3), rgba(168,85,247,0.2));
        border: 1px solid rgba(99,102,241,0.5);
        border-radius: 10px;
        padding: 8px 12px;
        font-weight: 600;
        color: #a78bfa;
    }

    /* History card */
    .history-card {
        background: linear-gradient(135deg, rgba(15,15,26,0.95), rgba(26,26,46,0.9));
        border: 1px solid rgba(99,102,241,0.2);
        border-radius: 14px;
        padding: 20px 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        transition: border-color 0.2s ease;
    }

    .history-card:hover {
        border-color: rgba(99,102,241,0.5);
    }

    .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 14px;
    }

    .card-url {
        font-size: 0.78rem;
        color: #6366f1;
        word-break: break-all;
        text-decoration: none;
    }

    .card-timestamp {
        font-size: 0.72rem;
        color: #6b7280;
        white-space: nowrap;
        margin-left: 12px;
        flex-shrink: 0;
    }

    .tag {
        display: inline-block;
        background: rgba(99,102,241,0.15);
        color: #818cf8;
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 20px;
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 10px;
        margin-right: 6px;
        margin-bottom: 10px;
        letter-spacing: 0.04em;
        text-transform: uppercase;
    }

    .short-summary-text {
        color: #e2e8f0;
        font-size: 0.95rem;
        line-height: 1.65;
        margin-bottom: 14px;
    }

    .takeaway-item {
        display: flex;
        align-items: flex-start;
        gap: 10px;
        padding: 6px 0;
        color: #cbd5e1;
        font-size: 0.88rem;
        line-height: 1.5;
    }

    .takeaway-bullet {
        color: #6366f1;
        font-weight: 700;
        flex-shrink: 0;
        margin-top: 1px;
    }

    .main-header {
        background: linear-gradient(135deg, #6366f1, #a855f7);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        margin-bottom: 0;
    }

    .subtitle {
        color: #64748b;
        font-size: 0.95rem;
        margin-top: 4px;
        margin-bottom: 28px;
    }

    .divider {
        border: none;
        border-top: 1px solid rgba(99,102,241,0.15);
        margin: 24px 0;
    }

    .history-label {
        color: #6366f1;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 16px;
    }

    .empty-state {
        text-align: center;
        padding: 60px 20px;
        color: #374151;
    }

    .empty-state-icon {
        font-size: 3rem;
        margin-bottom: 12px;
    }

    .error-card {
        background: rgba(239,68,68,0.08);
        border: 1px solid rgba(239,68,68,0.25);
        border-radius: 12px;
        padding: 16px 20px;
        color: #fca5a5;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


def init_state():
    if "sessions" not in st.session_state:
        first_id = str(uuid.uuid4())
        st.session_state.sessions = {
            first_id: {"name": "Session 1", "history": []}
        }
        st.session_state.active_session_id = first_id

    if "active_session_id" not in st.session_state:
        st.session_state.active_session_id = next(iter(st.session_state.sessions))

    if "renaming_id" not in st.session_state:
        st.session_state.renaming_id = None


init_state()


def active_session():
    return st.session_state.sessions[st.session_state.active_session_id]


def add_new_session():
    new_id = str(uuid.uuid4())
    n = len(st.session_state.sessions) + 1
    st.session_state.sessions[new_id] = {"name": f"Session {n}", "history": []}
    st.session_state.active_session_id = new_id
    st.session_state.renaming_id = None


def switch_session(sid):
    st.session_state.active_session_id = sid
    st.session_state.renaming_id = None


def start_rename(sid):
    st.session_state.renaming_id = sid


def finish_rename(sid, new_name):
    if new_name.strip():
        st.session_state.sessions[sid]["name"] = new_name.strip()
    st.session_state.renaming_id = None


def delete_session(sid):
    del st.session_state.sessions[sid]
    if not st.session_state.sessions:
        add_new_session()
    else:
        st.session_state.active_session_id = next(iter(st.session_state.sessions))
    st.session_state.renaming_id = None


with st.sidebar:
    st.markdown("### 🎥 Sessions")

    if st.button("＋ New Session", use_container_width=True, key="new_session_btn"):
        add_new_session()

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:12px 0'>", unsafe_allow_html=True)

    for sid, sdata in st.session_state.sessions.items():
        is_active = sid == st.session_state.active_session_id
        is_renaming = st.session_state.renaming_id == sid

        if is_renaming:
            new_name = st.text_input(
                "Rename",
                value=sdata["name"],
                key=f"rename_input_{sid}",
                label_visibility="collapsed"
            )
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✓ Save", key=f"save_{sid}", use_container_width=True):
                    finish_rename(sid, new_name)
            with col2:
                if st.button("✗ Cancel", key=f"cancel_{sid}", use_container_width=True):
                    st.session_state.renaming_id = None
        else:
            cols = st.columns([6, 1, 1])
            with cols[0]:
                label = f"{'●' if is_active else '○'}  {sdata['name']}"
                hist_count = len(sdata["history"])
                if hist_count:
                    label += f" ({hist_count})"
                btn_type = "primary" if is_active else "secondary"
                if st.button(label, key=f"sess_{sid}", use_container_width=True, type=btn_type):
                    switch_session(sid)
            with cols[1]:
                if st.button("✏", key=f"edit_{sid}", help="Rename"):
                    start_rename(sid)
            with cols[2]:
                if len(st.session_state.sessions) > 1:
                    if st.button("🗑", key=f"del_{sid}", help="Delete"):
                        delete_session(sid)

    st.markdown("<hr style='border-color:rgba(255,255,255,0.08);margin:12px 0'>", unsafe_allow_html=True)
    total = sum(len(s["history"]) for s in st.session_state.sessions.values())
    st.caption(f"🗂 {len(st.session_state.sessions)} sessions · {total} summaries")


session = active_session()

st.markdown(f'<div class="main-header">🎥 {session["name"]}</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Paste a YouTube URL below to generate a summary.</div>', unsafe_allow_html=True)

col_url, col_btn = st.columns([5, 1])
with col_url:
    url_input = st.text_input(
        "YouTube URL",
        placeholder="https://www.youtube.com/watch?v=...",
        label_visibility="collapsed",
        key=f"url_input_{st.session_state.active_session_id}"
    )
with col_btn:
    summarize_clicked = st.button("Summarize ▶", use_container_width=True, type="primary")

if summarize_clicked:
    if not url_input.strip():
        st.warning("Please enter a YouTube URL.")
    else:
        with st.spinner("Extracting transcript & summarizing… This may take a moment."):
            entry = {
                "url": url_input.strip(),
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "short_summary": None,
                "key_takeaways": [],
                "detailed_summary": None,
                "error": None,
            }
            try:
                transcript = get_transcript(url_input)
                summary_data = summarize(transcript)
                entry["short_summary"] = summary_data.get("short_summary", "")
                entry["key_takeaways"] = summary_data.get("key_takeaways", [])
                entry["detailed_summary"] = summary_data.get("detailed_summary", "")
            except (InvalidYouTubeURLError, TranscriptNotAvailableError, APIError) as e:
                entry["error"] = str(e)
            except Exception as e:
                entry["error"] = f"Unexpected error: {str(e)}"

            session["history"].insert(0, entry)
            st.rerun()

st.markdown('<hr class="divider">', unsafe_allow_html=True)

if not session["history"]:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-state-icon">🎬</div>
        <p style="color:#4b5563;font-size:1rem;">No summaries yet in this session.<br>Paste a YouTube URL above to get started!</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f'<div class="history-label">📋 History — {len(session["history"])} item(s)</div>', unsafe_allow_html=True)

    for idx, entry in enumerate(session["history"]):
        if entry.get("error"):
            st.markdown(f"""
            <div class="history-card">
                <div class="card-header">
                    <a class="card-url" href="{entry['url']}" target="_blank">🔗 {entry['url']}</a>
                    <span class="card-timestamp">🕐 {entry['timestamp']}</span>
                </div>
                <div class="error-card">❌ {entry['error']}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            takeaways_html = "".join(
                f'<div class="takeaway-item"><span class="takeaway-bullet">›</span><span>{t}</span></div>'
                for t in entry.get("key_takeaways", [])
            )
            detailed = entry.get("detailed_summary", "")

            st.markdown(f"""
            <div class="history-card">
                <div class="card-header">
                    <a class="card-url" href="{entry['url']}" target="_blank">🔗 {entry['url']}</a>
                    <span class="card-timestamp">🕐 {entry['timestamp']}</span>
                </div>
                <span class="tag">Short Summary</span>
                <div class="short-summary-text">{entry.get('short_summary', '')}</div>
                <span class="tag">Key Takeaways</span>
                {takeaways_html}
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"📄 Detailed Summary — #{idx + 1}", expanded=False):
                st.write(detailed)
