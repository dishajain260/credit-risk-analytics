-- =============================================================================================
-- Enterprise Credit Risk Analytics Platform | Kotak Mahindra Group Alignment
-- Script: 02_exploratory_data_analysis.sql
-- Description: Diagnostic queries measuring credit portfolio exposure, default risk drivers,
--              and interest rate pricing consistency across underwriting dimensions.
-- =============================================================================================

-- =============================================================================================
-- 1. PORTFOLIO VOLUME & OVERALL DEFAULT KPI
-- Baseline metrics for executive reporting: total book size, default count, and delinquency rate
-- =============================================================================================

SELECT 
    COUNT(*) AS total_borrowers,
    SUM(loan_amnt) AS total_portfolio_amount,
    ROUND(AVG(loan_amnt), 2) AS avg_loan_size,
    SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) AS total_defaulters,
    SUM(CASE WHEN loan_status = 0 THEN 1 ELSE 0 END) AS total_non_defaulters,
    ROUND(SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS portfolio_default_rate_pct
FROM credit_risk_cleaned;

-- =============================================================================================
-- 2. INTEREST RATE & RISK-BASED PRICING ALIGNMENT
-- Assessing whether higher risk segments are adequately priced with risk premiums
-- =============================================================================================

-- Overall Average Interest Rate
SELECT 
    ROUND(AVG(loan_int_rate), 2) AS overall_avg_interest_rate
FROM credit_risk_cleaned;

-- Interest Rate Spread between Defaulters and Non-Defaulters
SELECT 
    CASE WHEN loan_status = 1 THEN 'Defaulter' ELSE 'Non-Defaulter' END AS borrower_status,
    COUNT(*) AS borrower_count,
    ROUND(AVG(loan_int_rate), 2) AS avg_interest_rate_pct,
    ROUND(AVG(loan_percent_income) * 100, 2) AS avg_dti_pct
FROM credit_risk_cleaned
GROUP BY loan_status;

-- Average Interest Rate & Volume by Loan Risk Grade (A through G)
SELECT 
    loan_grade,
    COUNT(*) AS total_loans,
    ROUND(SUM(loan_amnt), 2) AS total_volume,
    ROUND(AVG(loan_int_rate), 2) AS avg_interest_rate_pct,
    ROUND(SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS default_rate_pct
FROM credit_risk_cleaned
GROUP BY loan_grade
ORDER BY loan_grade ASC;

-- Average Interest Rate & Default Distribution by Loan Intent
SELECT 
    loan_intent,
    COUNT(*) AS total_loans,
    ROUND(AVG(loan_amnt), 2) AS avg_loan_size,
    ROUND(AVG(loan_int_rate), 2) AS avg_interest_rate_pct,
    SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) AS defaulter_count,
    ROUND(SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS default_rate_pct
FROM credit_risk_cleaned
GROUP BY loan_intent
ORDER BY default_rate_pct DESC;

-- =============================================================================================
-- 3. CORE RISK DRIVERS & UNDERWRITING SENSITIVITY
-- Diagnostic analysis of credit history, debt burden, and demographic characteristics
-- =============================================================================================

-- Risk Driver 1: Impact of Historical Default on File (Credit Bureau Flag)
SELECT 
    cb_person_default_on_file AS has_historical_default,
    COUNT(*) AS total_borrowers,
    SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) AS current_defaulters,
    ROUND(SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS current_default_rate_pct
FROM credit_risk_cleaned
GROUP BY cb_person_default_on_file;

-- Risk Driver 2: Debt-to-Income / Loan Percent of Income (DTI) Tier Analysis
SELECT 
    CASE 
        WHEN loan_percent_income < 0.20 THEN '1. Low (< 20%)'
        WHEN loan_percent_income < 0.40 THEN '2. Moderate (20% - 40%)'
        ELSE '3. High (> 40%)'
    END AS dti_bracket,
    COUNT(*) AS total_loans,
    ROUND(SUM(loan_amnt), 2) AS total_exposure,
    ROUND(SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS default_rate_pct
FROM credit_risk_cleaned
GROUP BY 
    CASE 
        WHEN loan_percent_income < 0.20 THEN '1. Low (< 20%)'
        WHEN loan_percent_income < 0.40 THEN '2. Moderate (20% - 40%)'
        ELSE '3. High (> 40%)'
    END
ORDER BY dti_bracket ASC;

-- Risk Driver 3: Age Demographics and Default Distribution
SELECT 
    CASE 
        WHEN person_age BETWEEN 18 AND 25 THEN '18-25 (Young Adult)'
        WHEN person_age BETWEEN 26 AND 35 THEN '26-35 (Core Career)'
        WHEN person_age BETWEEN 36 AND 50 THEN '36-50 (Mature)'
        ELSE '51+ (Senior)'
    END AS age_cohort,
    COUNT(*) AS total_borrowers,
    ROUND(AVG(person_income), 2) AS avg_annual_income,
    ROUND(AVG(loan_amnt), 2) AS avg_loan_amount,
    ROUND(SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS default_rate_pct
FROM credit_risk_cleaned
GROUP BY 
    CASE 
        WHEN person_age BETWEEN 18 AND 25 THEN '18-25 (Young Adult)'
        WHEN person_age BETWEEN 26 AND 35 THEN '26-35 (Core Career)'
        WHEN person_age BETWEEN 36 AND 50 THEN '36-50 (Mature)'
        ELSE '51+ (Senior)'
    END
ORDER BY age_cohort ASC;

-- Risk Driver 4: Home Ownership Risk Profile
SELECT 
    person_home_ownership,
    COUNT(*) AS total_borrowers,
    ROUND(AVG(person_income), 2) AS avg_income,
    ROUND(SUM(CASE WHEN loan_status = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) AS default_rate_pct
FROM credit_risk_cleaned
GROUP BY person_home_ownership
ORDER BY default_rate_pct DESC;
