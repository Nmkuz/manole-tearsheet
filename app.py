import io
import streamlit as st
import yfinance as yf
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

# ── page config ───────────────────────────────────────────────────────
st.set_page_config(
    page_title="Manole Capital — Equity Tearsheet",
    page_icon="📊",
    layout="centered",
)

# ── styling ───────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f7f9fc; }
  .header-block {
    background: #0D1E3F;
    border-radius: 10px;
    padding: 28px 32px 20px 32px;
    margin-bottom: 28px;
  }
  .header-block h1 { color: white; font-size: 1.7rem; margin: 0 0 4px 0; }
  .header-block p  { color: #8C9DB5; margin: 0; font-size: 0.95rem; }
  .metric-card {
    background: white;
    border-radius: 8px;
    padding: 14px 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.07);
    margin-bottom: 4px;
  }
  .metric-label { color: #8C9DB5; font-size: 0.78rem; margin-bottom: 2px; }
  .metric-value { color: #0D1E3F; font-size: 1.15rem; font-weight: 700; }
  .section-title {
    color: #1A55A3;
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-bottom: 1.5px solid #1A55A3;
    padding-bottom: 4px;
    margin: 22px 0 12px 0;
  }
  .green { color: #1A7A4A; }
  .red   { color: #B22222; }
  .desc  { color: #333; font-size: 0.88rem; line-height: 1.65; }
  .stDownloadButton > button {
    background: #0D1E3F !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 28px !important;
    font-size: 1rem !important;
    width: 100%;
    margin-top: 8px;
  }
</style>
""", unsafe_allow_html=True)

# ── helpers ───────────────────────────────────────────────────────────
def fmt(n, prefix="$"):
    if n is None: return "N/A"
    try:
        n = float(n)
        if abs(n) >= 1e9: return f"{prefix}{n/1e9:.2f}B"
        if abs(n) >= 1e6: return f"{prefix}{n/1e6:.2f}M"
        return f"{prefix}{n:,.0f}"
    except: return "N/A"

def pct(n):
    if n is None: return "N/A", None
    try: v = float(n); return f"{v*100:.1f}%", v
    except: return "N/A", None

def mul(n):
    if n is None: return "N/A"
    try: return f"{float(n):.1f}x"
    except: return "N/A"

def colored_pct(n):
    text, v = pct(n)
    if v is None: return text, ""
    css = "green" if v >= 0 else "red"
    return text, css

def fetch(sym):
    t = yf.Ticker(sym)
    i = t.info
    if not i.get("longName"):
        raise ValueError(f"No data found for '{sym}'. Check the ticker and try again.")
    return {
        "name":     i.get("longName", sym),
        "sector":   i.get("sector", "N/A"),
        "industry": i.get("industry", "N/A"),
        "website":  i.get("website", "N/A"),
        "desc":     i.get("longBusinessSummary", ""),
        "price":    i.get("currentPrice") or i.get("regularMarketPrice"),
        "mktcap":   i.get("marketCap"),
        "cash":     i.get("totalCash"),
        "debt":     i.get("totalDebt"),
        "ev":       i.get("enterpriseValue"),
        "perf52":   i.get("52WeekChange"),
        "beta":     i.get("beta"),
        "rev":      i.get("totalRevenue"),
        "rev_g":    i.get("revenueGrowth"),
        "ebitda":   i.get("ebitda"),
        "ebitda_m": i.get("ebitdaMargins"),
        "ni":       i.get("netIncomeToCommon"),
        "eps":      i.get("trailingEps"),
        "eps_g":    i.get("earningsGrowth"),
        "pe":       i.get("trailingPE"),
        "fpe":      i.get("forwardPE"),
        "ev_ebt":   i.get("enterpriseToEbitda"),
        "ev_rev":   i.get("enterpriseToRevenue"),
        "ticker":   sym.upper(),
    }

# ── PDF builder (same as tearsheet.py) ───────────────────────────────
def build_pdf(d):
    buf = io.BytesIO()

    NAVY   = colors.HexColor("#0D1E3F")
    BLUE   = colors.HexColor("#1A55A3")
    SILVER = colors.HexColor("#8C9DB5")
    LIGHT  = colors.HexColor("#EEF2F8")
    WHITE  = colors.white
    BLACK  = colors.HexColor("#1A1A1A")
    GREEN  = colors.HexColor("#1A7A4A")
    RED    = colors.HexColor("#B22222")

    def style(name, **kw):
        d = dict(fontName="Helvetica", fontSize=9, leading=13,
                 textColor=BLACK, spaceAfter=0, spaceBefore=0)
        d.update(kw)
        return ParagraphStyle(name, **d)

    S_co    = style("co",   fontName="Helvetica-Bold", fontSize=18, textColor=WHITE, leading=22)
    S_sec   = style("sec",  fontName="Helvetica-Bold", fontSize=8, textColor=BLUE, leading=10, spaceBefore=4)
    S_lbl   = style("lbl",  fontSize=8.5, textColor=SILVER)
    S_val   = style("val",  fontName="Helvetica-Bold", fontSize=9, textColor=BLACK)
    S_desc  = style("desc", fontSize=8.5, leading=13, textColor=BLACK)
    S_foot  = style("foot", fontSize=7, textColor=SILVER, alignment=TA_CENTER)

    def color_pct(raw):
        if raw is None: return "N/A"
        try:
            v = float(raw)
            c = GREEN if v >= 0 else RED
            col = c.hexval()[2:]
            return f'<font color="#{col}">{v*100:.1f}%</font>'
        except: return "N/A"

    def two_col(left, right):
        def col(rows):
            return [[Paragraph(k, S_lbl), Paragraph(v, S_val)] for k, v in rows]
        L, R = col(left), col(right)
        combined = []
        for i in range(max(len(L), len(R))):
            lr = L[i] if i < len(L) else [Paragraph("", S_lbl), Paragraph("", S_val)]
            rr = R[i] if i < len(R) else [Paragraph("", S_lbl), Paragraph("", S_val)]
            combined.append(lr + [Paragraph("", S_lbl)] + rr)
        t = Table(combined, colWidths=[1.6*inch, 1.4*inch, 0.3*inch, 1.6*inch, 1.4*inch])
        t.setStyle(TableStyle([
            ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1),3),
            ("BOTTOMPADDING", (0,0),(-1,-1),3),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE, LIGHT]),
            ("LEFTPADDING",   (0,0),(0,-1),6),
            ("LEFTPADDING",   (3,0),(3,-1),6),
        ]))
        return t

    def one_col(rows):
        data = [[Paragraph(k, S_lbl), Paragraph(v, S_val)] for k, v in rows]
        t = Table(data, colWidths=[2.2*inch, 2.8*inch])
        t.setStyle(TableStyle([
            ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1),3),
            ("BOTTOMPADDING", (0,0),(-1,-1),3),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE, LIGHT]),
            ("LEFTPADDING",   (0,0),(0,-1),6),
        ]))
        return t

    def sec(title):
        return [
            HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=3),
            Paragraph(title.upper(), S_sec),
        ]

    doc = SimpleDocTemplate(buf, pagesize=letter,
        leftMargin=0.65*inch, rightMargin=0.65*inch,
        topMargin=0.5*inch, bottomMargin=0.65*inch)

    story = []

    hdr = [[
        Paragraph(
            f"{d['name']}<br/>"
            f"<font size='11' color='#8C9DB5'>{d['ticker']}  ·  {d['sector']}  ·  {d['industry']}</font>",
            S_co),
        Paragraph(
            f"<b>Manole Capital Management</b><br/>Equity Tearsheet<br/>{datetime.now().strftime('%B %d, %Y')}",
            style("hr", fontSize=8, textColor=SILVER, alignment=TA_RIGHT, leading=13)),
    ]]
    ht = Table(hdr, colWidths=[4.4*inch, 2.3*inch])
    ht.setStyle(TableStyle([
        ("BACKGROUND",    (0,0),(-1,-1),NAVY),
        ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",    (0,0),(-1,-1),14),
        ("BOTTOMPADDING", (0,0),(-1,-1),14),
        ("LEFTPADDING",   (0,0),(0,-1),14),
        ("RIGHTPADDING",  (1,0),(1,-1),14),
    ]))
    story.append(ht)
    story.append(Spacer(1, 10))

    story += sec("Market Data & Valuation")
    story.append(Spacer(1, 4))
    beta_str = f"{float(d['beta']):.2f}" if d["beta"] else "N/A"
    story.append(two_col(
        [("Current Price", fmt(d["price"])),
         ("Market Cap",    fmt(d["mktcap"])),
         ("Enterprise Value", fmt(d["ev"])),
         ("Cash & Equiv.", fmt(d["cash"])),
         ("Total Debt",    fmt(d["debt"])),
         ("52-Week Return", color_pct(d["perf52"])),
         ("Beta",          beta_str)],
        [("P/E (TTM)",  mul(d["pe"])),
         ("P/E (Fwd)",  mul(d["fpe"])),
         ("EV/EBITDA",  mul(d["ev_ebt"])),
         ("EV/Revenue", mul(d["ev_rev"]))],
    ))
    story.append(Spacer(1, 10))

    story += sec("Financials (TTM)")
    story.append(Spacer(1, 4))
    story.append(two_col(
        [("Revenue",       fmt(d["rev"])),
         ("Revenue Growth",color_pct(d["rev_g"])),
         ("EBITDA",        fmt(d["ebitda"])),
         ("EBITDA Margin", f"{float(d['ebitda_m'])*100:.1f}%" if d["ebitda_m"] else "N/A")],
        [("Net Income", fmt(d["ni"])),
         ("EPS (TTM)", f"${float(d['eps']):.2f}" if d["eps"] else "N/A"),
         ("EPS Growth", color_pct(d["eps_g"]))],
    ))
    story.append(Spacer(1, 10))

    story += sec("Business")
    story.append(Spacer(1, 4))
    story.append(one_col([
        ("Sector",   d["sector"]),
        ("Industry", d["industry"]),
        ("Website",  f'<link href="{d["website"]}">{d["website"]}</link>'),
    ]))
    story.append(Spacer(1, 6))
    if d["desc"]:
        story.append(Paragraph(d["desc"], S_desc))
    story.append(Spacer(1, 10))

    quartr = f"https://web.quartr.com/search?query={d['ticker']}"
    sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={d['ticker']}&type=10-K&dateb=&owner=include&count=10"
    story += sec("Resources")
    story.append(Spacer(1, 4))
    story.append(one_col([
        ("Quartr (Earnings Calls)", f'<link href="{quartr}">{quartr}</link>'),
        ("SEC Filings (10-K / 10-Q)", f'<link href="{sec_url}">EDGAR — {d["ticker"]}</link>'),
        ("Investor Relations", f'<link href="{d["website"]}">{d["website"]}</link>'),
    ]))
    story.append(Spacer(1, 14))

    story.append(HRFlowable(width="100%", thickness=0.4, color=SILVER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Data sourced from Yahoo Finance. For informational purposes only — not investment advice. "
        "Generated by Manole Capital intern tearsheet tool.",
        S_foot))

    doc.build(story)
    buf.seek(0)
    return buf

# ── UI ────────────────────────────────────────────────────────────────
st.markdown("""
<div class="header-block">
  <h1>📊 Equity Tearsheet Generator</h1>
  <p>Manole Capital Management &nbsp;·&nbsp; Enter any ticker to generate a tearsheet</p>
</div>
""", unsafe_allow_html=True)

ticker_input = st.text_input(
    "", placeholder="e.g. V, MA, PYPL, ASTS",
    label_visibility="collapsed"
)

generate = st.button("Generate Tearsheet", use_container_width=True)

if generate and ticker_input.strip():
    tickers = [t.strip().upper() for t in ticker_input.replace(",", " ").split() if t.strip()]

    for sym in tickers:
        with st.spinner(f"Fetching data for {sym}..."):
            try:
                d = fetch(sym)
            except Exception as e:
                st.error(str(e))
                continue

        st.markdown(f"<div class='section-title'>Market Data &amp; Valuation — {d['name']} ({d['ticker']})</div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Price",        fmt(d["price"]))
        c2.metric("Market Cap",   fmt(d["mktcap"]))
        c3.metric("Ent. Value",   fmt(d["ev"]))
        c4.metric("52-Wk Return", pct(d["perf52"])[0])

        c5, c6, c7, c8 = st.columns(4)
        c5.metric("Cash",         fmt(d["cash"]))
        c6.metric("Total Debt",   fmt(d["debt"]))
        c7.metric("P/E (TTM)",    mul(d["pe"]))
        c8.metric("EV/EBITDA",    mul(d["ev_ebt"]))

        st.markdown("<div class='section-title'>Financials (TTM)</div>", unsafe_allow_html=True)

        c9, c10, c11, c12 = st.columns(4)
        c9.metric("Revenue",      fmt(d["rev"]))
        c10.metric("Rev Growth",  pct(d["rev_g"])[0])
        c11.metric("Net Income",  fmt(d["ni"]))
        c12.metric("EPS",         f"${float(d['eps']):.2f}" if d["eps"] else "N/A")

        st.markdown("<div class='section-title'>Business</div>", unsafe_allow_html=True)
        st.markdown(f"<p class='desc'><b>{d['sector']}</b> · {d['industry']}<br/><br/>{d['desc']}</p>", unsafe_allow_html=True)

        # PDF download
        st.markdown("<div class='section-title'>Download</div>", unsafe_allow_html=True)
        pdf_buf = build_pdf(d)
        date_str = datetime.now().strftime("%Y%m%d")
        st.download_button(
            label=f"⬇ Download {sym} Tearsheet PDF",
            data=pdf_buf,
            file_name=f"{sym}_tearsheet_{date_str}.pdf",
            mime="application/pdf",
            key=f"dl_{sym}",
        )

        st.divider()

elif generate:
    st.warning("Please enter a ticker symbol.")
