import streamlit as st
from agents.base import AVAILABLE_MODELS, DEFAULT_MODEL
from agents.pipeline import PIPELINE_STEPS, PipelineAgent, run_pipeline
from utils.document_parser import parse_document
from utils.html_generator import generate_proposal_html

st.set_page_config(page_title="RFP Agent Suite", layout="wide")

for key, default in {
    "rfp_text": "",
    "knowledge_base": [],
    "step_outputs": {},
    "html_result": "",
    "pipeline_running": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# --- Sidebar ---
with st.sidebar:
    st.title("RFP Agent Suite")

    api_key = st.text_input("Groq API Key", type="password",
                             help="Free at console.groq.com")
    selected_model = st.selectbox("Model", AVAILABLE_MODELS,
                                  index=AVAILABLE_MODELS.index(DEFAULT_MODEL))

    st.divider()

    st.subheader("1. Upload RFP Document")
    rfp_file = st.file_uploader(
        "PDF, PPTX, or TXT",
        type=["pdf", "pptx", "ppt", "txt"],
        key="rfp_uploader",
    )
    if rfp_file:
        st.session_state.rfp_text = parse_document(rfp_file)
        st.success(f"Loaded: {rfp_file.name} ({len(st.session_state.rfp_text):,} chars)")

    st.subheader("2. Knowledge Base (Optional)")
    kb_files = st.file_uploader(
        "Past proposals, company docs",
        type=["pdf", "pptx", "ppt", "txt", "md", "csv"],
        accept_multiple_files=True,
        key="kb_uploader",
    )
    if kb_files:
        st.session_state.knowledge_base = [parse_document(f) for f in kb_files]
        st.success(f"Loaded {len(kb_files)} document(s)")

    st.divider()

    st.subheader("3. Run Mode")
    mode = st.radio("Mode", ["Full Pipeline (Auto)", "Single Agent"], horizontal=True)

    selected_step = None
    if mode == "Single Agent":
        step_names = [s["name"] for s in PIPELINE_STEPS]
        selected_step = st.selectbox("Choose Agent", step_names)
        step_cfg = next(s for s in PIPELINE_STEPS if s["name"] == selected_step)
        st.info(step_cfg["description"])

    st.divider()
    proposal_title = st.text_input("Proposal Title", value="Proposal Response")

    if st.button("Clear All Outputs"):
        st.session_state.step_outputs = {}
        st.session_state.html_result = ""
        st.rerun()

# --- Pipeline Steps Reference ---
col_main, col_side = st.columns([3, 1])

with col_side:
    st.markdown("### Pipeline Steps")
    for i, step in enumerate(PIPELINE_STEPS, 1):
        done = step["name"] in st.session_state.step_outputs
        icon = "✅" if done else f"**{i}.**"
        with st.expander(f"{icon} {step['name']}"):
            st.write(step["description"])
            if done:
                st.caption("Output generated")

# --- Main Area ---
with col_main:
    st.markdown("### Generate Proposal")

    user_prompt = st.text_area(
        "Describe what you need or add specific instructions:",
        placeholder="e.g. Generate a complete proposal response for this RFP. Focus on our cloud migration expertise.",
        height=100,
    )

    run_btn = st.button("Run", type="primary", use_container_width=True)

    if run_btn:
        if not api_key:
            st.error("Enter your Groq API key in the sidebar.")
            st.stop()
        if not st.session_state.rfp_text:
            st.error("Upload an RFP document first.")
            st.stop()
        if not user_prompt.strip():
            st.error("Enter instructions above.")
            st.stop()

        if mode == "Single Agent" and selected_step:
            # --- Single Agent Mode ---
            step_cfg = next(s for s in PIPELINE_STEPS if s["name"] == selected_step)
            agent = PipelineAgent(api_key, selected_model, step_cfg)

            context = f"RFP DOCUMENT:\n{st.session_state.rfp_text}"
            if st.session_state.knowledge_base:
                context += "\n\nKNOWLEDGE BASE:\n" + "\n---\n".join(
                    st.session_state.knowledge_base
                )
            if st.session_state.step_outputs:
                prev = "\n\n".join(
                    f"--- {n} ---\n{t}" for n, t in st.session_state.step_outputs.items()
                )
                context += f"\n\nPREVIOUS STEPS OUTPUT:\n{prev}"

            with st.spinner(f"Running {selected_step}..."):
                prompt = f"{user_prompt}\n\nGenerate the '{selected_step}' section."
                result = agent.run(prompt, context)

            st.session_state.step_outputs[selected_step] = result
            st.rerun()

        else:
            # --- Full Pipeline Mode ---
            progress = st.progress(0, text="Starting pipeline...")
            step_containers = {}
            for step in PIPELINE_STEPS:
                step_containers[step["name"]] = st.empty()

            results = {}
            rfp_ctx = f"RFP DOCUMENT:\n{st.session_state.rfp_text}"
            kb_ctx = (
                "\n---\n".join(st.session_state.knowledge_base)
                if st.session_state.knowledge_base
                else ""
            )

            for i, step in enumerate(PIPELINE_STEPS):
                pct = int((i / len(PIPELINE_STEPS)) * 100)
                progress.progress(pct, text=f"Step {i+1}/7: {step['name']}...")

                agent = PipelineAgent(api_key, selected_model, step)

                context = rfp_ctx
                if kb_ctx:
                    context += f"\n\nKNOWLEDGE BASE:\n{kb_ctx}"
                if results:
                    prev = "\n\n".join(
                        f"--- {n} ---\n{t}" for n, t in results.items()
                    )
                    context += f"\n\nPREVIOUS STEPS OUTPUT:\n{prev}"

                prompt = f"{user_prompt}\n\nGenerate the '{step['name']}' section for this proposal."
                output = agent.run(prompt, context)
                results[step["name"]] = output

                with step_containers[step["name"]].expander(
                    f"Step {i+1}: {step['name']}", expanded=(i == len(PIPELINE_STEPS) - 1)
                ):
                    st.markdown(output)

            progress.progress(100, text="Pipeline complete!")
            st.session_state.step_outputs = results

            html = generate_proposal_html(results, proposal_title)
            st.session_state.html_result = html
            st.success("All 7 steps complete. Download your HTML proposal below.")

    # --- Display existing outputs ---
    if st.session_state.step_outputs and not run_btn:
        for i, step in enumerate(PIPELINE_STEPS, 1):
            name = step["name"]
            if name in st.session_state.step_outputs:
                with st.expander(f"Step {i}: {name}", expanded=False):
                    st.markdown(st.session_state.step_outputs[name])

    # --- HTML Preview & Download ---
    if st.session_state.step_outputs:
        st.divider()

        if not st.session_state.html_result:
            st.session_state.html_result = generate_proposal_html(
                st.session_state.step_outputs, proposal_title
            )

        col_dl1, col_dl2 = st.columns(2)
        with col_dl1:
            st.download_button(
                label="Download Proposal as HTML",
                data=st.session_state.html_result,
                file_name=f"{proposal_title.replace(' ', '_')}.html",
                mime="text/html",
                type="primary",
                use_container_width=True,
            )
        with col_dl2:
            if st.button("Preview HTML", use_container_width=True):
                st.session_state["show_preview"] = not st.session_state.get("show_preview", False)

        if st.session_state.get("show_preview"):
            st.components.v1.html(st.session_state.html_result, height=800, scrolling=True)
