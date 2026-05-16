"""
RAG Engine untuk SNBT Chatbot.
Menggunakan LangChain + ChromaDB + Gemini Embeddings.
"""

import os
import tempfile
from typing import List, Optional
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.documents import Document
from langchain_classic.chains import ConversationalRetrievalChain
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.tools import DuckDuckGoSearchRun
from knowledge_base import get_knowledge_text


class SNBTRagEngine:
    """
    RAG Engine khusus persiapan SNBT.
    Supports: built-in knowledge, PDF upload, web search.
    """

    def __init__(self, api_key: str):
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key

        self.max_output_tokens = int(os.getenv("SINTA_MAX_OUTPUT_TOKENS_RAG", "4096"))

        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-001",
            google_api_key=api_key
        )

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.7,
            max_output_tokens=self.max_output_tokens,
            convert_system_message_to_human=True
        )

        self.vectorstore = None
        self.chat_history = []
        self.chat_history_window = 30
        self.search_tool = DuckDuckGoSearchRun()
        self._init_vectorstore()

    def _init_vectorstore(self):
        """Inisialisasi vector store dengan materi built-in."""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", "---", ".", " "]
        )

        knowledge_text = get_knowledge_text()
        chunks = splitter.split_text(knowledge_text)

        docs = [
            Document(
                page_content=chunk,
                metadata={"source": "built-in", "type": "materi_snbt"}
            )
            for chunk in chunks
        ]

        self.vectorstore = Chroma.from_documents(
            documents=docs,
            embedding=self.embeddings,
            collection_name="snbt_knowledge"
        )

    def add_pdf(self, pdf_path: str, filename: str = "uploaded.pdf") -> int:
        """Tambahkan PDF ke vector store."""
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100
        )
        docs = splitter.split_documents(pages)

        for doc in docs:
            doc.metadata["source"] = filename
            doc.metadata["type"] = "pdf_upload"

        self.vectorstore.add_documents(docs)
        return len(docs)

    def search_web(self, query: str) -> str:
        """Cari informasi terkini dari web."""
        try:
            result = self.search_tool.run(query + " SNBT 2026")
            return result[:1500]
        except Exception:
            return ""

    def _build_system_prompt(self) -> str:
        return """Kamu adalah SINTA — asisten AI khusus persiapan SNBT yang cerdas, suportif, dan interaktif.

KEPRIBADIAN:
- Ramah, semangat, dan suportif layaknya kakak/mentor yang care
- Gunakan bahasa yang jelas dan mudah dipahami siswa SMA
- Beri pujian saat siswa menjawab benar, beri semangat saat salah
- Selalu ada sumber/alasan di balik setiap jawaban

FORMAT RESPONS UNTUK SOAL LATIHAN:
Saat membuat soal, selalu gunakan format ini:
---
📝 **SOAL [NOMOR]**
[Pertanyaan yang jelas]

A) [Opsi A]
B) [Opsi B]  
C) [Opsi C]
D) [Opsi D]
E) [Opsi E]

⏱️ *Waktu ideal: [X] menit*
---

FORMAT PEMBAHASAN (setelah siswa menjawab):
---
[✅ BENAR! / ❌ Belum tepat, nih jawaban yang benar:]

🎯 **Jawaban:** [Huruf] — [Opsi]

📖 **Pembahasan:**
[Penjelasan lengkap step-by-step]

💡 **Konsep Kunci:**
[Ringkasan konsep yang perlu diingat]

🔥 **Tips Soal Serupa:**
[Strategi untuk soal tipe ini]
---

PANDUAN UMUM:
1. Jika siswa minta latihan soal → buat 1 soal dulu, tunggu jawaban, baru beri pembahasan
2. Jika siswa salah → jangan langsung kasih jawaban, coba tanya "Kamu yakin? Coba pikir lagi..."
3. Selalu kaitkan materi dengan konteks ujian SNBT
4. Jika ditanya di luar SNBT → arahkan balik ke persiapan SNBT
5. Gunakan konteks dari retrieved documents untuk menjawab
6. Jawab ringkas, padat, dan langsung ke inti; hindari pengulangan yang tidak perlu

ATURAN LATEX / RUMUS:
- Jika ada rumus, persamaan, simbol matematika, atau langkah hitung, wajib gunakan delimiter KaTeX.
- Gunakan `$...$` untuk rumus inline.
- Gunakan `$$...$$` untuk rumus berdiri sendiri atau langkah hitung yang penting.
- Jangan menulis rumus tanpa delimiter jika ingin diproses viewer.
- Jangan bungkus rumus dengan code block kecuali user memang minta format teks biasa.

Ingat: Tugasmu adalah membantu siswa BENAR-BENAR PAHAM, bukan sekadar tahu jawaban!"""

    def get_chain(self):
        """Buat conversational retrieval chain."""
        from langchain_core.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate, ChatPromptTemplate

        system_template = self._build_system_prompt() + """

KONTEKS DARI MATERI/DOKUMEN:
{context}

RIWAYAT PERCAKAPAN:
{chat_history}
"""
        messages = [
            SystemMessagePromptTemplate.from_template(system_template),
            HumanMessagePromptTemplate.from_template("{question}")
        ]
        prompt = ChatPromptTemplate.from_messages(messages)

        chain = ConversationalRetrievalChain.from_llm(
            llm=self.llm,
            retriever=self.vectorstore.as_retriever(
                search_kwargs={"k": 4}
            ),
            combine_docs_chain_kwargs={"prompt": prompt},
            return_source_documents=True,
            verbose=False
        )
        return chain

    def chat(self, question: str, use_web: bool = False) -> dict:
        """
        Main chat function.
        Returns: {"answer": str, "sources": list, "web_used": bool}
        """
        web_context = ""
        web_used = False

        if use_web:
            web_result = self.search_web(question)
            if web_result:
                web_context = f"\n\n[INFO TERKINI DARI WEB]: {web_result}"
                web_used = True

        enhanced_question = question + web_context

        chain = self.get_chain()
        result = chain.invoke(
            {
                "question": enhanced_question,
                "chat_history": self.chat_history,
            }
        )
        self.chat_history.append((question, result["answer"]))
        self.chat_history = self.chat_history[-self.chat_history_window:]

        sources = []
        if "source_documents" in result:
            seen = set()
            for doc in result["source_documents"]:
                src = doc.metadata.get("source", "built-in")
                if src not in seen:
                    seen.add(src)
                    sources.append(src)

        return {
            "answer": result["answer"],
            "sources": sources,
            "web_used": web_used
        }

    def clear_memory(self):
        """Reset conversation memory."""
        self.chat_history.clear()
