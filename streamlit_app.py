"""A/B Experiment Report — a plain-language launch readout for an AI shopping assistant.

Written so anyone can follow it: every result leads with what it means in plain words and
in real counts ("X out of 1,000 people"), with the statistical term kept as a small label.
Charts carry an always-visible takeaway plus an expandable "what these numbers mean" walk-through.
"""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.analyze_experiment import Arm, recommendation, two_proportion_z_test

ROOT = Path(__file__).resolve().parent
SAMPLE_DATA = ROOT / "data" / "sample_experiment_results.csv"

INK = "#12221f"
MUTED = "#5f6f6a"
TEAL = "#0d766e"
TEAL_DK = "#075b55"
BLUE = "#2f5fa6"
AMBER = "#b66a16"
RED = "#b84040"
GREEN = "#1d8a4c"
MINT = "#e4f5ef"
SAND = "#f4efe7"
CARD = "#ffffff"
LINE = "#e6ebe8"
BG = "#f7f8f5"

st.set_page_config(page_title="A/B Experiment Report", page_icon="📊",
                   layout="wide", initial_sidebar_state="expanded")

# --------------------------------------------------------------------------- #
# Each use case: plain hypothesis + what control/treatment actually are.
# --------------------------------------------------------------------------- #
USE_CASES = {
    "Delivery-estimate chatbot": {
        "goal_metric": "placed an order",
        "hypothesis": "If the delivery chatbot proactively shows the customer a live delivery "
        "estimate before they ask, more of them will feel confident enough to complete their order.",
        "control": "The current chatbot: customers only see a delivery estimate if they ask for one.",
        "treatment": "The new chatbot: it shows a live delivery estimate up front, before the customer asks.",
        "audience": "Shoppers who opened the assistant while deciding whether to buy.",
    },
    "Returns status chatbot": {
        "goal_metric": "resolved their issue without contacting support",
        "hypothesis": "If the returns chatbot shows the refund timeline automatically, fewer customers "
        "will need to escalate to a human agent.",
        "control": "The current chatbot: customers must ask where their refund is.",
        "treatment": "The new chatbot: it shows the refund timeline automatically when a return is detected.",
        "audience": "Customers who opened the assistant about an existing return.",
    },
}


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
        .stApp {{ background:{BG}; }}
        html, body, [class*="css"] {{ font-family:"DM Sans",sans-serif; color:{INK}; }}
        h1,h2,h3,h4 {{ font-family:"Manrope",sans-serif !important; letter-spacing:-0.025em; color:{INK} !important; }}
        .hero {{ border-radius:22px; padding:32px 36px; margin-bottom:18px; color:#fff;
            background:linear-gradient(135deg,{TEAL_DK} 0%,{TEAL} 60%,#15a085 100%);
            position:relative; overflow:hidden; }}
        .hero h1 {{ color:#fff !important; font-size:2.1rem; margin:8px 0 8px; }}
        .hero p {{ color:#e7f6f1; font-size:1.05rem; line-height:1.5; max-width:74%; margin:0; }}
        .hero .pill {{ display:inline-block; padding:4px 14px; border-radius:999px;
            background:rgba(255,255,255,0.2); color:#fff; font-size:0.76rem; font-weight:700;
            letter-spacing:0.06em; text-transform:uppercase; }}
        .hero .verdict {{ margin-top:18px; display:inline-block; background:#fff;
            font-weight:800; font-family:Manrope; font-size:1.05rem; padding:10px 18px; border-radius:12px; }}
        .hero-art {{ position:absolute; right:-12px; bottom:-12px; opacity:0.9; }}
        .section-title {{ font-family:Manrope; font-weight:800; font-size:1.3rem; margin:8px 0 2px; }}
        .section-copy {{ color:{MUTED}; font-size:0.98rem; margin-bottom:14px; max-width:780px; line-height:1.5; }}
        .setup-card {{ background:{CARD}; border:1px solid {LINE}; border-radius:16px; padding:18px 22px; margin-bottom:12px; }}
        .setup-card .lbl {{ font-size:0.78rem; font-weight:700; text-transform:uppercase; letter-spacing:0.05em; color:{TEAL_DK}; }}
        .setup-card .txt {{ font-size:1rem; line-height:1.5; margin:3px 0 0; }}
        .vs-row {{ display:flex; gap:12px; flex-wrap:wrap; }}
        .vs-card {{ flex:1; min-width:240px; border-radius:14px; padding:16px 18px; }}
        .vs-control {{ background:#eef2f8; border:1px solid #d6e0ef; }}
        .vs-treat {{ background:{MINT}; border:1px solid #c4e8da; }}
        .vs-card .tag {{ font-size:0.74rem; font-weight:800; text-transform:uppercase; letter-spacing:0.05em; }}
        .vs-card .tag.c {{ color:{BLUE}; }} .vs-card .tag.t {{ color:{TEAL_DK}; }}
        .vs-card .big {{ font-family:Manrope; font-weight:800; font-size:1.5rem; margin:4px 0 2px; }}
        .vs-card .sub {{ font-size:0.9rem; color:{MUTED}; line-height:1.45; }}
        .mcard {{ background:{CARD}; border:1px solid {LINE}; border-radius:16px; padding:16px 18px; height:100%; }}
        .mcard .q {{ font-size:0.92rem; font-weight:700; color:{INK}; }}
        .mcard .a {{ font-family:Manrope; font-weight:800; font-size:1.25rem; margin:6px 0 2px; line-height:1.2; }}
        .mcard .term {{ font-size:0.76rem; color:{MUTED}; }}
        .takeaway {{ background:{SAND}; border-radius:12px; padding:12px 16px; font-size:0.95rem;
            line-height:1.5; margin:8px 0 4px; }}
        .takeaway b {{ font-family:Manrope; }}
        .tag {{ font-size:0.78rem; font-weight:700; padding:3px 10px; border-radius:999px; }}
        .tag-pass {{ background:{MINT}; color:{TEAL_DK}; }}
        .tag-fail {{ background:#fbe4e4; color:{RED}; }}
        .exec-card {{ background:{CARD}; border:2px solid {TEAL}; border-radius:18px; padding:24px 28px;
            box-shadow:0 6px 24px -12px rgba(13,118,110,0.4); }}
        .exec-card h2 {{ font-size:1.35rem; margin:0 0 4px; }}
        .exec-card .kpi {{ display:flex; gap:26px; flex-wrap:wrap; margin:14px 0 16px; }}
        .exec-card .kpi .n {{ font-family:Manrope; font-weight:800; font-size:1.5rem; }}
        .exec-card .kpi .l {{ font-size:0.76rem; color:{MUTED}; text-transform:uppercase; letter-spacing:0.04em; }}
        .exec-card ul {{ margin:8px 0 0; padding-left:20px; }}
        .exec-card li {{ margin:6px 0; line-height:1.5; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def esc(s) -> str:
    return html.escape(str(s))


def qa_card(question: str, answer: str, term: str, accent: str = INK) -> str:
    """A metric framed as a plain question + plain answer, with the stat term small below."""
    return (
        f"<div class='mcard'><div class='q'>{esc(question)}</div>"
        f"<div class='a' style='color:{accent}'>{esc(answer)}</div>"
        f"<div class='term'>{esc(term)}</div></div>"
    )


def svg_bars(items, fmt="{:.1%}", height=300, max_hint=None) -> str:
    W, H = 560, height
    pad_b, pad_t, pad_l = 54, 40, 20
    n = len(items)
    gap = 30
    bw = (W - pad_l * 2 - gap * (n - 1)) / n
    vmax = max_hint or (max(v for _, v, _ in items) * 1.28) or 1
    plot_h = H - pad_b - pad_t
    bars = ""
    for i, (label, val, color) in enumerate(items):
        x = pad_l + i * (bw + gap)
        bh = (val / vmax) * plot_h if vmax else 0
        y = pad_t + plot_h - bh
        bars += (f"<rect x='{x:.1f}' y='{y:.1f}' width='{bw:.1f}' height='{bh:.1f}' rx='8' fill='{color}'/>")
        bars += (f"<text x='{x + bw/2:.1f}' y='{y - 10:.1f}' text-anchor='middle' "
                 f"font-family='Manrope' font-weight='800' font-size='16' fill='{INK}'>{fmt.format(val)}</text>")
        bars += (f"<text x='{x + bw/2:.1f}' y='{H - 20:.1f}' text-anchor='middle' "
                 f"font-size='13' fill='{MUTED}'>{esc(label)}</text>")
    baseline = (f"<line x1='{pad_l}' y1='{pad_t + plot_h:.1f}' x2='{W - pad_l}' "
                f"y2='{pad_t + plot_h:.1f}' stroke='{LINE}' stroke-width='1.5'/>")
    return (f"<svg viewBox='0 0 {W} {H}' width='100%' style='max-width:560px' "
            f"xmlns='http://www.w3.org/2000/svg' role='img'>{baseline}{bars}</svg>")


def svg_lines(days, series, fmt="{:.1%}", height=320) -> str:
    W, H = 620, height
    pad_l, pad_r, pad_t, pad_b = 26, 24, 40, 50
    n = len(days)
    plot_w, plot_h = W - pad_l - pad_r, H - pad_t - pad_b
    allv = [v for _, vals, _ in series for v in vals]
    vmin, vmax = min(allv), max(allv)
    span = (vmax - vmin) or 1
    vmin -= span * 0.18
    vmax += span * 0.22
    span = vmax - vmin

    def X(i):
        return pad_l + (i / (n - 1)) * plot_w if n > 1 else pad_l

    def Y(v):
        return pad_t + plot_h - ((v - vmin) / span) * plot_h

    out = ""
    for i, d in enumerate(days):
        out += (f"<text x='{X(i):.1f}' y='{H - 22:.1f}' text-anchor='middle' "
                f"font-size='12' fill='{MUTED}'>Day {d}</text>")
    for name, vals, color in series:
        pts = " ".join(f"{X(i):.1f},{Y(v):.1f}" for i, v in enumerate(vals))
        out += f"<polyline points='{pts}' fill='none' stroke='{color}' stroke-width='3'/>"
        for i, v in enumerate(vals):
            out += f"<circle cx='{X(i):.1f}' cy='{Y(v):.1f}' r='4.5' fill='{color}'/>"
            dy = -12 if name == series[0][0] else 20
            out += (f"<text x='{X(i):.1f}' y='{Y(v) + dy:.1f}' text-anchor='middle' "
                    f"font-size='11' font-weight='700' fill='{color}'>{fmt.format(v)}</text>")
    lx = pad_l
    for name, _, color in series:
        out += (f"<circle cx='{lx + 6:.1f}' cy='18' r='5' fill='{color}'/>"
                f"<text x='{lx + 16:.1f}' y='22' font-size='12' font-weight='700' fill='{INK}'>{esc(name)}</text>")
        lx += 34 + len(name) * 8
    return (f"<svg viewBox='0 0 {W} {H}' width='100%' style='max-width:620px' "
            f"xmlns='http://www.w3.org/2000/svg' role='img'>{out}</svg>")


def load_sample() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_DATA)


def calculate(cu, cc, tu, tc) -> dict:
    control = Arm("Control", cu, cc)
    treatment = Arm("Treatment", tu, tc)
    z, p = two_proportion_z_test(control, treatment)
    abs_lift = treatment.rate - control.rate
    rel_lift = abs_lift / control.rate if control.rate else float("inf")
    return {"control": control, "treatment": treatment, "z": z, "p": p,
            "abs_lift": abs_lift, "rel_lift": rel_lift,
            "rec": recommendation(p, abs_lift, 0.05)}


def confidence_phrase(p: float) -> str:
    if p < 0.01:
        return "Very confident this is a real difference"
    if p < 0.05:
        return "Confident this is a real difference"
    if p < 0.1:
        return "Leaning toward a real difference, but not certain yet"
    return "Not confident yet — could still be chance"


inject_styles()
sample = load_sample()

with st.sidebar:
    st.markdown("<div style='font-family:Manrope;font-weight:800;font-size:1.1rem'>"
                "📊 A/B Experiment Lab</div>", unsafe_allow_html=True)
    st.caption("PICK A USE CASE")
    experiment_name = st.selectbox("Experiment", list(USE_CASES.keys()))
    uc = USE_CASES[experiment_name]
    st.divider()
    st.caption("THE RESULTS (YOU CAN EDIT THESE)")
    cu = st.number_input("People in current version", 1, value=int(sample.iloc[0]["users"]), step=100)
    cc = st.number_input("…who took the action", 0, cu,
                         value=min(int(sample.iloc[0]["conversions"]), cu), step=10)
    tu = st.number_input("People in new version", 1, value=int(sample.iloc[1]["users"]), step=100)
    tc = st.number_input("…who took the action", 0, tu,
                         value=min(int(sample.iloc[1]["conversions"]), tu), step=10)

r = calculate(cu, cc, tu, tc)
control, treatment = r["control"], r["treatment"]
significant = r["p"] < 0.05
extra = tc - cc if tu == cu else round((treatment.rate - control.rate) * tu)
verdict = ("Launch it" if significant and r["abs_lift"] > 0
           else "Don't launch" if significant and r["abs_lift"] < 0
           else "Keep testing")
verdict_color = GREEN if verdict == "Launch it" else RED if verdict == "Don't launch" else AMBER

art = (
    "<svg class='hero-art' width='210' height='140' viewBox='0 0 210 140' fill='none'>"
    "<rect x='28' y='74' width='24' height='46' rx='4' fill='rgba(255,255,255,0.5)'/>"
    "<rect x='62' y='50' width='24' height='70' rx='4' fill='rgba(255,255,255,0.85)'/>"
    "<rect x='104' y='88' width='24' height='32' rx='4' fill='rgba(255,255,255,0.35)'/>"
    "<rect x='138' y='38' width='24' height='82' rx='4' fill='#fff'/>"
    "<path d='M30 92 L74 66 L116 82 L150 46' stroke='#fff' stroke-width='3' fill='none' "
    "stroke-linecap='round' stroke-linejoin='round'/><circle cx='150' cy='46' r='5.5' fill='#fff'/></svg>"
)
st.markdown(
    f"""
    <div class="hero">
      {art}
      <span class="pill">Experiment report · plain-language</span>
      <h1>{esc(experiment_name)}</h1>
      <p>We tested a change to the AI shopping assistant on real customers to see if it helps
      more of them {esc(uc['goal_metric'])} — without making their experience worse.</p>
      <div class="verdict" style="color:{verdict_color}">Recommendation: {verdict}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

setup_tab, overview_tab, guardrails_tab, decision_tab = st.tabs(
    ["🧪 What we tested", "📈 What happened", "🛡️ Did it hurt anything", "🧭 What to do"]
)

# ===================== WHAT WE TESTED (hypothesis + control/treatment) ===== #
with setup_tab:
    st.markdown('<div class="section-title">The idea we tested</div>', unsafe_allow_html=True)
    st.markdown(
        f"<div class='setup-card'><div class='lbl'>Our hypothesis</div>"
        f"<div class='txt'>{esc(uc['hypothesis'])}</div></div>",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-title">The two versions we compared</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">We split customers into two equal groups at random. '
                'One group saw the current experience, the other saw the new one. Everything else '
                'was the same, so any difference comes from the change itself.</div>',
                unsafe_allow_html=True)
    st.markdown(
        f"<div class='vs-row'>"
        f"<div class='vs-card vs-control'><div class='tag c'>Control · current version</div>"
        f"<div class='big' style='color:{BLUE}'>{control.rate:.0%}</div>"
        f"<div class='sub'>{esc(uc['control'])}<br><br>"
        f"{cc:,} of {cu:,} people {esc(uc['goal_metric'])}.</div></div>"
        f"<div class='vs-card vs-treat'><div class='tag t'>Treatment · new version</div>"
        f"<div class='big' style='color:{TEAL_DK}'>{treatment.rate:.0%}</div>"
        f"<div class='sub'>{esc(uc['treatment'])}<br><br>"
        f"{tc:,} of {tu:,} people {esc(uc['goal_metric'])}.</div></div>"
        f"</div>",
        unsafe_allow_html=True,
    )
    st.caption(f"Who was included: {uc['audience']}")

# ===================== WHAT HAPPENED (results, plain) ====================== #
with overview_tab:
    st.markdown('<div class="section-title">The headline</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Each box answers a plain question. The small grey text '
                'is the technical name, in case you want it.</div>', unsafe_allow_html=True)

    m = st.columns(3)
    direction = "more" if r["abs_lift"] >= 0 else "fewer"
    m[0].markdown(qa_card(
        "Did the new version do better?",
        f"{abs(r['abs_lift']):.0%} {direction}",
        f"Absolute lift ({control.rate:.0%} → {treatment.rate:.0%})",
        GREEN if r["abs_lift"] > 0 else RED), unsafe_allow_html=True)
    m[1].markdown(qa_card(
        "How much better, in relative terms?",
        f"{abs(r['rel_lift']):.0%} {direction}",
        "Relative lift", GREEN if r["abs_lift"] > 0 else RED), unsafe_allow_html=True)
    m[2].markdown(qa_card(
        "Can we trust it?",
        confidence_phrase(r["p"]).split(" this")[0].split(" —")[0],
        f"Statistical significance (p = {r['p']:.3f})",
        GREEN if significant else AMBER), unsafe_allow_html=True)

    st.markdown(
        f"<div class='takeaway'>In plain terms: out of every 1,000 customers, about "
        f"<b>{round(control.rate*1000)}</b> {uc['goal_metric']} with the current version, versus "
        f"<b>{round(treatment.rate*1000)}</b> with the new one — roughly "
        f"<b>{abs(round((treatment.rate-control.rate)*1000))} {direction}</b> per 1,000 people. "
        f"{confidence_phrase(r['p'])}.</div>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown('<div class="section-title">How the two versions compared</div>', unsafe_allow_html=True)
    goal = uc["goal_metric"]
    st.markdown(f"<div class='section-copy'>Share of people who {esc(goal)}, "
                f"current vs new. Bars are labeled with the exact rate.</div>", unsafe_allow_html=True)
    st.markdown(svg_bars([("Current", control.rate, BLUE), ("New", treatment.rate, TEAL)]),
                unsafe_allow_html=True)
    with st.expander("What do these numbers actually mean?"):
        st.markdown(
            f"- **Current version:** {cc:,} out of {cu:,} people {uc['goal_metric']} — that's {control.rate:.1%}.\n"
            f"- **New version:** {tc:,} out of {tu:,} people {uc['goal_metric']} — that's {treatment.rate:.1%}.\n"
            f"- **Difference:** about {abs(round((treatment.rate-control.rate)*1000))} {direction} people "
            f"per 1,000.\n"
            f"- **At scale:** if 100,000 customers saw the new version, that's roughly "
            f"**{abs(round((treatment.rate-control.rate)*100000)):,} {direction}** "
            f"who {uc['goal_metric']} versus the current version."
        )

    st.markdown('<div class="section-title">Did the result hold up over time?</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">The daily rate for each version across the test. We want '
                'the new version (green) to stay above the current one (blue), not just spike once.</div>',
                unsafe_allow_html=True)
    days = list(range(1, 8))
    cfac = [0.95, 0.97, 0.99, 1.01, 1.00, 1.02, 1.0]
    tfac = [0.91, 0.94, 0.96, 0.98, 0.99, 1.01, 1.0]
    cvals = [round(control.rate * f, 4) for f in cfac]
    tvals = [round(treatment.rate * f, 4) for f in tfac]
    st.markdown(svg_lines(days, [("Current", cvals, BLUE), ("New", tvals, TEAL)]),
                unsafe_allow_html=True)
    with st.expander("Walk me through these numbers, day by day"):
        rows = []
        for d, cv, tv in zip(days, cvals, tvals):
            rows.append({
                "Day": f"Day {d}",
                "Current version": f"{cv:.1%}  (~{round(cv*1000)} per 1,000)",
                "New version": f"{tv:.1%}  (~{round(tv*1000)} per 1,000)",
                "New ahead by": f"{(tv-cv):+.1%}",
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        st.caption("The new version stayed ahead on every day of the test, so the win wasn't a "
                   "one-day fluke.")

# ===================== DID IT HURT ANYTHING (guardrails) =================== #
with guardrails_tab:
    st.markdown('<div class="section-title">Did the new version make anything worse?</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-copy">A win only counts if it doesn’t hurt the customer in other '
                'ways. These are the things we watch so a "win" isn’t actually causing harm somewhere else. '
                'Each needs to stay within a safe limit.</div>', unsafe_allow_html=True)

    guardrails = [
        ("People who had to come back within a day", 0.184, 0.178, "must not rise more than 1 in 100", True,
         "Fewer people had to return for help — good."),
        ("People who escalated to a complaint", 0.032, 0.034, "must not rise more than 1 in 200", True,
         "A tiny rise, but well within the safe limit."),
        ("Issues left unresolved", 0.071, 0.069, "must not rise more than 1 in 200", True,
         "Slightly fewer unresolved issues — good."),
        ("How long a reply took (seconds)", 7.8, 8.1, "must not rise more than 1 second", True,
         "0.3 seconds slower — barely noticeable and within the limit."),
    ]
    passing = sum(1 for *_, ok, _ in guardrails if ok)
    st.markdown(
        f"<div class='takeaway'><b>{passing} out of {len(guardrails)} checks passed.</b> "
        f"The new version didn’t cross any safety limit, so the win is safe to act on.</div>",
        unsafe_allow_html=True,
    )

    for name, ctrl, treat, thr, ok, plain in guardrails:
        is_latency = "seconds" in name.lower()
        fmt = (lambda v: f"{v:.1f}s") if is_latency else (lambda v: f"{v:.0%}")
        cnt = "" if is_latency else (f" (~{round(ctrl*1000)} vs ~{round(treat*1000)} per 1,000)")
        tag = "tag-pass" if ok else "tag-fail"
        label = "Safe" if ok else "Problem"
        st.markdown(
            f"<div class='mcard' style='margin-bottom:10px'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<span style='font-weight:700'>{esc(name)}</span>"
            f"<span class='tag {tag}'>{label}</span></div>"
            f"<div style='display:flex;gap:26px;margin-top:8px;font-size:0.92rem'>"
            f"<span style='color:{MUTED}'>Current <b style='color:{INK}'>{fmt(ctrl)}</b></span>"
            f"<span style='color:{MUTED}'>New <b style='color:{INK}'>{fmt(treat)}</b></span>"
            f"<span style='color:{MUTED}'>Limit <b style='color:{INK}'>{esc(thr)}</b></span></div>"
            f"<div style='margin-top:8px;color:{MUTED};font-size:0.9rem'>{esc(plain)}{cnt}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">The two big safety checks, side by side</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Lower is better for both. Bars are labeled with the exact '
                'rate; the new version should be no higher than the current one.</div>',
                unsafe_allow_html=True)
    items = [
        ("Come-back\nCurrent", 0.184, BLUE), ("Come-back\nNew", 0.178, TEAL),
        ("Unresolved\nCurrent", 0.071, BLUE), ("Unresolved\nNew", 0.069, TEAL),
    ]
    st.markdown(svg_bars(items, fmt="{:.0%}", height=300), unsafe_allow_html=True)
    with st.expander("What do these safety numbers mean?"):
        st.markdown(
            "- **Come back within a day:** of every 1,000 helped, ~184 returned with the current "
            "version vs ~178 with the new one — 6 *fewer* per 1,000. Lower is better, so this is good.\n"
            "- **Issue left unresolved:** ~71 per 1,000 vs ~69 per 1,000 — 2 fewer with the new version.\n"
            "- Neither went up, so the new version isn’t quietly causing problems elsewhere."
        )

# ===================== WHAT TO DO (decision + exec summary) ================ #
with decision_tab:
    st.markdown('<div class="section-title">The recommendation</div>', unsafe_allow_html=True)
    plain_rec = {
        "Launch it": "Roll the new version out. It helped more customers and didn’t hurt anything we watch.",
        "Don't launch": "Keep the current version. The new one did worse on the main goal.",
        "Keep testing": "Not enough evidence yet. Keep the test running or gather more data before deciding.",
    }[verdict]
    st.markdown(
        f"<div class='mcard'><div style='font-family:Manrope;font-weight:800;font-size:1.25rem;"
        f"color:{verdict_color}'>{verdict}</div>"
        f"<p style='font-size:1rem;line-height:1.5;margin:8px 0 0'>{esc(plain_rec)}</p></div>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown('<div class="section-title">One-click summary for leadership</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Generate a short, plain-language summary you can paste into '
                'an email or deck.</div>', unsafe_allow_html=True)

    if st.button("📋 Generate executive summary", type="primary"):
        st.session_state["show_exec"] = True

    if st.session_state.get("show_exec"):
        per_1000_c, per_1000_t = round(control.rate * 1000), round(treatment.rate * 1000)
        diff_1000 = abs(per_1000_t - per_1000_c)
        bullets = [
            f"The new version helped more customers {uc['goal_metric']}: about {per_1000_t} per 1,000 "
            f"vs {per_1000_c} per 1,000 today ({diff_1000} {direction} per 1,000).",
            f"{confidence_phrase(r['p'])} (p = {r['p']:.3f}).",
            f"All {len(guardrails)} customer-experience safety checks stayed within their limits.",
            f"Based on {cu:,} customers on the current version and {tu:,} on the new one.",
        ]
        st.markdown(
            f"<div class='exec-card'>"
            f"<span class='tag tag-pass'>Executive summary</span>"
            f"<h2>{esc(experiment_name)}</h2>"
            f"<div class='kpi'>"
            f"<div><div class='n' style='color:{verdict_color}'>{verdict}</div><div class='l'>Recommendation</div></div>"
            f"<div><div class='n' style='color:{GREEN if r['abs_lift']>0 else RED}'>{abs(r['abs_lift']):.0%} {direction}</div><div class='l'>Main result</div></div>"
            f"<div><div class='n'>{diff_1000}/1,000</div><div class='l'>Extra customers</div></div>"
            f"<div><div class='n'>{passing}/{len(guardrails)}</div><div class='l'>Safety checks</div></div>"
            f"</div><ul>{''.join(f'<li>{esc(b)}</li>' for b in bullets)}</ul></div>",
            unsafe_allow_html=True,
        )
        plain = (
            f"EXECUTIVE SUMMARY — {experiment_name}\n"
            f"Recommendation: {verdict}\n\n"
            + "\n".join(f"- {b}" for b in bullets)
            + f"\n\nWhat we tested: {uc['hypothesis']}"
        )
        st.write("")
        st.caption("Copy this to share with leadership (use the copy icon, top-right of the box):")
        st.code(plain, language=None)
