import streamlit as st
import pandas as pd
import psycopg2
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai

# --- 1. App Configuration ---
st.set_page_config(
    page_title="AI Talent Navigator",
    page_icon="🎯",
    layout="wide"
)

# --- 2. API & State Initialization ---
try:
    genai.configure(api_key=st.secrets["google_api_key"])
except (KeyError, AttributeError):
    st.error("⚠️ Google API Key not found. Please add it to your Streamlit secrets.")
    st.stop()

# Initialize session state to persist data across reruns
if 'analysis_run' not in st.session_state:
    st.session_state.analysis_run = False
if 'main_df' not in st.session_state:
    st.session_state.main_df = pd.DataFrame()
if 'ranked_list' not in st.session_state:
    st.session_state.ranked_list = pd.DataFrame()


# --- 3. Core Functions (with Caching for Performance) ---

@st.cache_resource
def get_db_connection():
    # Connects to the Supabase PostgreSQL database using credentials from secrets.
    try:
        conn = psycopg2.connect(
            host=st.secrets["db_host"],
            database=st.secrets["db_name"],
            user=st.secrets["db_user"],
            password=st.secrets["db_password"],
            port=st.secrets["db_port"]
        )
        return conn
    except psycopg2.OperationalError as e:
        st.error(f"Error connecting to database: {e}")
        st.stop()

@st.cache_data(ttl=600)
def run_talent_query(_conn, benchmark_ids_tuple):
    # Executes the main SQL query to calculate talent match rates.
    sql_query = """
    WITH
        BenchmarkTalent AS (
            SELECT employee_id FROM employees WHERE employee_id IN %s
        ),
        UnifiedTalentData AS (
            SELECT employee_id, 'Cognitive Complexity & Problem-Solving' AS tgv_name, 'Overall IQ Score' AS tv_name, iq AS score_numeric, NULL AS score_categorical, 'higher_is_better' AS scoring_direction, 'profiles_psych' as source FROM profiles_psych WHERE iq IS NOT NULL UNION ALL
            SELECT employee_id, 'Cognitive Complexity & Problem-Solving' AS tgv_name, 'Overall GTQ Score' AS tv_name, gtq, NULL, 'higher_is_better', 'profiles_psych' FROM profiles_psych WHERE gtq IS NOT NULL UNION ALL
            SELECT employee_id, 'Cognitive Complexity & Problem-Solving' AS tgv_name, 'Overall TIKI Score' AS tv_name, tiki, NULL, 'higher_is_better', 'profiles_psych' FROM profiles_psych WHERE tiki IS NOT NULL UNION ALL
            SELECT employee_id, 'Motivation & Drive' AS tgv_name, 'Initial Performance (Pauli)' AS tv_name, pauli, NULL, 'higher_is_better', 'profiles_psych' FROM profiles_psych WHERE pauli IS NOT NULL UNION ALL
            SELECT employee_id, 'Motivation & Drive', 'Drive to complete tasks (Papi_N)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_N' UNION ALL
            SELECT employee_id, 'Motivation & Drive', 'High effort and persistence (Papi_G)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_G' UNION ALL
            SELECT employee_id, 'Motivation & Drive', 'Desire for achievement (Papi_A)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_A' UNION ALL
            SELECT employee_id, 'Leadership & Influence', 'Directness, control (DISC D)', NULL, 'D', 'categorical', 'profiles_psych' FROM profiles_psych WHERE disc = 'D' UNION ALL
            SELECT employee_id, 'Leadership & Influence', 'Tendency to take leadership (Papi_L)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_L' UNION ALL
            SELECT employee_id, 'Leadership & Influence', 'Desire to control others (Papi_P)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_P' UNION ALL
            SELECT employee_id, 'Leadership & Influence', 'MBTI Extraversion', NULL, 'E', 'categorical', 'profiles_psych' FROM profiles_psych WHERE mbti LIKE 'E%%' UNION ALL
            SELECT employee_id, 'Leadership & Influence', 'MBTI Introversion', NULL, 'I', 'categorical', 'profiles_psych' FROM profiles_psych WHERE mbti LIKE 'I%%' UNION ALL
            SELECT employee_id, 'Social Orientation & Collaboration', 'Sociability, persuasion (DISC I)', NULL, 'I', 'categorical', 'profiles_psych' FROM profiles_psych WHERE disc = 'I' UNION ALL
            SELECT employee_id, 'Adaptability & Stress Tolerance', 'Patience, cooperation (DISC S)', NULL, 'S', 'categorical', 'profiles_psych' FROM profiles_psych WHERE disc = 'S' UNION ALL
            SELECT employee_id, 'Conscientiousness & Reliability', 'Accuracy, rule orientation (DISC C)', NULL, 'C', 'categorical', 'profiles_psych' FROM profiles_psych WHERE disc = 'C' UNION ALL
            SELECT employee_id, 'Creativity & Innovation Orientation', 'MBTI Intuition', NULL, 'N', 'categorical', 'profiles_psych' FROM profiles_psych WHERE mbti LIKE '_N%%' UNION ALL
            SELECT employee_id, 'Creativity & Innovation Orientation', 'Drive for variety and novelty (Papi_Z)', score, NULL, 'lower_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_Z' UNION ALL
            SELECT employee_id, 'Adaptability & Stress Tolerance', 'Work speed preference (Papi_T)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_T' UNION ALL
            SELECT employee_id, 'Adaptability & Stress Tolerance', 'Emotional resilience (Papi_E)', score, NULL, 'higher_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_E' UNION ALL
            SELECT employee_id, 'Leadership & Influence', 'Assertive and firm (Papi_K)', score, NULL, 'lower_is_better', 'papi_scores' FROM papi_scores WHERE scale_code = 'Papi_K' UNION ALL
            SELECT employee_id, CASE WHEN theme IN ('Achiever') THEN 'Motivation & Drive' WHEN theme IN ('Arranger', 'Command', 'Self-Assurance', 'Developer') THEN 'Leadership & Influence' WHEN theme IN ('Belief') THEN 'Cultural & Values Urgency' WHEN theme IN ('Deliberative', 'Discipline') THEN 'Conscientiousness & Reliability' WHEN theme IN ('Communication', 'Woo', 'Relator') THEN 'Social Orientation & Collaboration' WHEN theme IN ('Adaptability') THEN 'Adaptability & Stress Tolerance' WHEN theme IN ('Connectedness', 'Analytical', 'Strategic') THEN 'Cognitive Complexity & Problem-Solving' WHEN theme IN ('Futuristic', 'Ideation') THEN 'Creativity & Innovation Orientation' ELSE 'Other Strengths' END AS tgv_name, theme AS tv_name, NULL, theme AS score_categorical, 'categorical', 'strengths' FROM strengths
        ),
        BenchmarkBaseline AS (
            SELECT utd.tgv_name, utd.tv_name, utd.scoring_direction, PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY utd.score_numeric) AS baseline_score_numeric, MODE() WITHIN GROUP (ORDER BY utd.score_categorical) AS baseline_score_categorical FROM UnifiedTalentData utd JOIN BenchmarkTalent bt ON utd.employee_id = bt.employee_id GROUP BY 1, 2, 3
        ),
        TV_MatchRate AS (
            SELECT utd.employee_id, utd.tgv_name, utd.tv_name, utd.source, COALESCE(bb.baseline_score_numeric::TEXT, bb.baseline_score_categorical) AS baseline_score, COALESCE(utd.score_numeric::TEXT, utd.score_categorical) AS user_score, CASE WHEN bb.scoring_direction = 'higher_is_better' AND bb.baseline_score_numeric > 0 THEN LEAST((utd.score_numeric / bb.baseline_score_numeric) * 100, 150.0) WHEN bb.scoring_direction = 'lower_is_better' AND utd.score_numeric IS NOT NULL AND bb.baseline_score_numeric > 0 THEN LEAST(((2 * bb.baseline_score_numeric - utd.score_numeric) / bb.baseline_score_numeric) * 100, 150.0) WHEN bb.scoring_direction = 'categorical' THEN CASE WHEN utd.score_categorical = bb.baseline_score_categorical THEN 100.0 ELSE 0.0 END ELSE 0.0 END AS tv_match_rate FROM UnifiedTalentData utd JOIN BenchmarkBaseline bb ON utd.tgv_name = bb.tgv_name AND utd.tv_name = bb.tv_name
        ),
        TGV_MatchRate AS (
            SELECT employee_id, tgv_name, AVG(tv_match_rate) AS tgv_match_rate FROM TV_MatchRate GROUP BY 1, 2
        ),
        Final_MatchRate AS (
            SELECT employee_id, AVG(tgv_match_rate) AS final_match_rate FROM TGV_MatchRate GROUP BY 1
        )
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
    """
    df = pd.read_sql_query(sql_query, _conn, params=(benchmark_ids_tuple,))
    return df

@st.cache_data
def generate_ai_profile(role_name, job_level, role_purpose):
    # Generates the job profile using the Gemini API. Cached to prevent re-running.
    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Act as a professional HR recruitment specialist. Based on the following job details, generate a concise and structured AI-Generated Job Profile.
    The output must include exactly these three sections (use these headers exactly):
    ### Job requirements
    ### Job description
    ### Key competencies
    Formatting and tone rules:
    - Write in short, specific bullet points or concise sentences (avoid long paragraphs).
    - Use colon-based key-value style for skills (e.g., “SQL expertise: complex joins, window functions, performance tuning basics”).
    - Keep each line direct and professional — avoid verbose sentences.
    - Focus on technical and analytical skills (like SQL, Python/R, BI tools, data modeling, etc.).
    - For Job description, limit to 2–3 concise sentences summarizing the role’s purpose and responsibilities.
    - For Key competencies, list tools and technical proficiencies in a compact format (e.g., “SQL (Postgres/Snowflake/BigQuery), Git, DBT (nice), Airflow (nice)”).
    - The tone must be clear, succinct, and skill-focused (no lengthy prose or generic HR language).
    Job Details:
    - Role Name: {role_name}
    - Job Level: {job_level}
    - Role Purpose: {role_purpose}
    Generate the profile following this exact tone and structure — clear, succinct, and skill-focused (no lengthy prose or generic HR language).
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating AI profile: {e}"

@st.cache_data
def generate_ai_summary(candidate_info_tuple, tgv_scores_tuple, role_name):
    # Generates a candidate summary using the Gemini API. Cached for performance.
    candidate_info = dict(candidate_info_tuple)
    tgv_scores = pd.DataFrame(list(tgv_scores_tuple))

    model = genai.GenerativeModel('gemini-2.5-flash')
    prompt = f"""
    Act as a senior talent analyst. You are given data for a candidate being evaluated for the **{role_name}** role.
    Provide a concise, data-driven summary (2-3 sentences) explaining why this candidate is a strong or weak fit.
    Highlight their key strengths (top TGVs) and potential development areas (bottom TGVs) in relation to the role.
    **Candidate Data:**
    - **Name:** {candidate_info['fullname']}
    - **Final Match Rate:** {candidate_info['final_match_rate']}%
    - **Top 3 Strengths (TGV Scores):** {tgv_scores.head(3).to_dict('records')}
    - **Top 3 Gaps (TGV Scores):** {tgv_scores.tail(3).to_dict('records')}
    Generate the summary now.
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating AI summary: {e}"


# --- 4. User Interface Layout ---
st.title("🎯 AI Talent Navigator")
st.markdown("---")

# Input form for defining the job profile
with st.expander("🔍 Define Job Profile & Find Talent", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        role_name = st.text_input("Role Name", "")
        job_level = st.text_input("Job Level", "")
    with col2:
        benchmark_ids_str = st.text_input("Benchmark Employee IDs (comma-separated)", "")
        
    role_purpose = st.text_area("Role Purpose", "")
    
    analyze_button = st.button("🚀 Analyze", type="primary", use_container_width=True)


# --- 5. Data Processing on Button Click ---
if analyze_button:
    # Validate inputs before proceeding
    if not all([role_name, job_level, role_purpose, benchmark_ids_str]):
        st.warning("Please fill in all the fields to start the analysis.")
    else:
        benchmark_ids = [s.strip() for s in benchmark_ids_str.split(',') if s.strip()]
        if not benchmark_ids:
            st.warning("Please provide at least one valid benchmark employee ID.")
        else:
            benchmark_ids_tuple = tuple(benchmark_ids)
            
            # Run query and store results in session state
            with st.spinner("Connecting to database and running analysis..."):
                conn = get_db_connection()
                st.session_state.main_df = run_talent_query(conn, benchmark_ids_tuple)
                conn.close()
            
            if not st.session_state.main_df.empty:
                st.success("Analysis Complete!")
                st.session_state.analysis_run = True

                # Process and enrich the ranked list
                main_df = st.session_state.main_df
                base_ranked_list = main_df[['employee_id', 'fullname', 'role', 'grade', 'final_match_rate']].drop_duplicates()
                tgv_scores_df = main_df[['employee_id', 'tgv_name', 'tgv_match_rate']].drop_duplicates()
                top_tgv = tgv_scores_df.loc[tgv_scores_df.groupby('employee_id')['tgv_match_rate'].idxmax()]
                top_tgv = top_tgv.rename(columns={'tgv_name': 'top_tgv'}).drop(columns='tgv_match_rate')
                strengths_df = main_df[main_df['source'] == 'strengths'][['employee_id', 'tv_name']].drop_duplicates()
                agg_strengths = strengths_df.groupby('employee_id')['tv_name'].apply(lambda x: ', '.join(x.head(3))).reset_index()
                agg_strengths = agg_strengths.rename(columns={'tv_name': 'top_strengths'})
                ranked_list_final = pd.merge(base_ranked_list, top_tgv, on='employee_id', how='left')
                ranked_list_final = pd.merge(ranked_list_final, agg_strengths, on='employee_id', how='left')
                st.session_state.ranked_list = ranked_list_final.sort_values('final_match_rate', ascending=False).reset_index(drop=True)

            else:
                st.error("No data returned. Please check benchmark IDs and database connection.")
                st.session_state.analysis_run = False


# --- 6. Results Display (persists after analysis is run) ---
if st.session_state.analysis_run and not st.session_state.ranked_list.empty:
    st.markdown("---")
    
    # Retrieve data from session state
    main_df = st.session_state.main_df
    ranked_list = st.session_state.ranked_list

    # Display Section 1: AI Job Profile
    st.header("1. AI Generated Job Profile")
    ai_profile = generate_ai_profile(role_name, job_level, role_purpose)
    st.markdown(ai_profile)
    
    st.markdown("---")

    # Display Section 2: Ranked Talent List
    st.header("2. Ranked Talent List")
    st.dataframe(ranked_list, use_container_width=True)
    
    st.markdown("---")
    
    # Display Section 3: In-Depth Candidate Dashboard
    st.header("3. In-Depth Candidate Dashboard")
    selected_employee_id = st.selectbox(
        "Select a candidate to analyze:",
        options=ranked_list['employee_id'],
        format_func=lambda x: f"{x} - {ranked_list.loc[ranked_list['employee_id'] == x, 'fullname'].iloc[0]}"
    )

    if selected_employee_id:
        candidate_data = main_df[main_df['employee_id'] == selected_employee_id]
        candidate_info = ranked_list[ranked_list['employee_id'] == selected_employee_id].iloc[0]

        # Prepare arguments for cached AI summary function
        candidate_info_tuple = tuple(candidate_info.to_dict().items())
        tgv_scores_df = candidate_data[['tgv_name', 'tgv_match_rate']].drop_duplicates().sort_values('tgv_match_rate', ascending=False)
        tgv_scores_tuple = tuple(map(tuple, tgv_scores_df.to_numpy()))

        ai_summary = generate_ai_summary(candidate_info_tuple, tgv_scores_tuple, role_name)
        st.info(f"**AI Analyst Summary for {candidate_info['fullname']}:**\n\n{ai_summary}")

        # Visualization columns
        vis_col1, vis_col2 = st.columns(2)
        with vis_col1:
            st.subheader("TGV Profile vs. Benchmark")
            candidate_tgv_scores = candidate_data[['tgv_name', 'tgv_match_rate']].drop_duplicates()
            benchmark_ids_list = [s.strip() for s in benchmark_ids_str.split(',') if s.strip()]
            benchmark_tgv_scores = main_df[main_df['employee_id'].isin(benchmark_ids_list)][['tgv_name', 'tgv_match_rate']].groupby('tgv_name')['tgv_match_rate'].mean().reset_index()
            radar_df = pd.merge(candidate_tgv_scores, benchmark_tgv_scores, on='tgv_name', suffixes=('_candidate', '_benchmark'))
            
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(r=radar_df['tgv_match_rate_candidate'], theta=radar_df['tgv_name'], fill='toself', name=f"{candidate_info['fullname']}"))
            fig_radar.add_trace(go.Scatterpolar(r=radar_df['tgv_match_rate_benchmark'], theta=radar_df['tgv_name'], fill='toself', name='Benchmark Avg'))
            fig_radar.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), showlegend=True, height=400, margin=dict(l=40, r=40, t=40, b=40))
            st.plotly_chart(fig_radar, use_container_width=True)

        with vis_col2:
            st.subheader("Strengths & Gaps")
            sorted_scores = candidate_tgv_scores.sort_values('tgv_match_rate', ascending=True)
            fig_bar = px.bar(sorted_scores, x='tgv_match_rate', y='tgv_name', orientation='h', color='tgv_match_rate', color_continuous_scale='RdYlGn', range_color=[0,100])
            fig_bar.update_layout(yaxis_title="", xaxis_title="Match Rate (%)", height=400, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig_bar, use_container_width=True)
        
        st.subheader("Overall Match Rate Distribution")
        fig_hist = px.histogram(ranked_list, x="final_match_rate", nbins=20, title="Distribution Across All Candidates")
        fig_hist.add_vline(x=candidate_info['final_match_rate'], line_width=3, line_dash="dash", line_color="red", annotation_text="Selected Candidate", annotation_position="top left")
        st.plotly_chart(fig_hist, use_container_width=True)