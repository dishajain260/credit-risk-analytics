# Credit Risk Analytics Platform — Interview Master Guide
> **Tailored for Kotak Mahindra Group / Banking Software & BI Roles**

This guide is your complete cheat sheet for explaining this project in technical and business interviews. It breaks down the architecture, data pipeline decisions, dimensional modeling rationale, and business insights into clear talking points.

---

## 1. The 30-Second Elevator Pitch

> *"I developed an end-to-end Credit Risk Analytics & Underwriting Platform that analyzes retail lending portfolios to optimize credit decisions and reduce loan defaults. The solution extracts and cleans 32,400+ applicant records in SQL, models them into an Enterprise Star Schema (Fact and Dimension tables), and exposes interactive analytics through both a Power BI executive suite and a deployed Python/Streamlit web application with an automated underwriting risk calculator. Across the $311M portfolio, the platform proved that historical default records double applicant default probability (37.9% vs 18.4%), identified that DTI over 20% triples default risk, and verified risk-based pricing alignment across loan grades A through G."*

---

## 2. System Architecture & End-to-End Pipeline

```
[ Raw Lending Data ]
       │
       ▼
[ Step 1: SQL Staging & Cleansing ] (01_data_cleaning.sql)
       ├─ Deduplication (Window Functions: ROW_NUMBER)
       ├─ String standardization & formatting
       ├─ Risk-grade median/average imputation for missing interest rates
       └─ Outlier & logical anomaly filtration (age ≥ 100, employment > 45 yrs)
       │
       ▼
[ Step 2: Dimensional Modeling ] (03_dimensional_modeling.sql)
       ├─ dim_borrower (Demographics, Bureau Credit History, Income Tiers)
       ├─ dim_loan_profile (Loan Intent, Risk Grade A-G, Expected Loss Tiers)
       └─ fact_loan_applications (Loan Amount, Rate, Status, DTI)
       │
       ▼
[ Step 3: Analytical Consumption & Deployment ]
       ├─ Power BI Executive Dashboard (.pbix) — 3-page executive reporting
       ├─ Python Web Application (app.py) — Interactive BI dashboard + Underwriting Calculator
       └─ Cloud Deployment (Streamlit Community Cloud / GitHub)
```

---

## 3. Key Data Engineering & Cleaning Decisions (Why You Did What You Did)

When interviewers ask: *"How did you clean the data?"* or *"Why didn't you just drop all nulls?"*

1. **Staging Table Pattern**:
   - *Why*: Never run transformations directly on raw tables. Staging (`credit_risk_stage`) preserves auditability and raw data lineage.
2. **Deduplication via Window Function (`ROW_NUMBER() OVER(PARTITION BY ...)`):**
   - *Why*: In banking transaction feeds, network retries or batch re-runs often introduce duplicate entries. Using `ROW_NUMBER()` allows precise identification and deterministic deduplication.
3. **Domain-Specific Imputation for Missing Interest Rates**:
   - *Why*: Interest rate was missing for ~3,000 records. Dropping them would discard valuable default outcome data. Using a global mean would distort risk pricing because interest rates strictly scale with credit risk grade (Grade A ~7.5%, Grade G ~18.5%). We imputed missing rates using the **group average of the corresponding loan grade**.
4. **Logical Anomaly Elimination**:
   - *Why*: Records with age $\ge 100$ or employment $> 45$ years represented corrupt data entries (including an erroneous \$6M income outlier). In risk modeling, preserving corrupt data distorts statistical loss distributions.

---

## 4. Dimensional Modeling (Star Schema) Concepts

When interviewers ask: *"Why did you use a Star Schema instead of keeping one flat table?"*

1. **Star Schema vs. 3NF / Snowflake**:
   - **Performance**: Star Schema creates single-hop joins between the fact table (`fact_loan_applications`) and dimensions (`dim_borrower`, `dim_loan_profile`). In analytical engines like Power BI (VertiPaq) and Snowflake, this minimizes query join overhead.
   - **Simplicity & Usability**: Business users and dashboard designers can easily slice metrics without navigating complex multi-level snowflake hierarchies.
   - **Columnar Compression**: High cardinality numeric facts stay in the fact table, while low-cardinality repetitive strings live in dimension tables, maximizing memory compression.
2. **Fact vs. Dimension Tables**:
   - **Fact Table**: Contains quantitative financial measures (`loan_amount`, `interest_rate`, `loan_status`, `loan_percent_income`).
   - **Dimension Tables**: Provide descriptive context and filtering hierarchies (`age_group`, `loan_grade`, `loan_intent`, `cb_person_default_on_file`).

---

## 5. Core Banking & Credit Risk Metrics

| Metric | Formula | Business Meaning in Lending |
| :--- | :--- | :--- |
| **Default Rate (PD)** | $\frac{\text{Defaulted Loans}}{\text{Total Loans}} \times 100$ | Baseline Probability of Default across the portfolio (**21.87%** overall). |
| **DTI / Loan-to-Income** | $\frac{\text{Loan Amount}}{\text{Annual Income}}$ | Measures debt burden. Borrowers with DTI $> 20\%$ default at nearly $3\times$ the rate of low DTI borrowers ($40.5\%$ vs $13.6\%$). |
| **Risk-Based Pricing** | Interest Rate by Grade | Verifies that high-risk borrowers pay an appropriate risk premium (Grade A: $7.5\%$ rate / $9.9\%$ default vs Grade G: $18.5\%$ rate / $98.4\%$ default). |
| **Bureau Multiplier** | $\frac{\text{Default Rate (Prior Default)}}{\text{Default Rate (Clean Record)}}$ | Bureau historical default flag is a **2.05x risk multiplier** ($37.9\%$ vs $18.4\%$). |

---

## 6. Top 10 Technical Interview Questions & Answers

### Q1: What was your role in this project?
> **Answer**: I was responsible for end-to-end data pipeline development: writing the SQL data staging, cleaning, and validation scripts; designing the dimensional Star Schema; implementing diagnostic EDA queries; and building an interactive Python/Streamlit web dashboard featuring an automated underwriting risk scoring engine.

### Q2: How did you validate data quality before feeding it into reporting?
> **Answer**: I wrote validation checks in SQL to ensure zero negative loan amounts, zero negative incomes, checked completeness across key fields, verified categorical cardinality (loan grades restricted to A–G), and ensured that imputed interest rates fell strictly within the 5th to 95th percentile of their respective risk grade cohorts.

### Q3: Why did you choose Python/Streamlit in addition to Power BI?
> **Answer**: While Power BI is excellent for internal executive reporting, banking loan officers and branch underwriters need real-time, interactive decision support tools that can be accessed via web applications without desktop software licenses. Streamlit allowed me to deploy a full software application with dynamic filtering and an automated risk-scoring simulator that computes instant approval recommendations.

### Q4: If an applicant has a previous default on file, would you automatically reject them?
> **Answer**: Not necessarily, but they require strict underwriting controls. Our EDA showed that applicants with a prior default have a 37.9% default rate. However, if their Debt-to-Income (DTI) is under 15% and they are applying for lower-risk intents (e.g. venture/education with guarantor or collateral), the bank can approve them with appropriate risk-based interest rate pricing or collateral requirements.

### Q5: How would you scale this pipeline for millions of records in an Enterprise Cloud warehouse?
> **Answer**: In a cloud data warehouse like Google BigQuery or Snowflake:
> 1. Use partitioned tables on application date and cluster by `loan_grade` and `borrower_key`.
> 2. Implement an automated orchestration DAG (e.g. Apache Airflow / Cloud Composer or dbt) for incremental batch ELT.
> 3. Cache summary aggregate tables (marts) for high-frequency dashboard queries.

### Q6: What is the most critical risk driver you discovered?
> **Answer**: Loan Risk Grade and Debt-to-Income (DTI). While loan grade captures overall creditworthiness, DTI is the strongest inflection point: once loan amount exceeds 20% of annual income, default probability spikes from 13.56% to 40.53%.

### Q7: What are the differences between Type 1, Type 2, and Type 3 Slowly Changing Dimensions (SCD)?
> **Answer**: In our model, `dim_borrower` could track changes over time. SCD Type 1 overwrites old data (no history). SCD Type 2 adds a new row with validity dates (`effective_date`, `end_date`, `is_current`) to maintain complete audit history—ideal for tracking credit score changes in banking. SCD Type 3 adds a previous value column to track only the immediate prior state.

### Q8: What DAX measures did you create for performance optimization?
> **Answer**: I used explicit measures using `DIVIDE()` to handle division-by-zero safely and `CALCULATE()` with `KEEPFILTERS()` to preserve filter context. For large tables, I avoided row-by-row iterators (`SUMX`) on non-indexed calculated columns and leveraged column-store VertiPaq engine aggregation.

### Q9: Which loan intent had the highest default rate, and why?
> **Answer**: Debt consolidation loans had the highest default frequency. Borrowers seeking debt consolidation often already experience liquidity strain or cash flow constraints, making them sensitive to minor economic shocks compared to borrowers taking out targeted educational or venture loans.

### Q10: How does your Python application compute loan approval recommendations?
> **Answer**: The underwriting engine checks three primary criteria:
> 1. **DTI Ratio**: Must be $\le 35\%$.
> 2. **Credit History**: Evaluates historical default flag and assigns a penalty score.
> 3. **Risk Grade**: Checks loan grade tier. 
> If the combined risk score exceeds the acceptable risk tolerance threshold, it flags the application for secondary credit committee review or declines it with explicit adverse action reasons.
