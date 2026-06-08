from __future__ import annotations

from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from scripts.analyze_experiment import Arm, recommendation, two_proportion_z_test


ROOT = Path(__file__).resolve().parent
SAMPLE_DATA = ROOT / "data" / "sample_experiment_results.csv"

COLORS = {
    "ink": "#12221f",
    "muted": "#62706d",
    "teal": "#0d766e",
    "teal_dark": "#075b55",
    "mint": "#dff4ef",
    "sand": "#f4efe7",
    "amber": "#b66a16",
    "red": "#b84040",
    "blue": "#476aa3",
}


st.set_page_config(
    page_title="Experiment Lab",
    page_icon="A",
    layout="wide",
    initial_sidebar_state="expanded",
)


def inject_styles() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@600;700;800&display=swap');

        :root {{
            --ink: {COLORS["ink"]};
            --muted: {COLORS["muted"]};
            --teal: {COLORS["teal"]};
            --mint: {COLORS["mint"]};
            --sand: {COLORS["sand"]};
        }}

        html, body, [class*="css"] {{
            font-family: "DM Sans", sans-serif;
            color: var(--ink);
        }}

        h1, h2, h3 {{
            font-family: "Manrope", sans-serif !important;
            letter-spacing: -0.03em;
        }}

        [data-testid="stAppViewContainer"] {{
            background:
                radial-gradient(circle at 85% 2%, rgba(13, 118, 110, 0.09), transparent 25rem),
                #f7f8f5;
        }}

        [data-testid="stHeader"] {{
            background: rgba(247, 248, 245, 0.82);
            backdrop-filter: blur(12px);
        }}

        [data-testid="stSidebar"] {{
            background: #102724;
        }}

        [data-testid="stSidebar"] * {{
            color: #edf6f3;
        }}

        [data-testid="stSidebar"] label p {{
            color: #bed1cc !important;
            font-weight: 600;
        }}

        [data-testid="stSidebar"] [data-baseweb="select"] > div,
        [data-testid="stSidebar"] input {{
            background: #18332f;
            border-color: #34524d;
        }}

        .block-container {{
            max-width: 1440px;
            padding-top: 2rem;
            padding-bottom: 4rem;
        }}

        .brand {{
            display: flex;
            align-items: center;
            gap: 0.7rem;
            margin: 0.25rem 0 2rem;
            color: white;
            font-family: "Manrope", sans-serif;
            font-size: 1.05rem;
            font-weight: 800;
        }}

        .brand-mark {{
            display: grid;
            width: 2.25rem;
            height: 2.25rem;
            place-items: center;
            border-radius: 0.7rem;
            background: #39b7a5;
            color: #09211d;
            font-size: 1.15rem;
        }}

        .eyebrow {{
            margin-bottom: 0.55rem;
            color: var(--teal);
            font-size: 0.75rem;
            font-weight: 800;
            letter-spacing: 0.12em;
            text-transform: uppercase;
        }}

        .hero {{
            position: relative;
            overflow: hidden;
            margin-bottom: 1.25rem;
            border: 1px solid #dbe4df;
            border-radius: 1.35rem;
            padding: clamp(1.5rem, 4vw, 3.4rem);
            background: linear-gradient(125deg, #ffffff 35%, #e2f2ed 100%);
            box-shadow: 0 18px 45px rgba(19, 56, 49, 0.08);
        }}

        .hero::after {{
            content: "";
            position: absolute;
            width: 19rem;
            height: 19rem;
            top: -11rem;
            right: -5rem;
            border: 2.5rem solid rgba(13, 118, 110, 0.08);
            border-radius: 50%;
        }}

        .hero h1 {{
            max-width: 900px;
            margin: 0;
            color: var(--ink);
            font-size: clamp(2rem, 4.8vw, 4.2rem);
            line-height: 1.02;
        }}

        .hero-copy {{
            max-width: 800px;
            margin: 1.1rem 0 0;
            color: #4c5d59;
            font-size: 1.05rem;
            line-height: 1.65;
        }}

        .pill {{
            display: inline-flex;
            align-items: center;
            margin-top: 1.25rem;
            border: 1px solid #a9d5ca;
            border-radius: 999px;
            padding: 0.42rem 0.75rem;
            background: rgba(255, 255, 255, 0.72);
            color: var(--teal);
            font-size: 0.8rem;
            font-weight: 700;
        }}

        [data-testid="stMetric"] {{
            min-height: 132px;
            border: 1px solid #dce4e0;
            border-radius: 1rem;
            padding: 1.15rem 1.2rem;
            background: rgba(255, 255, 255, 0.9);
            box-shadow: 0 8px 24px rgba(18, 34, 31, 0.04);
        }}

        [data-testid="stMetricLabel"] p {{
            color: var(--muted);
            font-weight: 700;
        }}

        [data-testid="stMetricValue"] {{
            font-family: "Manrope", sans-serif;
            color: var(--ink);
        }}

        [data-testid="stMetricDelta"] svg {{
            display: none;
        }}

        div[data-testid="stTabs"] button {{
            height: 3.25rem;
            color: #5b6b67;
            font-weight: 700;
        }}

        div[data-testid="stTabs"] button[aria-selected="true"] {{
            color: var(--teal);
        }}

        div[data-testid="stTabs"] [data-baseweb="tab-highlight"] {{
            background-color: var(--teal);
        }}

        .section-title {{
            margin: 1.4rem 0 0.2rem;
            color: var(--ink);
            font-family: "Manrope", sans-serif;
            font-size: 1.45rem;
            font-weight: 800;
            letter-spacing: -0.03em;
        }}

        .section-copy {{
            margin-bottom: 1.1rem;
            color: var(--muted);
        }}

        .insight-card, .decision-card {{
            height: 100%;
            border: 1px solid #dce4e0;
            border-radius: 1rem;
            padding: 1.2rem;
            background: white;
        }}

        .insight-number {{
            display: grid;
            width: 2rem;
            height: 2rem;
            place-items: center;
            margin-bottom: 0.8rem;
            border-radius: 0.65rem;
            background: var(--mint);
            color: var(--teal);
            font-weight: 800;
        }}

        .decision-card {{
            border-color: #9bcfc3;
            padding: 1.6rem;
            background: linear-gradient(135deg, #e6f5f1, #ffffff);
        }}

        .decision-card h3 {{
            margin: 0.25rem 0 0.7rem;
            font-size: 1.65rem;
        }}

        .decision-card p, .insight-card p {{
            color: #566762;
            line-height: 1.55;
        }}

        .status-good, .status-watch {{
            display: inline-block;
            border-radius: 999px;
            padding: 0.3rem 0.65rem;
            font-size: 0.75rem;
            font-weight: 800;
        }}

        .status-good {{
            background: #daf1e9;
            color: #08705f;
        }}

        .status-watch {{
            background: #fff0d9;
            color: #98570c;
        }}

        .footer-note {{
            margin-top: 2.5rem;
            border-top: 1px solid #dde5e1;
            padding-top: 1rem;
            color: #77847f;
            font-size: 0.82rem;
        }}

        .stButton > button {{
            border-radius: 0.75rem;
            border-color: var(--teal);
            background: var(--teal);
            color: white;
            font-weight: 700;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_sample() -> pd.DataFrame:
    return pd.read_csv(SAMPLE_DATA)


def calculate(control_users: int, control_conversions: int, treatment_users: int, treatment_conversions: int) -> dict:
    control = Arm("Control", control_users, control_conversions)
    treatment = Arm("Treatment", treatment_users, treatment_conversions)
    z_score, p_value = two_proportion_z_test(control, treatment)
    absolute_lift = treatment.rate - control.rate
    relative_lift = absolute_lift / control.rate if control.rate else float("inf")
    return {
        "control": control,
        "treatment": treatment,
        "z_score": z_score,
        "p_value": p_value,
        "absolute_lift": absolute_lift,
        "relative_lift": relative_lift,
        "recommendation": recommendation(p_value, absolute_lift, 0.05),
    }


@alt.theme.register("experiment_lab", enable=True)
def chart_theme() -> alt.theme.ThemeConfig:
    return alt.theme.ThemeConfig({
        "config": {
            "view": {"stroke": "transparent"},
            "axis": {
                "domain": False,
                "gridColor": "#e7ece9",
                "labelColor": COLORS["muted"],
                "titleColor": COLORS["muted"],
                "tickColor": "transparent",
            },
            "legend": {
                "labelColor": COLORS["muted"],
                "titleColor": COLORS["ink"],
                "orient": "top",
            },
            "title": {"color": COLORS["ink"], "font": "Manrope", "fontSize": 16},
        }
    })


inject_styles()

sample = load_sample()

with st.sidebar:
    st.markdown(
        '<div class="brand"><span class="brand-mark">A/B</span>Experiment Lab</div>',
        unsafe_allow_html=True,
    )
    st.caption("EXPERIMENT CONTROLS")
    experiment_name = st.selectbox(
        "Experiment",
        [
            "Last-mile delivery chatbot",
            "Returns status chatbot",
        ],
    )
    segment = st.selectbox(
        "Audience segment",
        ["Overall", "High intent confidence", "Low intent confidence"],
        disabled=experiment_name == "Returns status chatbot",
    )
    st.divider()
    st.caption("SAMPLE RESULTS")
    control_users = st.number_input("Control users", min_value=1, value=int(sample.iloc[0]["users"]), step=100)
    control_conversions = st.number_input(
        "Control conversions",
        min_value=0,
        max_value=control_users,
        value=min(int(sample.iloc[0]["conversions"]), control_users),
        step=10,
    )
    treatment_users = st.number_input("Treatment users", min_value=1, value=int(sample.iloc[1]["users"]), step=100)
    treatment_conversions = st.number_input(
        "Treatment conversions",
        min_value=0,
        max_value=treatment_users,
        value=min(int(sample.iloc[1]["conversions"]), treatment_users),
        step=10,
    )
    st.divider()
    st.caption("Demo data only")
    st.write("Adjust the sample counts to see the statistical readout and decision update instantly.")

results = calculate(control_users, control_conversions, treatment_users, treatment_conversions)
control = results["control"]
treatment = results["treatment"]

if experiment_name == "Returns status chatbot":
    title = "Returns status chatbot containment experiment"
    audience = "Returns support"
    hypothesis = (
        "If customers can check return status and next steps inside the chatbot, more customers "
        "will complete support journeys without agent handoff or repeat contact."
    )
    primary_metric = "Containment rate"
    status = "Ship"
else:
    title = "Last-mile delivery chatbot launch experiment"
    audience = "Delivery support"
    hypothesis = (
        "If customers with delivery questions receive the improved chatbot experience, "
        "self-service resolution will increase without harming customer experience guardrails."
    )
    primary_metric = "Self-service resolution"
    status = "Ramp" if results["p_value"] < 0.05 and results["absolute_lift"] > 0 else "Iterate"

st.markdown(
    f"""
    <section class="hero">
        <div class="eyebrow">Experiment command center</div>
        <h1>{title}</h1>
        <p class="hero-copy">{hypothesis}</p>
        <span class="pill">Live synthetic readout &nbsp;|&nbsp; {audience}</span>
    </section>
    """,
    unsafe_allow_html=True,
)

metric_columns = st.columns(4)
metric_columns[0].metric(primary_metric, f"{treatment.rate:.1%}", f"{results['absolute_lift']:+.1%} vs control")
metric_columns[1].metric("Control baseline", f"{control.rate:.1%}", f"{control.conversions:,} conversions")
metric_columns[2].metric("Statistical signal", f"p={results['p_value']:.3f}", f"z = {results['z_score']:.2f}")
metric_columns[3].metric("Recommendation", status, "Guardrails reviewed")

overview_tab, setup_tab, guardrails_tab, decision_tab = st.tabs(
    ["Overview", "Experiment setup", "Guardrails", "Decision"]
)

with overview_tab:
    st.markdown('<div class="section-title">Performance readout</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Compare the primary outcome and see how the result developed over the test window.</div>',
        unsafe_allow_html=True,
    )

    performance = pd.DataFrame(
        {
            "Variant": ["Control", "Treatment"],
            "Rate": [control.rate, treatment.rate],
            "Users": [control.users, treatment.users],
        }
    )
    bar = (
        alt.Chart(performance)
        .mark_bar(cornerRadiusTopLeft=8, cornerRadiusTopRight=8, size=78)
        .encode(
            x=alt.X("Variant:N", axis=alt.Axis(labelAngle=0, title=None)),
            y=alt.Y("Rate:Q", axis=alt.Axis(format=".0%"), scale=alt.Scale(domain=[0, max(performance["Rate"]) * 1.25])),
            color=alt.Color(
                "Variant:N",
                scale=alt.Scale(domain=["Control", "Treatment"], range=[COLORS["blue"], COLORS["teal"]]),
                legend=None,
            ),
            tooltip=["Variant:N", alt.Tooltip("Rate:Q", format=".2%"), "Users:Q"],
        )
        .properties(height=330)
    )
    labels = bar.mark_text(dy=-14, font="Manrope", fontSize=16, fontWeight=700).encode(
        text=alt.Text("Rate:Q", format=".1%")
    )

    chart_col, readout_col = st.columns([1.45, 1], gap="large")
    with chart_col:
        st.altair_chart(bar + labels, width="stretch")
    with readout_col:
        st.markdown(
            f"""
            <div class="decision-card">
                <div class="eyebrow">Executive readout</div>
                <h3>{results["absolute_lift"]:+.1%} absolute lift</h3>
                <p>Treatment delivered a <strong>{results["relative_lift"]:+.1%}</strong> relative change.
                The two-sided proportion test returned <strong>p = {results["p_value"]:.4f}</strong>.</p>
                <p><strong>{results["recommendation"]}</strong></p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-title">Experiment trend</div>', unsafe_allow_html=True)
    trend = pd.DataFrame(
        {
            "Day": list(range(1, 8)) * 2,
            "Variant": ["Control"] * 7 + ["Treatment"] * 7,
            "Rate": [
                control.rate * 0.95,
                control.rate * 0.97,
                control.rate * 0.99,
                control.rate * 1.01,
                control.rate * 1.00,
                control.rate * 1.02,
                control.rate,
                treatment.rate * 0.91,
                treatment.rate * 0.94,
                treatment.rate * 0.96,
                treatment.rate * 0.98,
                treatment.rate * 0.99,
                treatment.rate * 1.01,
                treatment.rate,
            ],
        }
    )
    line = (
        alt.Chart(trend)
        .mark_line(point=alt.OverlayMarkDef(size=70, filled=True), strokeWidth=3)
        .encode(
            x=alt.X("Day:O", title="Experiment day"),
            y=alt.Y("Rate:Q", axis=alt.Axis(format=".0%"), scale=alt.Scale(zero=False)),
            color=alt.Color(
                "Variant:N",
                scale=alt.Scale(domain=["Control", "Treatment"], range=[COLORS["blue"], COLORS["teal"]]),
                title=None,
            ),
            tooltip=["Day:O", "Variant:N", alt.Tooltip("Rate:Q", format=".2%")],
        )
        .properties(height=300)
    )
    st.altair_chart(line, width="stretch")

    st.markdown('<div class="section-title">What the data says</div>', unsafe_allow_html=True)
    insight_columns = st.columns(3)
    insights = [
        (
            "Primary outcome",
            f"Treatment moved {primary_metric.lower()} by {results['absolute_lift']:+.1%} versus control.",
        ),
        (
            "Decision quality",
            "The framework combines statistical evidence with customer-experience guardrails before rollout.",
        ),
        (
            "Portfolio story",
            "The readout connects experiment design, instrumentation, analysis, and launch governance in one workflow.",
        ),
    ]
    for index, (heading, copy) in enumerate(insights):
        insight_columns[index].markdown(
            f"""
            <div class="insight-card">
                <div class="insight-number">0{index + 1}</div>
                <h3>{heading}</h3>
                <p>{copy}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

with setup_tab:
    st.markdown('<div class="section-title">Pre-launch specification</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">A decision-ready test starts with a clear contract across product, data, and engineering.</div>',
        unsafe_allow_html=True,
    )

    setup_left, setup_right = st.columns(2, gap="large")
    with setup_left:
        st.subheader("Experiment design")
        st.markdown(
            """
            **Hypothesis**  
            Improved task-specific guidance increases successful self-service resolution.

            **Assignment unit**  
            Customer account with a deterministic 50/50 split.

            **Eligibility**  
            Delivery-related support contacts with active order context.

            **Primary metric**  
            Resolution without agent handoff or repeat contact within 24 hours.
            """
        )
    with setup_right:
        st.subheader("Launch gates")
        gates = [
            ("Pass", "Stable assignment across sessions"),
            ("Pass", "Exposure logged when treatment is visible"),
            ("Pass", "Internal and consent-ineligible traffic excluded"),
            ("Pass", "Primary metric and guardrails defined"),
            ("Watch", "Complaint escalation monitored during ramp"),
        ]
        for gate_status, gate_name in gates:
            css_class = "status-good" if gate_status == "Pass" else "status-watch"
            st.markdown(
                f'<p><span class="{css_class}">{gate_status}</span>&nbsp;&nbsp; {gate_name}</p>',
                unsafe_allow_html=True,
            )

    st.divider()
    st.subheader("Instrumentation contract")
    event_data = pd.DataFrame(
        [
            ["experiment_exposed", "experiment_id, variant, user_id, session_id, surface"],
            ["delivery_intent_detected", "intent, confidence_band, order_context_available"],
            ["chatbot_resolution_offered", "resolution_type, policy_path, fallback_available"],
            ["agent_handoff_requested", "handoff_reason, conversation_turn, context_passed"],
            ["repeat_contact_24h", "contact_channel, original_conversation_id"],
        ],
        columns=["Event", "Required properties"],
    )
    st.dataframe(event_data, hide_index=True, width="stretch")

with guardrails_tab:
    st.markdown('<div class="section-title">Customer experience guardrails</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">A primary-metric win is only useful when the experience remains healthy.</div>',
        unsafe_allow_html=True,
    )

    guardrails = pd.DataFrame(
        [
            ["Repeat contact within 24h", 0.184, 0.178, "<= +1.0 pp", "Pass"],
            ["Complaint escalation rate", 0.032, 0.034, "<= +0.5 pp", "Pass"],
            ["Unresolved issue rate", 0.071, 0.069, "<= +0.5 pp", "Pass"],
            ["Response latency", 7.8, 8.1, "<= +1.0 sec", "Pass"],
        ],
        columns=["Metric", "Control", "Treatment", "Threshold", "Status"],
    )
    display_guardrails = guardrails.astype(object)
    for row_index in range(3):
        display_guardrails.loc[row_index, "Control"] = f"{guardrails.loc[row_index, 'Control']:.1%}"
        display_guardrails.loc[row_index, "Treatment"] = f"{guardrails.loc[row_index, 'Treatment']:.1%}"
    display_guardrails.loc[3, "Control"] = f"{guardrails.loc[3, 'Control']:.1f} sec"
    display_guardrails.loc[3, "Treatment"] = f"{guardrails.loc[3, 'Treatment']:.1f} sec"
    st.dataframe(display_guardrails, hide_index=True, width="stretch")

    guardrail_chart = (
        alt.Chart(guardrails.iloc[:3].melt("Metric", ["Control", "Treatment"], var_name="Variant", value_name="Rate"))
        .mark_bar(cornerRadiusEnd=5)
        .encode(
            y=alt.Y("Metric:N", sort=None, title=None),
            x=alt.X("Rate:Q", axis=alt.Axis(format=".0%")),
            color=alt.Color(
                "Variant:N",
                scale=alt.Scale(domain=["Control", "Treatment"], range=[COLORS["blue"], COLORS["teal"]]),
                title=None,
            ),
            yOffset="Variant:N",
            tooltip=["Metric:N", "Variant:N", alt.Tooltip("Rate:Q", format=".2%")],
        )
        .properties(height=280)
    )
    st.altair_chart(guardrail_chart, width="stretch")
    st.success("4 of 4 guardrails are within the launch thresholds.")

with decision_tab:
    st.markdown('<div class="section-title">Decision brief</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">Translate evidence into a rollout decision with clear owners and monitoring.</div>',
        unsafe_allow_html=True,
    )

    decision_left, decision_right = st.columns([1.2, 1], gap="large")
    with decision_left:
        st.markdown(
            f"""
            <div class="decision-card">
                <div class="eyebrow">Recommended action</div>
                <h3>{status} the treatment</h3>
                <p>{results["recommendation"]} The primary metric moved
                <strong>{results["absolute_lift"]:+.1%}</strong> and the current guardrail review is clean.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.subheader("Next actions")
        st.checkbox("Ramp treatment to 75% of eligible traffic", value=True)
        st.checkbox("Monitor complaint escalation daily", value=True)
        st.checkbox("Review low-confidence intent fallbacks", value=True)
    with decision_right:
        st.subheader("Evidence summary")
        st.metric("Observed lift", f"{results['absolute_lift']:+.1%}")
        st.metric("P-value", f"{results['p_value']:.4f}")
        st.metric("Guardrails passing", "4 / 4")

        st.download_button(
            "Download sample results",
            data=sample.to_csv(index=False),
            file_name="sample_experiment_results.csv",
            mime="text/csv",
            width="stretch",
        )

st.markdown(
    """
    <div class="footer-note">
        Synthetic portfolio data only. This dashboard demonstrates experiment design,
        measurement, and launch decisioning without employer or customer telemetry.
    </div>
    """,
    unsafe_allow_html=True,
)
