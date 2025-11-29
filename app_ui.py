import streamlit as st
import fitz  # PyMuPDF for PDF preview and page selection (new added feature)
from app import LocalRAGApp  # importing app.py

st.set_page_config(page_title="Local RAG QA", layout="wide", page_icon="")

# Styles
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Merriweather:wght@400;600;700&display=swap');

    /* Global layout & typography */
    .stApp, body {
        background-color: #FDFCF8;
        color: #2D2D2D;
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    }

    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 900px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #F5F3FF !important;
        border-right: none !important;
        box-shadow: none !important;
    }

    .sidebar .sidebar-content {
        padding-top: 2rem;
    }

    /* Headings */
    h1, h2, h3, h4, h5 {
        font-family: 'Merriweather', 'Georgia', serif;
        letter-spacing: -0.01em;
        color: #2D2D2D;
    }

    /* Body text */
    p, div, span, label {
        font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        line-height: 1.6;
    }

    .section-header {
        display: flex;
        align-items: center;
        gap: 0.6rem;
        margin-bottom: 0.75rem;
    }

    .section-icon {
        width: 28px;
        height: 28px;
        border-radius: 999px;
        background: #7C3AED;
        display: flex;
        align-items: center;
        justify-content: center;
        color: #FDFCF8;
        font-weight: 600;
        font-size: 0.8rem;
    }

    .section-title-text {
        font-size: 0.9rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #4A4A4A;
    }

    /* Floating input cards */
    .stTextInput>div>div>input,
    .stTextArea>div>textarea {
        background-color: #FFFFFF;
        color: #2D2D2D;
        border-radius: 10px;
        border: 1px solid rgba(0, 0, 0, 0.04);
        padding: 0.7rem 0.9rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
    }

    .stTextArea>div>textarea {
        min-height: 160px;
    }

    .stTextInput>div>div>input:focus,
    .stTextArea>div>textarea:focus {
        border-color: rgba(124, 58, 237, 0.7);
        box-shadow: 0 0 0 1px rgba(124, 58, 237, 0.7);
        outline: none;
    }

    /* Soft buttons */
    .stButton>button, .stDownloadButton>button {
        border-radius: 8px;
        border: 1px solid rgba(124, 58, 237, 0.4);
        background: #FDFCF8;
        color: #7C3AED;
        font-weight: 500;
        padding: 0.45rem 1.2rem;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
        transition: background 0.15s ease, color 0.15s ease, box-shadow 0.15s ease;
    }

    .stButton>button:hover, .stDownloadButton>button:hover {
        background: #7C3AED;
        color: #FDFCF8;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }

    /* Chat response block */
    .response-block {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 1.25rem 1.5rem;
        box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
        margin-top: 1rem;
    }

    .response-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.16em;
        color: #8A8A8A;
        margin-bottom: 0.5rem;
    }

    .response-content {
        font-size: 0.95rem;
        line-height: 1.7;
        color: #2D2D2D;
    }

    .response-content strong {
        color: #7C3AED;
        font-weight: 600;
    }

    .response-content ul {
        list-style-type: none;
        padding-left: 0;
        margin: 0.25rem 0 0 0;
    }

    .response-content li {
        border-bottom: 1px solid #EEEEEE;
        padding: 8px 0;
    }

    .response-content hr {
        border: none;
        border-top: 1px dashed #7C3AED;
        opacity: 0.3;
        margin: 0.75rem 0;
    }

    .source-pill {
        display: inline-block;
        padding: 0.15rem 0.6rem;
        border-radius: 999px;
        background: rgba(124, 58, 237, 0.08);
        color: #7C3AED;
        font-size: 0.75rem;
        margin-right: 0.35rem;
        margin-top: 0.15rem;
        border: 1px solid rgba(124, 58, 237, 0.35);
    }

    /* Welcome header */
    .welcome-hero {
        text-align: center;
        margin-bottom: 2.5rem;
    }

    .welcome-hero h1 {
        margin-bottom: 0.6rem;
        font-size: 2rem;
    }

    .welcome-hero p {
        max-width: 640px;
        margin: 0 auto;
        color: #555555;
        font-size: 0.98rem;
    }

    /* Hide default Streamlit chrome */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="welcome-hero">
        <h1>Local RAG Document QA</h1>
        <p>
            Upload a document, let the model read it carefully, and then explore it through
            calm, conversational questions and focused summaries.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)
app = LocalRAGApp()
data = None

with st.sidebar:
    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">U</div>
            <div class="section-title-text">Upload PDF</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    uploaded_file = st.file_uploader("Choose a PDF", type=["pdf"])

    if uploaded_file:
        with open("temp.pdf", "wb") as f:
            f.write(uploaded_file.read())
        data = app.load_document("temp.pdf")

        with st.spinner("Processing your document..."):
            app.create_vector_db(data)
            app.setup_retrieval_chain()

        st.success("PDF processed and ready!")

if uploaded_file:
    st.markdown("---")
    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">Q</div>
            <div class="section-title-text">Ask Questions</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Type your question below", expanded=True):
        question = st.text_input("Ask a question about your document")

    if uploaded_file and question:
        with st.spinner("Searching the document..."):
            placeholder = st.empty()
            full_text = ""
            for chunk in app.chain.stream(question):
                full_text += chunk
                placeholder.markdown(
                    f"""
                    <div class="response-block">
                        <div class="response-label">Answer</div>
                        <div class="response-content">{full_text}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        # After streaming finishes, fetch sources and append them as footnote-style pills
        source_html = ""
        try:
            docs = app.get_sources(question)
            pages = sorted(
                {
                    doc.metadata.get("page")
                    for doc in docs
                    if isinstance(doc.metadata.get("page"), int)
                }
            )
            if pages:
                pills = " ".join(
                    f"<span class='source-pill'>Page {p + 1}</span>" for p in pages
                )
                source_html = f"""
                <div class="response-label" style="margin-top: 1rem;">Sources</div>
                <div>{pills}</div>
                """
        except Exception as e:
            # In case of any retrieval error, just skip showing sources
            source_html = ""

        final_html = f"""
        <div class="response-block">
            <div class="response-label">Answer</div>
            <div class="response-content">{full_text}</div>
            {source_html}
        </div>
        """
        placeholder.markdown(final_html, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">S</div>
            <div class="section-title-text">Section Summaries</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Generate a simplified summary of the entire PDF"):
        if st.button("Summarize PDF Sections"):
            with st.spinner("Summarizing..."):
                app.summarize_sections(data)
                try:
                    with open("summaries.txt", "r", encoding="utf-8") as f:
                        summaries = f.read()
                    st.success("Summary generated!")
                    st.text_area("Summaries", summaries, height=400)

                    st.download_button(
                        label="Download Summary (.txt)",
                        data=summaries,
                        file_name="resume_sections.txt",
                        mime="text/plain"
                    )
                except FileNotFoundError:
                    st.error("Something went wrong.")

    st.markdown("---")
    st.markdown(
        """
        <div class="section-header">
            <div class="section-icon">P</div>
            <div class="section-title-text">Selected Pages</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander("Preview & Select Pages"):
        doc = fitz.open("temp.pdf")
        num_pages = len(doc)
        st.markdown(f"**Total pages:** {num_pages}")

        page_selection = st.multiselect(
            "Select page numbers to summarize (starting from 1):",
            options=list(range(1, num_pages + 1))
        )

        if page_selection and st.button("Summarize Selected Pages"):
            with st.spinner("Generating summary for selected pages..."):
                summaries = app.summarize_selected_pages("temp.pdf", [p - 1 for p in page_selection])
                full_summary = "\n\n".join(summaries)
                st.success("Summary generated for selected pages!")
                st.text_area("Summaries of Selected Pages", full_summary, height=400)

                st.download_button(
                    "Download Selected Summary",
                    full_summary,
                    file_name="selected_summary.txt"
                )
        elif not page_selection:
            st.info("Please select at least one page.")