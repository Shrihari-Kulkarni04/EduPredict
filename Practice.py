from dotenv import load_dotenv
import base64
import html
import os
load_dotenv()
from datetime import datetime, UTC
import streamlit as st
from pymongo import MongoClient
import bcrypt
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# Set page config at the beginning
st.set_page_config(page_title="EduPredict", layout="wide")

# MongoDB Connection
import os
client = MongoClient(os.getenv("MONGO_URI"))
print("MONGO_URI =", os.getenv("MONGO_URI"))
db = client["education_system"]

users_collection = db["users"]

users_collection.create_index(
  [("createdAt", 1)],
   expireAfterSeconds=1728000,
  name="ttl_20_days"
)

GRADE_OPTIONS = ["6", "7", "8", "9", "10", "11 Science", "11 Commerce", "12 Science", "12 Commerce"]
MAX_PROFILE_IMAGE_BYTES = 1_000_000
ALLOWED_PROFILE_IMAGE_TYPES = {"image/png", "image/jpeg", "image/jpg", "image/webp"}

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )

# ADD HERE

import re

def validate_password(password):

    if len(password) < 8:
        return "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return "Password must contain at least one lowercase letter."

    if not re.search(r"[0-9]", password):
        return "Password must contain at least one number."

    return None

import re

def validate_username(username):

    username = username.strip()

    if len(username) < 4:
        return "Username must be at least 4 characters long."

    if len(username) > 20:
        return "Username cannot exceed 20 characters."

    if " " in username:
        return "Username cannot contain spaces."

    if not re.match(r"^[A-Za-z0-9_]+$", username):
        return "Username can only contain letters, numbers, and underscore (_)."

    return None

# Apply styling
st.markdown(
    """
    <style>
        body {
            background: linear-gradient(135deg, #121212, #2c2c2c) !important;
        }
        .login-box {
            background-color: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            box-shadow: 0px 4px 10px rgba(255, 255, 255, 0.2);
        }
        input::placeholder {
            color: black !important;
        }
        .stButton>button {
            background-color: black !important;
            color: white !important;
            border-radius: 5px !important;
            font-weight: bold !important;
        }
        .nav-button {
            background-color: #2c2c2c;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            margin: 5px;
            text-decoration: none;
            display: inline-block;
        }
        .nav-button:hover {
            background-color: #404040;
        }
        .nav-container {
            display: flex;
            align-items: center;
            justify-content: center;
            background: rgba(0, 0, 0, 0.2);
            margin-bottom: 20px;
        }
        .site-name {
            flex: 1;
            font-size: 24px;
            font-weight: bold;
            color: black;
            text-align: center;
        }
        .profile-summary {
            display: flex;
            gap: 12px;
            align-items: center;
            padding: 8px 0 12px;
        }
        .profile-summary img {
            width: 72px;
            height: 72px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #111111;
        }
        .profile-summary strong {
            display: block;
            font-size: 18px;
        }
        .profile-summary span {
            color: #555555;
            font-size: 14px;
        }

        .welcome-section {
            padding: 20px;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .book-card {
            background: rgba(255, 255, 255, 0.1);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
    </style>
    """,
    unsafe_allow_html=True
)

def get_user_initials(user):
    if not user:
        return "U"

    display_name = user.get("full_name") or user.get("username") or "User"
    name_parts = display_name.split()
    if not name_parts:
        return "U"
    if len(name_parts) == 1:
        return name_parts[0][:2].upper()
    return "".join(part[0].upper() for part in name_parts[:2])

def build_default_avatar(initials):
    safe_initials = html.escape(initials[:2] or "U")
    svg = f"""
        <svg xmlns="http://www.w3.org/2000/svg" width="160" height="160" viewBox="0 0 160 160">
            <rect width="160" height="160" rx="80" fill="#111111"/>
            <circle cx="118" cy="38" r="28" fill="#4CAF50" opacity="0.92"/>
            <circle cx="40" cy="120" r="34" fill="#2d7ff9" opacity="0.9"/>
            <text x="80" y="94" text-anchor="middle" font-family="Arial, sans-serif"
                  font-size="54" font-weight="700" fill="#ffffff">{safe_initials}</text>
        </svg>
    """
    encoded_svg = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded_svg}"

def get_profile_picture_src(user):
    if user and user.get("profile_pic"):
        return user["profile_pic"]
    return build_default_avatar(get_user_initials(user))

def get_grade_options(current_grade):
    options = GRADE_OPTIONS.copy()
    if current_grade and current_grade not in options:
        options.append(current_grade)
    return options

def image_to_data_uri(uploaded_file):
    if uploaded_file is None:
        return None

    image_bytes = uploaded_file.getvalue()
    image_type = uploaded_file.type or ""
    if image_type not in ALLOWED_PROFILE_IMAGE_TYPES:
        st.error("Please upload a PNG, JPG, JPEG, or WEBP profile picture.")
        return None
    if len(image_bytes) > MAX_PROFILE_IMAGE_BYTES:
        st.error("Please upload a profile picture smaller than 1 MB.")
        return None

    encoded_image = base64.b64encode(image_bytes).decode("ascii")
    return f"data:{image_type};base64,{encoded_image}"


def show_username_taken_modal(username):
    # Simple non-modal notification to avoid compatibility issues across Streamlit versions
    st.error(f"The username '{username}' is already taken. Please choose another one.")

def save_profile_changes(current_user, full_name, class_grade, new_username, uploaded_file, remove_profile_pic):
    current_username = current_user.get("username", "")
    clean_full_name = full_name.strip()
    clean_username = new_username.strip()

    if not clean_full_name:
        st.error("Name cannot be empty.")
        return
    if not clean_username:
        st.error("Username cannot be empty.")
        return

    if clean_username != current_username and users_collection.find_one({"username": clean_username}):
        show_username_taken_modal(clean_username)
        return

    profile_pic = image_to_data_uri(uploaded_file)
    if uploaded_file is not None and profile_pic is None:
        return

    update_payload = {
        "$set": {
            "full_name": clean_full_name, 
            "class_grade": class_grade,
            "username": clean_username,
        }
    }

    if profile_pic:
        update_payload["$set"]["profile_pic"] = profile_pic
    elif remove_profile_pic:
        update_payload["$unset"] = {"profile_pic": ""}

    result = users_collection.update_one({"username": current_username}, update_payload)
    if result.matched_count == 0:
        st.error("Could not find your profile to update.")
        return

    updated_user = users_collection.find_one(
        {"username": clean_username}
    )
    st.session_state["user"] = updated_user
    if class_grade != current_user.get("class_grade"):
        st.session_state.pop("predictions", None)
        st.session_state.pop("last_scores_state", None)

    updated_user = users_collection.find_one(
        {"username": clean_username}
    )

    st.session_state["user"] = updated_user
    st.session_state["profile_update_success"] = True
    st.rerun()

def render_profile_editor(user):
    if not user:
        st.error("User profile could not be loaded.")
        return

    if st.session_state.pop("profile_update_success", False):
        st.success("Profile updated successfully.")

    profile_src = html.escape(get_profile_picture_src(user), quote=True)
    safe_name = html.escape(user.get("full_name", "User"))
    safe_username = html.escape(user.get("username", ""))
    safe_class = html.escape(user.get("class_grade", ""))

    st.markdown(
        f"""
        <div class="profile-summary">
            <img src="{profile_src}" alt="Profile picture">
            <div>
                <strong>{safe_name}</strong>
                <span>Class {safe_class} | @{safe_username}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    grade_options = get_grade_options(user.get("class_grade", ""))
    current_grade_index = grade_options.index(user.get("class_grade", "")) if user.get("class_grade", "") in grade_options else 0

    with st.form("profile_edit_form"):

        full_name = st.text_input(
            "Name",
            value=user.get("full_name", ""),
            key="profile_full_name"
        )

        class_grade = st.selectbox(
            "Class",
            grade_options,
            index=current_grade_index,
            key="profile_class"
        )

        new_username = st.text_input(
            "Username",
            value=user.get("username", ""),
            key="profile_username"
        )

        uploaded_file = st.file_uploader(
            "Profile picture",
            type=["png", "jpg", "jpeg", "webp"],
            key="profile_picture_upload"
        )

        remove_profile_pic = st.checkbox(
            "Remove current profile picture",
            value=False,
            disabled=not user.get("profile_pic"),
            key="remove_profile_picture"
        )

        submitted = st.form_submit_button("Save Profile")
        
    if submitted:
        save_profile_changes(user, full_name, class_grade, new_username, uploaded_file, remove_profile_pic)

    st.markdown("<hr>", unsafe_allow_html=True)
    # Move Logout into the profile settings panel
    if st.button("Logout", key="profile_logout"):
        st.session_state["page"] = "login"
        st.session_state.pop("current_page", None)
        st.session_state.pop("marks_displayed", None)
        st.session_state.pop("show_profile_editor", None)
        st.session_state.pop("username", None)
        st.rerun()

def create_navigation():

    user = st.session_state.get("user")

    col_title, col_profile = st.columns([9,1])

    with col_title:
        st.image("assets/edupredict_icon.png", width=80)

    with col_profile:

        st.markdown("", unsafe_allow_html=True)
        profile_src = get_profile_picture_src(user)
        css_profile_src = profile_src.replace("\\", "\\\\").replace('"', '\\"')

        # Ensure session state flags exist
        if "show_profile_menu" not in st.session_state:
            st.session_state["show_profile_menu"] = False

        # image button for profile menu
        st.markdown(
            f"""
            <style>
            .st-key-profile_avatar_btn {{
                display: flex;
                justify-content: flex-end;
            }}
            .st-key-profile_avatar_btn button {{
                width: 55px !important;
                min-width: 55px !important;
                height: 55px !important;
                padding: 0 !important;
                border-radius: 50% !important;
                border: 2px solid #ddd !important;
                background-image: url("{css_profile_src}") !important;
                background-position: center !important;
                background-size: cover !important;
                cursor: pointer !important;
            }}
            .st-key-profile_avatar_btn button p {{
                font-size: 0 !important;
            }}
            </style>
            """,
            unsafe_allow_html=True
        )

        if st.button("", key="profile_avatar_btn", help="Open profile menu"):

            if st.session_state.get("show_profile_editor", False):
                st.session_state["show_profile_editor"] = False
                st.session_state["show_profile_menu"] = False

            else:
                st.session_state["show_profile_menu"] = not st.session_state.get(
                    "show_profile_menu", False
                )

            st.rerun()

        # Render dropdown overlay card when menu is shown
        if st.session_state.get("show_profile_menu"):

            st.markdown("---")

            if st.button("✏️ Edit Profile", key="edit_profile_btn"):
                st.session_state["show_profile_editor"] = True
                st.session_state["show_profile_menu"] = False
                st.rerun()

            if st.button("Logout", key="profile_logout"):
                st.session_state.clear()
                st.session_state["page"] = "login"
                st.rerun()
                
    st.markdown("<br>", unsafe_allow_html=True)
    # Add spacer columns between the four main nav buttons to increase horizontal gaps
    left_space, col1, gap1, col2, gap2, col3, gap3, col4, right_space = st.columns(
        [2, 3, 1.5, 3, 1.5, 3, 1.5, 3, 2]
    )
    with col1:
        if st.button("Performance History", key="nav_performance"):
            st.session_state["current_page"] = "performance"
            st.rerun()
    with col2:
        if st.button("Study Material", key="nav_study"):
            st.session_state["current_page"] = "study"
            st.rerun()
    with col3:
        if st.button("Predict Score", key="nav_predictor"):
            st.session_state["current_page"] = "predictor"
            st.rerun()
    with col4:
        if st.button("Analytics Dashboard", key="nav_analytics"):
            st.session_state["current_page"] = "analytics"
            st.rerun()

def display_dashboard(username):
    
    user = st.session_state.get("user")

    if not user:
        st.error("User not found!")
        return

    # Welcome Section
    st.markdown(f"""
        <div class='welcome-section'>
            <h1>Welcome, {user['full_name']}! 👋</h1>
            <h2>Class: {user['class_grade']}</h2>
            <br />
            <h1>"The Secret of getting Ahead is getting Started ~ Mark Twain"</h1>
        </div>
    """, unsafe_allow_html=True)

def create_marks_bar_graph(subject_scores):
    # Create a bar graph using plotly
    fig = go.Figure()
    
    # Define colors for different entries
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green
    
    # Process each subject
    for subject, scores in subject_scores.items():
        # Get only the last 3 entries
        recent_scores = scores[-3:] if len(scores) >= 3 else scores
        
        # Add bars for each score entry
        for i, score in enumerate(recent_scores):
            entry_number = len(scores) - len(recent_scores) + i + 1
            fig.add_trace(go.Bar(
                name=f"Entry {entry_number}",
                x=[subject],
                y=[score],
                text=[f"{score:.1f}"],
                textposition='auto',
                marker_color=colors[i % len(colors)],
                showlegend=True,
                legendgroup=f"Entry {entry_number}",
                hovertemplate=f"{subject}<br>Entry {entry_number}: {score:.1f}<extra></extra>"
            ))
    
    # Update layout
    fig.update_layout(
        title={
            'text': "Last 3 Marks Entries per Subject",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {'size': 24}
        },
        xaxis_title="Subjects",
        yaxis_title="Marks (out of 100)",
        yaxis=dict(
            range=[0, 100],
            tickmode='linear',
            tick0=0,
            dtick=10,
            gridcolor='rgba(200, 200, 200, 0.2)'
        ),
        barmode='group',
        bargap=0.0005,
        bargroupgap=0.05,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        showlegend=True,
        legend_title_text="Mark Entries",
        height=500,
        margin=dict(t=1, b=5, l=5, r=5)
    )
    
    # Update axes lines
    fig.update_xaxes(showline=True, linewidth=2, linecolor='black', gridcolor='rgba(200, 200, 200, 0.2)')
    fig.update_yaxes(showline=True, linewidth=2, linecolor='black', gridcolor='rgba(200, 200, 200, 0.2)')
    
    return fig

from sklearn.linear_model import LinearRegression

def train_and_predict(subject_scores):
    predictions = {}

    for subject, scores in subject_scores.items():

        if len(scores) < 2:
            predictions[subject] = "Not enough data to make a prediction."
            continue

        mean_score = sum(scores) / len(scores)

        X = np.array(range(len(scores))).reshape(-1, 1)
        y = np.array(scores)

        model = LinearRegression()
        model.fit(X, y)

        next_index = np.array([[len(scores)]])
        predicted_score = float(model.predict(next_index)[0])

        final_prediction = max(min(predicted_score, 95), mean_score)

        predictions[subject] = round(final_prediction, 2)

    return predictions

# Add function to save scores to MongoDB
def save_scores_to_mongodb(username, subject_scores):
    users_collection.update_one(
        {"username": username},
        {"$set": {"subject_scores": subject_scores}},
        upsert=True
    )

# Add function to load scores from MongoDB
def load_scores_from_mongodb(username):
    user = users_collection.find_one({"username": username})
    if user and "subject_scores" in user:
        return user["subject_scores"]
    return {}

def get_subjects_for_grade(class_grade):
    if class_grade in ["6", "7", "8", "9", "10"]:
        return ["Hindi", "Social Science", "English", "Science", "Maths"]
    elif class_grade in ["11 Science", "12 Science"]:
        return ["Chemistry", "Physics", "English", "Computer Science", "Maths/Biology"]
    elif class_grade in ["11 Commerce", "12 Commerce"]:
        return ["Business Studies", "Accountancy", "Economics", "Information Technology", "Maths"]
    else:
        return []


def compute_analytics(subject_scores):
    # Flatten all scores and compute metrics
    if not subject_scores:
        return None

    subject_averages = {}
    all_scores = []
    for subject, scores in subject_scores.items():
        if scores and len(scores) > 0:
            avg = sum(scores) / len(scores)
            subject_averages[subject] = round(avg, 2)
            all_scores.extend(scores)
        else:
            subject_averages[subject] = 0.0

    if not all_scores:
        return None

    average_score = round(sum(all_scores) / len(all_scores), 2)
    strongest_subject = max(subject_averages, key=lambda s: subject_averages[s])
    weakest_subject = min(subject_averages, key=lambda s: subject_averages[s])
    total_subjects = len(subject_averages)
    highest_score = max(all_scores)
    lowest_score = min(all_scores)
    subjects_needing_improvement = [s for s, a in subject_averages.items() if a < 75]

    return {
        "average_score": average_score,
        "strongest_subject": strongest_subject,
        "weakest_subject": weakest_subject,
        "total_subjects": total_subjects,
        "highest_score": highest_score,
        "lowest_score": lowest_score,
        "subject_averages": subject_averages,
        "subjects_needing_improvement": subjects_needing_improvement,
    }


def build_subject_avg_bar_chart(subject_averages):
    subjects = list(subject_averages.keys())
    averages = [subject_averages[s] for s in subjects]
    fig = go.Figure(go.Bar(x=subjects, y=averages, marker_color='rgb(55, 83, 109)'))
    fig.update_layout(
        title_text='Subject-wise Average Score',
        xaxis_title='Subjects',
        yaxis_title='Average Score',
        yaxis=dict(range=[0, 100]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def build_performance_trend_line_chart(subject_scores):
    fig = go.Figure()
    for subject, scores in subject_scores.items():
        if scores:
            x = list(range(1, len(scores) + 1))
            fig.add_trace(go.Scatter(x=x, y=scores, mode='lines+markers', name=subject))
    fig.update_layout(
        title_text='Performance Trend by Entry (per Subject)',
        xaxis_title='Entry Number',
        yaxis_title='Score',
        yaxis=dict(range=[0, 100]),
        legend_title='Subject',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def build_score_distribution_pie_chart(subject_averages):
    labels = list(subject_averages.keys())
    values = [max(0.01, v) for v in subject_averages.values()]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.35))
    fig.update_layout(title_text='Score Distribution (by Subject Average)', paper_bgcolor='rgba(0,0,0,0)')
    return fig


def render_analytics_page(subject_scores):
    analytics = compute_analytics(subject_scores)
    if analytics is None:
        st.info("No performance data available.")
        return

    # Top row KPI Cards

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f"""
        <div style="
            background:white;
            padding:20px;
            border-radius:15px;
            text-align:center;
            box-shadow:0 4px 12px rgba(0,0,0,0.08);
            border:1px solid #e5e7eb;
        ">
            <h4>📈 Average Score</h4>
            <h2>{analytics['average_score']}</h2>
        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div style="
            background:white;
            padding:20px;
            border-radius:15px;
            text-align:center;
            box-shadow:0 4px 12px rgba(0,0,0,0.08);
            border:1px solid #e5e7eb;
        ">
            <h4>🏆 Strongest Subject</h4>
            <h2>{analytics['strongest_subject']}</h2>
        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div style="
            background:white;
            padding:20px;
            border-radius:15px;
            text-align:center;
            box-shadow:0 4px 12px rgba(0,0,0,0.08);
            border:1px solid #e5e7eb;
        ">
            <h4>⚠️ Weakest Subject</h4>
            <h2>{analytics['weakest_subject']}</h2>
        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div style="
            background:white;
            padding:20px;
            border-radius:15px;
            text-align:center;
            box-shadow:0 4px 12px rgba(0,0,0,0.08);
            border:1px solid #e5e7eb;
        ">
            <h4>📚 Total Subjects</h4>
            <h2>{analytics['total_subjects']}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Middle row charts
    c1, c2 = st.columns([2, 3])
    with c1:
        fig_bar = build_subject_avg_bar_chart(analytics['subject_averages'])
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        fig_line = build_performance_trend_line_chart(subject_scores)
        st.plotly_chart(fig_line, use_container_width=True)

    # Bottom row insights and pie chart
    b1, b2 = st.columns([3, 2])
    with b1:
        st.subheader("Insights")
        st.write(f"**Highest Score Achieved:** {analytics['highest_score']}")
        st.write(f"**Lowest Score Achieved:** {analytics['lowest_score']}")
        st.write(f"**Strongest Subject:** {analytics['strongest_subject']}")
        st.write(f"**Weakest Subject:** {analytics['weakest_subject']}")
        if analytics['subjects_needing_improvement']:
            st.warning("Subjects Needing Improvement (avg < 75): " + ", ".join(analytics['subjects_needing_improvement']))
        else:
            st.success("No subjects need immediate improvement (all averages >= 75).")
    with b2:
        fig_pie = build_score_distribution_pie_chart(analytics['subject_averages'])
        st.plotly_chart(fig_pie, use_container_width=True)


def display_dashboard_page():
    
    user = st.session_state.get("user")

    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "dashboard"

    # Create navigation
    create_navigation()
    
    st.markdown("<hr>", unsafe_allow_html=True)

    if st.session_state.get("show_profile_editor", False):
        render_profile_editor(st.session_state.get("user"))
        st.markdown("<hr>", unsafe_allow_html=True)

    # Load scores from MongoDB when initializing
    if "subject_scores" not in st.session_state:
        st.session_state["subject_scores"] = load_scores_from_mongodb(st.session_state.get("username", ""))

    # Display current page content
    if st.session_state["current_page"] == "dashboard":
        display_dashboard(st.session_state.get("username", ""))
    elif st.session_state["current_page"] == "performance":
        st.title("Performance History")
       
        all_scores = {
            subject: sum(scores) / len(scores)
            for subject, scores in st.session_state.get("subject_scores", {}).items()
            if scores
        }

        if all_scores:

            st.markdown(f"""
            ### 👋 Welcome Back, {user['full_name']}!
            Track your academic progress and identify areas for improvement.
            """)

            best_subject = max(all_scores, key=all_scores.get)
            weak_subject = min(all_scores, key=all_scores.get)
            avg_score = round(sum(all_scores.values()) / len(all_scores), 2)

            col1, col2, col3 = st.columns(3)

            with col1:
                st.success(f"🏆 Strongest Subject: {best_subject}")

            with col2:
                st.warning(f"⚠️ Focus Area: {weak_subject}")

            with col3:
                st.info(f"📈 Average Score: {avg_score}")

        else:

            st.markdown(f"""
            ### 🌟 Welcome to EduPredict, {user['full_name']}!

            We're excited to have you here.

            📚 Add your first scores to unlock:
            • Performance Tracking
            • AI Predictions
            • Analytics Dashboard

            🚀 Start by clicking **Add Score** below.
            """)
            
        # Get user's class grade
        user = st.session_state.get("user")

        if user:
            class_grade = user.get("class_grade", "")
            subjects = get_subjects_for_grade(class_grade)

            # Display the bar chart with recent entries if scores exist
            if st.session_state["subject_scores"]:
                st.subheader("Recent Performance")
                fig = create_marks_bar_graph(st.session_state["subject_scores"])
                st.plotly_chart(fig, use_container_width=True)

                # Display the numerical data
                st.subheader("Score History")
                for subject, scores in st.session_state["subject_scores"].items():
                    recent_scores = scores[-3:] if len(scores) >= 3 else scores
                    st.write(f"{subject}: {', '.join(map(str, recent_scores))}")

            # Add buttons in columns
            col1, col2 = st.columns(2)
            
            # Add Score Button and Form
            with col1:
                if st.button("Add Score", key="add_score_btn"):
                    st.session_state["show_add_form"] = True
                    st.session_state["show_change_form"] = False

            # Change Subject Marks Button and Form
            with col2:
                if st.button("Change Subject Marks", key="change_marks_btn"):
                    st.session_state["show_change_form"] = True
                    st.session_state["show_add_form"] = False

            # Add Score Form
            if st.session_state.get("show_add_form", False):
                with st.form("add_score_form"):
                    st.subheader("Add New Scores")
                    scores_to_add = {}
                    for subject in subjects:
                        scores_to_add[subject] = st.number_input(f"{subject} Score", min_value=0, max_value=100, value=0, key=f"add_{subject}_score")
                    submitted = st.form_submit_button("Submit New Scores")
                    if submitted:
                        for subject, score in scores_to_add.items():
                            if isinstance(st.session_state["subject_scores"].get(subject), list):
                                st.session_state["subject_scores"][subject].append(score)
                            else:
                                st.session_state["subject_scores"][subject] = [score]
                        # Save scores to MongoDB
                        save_scores_to_mongodb(st.session_state.get("username", ""), st.session_state["subject_scores"])
                        st.success("Scores added successfully!")
                        st.session_state["show_add_form"] = False
                        st.rerun()

            # Change Subject Marks Form
            if st.session_state.get("show_change_form", False):
                with st.form("change_marks_form"):
                    st.subheader("Change Subject Marks")
                    subject_to_change = st.selectbox("Select Subject", subjects)
                    if subject_to_change in st.session_state["subject_scores"] and len(st.session_state["subject_scores"][subject_to_change]) > 0:
                        entry_index = st.selectbox("Select Entry to Change", 
                                                range(1, len(st.session_state["subject_scores"][subject_to_change]) + 1),
                                                format_func=lambda x: f"Entry {x}")
                        new_score = st.number_input("New Score", min_value=0, max_value=100, 
                                                value=st.session_state["subject_scores"][subject_to_change][entry_index-1])
                        submitted = st.form_submit_button("Update Score")
                        if submitted:
                            st.session_state["subject_scores"][subject_to_change][entry_index-1] = new_score
                            # Save updated scores to MongoDB
                            save_scores_to_mongodb(st.session_state.get("username", ""), st.session_state["subject_scores"])
                            st.success(f"Score updated successfully for {subject_to_change}!")
                            st.session_state["show_change_form"] = False
                            st.rerun()
                    else:
                        st.warning("No scores available for this subject yet.")
                        st.form_submit_button("Close", disabled=True)
    elif st.session_state["current_page"] == "study":
        st.title("Study Material")
        
        # Get user's class grade
        user = st.session_state.get("user")
        if user:
            class_grade = user.get("class_grade", "")
            
            if class_grade == "12 Science":
                st.info("Redirecting to Class 12 Science Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 12 Science Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1vz83zfD-BZa5JQ_kzH0sR7IR6d9gZciZ" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            elif class_grade == "11 Science":
                st.info("Redirecting to Class 11 Science Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 11 Science Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1L2gGlZGXgLyRbIrX8VmmUxOGavSoZ14b" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            elif class_grade == "11 Commerce":
                st.info("Redirecting to Class 11 Commerce Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 11 Commerce Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1eDugXGA7xhEu2ntPeD9YBEoA8ZjmC2E6" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            elif class_grade == "10":
                st.info("Redirecting to Class 10 Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 10 Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1vNF3k7N2mO4p99F0qxe-FRG3P4d2ncEm" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            elif class_grade == "9":
                st.info("Redirecting to Class 9 Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 9 Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1irw_9irQa-gNa96NDp8bHtiMVS24XFL1" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            elif class_grade == "8":
                st.info("Redirecting to Class 8 Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 8 Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1PJrhYf3o7l4HIMtb2Efttm26aUsMLCpL" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            elif class_grade == "7":
                st.info("Redirecting to Class 7 Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 7 Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1psTVTOizf2ooZL3nrniJPVKuD9VtyXTx" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            elif class_grade == "6":
                st.info("Redirecting to Class 6 Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 6 Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1XK_mZLmVLv3AI3Bl7woOJvKwgkm2u6Hr" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            elif class_grade == "12 Commerce":
                st.info("Redirecting to Class 12 Commerce Study Material...")
                st.markdown("""
                    <div style="text-align: center; padding: 20px;">
                        <h3>Class 12 Commerce Study Material</h3>
                        <p>Click the button below to access your study material:</p>
                        <a href="https://drive.google.com/drive/folders/1HetMbC0geyHfH35pcVyBWwdN_G1LouEv" target="_blank">
                            <button style="background-color: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px;">
                                Access Study Material
                            </button>
                        </a>
                    </div>
                """, unsafe_allow_html=True)
            else:
                st.info(f"Study material for Class {class_grade} will be available soon!")
    elif st.session_state["current_page"] == "predictor":
        st.title("Predict Score")
        
        # Initialize prediction state if not exists
        if "predictions" not in st.session_state:
            st.session_state["predictions"] = None
        if "last_scores_state" not in st.session_state:
            st.session_state["last_scores_state"] = None
        else:
            st.subheader("Student Performance Dashboard")

        if "subject_scores" not in st.session_state:
            st.info("Please enter your scores for each subject.")
            # Get user's class grade
            user = st.session_state.get("user")
            if user:
                class_grade = user.get("class_grade", "")
                subjects = get_subjects_for_grade(class_grade)
                scores = {}
                with st.form("score_form"):
                    for subject in subjects:
                        scores[subject] = st.number_input(f"{subject} Score", min_value=0, max_value=100, value=0)
                    submitted = st.form_submit_button("Submit Scores")
                    if submitted:
                        st.session_state["subject_scores"] = {subject: [score] for subject, score in scores.items()}
                        # Reset predictions when new scores are submitted
                        st.session_state["predictions"] = None
                        st.session_state["last_scores_state"] = None
                        st.success("Scores submitted successfully!")
                        st.rerun()
        else:
            # Check if scores have changed
            current_scores_state = str(st.session_state["subject_scores"])
            scores_changed = current_scores_state != st.session_state["last_scores_state"]

            # Only recalculate predictions if scores have changed or no predictions exist
            if scores_changed or st.session_state["predictions"] is None:
                with st.spinner('Predicting scores... Please wait.'):
                    st.session_state["predictions"] = train_and_predict(st.session_state["subject_scores"])
                    st.session_state["last_scores_state"] = current_scores_state
            
            # Display predictions
            st.subheader("Predicted Next Scores")
            
            # Create two columns for better visualization
            col1, col2 = st.columns(2)
            
            # Display predictions in a table format
            with col1:
                st.markdown("### Subject-wise Predictions")
                for subject, prediction in st.session_state["predictions"].items():
                    if isinstance(prediction, str):
                        st.warning(f"{subject}: {prediction}")
                    else:
                        st.info(f"{subject}: {prediction}")

                        if prediction < 50:
                            st.error("Recommendation: Focus on fundamentals, revise NCERT chapters, and practice daily.")
                        elif prediction < 70:
                            st.warning("Recommendation: Increase practice and solve previous year questions.")
                        else:
                            st.success("Recommendation: Maintain consistency and attempt advanced problems.")
            
            # Display average prediction
            with col2:
                valid_predictions = [pred for pred in st.session_state["predictions"].values() if isinstance(pred, (int, float))]
                if valid_predictions:
                    avg_prediction = round(sum(valid_predictions) / len(valid_predictions), 2)
                    st.markdown("### Overall Prediction")
                    st.metric("Average Predicted Score", f"{avg_prediction}")
                    highest_subject = max(
                        st.session_state["predictions"],
                        key=lambda x: st.session_state["predictions"][x]
                        if isinstance(st.session_state["predictions"][x], (int, float))
                        else -1
                    )

                    st.success(f"Strongest Subject: {highest_subject}")
                    lowest_subject = min(
                        st.session_state["predictions"],
                        key=lambda x: st.session_state["predictions"][x]
                        if isinstance(st.session_state["predictions"][x], (int, float))
                        else 999
                    )

                    st.error(f"Weakest Subject: {lowest_subject}")
    elif st.session_state["current_page"] == "analytics":
        st.title("Analytics Dashboard")
        # Ensure subject_scores available
        subject_scores = st.session_state.get("subject_scores", {})
        render_analytics_page(subject_scores)
    else:
        st.info("📚 No performance data available yet. Start entering scores to view insights.")
                    
# Initialize session state
if "page" not in st.session_state:
    st.session_state["page"] = "login"

# Main application logic
if st.session_state["page"] == "dashboard":
    display_dashboard_page()
else:
    # UI Layout - Two Vertical Parts
    col1, col2 = st.columns([2, 1])

    # Left Side - Features of Product
    with col1:

        st.image(
        "assets/edupredict_logo.png",
        width=180
        )
        st.markdown("""
        <div style='text-align:center;'>
        <p style='font-size:24px;'>
        AI-powered personalized learning, score prediction,
        and academic analytics.
        </p>
        </div>
        """, unsafe_allow_html=True)

        if st.button(
            "🚀 Start Learning Today",
            key="hero_get_started",
            use_container_width=True
        ):
            st.session_state["page"] = "signup"
            st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        col_a, col_b, col_c = st.columns(3)

        with col_a:
            st.markdown("""
            <div style="
                background:white;
                padding:20px;
                border-radius:10px;
                border:1px solid #e5e7eb;
                height:200px;
            ">
                <h3>📊 Performance Analytics</h3>
                <p>Track academic progress and monitor performance trends.</p>
            </div>
            """, unsafe_allow_html=True)

        with col_b:
            st.markdown("""
            <div style="
                background:white;
                padding:20px;
                border-radius:10px;
                border:1px solid #e5e7eb;
                height:200px;
            ">
                <h3>🤖 AI Score Prediction</h3>
                <p>Predict future scores using AI-powered analysis.</p>
            </div>
            """, unsafe_allow_html=True)

        with col_c:
            st.markdown("""
            <div style="
                background:white;
                padding:20px;
                border-radius:10px;
                border:1px solid #e5e7eb;
                height:200px;
            ">
                <h3>📚 Study Material</h3>
                <p>Access class-wise learning resources and materials.</p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


        st.markdown("### Trusted Learning Insights")
        st.caption("Helping students track progress and improve performance.")


        stat1, stat2, stat3, stat4 = st.columns(4)

        with stat1:
            st.metric("📚 Resources", "500+")

        with stat2:
            st.metric("🤖 Predictions", "1000+")

        with stat3:
            st.metric("🎓 Students", "100+")

        with stat4:
            st.metric("📈 Accuracy", "85%")

    # Right Side - Login/Signup Form
    with col2:
        st.markdown("""
        <style>
        .login-container {
            background: white;
            padding: 30px;
            border-radius: 16px;
            border: 1px solid #e5e7eb;
            box-shadow: 0px 15px 35px rgba(0,0,0,0.12);
        }
        </style>
        """, unsafe_allow_html=True)
        st.markdown("""
        
        """, unsafe_allow_html=True)

        card = st.container(border=True)

        with card:
        
            if st.session_state["page"] == "login":
                st.markdown("""
                    <div style="
                        text-align:center;
                        padding-bottom:15px;
                    ">
                        <h2>🔐 Welcome Back</h2>
                        <p>Access your personalized learning dashboard</p>
                    </div> 
                    """, unsafe_allow_html=True)
                st.markdown("""
                    <div style="text-align:center; padding:5px; color:#000000; font-style:bold; font-size:30px;">
                    𝓛𝓸𝓰𝓲𝓷

                """,
                  unsafe_allow_html=True)
                username = st.text_input("User ID", placeholder="Enter User ID", key="login_username")
                password = st.text_input("Password", type="password", placeholder="Enter Password", key="login_password")
                
                col_login, col_signup = st.columns([1,1], gap="large")
                
                with col_login:
                    if st.button("🚀 Login", use_container_width=True):

                        if not username.strip():
                            st.error("Please enter your username.")

                        elif not password:
                            st.error("Please enter your password.")

                        else:
                            user = users_collection.find_one(
                                {"username": username.strip()}
                            )

                            if not user:
                                st.error("Username does not exist.")

                            elif not verify_password(password, user["password"]):
                                st.error("Incorrect password.")

                            else:
                                st.session_state["page"] = "dashboard"
                                st.session_state["username"] = username.strip()
                                st.session_state["user"] = user
                                st.rerun()
                
                with col_signup:
                   if st.button("Create Account", use_container_width=True):
                    st.session_state["page"] = "signup"
                    st.rerun()

            elif st.session_state["page"] == "signup":

                st.markdown("""
                    <div style="text-align:center; padding:5px; color:#000000; font-style:bold; font-size:30px;">
                    𝓢𝓲𝓰𝓷 𝓤𝓹

                """,
                  unsafe_allow_html=True)

                full_name = st.text_input("Full Name")
                username = st.text_input("Username")
                class_grade = st.selectbox("Class", GRADE_OPTIONS)
                password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")

                if password != confirm_password:
                    st.error("Passwords do not match.")
                col_create, col_back = st.columns(2)

                with col_create:
                    if st.button("Sign Up", use_container_width=True):

                        username_error = validate_username(username)
                        password_error = validate_password(password)

                        if not full_name.strip():
                            st.error("Full name cannot be empty.")

                        elif username_error:
                            st.error(username_error)

                        elif password != confirm_password:
                            st.error("Passwords do not match.")

                        elif password_error:
                            st.error(password_error)

                        elif users_collection.find_one({"username": username.strip()}):
                            st.error("Username already exists.")

                        else:
                            users_collection.insert_one({
                                "full_name": full_name.strip(),
                                "username": username.strip(),
                                "class_grade": class_grade,
                                "password": hash_password(password),
                                "createdAt": datetime.now(UTC)
                            })

                            st.success("Account created successfully!")

                            st.session_state["username"] = username.strip()
                            st.session_state["page"] = "dashboard"

                            st.rerun()

                with col_back:
                    if st.button("Back to Login"):
                        st.session_state["page"] = "login"
                        st.rerun()
            
    st.markdown("---")

    st.markdown("""
        <div style="text-align:center; padding:20px; color:#6b7280;">
            <h4>EduPredict © 2026</h4>
            <p style="margin-top:15px; font-size:14px;">
                Developed by <b><I>Shrihari H Kulkarni</b></I><br>
                AI-Powered Personalized Learning Platform<br>
                Built with Python • Streamlit • MongoDB • TensorFlow
            </p>
        </div>
        """, unsafe_allow_html=True)
        
