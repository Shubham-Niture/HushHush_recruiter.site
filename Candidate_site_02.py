!pip install openai
import streamlit as st
import pandas as pd
import time
from datetime import datetime
from pathlib import Path
import openai

# Configure theme colors
THEME_COLOR = "#4f0202"
ACCENT_COLOR = "#F4D03F"
BACKGROUND_COLOR = "#595353"

def load_questions():
    BASE_DIR = Path(__file__).resolve().parent
    file_path = BASE_DIR / "AI_ML_Coding_Challenge_Questions.xlsx"

    try:
        df = pd.read_excel(file_path, engine='openpyxl')
        required_columns = ["Question", "Difficulty", "Topics", "Expected Output Example"]
        if not all(col in df.columns for col in required_columns):
            st.error("Missing required columns in the question bank")
            return None
        return df[required_columns].dropna()
    except Exception as e:
        st.error(f"Error loading questions: {str(e)}")
        return None

def initialize_session():
    defaults = {
        'questions': None, 'current_q': 0, 'answers': {},
        'quiz_active': False, 'progress': 0, 'start_time': None,
        'quiz_duration': 60 * 60, 'user_name': "", 'user_id': "",
        'selected_topics': [], 'difficulty': "All Levels"
    }
    for key, val in defaults.items():
        st.session_state.setdefault(key, val)

def select_questions(df, num=15):
    # Difficulty filter
    if st.session_state.difficulty != "All Levels":
        df = df[df["Difficulty"] == st.session_state.difficulty]
    
    # Topic filter
    if st.session_state.selected_topics:
        topic_mask = df["Topics"].apply(
            lambda t: any(topic.strip() in st.session_state.selected_topics 
                     for topic in t.split(',')))  # Fixed syntax error here
        df = df[topic_mask]
    
    return df.sample(min(num, len(df))).reset_index(drop=True)

def start_quiz():
    df = load_questions()
    if df is not None:
        st.session_state.questions = select_questions(df)
        if not st.session_state.questions.empty:
            st.session_state.quiz_active = True
            st.session_state.start_time = time.time()
            st.rerun()

def time_remaining():
    elapsed = time.time() - st.session_state.start_time
    remaining = st.session_state.quiz_duration - elapsed
    return max(0, int(remaining))

def question_navigator():
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("⏮ Previous", disabled=st.session_state.current_q == 0):
            st.session_state.current_q -= 1
    with col2:
        if st.button("Next ⏭", disabled=st.session_state.current_q == len(st.session_state.questions)-1):
            st.session_state.current_q += 1

def save_answer(q_index, answer):
    st.session_state.answers[q_index] = answer
    st.session_state.progress = len(st.session_state.answers) / len(st.session_state.questions) * 100

def submit_quiz():
    st.session_state.quiz_active = False
    try:
        results = {
            "Candidate": [st.session_state.user_name],
            "UserID": [st.session_state.user_id],
            "CompletionTime": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        }
        
        for idx, row in st.session_state.questions.iterrows():
            results[f"Q{idx+1}"] = [row['Question']]
            results[f"Topics"] = [row['Topics']]
            results[f"Difficulty"] = [row['Difficulty']]
            results[f"ExpectedOutput"] = [row['Expected Output Example']]
            results[f"Answer"] = [st.session_state.answers.get(idx, "No response")]
        
        results_dir = Path("TechnicalResults")
        results_dir.mkdir(exist_ok=True)
        filename = results_dir / f"{st.session_state.user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        pd.DataFrame(results).to_excel(filename, index=False)
        
        st.success("✅ Answers submitted successfully! Results saved.")
    except Exception as e:
        st.error(f"Submission error: {str(e)}")

def quiz_interface():
    st.markdown(f"""
    <style>
        .stProgress > div > div {{ background-color: {THEME_COLOR}; }}
        .stTextArea textarea {{ border: 2px solid {THEME_COLOR}; }}
        .stExpander {{ border: 1px solid {THEME_COLOR}; }}
    </style>
    """, unsafe_allow_html=True)

    st.header("💻 Technical Screening Challenge")
    current_q = st.session_state.current_q
    question_data = st.session_state.questions.iloc[current_q]
    
    # Time display
    time_left = time_remaining()
    mins, secs = divmod(time_left, 60)
    time_col, prog_col = st.columns([1, 4])
    with time_col:
        st.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
    with prog_col:
        st.progress(st.session_state.progress/100)
    
    # Question display
    with st.expander(f"Question {current_q+1} of {len(st.session_state.questions)}", expanded=True):
        st.markdown(f"""
        **Difficulty:** {question_data['Difficulty']}  
        **Topics:** {question_data['Topics']}
        """)
        st.markdown(f"#### {question_data['Question']}")
        st.info(f"**Expected Output Format:**\n```\n{question_data['Expected Output Example']}\n```")
        
        answer = st.text_area(
            "Your Solution:", 
            key=f"answer_{current_q}", 
            height=200,
            help="Write your code implementation or detailed explanation here"
        )
        
        if st.button("💾 Save Response", use_container_width=True):
            save_answer(current_q, answer)
    
    question_navigator()
    
    if st.button("🏁 Final Submission", type="primary", use_container_width=True):
        submit_quiz()

def main():
    st.set_page_config(
        page_title="Hush Hush Recruiter", 
        page_icon="💻", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    initialize_session()
    
    if not st.session_state.quiz_active:
        st.markdown(f"""
        <div style='padding:2rem; border-radius:15px; background:{BACKGROUND_COLOR};'>
            <h1 style='color:{THEME_COLOR};'>Hush Hush Recruiter</h1>
            <h3 style='color:{ACCENT_COLOR};'>Technical Assessment Platform</h3>
            <p>Features:</p>
            <ul>
                <li>🔍 Topic-focused questions (Algorithms, ML, Systems)</li>
                <li>⚖️ Difficulty levels from Beginner to Expert</li>
                <li>⏳ 60-minute time limit</li>
                <li>📝 Code and theory questions</li>
                <li>📤 Automatic result archiving</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        with st.form("candidate_info"):
            st.session_state.user_name = st.text_input("Candidate Name")
            st.session_state.user_id = st.text_input("Unique Candidate ID")
            
            df = load_questions()
            if df is not None:
                # Topic selection
                all_topics = set()
                for topics in df['Topics']:
                    for topic in topics.split(','):
                        all_topics.add(topic.strip())
                
                st.session_state.selected_topics = st.multiselect(
                    "Select assessment topics:",
                    options=sorted(all_topics),
                    help="Select at least one topic for question filtering"
                )
                
                # Difficulty selection
                difficulties = ["All Levels"] + sorted(df['Difficulty'].unique())
                st.session_state.difficulty = st.selectbox(
                    "Select difficulty level:",
                    options=difficulties
                )
            
            if st.form_submit_button("🚀 Start Assessment", use_container_width=True):
                if st.session_state.user_name and st.session_state.user_id:
                    start_quiz()
                else:
                    st.error("Please provide both name and candidate ID")
    
    else:
        quiz_interface()

if __name__ == "__main__":
    main()
