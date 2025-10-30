# AI Talent Navigator 🎯
https://talent-match-intelligence-d7sc9mwbyykssrbshijpha.streamlit.app/

An interactive web application built with **Streamlit** that leverages a dynamic SQL matching engine and **Google's Generative AI** to identify and analyze internal talent.  
This tool empowers HR and hiring managers to make **data-driven decisions** by matching employees against ideal job profiles in real-time.

---

## 🚀 Features

- **Dynamic Job Profiling:** Define a role, level, and purpose to get an AI-generated job profile on the fly.  
- **Benchmark-Based Matching:** Select top-performing employees as a benchmark to create an ideal talent profile.  
- **Ranked Talent List:** Instantly view a ranked list of all employees based on their `final_match_rate`, enriched with top competencies and strengths.  
- **In-Depth Candidate Dashboard:** Explore any candidate’s profile with interactive visualizations:  
  - AI Analyst Summary explaining their fit  
  - Radar Chart comparing competencies vs. benchmark  
  - Bar Chart highlighting strengths and gaps  
  - Histogram showing relative rank  

---

## 🧠 Tech Stack

| Layer | Technology |
|-------|-------------|
| Frontend | Streamlit |
| Data Backend | Supabase (PostgreSQL) |
| Data Analysis | Pandas |
| Generative AI | Google Gemini API |
| Visualization | Plotly |

---

## 📁 Project Structure

```
.
├── .streamlit/
│   └── secrets.toml        # Secret credentials for local development
├── app.py                  # The main Streamlit application script
├── query.sql               # The external SQL matching script
└── requirements.txt        # Python dependencies
```

---

## ⚙️ Setup and Deployment

Follow these instructions to run the application locally or deploy it to the cloud.

### 🧩 Prerequisites
- Python 3.8+  
- Git  
- Supabase and Google Gemini API credentials  

---

### 🖥️ 1. Local Development Setup

**Step 1: Clone the Repository**
```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

**Step 2: Create and Activate a Virtual Environment**
```bash
# For macOS/Linux
python3 -m venv venv
source venv/bin/activate

# For Windows
python -m venv venv
venv\Scripts\activate
```

**Step 3: Install Dependencies**
```bash
pip install -r requirements.txt
```

**Step 4: Add Your Secrets**
Create a folder named `.streamlit` and a file named `secrets.toml` inside it.  
Add your credentials in the following format:

```toml
# Supabase Database Credentials
db_host = "your_supabase_host"
db_name = "postgres"
db_user = "your_supabase_user"
db_password = "your_supabase_password"
db_port = "5432"

# Google Gemini API Key
google_api_key = "your_google_ai_api_key"
```

**Step 5: Run the App**
```bash
streamlit run app.py
```
Your app will open in your browser at **http://localhost:8501**.

---

### ☁️ 2. Deployment to Streamlit Community Cloud

**Step 1: Push Your Code to GitHub**
Ensure your repo with `app.py`, `query.sql`, and `requirements.txt` is pushed to GitHub.

**Step 2: Create a New App in Streamlit Cloud**
- Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
- Click **“New app” → “From existing repo”**.
- Select your repository and ensure **Main file path = app.py**.

**Step 3: Add Your Secrets**
- In Streamlit Cloud, open **Advanced settings → Secrets**.
- Copy your local `secrets.toml` content and paste it there.
- Click **Save**.

**Step 4: Deploy!**
Click **Deploy!** — Streamlit will build and deploy your app.  
Once done, you’ll get a **public URL** to share your deployed AI Talent Navigator.

---
