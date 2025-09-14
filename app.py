# app.py
import io
import os
import sys
from datetime import datetime
import streamlit as st
from fpdf import FPDF
import streamlit.components.v1 as components

# ========= CONFIG (PORTABLE PATHS) =========
# Works locally and on cloud hosts. If ever bundled, sys._MEIPASS helps (PyInstaller).
def _app_dir():
    return getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))

APP_DIR = _app_dir()

def P(*parts):
    return os.path.join(APP_DIR, *parts)

FONTS = ("Maneo.ttf", "cyrvetica.ttf", "cyrvetica_bold.ttf", "SimpleNathalie.otf")

st.set_page_config(page_title="Thanks!", page_icon="🙏", layout="wide")

# ========= STYLES =========
st.markdown("""
<style>
:root{ --teal:#14b8a6; --teal-2:#0ea5b7; --teal-3:#0d9488; --danger:#ef4444; --danger-2:#dc2626; }
body{
  background:
    radial-gradient(900px 600px at -10% -20%, #ccfbf1 0%, transparent 60%),
    radial-gradient(700px 500px at 110% 0%, #a5f3fc 0%, transparent 55%),
    linear-gradient(180deg, #f0fdfa 0%, #ecfeff 60%, #f8fafc 100%);
  background-attachment: fixed;
}
.block-container{ max-width:860px; padding:1rem 0 1.2rem; }
header, footer{ visibility:hidden; height:0; }
.app-title{
  display:inline-block; padding:.45rem 1rem; border-radius:999px;
  background:linear-gradient(90deg, rgba(20,184,166,.18), rgba(14,165,183,.18));
  color:#0ea5b7; font-weight:900; letter-spacing:.2px;
}
.stTextInput>div>div>input, .stTextArea textarea{ border-radius:12px; }
.stButton>button, .stDownloadButton>button{
  border-radius:12px; padding:.6rem 1rem; font-weight:700; white-space:nowrap; width:100%; min-height:44px;
}
/* primary -> TEAL */
.stButton [data-testid="baseButton-primary"],
.stDownloadButton [data-testid="baseButton-primary"],
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"]{
  background:linear-gradient(180deg,var(--teal),var(--teal-2)) !important; border:1px solid var(--teal-2) !important; color:#fff !important;
}
.stButton [data-testid="baseButton-primary"]:hover,
.stDownloadButton [data-testid="baseButton-primary"]:hover,
.stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover{
  background:linear-gradient(180deg,var(--teal-2),var(--teal-3)) !important; border-color:var(--teal-3) !important;
}
/* secondary -> RED (the X) */
.stButton [data-testid="baseButton-secondary"], .stButton > button[kind="secondary"]{
  background:var(--danger) !important; color:#fff !important; border:1px solid var(--danger) !important;
  width:38px !important; height:38px !important; border-radius:10px !important; font-weight:900;
}
.stButton [data-testid="baseButton-secondary"]:hover, .stButton > button[kind="secondary"]:hover{
  background:var(--danger-2) !important; border-color:var(--danger-2) !important;
}
/* card */
[data-testid="stContainer"][aria-expanded="true"] > div{
  border:1px solid rgba(14,165,183,.35); border-radius:16px; background:#fff;
  box-shadow:0 12px 24px rgba(2,6,23,.06); padding:12px 12px 10px;
}
/* title */
.card-title{ position:relative; margin:0 0 .8rem 0; font-size:1.35rem; font-weight:900; letter-spacing:.2px; color:#084c4b; }
.card-title::after{ content:""; position:absolute; left:0; bottom:-8px; width:220px; height:4px; border-radius:999px;
  background:linear-gradient(90deg, #14b8a6, #0ea5b7); }
/* badge (not used, kept from original) */
.badge{ display:inline-block; margin-top:.35rem; padding:.15rem .6rem; font-weight:700; font-size:.8rem;
  color:#065f5b; background:#ecfeff; border:1px solid rgba(14,165,183,.35); border-radius:999px; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1 class='app-title'>🙏 Thanks!</h1>", unsafe_allow_html=True)
st.caption("Create printable <em>Thanks Cards</em> and download a PDF.", unsafe_allow_html=True)

# ========= HELPERS / DATA =========
@st.cache_data(show_spinner=False)
def check_assets():
    if not os.path.exists(P("scc_logo.png")):
        return False, "Missing logo: scc_logo.png", False
    for i in range(1,6):
        if not os.path.exists(P("check_mark2", f"v ({i}).svg")):
            return False, "Missing checkmark SVGs at check_mark2/v (1..5).svg", False
    fonts_ok = all(os.path.exists(P("fonts", f)) for f in FONTS)
    return True, "", fonts_ok

def encode_code(s1,s2,s3,s4,s5):  # -> "12345" subset
    return "".join(d for d,f in zip("12345",[s1,s2,s3,s4,s5]) if f)

# Button helper (tolerates Streamlit versions without "type")
def btn(label, *, key, kind=None, **kwargs):
    try:
        if kind:
            return st.button(label, key=key, type=kind, **kwargs)
        return st.button(label, key=key, **kwargs)
    except TypeError:
        return st.button(label, key=key, **kwargs)

def do_rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()

# ========= LOAD (assets only; no staff file) =========
ok_assets, msg, FONTS_OK = check_assets()
if not ok_assets:
    st.error(msg); st.stop()

# ========= SESSION =========
if "cards" not in st.session_state:
    st.session_state.cards = [dict(awarded_to="", reason="", code="")]

# ========= PDF =========
def build_pdf(name_from: str, cards: dict, fonts_ok: bool) -> bytes:
    r,g,b = 5,172,193
    pdf = FPDF("P","mm","Letter"); pdf.set_margins(5,5,5); pdf.add_page()

    if fonts_ok:
        pdf.add_font("Maneo","",P("fonts","Maneo.ttf"), uni=True)
        pdf.add_font("Cyrvetica","",P("fonts","cyrvetica.ttf"), uni=True)
        pdf.add_font("Cyrvetica","B",P("fonts","cyrvetica_bold.ttf"), uni=True)
        pdf.add_font("SimpleNathalie","",P("fonts","SimpleNathalie.otf"), uni=True)
        FT=("Maneo",""); FL=("Cyrvetica",""); FLB=("Cyrvetica","B"); FN=("SimpleNathalie","")
    else:
        FT=FL=FLB=FN=("Helvetica","")

    y=-1; x_text=0; x_obj=-5
    for awardee in cards:
        if y==-1: y=0
        elif y==0: y=80
        elif y==80: y=160
        else: pdf.add_page(); y=0

        pdf.image(P("scc_logo.png"), x_obj+73.5, y+3.5, 60)
        pdf.set_draw_color(r,g,b); pdf.set_fill_color(r,g,b)
        pdf.set_line_width(0.2); pdf.rect(x_obj+8, y+2, 127, 69, "D")
        pdf.set_line_width(0.2); pdf.rect(x_obj+8, y+71, 127, 5, "DF")

        pdf.set_font(FT[0], FT[1], 70); pdf.set_text_color(r,g,b)
        pdf.set_x(x_text); pdf.set_y(y+11); pdf.cell(4,7,"thanks!")

        pdf.set_font(FL[0], FL[1], 8); pdf.set_text_color(0,0,0)
        pdf.set_x(x_text+14); pdf.set_y(y+25); pdf.cell(0,7,"  Awarded to:")
        pdf.set_x(x_text+14); pdf.set_y(y+32); pdf.cell(0,7,"  Submitted by:")
        pdf.set_x(x_text+14); pdf.set_y(y+39); pdf.cell(0,5,"  For...")

        pdf.set_draw_color(168,177,175); pdf.set_line_width(0.1)
        for yy, x1 in [(29.5,28),(36.5,30),(43.4,19.3),(49,12.7),(54.5,12.7),(60,12.7),(65.5,12.7)]:
            pdf.line(x_obj+x1, y+yy, x_obj+130.6, y+yy)

        pdf.set_x(x_text+11); pdf.set_y(y+70.4); pdf.set_text_color(245,245,245)
        pdf.set_font(FLB[0], FLB[1], 8.5)
        pdf.cell(0,7,"   SAFETY                COURTESY                 SHOW               EFFICIENCY            EVALUATION")

        code = cards[awardee][1]
        def svg(idx, x, yy): pdf.image(P("check_mark2", f"v ({idx}).svg"), x, yy, h=10, w=4, keep_aspect_ratio=True)
        if "1" in code: svg(1, x_obj+18,  y+66)
        if "2" in code: svg(2, x_obj+43,  y+65)
        if "3" in code: svg(3, x_obj+68,  y+66)
        if "4" in code: svg(4, x_obj+92,  y+65)
        if "5" in code: svg(5, x_obj+118, y+66)

        # wrap reason lines (49 first, then 53)
        comment = cards[awardee][0] or ""
        words = comment.split(); parts=[]; line=""
        for w in words:
            lim = 53 if parts else 49
            cand = (line+" "+w).strip()
            if len(cand)>lim: parts.append(line.strip()); line=w
            else: line=cand
        parts.append(line.strip()); parts += [""]*(6-len(parts))

        pdf.set_x(0); pdf.set_y(0); pdf.set_font(FN[0], FN[1], 25); pdf.set_text_color(0,0,0)
        pdf.set_xy(30, y+25.5); pdf.cell(0,5,awardee)
        pdf.set_xy(33, y+32.5); pdf.cell(0,5,name_from or "")
        pdf.set_xy(14, y+40);  pdf.cell(0,5,parts[0])
        pdf.set_xy(8,  y+45.5); pdf.cell(0,5,parts[1])
        pdf.set_xy(8,  y+51);   pdf.cell(0,5,parts[2])
        pdf.set_xy(8,  y+56.5); pdf.cell(0,5,parts[3])
        pdf.set_xy(8,  y+62);   pdf.cell(0,5,parts[4])
        pdf.set_xy(8,  y+67);   pdf.cell(0,5,parts[5])

    out = pdf.output(dest="S")
    if isinstance(out, (bytes, bytearray)): return bytes(out)
    if isinstance(out, str): return out.encode("latin-1")
    return bytes(out)

# ========= UI =========
name_from = st.text_input("Submitted by:", key="submitted_by", placeholder="Your name")

def render_card(i: int):
    c = st.session_state.cards[i]
    with st.container(border=True):
        L, R = st.columns([12,1])
        with L:
            st.markdown(f"<div class='card-title'>Thanks Card {i+1}</div>", unsafe_allow_html=True)
        with R:
            if btn("x", key=f"remove_{i}", kind="secondary", help="Remove this card"):
                if len(st.session_state.cards) > 1:
                    st.session_state.cards.pop(i)
                    do_rerun()

        # Awarded to (TEXT INPUT ONLY; no lookup/normalization/badges)
        name_val = st.text_input(
            "Awarded to:", key=f"awarded_to_{i}",
            value=c.get("awarded_to",""), placeholder="Type a name…"
        ).strip()
        st.session_state.cards[i]["awarded_to"] = name_val

        # Reason
        reason = st.text_area(
            "For…", key=f"reason_{i}", value=c.get("reason",""),
            height=120, max_chars=300,
            placeholder="Why you’re thanking them (max 300 characters)."
        ).strip()
        st.caption(f"{len(reason)}/300 characters")

        # Standards
        col1,col2,col3,col4,col5 = st.columns(5)
        with col1: s1 = st.checkbox("🛡️ Safety",     key=f"s1_{i}", value="1" in c.get("code",""))
        with col2: s2 = st.checkbox("🤝 Courtesy",   key=f"s2_{i}", value="2" in c.get("code",""))
        with col3: s3 = st.checkbox("🌟 Show",       key=f"s3_{i}", value="3" in c.get("code",""))
        with col4: s4 = st.checkbox("⚙️ Efficiency", key=f"s4_{i}", value="4" in c.get("code",""))
        with col5: s5 = st.checkbox("📊 Evaluation", key=f"s5_{i}", value="5" in c.get("code",""))
        st.session_state.cards[i].update({"reason":reason, "code":encode_code(s1,s2,s3,s4,s5)})

# --- Render all cards ---
for idx in range(len(st.session_state.cards)):
    render_card(idx)

# Anchor at the end of cards for new-card scroll
st.markdown('<div id="cards-end"></div>', unsafe_allow_html=True)

# --- Action buttons (center) ---
L,C,R = st.columns([1,2,1])
with C:
    c1, c2 = st.columns(2, gap="small")
    with c1:
        add_clicked = btn("➕ New Thanks Card", key="btn_add", kind="primary")
    with c2:
        create_clicked = btn("📝 Create Thanks Cards", key="btn_create", kind="primary")

    # Anchor & placeholder for download button directly under action buttons
    st.markdown('<div id="download-anchor"></div>', unsafe_allow_html=True)
    dl_placeholder = st.empty()

# --- Handlers ---
if add_clicked:
    st.session_state.cards.append(dict(awarded_to="", reason="", code=""))
    st.session_state["_scroll_target"] = "cards_end"
    do_rerun()

if create_clicked:
    errs, usable = [], []
    if not name_from.strip(): errs.append("Please enter **Submitted by**.")
    for i,c in enumerate(st.session_state.cards, start=1):
        a, r = c.get("awarded_to","").strip(), c.get("reason","").strip()
        if a or r:
            if not a: errs.append(f"Card {i}: **Awarded to** is required.")
            if not r: errs.append(f"Card {i}: **For…** is required.")
            usable.append({"awarded_to":a, "reason":r, "code":c.get("code","")})
    if not usable: errs.append("Add at least one card.")

    if errs:
        for e in errs: st.error(e)
    else:
        # Build dict {AwardedTo: [Reason, Code]} (disambiguate duplicates)
        cards_dict, seen = {}, {}
        for c in usable:
            k = c["awarded_to"]; seen[k] = seen.get(k,0)+1
            key = k if seen[k]==1 else f"{k} ({seen[k]})"
            cards_dict[key] = [c["reason"], c["code"]]
        try:
            pdf_bytes = build_pdf(name_from=name_from.strip(), cards=cards_dict, fonts_ok=FONTS_OK)
        except Exception as e:
            st.error(f"PDF generation failed: {e}")
        else:
            with dl_placeholder.container():
                st.success("Cards created.")
                fname = f"thanks_cards_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                st.download_button("⬇️ Download PDF",
                                   data=io.BytesIO(pdf_bytes),
                                   file_name=fname, mime="application/pdf",
                                   type="primary", key=f"btn_dl_{fname}")

            # Auto-scroll to the download area
            components.html(
                """
                <script>
                  const anchor = window.parent.document.getElementById('download-anchor');
                  if (anchor) { anchor.scrollIntoView({behavior:'smooth', block:'start'}); }
                  else {
                    const main = window.parent.document.querySelector('section.main');
                    if (main) main.scrollTo({top: main.scrollHeight, behavior:'smooth'});
                  }
                </script>
                """,
                height=0,
            )

# --- Post-render: handle new-card scroll if flagged ---
if st.session_state.pop("_scroll_target", None) == "cards_end":
    components.html(
        """
        <script>
          const el = window.parent.document.getElementById('cards-end');
          if (el) { el.scrollIntoView({behavior:'smooth', block:'start'}); }
          else {
            const main = window.parent.document.querySelector('section.main');
            if (main) main.scrollTo({top: main.scrollHeight, behavior:'smooth'});
          }
        </script>
        """,
        height=0,
    )
