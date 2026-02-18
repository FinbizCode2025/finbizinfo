from langchain.text_splitter import RecursiveCharacterTextSplitter # type: ignore
from langchain_google_genai import GoogleGenerativeAI
from langchain.chains import ConversationalRetrievalChain # type: ignore
from langchain.memory import ConversationBufferMemory # type: ignore
from langchain.vectorstores import FAISS # type: ignore
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.document_loaders import PyMuPDFLoader # type: ignore
from langchain.prompts import PromptTemplate # type: ignore
import os

class DocumentProcessor:
    def __init__(self, api_key):
        self.api_key = api_key
        self.embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            add_start_index=True,
        )
        self.llm = GoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)

    def process_document(self, file_path):
        """Process a PDF document and create a vector store."""
        try:
            # Load the document
            loader = PyMuPDFLoader(file_path)
            documents = loader.load()
            
            # Split the documents into chunks
            texts = self.text_splitter.split_documents(documents)
            
            # Create vector store
            vectorstore = FAISS.from_documents(texts, self.embeddings)
            
            return vectorstore
        except Exception as e:
            print(f"Error processing document: {e}")
            raise

    def create_chain(self, vectorstore):
        """Create a conversational chain with the processed document."""
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        # Custom prompt template for financial analysis
        template = """You are a financial analyst expert. Use the context below to answer questions about the financial document.
        Focus on providing accurate financial insights, ratio analysis, and clear explanations.

        Context: {context}

        Chat History: {chat_history}

        Question: {question}

        Please provide a detailed analysis with the following structure when relevant:
        1. Direct answer to the question
        2. Key financial metrics mentioned
        3. Interpretation and implications
        4. Any relevant recommendations

        Answer:"""

        PROMPT = PromptTemplate(
            input_variables=["context", "chat_history", "question"],
            template=template
        )

        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=vectorstore.as_retriever(),
            memory=memory,
            combine_docs_chain_kwargs={"prompt": PROMPT},
            return_source_documents=True
        )

        return chain

    def analyze_financials(self, chain, query):
        """Run a financial analysis query through the chain."""
        try:
            result = chain({"question": query})
            return {
                "answer": result["answer"],
                "sources": [doc.page_content for doc in result.get("source_documents", [])]
            }
        except Exception as e:
            print(f"Error in analysis: {e}")
            return {"error": str(e)}