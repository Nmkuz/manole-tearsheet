"""
Manole Capital — Equity Tearsheet Generator
Usage:
  python3 tearsheet.py TICKER          # print to console
  python3 tearsheet.py TICKER --pdf    # save PDF to current directory
  python3 tearsheet.py V MA PYPL --pdf # batch PDF generation
"""

import sys
import yfinance as yf
from datetime import datetime


# ── formatting helpers ────────────────────────────────────────────────

def fmt(n, prefix="$"):
    if n is None or n == "N/A":
        return "N/A"
    try:
        n = float(n)
        if abs(n) >= 1e9:
            return f"{prefix}{n/1e9:.2f}B"
        elif abs(n) >= 1e6:
            return f"{prefix}{n/1e6:.2f}M"
        else:
            return f"{prefix}{n:,.0f}"
    except Exception:
        return "N/A"

def pct(n):
    if n is None or n == "N/A":
        return "N/A"
    try:
        return f"{float(n)*100:.1f}%"
    except Exception:
        return "N/A"

def mul(n):
    if n is None or n == "N/A":
        return "N/A"
    try:
        return f"{float(n):.1f}x"
    except Exception:
        return "N/A"

def wrap(text, width=68, indent="  "):
    words = text.split()
    lines, line = [], indent
    for w in words:
        if len(line) + len(w) + 1 > width:
            lines.append(line.rstrip())
            line = indent + w + " "
        else:
            line += w + " "
    if line.strip():
        lines.append(line.rstrip())
    return "\n".join(lines)


# ── data fetch ────────────────────────────────────────────────────────

def fetch(ticker_symbol):
    t = yf.Ticker(ticker_symbol)
    i = t.info
    return {
        "name":     i.get("longName", ticker_symbol),
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
        "ticker":   ticker_symbol.upper(),
    }


# ── console output ────────────────────────────────────────────────────

def console_tearsheet(d):
    div = "=" * 70
    sec = lambda s: f"\n── {s} " + "─" * (66 - len(s))
    row = lambda k, v: f"  {k:<22} {v}"

    lines = [
        div,
        f"  EQUITY TEARSHEET — {d['name']} ({d['ticker']})",
        f"  Generated: {datetime.now().strftime('%B %d, %Y')}",
        f"  Source: Yahoo Finance  |  Quartr: web.quartr.com",
        div,

        sec("MARKET DATA"),
        row("Current Price:",    fmt(d["price"])),
        row("Market Cap:",       fmt(d["mktcap"])),
        row("Enterprise Value:", fmt(d["ev"])),
        row("Cash & Equiv.:",    fmt(d["cash"])),
        row("Total Debt:",       fmt(d["debt"])),
        row("52-Week Return:",   pct(d["perf52"])),
        row("Beta:",             f"{float(d['beta']):.2f}" if d["beta"] else "N/A"),

        sec("FINANCIALS (TTM)"),
        row("Revenue:",          fmt(d["rev"])),
        row("Revenue Growth:",   pct(d["rev_g"])),
        row("EBITDA:",           fmt(d["ebitda"])),
        row("EBITDA Margin:",    pct(d["ebitda_m"])),
        row("Net Income:",       fmt(d["ni"])),
        row("EPS:",              f"${float(d['eps']):.2f}" if d["eps"] else "N/A"),
        row("EPS Growth:",       pct(d["eps_g"])),

        sec("VALUATION"),
        row("P/E (TTM):",        mul(d["pe"])),
        row("P/E (Fwd):",        mul(d["fpe"])),
        row("EV/EBITDA:",        mul(d["ev_ebt"])),
        row("EV/Revenue:",       mul(d["ev_rev"])),

        sec("BUSINESS"),
        row("Sector:",   d["sector"]),
        row("Industry:", d["industry"]),
        row("Website:",  d["website"]),
        "",
        wrap(d["desc"]) if d["desc"] else "  N/A",

        sec("RESOURCES"),
        row("Quartr:",        f"https://web.quartr.com/search?query={d['ticker']}"),
        row("SEC Filings:",   f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={d['ticker']}&type=10-K&dateb=&owner=include&count=10"),
        row("Inv. Relations:", d["website"]),

        "\n" + div,
    ]

    return "\n".join(lines)


# ── PDF output ────────────────────────────────────────────────────────

def pdf_tearsheet(d, output_path=None):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

    if output_path is None:
        date_str = datetime.now().strftime("%Y%m%d")
        output_path = f"{d['ticker']}_tearsheet_{date_str}.pdf"

    # ── palette ──────────────────────────────────────────────────────
    NAVY    = colors.HexColor("#0D1E3F")
    BLUE    = colors.HexColor("#1A55A3")
    SILVER  = colors.HexColor("#8C9DB5")
    LIGHT   = colors.HexColor("#EEF2F8")
    WHITE   = colors.white
    BLACK   = colors.HexColor("#1A1A1A")
    GREEN   = colors.HexColor("#1A7A4A")
    RED     = colors.HexColor("#B22222")

    # ── styles ───────────────────────────────────────────────────────
    def style(name, **kw):
        defaults = dict(fontName="Helvetica", fontSize=9, leading=13,
                        textColor=BLACK, spaceAfter=0, spaceBefore=0)
        defaults.update(kw)
        return ParagraphStyle(name, **defaults)

    S_header_co  = style("co",    fontName="Helvetica-Bold", fontSize=18,
                          textColor=WHITE, leading=22)
    S_header_sub = style("sub",   fontSize=9, textColor=SILVER, leading=12)
    S_section    = style("sec",   fontName="Helvetica-Bold", fontSize=8,
                          textColor=BLUE, leading=10, spaceBefore=4)
    S_label      = style("lbl",   fontSize=8.5, textColor=SILVER)
    S_value      = style("val",   fontName="Helvetica-Bold", fontSize=9,
                          textColor=BLACK)
    S_desc       = style("desc",  fontSize=8.5, leading=13, textColor=BLACK)
    S_link       = style("link",  fontSize=8, textColor=BLUE, leading=12)
    S_footer     = style("foot",  fontSize=7, textColor=SILVER,
                          alignment=TA_CENTER)

    # ── helpers ──────────────────────────────────────────────────────
    def color_value(raw, fmt_fn):
        """Color positive/negative percentages."""
        text = fmt_fn(raw)
        if raw is not None:
            try:
                v = float(raw)
                c = GREEN.hexval() if v >= 0 else RED.hexval()
                return f'<font color="#{c[2:]}">{text}</font>'
            except Exception:
                pass
        return text

    def section_header(title):
        return [
            HRFlowable(width="100%", thickness=0.5, color=BLUE, spaceAfter=3),
            Paragraph(title.upper(), S_section),
        ]

    def metric_table(rows):
        """rows = [(label, value), ...]"""
        data = [[Paragraph(k, S_label), Paragraph(v, S_value)] for k, v in rows]
        t = Table(data, colWidths=[2.2*inch, 2.8*inch])
        t.setStyle(TableStyle([
            ("VALIGN",      (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",  (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [WHITE, LIGHT]),
            ("LEFTPADDING", (0, 0), (0, -1), 6),
        ]))
        return t

    def two_col_metrics(left_rows, right_rows):
        """Two side-by-side metric blocks."""
        def col(rows):
            return [
                [Paragraph(k, S_label), Paragraph(v, S_value)]
                for k, v in rows
            ]
        left  = col(left_rows)
        right = col(right_rows)
        combined = []
        for i in range(max(len(left), len(right))):
            lr = left[i]  if i < len(left)  else [Paragraph("", S_label), Paragraph("", S_value)]
            rr = right[i] if i < len(right) else [Paragraph("", S_label), Paragraph("", S_value)]
            combined.append(lr + [Paragraph("", S_label)] + rr)
        t = Table(combined, colWidths=[1.6*inch, 1.4*inch, 0.3*inch, 1.6*inch, 1.4*inch])
        t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS",(0, 0), (-1, -1), [WHITE, LIGHT]),
            ("LEFTPADDING",   (0, 0), (0, -1), 6),
            ("LEFTPADDING",   (3, 0), (3, -1), 6),
        ]))
        return t

    # ── document ─────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.65*inch, rightMargin=0.65*inch,
        topMargin=0.5*inch,   bottomMargin=0.65*inch,
    )

    story = []

    # Header block
    header_data = [[
        Paragraph(f"{d['name']}<br/><font size='11' color='#8C9DB5'>{d['ticker']}  ·  {d['sector']}  ·  {d['industry']}</font>", S_header_co),
        Paragraph(
            f"<b>Manole Capital Management</b><br/>"
            f"Equity Tearsheet<br/>"
            f"{datetime.now().strftime('%B %d, %Y')}",
            style("hdr_right", fontSize=8, textColor=SILVER, alignment=TA_RIGHT, leading=13)
        ),
    ]]
    header_tbl = Table(header_data, colWidths=[4.4*inch, 2.3*inch])
    header_tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, -1), NAVY),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",   (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 14),
        ("LEFTPADDING",  (0, 0), (0, -1), 14),
        ("RIGHTPADDING", (1, 0), (1, -1), 14),
        ("ROUNDEDCORNERS", [4]),
    ]))
    story.append(header_tbl)
    story.append(Spacer(1, 10))

    # Market data + Valuation (two columns)
    story += section_header("Market Data & Valuation")
    story.append(Spacer(1, 4))
    story.append(two_col_metrics(
        [
            ("Current Price",    fmt(d["price"])),
            ("Market Cap",       fmt(d["mktcap"])),
            ("Enterprise Value", fmt(d["ev"])),
            ("Cash & Equiv.",    fmt(d["cash"])),
            ("Total Debt",       fmt(d["debt"])),
            ("52-Week Return",   color_value(d["perf52"], pct)),
            ("Beta",             f"{float(d['beta']):.2f}" if d["beta"] else "N/A"),
        ],
        [
            ("P/E (TTM)",    mul(d["pe"])),
            ("P/E (Fwd)",    mul(d["fpe"])),
            ("EV/EBITDA",    mul(d["ev_ebt"])),
            ("EV/Revenue",   mul(d["ev_rev"])),
        ],
    ))
    story.append(Spacer(1, 10))

    # Financials (TTM)
    story += section_header("Financials (TTM)")
    story.append(Spacer(1, 4))
    story.append(two_col_metrics(
        [
            ("Revenue",       fmt(d["rev"])),
            ("Revenue Growth",color_value(d["rev_g"],  pct)),
            ("EBITDA",        fmt(d["ebitda"])),
            ("EBITDA Margin", pct(d["ebitda_m"])),
        ],
        [
            ("Net Income",  fmt(d["ni"])),
            ("EPS (TTM)",   f"${float(d['eps']):.2f}" if d["eps"] else "N/A"),
            ("EPS Growth",  color_value(d["eps_g"], pct)),
        ],
    ))
    story.append(Spacer(1, 10))

    # Business
    story += section_header("Business")
    story.append(Spacer(1, 4))
    story.append(metric_table([
        ("Sector",   d["sector"]),
        ("Industry", d["industry"]),
        ("Website",  f'<link href="{d["website"]}">{d["website"]}</link>'),
    ]))
    story.append(Spacer(1, 6))
    if d["desc"]:
        story.append(Paragraph(d["desc"], S_desc))
    story.append(Spacer(1, 10))

    # Resources
    story += section_header("Resources")
    story.append(Spacer(1, 4))
    quartr_url = f"https://web.quartr.com/search?query={d['ticker']}"
    sec_url    = f"https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={d['ticker']}&type=10-K&dateb=&owner=include&count=10"
    story.append(metric_table([
        ("Quartr (Earnings Calls)",
         f'<link href="{quartr_url}">{quartr_url}</link>'),
        ("SEC Filings (10-K / 10-Q)",
         f'<link href="{sec_url}">EDGAR — {d["ticker"]}</link>'),
        ("Investor Relations",
         f'<link href="{d["website"]}">{d["website"]}</link>'),
    ]))
    story.append(Spacer(1, 14))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.4, color=SILVER))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Data sourced from Yahoo Finance. For informational purposes only — not investment advice. "
        "Generated by Manole Capital intern tearsheet tool.",
        S_footer,
    ))

    doc.build(story)
    return output_path


# ── entry point ───────────────────────────────────────────────────────

if __name__ == "__main__":
    args    = [a for a in sys.argv[1:] if not a.startswith("--")]
    as_pdf  = "--pdf" in sys.argv

    if not args:
        args = [input("Ticker: ").strip().upper()]

    for sym in args:
        sym = sym.upper()
        print(f"Fetching {sym}...", flush=True)
        try:
            data = fetch(sym)
        except Exception as e:
            print(f"  Error fetching {sym}: {e}")
            continue

        if as_pdf:
            path = pdf_tearsheet(data)
            print(f"  Saved → {path}")
        else:
            print(console_tearsheet(data))
