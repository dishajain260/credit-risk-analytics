# Enterprise Credit Risk Data Model Documentation

This document outlines the dimensional architecture, table specifications, and data dictionary for the Credit Risk Analytics Platform, designed in accordance with enterprise data warehousing best practices.

---

## 1. Dimensional Architecture Overview

The data warehouse implements an industry-standard **Star Schema** optimized for analytical querying, Power BI VertiPaq engine compression, and interactive DAX measures.

```
+-----------------------------------+
|           dim_borrower            |
+-----------------------------------+
| PK: borrower_key (INT)            |
|     person_age (INT)              |
|     age_group (VARCHAR)           |
|     person_income (DECIMAL)       |
|     income_bracket (VARCHAR)      |
|     person_home_ownership (VC)    |
|     person_emp_length (INT)       |
|     employment_tier (VARCHAR)     |
|     cb_person_default_on_file (CH)|
|     cb_person_cred_hist_length(IN)|
+-----------------+-----------------+
                  | 1
                  |
                  | *
+-----------------+-----------------+       +-----------------------------------+
|      fact_loan_applications       | *   1 |         dim_loan_profile          |
+-----------------------------------+-------+-----------------------------------+
| PK: application_id (INT)          |       | PK: loan_profile_key (INT)        |
| FK: borrower_key (INT)            |       |     loan_intent (VARCHAR)         |
| FK: loan_profile_key (INT)        |       |     loan_grade (CHAR)             |
|     loan_amount (DECIMAL)         |       |     risk_category (VARCHAR)       |
|     interest_rate (DECIMAL)       |       |     expected_loss_tier (VARCHAR)  |
|     loan_status (TINYINT)         |       +-----------------------------------+
|     loan_percent_income (DECIMAL) |
|     is_defaulted (BOOLEAN)        |
+-----------------------------------+
```

---

## 2. Table Specifications

### Central Fact Table: `fact_loan_applications`
- **Granularity**: One row per funded loan application.
- **Role**: Stores numerical measures, pricing rates, and repayment outcomes.

| Column | Data Type | Key Type | Description |
| :--- | :--- | :--- | :--- |
| `application_id` | INT | Primary Key | Unique surrogate identifier for each loan record |
| `borrower_key` | INT | Foreign Key | References `dim_borrower.borrower_key` |
| `loan_profile_key` | INT | Foreign Key | References `dim_loan_profile.loan_profile_key` |
| `loan_amount` | DECIMAL(12,2) | Measure | Funded loan principal amount ($) |
| `interest_rate` | DECIMAL(5,2) | Measure | Contractual loan interest rate (%) |
| `loan_status` | TINYINT | Dimension / Measure | Repayment outcome: `0` = Non-Defaulter, `1` = Defaulter |
| `loan_percent_income` | DECIMAL(5,4) | Measure | Debt burden ratio (`loan_amount / annual_income`) |
| `is_defaulted` | BOOLEAN | Calculated Flag | Boolean flag indicating default event |

---

### Dimension Table: `dim_borrower`
- **Granularity**: One row per borrower profile.
- **Role**: Contains demographic, socioeconomic, and credit bureau indicators.

| Column | Data Type | Key Type | Description / Logic |
| :--- | :--- | :--- | :--- |
| `borrower_key` | INT | Primary Key | Unique surrogate key for borrower |
| `person_age` | INT | Attribute | Chronological age of applicant (18–99) |
| `age_group` | VARCHAR(30) | Attribute | Cohorts: `18-25`, `26-35`, `36-50`, `51+` |
| `person_income` | DECIMAL(12,2) | Attribute | Stated annual income ($) |
| `income_bracket` | VARCHAR(30) | Attribute | Tiered brackets: `<$30k`, `$30k-$60k`, `$60k-$100k`, `$100k+` |
| `person_home_ownership` | VARCHAR(20) | Attribute | Standardized ownership: `Rent`, `Own`, `Mortgage`, `Other` |
| `person_emp_length` | INT | Attribute | Total employment duration in years (0–45) |
| `employment_tier` | VARCHAR(30) | Attribute | `Entry (<2 yrs)`, `Mid (2-5 yrs)`, `Senior (6+ yrs)` |
| `cb_person_default_on_file` | CHAR(1) | Attribute | Bureau flag: `Y` = Prior default record, `N` = Clean record |
| `cb_person_cred_hist_length`| INT | Attribute | Duration of active credit bureau history in years |

---

### Dimension Table: `dim_loan_profile`
- **Granularity**: Unique combinations of loan purpose and underwriting credit grade.
- **Role**: Governs portfolio segmentation, risk banding, and pricing tiers.

| Column | Data Type | Key Type | Description / Logic |
| :--- | :--- | :--- | :--- |
| `loan_profile_key` | INT | Primary Key | Surrogate key for loan classification |
| `loan_intent` | VARCHAR(50) | Attribute | Purpose: `Debt consolidation`, `Education`, `Home improvement`, `Medical`, `Personal`, `Venture` |
| `loan_grade` | CHAR(1) | Attribute | Underwriting rating scale from `A` (Lowest Risk) to `G` (Highest Risk) |
| `risk_category` | VARCHAR(30) | Attribute | `Prime / Low Risk` (A-B), `Near-Prime` (C-D), `Subprime` (E-G) |
| `expected_loss_tier` | VARCHAR(30) | Attribute | `Tier 1 (<15% PD)`, `Tier 2 (15%-40% PD)`, `Tier 3 (>40% PD)` |

---

## 3. Core DAX & Analytical Metric Formulas

1. **Portfolio Default Rate (%)**:
   ```dax
   Default Rate = DIVIDE(
       CALCULATE(COUNTROWS('fact_loan_applications'), 'fact_loan_applications'[loan_status] = 1),
       COUNTROWS('fact_loan_applications'),
       0
   ) * 100
   ```

2. **Total Exposure ($)**:
   ```dax
   Total Funded Amount = SUM('fact_loan_applications'[loan_amount])
   ```

3. **Weighted Average Interest Rate (%)**:
   ```dax
   Weighted Avg Interest Rate = DIVIDE(
       SUMX('fact_loan_applications', 'fact_loan_applications'[loan_amount] * 'fact_loan_applications'[interest_rate]),
       SUM('fact_loan_applications'[loan_amount]),
       0
   )
   ```

4. **Risk Multiplier (Prior Default)**:
   ```dax
   Default Multiplier = DIVIDE(
       CALCULATE([Default Rate], 'dim_borrower'[cb_person_default_on_file] = "Y"),
       CALCULATE([Default Rate], 'dim_borrower'[cb_person_default_on_file] = "N"),
       0
   )
   ```
