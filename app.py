import streamlit as st
from agent import run_agent
from report import save_report

st.set_page_config(
    page_title="AI Research Assistant",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 AI Research Assistant Agent")
st.caption("Powered by Groq (Llama) + DuckDuckGo")

st.divider()

# --- Sidebar ---
with st.sidebar:
    st.header("About")
    st.info(
        "This agent autonomously researches any topic by:\n\n"
        "1. 🔍 Searching the web\n"
        "2. 📄 Reading sources\n"
        "3. 📝 Compiling a report"
    )
    st.header("Recent Topics")
    if "history" not in st.session_state:
        st.session_state.history = []
    if st.session_state.history:
        for t in reversed(st.session_state.history[-5:]):
            st.markdown(f"- {t}")
    else:
        st.caption("No recent topics yet.")

# --- Main area ---
topic = st.text_input(
    "Enter a research topic",
    placeholder="e.g. artificial intelligence in healthcare"
)

run_btn = st.button("🔍 Research", type="primary")

if run_btn:
    if not topic.strip():
        st.warning("Please enter a topic first!")
    else:
        # Add to history
        if topic not in st.session_state.history:
            st.session_state.history.append(topic)

        # Progress steps
        st.subheader("Agent Progress")
        step1 = st.status("Searching the web...", expanded=True)
        step2 = st.status("Reading pages...", expanded=False)
        step3 = st.status("Compiling report...", expanded=False)

        with step1:
            st.write("Calling DuckDuckGo search...")

        # Run the agent
        with st.spinner("Agent is working..."):
            report_content, sources = run_agent(topic)

        step1.update(label="✅ Web search complete", state="complete")
        step2.update(label="✅ Pages read", state="complete")
        step3.update(label="✅ Report compiled", state="complete")

        st.divider()

        # --- Report output ---
        st.subheader("📄 Research Report")
        st.markdown(report_content)

        # --- Sources ---
        if sources:
            st.divider()
            st.subheader("🔗 Sources")
            for i, url in enumerate(sources, 1):
                st.markdown(f"{i}. [{url}]({url})")

        # --- Download ---
        st.divider()
        full_report = report_content
        if sources:
            full_report += "\n\n---\n**Sources:**\n"
            for i, url in enumerate(sources, 1):
                full_report += f"{i}. {url}\n"

        filepath = save_report(topic, full_report)

        st.download_button(
            label="⬇️ Download Report (.txt)",
            data=full_report,
            file_name=f"{topic.replace(' ', '_')}_report.txt",
            mime="text/plain"
        )

        st.success(f"✅ Report also saved to: {filepath}")