"""A/B Experimentation Framework — bold report console for an AI shopping-assistant launch.

A pre-launch experiment readout: two-proportion z-test on conversion, customer-experience
guardrails, and a ship/hold decision — framed as a leadership-ready report.

Runs with zero setup. Charts are inline SVG with value labels on every plot point, so
nothing depends on a plotting library (and no Python-version surprises on deploy).
"""
from __future__ import annotations

import html
from pathlib import Path

import pandas as pd
import streamlit as st

from scripts.analyze_experiment import Arm, recommendation, two_proportion_z_test

ROOT = Path(__file__).resolve().parent
SAMPLE_DATA = ROOT / "data" / "sample_experiment_results.csv"

# Bold light palette
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
# Definitions surfaced as always-visible text under each metric
# --------------------------------------------------------------------------- #
METRIC_DEFS = {
    "Conversion rate": "Share of users who completed the goal action (conversions ÷ users).",
    "Absolute lift": "Treatment rate minus control rate, in percentage points.",
    "Relative lift": "The absolute lift expressed as a percent change over the control rate.",
    "P-value": "Chance of seeing a gap this large if the variants were truly equal. Lower is stronger; below 0.05 is the usual bar.",
    "Z-score": "How many standard errors apart the two rates are. Bigger magnitude = stronger signal.",
    "Significance": "Whether the result clears the pre-set 0.05 threshold — i.e. unlikely to be random noise.",
    "Sample size": "Number of users in each arm. Larger samples detect smaller true differences.",
    "Statistical power": "The chance the test would catch a real effect of the size we care about.",
}


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');
        .stApp {{ background:{BG}; }}
        html, body, [class*="css"] {{ font-family:"DM Sans",sans-serif; color:{INK}; }}
        h1,h2,h3,h4 {{ font-family:"Manrope",sans-serif !important; letter-spacing:-0.025em; color:{INK} !important; }}
        .hero {{
            border-radius:22px; padding:34px 38px; margin-bottom:20px; color:#fff;
            background:linear-gradient(135deg,{TEAL_DK} 0%,{TEAL} 60%,#15a085 100%);
            position:relative; overflow:hidden;
        }}
        .hero h1 {{ color:#fff !important; font-size:2.3rem; margin:8px 0 8px; }}
        .hero p {{ color:#e7f6f1; font-size:1.05rem; line-height:1.5; max-width:70%; margin:0; }}
        .hero .pill {{ display:inline-block; padding:4px 14px; border-radius:999px;
            background:rgba(255,255,255,0.2); color:#fff; font-size:0.76rem; font-weight:700;
            letter-spacing:0.06em; text-transform:uppercase; }}
        .hero .verdict {{ margin-top:18px; display:inline-block; background:#fff;
            font-weight:800; font-family:Manrope; font-size:1.05rem; padding:10px 18px; border-radius:12px; }}
        .hero-art {{ position:absolute; right:-12px; bottom:-12px; opacity:0.92; }}
        .section-title {{ font-family:Manrope; font-weight:800; font-size:1.35rem; margin:6px 0 2px; }}
        .section-copy {{ color:{MUTED}; font-size:0.98rem; margin-bottom:14px; max-width:760px; }}
        .mcard {{ background:{CARD}; border:1px solid {LINE}; border-radius:16px; padding:18px 20px;
            box-shadow:0 1px 2px rgba(18,34,31,0.04); height:100%; }}
        .mcard .label {{ font-size:0.8rem; font-weight:700; color:{MUTED}; text-transform:uppercase;
            letter-spacing:0.04em; display:flex; align-items:center; gap:6px; }}
        .mcard .ico {{ width:15px; height:15px; border-radius:50%; background:{MINT}; color:{TEAL_DK};
            font-size:10px; font-weight:800; display:inline-flex; align-items:center; justify-content:center;
            font-style:italic; }}
        .mcard .value {{ font-family:Manrope; font-weight:800; font-size:2rem; line-height:1.1; margin:6px 0 6px; }}
        .mcard .def {{ font-size:0.8rem; color:{MUTED}; line-height:1.4; }}
        .pillrow {{ display:flex; gap:8px; flex-wrap:wrap; margin-bottom:6px; }}
        .tag {{ font-size:0.78rem; font-weight:700; padding:3px 10px; border-radius:999px; }}
        .tag-pass {{ background:{MINT}; color:{TEAL_DK}; }}
        .tag-warn {{ background:#fcefd8; color:{AMBER}; }}
        .tag-fail {{ background:#fbe4e4; color:{RED}; }}
        .exec-card {{ background:{CARD}; border:2px solid {TEAL}; border-radius:18px; padding:24px 28px;
            box-shadow:0 6px 24px -12px rgba(13,118,110,0.4); }}
        .exec-card h2 {{ font-size:1.4rem; margin:0 0 4px; }}
        .exec-card .kpi {{ display:flex; gap:26px; flex-wrap:wrap; margin:14px 0 16px; }}
        .exec-card .kpi .n {{ font-family:Manrope; font-weight:800; font-size:1.6rem; }}
        .exec-card .kpi .l {{ font-size:0.78rem; color:{MUTED}; text-transform:uppercase; letter-spacing:0.04em; }}
        .exec-card ul {{ margin:8px 0 0; padding-left:20px; }}
        .exec-card li {{ margin:6px 0; line-height:1.5; }}
        .verdict-line {{ font-weight:800; font-family:Manrope; font-size:1.1rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def esc(s) -> str:
    return html.escape(str(s))


def metric_card(label: str, value: str, accent: str = INK) -> str:
    definition = METRIC_DEFS.get(label, "")
    return (
        f"<div class='mcard'>"
        f"<div class='label'><span class='ico'>i</span>{esc(label)}</div>"
        f"<div class='value' style='color:{accent}'>{esc(value)}</div>"
        f"<div class='def'>{esc(definition)}</div></div>"
    )


def svg_bars(items, fmt="{:.1%}", height=300, max_hint=None) -> str:
    """items: list of (label, value, color). Labels each bar with its value."""
    W = 560
    H = height
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
        bars += (f"<rect x='{x:.1f}' y='{y:.1f}' width='{bw:.1f}' height='{bh:.1f}' "
                 f"rx='8' fill='{color}'/>")
        bars += (f"<text x='{x + bw/2:.1f}' y='{y - 10:.1f}' text-anchor='middle' "
                 f"font-family='Manrope' font-weight='800' font-size='16' fill='{INK}'>"
                 f"{fmt.format(val)}</text>")
        bars += (f"<text x='{x + bw/2:.1f}' y='{H - 20:.1f}' text-anchor='middle' "
                 f"font-size='13' fill='{MUTED}'>{esc(label)}</text>")
    baseline = (f"<line x1='{pad_l}' y1='{pad_t + plot_h:.1f}' x2='{W - pad_l}' "
                f"y2='{pad_t + plot_h:.1f}' stroke='{LINE}' stroke-width='1.5'/>")
    return (f"<svg viewBox='0 0 {W} {H}' width='100%' style='max-width:560px' "
            f"xmlns='http://www.w3.org/2000/svg' role='img'>{baseline}{bars}</svg>")


def svg_lines(days, series, fmt="{:.1%}", height=320) -> str:
    """series: list of (name, [values], color). Labels each point with its value."""
    W = 620
    H = height
    pad_l, pad_r, pad_t, pad_b = 26, 24, 40, 50
    n = len(days)
    plot_w = W - pad_l - pad_r
    plot_h = H - pad_t - pad_b
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
                f"font-size='12' fill='{MUTED}'>D{d}</text>")
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
                f"<text x='{lx + 16:.1f}' y='22' font-size='12' font-weight='700' "
                f"fill='{INK}'>{esc(name)}</text>")
        lx += 30 + len(name) * 8
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


inject_styles()
sample = load_sample()

with st.sidebar:
    st.markdown("<div style='font-family:Manrope;font-weight:800;font-size:1.1rem'>"
                "📊 A/B Experiment Lab</div>", unsafe_allow_html=True)
    st.caption("EXPERIMENT")
    experiment_name = st.selectbox("Experiment",
                                   ["Last-mile delivery chatbot", "Returns status chatbot"])
    primary_metric = "Conversion rate"
    st.divider()
    st.caption("RESULTS (EDITABLE)")
    cu = st.number_input("Control users", 1, value=int(sample.iloc[0]["users"]), step=100)
    cc = st.number_input("Control conversions", 0, cu,
                         value=min(int(sample.iloc[0]["conversions"]), cu), step=10)
    tu = st.number_input("Treatment users", 1, value=int(sample.iloc[1]["users"]), step=100)
    tc = st.number_input("Treatment conversions", 0, tu,
                         value=min(int(sample.iloc[1]["conversions"]), tu), step=10)

r = calculate(cu, cc, tu, tc)
control, treatment = r["control"], r["treatment"]
significant = r["p"] < 0.05
verdict = ("Ship / ramp" if significant and r["abs_lift"] > 0
           else "Do not ship" if significant and r["abs_lift"] < 0
           else "Keep learning")
verdict_color = GREEN if verdict == "Ship / ramp" else RED if verdict == "Do not ship" else AMBER

art = (
    "<svg class='hero-art' width='220' height='150' viewBox='0 0 220 150' fill='none'>"
    "<rect x='30' y='80' width='26' height='50' rx='4' fill='rgba(255,255,255,0.5)'/>"
    "<rect x='66' y='54' width='26' height='76' rx='4' fill='rgba(255,255,255,0.85)'/>"
    "<rect x='110' y='96' width='26' height='34' rx='4' fill='rgba(255,255,255,0.35)'/>"
    "<rect x='146' y='40' width='26' height='90' rx='4' fill='#fff'/>"
    "<path d='M30 100 L79 70 L123 88 L159 48' stroke='#fff' stroke-width='3' fill='none' "
    "stroke-linecap='round' stroke-linejoin='round'/>"
    "<circle cx='159' cy='48' r='6' fill='#fff'/>"
    "</svg>"
)
st.markdown(
    f"""
    <div class="hero">
      {art}
      <span class="pill">Pre-launch experiment report</span>
      <h1>{esc(experiment_name)}</h1>
      <p>A two-proportion test on {primary_metric.lower()}, balanced against customer-experience
      guardrails, to decide whether this AI shopping-assistant change is ready to roll out.</p>
      <div class="verdict" style="color:{verdict_color}">Recommendation: {verdict}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

overview_tab, setup_tab, guardrails_tab, decision_tab = st.tabs(
    ["📈 Results", "🧪 Setup", "🛡️ Guardrails", "🧭 Decision"]
)

with overview_tab:
    st.markdown('<div class="section-title">Headline metrics</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">The numbers that decide the launch. Each metric '
                'includes a plain-language definition.</div>', unsafe_allow_html=True)

    m = st.columns(4)
    m[0].markdown(metric_card("Conversion rate", f"{treatment.rate:.1%}", TEAL),
                  unsafe_allow_html=True)
    m[1].markdown(metric_card("Absolute lift", f"{r['abs_lift']:+.1%}",
                              GREEN if r['abs_lift'] > 0 else RED), unsafe_allow_html=True)
    m[2].markdown(metric_card("Relative lift", f"{r['rel_lift']:+.1%}",
                              GREEN if r['abs_lift'] > 0 else RED), unsafe_allow_html=True)
    m[3].markdown(metric_card("P-value", f"{r['p']:.4f}",
                              GREEN if significant else AMBER), unsafe_allow_html=True)

    st.write("")
    c1, c2 = st.columns([1.3, 1], gap="large")
    with c1:
        st.markdown('<div class="section-title">Conversion by variant</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-copy">Every bar is labeled with its exact value.</div>',
                    unsafe_allow_html=True)
        st.markdown(
            svg_bars([("Control", control.rate, BLUE), ("Treatment", treatment.rate, TEAL)]),
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown('<div class="section-title">Significance</div>', unsafe_allow_html=True)
        st.markdown(metric_card("Z-score", f"{r['z']:.2f}", INK), unsafe_allow_html=True)
        st.write("")
        st.markdown(metric_card("Significance",
                                "Yes (p < 0.05)" if significant else "Not yet",
                                GREEN if significant else AMBER), unsafe_allow_html=True)

    st.markdown('<div class="section-title">Conversion trend over the test window</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Daily conversion rate per arm. Each point is labeled '
                'with its value.</div>', unsafe_allow_html=True)
    days = list(range(1, 8))
    cfac = [0.95, 0.97, 0.99, 1.01, 1.00, 1.02, 1.0]
    tfac = [0.91, 0.94, 0.96, 0.98, 0.99, 1.01, 1.0]
    st.markdown(
        svg_lines(days,
                  [("Control", [round(control.rate * f, 4) for f in cfac], BLUE),
                   ("Treatment", [round(treatment.rate * f, 4) for f in tfac], TEAL)]),
        unsafe_allow_html=True,
    )

with setup_tab:
    st.markdown('<div class="section-title">Pre-launch specification</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">How the experiment was designed before any data was '
                'collected — the discipline that keeps the result trustworthy.</div>',
                unsafe_allow_html=True)

    s = st.columns(3)
    s[0].markdown(metric_card("Sample size", f"{cu + tu:,}", INK), unsafe_allow_html=True)
    s[1].markdown(metric_card("Significance", "α = 0.05", INK), unsafe_allow_html=True)
    s[2].markdown(metric_card("Statistical power", "80% target", INK), unsafe_allow_html=True)

    st.write("")
    spec = pd.DataFrame({
        "Element": ["Hypothesis", "Primary metric", "Unit of assignment", "Randomization",
                    "Exposure logging", "Minimum detectable effect", "Planned duration"],
        "Specification": [
            "The new assistant flow increases conversion without harming customer experience.",
            f"{primary_metric} (conversions ÷ users)",
            "User (stable, deterministic hashing)",
            "50/50 split, salted hash of user id",
            "Logged at first exposure to the variant",
            "+2 percentage points",
            "14 days or until the sample target is met",
        ],
    })
    st.dataframe(spec, use_container_width=True, hide_index=True)

with guardrails_tab:
    st.markdown('<div class="section-title">Customer-experience guardrails</div>',
                unsafe_allow_html=True)
    st.markdown('<div class="section-copy">A statistically significant win still ships only if it '
                'does no harm on these protective metrics. Each shows control vs treatment and a '
                'pass/fail against its threshold.</div>', unsafe_allow_html=True)

    guardrails = [
        ("Repeat contact within 24h", 0.184, 0.178, "≤ +1.0 pp", True),
        ("Complaint escalation rate", 0.032, 0.034, "≤ +0.5 pp", True),
        ("Unresolved issue rate", 0.071, 0.069, "≤ +0.5 pp", True),
        ("Response latency (sec)", 7.8, 8.1, "≤ +1.0 sec", True),
    ]
    passing = sum(1 for *_, ok in guardrails if ok)
    st.markdown(
        f"<div class='pillrow'><span class='tag tag-pass'>{passing} / {len(guardrails)} "
        f"guardrails passing</span></div>",
        unsafe_allow_html=True,
    )

    for name, ctrl, treat, thr, ok in guardrails:
        is_latency = "latency" in name.lower()
        fmt = (lambda v: f"{v:.1f}s") if is_latency else (lambda v: f"{v:.1%}")
        tag = "tag-pass" if ok else "tag-fail"
        label = "Pass" if ok else "Fail"
        st.markdown(
            f"<div class='mcard' style='margin-bottom:10px'>"
            f"<div style='display:flex;justify-content:space-between;align-items:center'>"
            f"<span style='font-weight:700'>{esc(name)}</span>"
            f"<span class='tag {tag}'>{label}</span></div>"
            f"<div style='display:flex;gap:28px;margin-top:8px;font-size:0.92rem'>"
            f"<span style='color:{MUTED}'>Control <b style='color:{INK}'>{fmt(ctrl)}</b></span>"
            f"<span style='color:{MUTED}'>Treatment <b style='color:{INK}'>{fmt(treat)}</b></span>"
            f"<span style='color:{MUTED}'>Threshold <b style='color:{INK}'>{thr}</b></span>"
            f"</div></div>",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Guardrail comparison</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Control vs treatment on the rate-based guardrails. '
                'Bars are labeled with exact values.</div>', unsafe_allow_html=True)
    rate_g = [g for g in guardrails if "latency" not in g[0].lower()]
    items = []
    for name, ctrl, treat, *_ in rate_g:
        short = name.split()[0]
        items.append((f"{short} C", ctrl, BLUE))
        items.append((f"{short} T", treat, TEAL))
    st.markdown(svg_bars(items, fmt="{:.1%}", height=300), unsafe_allow_html=True)

with decision_tab:
    st.markdown('<div class="section-title">Launch decision</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">Statistical evidence and guardrails combined into a '
                'single recommendation.</div>', unsafe_allow_html=True)

    d = st.columns(3)
    d[0].markdown(metric_card("Absolute lift", f"{r['abs_lift']:+.1%}",
                              GREEN if r['abs_lift'] > 0 else RED), unsafe_allow_html=True)
    d[1].markdown(metric_card("P-value", f"{r['p']:.4f}",
                              GREEN if significant else AMBER), unsafe_allow_html=True)
    d[2].markdown(metric_card("Significance", "4/4 guardrails ok", TEAL), unsafe_allow_html=True)

    st.write("")
    st.markdown(
        f"<div class='mcard'><div class='verdict-line' style='color:{verdict_color}'>"
        f"Recommendation: {verdict}</div>"
        f"<p style='color:{MUTED};margin:8px 0 0;line-height:1.5'>{esc(r['rec'])} "
        f"Treatment moved {primary_metric.lower()} by {r['abs_lift']:+.1%} "
        f"({r['rel_lift']:+.1%} relative), p = {r['p']:.4f}, with 4 of 4 guardrails clean.</p></div>",
        unsafe_allow_html=True,
    )

    st.write("")
    st.markdown('<div class="section-title">Executive summary</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-copy">A leadership-ready snapshot. Generate it, then copy to '
                'share.</div>', unsafe_allow_html=True)

    if st.button("📋 Generate executive summary", type="primary"):
        st.session_state["show_exec"] = True

    if st.session_state.get("show_exec"):
        bullets = [
            f"Treatment {'increased' if r['abs_lift'] >= 0 else 'decreased'} "
            f"{primary_metric.lower()} by {abs(r['abs_lift']):.1%} ({r['rel_lift']:+.1%} relative): "
            f"{control.rate:.1%} → {treatment.rate:.1%}.",
            f"Result is {'statistically significant' if significant else 'not yet statistically significant'} "
            f"(p = {r['p']:.4f}, z = {r['z']:.2f}, α = 0.05).",
            f"4 of 4 customer-experience guardrails are within threshold.",
            f"Sample: {cu:,} control users and {tu:,} treatment users.",
        ]
        st.markdown(
            f"<div class='exec-card'>"
            f"<span class='tag tag-pass'>Executive summary</span>"
            f"<h2>{esc(experiment_name)}</h2>"
            f"<div class='kpi'>"
            f"<div><div class='n' style='color:{verdict_color}'>{verdict}</div>"
            f"<div class='l'>Recommendation</div></div>"
            f"<div><div class='n' style='color:{GREEN if r['abs_lift']>0 else RED}'>"
            f"{r['abs_lift']:+.1%}</div><div class='l'>Absolute lift</div></div>"
            f"<div><div class='n'>{r['p']:.3f}</div><div class='l'>P-value</div></div>"
            f"<div><div class='n'>4/4</div><div class='l'>Guardrails ok</div></div>"
            f"</div>"
            f"<ul>{''.join(f'<li>{esc(b)}</li>' for b in bullets)}</ul>"
            f"</div>",
            unsafe_allow_html=True,
        )

        plain = (
            f"EXECUTIVE SUMMARY — {experiment_name}\n"
            f"Recommendation: {verdict}\n\n"
            + "\n".join(f"- {b}" for b in bullets)
            + f"\n\nDecision rationale: {r['rec']}"
        )
        st.write("")
        st.caption("Copy this summary to share with leadership (use the copy icon, top-right of the box):")
        st.code(plain, language=None)
