import streamlit as st
import time
from agent import run_agent
from report import save_report
from report import generate_pdf_bytes

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide"
)

# --- Custom CSS ---
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        background: linear-gradient(90deg, #378ADD, #4ec9b0);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-caption {
        color: #888;
        font-size: 0.95rem;
        margin-top: 0;
        margin-bottom: 1.5rem;
    }
    .step-complete {
        background: #1A2F1A;
        border-left: 3px solid #4ec9b0;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 14px;
        color: #4ec9b0;
    }
    .step-active {
        background: #1A1F2F;
        border-left: 3px solid #378ADD;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 14px;
        color: #378ADD;
    }
    .step-pending {
        background: #1A1C24;
        border-left: 3px solid #444;
        padding: 10px 16px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 14px;
        color: #666;
    }
    .report-meta {
        color: #888;
        font-size: 13px;
        margin-bottom: 1rem;
    }
    .source-link {
        background: #1A1F2F;
        border: 1px solid #378ADD44;
        border-radius: 6px;
        padding: 6px 12px;
        margin-bottom: 6px;
        font-size: 13px;
    }
</style>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/microscope.png", width=60)
    st.markdown("### AI Research Assistant")
    st.caption("Powered by Groq (Llama) + DuckDuckGo")
    st.divider()

    st.markdown("**How it works:**")
    st.markdown("""
    1. 🔍 Searches DuckDuckGo
    2. 📄 Reads top sources
    3. 🧠 Synthesizes with Llama
    4. 📝 Generates report
    """)
    st.divider()

    st.markdown("**Recent Topics**")
    if "history" not in st.session_state:
        st.session_state.history = []
    if st.session_state.history:
        for t in reversed(st.session_state.history[-5:]):
            st.markdown(f"• {t}")
    else:
        st.caption("No recent topics yet.")

# --- Main header ---
st.markdown('<p class="main-header">🔬 AI Research Assistant</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-caption">Enter any topic and the agent will autonomously research and compile a report.</p>', unsafe_allow_html=True)

# --- Input ---
with st.form(key="research_form"):
    col1, col2 = st.columns([5, 1])
    with col1:
        topic = st.text_input(
            "",
            placeholder="e.g. artificial intelligence in healthcare",
            label_visibility="collapsed"
        )
    with col2:
        run_btn = st.form_submit_button("🔍 Research", type="primary", use_container_width=True)

st.divider()

if run_btn:
    if not topic.strip():
        st.warning("⚠️ Please enter a topic first!")
    else:
        if topic not in st.session_state.history:
            st.session_state.history.append(topic)

        # --- Live progress animation ---
        st.markdown("#### ⚙️ Agent Progress")
        progress_container = st.container()

        with progress_container:
            s1 = st.empty()
            s2 = st.empty()
            s3 = st.empty()
            s4 = st.empty()

            # Step 1
            s1.markdown('<div class="step-active">🔍 Searching DuckDuckGo...</div>', unsafe_allow_html=True)
            s2.markdown('<div class="step-pending">📄 Reading pages...</div>', unsafe_allow_html=True)
            s3.markdown('<div class="step-pending">🧠 Synthesizing with Llama...</div>', unsafe_allow_html=True)
            s4.markdown('<div class="step-pending">📝 Compiling report...</div>', unsafe_allow_html=True)

            overall = st.progress(0, text="Starting research...")

            # Run agent
            overall.progress(10, text="Agent is working...")

            # Simulate step transitions while agent runs
            def update_steps(step):
                if step >= 1:
                    s1.markdown('<div class="step-complete">✅ Web search complete</div>', unsafe_allow_html=True)
                if step >= 2:
                    s2.markdown('<div class="step-active">📄 Reading pages...</div>', unsafe_allow_html=True)
                if step >= 3:
                    s2.markdown('<div class="step-complete">✅ Pages read</div>', unsafe_allow_html=True)
                    s3.markdown('<div class="step-active">🧠 Synthesizing with Llama...</div>', unsafe_allow_html=True)
                if step >= 4:
                    s3.markdown('<div class="step-complete">✅ Synthesis complete</div>', unsafe_allow_html=True)
                    s4.markdown('<div class="step-active">📝 Compiling report...</div>', unsafe_allow_html=True)

            update_steps(1)
            overall.progress(25, text="Searching the web...")
            time.sleep(0.5)

            update_steps(2)
            overall.progress(50, text="Reading sources...")
            time.sleep(0.5)

            update_steps(3)
            overall.progress(75, text="Synthesizing information...")

            report_content, sources = run_agent(topic)

            update_steps(4)
            overall.progress(100, text="Report ready!")
            time.sleep(0.3)

            s1.markdown('<div class="step-complete">✅ Web search complete</div>', unsafe_allow_html=True)
            s2.markdown('<div class="step-complete">✅ Pages read</div>', unsafe_allow_html=True)
            s3.markdown('<div class="step-complete">✅ Synthesis complete</div>', unsafe_allow_html=True)
            s4.markdown('<div class="step-complete">✅ Report compiled</div>', unsafe_allow_html=True)
            overall.progress(100, text="✅ Done!")

        st.divider()

        # --- Report ---
        st.markdown("#### 📄 Research Report")

        # Word count meta
        word_count = len(report_content.split())
        read_time = max(1, round(word_count / 200))
        st.markdown(f'<p class="report-meta">📊 {word_count} words &nbsp;·&nbsp; ⏱️ ~{read_time} min read &nbsp;·&nbsp; 🔗 {len(sources)} sources</p>', unsafe_allow_html=True)

        st.markdown(report_content)

        # --- Sources ---
        if sources:
            st.divider()
            st.markdown("#### 🔗 Sources")
            for i, url in enumerate(sources, 1):
                st.markdown(f'<div class="source-link">🔗 <a href="{url}" target="_blank">{url}</a></div>', unsafe_allow_html=True)

        # --- Download ---
        st.divider()
        full_report = report_content
        if sources:
            full_report += "\n\n---\n**Sources:**\n"
            for i, url in enumerate(sources, 1):
                full_report += f"{i}. {url}\n"

        filepath = save_report(topic, full_report)

        pdf_bytes = generate_pdf_bytes(topic, report_content, sources)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.download_button(
                label="⬇️ Download .txt",
                data=full_report,
                file_name=f"{topic.replace(' ', '_')}_report.txt",
                mime="text/plain",
                use_container_width=True
            )
        with col2:
            st.download_button(
                label="⬇️ Download PDF",
                data=pdf_bytes,
                file_name=f"{topic.replace(' ', '_')}_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with col3:
            st.success(f"✅ Saved")