import io
import base64
import os
import streamlit as st
import yfinance as yf
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image as RLImage
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT

LOGO_PATH       = os.path.join(os.path.dirname(__file__), "logo.png")
LOGO_WHITE_PATH = os.path.join(os.path.dirname(__file__), "logo_white.png")

def logo_b64(white=False):
    path = LOGO_WHITE_PATH if white else LOGO_PATH
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return None

st.set_page_config(
    page_title="Manole Capital — Equity Tearsheet",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
<style>
  /* force light base */
  html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #f0f4f9 !important;
    color: #0D1E3F !important;
  }
  [data-testid="stSidebar"] { display: none; }
  [data-testid="stToolbar"] { display: none; }

  /* header */
  .mc-header {
    background: linear-gradient(135deg, #0D1E3F 0%, #1A3A6B 100%);
    border-radius: 12px;
    padding: 32px 40px;
    margin-bottom: 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .mc-header-left h1 {
    color: #ffffff;
    font-size: 1.9rem;
    font-weight: 700;
    margin: 0 0 6px 0;
    letter-spacing: -0.02em;
  }
  .mc-header-left p { color: #8C9DB5; margin: 0; font-size: 0.92rem; }
  .mc-header-right {
    text-align: right;
    color: #8C9DB5;
    font-size: 0.82rem;
    line-height: 1.7;
  }
  .mc-header-right b { color: #ccd6e8; }

  /* company title bar */
  .co-bar {
    background: #0D1E3F;
    border-radius: 10px;
    padding: 18px 24px;
    margin: 0 0 20px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .co-bar-name { color: #fff; font-size: 1.35rem; font-weight: 700; }
  .co-bar-meta { color: #8C9DB5; font-size: 0.83rem; margin-top: 3px; }
  .co-bar-price { text-align: right; }
  .co-bar-price .price { color: #fff; font-size: 1.6rem; font-weight: 700; }
  .co-bar-price .perf { font-size: 0.85rem; margin-top: 2px; }
  .pos { color: #4CAF82; }
  .neg { color: #E05252; }

  /* section label */
  .sec-label {
    color: #1A55A3;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    border-bottom: 2px solid #1A55A3;
    padding-bottom: 5px;
    margin: 24px 0 14px 0;
  }

  /* metric cards */
  .metric-grid {
    display: grid;
    gap: 10px;
  }
  .metric-grid-3 { grid-template-columns: repeat(3, 1fr); }
  .metric-grid-4 { grid-template-columns: repeat(4, 1fr); }
  .metric-grid-5 { grid-template-columns: repeat(5, 1fr); }
  .mcard {
    background: #ffffff;
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(13,30,63,0.08);
    border-left: 3px solid #1A55A3;
  }
  .mcard-label {
    color: #8C9DB5;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    margin-bottom: 5px;
  }
  .mcard-value {
    color: #0D1E3F;
    font-size: 1.1rem;
    font-weight: 700;
  }
  .mcard-value.pos { color: #1A7A4A; }
  .mcard-value.neg { color: #B22222; }

  /* description */
  .co-desc {
    background: #fff;
    border-radius: 8px;
    padding: 16px 20px;
    color: #2c3e5c;
    font-size: 0.87rem;
    line-height: 1.7;
    box-shadow: 0 1px 3px rgba(13,30,63,0.06);
  }

  /* resource links */
  .res-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;
    margin-top: 4px;
  }
  .res-card {
    background: #fff;
    border-radius: 8px;
    padding: 14px 16px;
    box-shadow: 0 1px 3px rgba(13,30,63,0.08);
  }
  .res-card-label {
    color: #8C9DB5;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 5px;
  }
  .res-card a {
    color: #1A55A3;
    font-size: 0.82rem;
    font-weight: 600;
    text-decoration: none;
    word-break: break-all;
  }
  .res-card a:hover { text-decoration: underline; }

  /* input & button */
  [data-testid="stTextInput"] input {
    border: 2px solid #d0daea !important;
    border-radius: 8px !important;
    padding: 12px 16px !important;
    font-size: 1rem !important;
    background: #fff !important;
    color: #0D1E3F !important;
  }
  [data-testid="stTextInput"] input:focus {
    border-color: #1A55A3 !important;
    box-shadow: 0 0 0 3px rgba(26,85,163,0.15) !important;
  }
  [data-testid="stButton"] > button {
    background: #1A55A3 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 12px 32px !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    width: 100% !important;
    transition: background 0.2s !important;
  }
  [data-testid="stButton"] > button:hover {
    background: #0D3D82 !important;
  }
  [data-testid="stDownloadButton"] > button {
    background: #0D1E3F !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    width: 100% !important;
  }

  /* divider */
  hr { border: none; border-top: 1px solid #dde6f0; margin: 28px 0; }

  /* footer */
  .mc-footer {
    text-align: center;
    color: #8C9DB5;
    font-size: 0.75rem;
    margin-top: 40px;
    padding-top: 20px;
    border-top: 1px solid #dde6f0;
  }
</style>
""", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────

def fmt(n, prefix="$"):
    if n is None: return "—"
    try:
        n = float(n)
        if abs(n) >= 1e12: return f"{prefix}{n/1e12:.2f}T"
        if abs(n) >= 1e9:  return f"{prefix}{n/1e9:.2f}B"
        if abs(n) >= 1e6:  return f"{prefix}{n/1e6:.2f}M"
        return f"{prefix}{n:,.0f}"
    except: return "—"

def pct_str(n):
    if n is None: return "—", None
    try: v = float(n); return f"{v*100:.1f}%", v
    except: return "—", None

def mul(n):
    if n is None: return "—"
    try:
        v = float(n)
        if v < 0: return "N/M"
        return f"{v:.1f}x"
    except: return "—"

def color_class(v):
    if v is None: return ""
    return "pos" if float(v) >= 0 else "neg"

def card(label, value, css_class=""):
    return f'<div class="mcard"><div class="mcard-label">{label}</div><div class="mcard-value {css_class}">{value}</div></div>'

def cards(*items):
    n = len(items)
    cls = f"metric-grid-{min(n, 5)}"
    inner = "".join(card(l, v, c) for l, v, c in items)
    return f'<div class="metric-grid {cls}">{inner}</div>'


# ── data fetch ────────────────────────────────────────────────────────

@st.cache_data(ttl=3600, show_spinner=False)
def fetch(sym):
    t = yf.Ticker(sym)
    i = t.info
    if not i or not i.get("longName"):
        raise ValueError(f"Ticker '{sym}' not found. Please check the symbol and try again.")

    # try multiple price fields
    price = (i.get("currentPrice") or i.get("regularMarketPrice")
             or i.get("previousClose") or i.get("ask"))

    # 52w high/low
    hi52  = i.get("fiftyTwoWeekHigh")
    lo52  = i.get("fiftyTwoWeekLow")

    return {
        "name":     i.get("longName", sym),
        "sector":   i.get("sector") or "—",
        "industry": i.get("industry") or "—",
        "website":  i.get("website") or "",
        "desc":     i.get("longBusinessSummary", ""),
        "exchange": i.get("exchange") or "",
        "currency": i.get("currency") or "USD",
        "employees":i.get("fullTimeEmployees"),
        "price":    price,
        "hi52":     hi52,
        "lo52":     lo52,
        "mktcap":   i.get("marketCap"),
        "cash":     i.get("totalCash"),
        "debt":     i.get("totalDebt"),
        "ev":       i.get("enterpriseValue"),
        "perf52":   i.get("52WeekChange"),
        "beta":     i.get("beta"),
        "shares":   i.get("sharesOutstanding"),
        "div_yield":i.get("dividendYield"),
        "rev":      i.get("totalRevenue"),
        "rev_g":    i.get("revenueGrowth"),
        "gross_m":  i.get("grossMargins"),
        "ebitda":   i.get("ebitda"),
        "ebitda_m": i.get("ebitdaMargins"),
        "net_m":    i.get("profitMargins"),
        "ni":       i.get("netIncomeToCommon"),
        "eps":      i.get("trailingEps"),
        "eps_g":    i.get("earningsGrowth"),
        "fcf":      i.get("freeCashflow"),
        "pe":       i.get("trailingPE"),
        "fpe":      i.get("forwardPE"),
        "pb":       i.get("priceToBook"),
        "ps":       i.get("priceToSalesTrailing12Months"),
        "ev_ebt":   i.get("enterpriseToEbitda"),
        "ev_rev":   i.get("enterpriseToRevenue"),
        "ticker":   sym.upper(),
        "generated":datetime.now().strftime("%B %d, %Y  %I:%M %p"),
    }


# ── PDF builder ───────────────────────────────────────────────────────

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

    def sty(name, **kw):
        base = dict(fontName="Helvetica", fontSize=9, leading=13,
                    textColor=BLACK, spaceAfter=0, spaceBefore=0)
        base.update(kw)
        return ParagraphStyle(name, **base)

    S_co   = sty("co",  fontName="Helvetica-Bold", fontSize=17, textColor=WHITE, leading=21)
    S_sec  = sty("sec", fontName="Helvetica-Bold", fontSize=7.5, textColor=BLUE, leading=10, spaceBefore=2)
    S_lbl  = sty("lbl", fontSize=8, textColor=SILVER)
    S_val  = sty("val", fontName="Helvetica-Bold", fontSize=8.5, textColor=BLACK)
    S_desc = sty("dsc", fontSize=8, leading=12.5, textColor=BLACK)
    S_foot = sty("ft",  fontSize=6.5, textColor=SILVER, alignment=TA_CENTER)

    def cpct(raw):
        if raw is None: return "—"
        try:
            v = float(raw)
            col = GREEN.hexval()[2:] if v >= 0 else RED.hexval()[2:]
            return f'<font color="#{col}">{v*100:.1f}%</font>'
        except: return "—"

    def two_col(left, right):
        L = [[Paragraph(k, S_lbl), Paragraph(v, S_val)] for k, v in left]
        R = [[Paragraph(k, S_lbl), Paragraph(v, S_val)] for k, v in right]
        rows = []
        for i in range(max(len(L), len(R))):
            l = L[i] if i < len(L) else [Paragraph("", S_lbl), Paragraph("", S_val)]
            r = R[i] if i < len(R) else [Paragraph("", S_lbl), Paragraph("", S_val)]
            rows.append(l + [Paragraph("", S_lbl)] + r)
        t = Table(rows, colWidths=[1.55*inch, 1.35*inch, 0.25*inch, 1.55*inch, 1.35*inch])
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
        t = Table(data, colWidths=[2.1*inch, 3.95*inch])
        t.setStyle(TableStyle([
            ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1),3),
            ("BOTTOMPADDING", (0,0),(-1,-1),3),
            ("ROWBACKGROUNDS",(0,0),(-1,-1),[WHITE, LIGHT]),
            ("LEFTPADDING",   (0,0),(0,-1),6),
        ]))
        return t

    def section(title):
        return [HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=3),
                Paragraph(title.upper(), S_sec)]

    PAGE_H = letter[1]
    PAGE_W = letter[0]
    L_MAR = 0.6*inch
    R_MAR = 0.6*inch
    T_MAR = 0.45*inch
    B_MAR = 0.55*inch
    USABLE_H = PAGE_H - T_MAR - B_MAR

    doc = SimpleDocTemplate(buf, pagesize=letter,
        leftMargin=L_MAR, rightMargin=R_MAR,
        topMargin=T_MAR, bottomMargin=B_MAR)

    # ── footer pinned to bottom of every page via onPage callback ────
    FOOTER_TEXT = ("Data sourced from Yahoo Finance  ·  For informational purposes only  ·  "
                   "Not investment advice  ·  Manole Capital Management")

    def draw_footer(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColorRGB(0.55, 0.61, 0.71)
        canvas.setLineWidth(0.4)
        canvas.line(L_MAR, B_MAR - 6, letter[0] - R_MAR, B_MAR - 6)
        canvas.setFont("Helvetica", 6.5)
        canvas.setFillColorRGB(0.55, 0.61, 0.71)
        canvas.drawCentredString(letter[0] / 2, B_MAR - 16, FOOTER_TEXT)
        canvas.restoreState()

    # ── story factory — called fresh each time to avoid stateful flowable reuse ──
    def make_story(extra_pts=0):
        s = []

        # header — logo left, company info right
        sub = f"{d['ticker']}  ·  {d['sector']}  ·  {d['industry']}"
        if os.path.exists(LOGO_PATH):
            logo_cell = RLImage(LOGO_PATH, width=1.4*inch, height=0.55*inch)
        else:
            logo_cell = Paragraph("", sty("empty"))

        hdr_left = Table(
            [[logo_cell],
             [Paragraph(f"<font size='14' color='#ffffff'><b>{d['name']}</b></font>", sty("cn", textColor=WHITE, fontSize=14, fontName="Helvetica-Bold", leading=18))],
             [Paragraph(f"<font size='9' color='#8C9DB5'>{sub}</font>", sty("cs", textColor=SILVER, fontSize=9, leading=12))]],
            colWidths=[4.5*inch]
        )
        hdr_left.setStyle(TableStyle([("LEFTPADDING",(0,0),(-1,-1),0),("TOPPADDING",(0,0),(-1,-1),2),("BOTTOMPADDING",(0,0),(-1,-1),2)]))

        hdr = [[
            hdr_left,
            Paragraph(
                f"<b>Equity Tearsheet</b><br/>Manole Capital Management<br/>{d['generated']}",
                sty("r", fontSize=8, textColor=SILVER, alignment=TA_RIGHT, leading=13)),
        ]]
        ht = Table(hdr, colWidths=[4.5*inch, 2.4*inch])
        ht.setStyle(TableStyle([
            ("BACKGROUND",    (0,0),(-1,-1),NAVY),
            ("VALIGN",        (0,0),(-1,-1),"MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1),12),
            ("BOTTOMPADDING", (0,0),(-1,-1),12),
            ("LEFTPADDING",   (0,0),(0,-1),14),
            ("RIGHTPADDING",  (1,0),(1,-1),14),
        ]))
        s += [ht, Spacer(1, 10)]

        # market data + valuation
        s += section("Market Data & Valuation")
        s.append(Spacer(1, 4))
        beta  = f"{float(d['beta']):.2f}" if d["beta"] else "—"
        hi52  = fmt(d["hi52"], prefix="$") if d["hi52"] else "—"
        lo52  = fmt(d["lo52"], prefix="$") if d["lo52"] else "—"
        div_y = f"{float(d['div_yield'])*100:.2f}%" if d["div_yield"] else "—"
        s.append(two_col(
            [("Current Price",    fmt(d["price"])),
             ("Market Cap",       fmt(d["mktcap"])),
             ("Enterprise Value", fmt(d["ev"])),
             ("Cash & Equiv.",    fmt(d["cash"])),
             ("Total Debt",       fmt(d["debt"])),
             ("52-Week Return",   cpct(d["perf52"])),
             ("52-Week High",     hi52),
             ("52-Week Low",      lo52),
             ("Beta",             beta),
             ("Dividend Yield",   div_y)],
            [("P/E (TTM)",    mul(d["pe"])),
             ("P/E (Fwd)",    mul(d["fpe"])),
             ("EV/EBITDA",    mul(d["ev_ebt"])),
             ("EV/Revenue",   mul(d["ev_rev"])),
             ("Price/Book",   mul(d["pb"])),
             ("Price/Sales",  mul(d["ps"]))],
        ))
        s.append(Spacer(1, 10))

        # financials
        s += section("Financials (TTM)")
        s.append(Spacer(1, 4))
        gm  = f"{float(d['gross_m'])*100:.1f}%"  if d["gross_m"]  else "—"
        em  = f"{float(d['ebitda_m'])*100:.1f}%" if d["ebitda_m"] else "—"
        nm  = f"{float(d['net_m'])*100:.1f}%"    if d["net_m"]    else "—"
        eps = f"${float(d['eps']):.2f}"           if d["eps"]      else "—"
        s.append(two_col(
            [("Revenue",        fmt(d["rev"])),
             ("Revenue Growth", cpct(d["rev_g"])),
             ("Gross Margin",   gm),
             ("EBITDA",         fmt(d["ebitda"])),
             ("EBITDA Margin",  em),
             ("Net Income",     fmt(d["ni"])),
             ("Net Margin",     nm),
             ("Free Cash Flow", fmt(d["fcf"])),
             ("EPS (TTM)",      eps),
             ("EPS Growth",     cpct(d["eps_g"]))],
            [],
        ))
        s.append(Spacer(1, 10))

        # business
        s += section("Business")
        s.append(Spacer(1, 4))
        emp = f"{int(d['employees']):,}" if d["employees"] else "—"
        biz_rows = [("Sector", d["sector"]), ("Industry", d["industry"]), ("Employees", emp)]
        if d["website"]:
            biz_rows.append(("Website", f'<link href="{d["website"]}">{d["website"]}</link>'))
        s.append(one_col(biz_rows))
        s.append(Spacer(1, 6))
        if d["desc"]:
            s.append(Paragraph(d["desc"], S_desc))
        s.append(Spacer(1, 10))

        # filler pushes the last section down toward the bottom margin,
        # so the page looks full instead of trailing off with blank space
        if extra_pts:
            s.append(Spacer(1, extra_pts))

        # resources
        quartr  = f"https://web.quartr.com/search?query={d['ticker']}"
        sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={d['ticker']}&type=10-K&owner=include&count=10"
        s += section("Resources")
        s.append(Spacer(1, 4))
        res = [("Quartr — Earnings Calls & Transcripts",
                f'<link href="{quartr}">{quartr}</link>'),
               ("SEC Filings — 10-K / 10-Q",
                f'<link href="{sec_url}">EDGAR Search: {d["ticker"]}</link>')]
        if d["website"]:
            res.append(("Investor Relations", f'<link href="{d["website"]}">{d["website"]}</link>'))
        s.append(one_col(res))
        return s

    # ── binary search: max filler that keeps same page count ─────────
    class _Counter(SimpleDocTemplate):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.pg = 0
        def handle_pageEnd(self):
            self.pg += 1
            super().handle_pageEnd()

    def count_pages(filler_pts=0):
        tmp = io.BytesIO()
        c = _Counter(tmp, pagesize=letter,
                     leftMargin=L_MAR, rightMargin=R_MAR,
                     topMargin=T_MAR, bottomMargin=B_MAR + 22)
        c.build(make_story(filler_pts))
        return c.pg

    base_pages = count_pages()

    lo, hi = 0.0, float(USABLE_H)
    for _ in range(8):
        mid = (lo + hi) / 2
        if count_pages(mid) <= base_pages:
            lo = mid
        else:
            hi = mid

    doc = SimpleDocTemplate(buf, pagesize=letter,
        leftMargin=L_MAR, rightMargin=R_MAR,
        topMargin=T_MAR, bottomMargin=B_MAR + 22)
    doc.build(make_story(lo), onFirstPage=draw_footer, onLaterPages=draw_footer)
    buf.seek(0)
    return buf


# ── UI ────────────────────────────────────────────────────────────────

_b64 = logo_b64(white=False)
_logo_tag = (
    f'<div style="background:white;border-radius:8px;padding:8px 12px;display:inline-block;margin-bottom:10px;">'
    f'<img src="data:image/png;base64,{_b64}" style="height:44px;display:block;"/>'
    f'</div>'
) if _b64 else "<span style='color:white;font-size:1.5rem;font-weight:700;'>MCM</span>"
st.markdown(f"""
<div class="mc-header">
  <div class="mc-header-left">
    {_logo_tag}
    <p style="margin:6px 0 0 0;">Enter any ticker symbol to generate a full equity tearsheet with PDF export</p>
  </div>
  <div class="mc-header-right">
    <b>Equity Tearsheet Generator</b><br/>
    Fintech Research Tool<br/>
    Powered by Yahoo Finance
  </div>
</div>
""", unsafe_allow_html=True)

with st.form("search_form"):
    col_in, col_btn = st.columns([4, 1])
    with col_in:
        ticker_input = st.text_input("", placeholder="Enter ticker(s) — e.g. V, MA, PYPL, ASTS",
                                     label_visibility="collapsed")
    with col_btn:
        generate = st.form_submit_button("Generate", use_container_width=True)

if generate and ticker_input.strip():
    tickers = [t.strip().upper() for t in ticker_input.replace(",", " ").split() if t.strip()]

    for sym in tickers:
        with st.spinner(f"Fetching {sym}..."):
            try:
                d = fetch(sym)
            except Exception as e:
                st.error(f"⚠️ {e}")
                continue

        perf_text, perf_val = pct_str(d["perf52"])
        perf_class = color_class(perf_val) if perf_val is not None else ""

        # company title bar
        st.markdown(f"""
        <div class="co-bar">
          <div>
            <div class="co-bar-name">{d['name']} &nbsp;<span style="font-size:1rem;color:#8C9DB5;">({d['ticker']})</span></div>
            <div class="co-bar-meta">{d['sector']} &nbsp;·&nbsp; {d['industry']} &nbsp;·&nbsp; {d['exchange']}</div>
          </div>
          <div class="co-bar-price">
            <div class="price">{fmt(d['price'])}</div>
            <div class="perf {perf_class}">52-Wk &nbsp;{perf_text}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # market data
        st.markdown('<div class="sec-label">Market Data</div>', unsafe_allow_html=True)
        hi52 = fmt(d["hi52"]) if d["hi52"] else "—"
        lo52 = fmt(d["lo52"]) if d["lo52"] else "—"
        div_y = f"{float(d['div_yield'])*100:.2f}%" if d["div_yield"] else "—"
        beta_s = f"{float(d['beta']):.2f}" if d["beta"] else "—"
        st.markdown(cards(
            ("Market Cap",       fmt(d["mktcap"]),   ""),
            ("Enterprise Value", fmt(d["ev"]),        ""),
            ("Cash & Equiv.",    fmt(d["cash"]),      ""),
            ("Total Debt",       fmt(d["debt"]),      ""),
            ("Free Cash Flow",   fmt(d["fcf"]),       ""),
        ), unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(cards(
            ("52-Wk High",    hi52,   ""),
            ("52-Wk Low",     lo52,   ""),
            ("Beta",          beta_s, ""),
            ("Dividend Yield",div_y,  ""),
            ("Shares Out.",   fmt(d["shares"], prefix=""), ""),
        ), unsafe_allow_html=True)

        # valuation
        st.markdown('<div class="sec-label">Valuation</div>', unsafe_allow_html=True)
        st.markdown(cards(
            ("P/E (TTM)",   mul(d["pe"]),     ""),
            ("P/E (Fwd)",   mul(d["fpe"]),    ""),
            ("EV/EBITDA",   mul(d["ev_ebt"]), ""),
            ("EV/Revenue",  mul(d["ev_rev"]), ""),
            ("Price/Book",  mul(d["pb"]),     ""),
        ), unsafe_allow_html=True)

        # financials
        st.markdown('<div class="sec-label">Financials (TTM)</div>', unsafe_allow_html=True)
        rev_g_txt, rev_g_val = pct_str(d["rev_g"])
        eps_g_txt, eps_g_val = pct_str(d["eps_g"])
        gm  = f"{float(d['gross_m'])*100:.1f}%"  if d["gross_m"]  else "—"
        em  = f"{float(d['ebitda_m'])*100:.1f}%" if d["ebitda_m"] else "—"
        nm  = f"{float(d['net_m'])*100:.1f}%"    if d["net_m"]    else "—"
        eps = f"${float(d['eps']):.2f}"           if d["eps"]      else "—"
        st.markdown(cards(
            ("Revenue",       fmt(d["rev"]),  ""),
            ("Rev. Growth",   rev_g_txt,      color_class(rev_g_val)),
            ("Gross Margin",  gm,             ""),
            ("EBITDA Margin", em,             ""),
            ("Net Margin",    nm,             ""),
        ), unsafe_allow_html=True)
        st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
        st.markdown(cards(
            ("EBITDA",      fmt(d["ebitda"]),  ""),
            ("Net Income",  fmt(d["ni"]),      ""),
            ("EPS (TTM)",   eps,               ""),
            ("EPS Growth",  eps_g_txt,         color_class(eps_g_val)),
            ("Free CF",     fmt(d["fcf"]),     ""),
        ), unsafe_allow_html=True)

        # business
        st.markdown('<div class="sec-label">Business</div>', unsafe_allow_html=True)
        emp = f"{int(d['employees']):,} employees" if d["employees"] else ""
        st.markdown(f"""
        <div class="co-desc">
          <b>{d['sector']}</b> · {d['industry']}{"  ·  " + emp if emp else ""}<br/><br/>
          {d['desc'] or "No description available."}
        </div>
        """, unsafe_allow_html=True)

        # resources
        quartr  = f"https://web.quartr.com/search?query={d['ticker']}"
        sec_url = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={d['ticker']}&type=10-K&owner=include&count=10"
        ir_url  = d["website"] or "#"
        st.markdown('<div class="sec-label">Resources</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="res-grid">
          <div class="res-card">
            <div class="res-card-label">Quartr — Earnings &amp; Transcripts</div>
            <a href="{quartr}" target="_blank">web.quartr.com → {d['ticker']}</a>
          </div>
          <div class="res-card">
            <div class="res-card-label">SEC Filings — 10-K / 10-Q</div>
            <a href="{sec_url}" target="_blank">EDGAR Search: {d['ticker']}</a>
          </div>
          <div class="res-card">
            <div class="res-card-label">Investor Relations</div>
            <a href="{ir_url}" target="_blank">{d['website'] or '—'}</a>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # PDF download
        st.markdown('<div class="sec-label" style="margin-top:24px">Download</div>', unsafe_allow_html=True)
        date_str = datetime.now().strftime("%Y%m%d")
        pdf_buf = build_pdf(d)
        st.download_button(
            label=f"⬇  Download {sym} Tearsheet PDF",
            data=pdf_buf,
            file_name=f"{sym}_tearsheet_{date_str}.pdf",
            mime="application/pdf",
            key=f"dl_{sym}",
        )

        st.markdown("<hr>", unsafe_allow_html=True)

elif generate:
    st.warning("Please enter at least one ticker symbol.")

st.markdown("""
<div class="mc-footer">
  Data sourced from Yahoo Finance · For informational purposes only · Not investment advice<br/>
  Manole Capital Management — Intern Research Tool
</div>
""", unsafe_allow_html=True)
