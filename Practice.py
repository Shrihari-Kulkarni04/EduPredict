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
import streamlit.components.v1 as components

# Set page config at the beginning
st.set_page_config(page_title="EduPredict", layout="wide")

# MongoDB Connection
import os
@st.cache_resource
def get_database():
    client = MongoClient(os.getenv("MONGO_URI"))
    return client["education_system"]

db = get_database()
users_collection = db["users"]

users_collection = db["users"]

TTL_SECONDS = 20 * 24 * 60 * 60  # 20 days

indexes = users_collection.index_information()

ttl_index_name = None

for name, info in indexes.items():
    if info.get("key") == [("createdAt", 1)]:
        ttl_index_name = name
        current_ttl = info.get("expireAfterSeconds")

        if current_ttl != TTL_SECONDS:
            users_collection.drop_index(name)
            ttl_index_name = None
        break

if ttl_index_name is None:
    users_collection.create_index(
        [("createdAt", 1)],
        expireAfterSeconds=TTL_SECONDS,
        name="ttl_20_days"
    )

users_collection.create_index(
    [("username", 1)],
    unique=True,
    name="username_index"
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
        .stButton > button {
            background: #111827 !important;
            color: white !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 18px !important;
            font-size: 15px !important;
            font-weight: 600 !important;
            transition: all 0.25s ease !important;
            box-shadow: 0 4px 10px rgba(0,0,0,0.15) !important;
        }

        .stButton > button:hover {
            background: #000000 !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 18px rgba(0,0,0,0.25) !important;
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
        padding: 30px;
        background: linear-gradient(135deg, #2563EB, #7C3AED);
        color: white;
        border-radius: 18px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px rgba(37, 99, 235, 0.35);
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

st.markdown(
    """
    <style>
        @media (max-width: 1024px) {
            .stApp,
            [data-testid="stAppViewContainer"] {
                overflow-x: hidden !important;
            }
            [data-testid="stPlotlyChart"],
            [data-testid="stDataFrame"] {
                max-width: 100% !important;
                overflow-x: auto !important;
            }
            iframe,
            img,
            svg,
            canvas {
                max-width: 100% !important;
            }
            div[style] {
                box-sizing: border-box !important;
                max-width: 100% !important;
                overflow-wrap: break-word !important;
            }
            .study-page-wrap,
            .study-hero-card,
            .study-section-card,
            .study-tip-card,
            .study-viewer-card {
                max-width: 100% !important;
                box-sizing: border-box !important;
            }
        }

        @media (max-width: 768px) {
            [data-testid="column"] {
                width: 100% !important;
                min-width: 100% !important;
                flex: 1 1 100% !important;
            }
            .stButton > button {
                width: 100% !important;
                white-space: normal !important;
            }
            .stTextInput input,
            .stTextArea textarea,
            .stNumberInput input,
            .stSelectbox,
            .stFileUploader,
            [data-testid="stForm"] {
                width: 100% !important;
                max-width: 100% !important;
            }
            .study-page-wrap {
                padding-left: 8px !important;
                padding-right: 8px !important;
            }
            .study-hero-card,
            .study-section-card,
            .study-tip-card {
                padding: 20px !important;
            }
            .study-open-btn {
                width: 100% !important;
                text-align: center !important;
                box-sizing: border-box !important;
            }
            .study-subject-grid {
                grid-template-columns: 1fr !important;
            }
            .st-key-profile_avatar_btn {
                justify-content: flex-end !important;
            }
        }

        @media (max-width: 600px) {
            [data-testid="block-container"] {
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            h1 {
                line-height: 1.2 !important;
                overflow-wrap: break-word !important;
            }
            h2,
            h3,
            p,
            label {
                overflow-wrap: break-word !important;
            }
            [data-testid="stMetric"] {
                width: 100% !important;
            }
        }

        @media (max-width: 480px) {
            [data-testid="block-container"] {
                padding-left: 0.75rem !important;
                padding-right: 0.75rem !important;
            }
            .study-hero-card,
            .study-section-card,
            .study-tip-card {
                padding: 16px !important;
            }
            .study-icon {
                width: 56px !important;
                height: 56px !important;
                font-size: 28px !important;
            }
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
        st.toast("✅ Profile updated successfully!")

    profile_src = html.escape(get_profile_picture_src(user), quote=True)
    safe_name = html.escape(user.get("full_name", "User"))
    safe_username = html.escape(user.get("username", ""))
    safe_class = html.escape(user.get("class_grade", ""))

    st.markdown(
        f"""
        <div style="
            background:#ffffff;
            border:1px solid #E5E7EB;
            border-radius:18px;
            padding:24px;
            box-shadow:0 8px 20px rgba(0,0,0,.08);
            display:flex;
            align-items:center;
            gap:20px;
            margin-bottom:25px;
        ">

        <img src="{profile_src}"
        style="
            width:90px;
            height:90px;
            border-radius:50%;
            object-fit:cover;
            border:3px solid #2563EB;
        ">

        <div>

        <h3 style="
            margin:0;
            color:#111827;
        ">
        {safe_name}
        </h3>

        <p style="
            margin:6px 0;
            color:#6B7280;
        ">
            @{safe_username}
        </p>

        <span style="
            background:#EEF2FF;
            color:#2563EB;
            padding:6px 12px;
            border-radius:20px;
            font-size:13px;
            font-weight:600;
        ">
            Class {safe_class}
        </span>

        </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    grade_options = get_grade_options(user.get("class_grade", ""))
    current_grade_index = grade_options.index(user.get("class_grade", "")) if user.get("class_grade", "") in grade_options else 0

    with st.form("profile_edit_form"):

        col1, col2 = st.columns(2)

        with col1:
            full_name = st.text_input(
                "Full Name",
                value=user.get("full_name", ""),
                key="profile_full_name"
            )

        with col2:
            new_username = st.text_input(
                "Username",
                value=user.get("username", ""),
                key="profile_username"
            )

        class_grade = st.selectbox(
            "Class",
            grade_options,
            index=current_grade_index,
            key="profile_class"
        )

        st.markdown("### Profile Picture")

        uploaded_file = st.file_uploader(
            "Upload a new profile picture",
            type=["png", "jpg", "jpeg", "webp"],
            key="profile_picture_upload"
        )

        remove_profile_pic = st.checkbox(
            "Remove current profile picture",
            value=False,
            disabled=not user.get("profile_pic"),
            key="remove_profile_picture"
        )

        left, center, right = st.columns([3, 2, 3])

        with center:
            submitted = st.form_submit_button(
                "Save Profile",
                use_container_width=True
            )
        
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
    profile_src = get_profile_picture_src(user)
    css_profile_src = profile_src.replace("\\", "\\\\").replace('"', '\\"')

    # Ensure session state flags exist
    if "show_profile_menu" not in st.session_state:
        st.session_state["show_profile_menu"] = False
    if "show_mobile_nav" not in st.session_state:
        st.session_state["show_mobile_nav"] = False

    st.markdown(
        f"""
        <style>
        .st-key-edupredict_nav_mobile,
        .st-key-edupredict_mobile_menu {{
            display: none;
        }}
        .st-key-edupredict_nav_desktop,
        .st-key-edupredict_nav_mobile,
        .st-key-edupredict_mobile_menu {{
            width: 100%;
            max-width: 100%;
            box-sizing: border-box;
        }}
        .st-key-edupredict_nav_desktop [data-testid="stHorizontalBlock"] {{
            align-items: center;
        }}
        .st-key-edupredict_nav_desktop .stButton > button {{
            white-space: nowrap !important;
        }}
        .st-key-profile_avatar_btn,
        .st-key-mobile_profile_avatar_btn {{
            display: flex;
            justify-content: flex-end;
        }}
        .st-key-profile_avatar_btn button,
        .st-key-mobile_profile_avatar_btn button {{
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
        .st-key-profile_avatar_btn button p,
        .st-key-mobile_profile_avatar_btn button p {{
            font-size: 0 !important;
        }}
        @media (max-width: 768px) {{
            .st-key-edupredict_nav_desktop {{
                display: none !important;
            }}
            .st-key-edupredict_nav_mobile {{
                display: block !important;
            }}
            .st-key-edupredict_nav_mobile [data-testid="stHorizontalBlock"] {{
                display: flex !important;
                flex-direction: row !important;
                align-items: center !important;
                gap: 12px !important;
            }}
            .st-key-edupredict_nav_mobile [data-testid="column"] {{
                width: auto !important;
                min-width: 0 !important;
                flex: 0 0 auto !important;
            }}
            .st-key-edupredict_nav_mobile [data-testid="column"]:first-child {{
                flex: 1 1 auto !important;
            }}
            .st-key-edupredict_mobile_menu {{
                display: block !important;
            }}
            .st-key-edupredict_mobile_menu .stButton > button {{
                width: 100% !important;
                text-align: left;
            }}
        }}
        @media (min-width: 769px) {{
            .st-key-edupredict_nav_desktop {{
                display: block !important;
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )

    def go_to_page(page_name):
        st.session_state["current_page"] = page_name
        st.session_state["show_mobile_nav"] = False
        st.rerun()

    with st.container(key="edupredict_nav_desktop"):
        nav_logo, nav_dashboard, nav_performance_col, nav_analytics_col, nav_study_col, nav_predictor_col, nav_profile_col = st.columns(
            [1.6, 1.2, 1.6, 1.7, 1.8, 1.5, 0.8]
        )

        with nav_logo:
            st.image("assets/edupredict_icon.png", width=120)
        with nav_dashboard:
            if st.button("Dashboard", key="nav_dashboard"):
                go_to_page("dashboard")
        with nav_performance_col:
            if st.button("Performance", key="nav_performance"):
                go_to_page("performance")
        with nav_analytics_col:
            if st.button("Analytics", key="nav_analytics"):
                go_to_page("analytics")
        with nav_study_col:
            if st.button("Study Material", key="nav_study"):
                go_to_page("study")
        with nav_predictor_col:
            if st.button("Predict Score", key="nav_predictor"):
                go_to_page("predictor")
        with nav_profile_col:
            if st.button("", key="profile_avatar_btn", help="Open profile menu"):
                if st.session_state.get("show_profile_editor", False):
                    st.session_state["show_profile_editor"] = False
                    st.session_state["show_profile_menu"] = False
                else:
                    st.session_state["show_profile_menu"] = not st.session_state.get(
                        "show_profile_menu", False
                    )
                st.rerun()

    with st.container(key="edupredict_nav_mobile"):
        mobile_menu_col, mobile_profile_col = st.columns([6, 1])

        with mobile_menu_col:
            if st.button("☰ EduPredict", key="mobile_nav_toggle"):
                st.session_state["show_mobile_nav"] = not st.session_state.get("show_mobile_nav", False)
                st.rerun()
        with mobile_profile_col:
            if st.button("", key="mobile_profile_avatar_btn", help="Open profile menu"):
                if st.session_state.get("show_profile_editor", False):
                    st.session_state["show_profile_editor"] = False
                    st.session_state["show_profile_menu"] = False
                else:
                    st.session_state["show_profile_menu"] = not st.session_state.get(
                        "show_profile_menu", False
                    )
                st.rerun()

    if st.session_state.get("show_mobile_nav", False):
        with st.container(key="edupredict_mobile_menu"):
            if st.button("Dashboard", key="mobile_nav_dashboard"):
                go_to_page("dashboard")
            if st.button("Performance History", key="mobile_nav_performance"):
                go_to_page("performance")
            if st.button("Analytics Dashboard", key="mobile_nav_analytics"):
                go_to_page("analytics")
            if st.button("Study Material", key="mobile_nav_study"):
                go_to_page("study")
            if st.button("Predict Score", key="mobile_nav_predictor"):
                go_to_page("predictor")
            if st.button("Profile", key="mobile_nav_profile"):
                st.session_state["show_profile_editor"] = True
                st.session_state["show_profile_menu"] = False
                st.session_state["show_mobile_nav"] = False
                st.rerun()

    # Render dropdown overlay card when menu is shown
    if st.session_state.get("show_profile_menu"):

        if st.button("✏️ Edit Profile", key="edit_profile_btn"):
            st.session_state["show_profile_editor"] = True
            st.session_state["show_profile_menu"] = False
            st.rerun()

        if st.button("Logout", key="profile_logout"):
            st.session_state.clear()
            st.session_state["page"] = "login"
            st.rerun()

def display_dashboard(username):
    
            user = st.session_state.get("user")

            if not user:
                st.error("User not found!")
                return

            # Welcome Section
            st.markdown(f"""
        <div style="
        background:linear-gradient(135deg,#ffffff,#f8fafc);
        padding:30px;
        border-radius:18px;
        border:1px solid #e5e7eb;
        box-shadow:0 8px 20px rgba(0,0,0,.08);
        margin-bottom:25px;
        ">

        <p style="
        color:#111827;
        font-size:15px;
        font-weight:700;
        margin-bottom:8px;
        letter-spacing:1px;
        text-transform:uppercase;
        ">
        DASHBOARD
        </p>

        <h2 style="
        margin:0;
        color:#111827;
        font-size:32px;
        font-weight:700;
        line-height:1.2;
        ">
        Welcome back, {user['full_name']} 👋
        </h2>

        <p style="
        font-size:16px;
        color:#6b7280;
        margin-top:10px;
        margin-bottom:0;
        ">
        <b>Class:</b> {user['class_grade']}
        </p>

        <hr style="
        margin:20px 0;
        border:none;
        border-top:1px solid #E5E7EB;
        ">

        <p style="
        font-size:16px;
        color:#374151;
        margin:0;
        ">
        Track your academic performance, predict future scores, and access personalized study resources from one place.
        </p>
        </div>
        """, unsafe_allow_html=True)
            
            st.markdown("""
            <h3 style="
            color:#111827;
            font-size:24px;
            font-weight:700;
            margin-top:5px;
            margin-bottom:18px;
            ">
            Academic Overview
            </h3>
            """, unsafe_allow_html=True)

        # Dashboard Summary Cards
            subject_scores = st.session_state.get("subject_scores", {})
            analytics = compute_analytics(subject_scores)

            if analytics:

                c1, c2, c3, c4 = st.columns(4)

                cards = [
                    ("📈 Average Score", analytics["average_score"], "#2563EB"),
                    ("🏆 Strongest Subject", analytics["strongest_subject"], "#16A34A"),
                    ("⚠️ Weakest Subject", analytics["weakest_subject"], "#DC2626"),
                    ("📚 Total Subjects", analytics["total_subjects"], "#7C3AED"),
                ]

                for col, (title, value, color) in zip([c1, c2, c3, c4], cards):
                    with col:
                        st.markdown(f"""
<div style="
background:white;
padding:20px;
border-radius:15px;
border:1px solid #e5e7eb;
box-shadow:0 4px 12px rgba(0,0,0,.08);
text-align:center;
min-height:130px;
">

<p style="
color:{color};
font-size:15px;
margin-bottom:8px;
">
{title}
</p>

<h2 style="
color:{color};
margin:0;
">
{value}
</h2>

</div>
""", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

def create_marks_bar_graph(subject_scores):
    # Create a bar graph using plotly
    fig = go.Figure()
    
    # Define colors for different entries
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # Blue, Orange, Green
    
    # Process each subject
    for subject, scores in subject_scores.items():
        scores = get_numeric_scores(scores)
        if not scores:
            continue

        # Get only the last 3 entries
        recent_scores = scores[-3:].copy() if len(scores) >= 3 else scores.copy()
        
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

def get_numeric_scores(scores):
    return [
        score for score in scores
        if isinstance(score, (int, float))
    ]

from sklearn.linear_model import LinearRegression

def train_and_predict(subject_scores):
    predictions = {}

    for subject, scores in subject_scores.items():

        # Keep only numeric scores
        scores = get_numeric_scores(scores)

        # Require at least 3 entries
        if len(scores) < 3:
            predictions[subject] = "Minimum 3 score entries are required."
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
    
    predictions = st.session_state.get("predictions", {})

    valid_predictions = [
        p for p in predictions.values()
        if isinstance(p, (int, float))
    ]

    predicted_score = (
        round(sum(valid_predictions) / len(valid_predictions), 2)
        if valid_predictions else "--"
    )

    improvement_rate = "--"

    improvements = []

    for scores in subject_scores.values():
        scores = get_numeric_scores(scores)
        if len(scores) >= 2:
            previous = scores[-2]
            current = scores[-1]

            if previous != 0:
                improvements.append(((current - previous) / previous) * 100)

    if improvements:
        improvement_rate = f"{round(sum(improvements) / len(improvements), 1)}%"

    subject_averages = {}
    all_scores = []
    for subject, scores in subject_scores.items():
        scores = get_numeric_scores(scores)
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

    if average_score >= 90:
        study_readiness = "Excellent"
    elif average_score >= 80:
        study_readiness = "High"
    elif average_score >= 70:
        study_readiness = "Moderate"
    elif average_score >= 60:
        study_readiness = "Needs Focus"
    else:
        study_readiness = "At Risk"

    return {
    "average_score": average_score,
    "strongest_subject": strongest_subject,
    "weakest_subject": weakest_subject,
    "total_subjects": total_subjects,
    "highest_score": highest_score,
    "lowest_score": lowest_score,
    "subject_averages": subject_averages,
    "subjects_needing_improvement": subjects_needing_improvement,
    "predicted_score": predicted_score,
    "study_readiness": study_readiness,
    "improvement_rate": improvement_rate,
    }


def build_subject_avg_bar_chart(subject_averages):
    import plotly.express as px

    # Sort subjects by average score (Highest → Lowest)
    sorted_data = sorted(
        subject_averages.items(),
        key=lambda x: x[1],
        reverse=True
    )

    subjects = [item[0] for item in sorted_data]
    averages = [item[1] for item in sorted_data]

    fig = px.bar(
    x=averages,
    y=subjects,
    orientation="h",
    text=[f"{score:.1f}" for score in averages],
    color=subjects,
    color_discrete_sequence=[
        "#2563EB",  # Blue
        "#16A34A",  # Green
        "#F59E0B",  # Amber
        "#DC2626",  # Red
        "#7C3AED",  # Purple
        "#06B6D4",  # Cyan
        "#EA580C",  # Orange
        "#EC4899"   # Pink
    ]
    )

    fig.update_layout(
        title={
            "text": "📊 Subject Performance Ranking",
            "x": 0.02,
            "font": {"size": 20}
        },
        xaxis_title="Average Score",
        yaxis_title="",
        xaxis=dict(range=[0, 100]),
        coloraxis_showscale=False,
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=430,
        margin=dict(l=20, r=20, t=60, b=20)
    )

    return fig


def build_current_vs_predicted_chart(subject_averages, predictions):

    import plotly.graph_objects as go

    subjects = list(subject_averages.keys())

    current_scores = [
        subject_averages.get(subject, 0)
        for subject in subjects
    ]

    predicted_scores = [
        predictions.get(subject, 0)
        if isinstance(predictions.get(subject), (int, float))
        else 0
        for subject in subjects
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name="Current",
        x=subjects,
        y=current_scores,
        marker_color="#2563EB"
    ))

    fig.add_trace(go.Bar(
        name="Predicted",
        x=subjects,
        y=predicted_scores,
        marker_color="#16A34A"
    ))

    fig.update_layout(
        title="🤖 Current vs Predicted Performance",
        barmode="group",
        yaxis=dict(range=[0, 100]),
        xaxis_title="Subjects",
        yaxis_title="Score",
        plot_bgcolor="white",
        paper_bgcolor="white",
        height=430,
        legend=dict(
            orientation="h",
            y=1.1,
            x=0.5,
            xanchor="center"
        )
    )

    return fig


def build_score_distribution_pie_chart(subject_averages):
    labels = list(subject_averages.keys())
    values = [max(0.01, v) for v in subject_averages.values()]
    fig = go.Figure(go.Pie(labels=labels, values=values, hole=0.35))
    fig.update_layout(title_text='Score Distribution (by Subject Average)', paper_bgcolor='rgba(0,0,0,0)')
    return fig


def render_analytics_page(subject_scores):
    if (
        "predictions" not in st.session_state
        or st.session_state["predictions"] is None
    ):
        st.session_state["predictions"] = train_and_predict(subject_scores)

    analytics = compute_analytics(subject_scores)

    if analytics is None:
        st.info("No performance data available.")
        return

    # Top row KPI Cards

    st.markdown("""
    <h3 style="
    color:#111827;
    font-size:24px;
    font-weight:700;
    margin-bottom:18px;
    ">
    Academic Summary
    </h3>
    """, unsafe_allow_html=True)

    k1, k2, k3, k4 = st.columns(4)

    with k1:
        st.markdown(f"""
        <div style="
            background:#ffffff;
            padding:28px;
            border-radius:18px;
            border:1px solid #E5E7EB;
            box-shadow:0 8px 20px rgba(0,0,0,.08);
            min-height:190px;
            text-align:center;
        ">

        <div style="font-size:38px;">🎯</div>

        <p style="
            margin-top:12px;
            margin-bottom:14px;
            color:#6B7280;
            font-size:16px;
            font-weight:600;
        ">
        Overall Score
        </p>

        <h1 style="
            margin:0;
            color:#2563EB;
            font-size:42px;
            font-weight:700;
        ">
        {analytics['average_score']}%
        </h1>

        <p style="
            margin-top:14px;
            color:#9CA3AF;
            font-size:14px;
        ">
        Current Academic Performance
        </p>

        </div>
        """, unsafe_allow_html=True)

    with k2:
        st.markdown(f"""
        <div style="
            background:#ffffff;
            padding:28px;
            border-radius:18px;
            border:1px solid #E5E7EB;
            box-shadow:0 8px 20px rgba(0,0,0,.08);
            min-height:190px;
            text-align:center;
        ">

        <div style="font-size:38px;">🤖</div>

        <p style="
            margin-top:12px;
            margin-bottom:14px;
            color:#6B7280;
            font-size:16px;
            font-weight:600;
        ">
        Predicted Score
        </p>

        <h1 style="
            margin:0;
            color:#16A34A;
            font-size:42px;
            font-weight:700;
            min-height:52px;
            display:flex;
            align-items:center;
            justify-content:center;
        ">
        {analytics['predicted_score']}%
        </h1>

        <p style="
            margin-top:14px;
            color:#9CA3AF;
            font-size:14px;
        ">
        AI Estimated Performance
        </p>

        </div>
        """, unsafe_allow_html=True)

    with k3:
        st.markdown(f"""
        <div style="
            background:#ffffff;
            padding:28px;
            border-radius:18px;
            border:1px solid #E5E7EB;
            box-shadow:0 8px 20px rgba(0,0,0,.08);
            min-height:190px;
            text-align:center;
        ">

        <div style="font-size:38px;">📚</div>

        <p style="
            margin-top:12px;
            margin-bottom:14px;
            color:#6B7280;
            font-size:16px;
            font-weight:600;
        ">
        Study Readiness
        </p>

        <h1 style="
            margin:0;
            color:#F59E0B;
            font-size:36px;
            font-weight:700;
            min-height:52px;
            display:flex;
            align-items:center;
            justify-content:center;
        ">
        {analytics['study_readiness']}
        </h1>

        <p style="
            margin-top:14px;
            color:#9CA3AF;
            font-size:14px;
        ">
        Current Learning Status
        </p>

        </div>
        """, unsafe_allow_html=True)

    with k4:
        st.markdown(f"""
        <div style="
            background:#ffffff;
            padding:28px;
            border-radius:18px;
            border:1px solid #E5E7EB;
            box-shadow:0 8px 20px rgba(0,0,0,.08);
            min-height:190px;
            display:flex;
            flex-direction:column;
            align-items:center;
            justify-content:center;
        ">

        <div style="font-size:38px;">⬆️</div>

        <p style="
            margin-top:12px;
            margin-bottom:14px;
            color:#6B7280;
            font-size:16px;
            font-weight:600;
        ">
        Improvement Rate
        </p>

        <h1 style="
            margin:0;
            width:100%;
            color:#7C3AED;
            font-size:42px;
            font-weight:700;
            min-height:52px;
            display:flex;
            align-items:center;
            justify-content:center;
            text-align:center;
        ">
            {analytics['improvement_rate']}
        </h1>

        <p style="
            margin-top:14px;
            color:#9CA3AF;
            font-size:14px;
        ">
        Growth Since Last Entry
        </p>

        </div>
        """, unsafe_allow_html=True)

    st.markdown("""
    <h3 style="
    color:#111827;
    font-size:24px;
    font-weight:700;
    margin-bottom:18px;
    "><br><br><br>
    Performance Analytics
    </h3>
    """, unsafe_allow_html=True)

    # Middle row charts
    c1, c2 = st.columns([2, 3])
    with c1:
        fig_bar = build_subject_avg_bar_chart(analytics['subject_averages'])
        st.plotly_chart(fig_bar, use_container_width=True)
    with c2:
        fig_compare = build_current_vs_predicted_chart(
            analytics["subject_averages"],
            st.session_state["predictions"]
        )
        st.plotly_chart(fig_compare, use_container_width=True)

    # Bottom row insights and pie chart
    b1, b2 = st.columns([3, 2])
    with b1:

        st.markdown("## 📚 Study Readiness Report")

        readiness = analytics["study_readiness"]

        if readiness == "Excellent":
            badge = "🟢 Excellent"
        elif readiness == "High":
            badge = "🟢 High"
        elif readiness == "Moderate":
            badge = "🟡 Moderate"
        elif readiness == "Needs Focus":
            badge = "🟠 Needs Focus"
        else:
            badge = "🔴 At Risk"

        focus_subject = analytics["weakest_subject"]

        recommendation = {
            "Excellent": "Maintain your consistency and continue solving advanced questions.",
            "High": "Keep practicing regularly and strengthen weaker subjects.",
            "Moderate": "Increase weekly revision and focus on concept clarity.",
            "Needs Focus": "Create a structured study schedule and practice daily.",
            "At Risk": "Immediate attention required. Focus on fundamentals first."
        }

        st.metric("Overall Score", f"{analytics['average_score']}%")
        st.metric("Predicted Score", f"{analytics['predicted_score']}%")

        st.info(f"### Readiness Level\n{badge}")

        st.warning(f"### Focus Subject\n{focus_subject}")

        st.success(
            f"### Recommendation\n\n{recommendation[readiness]}"
        )
        def build_improvement_trend_chart(subject_scores):

            import plotly.graph_objects as go

            averages = []
            numeric_subject_scores = {
                subject: get_numeric_scores(scores)
                for subject, scores in subject_scores.items()
            }

            max_entries = max((len(scores) for scores in numeric_subject_scores.values()), default=0)

            for i in range(max_entries):
                current = []

                for scores in numeric_subject_scores.values():
                    if i < len(scores):
                        current.append(scores[i])

                if current:
                    averages.append(round(sum(current) / len(current), 2))

            if not averages:
                averages = [0]

            attempts = [f"Attempt {i+1}" for i in range(len(averages))]

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=attempts,
                y=averages,
                mode="lines+markers",
                fill="tozeroy",
                line=dict(color="#2563EB", width=4),
                marker=dict(size=9)
            ))

            fig.update_layout(
                title="📈 Improvement Trend",
                xaxis_title="Attempts",
                yaxis_title="Average Score",
                yaxis=dict(range=[0,100]),
                plot_bgcolor="white",
                paper_bgcolor="white",
                height=420
            )

            return fig
    with b2:
        fig_trend = build_improvement_trend_chart(subject_scores)
        st.plotly_chart(fig_trend, use_container_width=True)


def display_dashboard_page():
    
    user = st.session_state.get("user")

    if user is None:
        username = st.session_state.get("username")
        if username:
            user = users_collection.find_one({"username": username})
            st.session_state["user"] = user

    if user is None:
        st.error("User session expired. Please login again.")
        st.session_state["page"] = "login"
        st.rerun()
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
        st.session_state["subject_scores"] = {
            subject: get_numeric_scores(scores)
            for subject, scores in load_scores_from_mongodb(st.session_state.get("username", "")).items()
        }

    # Display current page content
    if st.session_state["current_page"] == "dashboard":
        display_dashboard(st.session_state.get("username", ""))
    elif st.session_state["current_page"] == "performance":
        st.title("Performance History")

        # Get user's class grade
        user = st.session_state.get("user")
        class_grade = user.get("class_grade", "") if user else ""
        subjects = get_subjects_for_grade(class_grade) if user else []
       
        all_scores = {
            subject: sum(get_numeric_scores(scores)) / len(get_numeric_scores(scores))
            for subject, scores in st.session_state["subject_scores"].items()
            if get_numeric_scores(scores)
        }

        if all_scores:

            st.markdown(f"""
            <p style="font-size:24px; font-weight:500; margin-bottom:25px; color:#6B7280;">
                Track and review your academic progress across all subjects.
            </p>
            """, unsafe_allow_html=True)

            best_subject = max(all_scores, key=all_scores.get)
            weak_subject = min(all_scores, key=all_scores.get)
            avg_score = round(sum(all_scores.values()) / len(all_scores), 2)

            total_entries = sum(
                len(get_numeric_scores(scores))
                for scores in st.session_state["subject_scores"].values()
            )

            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown(f"""
                <div style="
                    background:#ffffff;
                    padding:24px;
                    border-radius:18px;
                    border:1px solid #E5E7EB;
                    box-shadow:0 8px 20px rgba(0,0,0,.08);
                    min-height:170px;
                    text-align:center;
                ">
                    <div style="font-size:34px;">🏆</div>
                    <p style="
                        margin-top:10px;
                        color:#6B7280;
                        font-size:16px;
                        font-weight:600;
                    ">
                        Best Subject
                    </p>
                    <h2 style="
                        margin:8px 0;
                        color:#16A34A;
                        font-size:34px;
                        font-weight:700;
                    ">
                        {best_subject}
                    </h2>
                    <p style="
                        color:#9CA3AF;
                        font-size:14px;
                    ">
                        Highest Average
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col2:
                st.markdown(f"""
                <div style="
                    background:#ffffff;
                    padding:24px;
                    border-radius:18px;
                    border:1px solid #E5E7EB;
                    box-shadow:0 8px 20px rgba(0,0,0,.08);
                    min-height:170px;
                    text-align:center;
                ">
                    <div style="font-size:34px;">📈</div>
                    <p style="
                        margin-top:10px;
                        color:#6B7280;
                        font-size:16px;
                        font-weight:600;
                    ">
                        Overall Average
                    </p>
                    <h2 style="
                        margin:8px 0;
                        color:#2563EB;
                        font-size:34px;
                        font-weight:700;
                    ">
                        {avg_score}%
                    </h2>
                    <p style="
                        color:#9CA3AF;
                        font-size:14px;
                    ">
                        Across All Tests
                    </p>
                </div>
                """, unsafe_allow_html=True)

            with col3:
                st.markdown(f"""
                <div style="
                    background:#ffffff;
                    padding:24px;
                    border-radius:18px;
                    border:1px solid #E5E7EB;
                    box-shadow:0 8px 20px rgba(0,0,0,.08);
                    min-height:170px;
                    text-align:center;
                ">
                    <div style="font-size:34px;">📝</div>
                    <p style="
                        margin-top:10px;
                        color:#6B7280;
                        font-size:16px;
                        font-weight:600;
                    ">
                        Total Entries
                    </p>
                    <h2 style="
                        margin:8px 0;
                        color:#7C3AED;
                        font-size:34px;
                        font-weight:700;
                    ">
                        {total_entries}
                    </h2>
                    <p style="
                        color:#9CA3AF;
                        font-size:14px;
                    ">
                        Recorded Attempts
                    </p>
                </div>
                """, unsafe_allow_html=True)

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
            
        if user:
            # Display the bar chart with recent entries if scores exist
            if st.session_state["subject_scores"]:
                st.subheader("Recent Performance")
                fig = create_marks_bar_graph(st.session_state["subject_scores"])
                st.plotly_chart(fig, use_container_width=True)

                # Display the numerical data
                import pandas as pd

                st.subheader("📋 Score History")

                table_data = []

                for subject, scores in st.session_state["subject_scores"].items():

                    recent_scores = get_numeric_scores(scores)[-3:].copy()

                    while len(recent_scores) < 3:
                        recent_scores.append("-")

                    table_data.append({
                        "Subject": subject,
                        "Entry 1": recent_scores[0],
                        "Entry 2": recent_scores[1],
                        "Entry 3": recent_scores[2]
                    })

                df = pd.DataFrame(table_data)

                table_html = """
                <!DOCTYPE html>
                <html>
                <head>
                <style>

                body{
                    margin:0;
                    padding:15px;
                    font-family:Arial, sans-serif;
                    background:white;
                }
                table{
                    width:100%;
                    border-collapse:collapse;
                    border:1px solid #D1D5DB;
                    border-radius:12px;
                    overflow:hidden;
                    box-shadow:0 6px 18px rgba(0,0,0,.08);
                }
                .score-table-scroll{
                    width:100%;
                    overflow-x:auto;
                }

                tbody tr:last-child td{
                    border-bottom:1px solid #D1D5DB;
                }

                td:first-child,
                th:first-child{
                    border-left:1px solid #D1D5DB;
                }

                td:last-child,
                th:last-child{
                    border-right:1px solid #D1D5DB;
                }

                th{
                    background:#2563EB;
                    color:white;
                    padding:14px;
                    text-align:center;
                    font-size:16px;
                    background:#2563EB;
                    color:white;
                    padding:14px;
                    text-align:center;
                    border:1px solid #D1D5DB;
                    font-size:16px;
                }

                td{
                    padding:12px;
                    text-align:center;
                    border-bottom:1px solid #E5E7EB;
                    font-size:15px;
                    padding:12px;
                    text-align:center;
                    border:1px solid #E1D5DB;
                    font-size:15px;
                }

                tr:nth-child(even){
                    background:#F9FAFB;
                }

                tr:hover{
                    background:#EEF4FF;
                }

                @media (max-width:600px){
                    table{
                        min-width:520px;
                    }
                    th,
                    td{
                        white-space:nowrap;
                    }
                }

                </style>
                </head>

                <body>

                <div class="score-table-scroll">
                <table>

                <thead>
                <tr>
                <th>Subject</th>
                <th>Entry 1</th>
                <th>Entry 2</th>
                <th>Entry 3</th>
                </tr>
                </thead>

                <tbody>
                """

                for row in table_data:

                    table_html += f"""
                <tr>
                <td>{row['Subject']}</td>
                <td>{row['Entry 1']}</td>
                <td>{row['Entry 2']}</td>
                <td>{row['Entry 3']}</td>
                </tr>
                """

                table_html += """
                </tbody>

                </table>
                </div>
                </body>
                </html>
                """

                components.html(
                    table_html,
                    height=270,
                    scrolling=False
                )

                st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        
        # Add Score Button and Form
        with col1:
            if st.button("Add Score", key="add_score_btn"):
                st.session_state["show_add_form"] = True
                st.session_state["show_change_form"] = False

        # Change Subject Marks Button and Form
        with col2:
            if any(get_numeric_scores(scores) for scores in st.session_state["subject_scores"].values()):
                if st.button("Change Subject Marks", key="change_marks_btn"):
                    st.session_state["show_change_form"] = True
                    st.session_state["show_add_form"] = False
            else:
                st.info("No scores available yet.")

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
                    st.session_state["subject_scores"] = {
                        subject: get_numeric_scores(scores)
                        for subject, scores in st.session_state["subject_scores"].items()
                    }
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
                current_subject_scores = st.session_state["subject_scores"].get(subject_to_change, [])
                numeric_entry_indexes = [
                    index for index, score in enumerate(current_subject_scores)
                    if isinstance(score, (int, float))
                ]
                if numeric_entry_indexes:
                    entry_index = st.selectbox("Select Entry to Change", 
                                            range(1, len(numeric_entry_indexes) + 1),
                                            format_func=lambda x: f"Entry {x}")
                    actual_entry_index = numeric_entry_indexes[entry_index - 1]
                    new_score = st.number_input("New Score", min_value=0, max_value=100, 
                                            value=st.session_state["subject_scores"][subject_to_change][actual_entry_index])
                    submitted = st.form_submit_button("Update Score")
                    if submitted:
                        st.session_state["subject_scores"][subject_to_change][actual_entry_index] = new_score
                        st.session_state["subject_scores"] = {
                            subject: get_numeric_scores(scores)
                            for subject, scores in st.session_state["subject_scores"].items()
                        }
                        # Save updated scores to MongoDB
                        save_scores_to_mongodb(st.session_state.get("username", ""), st.session_state["subject_scores"])
                        st.success(f"Score updated successfully for {subject_to_change}!")
                        st.session_state["show_change_form"] = False
                        st.rerun()
                else:
                    st.warning("No scores available for this subject yet.")
                    st.form_submit_button("Close", disabled=True)
        else: 
            st.markdown("<br><br><br>", unsafe_allow_html=True)
    elif st.session_state["current_page"] == "study":
        st.title("Study Material")
        
        # Get user's class grade
        user = st.session_state.get("user")
        if user:
            class_grade = user.get("class_grade", "")

            drive_link = ""
            material_title = f"Class {class_grade} Study Material"
            available_subjects = []

            if class_grade == "12 Science":
                drive_link = "https://drive.google.com/drive/folders/1vz83zfD-BZa5JQ_kzH0sR7IR6d9gZciZ"
                material_title = "Class 12 Science Study Material"
                available_subjects = ["Physics", "Chemistry", "Mathematics", "Biology", "English", "Computer Science"]
            elif class_grade == "11 Science":
                drive_link = "https://drive.google.com/drive/folders/1L2gGlZGXgLyRbIrX8VmmUxOGavSoZ14b"
                material_title = "Class 11 Science Study Material"
                available_subjects = ["Physics", "Chemistry", "Mathematics", "Biology", "English"]
            elif class_grade == "11 Commerce":
                drive_link = "https://drive.google.com/drive/folders/1eDugXGA7xhEu2ntPeD9YBEoA8ZjmC2E6"
                material_title = "Class 11 Commerce Study Material"
                available_subjects = ["Business Studies", "Accountancy", "Economics", "Mathematics", "English", "Information Technology"]
            elif class_grade == "10":
                drive_link = "https://drive.google.com/drive/folders/1vNF3k7N2mO4p99F0qxe-FRG3P4d2ncEm"
                material_title = "Class 10 Study Material"
                available_subjects = ["Mathematics", "Science", "English", "Social Science"]
            elif class_grade == "9":
                drive_link = "https://drive.google.com/drive/folders/1irw_9irQa-gNa96NDp8bHtiMVS24XFL1"
                material_title = "Class 9 Study Material"
                available_subjects = ["Mathematics", "Science", "English", "Social Science", "Hindi"]
            elif class_grade == "8":
                drive_link = "https://drive.google.com/drive/folders/1PJrhYf3o7l4HIMtb2Efttm26aUsMLCpL"
                material_title = "Class 8 Study Material"
                available_subjects = ["Mathematics", "Science", "English", "Social Science", "Hindi"]
            elif class_grade == "7":
                drive_link = "https://drive.google.com/drive/folders/1psTVTOizf2ooZL3nrniJPVKuD9VtyXTx"
                material_title = "Class 7 Study Material"
                available_subjects = ["Mathematics", "Science", "English", "Social Science", "Hindi"]
            elif class_grade == "6":
                drive_link = "https://drive.google.com/drive/folders/1XK_mZLmVLv3AI3Bl7woOJvKwgkm2u6Hr"
                material_title = "Class 6 Study Material"
                available_subjects = ["Mathematics", "Science", "English", "Social Science", "Hindi"]
            elif class_grade == "12 Commerce":
                drive_link = "https://drive.google.com/drive/folders/1HetMbC0geyHfH35pcVyBWwdN_G1LouEv"
                material_title = "Class 12 Commerce Study Material"
                available_subjects = ["Business Studies", "Accountancy", "Economics", "Mathematics", "English", "Information Technology"]
            else:
                st.info(f"Study material for Class {class_grade} will be available soon!")

            if drive_link:
                safe_title = html.escape(material_title)
                safe_drive_link = html.escape(drive_link, quote=True)
                subject_items = "".join(
                    f"<div class='study-subject-item'><span>&#10004;</span>{html.escape(subject)}</div>"
                    for subject in available_subjects
                )

                st.markdown(f"""
                    <style>
                        .study-page-wrap {{
                            max-width: 980px;
                            margin: 0 auto;
                            padding: 10px 16px 34px;
                        }}
                        .study-hero-card {{
                            background: #ffffff;
                            border: 1px solid #e5e7eb;
                            border-radius: 18px;
                            box-shadow: 0 18px 40px rgba(15, 23, 42, 0.12);
                            padding: 34px 30px;
                            text-align: center;
                        }}
                        .study-icon {{
                            width: 72px;
                            height: 72px;
                            margin: 0 auto 16px;
                            border-radius: 20px;
                            background: #ecfdf5;
                            color: #16a34a;
                            display: flex;
                            align-items: center;
                            justify-content: center;
                            font-size: 34px;
                        }}
                        .study-hero-card h2 {{
                            margin: 0;
                            color: #111827;
                            font-size: 30px;
                            font-weight: 800;
                        }}
                        .study-hero-card p {{
                            margin: 12px auto 24px;
                            max-width: 560px;
                            color: #6b7280;
                            font-size: 16px;
                            line-height: 1.6;
                        }}
                        .study-open-btn {{
                            display: inline-block;
                            background: #16a34a;
                            color: #ffffff !important;
                            padding: 14px 28px;
                            border-radius: 12px;
                            font-size: 17px;
                            font-weight: 700;
                            text-decoration: none !important;
                            box-shadow: 0 10px 20px rgba(22, 163, 74, 0.24);
                        }}
                        .study-section-card {{
                            margin-top: 24px;
                            background: #ffffff;
                            border: 1px solid #e5e7eb;
                            border-radius: 16px;
                            box-shadow: 0 10px 24px rgba(15, 23, 42, 0.08);
                            padding: 24px;
                        }}
                        .study-section-card h3 {{
                            margin: 0 0 18px;
                            color: #111827;
                            font-size: 22px;
                            font-weight: 800;
                        }}
                        .study-subject-grid {{
                            display: grid;
                            grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
                            gap: 12px;
                        }}
                        .study-subject-item {{
                            background: #f9fafb;
                            border: 1px solid #eef2f7;
                            border-radius: 12px;
                            padding: 12px 14px;
                            color: #374151;
                            font-size: 15px;
                            font-weight: 600;
                        }}
                        .study-subject-item span {{
                            color: #16a34a;
                            font-weight: 800;
                            margin-right: 8px;
                        }}
                        .study-tip-card {{
                            margin-top: 24px;
                            background: #fefce8;
                            border: 1px solid #fde68a;
                            border-radius: 16px;
                            padding: 18px 20px;
                            color: #713f12;
                            box-shadow: 0 8px 18px rgba(113, 63, 18, 0.08);
                        }}
                        .study-tip-card strong {{
                            display: block;
                            margin-bottom: 6px;
                            color: #854d0e;
                            font-size: 17px;
                        }}
                    </style>
                    <div class="study-page-wrap">
                        <div class="study-hero-card">
                            <div class="study-icon">&#128218;</div>
                            <h2>{safe_title}</h2>
                            <p>Access all your organized study notes from one place.</p>
                            <a class="study-open-btn" href="{safe_drive_link}" target="_blank" rel="noopener">
                                &#128194; Open Study Material
                            </a>
                        </div>
                        <div class="study-section-card">
                            <h3>Available Subjects</h3>
                            <div class="study-subject-grid">
                                {subject_items}
                            </div>
                        </div>
                        <div class="study-tip-card">
                            <strong>&#128161; Study Tip</strong>
                            Revise these notes regularly to improve your academic performance.
                        </div>
                    </div>
                """, unsafe_allow_html=True)
    elif st.session_state["current_page"] == "predictor":

        st.title("🤖 AI Score Prediction")

        st.markdown(
            """
            <p style="font-size:28px; color:#6B7280; margin-top:-10px;">
                Predict your future academic performance based on your previous score history.
            </p>
            """,
            unsafe_allow_html=True
        )

        # Initialize prediction state
        if "predictions" not in st.session_state:
            st.session_state["predictions"] = None

        if "last_scores_state" not in st.session_state:
            st.session_state["last_scores_state"] = None

        subject_scores = st.session_state.get("subject_scores", {})
        numeric_subject_scores = {
            subject: get_numeric_scores(scores)
            for subject, scores in subject_scores.items()
        }

        # No scores available
        if not subject_scores or not any(numeric_subject_scores.values()):

            st.markdown("""
            <div style="
                background:#FFF7ED;
                border:1px solid #FDBA74;
                border-radius:14px;
                padding:25px;
                text-align:center;
                margin-top:20px;
            ">
                <h3>🔒 AI Prediction Locked</h3>
                <p>Please add your first score entries from the Performance History page.</p>
            </div>
            """, unsafe_allow_html=True)

            if st.button("➕ Add Score", use_container_width=True):
                st.session_state["current_page"] = "performance"
                st.session_state["show_add_form"] = True
                st.session_state["show_change_form"] = False
                st.rerun()

            st.stop()

        # Minimum entries among all subjects
        number_of_entries = min(len(scores) for scores in numeric_subject_scores.values())

        # Require minimum 3 entries
        if number_of_entries < 3:

            remaining = 3 - number_of_entries

            st.markdown(f"""
            <div style="
            background:#FFF7ED;
            border:1px solid #FDBA74;
            border-radius:12px;
            padding:25px;
            margin-top:20px;
            text-align:center;
            ">

            <h3 style="margin-bottom:10px;">
            🔒 AI Prediction Locked
            </h3>

            <p style="font-size:17px;">
            You need <b>{remaining}</b> more
            {'entry' if remaining == 1 else 'entries'}
            for each subject before AI Prediction becomes available.
            </p>

            <p style="color:#6B7280;">
            Current Progress: <b>{number_of_entries}/3 Entries</b>
            </p>

            </div>
            """, unsafe_allow_html=True)

            st.progress(number_of_entries / 3)

            if st.button("➕ Go to Performance History", use_container_width=True):
                st.session_state["current_page"] = "performance"
                st.rerun()

            st.stop()
            if st.button("Add Score", key="add_score_btn"):
                st.session_state["show_add_form"] = True
                st.session_state["show_change_form"] = False
                st.session_state["current_page"] = "performance"
                st.rerun()
        
            st.progress(number_of_entries / 3)

            st.markdown(f"**Progress : {number_of_entries}/3 Entries**")

            st.stop()

        current_scores_state = str(numeric_subject_scores)
        scores_changed = (
            current_scores_state != st.session_state["last_scores_state"]
        )

        if scores_changed or st.session_state["predictions"] is None:

            with st.spinner("Predicting scores... Please wait..."):

                st.session_state["predictions"] = train_and_predict(numeric_subject_scores)
                st.session_state["last_scores_state"] = current_scores_state

        # ---------------- Display ----------------

        st.markdown("""
        <div style="
        background:linear-gradient(135deg,#00000f,#1e3c72);
        padding:22px;
        border-radius:14px;
        color:white;
        text-align:center;
        margin-bottom:20px;
        box-shadow:0 8px 20px rgba(0,0,0,.15);
        ">
        <h2 style="margin:0;">📊 AI Prediction Results</h2>
        <p style="margin-top:8px;font-size:16px;">
        Your predicted performance based on previous score history
        </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("## 📚 Subject-wise Predictions")

        predictions = st.session_state["predictions"]
        prediction_items = list(predictions.items())

        for i in range(0, len(prediction_items), 2):

            col1, col2 = st.columns(2)

            for col, (subject, prediction) in zip(
                [col1, col2],
                prediction_items[i:i+2]
            ):

                with col:

                    if isinstance(prediction, str):

                        st.warning(f"{subject}: {prediction}")

                    else:

                        if prediction >= 70:
                            bg = "#ECFDF5"
                            border = "#22C55E"
                            status = "🟢 Excellent"
                            recommendation = "Maintain consistency and attempt advanced problems."

                        elif prediction >= 50:
                            bg = "#FEFCE8"
                            border = "#EAB308"
                            status = "🟡 Average"
                            recommendation = "Increase practice and solve previous year questions."

                        else:
                            bg = "#FEF2F2"
                            border = "#EF4444"
                            status = "🔴 Needs Improvement"
                            recommendation = "Focus on fundamentals, revise NCERT chapters, and practice daily."

                        st.markdown(f"""
                        <div style="
                        background:{bg};
                        border-left:6px solid {border};
                        padding:18px;
                        border-radius:12px;
                        margin-bottom:18px;
                        box-shadow:0 4px 12px rgba(0,0,0,.08);
                        ">

                        <h4 style="margin-bottom:8px;">📘 {subject}</h4>

                        <h2 style="margin:0;color:#1F2937;">
                        {prediction}/100
                        </h2>

                        <p style="font-weight:bold;">
                        {status}
                        </p>

                        <hr>

                        <b>Recommendation</b>

                        <p>{recommendation}</p>

                        </div>
                        """, unsafe_allow_html=True)

        valid_predictions = [
            pred
            for pred in st.session_state["predictions"].values()
            if isinstance(pred, (int, float))
        ]

        if valid_predictions:

            avg_prediction = round(
                sum(valid_predictions) / len(valid_predictions),
                2,
            )

            highest_subject = max(
                st.session_state["predictions"],
                key=lambda x: st.session_state["predictions"][x]
                if isinstance(st.session_state["predictions"][x], (int, float))
                else -1
            )

            lowest_subject = min(
                st.session_state["predictions"],
                key=lambda x: st.session_state["predictions"][x]
                if isinstance(st.session_state["predictions"][x], (int, float))
                else 999
            )

        st.markdown(f"""
    <div style="display:flex; gap:20px; margin-top:15px;">

    <div style="
        flex:1;
        background:#EFF6FF;
        border:1px solid #BFDBFE;
        border-radius:14px;
        padding:20px;
        text-align:center;
        box-shadow:0 4px 12px rgba(0,0,0,.08);
    ">
        <div style="font-size:15px;color:#6B7280;">🎯 Average Prediction</div>
        <div style="font-size:34px;font-weight:bold;color:#2563EB;margin-top:10px;">
            {avg_prediction}
        </div>
    </div>

    <div style="
        flex:1;
        background:#ECFDF5;
        border:1px solid #A7F3D0;
        border-radius:14px;
        padding:20px;
        text-align:center;
        box-shadow:0 4px 12px rgba(0,0,0,.08);
    ">
        <div style="font-size:15px;color:#6B7280;">🏆 Strongest Subject</div>
        <div style="font-size:30px;font-weight:bold;color:#16A34A;margin-top:10px;">
            {highest_subject}
        </div>
    </div>

    <div style="
        flex:1;
        background:#FEF2F2;
        border:1px solid #FECACA;
        border-radius:14px;
        padding:20px;
        text-align:center;
        box-shadow:0 4px 12px rgba(0,0,0,.08);
    ">
        <div style="font-size:15px;color:#6B7280;">📚 Focus Area</div>
        <div style="font-size:30px;font-weight:bold;color:#DC2626;margin-top:10px;">
            {lowest_subject}
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        recommendations = []

        for subject, prediction in st.session_state["predictions"].items():

            if isinstance(prediction, str):
                continue

            if prediction < 50:

                recommendations.append(
                    f"🔴 Focus more on **{subject}** fundamentals."
                )

            elif prediction < 70:

                recommendations.append(
                    f"🟡 Practice additional questions in **{subject}**."
                )

        if not recommendations:

            recommendations.append(
                "🟢 Excellent performance. Maintain your consistency."
            )

        for recommendation in recommendations:
            st.info(recommendation)
    elif st.session_state["current_page"] == "analytics":
        st.markdown("""
        <div style="
        background:linear-gradient(135deg,#ffffff,#f8fafc);
        padding:28px;
        border-radius:18px;
        border:1px solid #e5e7eb;
        box-shadow:0 8px 20px rgba(0,0,0,.08);
        margin-bottom:25px;
        ">
        <p style="
        color:#111827;
        font-size:15px;
        font-weight:700;
        letter-spacing:1px;
        text-transform:uppercase;
        margin-bottom:8px;
        ">
        ANALYTICS
        </p>

        <h2 style="
        margin:0;
        font-size:32px;
        font-weight:700;
        color:#111827;
        ">
        Analytics Dashboard
        </h2>

        <p style="
        margin-top:10px;
        font-size:16px;
        color:#6B7280;
        ">
        Visualize academic performance, identify trends, and gain actionable insights.
        </p>
        </div>
        """, unsafe_allow_html=True)
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
               background:#ffffff;
                padding:24px;
                border-radius:18px;
                border:1px solid #e5e7eb;
                min-height:220px;
                box-shadow:0 4px 12px rgba(0,0,0,0.08);
                transition:all .3s ease;
            ">
                <h3 style="
                    color:#2563EB;
                    font-size:24px;
                    font-weight:700;
                    margin-bottom:18px;
                    ">
                    📊 Performance Analytics
                </h3>
                <p style="
                font-size:16px;
                line-height:1.7;
                color:#4B5563;
                margin:0;
                ">
                Track academic progress and monitor performance trends.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_b:
                st.markdown("""
                <div style="
                background:#ffffff;
                padding:24px;
                border-radius:18px;
                border:1px solid #e5e7eb;
                min-height:220px;
                box-shadow:0 4px 12px rgba(0,0,0,0.08);
                transition:all .3s ease;
                ">
                <h3 style="
                color:#16A34A;
                font-size:24px;
                font-weight:700;
                margin-bottom:18px;
                ">
                🤖 AI Score Prediction
                </h3>
                <p style="
                font-size:16px;
                line-height:1.7;
                color:#4B5563;
                margin:0;
                ">
                Predict future scores using AI-powered analysis.
                </p>
            </div>
            """, unsafe_allow_html=True)

        with col_c:
            st.markdown("""
                <div style="
                background:#ffffff;
                padding:24px;
                border-radius:18px;
                border:1px solid #e5e7eb;
                min-height:220px;
                box-shadow:0 4px 12px rgba(0,0,0,0.08);
                transition:all .3s ease;
                ">
                <h3 style="
                color:#EA580C;
                font-size:24px;
                font-weight:700;
                margin-bottom:18px;
                ">
                📚 Study Material
                </h3>
                <p style="
                font-size:16px;
                line-height:1.7;
                color:#4B5563;
                margin:0;
                ">
                Access class-wise learning resources and materials.
                </p>
            </div>
            """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)


        st.markdown("""
        <div style="
        padding:8px 0 18px 0;
        ">
        <h2 style="
        margin:0;
        color:#111827;
        font-size:28px;
        font-weight:700;
        ">
        Trusted Learning Insights
        </h2>

        <p style="
        margin-top:8px;
        font-size:16px;
        color:#6B7280;
        ">
        Helping students track progress and improve performance.
        </p>
        </div>
        """, unsafe_allow_html=True)

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

        card = st.container()

        with card:
        
            if st.session_state["page"] == "login":
                st.markdown("""
                <div style="text-align:center; padding-bottom:18px;">
                    <h2 style="margin-bottom:8px; color:#111827; font-size:32px; font-weight:700;">
                        Welcome Back
                    </h2>
                    <p>
                        Sign in to continue your learning journey.
                    </p>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("""
                    <div style="text-align:center; padding:5px; color:#000000; font-style:bold; font-size:30px;">
                    𝓛𝓸𝓰𝓲𝓷

                """,
                  unsafe_allow_html=True)
                username = st.text_input(
                    "Username",
                    placeholder="Enter your username",
                    key="login_username"
                )

                password = st.text_input(
                    "Password",
                    type="password",
                    placeholder="Enter your password",
                    key="login_password"
                )
                
                col_login, col_signup = st.columns(2)
                
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

                            # Fetch the newly created user
                            new_user = users_collection.find_one({"username": username.strip()})

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
