-- =============================================================================================
-- Enterprise Credit Risk Analytics Platform | Kotak Mahindra Group Alignment
-- Script: 01_data_cleaning.sql
-- Description: Production-ready data staging, cleaning, validation, and imputation pipeline
-- Target Table: credit_risk_cleaned
-- =============================================================================================

-- STEP 1: DATA STAGING
-- Create a staging copy of raw credit records to preserve original source data integrity
CREATE TABLE IF NOT EXISTS credit_risk_stage LIKE credit_risk_raw;

INSERT INTO credit_risk_stage
SELECT * FROM credit_risk_raw;

-- =============================================================================================
-- STEP 2: DEDUPLICATION
-- Identify and remove exact duplicate records across borrower and loan attributes
-- =============================================================================================

WITH ranked_records AS (
    SELECT 
        person_age,
        person_income,
        person_home_ownership,
        person_emp_length,
        loan_intent,
        loan_grade,
        loan_amnt,
        loan_int_rate,
        loan_status,
        loan_percent_income,
        cb_person_default_on_file,
        cb_person_cred_hist_length,
        ROW_NUMBER() OVER(
            PARTITION BY 
                person_age, person_income, person_home_ownership, person_emp_length,
                loan_intent, loan_grade, loan_amnt, loan_int_rate, loan_status,
                loan_percent_income, cb_person_default_on_file, cb_person_cred_hist_length
            ORDER BY person_age
        ) AS duplicate_rank
    FROM credit_risk_stage
)
SELECT * 
FROM ranked_records
WHERE duplicate_rank > 1;

-- Create working table containing deduplicated data
CREATE TABLE credit_risk_cleaned AS
SELECT 
    person_age,
    person_income,
    person_home_ownership,
    person_emp_length,
    loan_intent,
    loan_grade,
    loan_amnt,
    loan_int_rate,
    loan_status,
    loan_percent_income,
    cb_person_default_on_file,
    cb_person_cred_hist_length
FROM (
    SELECT 
        *,
        ROW_NUMBER() OVER(
            PARTITION BY 
                person_age, person_income, person_home_ownership, person_emp_length,
                loan_intent, loan_grade, loan_amnt, loan_int_rate, loan_status,
                loan_percent_income, cb_person_default_on_file, cb_person_cred_hist_length
            ORDER BY person_age
        ) AS duplicate_rank
    FROM credit_risk_stage
) t
WHERE duplicate_rank = 1;

-- =============================================================================================
-- STEP 3: TEXT STANDARDIZATION & CATEGORICAL CLEANING
-- Normalize casing and spacing in categorical attributes for consistent dimensional modeling
-- =============================================================================================

-- Standardize Loan Intent values to Title Case with clean spacing
UPDATE credit_risk_cleaned
SET loan_intent = CONCAT(UPPER(LEFT(TRIM(loan_intent), 1)), LOWER(SUBSTRING(TRIM(loan_intent), 2)));

UPDATE credit_risk_cleaned
SET loan_intent = REPLACE(REPLACE(loan_intent, 'Debtconsolidation', 'Debt consolidation'), 'Homeimprovement', 'Home improvement');

-- Standardize Home Ownership values to Title Case
UPDATE credit_risk_cleaned
SET person_home_ownership = CONCAT(UPPER(LEFT(TRIM(person_home_ownership), 1)), LOWER(SUBSTRING(TRIM(person_home_ownership), 2)));

-- =============================================================================================
-- STEP 4: NULL VALUE HANDLING & GROUP-BASED IMPUTATION
-- Handle empty strings and impute missing interest rates using risk-grade group averages
-- =============================================================================================

-- Convert blank strings to true NULLs
UPDATE credit_risk_cleaned
SET loan_int_rate = NULL
WHERE TRIM(loan_int_rate) = '' OR loan_int_rate = 0;

UPDATE credit_risk_cleaned
SET person_emp_length = NULL
WHERE TRIM(person_emp_length) = '';

-- Impute missing interest rates with average interest rate of corresponding loan risk grade
UPDATE credit_risk_cleaned t
JOIN (
    SELECT loan_grade, ROUND(AVG(loan_int_rate), 2) AS avg_grade_rate
    FROM credit_risk_cleaned
    WHERE loan_int_rate IS NOT NULL
    GROUP BY loan_grade
) g ON t.loan_grade = g.loan_grade
SET t.loan_int_rate = g.avg_grade_rate
WHERE t.loan_int_rate IS NULL;

-- Type conversions
ALTER TABLE credit_risk_cleaned
MODIFY COLUMN loan_int_rate DECIMAL(5, 2),
MODIFY COLUMN person_emp_length INT,
MODIFY COLUMN loan_amnt DECIMAL(10, 2),
MODIFY COLUMN person_income DECIMAL(12, 2);

-- =============================================================================================
-- STEP 5: DOMAIN INTEGRITY & LOGICAL ANOMALY REMOVAL
-- Remove biologically and operationally impossible values (age >= 100, employment > 45 years)
-- =============================================================================================

-- Remove records with unrealistic age values (age >= 100)
DELETE FROM credit_risk_cleaned
WHERE person_age >= 100;

-- Remove records where employment duration is logically implausible (> 45 years)
DELETE FROM credit_risk_cleaned
WHERE person_emp_length > 45;

-- Final Verification of Row Count & Hygiene
SELECT 
    COUNT(*) AS total_clean_records,
    ROUND(AVG(loan_status) * 100, 2) AS portfolio_default_rate,
    ROUND(SUM(loan_amnt) / 1000000, 2) AS total_portfolio_volume_millions
FROM credit_risk_cleaned;
