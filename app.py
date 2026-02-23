import streamlit as st
from agents import AGENTS, AnalystAgent, ResearcherAgent, DrafterAgent, ReviewerAgent
from agents.base import AVAILABLE_MODELS, DEFAULT_MODEL
from utils.document_parser import parse_document

st.set_page_config(page_title="RFP Agent Suite", layout="wide")

AGENT_LIST = list(AGENTS.keys())

# --- Session State Initialization ---
for key, default in {
    "messages": [],
    "rfp_text": "",
    "knowledge_base": [],
    "agent_outputs": {},
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Sidebar ---
with st.sidebar:
    st.title("RFP Agent Suite")

    api_key = st.text_input("Groq API Key", type="password",
                             help="Get a free key at console.groq.com")

    selected_model = st.selectbox("Model", AVAILABLE_MODELS,
                                  index=AVAILABLE_MODELS.index(DEFAULT_MODEL))

    st.divider()

    st.subheader("1. Upload RFP Document")
    rfp_file = st.file_uploader(
        "Upload your RFP (PDF, PPTX, TXT)",
        type=["pdf", "pptx", "ppt", "txt"],
        key="rfp_uploader",
    )
    if rfp_file:
        st.session_state.rfp_text = parse_document(rfp_file)
        st.success(f"Loaded: {rfp_file.name} ({len(st.session_state.rfp_text):,} chars)")

    st.subheader("2. Upload Knowledge Base (Optional)")
    kb_files = st.file_uploader(
        "Past proposals, company docs, policies",
        type=["pdf", "pptx", "ppt", "txt", "md", "csv"],
        accept_multiple_files=True,
        key="kb_uploader",
    )
    if kb_files:
        st.session_state.knowledge_base = [parse_document(f) for f in kb_files]
        st.success(f"Loaded {len(kb_files)} knowledge base document(s)")

    st.divider()

    st.subheader("3. Select Mode")
    mode = st.radio("Run Mode", ["Auto Mode", "Manual Mode"], horizontal=True)

    selected_agent = None
    if mode == "Manual Mode":
        selected_agent = st.selectbox("Choose Agent", AGENT_LIST)
        agent_cls = AGENTS[selected_agent]
        st.info(f"**{agent_cls.name}**: {agent_cls.description}")
    else:
        st.info("Auto mode chains all 4 agents: Analyst -> Researcher -> Drafter -> Reviewer")

    st.divider()
    if st.button("Clear Chat History"):
        st.session_state.messages = []
        st.session_state.agent_outputs = {}
        st.rerun()

# --- Agent Info Panel ---
col1, col2 = st.columns([3, 1])

with col2:
    st.markdown("### Agents")
    for agent_name, agent_cls in AGENTS.items():
        with st.expander(agent_name):
            st.write(agent_cls.description)

# --- Main Chat Area ---
with col1:
    st.markdown("### Chat")

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("Ask about the RFP or give an instruction..."):
        if not api_key:
            st.error("Enter your Groq API key in the sidebar (free at console.groq.com).")
            st.stop()
        if not st.session_state.rfp_text:
            st.error("Upload an RFP document first.")
            st.stop()

        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if mode == "Manual Mode" and selected_agent:
                # --- Manual: Run a single agent ---
                agent = AGENTS[selected_agent](api_key, selected_model)
                context = f"RFP DOCUMENT:\n{st.session_state.rfp_text}"
                if st.session_state.knowledge_base:
                    context += "\n\nKNOWLEDGE BASE:\n" + "\n---\n".join(
                        st.session_state.knowledge_base
                    )

                with st.spinner(f"Running {selected_agent}..."):
                    response = agent.run(prompt, context)
                st.markdown(response)

            else:
                # --- Auto Mode: Chain all 4 agents ---
                st.markdown("**Running Auto Mode Pipeline...**")
                rfp_ctx = f"RFP DOCUMENT:\n{st.session_state.rfp_text}"
                kb_ctx = (
                    "\n---\n".join(st.session_state.knowledge_base)
                    if st.session_state.knowledge_base
                    else "No knowledge base documents uploaded."
                )

                # Step 1: Analyst
                with st.spinner("Step 1/4 - The Analyst: Extracting requirements..."):
                    analyst = AnalystAgent(api_key, selected_model)
                    analyst_result = analyst.run(prompt, rfp_ctx)
                with st.expander("Step 1: Analyst Output", expanded=True):
                    st.markdown(analyst_result)
                st.session_state.agent_outputs["analyst"] = analyst_result

                # Step 2: Researcher
                with st.spinner("Step 2/4 - The Researcher: Finding relevant facts..."):
                    researcher = ResearcherAgent(api_key, selected_model)
                    researcher_result = researcher.run(
                        f"Find facts relevant to these requirements:\n{analyst_result}",
                        f"KNOWLEDGE BASE:\n{kb_ctx}",
                    )
                with st.expander("Step 2: Researcher Output", expanded=True):
                    st.markdown(researcher_result)
                st.session_state.agent_outputs["researcher"] = researcher_result

                # Step 3: Drafter
                with st.spinner("Step 3/4 - The Drafter: Writing proposal response..."):
                    drafter = DrafterAgent(api_key, selected_model)
                    drafter_result = drafter.run(
                        f"Write a proposal response.\nREQUIREMENTS:\n{analyst_result}\n\nFACTS:\n{researcher_result}",
                        rfp_ctx,
                    )
                with st.expander("Step 3: Drafter Output", expanded=True):
                    st.markdown(drafter_result)
                st.session_state.agent_outputs["drafter"] = drafter_result

                # Step 4: Reviewer
                with st.spinner("Step 4/4 - The Reviewer: Checking compliance..."):
                    reviewer = ReviewerAgent(api_key, selected_model)
                    reviewer_result = reviewer.run(
                        f"Review this draft:\nDRAFT:\n{drafter_result}\n\nREQUIREMENTS:\n{analyst_result}",
                        rfp_ctx,
                    )
                with st.expander("Step 4: Reviewer Output", expanded=True):
                    st.markdown(reviewer_result)
                st.session_state.agent_outputs["reviewer"] = reviewer_result

                response = "Pipeline complete. All 4 agents have processed your request. Expand each step above to review the outputs."
                st.success(response)

            st.session_state.messages.append({"role": "assistant", "content": response})
