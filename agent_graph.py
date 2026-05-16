"""
SINTA — Multi-Agent LangGraph Workflow
Agents:
  1. RouterAgent    → tentukan intent user & route ke agent yang tepat
  2. QuizMaster     → bikin soal SNBT berkualitas tinggi
  3. Evaluator      → nilai jawaban & beri feedback mendalam
  4. Recommender    → rekomendasiin materi & strategi belajar
  5. RAGRetriever   → ambil konteks dari vector store
"""

from dataclasses import dataclass
import os
import re
from typing import Any, TypedDict, Literal, Optional

from langgraph.graph import StateGraph, END
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate


@dataclass
class LLMCallResult:
    content: str
    metadata: dict[str, Any]


# ─────────────────────────────────────────
# STATE: shared data antar semua node
# ─────────────────────────────────────────
class SNBTState(TypedDict):
    # Input dari user
    user_input: str
    chat_history: list

    # Routing
    intent: str           # quiz / evaluate / recommend / general
    subject: str          # TPS / Matematika / Fisika / dst
    difficulty: str       # mudah / sedang / sulit

    # Quiz master output
    current_question: str
    question_options: dict        # {"A": ..., "B": ..., "C": ..., "D": ..., "E": ...}
    correct_answer: str
    question_explanation: str

    # Evaluator output
    user_answer: str
    is_correct: bool
    feedback: str
    score_delta: int      # +1 benar, -1 salah, 0 skip

    # Recommender output
    recommendations: list[str]
    weak_topics: list[str]

    # RAG context
    rag_context: str

    # Final response ke user
    final_response: str
    model_metadata: dict

    # Metadata
    total_correct: int
    total_wrong: int
    questions_asked: int


# ─────────────────────────────────────────
# AGENT BUILDER
# ─────────────────────────────────────────
class SNBTAgentGraph:
    RUNTIME_VERSION = "chat-continuation-v2-latex-numbers"
    DEFAULT_MAX_OUTPUT_TOKENS_GENERAL = 4096
    DEFAULT_MAX_OUTPUT_TOKENS_PRECISE = 2048
    MAX_CONTINUATIONS = 2

    def __init__(self, api_key: str, rag_engine=None):
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        self.rag_engine = rag_engine

        # Batas output dibuat longgar agar pembahasan tidak terpotong.
        self.max_output_tokens_general = int(
            os.getenv("SINTA_MAX_OUTPUT_TOKENS_GENERAL", str(self.DEFAULT_MAX_OUTPUT_TOKENS_GENERAL))
        )
        self.max_output_tokens_precise = int(
            os.getenv("SINTA_MAX_OUTPUT_TOKENS_PRECISE", str(self.DEFAULT_MAX_OUTPUT_TOKENS_PRECISE))
        )
        self.runtime_fingerprint = self.expected_runtime_fingerprint()
        self.last_model_metadata: dict[str, Any] = {}

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.7,
            max_output_tokens=self.max_output_tokens_general,
            convert_system_message_to_human=True
        )
        self.llm_precise = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.2,   # lebih deterministik untuk evaluasi
            max_output_tokens=self.max_output_tokens_precise,
            convert_system_message_to_human=True
        )

        self.graph = self._build_graph()

    @classmethod
    def expected_runtime_fingerprint(cls) -> dict[str, Any]:
        return {
            "runtime_version": cls.RUNTIME_VERSION,
            "model": "gemini-2.5-flash",
            "general_max_output_tokens": int(
                os.getenv("SINTA_MAX_OUTPUT_TOKENS_GENERAL", str(cls.DEFAULT_MAX_OUTPUT_TOKENS_GENERAL))
            ),
            "precise_max_output_tokens": int(
                os.getenv("SINTA_MAX_OUTPUT_TOKENS_PRECISE", str(cls.DEFAULT_MAX_OUTPUT_TOKENS_PRECISE))
            ),
        }

    # ── HELPER ──────────────────────────────
    def _safe_jsonable(self, value: Any) -> Any:
        import json

        try:
            return json.loads(json.dumps(value, ensure_ascii=False, default=str))
        except Exception:
            return str(value)

    def _response_text(self, resp: Any) -> str:
        content = getattr(resp, "content", "")
        if isinstance(content, str):
            return content.strip()
        if isinstance(content, list):
            parts = []
            for item in content:
                if isinstance(item, dict):
                    parts.append(str(item.get("text") or item.get("content") or ""))
                else:
                    parts.append(str(getattr(item, "text", item)))
            return "\n".join(part for part in parts if part).strip()
        return str(content).strip()

    def _finish_reason(self, resp: Any) -> str:
        metadata = getattr(resp, "response_metadata", {}) or {}
        reason = metadata.get("finish_reason") or metadata.get("finishReason") or ""
        return str(reason)

    def _extract_call_metadata(self, resp: Any, content: str, precise: bool, attempt_index: int) -> dict[str, Any]:
        response_metadata = getattr(resp, "response_metadata", {}) or {}
        usage_metadata = getattr(resp, "usage_metadata", {}) or {}
        return {
            "runtime_version": self.RUNTIME_VERSION,
            "model_name": response_metadata.get("model_name") or response_metadata.get("model") or "gemini-2.5-flash",
            "finish_reason": self._finish_reason(resp),
            "usage": self._safe_jsonable(usage_metadata),
            "response_metadata": self._safe_jsonable(response_metadata),
            "max_output_tokens": self.max_output_tokens_precise if precise else self.max_output_tokens_general,
            "llm_mode": "precise" if precise else "general",
            "attempt_index": attempt_index,
            "chars": len(content),
        }

    def _finish_needs_continuation(self, finish_reason: str) -> bool:
        normalized = finish_reason.upper().replace(" ", "_")
        return (
            normalized in {"MAX_TOKENS", "LENGTH", "TOKEN_LIMIT", "UNKNOWN_2"}
            or normalized.endswith(".MAX_TOKENS")
        )

    def _looks_cut_off(self, content: str) -> bool:
        stripped = content.rstrip()
        if len(stripped) < 320:
            return False
        if stripped[-1:] in ".!?)]}\"'`":
            return False
        tail = stripped[-140:].lower()
        dangling_phrases = (
            " dan", " atau", " yang", " untuk", " karena", " dengan", " dari",
            " ke", " di", " pada", " agar", " supaya", " jika", " kalau",
            " jangan", " coba", " yaitu", " seperti", " adalah",
        )
        if tail.endswith(dangling_phrases):
            return True
        return bool(re.search(r"\b[a-zA-ZÀ-ÿ]{3,18}$", tail))

    def _continuation_prompt(self, user: str, combined: str) -> str:
        return f"""Jawaban sebelumnya berhenti sebelum selesai.

Instruksi:
- Lanjutkan dari titik terakhir secara natural.
- Jangan ulangi jawaban dari awal.
- Lengkapi kalimat yang terpotong jika ada.
- Tutup jawaban dengan akhir yang jelas.

Pertanyaan user:
{user}

Jawaban sejauh ini:
{combined[-8000:]}"""

    def _combine_continuation(self, combined: str, next_part: str) -> str:
        if not combined:
            return next_part.strip()
        if not next_part:
            return combined.strip()
        return f"{combined.rstrip()}\n\n{next_part.strip()}".strip()

    def _call_llm(self, system: str, user: str, precise=False, allow_continuation=True) -> LLMCallResult:
        llm = self.llm_precise if precise else self.llm
        combined = ""
        attempts: list[dict[str, Any]] = []
        current_user = user

        for attempt_index in range(self.MAX_CONTINUATIONS + 1):
            resp = llm.invoke([
                SystemMessage(content=system),
                HumanMessage(content=current_user)
            ])
            part = self._response_text(resp)
            combined = self._combine_continuation(combined, part)
            attempt_metadata = self._extract_call_metadata(resp, part, precise, attempt_index)
            attempts.append(attempt_metadata)

            finish_reason = attempt_metadata.get("finish_reason", "")
            needs_continuation = self._finish_needs_continuation(finish_reason) or self._looks_cut_off(combined)
            if not allow_continuation or not needs_continuation or attempt_index >= self.MAX_CONTINUATIONS:
                break

            current_user = self._continuation_prompt(user, combined)

        final_metadata = dict(attempts[-1]) if attempts else {}
        final_metadata.update(
            {
                "attempts": attempts,
                "continuations": max(0, len(attempts) - 1),
                "final_chars": len(combined),
                "looked_cut_off": self._looks_cut_off(combined),
            }
        )
        self.last_model_metadata = final_metadata
        return LLMCallResult(content=combined.strip(), metadata=final_metadata)

    def _latex_rules(self) -> str:
        return """
ATURAN MATEMATIKA / LATEX:
- Jika ada rumus, persamaan, simbol matematika, atau ekspresi aljabar, WAJIB tulis dengan delimiter KaTeX.
- Jika ada bilangan pada soal, opsi jawaban, atau pembahasan matematika, WAJIB apit dengan `$...$`.
- Contoh benar: `$20$`, `$0,25$`, `$\\frac{1}{2}$`, `$80\\%$`.
- Contoh salah: `20`, `0,25`, `1/2`, `80%` jika angka itu dimaksudkan tampil sebagai matematika.
- Gunakan `$...$` untuk rumus inline di dalam kalimat.
- Gunakan `$$...$$` untuk rumus berdiri sendiri atau langkah hitung penting.
- Jangan menulis rumus tanpa delimiter jika rumus itu ingin dirender oleh viewer.
- Jangan pakai code block untuk rumus matematika kecuali user minta format teks biasa.
- Untuk satu baris rumus penting, usahakan tampilkan satu rumus per baris.
"""

    def _latexize_plain_numbers(self, value: Any) -> str:
        """Wrap plain numeric tokens in KaTeX delimiters without touching existing math."""
        text = "" if value is None else str(value)
        if not text:
            return text

        math_segment_pattern = re.compile(r"(\$\$.*?\$\$|\$.*?\$)", re.DOTALL)
        number_pattern = re.compile(
            r"(?<![\w$])"
            r"([+-]?(?:\d+(?:[.,]\d+)*)(?:\s*/\s*[+-]?\d+(?:[.,]\d+)*)?)"
            r"(\s*%)?"
            r"(?![\w$])"
        )

        def wrap_segment(segment: str) -> str:
            def replace(match: re.Match[str]) -> str:
                number = match.group(1).strip().replace(" ", "")
                percent = match.group(2)
                if "/" in number:
                    parts = number.split("/", 1)
                    if len(parts) == 2 and parts[0] and parts[1]:
                        number = f"\\frac{{{parts[0]}}}{{{parts[1]}}}"
                if percent:
                    number = f"{number}\\%"
                return f"${number}$"

            return number_pattern.sub(replace, segment)

        parts = math_segment_pattern.split(text)
        for idx, part in enumerate(parts):
            if not part or part.startswith("$"):
                continue
            parts[idx] = wrap_segment(part)
        return "".join(parts)

    def _concise_rules(self) -> str:
        return """
ATURAN PANJANG JAWABAN:
- Jawab padat, tetapi jangan memotong pembahasan yang masih perlu untuk lengkap.
- Utamakan jawaban utuh yang selesai secara natural, bukan sekadar singkat.
- Kalau user meminta langkah, alasan, atau pembahasan, berikan detail yang cukup sampai tuntas.
- Hindari pengulangan, tetapi jangan mengorbankan kejelasan demi hemat kata.
- Akhiri dengan satu ajakan singkat untuk langkah berikutnya bila relevan.
"""

    def _time_context(self, state: SNBTState) -> str:
        current_time = state.get("current_time", "").strip()
        if not current_time:
            return ""
        return f"""
WAKTU SAAT USER MENGIRIM CHAT:
- {current_time}
- Gunakan informasi waktu ini untuk menilai kata seperti "hari ini", "baru", "terkini", atau konteks relevansi SNBT.
"""

    def _history_context(self, state: SNBTState, limit: int = 10) -> str:
        history = state.get("chat_history", [])[-limit:]
        if not history:
            return ""

        lines = []
        for msg in history:
            role = msg.get("role", "user")
            label = "User" if role == "user" else "SINTA"
            content = str(msg.get("content", "")).strip()
            if content:
                lines.append(f"{label}: {content}")

        if not lines:
            return ""

        return """
RIWAYAT PERCAKAPAN TERAKHIR:
{history}

ATURAN PENTING:
- Gunakan riwayat di atas sebagai konteks utama jika relevan.
- Jangan menjawab seolah ini interaksi pertama jika ada riwayat percakapan.
- Jika user merujuk ke percakapan sebelumnya, sambungkan jawaban dengan percakapan itu secara natural.
- Jika user bertanya "apa yang sudah kita bahas" atau sejenisnya, rangkum konteks dari riwayat, jangan mengarang.
""".replace("{history}", "\n".join(lines))

    # ── NODE 1: ROUTER ───────────────────────
    def router_node(self, state: SNBTState) -> SNBTState:
        """Analisa intent user & ekstrak metadata."""
        system = """Kamu adalah router untuk sistem belajar SNBT.
Analisa pesan user dan kembalikan JSON PERSIS seperti ini (tanpa markdown, tanpa komentar):
{
  "intent": "quiz" | "evaluate" | "recommend" | "general",
  "subject": "TPS" | "Matematika" | "Fisika" | "Kimia" | "Biologi" | "Sejarah" | "Geografi" | "Sosiologi" | "Ekonomi" | "General",
  "difficulty": "mudah" | "sedang" | "sulit"
}

Aturan intent:
- "quiz"     : user minta soal/latihan/quiz baru
- "evaluate" : user menjawab soal (A/B/C/D/E atau jawaban teks)
- "recommend": user minta saran, tips, strategi, jadwal belajar
- "general"  : pertanyaan materi, penjelasan konsep, dll

Konteks percakapan terakhir:
{history}

{time_context}
"""
        import json
        history_str = "\n".join(
            f"{'User' if m.get('role')=='user' else 'SINTA'}: {m.get('content','')}"
            for m in state.get("chat_history", [])[-4:]
        )
        call = self._call_llm(
            system.replace("{history}", history_str).replace("{time_context}", self._time_context(state)),
            state["user_input"],
            precise=True,
            allow_continuation=False
        )
        raw = call.content
        try:
            # bersihkan kalau ada markdown fence
            clean = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
        except Exception:
            data = {"intent": "general", "subject": "General", "difficulty": "sedang"}

        return {
            **state,
            "intent": data.get("intent", "general"),
            "subject": data.get("subject", "General"),
            "difficulty": data.get("difficulty", "sedang"),
        }

    # ── NODE 2: RAG RETRIEVER ────────────────
    def rag_retriever_node(self, state: SNBTState) -> SNBTState:
        """Ambil konteks relevan dari vector store."""
        context = ""
        if self.rag_engine and self.rag_engine.vectorstore:
            try:
                query = f"{state['subject']} {state['user_input']}"
                docs = self.rag_engine.vectorstore.similarity_search(query, k=3)
                context = "\n\n".join(d.page_content for d in docs)
            except Exception:
                context = ""
        return {**state, "rag_context": context}

    # ── NODE 3: QUIZ MASTER ──────────────────
    def quiz_master_node(self, state: SNBTState) -> SNBTState:
        """Buat soal SNBT berkualitas tinggi."""
        system = """Kamu adalah Quiz Master SNBT profesional.
Buatlah SATU soal pilihan ganda dengan 5 opsi (A-E) untuk ujian SNBT.

WAJIB kembalikan dalam format JSON PERSIS ini (tanpa markdown):
{
  "question": "teks soal lengkap",
  "A": "opsi A",
  "B": "opsi B",
  "C": "opsi C",
  "D": "opsi D",
  "E": "opsi E",
  "correct": "A",
  "explanation": "pembahasan lengkap step-by-step kenapa jawabannya itu"
}

Kriteria soal:
- Sesuai standar SNBT/UTBK terbaru
- Tingkat kesulitan: {difficulty}
- Mata pelajaran: {subject}
- Soal harus orisinal dan menguji pemahaman, bukan hafalan
- Pembahasan harus detail, ada langkah penyelesaian
{latex_rules}
{concise_rules}

{history_context}

{time_context}

Konteks materi relevan:
{context}
"""
        import json
        call = self._call_llm(
            system
              .replace("{difficulty}", state.get("difficulty", "sedang"))
              .replace("{subject}", state.get("subject", "TPS"))
              .replace("{latex_rules}", self._latex_rules())
              .replace("{concise_rules}", self._concise_rules())
              .replace("{history_context}", self._history_context(state))
              .replace("{time_context}", self._time_context(state))
              .replace("{context}", state.get("rag_context", "")[:1500]),
            f"Buat soal {state['subject']} {state['difficulty']} untuk SNBT",
            precise=True
        )
        raw = call.content
        try:
            clean = raw.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)
        except Exception:
            # fallback jika parse gagal
            data = {
                "question": raw[:500],
                "A": "A", "B": "B", "C": "C", "D": "D", "E": "E",
                "correct": "A",
                "explanation": "Lihat penjelasan di atas."
            }

        # Format response yang bagus
        options = {k: self._latexize_plain_numbers(data.get(k, "")) for k in ["A", "B", "C", "D", "E"]}
        question_text = self._latexize_plain_numbers(data.get("question", ""))
        question_explanation = self._latexize_plain_numbers(data.get("explanation", ""))
        options_str = "\n".join(f"**{k})** {v}" for k, v in options.items() if v)

        response = f"""📝 **SOAL {state.get('questions_asked', 0) + 1}** — {state['subject']} ({state['difficulty'].upper()})

{question_text}

{options_str}

⏱️ *Waktu ideal: {'2' if state['difficulty']=='mudah' else '3' if state['difficulty']=='sedang' else '5'} menit*

---
💬 *Ketik jawaban kamu (A/B/C/D/E) ya!*"""

        return {
            **state,
            "current_question": question_text,
            "question_options": options,
            "correct_answer": data.get("correct", "A"),
            "question_explanation": question_explanation,
            "questions_asked": state.get("questions_asked", 0) + 1,
            "final_response": response,
            "model_metadata": call.metadata
        }

    # ── NODE 4: EVALUATOR ────────────────────
    def evaluator_node(self, state: SNBTState) -> SNBTState:
        """Nilai jawaban user & beri feedback mendalam."""
        user_ans = state["user_input"].strip().upper()
        # ekstrak huruf jawaban (A/B/C/D/E)
        import re
        match = re.search(r'\b([A-E])\b', user_ans)
        user_letter = match.group(1) if match else user_ans[0] if user_ans else "?"

        correct = state.get("correct_answer", "").upper().strip()
        is_correct = user_letter == correct

        # Buat feedback dari LLM
        system = """Kamu adalah evaluator SNBT yang suportif dan detail.
User baru menjawab soal. Berikan feedback yang:
1. Konfirmasi benar/salah dengan jelas
2. Jelaskan pembahasan step-by-step
3. Highlight konsep kunci yang perlu diingat
4. Berikan tips soal serupa
5. Akhiri dengan kalimat semangat
{latex_rules}
{concise_rules}

{history_context}

{time_context}

Gunakan emoji untuk visual yang menarik. Jawab dalam Bahasa Indonesia."""

        context = f"""Soal: {state.get('current_question', '')}
Opsi: {state.get('question_options', {})}
Jawaban benar: {correct}
Pembahasan: {state.get('question_explanation', '')}
Jawaban user: {user_letter}
Benar/Salah: {'BENAR ✅' if is_correct else 'SALAH ❌'}"""

        call = self._call_llm(
            system.replace("{latex_rules}", self._latex_rules())
                  .replace("{concise_rules}", self._concise_rules())
                  .replace("{history_context}", self._history_context(state))
                  .replace("{time_context}", self._time_context(state)),
            context,
        )
        feedback_raw = call.content

        # Hitung skor
        score_delta = 1 if is_correct else -1
        new_correct = state.get("total_correct", 0) + (1 if is_correct else 0)
        new_wrong = state.get("total_wrong", 0) + (0 if is_correct else 1)

        # Score badge
        total = new_correct + new_wrong
        accuracy = round((new_correct / total) * 100) if total > 0 else 0
        score_bar = "🟢" * min(new_correct, 10) + "🔴" * min(new_wrong, 10)

        full_response = f"""{feedback_raw}

---
📊 **Progress Sesi:**
{score_bar}
✅ Benar: {new_correct} | ❌ Salah: {new_wrong} | 🎯 Akurasi: {accuracy}%

---
💬 *Mau lanjut soal berikutnya? Ketik "soal lagi" atau tanya materi lain!*"""

        return {
            **state,
            "user_answer": user_letter,
            "is_correct": is_correct,
            "feedback": feedback_raw,
            "score_delta": score_delta,
            "total_correct": new_correct,
            "total_wrong": new_wrong,
            "final_response": full_response,
            "model_metadata": call.metadata
        }

    # ── NODE 5: RECOMMENDER ──────────────────
    def recommender_node(self, state: SNBTState) -> SNBTState:
        """Rekomendasiin materi & strategi belajar personal."""
        system = """Kamu adalah SINTA, tutor SNBT pribadi yang hangat, suportif, dan tegas dalam memberi arah.
Berikan rekomendasi yang:
- Personal dan spesifik (bukan generik)
- Berbasis data performa user (kalau ada)
- Mencakup: prioritas materi, strategi mengerjakan, tips psikologis
- Action-oriented: apa yang harus dilakukan SEKARANG
- Wajib terasa seperti suara SINTA, bukan AI generik
- Gunakan sudut pandang "SINTA menyarankan..." / "SINTA melihat..." / "SINTA merekomendasikan..."
- Jika data sesi belum ada, akui dengan jujur dan arahkan ke langkah awal yang paling tepat
{latex_rules}
{concise_rules}

{history_context}

{time_context}

Format dengan struktur yang clear, gunakan emoji secukupnya, dan tetap hangat. Bahasa Indonesia yang semangat!"""

        # Bangun konteks performa
        total = state.get("total_correct", 0) + state.get("total_wrong", 0)
        accuracy = round((state.get("total_correct", 0) / total) * 100) if total > 0 else 0

        if total == 0:
            context_hint = state.get("rag_context", "")[:800]
            response = f"""Halo, aku SINTA. Karena kamu belum punya data pengerjaan, aku akan bantu mulai dari fondasi SNBT dulu.

**Prioritas awal dari SINTA:**
- **TPS dulu**: Penalaran Umum, PPU, PBM, dan PK
- **Mulai dari soal pendek**: 1 subtes per sesi agar tidak kewalahan
- **Buat kebiasaan kecil**: akurasi dulu, kecepatan menyusul
- **Catat salahnya di mana**: supaya SINTA bisa bantu baca pola belajarmu

**Langkah konkret hari ini:**
1. Pilih 1 subtes TPS untuk latihan
2. Kerjakan 10-15 soal dengan timer
3. Kirim hasilnya ke SINTA supaya aku bantu analisis

**Arah belajar awal:**
- Fokus subjek: {state.get('subject', 'General')}
- Level sekarang: pemula yang sedang bangun fondasi

{f'Konteks materi relevan: {context_hint}' if context_hint else ''}

Kalau kamu mau, SINTA bisa langsung bikin rencana 7 hari pertama yang ringan tapi efektif."""

            return {
                **state,
                "final_response": response,
                "model_metadata": {
                    "runtime_version": self.RUNTIME_VERSION,
                    "source": "deterministic_recommender",
                    "final_chars": len(response),
                    "continuations": 0,
                },
            }

        perf_context = f"""
Performa sesi ini:
- Total soal dikerjakan: {total}
- Benar: {state.get('total_correct', 0)}, Salah: {state.get('total_wrong', 0)}
- Akurasi: {accuracy}%
- Fokus subjek: {state.get('subject', 'General')}

Pertanyaan user: {state['user_input']}

Konteks materi dari knowledge base:
{state.get('rag_context', '')[:1000]}
"""
        call = self._call_llm(
            system.replace("{latex_rules}", self._latex_rules())
                  .replace("{concise_rules}", self._concise_rules())
                  .replace("{history_context}", self._history_context(state))
                  .replace("{time_context}", self._time_context(state)),
            perf_context,
        )
        response = call.content
        if "SINTA" not in response[:200]:
            response = f"SINTA melihat ini sebagai prioritas awalmu.\n\n{response}"

        return {
            **state,
            "final_response": response,
            "model_metadata": call.metadata
        }

    # ── NODE 6: GENERAL QA ───────────────────
    def general_qa_node(self, state: SNBTState) -> SNBTState:
        """Jawab pertanyaan umum tentang materi/konsep SNBT."""
        system = """Kamu adalah SINTA, tutor SNBT yang cerdas dan suportif.
Jawab pertanyaan user tentang materi SNBT dengan:
- Penjelasan yang jelas dan terstruktur
- Contoh konkret jika relevan
- Kaitkan dengan format soal SNBT
- Bahasa yang ramah dan semangat
- Gunakan emoji secukupnya
{latex_rules}
{concise_rules}

{history_context}

{time_context}

Gunakan konteks materi berikut jika relevan:
{context}"""

        call = self._call_llm(
            system.replace("{latex_rules}", self._latex_rules())
                  .replace("{concise_rules}", self._concise_rules())
                  .replace("{history_context}", self._history_context(state))
                  .replace("{time_context}", self._time_context(state))
                  .replace("{context}", state.get("rag_context", "")[:1500]),
            state["user_input"]
        )
        response = call.content

        return {**state, "final_response": response, "model_metadata": call.metadata}

    def _is_repair_request(self, user_input: str) -> bool:
        q = user_input.lower()
        patterns = [
            r"\b(terpotong|kepotong|terputus|belum selesai)\b",
            r"\b(lanjut|lanjutkan)\b",
            r"\b(kurang lengkap|belum lengkap|lebih lengkap)\b",
            r"\b(pendek banget|terlalu pendek|jawabannya pendek|jawaban pendek)\b",
        ]
        return any(re.search(pattern, q) for pattern in patterns)

    def _last_assistant_answer(self, state: SNBTState) -> str:
        for message in reversed(state.get("chat_history", [])):
            if message.get("role") == "assistant":
                return str(message.get("content", "")).strip()
        return ""

    def repair_response_node(self, state: SNBTState) -> SNBTState:
        last_answer = self._last_assistant_answer(state)
        if not last_answer:
            return self.general_qa_node(state)

        system = """Kamu adalah SINTA, tutor SNBT.
User memberi sinyal bahwa jawaban sebelumnya terlalu pendek, kurang lengkap, atau terpotong.

Tugas:
- Lanjutkan atau perluas jawaban sebelumnya sesuai permintaan user.
- Jangan minta maaf panjang.
- Jangan ulangi seluruh jawaban dari awal kecuali memang perlu.
- Jika jawaban sebelumnya terpotong di tengah kalimat, lanjutkan dari titik terpotong.
- Beri akhir yang jelas dan selesai secara natural.
{latex_rules}
"""
        user = f"""Permintaan user:
{state['user_input']}

Jawaban assistant sebelumnya:
{last_answer}

Berikan versi lanjutan/perluasan yang lengkap."""
        call = self._call_llm(
            system.replace("{latex_rules}", self._latex_rules()),
            user,
            precise=False,
        )
        return {
            **state,
            "intent": "general",
            "final_response": call.content,
            "model_metadata": {
                **call.metadata,
                "repair_request": True,
                "repaired_previous_chars": len(last_answer),
            },
        }

    # ── ROUTING CONDITION ────────────────────
    def route_by_intent(self, state: SNBTState) -> Literal["quiz_master", "evaluator", "recommender", "general_qa"]:
        intent = state.get("intent", "general")
        if intent == "quiz":
            return "quiz_master"
        elif intent == "evaluate":
            # kalau belum ada soal aktif, bikin soal dulu
            return "evaluator" if state.get("current_question") else "quiz_master"
        elif intent == "recommend":
            return "recommender"
        else:
            return "general_qa"

    # ── BUILD GRAPH ──────────────────────────
    def _build_graph(self) -> StateGraph:
        g = StateGraph(SNBTState)

        # Tambah semua node
        g.add_node("router", self.router_node)
        g.add_node("rag_retriever", self.rag_retriever_node)
        g.add_node("quiz_master", self.quiz_master_node)
        g.add_node("evaluator", self.evaluator_node)
        g.add_node("recommender", self.recommender_node)
        g.add_node("general_qa", self.general_qa_node)

        # Entry point
        g.set_entry_point("router")

        # Router → RAG retriever (selalu ambil context dulu)
        g.add_edge("router", "rag_retriever")

        # RAG → conditional routing by intent
        g.add_conditional_edges(
            "rag_retriever",
            self.route_by_intent,
            {
                "quiz_master": "quiz_master",
                "evaluator": "evaluator",
                "recommender": "recommender",
                "general_qa": "general_qa",
            }
        )

        # Semua agent → END
        g.add_edge("quiz_master", END)
        g.add_edge("evaluator", END)
        g.add_edge("recommender", END)
        g.add_edge("general_qa", END)

        return g.compile()

    # ── PUBLIC: RUN ──────────────────────────
    def run(self, user_input: str, prev_state: dict = None) -> dict:
        """
        Jalankan graph dari input user.
        prev_state: state dari turn sebelumnya (untuk continuity).
        Returns: updated state dict
        """
        init_state: SNBTState = {
            "user_input": user_input,
            "chat_history": prev_state.get("chat_history", []) if prev_state else [],
            "intent": "",
            "subject": "General",
            "difficulty": "sedang",
            "current_time": prev_state.get("current_time", "") if prev_state else "",
            "current_question": prev_state.get("current_question", "") if prev_state else "",
            "question_options": prev_state.get("question_options", {}) if prev_state else {},
            "correct_answer": prev_state.get("correct_answer", "") if prev_state else "",
            "question_explanation": prev_state.get("question_explanation", "") if prev_state else "",
            "user_answer": "",
            "is_correct": False,
            "feedback": "",
            "score_delta": 0,
            "recommendations": [],
            "weak_topics": [],
            "rag_context": "",
            "final_response": "",
            "model_metadata": {},
            "total_correct": prev_state.get("total_correct", 0) if prev_state else 0,
            "total_wrong": prev_state.get("total_wrong", 0) if prev_state else 0,
            "questions_asked": prev_state.get("questions_asked", 0) if prev_state else 0,
        }

        if self._is_repair_request(user_input):
            result = self.repair_response_node(init_state)
        else:
            result = self.graph.invoke(init_state)
        result.setdefault("model_metadata", self.last_model_metadata)
        return result
