"""Reusable Streamlit UI fragments for SINTA."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

ASSET_DIR = Path(__file__).resolve().parent.parent / "assets"
SINTA_LOGO_PATH = ASSET_DIR / "sinta_logo.png"
SINTA_ICON_PATH = ASSET_DIR / "ico.png"


def render_brand_logo(
    max_width: int = 360,
    centered: bool = True,
    icon_only: bool = False,
    framed: bool = False,
) -> None:
    path = SINTA_ICON_PATH if icon_only else SINTA_LOGO_PATH
    if not path.exists():
        st.error(f"Logo asset tidak ditemukan: {path.name}")
        return

    container = st.container()
    with container:
        if centered:
            st.markdown("<div style='display:flex;justify-content:center'>", unsafe_allow_html=True)
        if framed:
            st.markdown("<div class='brand-logo-card'>", unsafe_allow_html=True)
        st.image(str(path), width=max_width)
        if framed:
            st.markdown("</div>", unsafe_allow_html=True)
        if centered:
            st.markdown("</div>", unsafe_allow_html=True)


def render_styles() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Nunito+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Nunito Sans', sans-serif; }
#MainMenu, footer, .stDeployButton { visibility: hidden; display: none; }
.stApp {
    background:
        radial-gradient(circle at top left, rgba(103,80,164,0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(125,82,96,0.14), transparent 32%),
        linear-gradient(180deg, #FFFBFE 0%, #F3EDF7 100%);
    min-height: 100vh;
    color: #1C1B1F;
}
.stApp::before {
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
        radial-gradient(circle at 12% 18%, rgba(103,80,164,0.12), transparent 0 18%),
        radial-gradient(circle at 82% 14%, rgba(125,82,96,0.11), transparent 0 16%),
        radial-gradient(circle at 78% 80%, rgba(232,222,248,0.55), transparent 0 18%);
    filter: blur(18px);
    opacity: 0.9;
}
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #F3EDF7 0%, #E8DEF8 100%) !important;
    border-right: 1px solid rgba(121,116,126,0.18) !important;
}
section[data-testid="stSidebar"] * { color: #1C1B1F !important; }
.brand-logo-wrap {
    display: block;
}
.brand-logo-card {
    background: rgba(255,255,255,0.72);
    border: 1px solid rgba(121,116,126,0.12);
    border-radius: 22px;
    padding: 10px 12px;
    box-shadow: 0 10px 24px rgba(28,27,31,0.08);
}
.brand-logo {
    width: 100%;
    height: auto;
    display: block;
}
.brand-logo-icon {
    object-fit: cover;
}
.sinta-shell {
    position: relative;
    background: rgba(255,251,254,0.72);
    border: 1px solid rgba(121,116,126,0.14);
    border-radius: 32px;
    padding: 20px;
    backdrop-filter: blur(12px);
    box-shadow: 0 12px 40px rgba(28,27,31,0.08);
}
.sinta-title {
    font-size: 2.7rem;
    font-weight: 700;
    text-align: center;
    color: #1C1B1F;
    letter-spacing: -0.04em;
    margin: 0;
}
.sinta-title .accent {
    color: #6750A4;
}
.sinta-sub {
    text-align: center;
    color: #49454F;
    font-size: 0.92rem;
    margin-top: 4px;
    letter-spacing: 0.02em;
}
.sinta-badge-row, .chip-row, .bubble-strip {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin: 10px 0 8px 0;
}
.bubble, .chip {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    border-radius: 9999px;
    padding: 8px 12px;
    font-size: 0.8rem;
    line-height: 1.35;
    color: #1D192B;
    border: 1px solid rgba(121,116,126,0.18);
    background: rgba(232,222,248,0.75);
}
.bubble-accent, .chip-strong {
    background: rgba(103,80,164,0.14);
    border-color: rgba(103,80,164,0.22);
}
.hero-card, .panel-card, .message-card, .feature-card, .metric-card {
    border-radius: 24px;
    border: 1px solid rgba(121,116,126,0.16);
    background: rgba(243,237,247,0.78);
    box-shadow: 0 10px 30px rgba(28,27,31,0.08);
}
.hero-card {
    padding: 22px;
    text-align: center;
    margin: 14px 0 18px 0;
    position: relative;
    overflow: hidden;
}
.hero-brand {
    margin-bottom: 10px;
}
.hero-card::before,
.hero-card::after {
    content: "";
    position: absolute;
    inset: auto;
    border-radius: 9999px;
    pointer-events: none;
    filter: blur(22px);
}
.hero-card::before {
    width: 180px;
    height: 180px;
    background: rgba(103,80,164,0.14);
    top: -40px;
    left: -30px;
}
.hero-card::after {
    width: 220px;
    height: 220px;
    background: rgba(125,82,96,0.12);
    bottom: -90px;
    right: -70px;
}
.message-card {
    padding: 14px 18px;
    margin: 8px 0;
    color: #1C1B1F;
    line-height: 1.7;
    background: rgba(255,255,255,0.62);
}
.user-bubble {
    background: #6750A4;
    color: #FFFFFF;
    padding: 13px 16px;
    border-radius: 20px 20px 6px 20px;
    max-width: min(78%, 720px);
    margin: 6px 0 6px auto;
    box-shadow: 0 10px 25px rgba(103,80,164,0.18);
    display: inline-block;
    position: relative;
}
.bot-bubble {
    background: #F3EDF7;
    color: #1C1B1F;
    padding: 15px 18px;
    border-radius: 6px 20px 20px 20px;
    max-width: min(88%, 780px);
    margin: 6px 0;
    border: 1px solid rgba(121,116,126,0.16);
    box-shadow: 0 10px 24px rgba(28,27,31,0.06);
    display: inline-block;
    position: relative;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #F3EDF7 !important;
    border: 1px solid rgba(121,116,126,0.16) !important;
    border-radius: 6px 20px 20px 20px !important;
    box-shadow: 0 10px 24px rgba(28,27,31,0.06) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] {
    color: #1C1B1F !important;
    line-height: 1.7 !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p {
    margin-bottom: 0.65rem !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stMarkdownContainer"] p:last-child {
    margin-bottom: 0 !important;
}
.src-tag {
    display: inline-block;
    background: rgba(232,222,248,0.9);
    border: 1px solid rgba(103,80,164,0.18);
    color: #1D192B;
    padding: 3px 10px;
    border-radius: 9999px;
    font-size: 0.72rem;
    margin: 2px;
}
.stat-card {
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(121,116,126,0.12);
    border-radius: 18px;
    padding: 10px 12px;
    text-align: center;
}
.stat-num {
    font-size: 1.5rem;
    font-weight: 700;
    color: #1C1B1F;
}
.stat-lbl {
    font-size: 0.72rem;
    color: #49454F;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}
.panel-card {
    padding: 14px;
}
.feature-card {
    padding: 14px 16px;
}
.feature-kicker {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #49454F;
    margin-bottom: 4px;
}
.feature-icon {
    font-size: 1.05rem;
    margin-right: 6px;
}
.feature-value {
    font-size: 1rem;
    font-weight: 700;
    color: #1C1B1F;
}
.feature-note {
    font-size: 0.84rem;
    color: #49454F;
    margin-top: 4px;
}
.journal-shell {
    background: rgba(255,255,255,0.62);
    border: 1px solid rgba(121,116,126,0.14);
    border-radius: 28px;
    padding: 18px;
    margin: 10px 0 18px 0;
}
.journal-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 12px;
}
.journal-copy {
    margin-bottom: 14px;
    color: #1C1B1F;
}
.journal-title {
    font-size: 1.15rem;
    font-weight: 700;
    color: #1C1B1F;
    margin-bottom: 4px;
}
.journal-subtitle {
    font-size: 0.9rem;
    color: #49454F;
}
.hero-metrics {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 10px;
    margin: 12px 0 10px 0;
}
.metric-kicker {
    font-size: 0.68rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #49454F;
}
.metric-value {
    font-size: 1.05rem;
    font-weight: 700;
    color: #1C1B1F;
    margin-top: 4px;
}
.metric-note {
    font-size: 0.8rem;
    color: #49454F;
    margin-top: 2px;
}
.section-title {
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #49454F;
    margin: 6px 0 10px 0;
}
.quick-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px;
}
.quick-button .stButton > button {
    background: #E8DEF8 !important;
    color: #1D192B !important;
    border: 1px solid rgba(103,80,164,0.16) !important;
    border-radius: 9999px !important;
    font-weight: 700 !important;
    white-space: normal !important;
    line-height: 1.35 !important;
    padding: 0.76rem 0.95rem !important;
    min-height: 3.2rem !important;
    text-align: center !important;
    font-size: 0.92rem !important;
    box-shadow: 0 8px 20px rgba(28,27,31,0.08) !important;
    transition: transform 180ms cubic-bezier(0.2, 0, 0, 1), box-shadow 180ms cubic-bezier(0.2, 0, 0, 1), background 180ms cubic-bezier(0.2, 0, 0, 1) !important;
}
.quick-button .stButton > button:hover {
    background: #DDD3F0 !important;
    box-shadow: 0 12px 26px rgba(28,27,31,0.12) !important;
    transform: translateY(-1px) !important;
}
.quick-button .stButton > button:active {
    transform: scale(0.97) translateY(0) !important;
}
.stTextInput > div > div > input,
.stSelectbox > div > div {
    background: rgba(255,255,255,0.72) !important;
    border: 1px solid rgba(121,116,126,0.2) !important;
    color: #1C1B1F !important;
    border-radius: 16px !important;
}
.stButton > button {
    background: #6750A4 !important;
    color: white !important;
    border: none !important;
    border-radius: 9999px !important;
    font-weight: 700 !important;
    min-height: 3rem !important;
    transition: transform 180ms cubic-bezier(0.2, 0, 0, 1), box-shadow 180ms cubic-bezier(0.2, 0, 0, 1) !important;
}
.stButton > button:hover {
    box-shadow: 0 12px 26px rgba(103,80,164,0.2) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:active {
    transform: scale(0.97) !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: #E8DEF8 !important;
    color: #1D192B !important;
    border: 1px solid rgba(103,80,164,0.16) !important;
    box-shadow: 0 8px 20px rgba(28,27,31,0.08) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: #DDD3F0 !important;
    box-shadow: 0 12px 24px rgba(28,27,31,0.10) !important;
}
@media (max-width: 900px) {
    .journal-grid { grid-template-columns: 1fr; }
    .hero-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
    .quick-grid { grid-template-columns: 1fr; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {
        animation-duration: 0.01ms !important;
        animation-iteration-count: 1 !important;
        transition-duration: 0.01ms !important;
        scroll-behavior: auto !important;
    }
}
</style>
        """
        ,
        unsafe_allow_html=True,
    )


def project_label(project: dict) -> str:
    return f"📁 {project['name']} ({project.get('conversation_count', 0)} sesi)"


def conversation_label(conversation: dict) -> str:
    return f"💬 {conversation['title']} ({conversation.get('message_count', 0)} pesan)"


def render_journal_strip(active_project: str, active_conversation: str, total_messages: int, total_quiz: int, subject: str, project_count: int, conversation_count: int) -> None:
    st.markdown(
        f"""
        <div class='journal-shell'>
            <div class='journal-copy'>
                <div class='journal-title'>📔 Catatan Belajar SINTA</div>
                <div class='journal-subtitle'>Semua percakapan, proyek, dan hasil kuis tersimpan rapi di perangkatmu.</div>
            </div>
            <div class='bubble-strip'>
                <span class='bubble'>🗂️ {project_count} proyek</span>
                <span class='bubble'>💬 {conversation_count} sesi</span>
                <span class='bubble'>📝 {total_messages} pesan</span>
                <span class='bubble bubble-accent'>🎯 {subject}</span>
            </div>
            <div class='hero-metrics'>
                <div class='metric-card'>
                    <div class='metric-kicker'>📌 Fokus belajar</div>
                    <div class='metric-value'>{active_project}</div>
                    <div class='metric-note'>{conversation_count} sesi di proyek ini</div>
                </div>
                <div class='metric-card'>
                    <div class='metric-kicker'>💬 Sesi aktif</div>
                    <div class='metric-value'>{active_conversation}</div>
                    <div class='metric-note'>{total_messages} pesan tersimpan offline</div>
                </div>
                <div class='metric-card'>
                    <div class='metric-kicker'>📝 Latihan dikerjakan</div>
                    <div class='metric-value'>{total_quiz}</div>
                    <div class='metric-note'>log kuis sesi ini</div>
                </div>
                <div class='metric-card'>
                    <div class='metric-kicker'>🎈 Suasana</div>
                    <div class='metric-value'>Hangat & ringan</div>
                    <div class='metric-note'>lebih ramah saat dipakai belajar</div>
                </div>
            </div>
            <div class='journal-grid'>
                <div class='feature-card'>
                    <div class='feature-kicker'><span class='feature-icon'>📁</span>Proyek aktif</div>
                    <div class='feature-value'>{active_project}</div>
                    <div class='feature-note'>semua sesi terkumpul di sini</div>
                </div>
                <div class='feature-card'>
                    <div class='feature-kicker'><span class='feature-icon'>💬</span>Sesi aktif</div>
                    <div class='feature-value'>{active_conversation}</div>
                    <div class='feature-note'>lanjutkan konteks belajar tanpa hilang</div>
                </div>
                <div class='feature-card'>
                    <div class='feature-kicker'><span class='feature-icon'>✨</span>Mode belajar</div>
                    <div class='feature-value'>SNBT fokus, hangat, personal</div>
                    <div class='feature-note'>ubah preferensi di Pengaturan sidebar</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_state() -> None:
    st.markdown(
        """
        <p style='color:#49454F;font-size:0.98rem'>
        Tulis pertanyaan, minta latihan soal, cek jawaban, atau minta saran belajar.
        Percakapan kamu disimpan offline per proyek dan sesi.
        </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
