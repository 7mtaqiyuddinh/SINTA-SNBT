"""
SINTA - SNBT Intelligent Tutor Assistant
"""

from __future__ import annotations

from datetime import datetime
import re
from zoneinfo import ZoneInfo
import os
from pathlib import Path
import tempfile
from html import escape

import streamlit as st

from sinta_store import (
    append_message,
    create_conversation,
    create_project,
    delete_conversation,
    delete_project,
    ensure_default_project,
    get_conversation_state,
    list_conversations,
    list_messages,
    list_projects,
    list_quiz_attempts,
    rename_project,
    rename_conversation,
    reset_database,
    save_quiz_attempt,
    set_conversation_state,
)
from ui.components import (
    conversation_label,
    project_label,
    render_brand_logo,
    render_empty_state,
    render_journal_strip,
    render_styles,
)
from ui.theme import APP_TAGLINE, APP_TITLE


st.set_page_config(
    page_title=APP_TITLE,
    page_icon=str(Path(__file__).resolve().parent / "assets" / "ico.png"),
    layout="wide",
    initial_sidebar_state="expanded",
)
render_styles()


def init_session() -> None:
    defaults = {
        "messages": [],
        "rag_engine": None,
        "agent_graph": None,
        "runtime_fingerprint": {},
        "last_model_metadata": {},
        "api_key": "",
        "initialized": False,
        "pdf_uploaded": [],
        "graph_state": {},
        "use_web": True,
        "subject_filter": "Otomatis",
        "difficulty": "sedang",
        "sidebar_visible": True,
        "active_project_id": None,
        "selected_project_id": None,
        "active_conversation_id": None,
        "selected_conversation_id": None,
        "clear_main_input": False,
        "reset_notice": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def apply_sidebar_visibility() -> None:
    if not st.session_state.sidebar_visible:
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] { display: none !important; }
            div[data-testid="stSidebarNav"] { display: none !important; }
            </style>
            """,
            unsafe_allow_html=True,
        )


def init_runtime(api_key: str) -> None:
    os.environ["GOOGLE_API_KEY"] = api_key
    from agent_graph import SNBTAgentGraph
    from rag_engine import SNBTRagEngine

    rag = SNBTRagEngine(api_key)
    graph = SNBTAgentGraph(api_key, rag_engine=rag)
    st.session_state.rag_engine = rag
    st.session_state.agent_graph = graph
    st.session_state.runtime_fingerprint = graph.runtime_fingerprint
    st.session_state.initialized = True


def ensure_runtime_current() -> None:
    if not st.session_state.initialized or not st.session_state.api_key:
        return

    from agent_graph import SNBTAgentGraph

    expected = SNBTAgentGraph.expected_runtime_fingerprint()
    graph = st.session_state.agent_graph
    current = getattr(graph, "runtime_fingerprint", None) if graph else None
    if current != expected:
        init_runtime(st.session_state.api_key)


def load_conversation(conversation_id: int | None) -> None:
    if not conversation_id:
        st.session_state.messages = []
        st.session_state.graph_state = {}
        return
    st.session_state.messages = list_messages(conversation_id)
    st.session_state.graph_state = get_conversation_state(conversation_id)


def ensure_workspace() -> None:
    project_id = ensure_default_project()
    if st.session_state.active_project_id is None:
        st.session_state.active_project_id = project_id
    if st.session_state.selected_project_id is None:
        st.session_state.selected_project_id = st.session_state.active_project_id

    conversations = list_conversations(st.session_state.active_project_id)
    if not conversations:
        convo_id = create_conversation(st.session_state.active_project_id, "Sesi Baru")
        st.session_state.active_conversation_id = convo_id
        st.session_state.selected_conversation_id = convo_id
        load_conversation(convo_id)
    elif st.session_state.active_conversation_id is None:
        convo_id = conversations[0]["id"]
        st.session_state.active_conversation_id = convo_id
        st.session_state.selected_conversation_id = convo_id
        load_conversation(convo_id)


def summarize_title(question: str) -> str:
    clean = " ".join(question.split())
    return clean[:36] if len(clean) > 36 else clean


def current_chat_timestamp() -> str:
    return datetime.now(ZoneInfo("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S %Z")


def needs_recent_context(question: str) -> bool:
    q = question.lower()
    patterns = [
        r"\b(terbaru|terkini|update|up-to-date|baru|sekarang|hari ini|minggu ini|bulan ini|tahun ini)\b",
        r"\b(kapan|jadwal|deadline|tanggal|waktu)\b",
        r"\b(2025|2026)\b",
        r"\b(snbt terbaru|utbk terbaru|aturan terbaru|kebijakan terbaru)\b",
        r"\b(penerimaan|registrasi|pendaftaran|pengumuman)\b",
    ]
    return any(re.search(pattern, q) for pattern in patterns)


def should_use_web_search(question: str, intent: str) -> bool:
    if not st.session_state.use_web:
        return False
    if intent not in {"general", "recommend"}:
        return False
    return needs_recent_context(question)


def save_state_to_db() -> None:
    if st.session_state.active_conversation_id:
        set_conversation_state(st.session_state.active_conversation_id, st.session_state.graph_state)


def reset_runtime_session(project_id: int | None = None, conversation_id: int | None = None) -> None:
    st.session_state.messages = []
    st.session_state.graph_state = {}
    st.session_state.pdf_uploaded = []
    st.session_state.active_project_id = project_id
    st.session_state.selected_project_id = project_id
    st.session_state.active_conversation_id = conversation_id
    st.session_state.selected_conversation_id = conversation_id
    st.session_state.last_model_metadata = {}
    st.session_state.clear_main_input = True


def activate_workspace(project_id: int, conversation_id: int) -> None:
    st.session_state.active_project_id = project_id
    st.session_state.selected_project_id = project_id
    st.session_state.active_conversation_id = conversation_id
    st.session_state.selected_conversation_id = conversation_id
    st.session_state.last_model_metadata = {}
    st.session_state.clear_main_input = True
    load_conversation(conversation_id)


def first_conversation_or_create(project_id: int) -> int:
    conversations = list_conversations(project_id)
    if conversations:
        return int(conversations[0]["id"])
    return create_conversation(project_id, "Sesi Baru")


def switch_to_available_workspace() -> None:
    projects = list_projects()
    if projects:
        project_id = int(projects[0]["id"])
    else:
        project_id = ensure_default_project()
    activate_workspace(project_id, first_conversation_or_create(project_id))


def render_bot_bubble(content: str) -> None:
    bubble_col, _ = st.columns([5, 2])
    with bubble_col:
        with st.container(border=True):
            st.markdown(content)


def process_question(question: str) -> None:
    if not st.session_state.initialized:
        st.warning("Masukkan API Gemini di Pengaturan dulu.")
        return
    ensure_runtime_current()

    first_turn = len(st.session_state.messages) == 0
    st.session_state.clear_main_input = True
    st.session_state.messages.append({"role": "user", "content": question})
    append_message(st.session_state.active_conversation_id, "user", question)

    if first_turn:
        rename_conversation(st.session_state.active_conversation_id, summarize_title(question))

    prev_state = dict(st.session_state.graph_state)
    if st.session_state.subject_filter != "Otomatis":
        prev_state["subject"] = st.session_state.subject_filter
    prev_state["difficulty"] = st.session_state.difficulty
    if needs_recent_context(question):
        prev_state["current_time"] = current_chat_timestamp()
    else:
        prev_state.pop("current_time", None)
    prev_state.setdefault("chat_history", [])
    prev_state["chat_history"] = prev_state["chat_history"] + [{"role": "user", "content": question}]

    with st.spinner("SINTA sedang berpikir..."):
        try:
            result = st.session_state.agent_graph.run(question, prev_state=prev_state)
            answer = result.get("final_response", "Maaf, ada error.")
            model_metadata = dict(result.get("model_metadata") or {})
            web_used = False

            if should_use_web_search(question, result.get("intent", "general")):
                try:
                    web_res = st.session_state.rag_engine.search_web(question)
                    if web_res:
                        answer += f"\n\nInfo terbaru:\n{web_res[:400]}..."
                        web_used = True
                except Exception:
                    pass
            model_metadata.update(
                {
                    "final_chars": len(answer),
                    "web_used": web_used,
                    "runtime_fingerprint": st.session_state.runtime_fingerprint,
                }
            )
            st.session_state.last_model_metadata = model_metadata

            keep = [
                "current_question",
                "question_options",
                "correct_answer",
                "question_explanation",
                "total_correct",
                "total_wrong",
                "questions_asked",
                "chat_history",
                "subject",
                "difficulty",
                "current_time",
                "model_metadata",
            ]
            new_state = {k: result.get(k, prev_state.get(k)) for k in keep}
            new_state["model_metadata"] = model_metadata
            new_state["chat_history"] = new_state.get("chat_history", []) + [{"role": "assistant", "content": answer}]
            st.session_state.graph_state = new_state
            set_conversation_state(st.session_state.active_conversation_id, new_state)

            assistant_message = {
                "role": "assistant",
                "content": answer,
                "agent": result.get("intent", "general"),
                "sources": ["built-in"],
                "web_used": web_used,
                "model_metadata": model_metadata,
            }
            st.session_state.messages.append(assistant_message)
            append_message(
                st.session_state.active_conversation_id,
                "assistant",
                answer,
                agent=result.get("intent", "general"),
                sources=["built-in"],
                web_used=web_used,
                model_metadata=model_metadata,
            )

            if result.get("user_answer") or result.get("is_correct") is not None:
                save_quiz_attempt(
                    st.session_state.active_conversation_id,
                    result.get("current_question", question),
                    result.get("user_answer"),
                    result.get("correct_answer"),
                    result.get("is_correct"),
                    result.get("feedback") or result.get("question_explanation"),
                    result.get("subject") or st.session_state.subject_filter,
                    result.get("difficulty") or st.session_state.difficulty,
                    result.get("final_response", answer),
                )

            save_state_to_db()
            st.rerun()
        except Exception as exc:
            error_text = f"Terjadi error: {exc}"
            st.session_state.messages.append(
                {"role": "assistant", "content": error_text, "agent": "general", "sources": [], "web_used": False}
            )
            append_message(
                st.session_state.active_conversation_id,
                "assistant",
                error_text,
                agent="general",
                model_metadata={"error": str(exc), "runtime_fingerprint": st.session_state.runtime_fingerprint},
            )
            st.rerun()


def render_sidebar() -> None:
    with st.sidebar:
        render_brand_logo(max_width=120, centered=True, icon_only=False, framed=False)
        if st.session_state.reset_notice:
            st.success(st.session_state.reset_notice)
            st.session_state.reset_notice = ""
        # st.markdown(
        #     "<span style='color:rgba(25,23,28,0.62);font-size:0.82rem'>Proyek, sesi, dan pengaturan belajar</span>",
        #     unsafe_allow_html=True,
        # )
        # st.divider()

        projects = list_projects()
        if not projects:
            default_project_id = ensure_default_project()
            st.session_state.active_project_id = default_project_id
            projects = list_projects()

        project_ids = [p["id"] for p in projects]
        active_project_id = st.session_state.active_project_id or project_ids[0]
        if active_project_id not in project_ids:
            active_project_id = project_ids[0]
            st.session_state.active_project_id = active_project_id

        selected_project_id = st.selectbox(
            "Proyek",
            options=project_ids,
            index=project_ids.index(active_project_id),
            format_func=lambda pid: project_label(next(p for p in projects if p["id"] == pid)),
            label_visibility="collapsed",
        )
        st.session_state.selected_project_id = selected_project_id
        if selected_project_id != st.session_state.active_project_id:
            st.session_state.active_project_id = selected_project_id
            fresh_conversations = list_conversations(selected_project_id)
            if fresh_conversations:
                first_conversation_id = fresh_conversations[0]["id"]
                st.session_state.active_conversation_id = first_conversation_id
                st.session_state.selected_conversation_id = first_conversation_id
                load_conversation(first_conversation_id)
            else:
                new_conversation_id = create_conversation(selected_project_id, "Sesi Baru")
                st.session_state.active_conversation_id = new_conversation_id
                st.session_state.selected_conversation_id = new_conversation_id
                load_conversation(new_conversation_id)
            st.rerun()

        col_a, col_b = st.columns(2)
        with col_a:
            if st.button("Proyek baru", use_container_width=True):
                new_project_id = create_project(f"Proyek {len(projects) + 1}")
                new_conversation_id = create_conversation(new_project_id, "Sesi Baru")
                st.session_state.active_project_id = new_project_id
                st.session_state.selected_project_id = new_project_id
                st.session_state.active_conversation_id = new_conversation_id
                st.session_state.selected_conversation_id = new_conversation_id
                load_conversation(new_conversation_id)
                st.rerun()
        with col_b:
            if st.button("Sesi baru", use_container_width=True):
                new_conversation_id = create_conversation(selected_project_id, "Sesi Baru")
                st.session_state.active_project_id = selected_project_id
                st.session_state.active_conversation_id = new_conversation_id
                st.session_state.selected_conversation_id = new_conversation_id
                load_conversation(new_conversation_id)
                st.rerun()

        conversations = list_conversations(selected_project_id)
        if conversations:
            conversation_ids = [c["id"] for c in conversations]
            active_conversation_id = st.session_state.active_conversation_id or conversation_ids[0]
            if active_conversation_id not in conversation_ids:
                active_conversation_id = conversation_ids[0]
                st.session_state.active_conversation_id = active_conversation_id
                st.session_state.selected_conversation_id = active_conversation_id
            selected_conversation_id = st.selectbox(
                "Sesi",
                options=conversation_ids,
                index=conversation_ids.index(active_conversation_id),
                format_func=lambda cid: conversation_label(next(c for c in conversations if c["id"] == cid)),
                label_visibility="collapsed",
            )
            if selected_conversation_id != st.session_state.active_conversation_id:
                st.session_state.active_conversation_id = selected_conversation_id
                st.session_state.selected_conversation_id = selected_conversation_id
                load_conversation(selected_conversation_id)
                st.rerun()
        else:
            st.info("Belum ada sesi di proyek ini.")

        active_project = next((p for p in projects if p["id"] == selected_project_id), None)
        active_conversation = None
        if conversations:
            active_conversation = next(
                (c for c in conversations if c["id"] == st.session_state.active_conversation_id),
                conversations[0],
            )

        with st.expander("Kelola nama", expanded=False):
            if active_project:
                project_name = st.text_input(
                    "Nama proyek",
                    value=active_project["name"],
                    key=f"rename_project_name_{active_project['id']}",
                )
                if st.button("Ubah nama proyek", key=f"rename_project_btn_{active_project['id']}", use_container_width=True):
                    try:
                        rename_project(active_project["id"], project_name)
                        st.success("Nama proyek diperbarui.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal mengubah nama proyek: {exc}")

            if active_conversation:
                conversation_title = st.text_input(
                    "Nama sesi",
                    value=active_conversation["title"],
                    key=f"rename_conversation_title_{active_conversation['id']}",
                )
                if st.button(
                    "Ubah nama sesi",
                    key=f"rename_conversation_btn_{active_conversation['id']}",
                    use_container_width=True,
                ):
                    try:
                        rename_conversation(active_conversation["id"], conversation_title)
                        st.success("Nama sesi diperbarui.")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal mengubah nama sesi: {exc}")

        with st.expander("Hapus proyek / sesi", expanded=False):
            st.caption("Pilih item aktif, lalu hapus langsung.")

            if active_conversation:
                st.markdown("**Hapus sesi aktif**")
                st.caption(f"Sesi: {active_conversation['title']}")
                if st.button(
                    "Hapus sesi",
                    key=f"delete_conversation_btn_{active_conversation['id']}",
                    type="secondary",
                    use_container_width=True,
                ):
                    try:
                        deleted_title = active_conversation["title"]
                        delete_conversation(active_conversation["id"])
                        next_conversation_id = first_conversation_or_create(selected_project_id)
                        activate_workspace(selected_project_id, next_conversation_id)
                        st.session_state.reset_notice = f"Sesi '{deleted_title}' dihapus."
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menghapus sesi: {exc}")

            if active_project:
                st.divider()
                st.markdown("**Hapus proyek aktif**")
                st.caption(
                    f"Proyek: {active_project['name']} | "
                    f"{active_project.get('conversation_count', 0)} sesi akan ikut terhapus."
                )
                if st.button(
                    "Hapus proyek",
                    key=f"delete_project_btn_{active_project['id']}",
                    type="secondary",
                    use_container_width=True,
                ):
                    try:
                        deleted_name = active_project["name"]
                        delete_project(active_project["id"])
                        switch_to_available_workspace()
                        st.session_state.reset_notice = f"Proyek '{deleted_name}' dihapus."
                        st.rerun()
                    except Exception as exc:
                        st.error(f"Gagal menghapus proyek: {exc}")

        st.divider()

        gs = st.session_state.graph_state
        total_q = gs.get("questions_asked", 0)
        correct = gs.get("total_correct", 0)
        wrong = gs.get("total_wrong", 0)
        accuracy = round((correct / (correct + wrong)) * 100) if (correct + wrong) > 0 else 0

        st.markdown("### Ringkasan sesi")
        c1, c2, c3 = st.columns(3)
        for col, num, lbl in [(c1, total_q, "Soal"), (c2, correct, "Benar"), (c3, wrong, "Salah")]:
            with col:
                st.markdown(
                    f"<div class='stat-card'><div class='stat-num'>{num}</div><div class='stat-lbl'>{lbl}</div></div>",
                    unsafe_allow_html=True,
                )
        if total_q > 0:
            color = "#22c55e" if accuracy >= 70 else "#f59e0b" if accuracy >= 50 else "#ef4444"
            st.markdown(
                f"<div style='text-align:center;margin-top:6px;font-size:0.85rem;color:{color};font-weight:700'>Akurasi {accuracy}%</div>",
                unsafe_allow_html=True,
            )

        with st.expander("Log kuis terakhir", expanded=False):
            attempts = list_quiz_attempts(st.session_state.active_conversation_id or 0)[:5]
            if not attempts:
                st.caption("Belum ada log kuis pada sesi ini.")
            else:
                for attempt in attempts:
                    status = "Benar" if attempt.get("is_correct") else "Salah"
                    st.markdown(f"- {status}: {attempt.get('question', '')[:90]}")

        st.divider()

        with st.expander("📌 Pengaturan", expanded=not st.session_state.initialized):
            st.markdown("### Koneksi Gemini")
            st.caption("Masukkan API key untuk mengaktifkan SINTA.")
            api_input = st.text_input(
                "API key",
                type="password",
                value=st.session_state.api_key,
                placeholder="Tempel Gemini API key disini",
                label_visibility="collapsed",
            )
            if api_input != st.session_state.api_key:
                st.session_state.api_key = api_input.strip()
                st.session_state.initialized = False

            if st.button("Aktifkan SINTA", use_container_width=True):
                if not st.session_state.api_key:
                    st.warning("Masukkan API key terlebih dahulu.")
                else:
                    with st.spinner("Menyiapkan SINTA..."):
                        try:
                            init_runtime(st.session_state.api_key)
                            st.success("SINTA siap digunakan.")
                        except Exception as exc:
                            st.error(str(exc))

            st.divider()
            st.markdown("### Preferensi belajar")
            subjects = [
                "Otomatis",
                "TPS",
                "Matematika",
                "Fisika",
                "Kimia",
                "Biologi",
                "Sejarah",
                "Geografi",
                "Sosiologi",
                "Ekonomi",
            ]
            st.session_state.subject_filter = st.selectbox(
                "Mapel",
                subjects,
                index=subjects.index(st.session_state.subject_filter) if st.session_state.subject_filter in subjects else 0,
            )
            st.session_state.difficulty = st.selectbox(
                "Tingkat kesulitan",
                ["Mudah", "Sedang", "Sulit"],
                index=["Mudah", "Sedang", "Sulit"].index(st.session_state.difficulty)
                if st.session_state.difficulty in ["Mudah", "Sedang", "Sulit"]
                else 1,
            )
            st.session_state.use_web = st.toggle("Aktifkan pencarian web", value=st.session_state.use_web)

            st.divider()
            st.markdown("### 📚 PDF belajar")
            pdf_file = st.file_uploader("Unggah PDF", type=["pdf"], label_visibility="collapsed")
            if pdf_file and st.session_state.initialized:
                if pdf_file.name not in st.session_state.pdf_uploaded:
                    with st.spinner(f"Memproses {pdf_file.name}..."):
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(pdf_file.read())
                            tmp_path = tmp.name
                        try:
                            n = st.session_state.rag_engine.add_pdf(tmp_path, pdf_file.name)
                            st.session_state.pdf_uploaded.append(pdf_file.name)
                            st.success(f"Berhasil memproses {n} potongan teks.")
                        except Exception as exc:
                            st.error(str(exc))
                        finally:
                            os.unlink(tmp_path)
            for filename in st.session_state.pdf_uploaded:
                st.markdown(f"<span class='src-tag'>PDF: {filename}</span>", unsafe_allow_html=True)

            st.divider()
            st.markdown("### Reset database")
            st.caption("Mengosongkan database aktif dan membuat backup otomatis.")
            reset_confirm_1 = st.checkbox(
                "Saya paham semua proyek, sesi, pesan, dan log kuis di database aktif akan direset.",
                key="reset_database_confirm_1",
            )
            reset_confirm_2 = st.text_input(
                "Ketik RESET_DATABASE untuk konfirmasi kedua",
                value="",
                key="reset_database_confirm_2",
            )
            reset_ready = reset_confirm_1 and reset_confirm_2.strip() == "RESET_DATABASE"
            if st.button("Reset database", type="secondary", use_container_width=True, disabled=not reset_ready):
                try:
                    reset_info = reset_database(create_backup=True)
                    reset_runtime_session(reset_info.get("project_id"), reset_info.get("conversation_id"))
                    st.session_state.reset_notice = "Database berhasil direset. Backup otomatis sudah dibuat."
                    st.rerun()
                except Exception as exc:
                    st.error(f"Gagal reset database: {exc}")


def render_main_area() -> None:
    status_text = "Siap membantu" if st.session_state.initialized else "Perlu API Gemini, masukkan API di Pengaturan."
    render_brand_logo(max_width=560, centered=True, icon_only=False, framed=False)
    st.markdown(f"<p class='sinta-sub' style='margin-top:8px'>{APP_TAGLINE}</p>", unsafe_allow_html=True)
    st.markdown(
        f"<div style='text-align:left;font-size:0.82rem;color:#49454F;margin:6px 0 14px 0'>{status_text}</div>",
        unsafe_allow_html=True,
    )

    if not st.session_state.messages:
        render_empty_state()
        quick_prompts = [
            ("Soal TPS\nLogika", "Berikan soal latihan TPS Penalaran Logis level sedang"),
            ("Soal Fisika\nlistrik", "Berikan soal latihan Fisika SNBT tentang listrik"),
            ("Strategi\nSNBT", "Berikan strategi dan tips menghadapi SNBT"),
            ("Matematika\npeluang", "Jelaskan konsep peluang untuk SNBT"),
            ("Soal Kimia\nstoikiometri", "Berikan soal kimia stoikiometri level sulit"),
            ("Pembahasan\ncepat", "Jelaskan cara menjawab soal TPS dengan cepat"),
        ]
        for row_start in range(0, len(quick_prompts), 3):
            cols = st.columns(3)
            row_items = quick_prompts[row_start : row_start + 3]
            for offset, (label, prompt) in enumerate(row_items):
                with cols[offset]:
                    if st.button(label, key=f"quick_{row_start + offset}", use_container_width=True):
                        process_question(prompt)
    else:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(
                    f"<div style='display:flex;justify-content:flex-end'><div class='user-bubble'>{escape(message['content'])}</div></div>",
                    unsafe_allow_html=True,
                )
            else:
                label_map = {
                    "quiz": "Latihan Soal",
                    "evaluate": "Penilaian Jawaban",
                    "recommend": "Rekomendasi Belajar",
                    "general": "Tanya Jawab",
                }
                label = label_map.get(message.get("agent", "general"), "Tanya Jawab")
                st.markdown(f"<div class='message-card'><b>{label}</b></div>", unsafe_allow_html=True)
                render_bot_bubble(message["content"])
                sources = message.get("sources", [])
                if sources:
                    rendered_sources = ["Materi SINTA" if s == "built-in" else s for s in sources]
                    src_html = "".join(f"<span class='src-tag'>{s}</span>" for s in rendered_sources)
                    st.markdown(f"<div style='margin-top:8px'>{src_html}</div>", unsafe_allow_html=True)
                if message.get("web_used"):
                    st.markdown("<span class='src-tag'>Web</span>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    if st.session_state.clear_main_input:
        st.session_state.main_input = ""
        st.session_state.clear_main_input = False

    with st.form("chat_form", clear_on_submit=False):
        input_col, button_col = st.columns([6, 1])
        with input_col:
            user_input = st.text_input(
                "Pesan",
                placeholder="Tanya materi, minta soal, jawab A/B/C/D/E, atau minta strategi...",
                label_visibility="collapsed",
                key="main_input",
            )
        with button_col:
            send = st.form_submit_button("Kirim", use_container_width=True)

    if send and user_input.strip():
        process_question(user_input.strip())

    st.markdown(
        f"<div style='text-align:center;color:#79747E;font-size:0.72rem;padding:20px'>{APP_TITLE}</div>",
        unsafe_allow_html=True,
    )


init_session()
apply_sidebar_visibility()
ensure_workspace()
render_sidebar()
render_main_area()
