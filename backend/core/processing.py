# backend/core/processing.py
import requests
import pypdf
import io
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

class DocumentProcessor:
    def __init__(self, groq_api_key: str):
        # Initialize the LLM with Groq for fast responses (low latency)
        self.llm = ChatGroq(model="llama3-8b-8192", groq_api_key=groq_api_key)
        
        # Use a reliable open-source model for embeddings
        self.embedding_model = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        # Define the prompt template for the LLM
        # This instructs the LLM to base its answer only on the provided context
        self.prompt = ChatPromptTemplate.from_template(
            """
            Answer the user's question accurately and concisely based ONLY on the following context.
            If the information is not in the context, say "Information not found in the document."
            
            Context:
            {context}
            
            Question:
            {input}
            """
        )

    def _load_and_extract_text(self, url: str) -> str:
        """Downloads a PDF from a URL and extracts its text."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            pdf_file = io.BytesIO(response.content)
            reader = pypdf.PdfReader(pdf_file)
            text = "".join(page.extract_text() for page in reader.pages)
            return text
        except requests.RequestException as e:
            raise ValueError(f"Failed to download document: {e}")
        except Exception as e:
            raise ValueError(f"Failed to parse PDF: {e}")

    def create_vector_store(self, document_url: str):
        """Creates a FAISS vector store from a document URL."""
        # 1. Load and extract text
        raw_text = self._load_and_extract_text(document_url)
        
        # 2. Split text into manageable chunks
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = text_splitter.split_text(raw_text)
        
        # 3. Create FAISS vector store from chunks
        self.vector_store = FAISS.from_texts(texts=chunks, embedding=self.embedding_model)

    def answer_questions(self, questions: list[str]) -> list[str]:
        """Answers a list of questions using the created vector store."""
        if not hasattr(self, 'vector_store'):
            raise ValueError("Vector store not created. Call create_vector_store first.")

        answers = []
        # Create a retrieval chain that combines document retrieval and question answering
        document_chain = create_stuff_documents_chain(self.llm, self.prompt)
        retrieval_chain = create_retrieval_chain(self.vector_store.as_retriever(), document_chain)
        
        for question in questions:
            # The chain automatically handles retrieval, context stuffing, and answer generation
            response = retrieval_chain.invoke({"input": question})
            answers.append(response["answer"])
            
        return answers