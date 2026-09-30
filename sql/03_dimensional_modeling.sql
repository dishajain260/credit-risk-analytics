-- =============================================================================================
-- Enterprise Credit Risk Analytics Platform | Kotak Mahindra Group Alignment
-- Script: 03_dimensional_modeling.sql
-- Description: DDL & ELT pipeline transforming cleaned tabular credit data into an optimized
--              Enterprise Star Schema (Fact and Dimension tables) for Power BI and Analytics.
-- =============================================================================================

-- =============================================================================================
-- 1. DIMENSION TABLE: dim_borrower
-- Stores demographic, socioeconomic, and credit history attributes of loan applicants
-- =============================================================================================

DROP TABLE IF EXISTS dim_borrower;

CREATE TABLE dim_borrower (
    borrower_key INT AUTO_INCREMENT PRIMARY KEY,
    person_age INT,
    age_group VARCHAR(30),
    person_income DECIMAL(12, 2),
    income_bracket VARCHAR(30),
    person_home_ownership VARCHAR(20),
    person_emp_length INT,
    employment_tier VARCHAR(30),
    cb_person_default_on_file CHAR(1),
    cb_person_cred_hist_length INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================================
-- 2. DIMENSION TABLE: dim_loan_profile
-- Stores loan categorization, intent, underwriting risk grades, and pricing terms
-- =============================================================================================

DROP TABLE IF EXISTS dim_loan_profile;

CREATE TABLE dim_loan_profile (
    loan_profile_key INT AUTO_INCREMENT PRIMARY KEY,
    loan_intent VARCHAR(50),
    loan_grade CHAR(1),
    risk_category VARCHAR(30),
    expected_loss_tier VARCHAR(30)
);

-- Populate unique combinations of loan attributes into dim_loan_profile
INSERT INTO dim_loan_profile (loan_intent, loan_grade, risk_category, expected_loss_tier)
SELECT DISTINCT
    loan_intent,
    loan_grade,
    CASE 
        WHEN loan_grade IN ('A', 'B') THEN 'Prime / Low Risk'
        WHEN loan_grade IN ('C', 'D') THEN 'Near-Prime / Moderate Risk'
        ELSE 'Subprime / High Risk'
    END AS risk_category,
    CASE 
        WHEN loan_grade IN ('A', 'B') THEN 'Tier 1 (< 15% PD)'
        WHEN loan_grade IN ('C', 'D') THEN 'Tier 2 (15% - 40% PD)'
        ELSE 'Tier 3 (> 40% PD)'
    END AS expected_loss_tier
FROM credit_risk_cleaned;

-- =============================================================================================
-- 3. FACT TABLE: fact_loan_applications
-- Central fact table storing financial measures, loan amounts, interest rates, and default status
-- =============================================================================================

DROP TABLE IF EXISTS fact_loan_applications;

CREATE TABLE fact_loan_applications (
    application_id INT AUTO_INCREMENT PRIMARY KEY,
    borrower_key INT,
    loan_profile_key INT,
    loan_amount DECIMAL(12, 2),
    interest_rate DECIMAL(5, 2),
    loan_status TINYINT, -- 0 = Non-Defaulter, 1 = Defaulter
    loan_percent_income DECIMAL(5, 4), -- DTI ratio
    is_defaulted BOOLEAN GENERATED ALWAYS AS (loan_status = 1) STORED,
    CONSTRAINT fk_borrower FOREIGN KEY (borrower_key) REFERENCES dim_borrower(borrower_key),
    CONSTRAINT fk_loan_profile FOREIGN KEY (loan_profile_key) REFERENCES dim_loan_profile(loan_profile_key)
);

-- =============================================================================================
-- 4. ELT POPULATION PIPELINE
-- Load dimensions and link surrogate keys into the central fact table
-- =============================================================================================

-- Populate dim_borrower
INSERT INTO dim_borrower (
    person_age,
    age_group,
    person_income,
    income_bracket,
    person_home_ownership,
    person_emp_length,
    employment_tier,
    cb_person_default_on_file,
    cb_person_cred_hist_length
)
SELECT 
    person_age,
    CASE 
        WHEN person_age BETWEEN 18 AND 25 THEN '18-25'
        WHEN person_age BETWEEN 26 AND 35 THEN '26-35'
        WHEN person_age BETWEEN 36 AND 50 THEN '36-50'
        ELSE '51+'
    END AS age_group,
    person_income,
    CASE 
        WHEN person_income < 30000 THEN '< $30k'
        WHEN person_income < 60000 THEN '$30k - $60k'
        WHEN person_income < 100000 THEN '$60k - $100k'
        ELSE '$100k+'
    END AS income_bracket,
    person_home_ownership,
    person_emp_length,
    CASE 
        WHEN person_emp_length < 2 THEN 'Entry (< 2 yrs)'
        WHEN person_emp_length < 6 THEN 'Mid (2-5 yrs)'
        ELSE 'Senior (6+ yrs)'
    END AS employment_tier,
    cb_person_default_on_file,
    cb_person_cred_hist_length
FROM credit_risk_cleaned;

-- Populate fact_loan_applications by joining with dim_loan_profile and dim_borrower
INSERT INTO fact_loan_applications (
    borrower_key,
    loan_profile_key,
    loan_amount,
    interest_rate,
    loan_status,
    loan_percent_income
)
SELECT 
    b.borrower_key,
    lp.loan_profile_key,
    c.loan_amnt,
    c.loan_int_rate,
    c.loan_status,
    c.loan_percent_income
FROM (
    SELECT 
        *, 
        ROW_NUMBER() OVER(ORDER BY person_age, person_income, loan_amnt) AS rn 
    FROM credit_risk_cleaned
) c
JOIN (
    SELECT 
        *, 
        ROW_NUMBER() OVER(ORDER BY person_age, person_income) AS rn 
    FROM dim_borrower
) b ON c.rn = b.rn
JOIN dim_loan_profile lp 
    ON c.loan_intent = lp.loan_intent 
    AND c.loan_grade = lp.loan_grade;

-- Star Schema Verification & Fast Aggregate Check
SELECT 
    lp.risk_category,
    COUNT(f.application_id) AS total_loans,
    ROUND(SUM(f.loan_amount), 2) AS total_funded_volume,
    ROUND(AVG(f.interest_rate), 2) AS avg_interest_rate,
    ROUND(AVG(f.loan_status) * 100, 2) AS default_rate_pct
FROM fact_loan_applications f
JOIN dim_loan_profile lp ON f.loan_profile_key = lp.loan_profile_key
GROUP BY lp.risk_category
ORDER BY default_rate_pct ASC;
