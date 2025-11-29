import os
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import OllamaEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.chat_models import ChatOllama
from langchain_core.runnables import RunnablePassthrough
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
import time

# Function to push metrics to Pushgateway
def push_metrics(requests, time_taken, avg_len):
    registry = CollectorRegistry()
    request_count = Gauge('rag_request_count', 'Number of processed PDF summaries', registry=registry)
    processing_time = Gauge('rag_processing_seconds', 'Processing time for the last request', registry=registry)
    summary_length = Gauge('rag_summary_length', 'Average summary length', registry=registry)

    request_count.set(requests)
    processing_time.set(time_taken)
    summary_length.set(avg_len)

    raw_gateway = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")
    gateway = raw_gateway.replace("http://", "").replace("https://", "")

    try:
        push_to_gateway(gateway, job='localrag_app', registry=registry)
        print("✅ Metrics pushed successfully to Pushgateway.")
    except Exception as e:
        print(f"⚠️ Could not push metrics: {e}")


class LocalRAGApp:
    def __init__(self):
        self.vector_db = None
        self.chain = None
        self.local_model = "deepseek-r1:1.5b"

    def install_dependencies(self):
        """Install required dependencies"""
        print("Installing required packages...")
        os.system("pip install --quiet unstructured langchain")
        os.system("pip install --quiet \"unstructured[all-docs]\"")
        os.system("pip install --quiet langchain-community")
        os.system("pip install --quiet pymupdf")
        os.system("pip install --quiet chromadb")
        os.system("pip install --quiet langchain-text-splitters")
        os.system("ollama pull  znbang/bge:small-en-v1.5-q8_0")
        os.system("ollama pull deepseek-r1:1.5b ")
        print("Dependencies installed successfully.")

    def load_document(self, file_path):
        """Load and process PDF document"""
        print(f"Loading document: {file_path}")
        loader = PyMuPDFLoader(file_path)
        data = loader.load()
        print(f"Document loaded successfully. Pages: {len(data)}")
        return data

    def create_vector_db(self, data):
        """Create vector database from document chunks"""
        print("Creating vector database")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=7500, chunk_overlap=100)
        chunks = text_splitter.split_documents(data)

        # Add to vector database
        self.vector_db = Chroma.from_documents(
            documents=chunks, 
            embedding=OllamaEmbeddings(model="znbang/bge:small-en-v1.5-q8_0", show_progress=False),
            collection_name="local-rag"
        )
        print("Vector database created successfully.")

    def setup_retrieval_chain(self):
        """Set up the retrieval and response chain"""
        print("Setting up retrieval chain")

        llm = ChatOllama(model=self.local_model)

        QUERY_PROMPT = PromptTemplate(
            input_variables=["question"],
            template="""You are an AI assistant with access to specific document context. 
            Answer the question strictly based on the provided context below. 
            Do not use any external knowledge. If the answer is not in the context, simply say: 
            I could not find the answer in the document
            Original question: {question}""",
        )

        retriever = self.vector_db.as_retriever()

        template = """Answer the question based ONLY on the following context:
        {context}
        Question: {question}
        """

        prompt = ChatPromptTemplate.from_template(template)

        self.chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | prompt
            | llm
            | StrOutputParser()
        )
        print("Retrieval chain setup complete.")

    def summarize_sections(self, documents):
        """Résumé clair par section, enregistré dans summaries.txt + envoi de métriques à Prometheus Pushgateway"""
        print("Génération des résumés de sections...")
        llm = ChatOllama(model=self.local_model)

        registry = CollectorRegistry()
        summary_time = Gauge('summary_generation_seconds', 'Time spent generating summaries', registry=registry)
        summary_chunks = Gauge('summary_chunks_total', 'Total number of chunks processed', registry=registry)
        success_chunks = Gauge('summary_chunks_successful', 'Number of successfully summarized chunks', registry=registry)
        failed_chunks = Gauge('summary_chunks_failed', 'Number of chunks that failed summarization', registry=registry)

        start_time = time.time()
        total_chunks = 0
        successful = 0
        failed = 0

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
        chunks = text_splitter.split_documents(documents)

        prompt_template = ChatPromptTemplate.from_template(
            "Voici un extrait d'un document :\n\n{content}\n\nFais un résumé clair, simple à comprendre et concis. "
            "Formate la sortie comme une liste Markdown propre, avec des puces de premier niveau uniquement (pas de puces imbriquées)."
        )

        chain = (
            {"content": lambda x: x.page_content}
            | prompt_template
            | llm
            | StrOutputParser()
        )

        with open("summaries.txt", "w", encoding="utf-8") as f:
            for chunk in chunks:
                total_chunks += 1
                try:
                    summary = chain.invoke(chunk)
                    if summary.strip():
                        successful += 1
                        f.write(summary + "\n\n" + "-" * 60 + "\n\n")
                except Exception as e:
                    failed += 1
                    print(f"Erreur sur un chunk : {e}")

        duration = time.time() - start_time
        summary_time.set(duration)
        summary_chunks.set(total_chunks)
        success_chunks.set(successful)
        failed_chunks.set(failed)

        raw_gateway = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")
        gateway = raw_gateway.replace("http://", "").replace("https://", "")

        try:
            push_to_gateway(gateway, job='localrag_summary_job', registry=registry)
            print("✅ Metrics pushed successfully to Prometheus Pushgateway!")
        except Exception as e:
            print(f"⚠️ Could not push metrics: {e}")

        print("Résumé enregistré dans summaries.txt")

    def get_sources(self, question):
        """Retrieve source documents for a given question"""
        if not self.vector_db:
            return []
        try:
            retriever = self.vector_db.as_retriever()
            docs = retriever.invoke(question)
            return docs
        except Exception as e:
            print(f"Error retrieving sources: {e}")
            return []

    def summarize_selected_pages(self, file_path, page_numbers):
        """Summarize specific pages from the PDF and save to summaries.txt"""

        import fitz  # PyMuPDF

        print(f"Summarizing selected pages: {page_numbers}")
        llm = ChatOllama(model=self.local_model)

        with fitz.open(file_path) as doc:
            selected_texts = []
            for page_num in page_numbers:
                if 0 <= page_num < len(doc):
                    text = doc[page_num].get_text()
                    selected_texts.append(text)

        summaries = []
        prompt_template = ChatPromptTemplate.from_template(
            "Voici un extrait d'un document :\n\n{content}\n\nFais un résumé clair, simple à comprendre et concis. "
            "Formate la sortie comme une liste Markdown propre, avec des puces de premier niveau uniquement (pas de puces imbriquées)."
    )

        chain = (
            {"content": lambda x: x}
            | prompt_template
            | llm
            | StrOutputParser()
    )

        with open("summaries.txt", "w", encoding="utf-8") as f:
            for page_text in selected_texts:
                try:
                    summary = chain.invoke(page_text)
                    if summary.strip():
                        f.write(summary + "\n\n" + "-" * 60 + "\n\n")
                        summaries.append(summary)
                except Exception as e:
                    print(f"Error summarizing a page: {e}")
    
        return summaries
 
    
    def query(self, question):
        """Query the RAG system"""
        if not self.chain:
            print("Error: Please load a document and setup the chain first.")
            return
        
        print("Processing your question...")
        result = self.chain.invoke(question)
        print("\nResponse:")
        print(result)
    

    def cleanup(self):
        """Clean up resources"""
        if self.vector_db:
            self.vector_db.delete_collection()
            print("Vector database collection deleted.")

def main():
    app = LocalRAGApp()
    
    print("\nLocal RAG Application with Ollama")
    print("--------------------------------")
    
    # Check if dependencies are installed correctly
    install = input("Do you want to install required dependencies? (y/n): ").lower()
    if install == 'y':
        app.install_dependencies()
    
    
    file_path = input("\nEnter the path to your PDF document: ")
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        return
    
    data = app.load_document(file_path)
    app.summarize_sections(data)  # Génére et exporte les résumés

    app.create_vector_db(data)
    app.setup_retrieval_chain()
    
    # Interactive query loop
    print("\nEnter your questions about the document (type 'exit' to quit):")
    while True:
        question = input("\nQuestion: ")
        if question.lower() == 'exit':
            break
        app.query(question)
    
    # Cleanup after finishing everything up
    app.cleanup()
    print("\nApplication closed.")


if __name__ == "__main__":
    main()