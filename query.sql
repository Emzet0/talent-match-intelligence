-- # FINAL SCRIPT: TALENT MATCHING ENGINE

WITH
    -- Step 1: Define the Benchmark Profile
    -- This CTE selects the group of "ideal" employees who will serve as the benchmark.
    -- Their combined profile will be used as the standard for comparison.
    BenchmarkTalent AS (
        SELECT
            employee_id
        FROM
            employees
        WHERE
            employee_id IN %s -- This placeholder will be filled by the Python script
    ),

    -- Step 2: Unify All Talent Data
    -- This CTE gathers raw data from multiple source tables (profiles_psych, papi_scores, strengths)
    -- and transforms it into a standardized, long-format table. Each row represents a single
    -- Talent Variable (TV) for an employee, mapped to its corresponding Talent Group Variable (TGV).
    UnifiedTalentData AS (
        -- Cognitive Complexity & Problem-Solving from profiles_psych
        SELECT employee_id, 'Cognitive Complexity & Problem-Solving' AS tgv_name, 'Overall IQ Score' AS tv_name, iq AS score_numeric, NULL AS score_categorical, 'higher_is_better' AS scoring_direction, 'profiles_psych' as source FROM profiles_psych WHERE iq IS NOT NULL
        UNION ALL
        SELECT employee_id, 'Cognitive Complexity & Problem-Solving' AS tgv_name, 'Overall GTQ Score' AS tv_name, gtq, NULL, 'higher_is_better', 'profiles_psych' FROM profiles_psych WHERE gtq IS NOT NULL
        UNION ALL
        SELECT employee_id, 'Cognitive Complexity & Problem-Solving' AS tgv_name, 'Overall TIKI Score' AS tv_name, tiki, NULL, 'higher_is_better', 'profiles_psych' FROM profiles_psych WHERE tiki IS NOT NULL
        UNION ALL
        -- Motivation & Drive from profiles_psych & papi_scores
        SELECT employee_id, 'Motivation & Drive' AS tgv_name, 'Initial Performance (Pauli)' AS tv_name, pauli, NULL, 'higher_is_better', 'profiles_psych' FROM profiles_psych WHERE pauli IS NOT NULL
        UNION ALL
        SELECT employee_id, 'Motivation & Drive', 'Drive to complete tasks (Papi_N)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_N'
        UNION ALL
        SELECT employee_id, 'Motivation & Drive', 'High effort and persistence (Papi_G)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_G'
        UNION ALL
        SELECT employee_id, 'Motivation & Drive', 'Desire for achievement (Papi_A)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_A'
        UNION ALL
        -- Leadership & Influence from profiles_psych & papi_scores
        SELECT employee_id, 'Leadership & Influence', 'Directness, control (DISC D)', NULL, 'D', 'categorical', 'profiles_psych' FROM profiles_psych WHERE disc = 'D'
        UNION ALL
        SELECT employee_id, 'Leadership & Influence', 'Tendency to take leadership (Papi_L)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_L'
        UNION ALL
        SELECT employee_id, 'Leadership & Influence', 'Desire to control others (Papi_P)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_P'
        UNION ALL
        SELECT employee_id, 'Leadership & Influence', 'MBTI Extraversion', NULL, 'E', 'categorical', 'profiles_psych' FROM profiles_psych WHERE mbti LIKE 'E%%'
        UNION ALL
        SELECT employee_id, 'Leadership & Influence', 'MBTI Introversion', NULL, 'I', 'categorical', 'profiles_psych' FROM profiles_psych WHERE mbti LIKE 'I%%'
        UNION ALL
        -- Other TGVs from PAPI, DISC, MBTI
        SELECT employee_id, 'Social Orientation & Collaboration', 'Sociability, persuasion (DISC I)', NULL, 'I', 'categorical', 'profiles_psych' FROM profiles_psych WHERE disc = 'I'
        UNION ALL
        SELECT employee_id, 'Adaptability & Stress Tolerance', 'Patience, cooperation (DISC S)', NULL, 'S', 'categorical', 'profiles_psych' FROM profiles_psych WHERE disc = 'S'
        UNION ALL
        SELECT employee_id, 'Conscientiousness & Reliability', 'Accuracy, rule orientation (DISC C)', NULL, 'C', 'categorical', 'profiles_psych' FROM profiles_psych WHERE disc = 'C'
        UNION ALL
        SELECT employee_id, 'Creativity & Innovation Orientation', 'MBTI Intuition', NULL, 'N', 'categorical', 'profiles_psych' FROM profiles_psych WHERE mbti LIKE '_N%%'
        UNION ALL
        SELECT employee_id, 'Creativity & Innovation Orientation', 'Drive for variety and novelty (Papi_Z)', score, NULL, 'lower_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_Z'
        UNION ALL
        SELECT employee_id, 'Adaptability & Stress Tolerance', 'Work speed preference (Papi_T)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_T'
        UNION ALL
        SELECT employee_id, 'Adaptability & Stress Tolerance', 'Emotional resilience (Papi_E)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_E'
        UNION ALL
        SELECT employee_id, 'Leadership & Influence', 'Assertive and firm (Papi_K)', score, NULL, 'lower_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_K'
        UNION ALL
        -- CliftonStrengths (Categorical) mapped to TGVs
        SELECT
            employee_id,
            CASE
                WHEN theme IN ('Achiever') THEN 'Motivation & Drive'
                WHEN theme IN ('Arranger', 'Command', 'Self-Assurance', 'Developer') THEN 'Leadership & Influence'
                WHEN theme IN ('Belief') THEN 'Cultural & Values Urgency'
                WHEN theme IN ('Deliberative', 'Discipline') THEN 'Conscientiousness & Reliability'
                WHEN theme IN ('Communication', 'Woo', 'Relator') THEN 'Social Orientation & Collaboration'
                WHEN theme IN ('Adaptability') THEN 'Adaptability & Stress Tolerance'
                WHEN theme IN ('Connectedness', 'Analytical', 'Strategic') THEN 'Cognitive Complexity & Problem-Solving'
                WHEN theme IN ('Futuristic', 'Ideation') THEN 'Creativity & Innovation Orientation'
                ELSE 'Other Strengths'
            END AS tgv_name,
            theme AS tv_name,
            NULL,
            theme AS score_categorical,
            'categorical',
            'strengths'
        FROM strengths
    ),

    -- Step 3: Calculate the Benchmark Baseline
    -- This CTE computes the "ideal score" for each TV by aggregating the data from the
    -- benchmark employees. It uses the MEDIAN for numeric scores and the MODE for categorical traits.
    BenchmarkBaseline AS (
        SELECT
            utd.tgv_name,
            utd.tv_name,
            utd.scoring_direction,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY utd.score_numeric) AS baseline_score_numeric,
            MODE() WITHIN GROUP (ORDER BY utd.score_categorical) AS baseline_score_categorical
        FROM UnifiedTalentData utd
        JOIN BenchmarkTalent bt ON utd.employee_id = bt.employee_id
        GROUP BY 1, 2, 3
    ),

    -- Step 4: Calculate TV (Talent Variable) Match Rate
    -- This is the core calculation engine. It compares every employee's score against the baseline
    -- to generate a percentage match rate for each individual TV. It handles different scoring
    -- directions ('higher_is_better', 'lower_is_better', 'categorical').
    TV_MatchRate AS (
        SELECT
            utd.employee_id,
            utd.tgv_name,
            utd.tv_name,
            utd.source,
            COALESCE(bb.baseline_score_numeric::TEXT, bb.baseline_score_categorical) AS baseline_score,
            COALESCE(utd.score_numeric::TEXT, utd.score_categorical) AS user_score,
            CASE
                WHEN bb.scoring_direction = 'higher_is_better' AND bb.baseline_score_numeric > 0 THEN LEAST((utd.score_numeric / bb.baseline_score_numeric) * 100, 150.0)
                WHEN bb.scoring_direction = 'lower_is_better' AND utd.score_numeric IS NOT NULL AND bb.baseline_score_numeric > 0 THEN LEAST(((2 * bb.baseline_score_numeric - utd.score_numeric) / bb.baseline_score_numeric) * 100, 150.0)
                WHEN bb.scoring_direction = 'categorical' THEN CASE WHEN utd.score_categorical = bb.baseline_score_categorical THEN 100.0 ELSE 0.0 END
                ELSE 0.0
            END AS tv_match_rate
        FROM UnifiedTalentData utd
        JOIN BenchmarkBaseline bb ON utd.tgv_name = bb.tgv_name AND utd.tv_name = bb.tv_name
    ),

    -- Step 5: Aggregate to TGV (Talent Group Variable) Match Rate
    -- This CTE rolls up the individual TV match rates into their parent TGV categories by
    -- calculating the average match rate for each group per employee.
    TGV_MatchRate AS (
        SELECT employee_id, tgv_name, AVG(tv_match_rate) AS tgv_match_rate FROM TV_MatchRate GROUP BY 1, 2
    ),

    -- Step 6: Calculate the Final Match Rate
    -- This CTE performs the final aggregation, calculating a single, overall match score
    -- for each employee by averaging their TGV match rates.
    Final_MatchRate AS (
        SELECT employee_id, AVG(tgv_match_rate) AS final_match_rate FROM TGV_MatchRate GROUP BY 1
    )

-- Step 7: Assemble the Final Output
-- The final SELECT statement joins the calculated scores (TV, TGV, and Final rates) with
-- employee dimension data (name, role, etc.) to create a comprehensive output table.
-- The results are ordered by the final_match_rate to surface the top candidates.
SELECT
    e.employee_id, e.fullname, ddir.name AS directorate, dpos.name AS role, dgra.name AS grade,
    tvm.tgv_name, tvm.tv_name, tvm.source, tvm.baseline_score, tvm.user_score,
    ROUND(CAST(tvm.tv_match_rate AS numeric), 2) AS tv_match_rate,
    ROUND(CAST(tgvm.tgv_match_rate AS numeric), 2) AS tgv_match_rate,
    ROUND(CAST(fm.final_match_rate AS numeric), 2) AS final_match_rate
FROM
    TV_MatchRate tvm
    JOIN employees e ON tvm.employee_id = e.employee_id
    JOIN TGV_MatchRate tgvm ON tvm.employee_id = tgvm.employee_id AND tvm.tgv_name = tgvm.tgv_name
    JOIN Final_MatchRate fm ON tvm.employee_id = fm.employee_id
    LEFT JOIN dim_directorates ddir ON e.directorate_id = ddir.directorate_id
    LEFT JOIN dim_positions dpos ON e.position_id = dpos.position_id
    LEFT JOIN dim_grades dgra ON e.grade_id = dgra.grade_id;