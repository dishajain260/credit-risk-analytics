"""
=============================================================================================
Enterprise Credit Risk Analytics & Underwriting Platform
Built for Banking & Credit Portfolio Intelligence (Kotak Mahindra Group Alignment)
Author: Disha Jain (dishajain260)
=============================================================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

# ---------------------------------------------------------------------------------------------
# PAGE CONFIGURATION
# ---------------------------------------------------------------------------------------------
st.set_page_config(
    page_title="Credit Risk Analytics & Underwriting Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Banking UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #0F2A4A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #4A5568;
        margin-bottom: 1.5rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #F8FAFC 0%, #EDF2F7 100%);
        border-left: 5px solid #0F2A4A;
        padding: 18px 22px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .kpi-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #4A5568;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .kpi-value {
        font-size: 1.85rem;
        font-weight: 700;
        color: #0F2A4A;
        margin-top: 4px;
    }
    .kpi-sub {
        font-size: 0.8rem;
        color: #718096;
        margin-top: 2px;
    }
    .badge-approved {
        background-color: #DEF7EC;
        color: #03543F;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.1rem;
        display: inline-block;
    }
    .badge-review {
        background-color: #FEF08A;
        color: #713F12;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.1rem;
        display: inline-block;
    }
    .badge-declined {
        background-color: #FDE8E8;
        color: #9B1C1C;
        padding: 6px 14px;
        border-radius: 6px;
        font-weight: 700;
        font-size: 1.1rem;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------------------------
# DATA LOADING & CACHING
# ---------------------------------------------------------------------------------------------
@st.cache_data
def load_credit_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cleaned_path = os.path.join(base_dir, "data", "CREDIT_RISK2.csv")
    raw_path = os.path.join(base_dir, "data", "credit_risk_dataset.csv")

    if os.path.exists(cleaned_path):
        try:
            df = pd.read_csv(cleaned_path, sep=';')
            if 'person_age' not in df.columns or len(df.columns) < 5:
                df = pd.read_csv(cleaned_path, sep=',')
        except Exception:
            df = pd.read_csv(cleaned_path, sep=',')
    else:
        df = pd.read_csv(raw_path)

    # Standardize column names
    df.columns = df.columns.str.strip().str.lower()
    
    # Ensure numeric columns
    numeric_cols = ['person_age', 'person_income', 'person_emp_length', 'loan_amnt', 'loan_int_rate', 'loan_status', 'loan_percent_income', 'cb_person_cred_hist_length']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Create derived analytical columns
    if 'dti_bracket' not in df.columns:
        df['dti_bracket'] = pd.cut(
            df['loan_percent_income'],
            bins=[-0.01, 0.20, 0.40, 1.0],
            labels=['Low (< 20%)', 'Moderate (20% - 40%)', 'High (> 40%)']
        )
    
    if 'age_cohort' not in df.columns:
        df['age_cohort'] = pd.cut(
            df['person_age'],
            bins=[17, 25, 35, 50, 120],
            labels=['18-25 (Young Adult)', '26-35 (Core Career)', '36-50 (Mature)', '51+ (Senior)']
        )

    return df

try:
    df_raw = load_credit_data()
except Exception as e:
    st.error(f"Error loading credit risk dataset: {e}")
    st.stop()

# ---------------------------------------------------------------------------------------------
# SIDEBAR FILTERS
# ---------------------------------------------------------------------------------------------
st.sidebar.markdown("### 🏦 Credit Risk Portfolio")
st.sidebar.markdown("**Enterprise Underwriting Controls**")
st.sidebar.markdown("---")

# Filter: Loan Grade
all_grades = sorted(df_raw['loan_grade'].dropna().unique())
selected_grades = st.sidebar.multiselect(
    "Filter by Loan Grade:",
    options=all_grades,
    default=all_grades
)

# Filter: Loan Intent
all_intents = sorted(df_raw['loan_intent'].dropna().unique())
selected_intents = st.sidebar.multiselect(
    "Filter by Loan Intent:",
    options=all_intents,
    default=all_intents
)

# Filter: Home Ownership
all_home = sorted(df_raw['person_home_ownership'].dropna().unique())
selected_home = st.sidebar.multiselect(
    "Filter by Home Ownership:",
    options=all_home,
    default=all_home
)

# Filter: Age Range
min_age = int(df_raw['person_age'].min())
max_age = int(df_raw['person_age'].max())
age_range = st.sidebar.slider(
    "Applicant Age Range:",
    min_value=min_age,
    max_value=max_age,
    value=(min_age, max_age)
)

# Apply filters
df = df_raw[
    (df_raw['loan_grade'].isin(selected_grades)) &
    (df_raw['loan_intent'].isin(selected_intents)) &
    (df_raw['person_home_ownership'].isin(selected_home)) &
    (df_raw['person_age'] >= age_range[0]) &
    (df_raw['person_age'] <= age_range[1])
]

st.sidebar.markdown("---")
st.sidebar.info(
    f"**Filtered Book Size:**\n\n"
    f"• Loans: **{len(df):,}** of **{len(df_raw):,}**\n"
    f"• Exposure: **${df['loan_amnt'].sum()/1e6:,.2f}M**"
)

# ---------------------------------------------------------------------------------------------
# MAIN HEADER
# ---------------------------------------------------------------------------------------------
st.markdown('<div class="main-header">🏦 Enterprise Credit Risk Analytics & Underwriting Platform</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Automated Credit Risk Diagnostics, Star Schema Dimensional Modeling & Real-Time Underwriting Engine</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------------------------
# NAVIGATION TABS
# ---------------------------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Executive Portfolio Overview",
    "🔍 Risk & Default Drivers",
    "⚙️ Underwriting Decision Simulator",
    "📐 Data Model & Architecture"
])

# =============================================================================================
# TAB 1: EXECUTIVE PORTFOLIO OVERVIEW
# =============================================================================================
with tab1:
    # KPI Row
    total_volume = df['loan_amnt'].sum()
    total_loans = len(df)
    default_count = df['loan_status'].sum()
    default_rate = (default_count / total_loans * 100) if total_loans > 0 else 0
    avg_int_rate = df['loan_int_rate'].mean()
    avg_dti = df['loan_percent_income'].mean() * 100

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Total Portfolio Volume</div>
            <div class="kpi-value">${total_volume/1e6:.1f}M</div>
            <div class="kpi-sub">{total_loans:,} Active Loan Accounts</div>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Portfolio Default Rate</div>
            <div class="kpi-value" style="color: {'#C53030' if default_rate > 20 else '#0F2A4A'};">{default_rate:.2f}%</div>
            <div class="kpi-sub">{int(default_count):,} Total Defaults</div>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Average Interest Rate</div>
            <div class="kpi-value">{avg_int_rate:.2f}%</div>
            <div class="kpi-sub">Risk-Adjusted Portfolio Yield</div>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-title">Avg Debt-to-Income (DTI)</div>
            <div class="kpi-value">{avg_dti:.1f}%</div>
            <div class="kpi-sub">Loan-to-Stated Income Ratio</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Charts Row 1: Loan Grade Breakdown (Volume vs Default Rate)
    col_left, col_right = st.columns([6, 5])

    with col_left:
        st.markdown("#### 📈 Portfolio Exposure & Default Rate by Loan Grade")
        grade_stats = df.groupby('loan_grade').agg(
            total_vol=('loan_amnt', 'sum'),
            loan_count=('loan_amnt', 'count'),
            default_rate=('loan_status', lambda x: x.mean() * 100),
            avg_rate=('loan_int_rate', 'mean')
        ).reset_index()

        fig_grade = go.Figure()
        fig_grade.add_trace(go.Bar(
            x=grade_stats['loan_grade'],
            y=grade_stats['total_vol'] / 1e6,
            name="Funded Volume ($M)",
            marker_color="#1E3A8A",
            yaxis="y"
        ))
        fig_grade.add_trace(go.Scatter(
            x=grade_stats['loan_grade'],
            y=grade_stats['default_rate'],
            name="Default Rate (%)",
            mode="lines+markers+text",
            text=[f"{v:.1f}%" for v in grade_stats['default_rate']],
            textposition="top center",
            line=dict(color="#DC2626", width=3),
            yaxis="y2"
        ))
        fig_grade.update_layout(
            yaxis=dict(title="Funded Volume ($M)", showgrid=True),
            yaxis2=dict(title="Default Rate (%)", overlaying="y", side="right", range=[0, 105]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=40, r=40, t=40, b=30),
            height=380
        )
        st.plotly_chart(fig_grade, use_container_width=True)

    with col_right:
        st.markdown("#### 🎯 Loan Volume & Intent Distribution")
        intent_stats = df.groupby('loan_intent').agg(
            total_vol=('loan_amnt', 'sum'),
            default_rate=('loan_status', lambda x: x.mean() * 100)
        ).reset_index().sort_values(by='total_vol', ascending=True)

        fig_intent = px.bar(
            intent_stats,
            x='total_vol',
            y='loan_intent',
            orientation='h',
            color='default_rate',
            color_continuous_scale='Reds',
            labels={'total_vol': 'Funded Volume ($)', 'loan_intent': 'Loan Purpose', 'default_rate': 'Default %'},
            title="Portfolio Volume by Purpose (Colored by Default Rate)"
        )
        fig_intent.update_layout(height=380, margin=dict(l=40, r=40, t=40, b=30))
        st.plotly_chart(fig_intent, use_container_width=True)

    # Charts Row 2: Home Ownership & Income Distribution
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("#### 🏠 Home Ownership Breakdown")
        home_counts = df['person_home_ownership'].value_counts().reset_index()
        home_counts.columns = ['home_ownership', 'count']
        fig_home = px.pie(
            home_counts,
            names='home_ownership',
            values='count',
            hole=0.45,
            color_discrete_sequence=px.colors.qualitative.Prism
        )
        fig_home.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_home, use_container_width=True)

    with col_b:
        st.markdown("#### 💼 Employment Duration vs Annual Income")
        sample_df = df.sample(min(1500, len(df)), random_state=42).copy()
        sample_df['loan_outcome'] = sample_df['loan_status'].map({0: 'Non-Default', 1: 'Default'})
        fig_scatter = px.scatter(
            sample_df,
            x='person_emp_length',
            y='person_income',
            color='loan_outcome',
            color_discrete_map={'Non-Default': '#10B981', 'Default': '#EF4444'},
            labels={'person_emp_length': 'Employment Length (Years)', 'person_income': 'Annual Income ($)', 'loan_outcome': 'Loan Outcome'},
            opacity=0.6,
            log_y=True
        )
        fig_scatter.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig_scatter, use_container_width=True)

# =============================================================================================
# TAB 2: RISK & DEFAULT DRIVERS
# =============================================================================================
with tab2:
    st.markdown("### 🔬 Underwriting Diagnostics: What Drives Loan Default?")
    st.markdown("In-depth analysis of critical credit indicators: Credit Bureau history, Debt Burden, and Demographic tiers.")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("#### 1. Impact of Historical Default on File")
        bureau_stats = df.groupby('cb_person_default_on_file').agg(
            total_loans=('loan_amnt', 'count'),
            defaulters=('loan_status', 'sum'),
            default_rate=('loan_status', lambda x: x.mean() * 100)
        ).reset_index()
        bureau_stats['label'] = bureau_stats['cb_person_default_on_file'].map({
            'Y': 'Prior Default On File',
            'N': 'Clean Credit Bureau Record'
        })

        fig_bureau = px.bar(
            bureau_stats,
            x='label',
            y='default_rate',
            color='label',
            color_discrete_map={'Prior Default On File': '#DC2626', 'Clean Credit Bureau Record': '#2563EB'},
            text=[f"{r:.2f}%" for r in bureau_stats['default_rate']],
            labels={'default_rate': 'Default Rate (%)', 'label': 'Credit Bureau History'}
        )
        fig_bureau.update_traces(textposition='outside')
        fig_bureau.update_layout(height=350, showlegend=False, yaxis=dict(range=[0, 50]))
        st.plotly_chart(fig_bureau, use_container_width=True)

        st.caption("💡 **Key Finding**: Borrowers with a prior default record on file exhibit a default rate of **37.86%**, more than **double (2.05x)** that of applicants with a clean credit history (18.44%).")

    with c2:
        st.markdown("#### 2. Debt-to-Income (DTI) Bracket Analysis")
        dti_stats = df.groupby('dti_bracket', observed=False).agg(
            total_loans=('loan_amnt', 'count'),
            default_rate=('loan_status', lambda x: x.mean() * 100)
        ).reset_index()

        fig_dti = px.bar(
            dti_stats,
            x='dti_bracket',
            y='default_rate',
            color='default_rate',
            color_continuous_scale='YlOrRd',
            text=[f"{r:.2f}%" for r in dti_stats['default_rate']],
            labels={'default_rate': 'Default Rate (%)', 'dti_bracket': 'Debt Burden (Loan % of Income)'}
        )
        fig_dti.update_traces(textposition='outside')
        fig_dti.update_layout(height=350, yaxis=dict(range=[0, 80]))
        st.plotly_chart(fig_dti, use_container_width=True)

        st.caption("💡 **Key Finding**: The 20% DTI threshold is the primary credit risk tipping point. Default risk surges from **13.56%** in the <20% bracket to **40.53%** when loan amount exceeds 20% of annual income.")

    st.markdown("---")
    c3, c4 = st.columns(2)

    with c3:
        st.markdown("#### 3. Loan Grade vs Interest Rate Pricing Alignment")
        pricing_stats = df.groupby('loan_grade').agg(
            avg_int_rate=('loan_int_rate', 'mean'),
            default_rate=('loan_status', lambda x: x.mean() * 100)
        ).reset_index()

        fig_pricing = px.line(
            pricing_stats,
            x='loan_grade',
            y=['avg_int_rate', 'default_rate'],
            markers=True,
            labels={'value': 'Percentage (%)', 'loan_grade': 'Loan Risk Grade', 'variable': 'Metric'},
            title="Interest Rate vs Actual Default Rate by Grade"
        )
        fig_pricing.update_layout(height=350, legend=dict(title=None, orientation="h", y=1.1, x=0.5, xanchor="center"))
        st.plotly_chart(fig_pricing, use_container_width=True)

        st.caption("💡 **Key Finding**: While interest rates increase systematically from Grade A (7.5%) to Grade G (18.5%), Grade F and G default rates exceed 70% and 98%, indicating subprime tranches require stringent collateral requirements.")

    with c4:
        st.markdown("#### 4. Age Cohort Delinquency Distribution")
        age_stats = df.groupby('age_cohort', observed=False).agg(
            total_loans=('loan_amnt', 'count'),
            default_rate=('loan_status', lambda x: x.mean() * 100)
        ).reset_index()

        fig_age = px.bar(
            age_stats,
            x='age_cohort',
            y='default_rate',
            color='default_rate',
            color_continuous_scale='Blues',
            text=[f"{r:.1f}%" for r in age_stats['default_rate']],
            labels={'default_rate': 'Default Rate (%)', 'age_cohort': 'Age Cohort'}
        )
        fig_age.update_traces(textposition='outside')
        fig_age.update_layout(height=350, yaxis=dict(range=[0, 35]))
        st.plotly_chart(fig_age, use_container_width=True)

        st.caption("💡 **Key Finding**: Young adult applicants (18-25) exhibit slightly higher default tendency (23.5%), whereas mature borrowers (36-50) demonstrate greater stability (19.8%).")

# =============================================================================================
# TAB 3: UNDERWRITING DECISION SIMULATOR
# =============================================================================================
with tab3:
    st.markdown("### ⚙️ Real-Time Credit Underwriting & Risk Scoring Engine")
    st.markdown("Simulate loan application evaluation against portfolio credit policy parameters and empirical default rates.")

    u_col1, u_col2 = st.columns([1, 1])

    with u_col1:
        st.markdown("#### 📋 Applicant Parameters")
        app_age = st.slider("Applicant Age", 18, 80, 28)
        app_income = st.number_input("Annual Stated Income ($)", min_value=1000, max_value=1000000, value=55000, step=2500)
        app_loan_amt = st.number_input("Requested Loan Amount ($)", min_value=500, max_value=100000, value=12000, step=1000)
        app_intent = st.selectbox("Loan Purpose / Intent", options=all_intents, index=0)
        app_home = st.selectbox("Home Ownership Status", options=all_home, index=0)
        app_emp = st.slider("Employment Length (Years)", 0, 40, 4)
        app_prior_default = st.radio("Prior Default on File (Credit Bureau Flag)?", options=["No (Clean)", "Yes (Prior Default)"], horizontal=True)
        app_cred_hist = st.slider("Credit History Length (Years)", 1, 30, 5)

    # Computational Logic
    app_dti = app_loan_amt / app_income if app_income > 0 else 1.0
    has_prior_def = (app_prior_default == "Yes (Prior Default)")

    # Baseline empirical default rate by matched cohort
    matched_cohort = df_raw[
        (df_raw['loan_intent'] == app_intent) &
        (df_raw['cb_person_default_on_file'] == ('Y' if has_prior_def else 'N'))
    ]
    cohort_default_rate = matched_cohort['loan_status'].mean() * 100 if len(matched_cohort) > 0 else 21.87

    # Empirical grade suggestion based on DTI and bureau history
    if app_dti < 0.15 and not has_prior_def and app_emp >= 2:
        assigned_grade = "A"
        suggested_rate = 7.49
        risk_tier = "Prime / Low Risk"
        decision = "APPROVED"
        decision_class = "badge-approved"
        adverse_reasons = []
    elif app_dti < 0.25 and not has_prior_def:
        assigned_grade = "B"
        suggested_rate = 10.25
        risk_tier = "Prime / Standard Risk"
        decision = "APPROVED"
        decision_class = "badge-approved"
        adverse_reasons = []
    elif app_dti <= 0.35 and not has_prior_def:
        assigned_grade = "C"
        suggested_rate = 13.15
        risk_tier = "Near-Prime / Moderate Risk"
        decision = "CONDITIONAL APPROVAL"
        decision_class = "badge-review"
        adverse_reasons = ["Debt-to-Income elevated (25% - 35%); mandatory income verification required."]
    elif app_dti <= 0.35 and has_prior_def:
        assigned_grade = "D"
        suggested_rate = 15.65
        risk_tier = "Subprime / Elevated Risk"
        decision = "MANUAL UNDERWRITING REVIEW"
        decision_class = "badge-review"
        adverse_reasons = ["Prior credit bureau delinquency on file.", "Requires secondary credit committee sign-off or co-borrower."]
    else:
        assigned_grade = "E" if app_dti <= 0.45 else "F"
        suggested_rate = 18.25
        risk_tier = "High Risk / Policy Exception"
        decision = "DECLINED"
        decision_class = "badge-declined"
        adverse_reasons = [
            f"Debt-to-Income ratio ({app_dti*100:.1f}%) exceeds maximum statutory lending policy ceiling (35%).",
            "Severe probability of default predicted under current debt structure."
        ]

    with u_col2:
        st.markdown("#### ⚖️ Underwriting Scorecard & Decision")
        st.markdown(f"**Underwriting Assessment:** <span class='{decision_class}'>{decision}</span>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        sc1, sc2 = st.columns(2)
        with sc1:
            st.metric("Calculated DTI Ratio", f"{app_dti * 100:.2f}%", delta="Normal" if app_dti < 0.25 else "High", delta_color="inverse")
            st.metric("Assigned Loan Risk Grade", f"Grade {assigned_grade}", f"{risk_tier}")
        with sc2:
            st.metric("Risk-Adjusted Pricing Rate", f"{suggested_rate:.2f}%", "Annual APR")
            st.metric("Cohort Historical Default Rate", f"{cohort_default_rate:.2f}%", f"{len(matched_cohort):,} peer loans")

        st.markdown("---")
        st.markdown("##### 📌 Underwriting Policy Audit Notes:")
        if decision == "APPROVED":
            st.success("✅ Application meets all primary credit policy guidelines. Automated instant funding recommended.")
        elif decision in ["CONDITIONAL APPROVAL", "MANUAL UNDERWRITING REVIEW"]:
            st.warning("⚠️ Application flags risk policy thresholds. Requires credit officer underwriting review.")
            for r in adverse_reasons:
                st.write(f"- {r}")
        else:
            st.error("❌ Application violates risk criteria. Adverse action notice recommended.")
            for r in adverse_reasons:
                st.write(f"- {r}")

        st.markdown("##### 💡 Recommended Mitigation Actions:")
        if app_dti > 0.30:
            max_safe_loan = app_income * 0.25
            st.info(f"Counter-Offer Suggestion: Reduce loan principal to **${max_safe_loan:,.0f}** to bring DTI into prime 25% threshold.")

# =============================================================================================
# TAB 4: DATA MODEL & ARCHITECTURE
# =============================================================================================
with tab4:
    st.markdown("### 📐 Enterprise Star Schema & Data Architecture")
    st.markdown("The underlying analytical database is structured as an **Enterprise Star Schema**, separating transactional metrics from descriptive business dimensions.")

    st.markdown("""
    ```
    ┌─────────────────────────────────┐
    │          dim_borrower           │
    ├─────────────────────────────────┤
    │ PK: borrower_key                │
    │     person_age, age_group       │
    │     person_income, bracket      │
    │     person_home_ownership       │
    │     person_emp_length           │
    │     cb_person_default_on_file   │
    │     cb_person_cred_hist_length  │
    └────────────────┬────────────────┘
                     │ 1
                     │
                     │ *
    ┌────────────────┴────────────────┐         ┌───────────────────────────────┐
    │     fact_loan_applications      │ *     1 │       dim_loan_profile        │
    ├─────────────────────────────────┼─────────┤───────────────────────────────┤
    │ PK: application_id              │         │ PK: loan_profile_key          │
    │ FK: borrower_key                │         │     loan_intent               │
    │ FK: loan_profile_key            │         │     loan_grade (A - G)        │
    │     loan_amount                 │         │     risk_category             │
    │     interest_rate               │         │     expected_loss_tier        │
    │     loan_status (0/1)           │         └───────────────────────────────┘
    │     loan_percent_income (DTI)   │
    │     is_defaulted (Boolean)      │
    └─────────────────────────────────┘
    ```
    """)

    st.markdown("---")
    st.markdown("#### 📂 Preview Cleaned Warehouse Dataset")
    st.dataframe(df.head(100), use_container_width=True)

    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Cleaned Dataset (CSV)",
        data=csv_data,
        file_name="credit_risk_cleaned_kotak.csv",
        mime="text/csv"
    )

# ---------------------------------------------------------------------------------------------
# FOOTER
# ---------------------------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #718096; font-size: 0.85rem;'>"
    "Enterprise Credit Risk Analytics & Underwriting Platform | Developed by Disha Jain | "
    "Kotak Mahindra Group Alignment"
    "</div>",
    unsafe_allow_html=True
)
