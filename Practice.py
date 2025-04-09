import streamlit as st
from pymongo import MongoClient
import bcrypt
import plotly.graph_objects as go
import pandas as pd
import tensorflow as tf
import numpy as np

# Set page config at the beginning
st.set_page_config(page_title="AI Learning Platform", layout="wide")

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")  # Update if using a different connection
db = client["education_system"]
users_collection = db["users"]

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password, hashed_password):
    return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))

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

def create_navigation():
    st.markdown("""
        <div class="nav-container">
            <div class="site-name">
                AI Learning Platform
            </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Hidden buttons for state management
    col1, col2, col3, col4 = st.columns(4)
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
        if st.button("Logout", key="nav_logout"):
            st.session_state["page"] = "login"
            st.session_state.pop("current_page", None)
            st.session_state.pop("marks_displayed", None)
            st.rerun()

def display_dashboard(username):
    user = users_collection.find_one({"username": username})
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

def train_and_predict(subject_scores):
    predictions = {}
    for subject, scores in subject_scores.items():
        if len(scores) < 2:
            predictions[subject] = "Not enough data to make a prediction."
            continue

        # Calculate mean score for the subject
        mean_score = sum(scores) / len(scores)

        # Convert to a DataFrame
        df = pd.DataFrame(scores, columns=['score'])
        df['next_score'] = df['score'].shift(-1)
        df.dropna(inplace=True)

        # Split the data
        X = df[['score']].values
        y = df['next_score'].values

        # Define a simpler model
        model = tf.keras.Sequential([
            tf.keras.layers.Dense(5, activation='relu', input_shape=(1,)),
            tf.keras.layers.Dense(1)
        ])

        # Compile the model with a larger learning rate
        model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.01), loss='mse')

        # Train the model with fewer epochs
        model.fit(X, y, epochs=10, verbose=0)

        # Predict the next score
        last_score = np.array([scores[-1]]).reshape(-1, 1)
        predicted_score = model.predict(last_score, verbose=0)
        
        # Get the raw prediction
        raw_prediction = float(predicted_score[0][0])
        
        # Ensure prediction is between mean and 95
        final_prediction = max(min(raw_prediction, 95), mean_score)
        
        # Round the prediction to 2 decimal places
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

def display_dashboard_page():
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "dashboard"

    # Create navigation
    create_navigation()
    
    st.markdown("<hr>", unsafe_allow_html=True)

    # Load scores from MongoDB when initializing
    if "subject_scores" not in st.session_state:
        st.session_state["subject_scores"] = load_scores_from_mongodb(st.session_state.get("username", ""))

    # Display current page content
    if st.session_state["current_page"] == "dashboard":
        display_dashboard(st.session_state.get("username", ""))
    elif st.session_state["current_page"] == "performance":
        st.title("Performance History")
        
        # Get user's class grade
        user = users_collection.find_one({"username": st.session_state.get("username", "")})
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
        user = users_collection.find_one({"username": st.session_state.get("username", "")})
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

        if "subject_scores" not in st.session_state:
            st.info("Please enter your scores for each subject.")
            # Get user's class grade
            user = users_collection.find_one({"username": st.session_state.get("username", "")})
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
            
            # Display average prediction
            with col2:
                valid_predictions = [pred for pred in st.session_state["predictions"].values() if isinstance(pred, (int, float))]
                if valid_predictions:
                    avg_prediction = round(sum(valid_predictions) / len(valid_predictions), 2)
                    st.markdown("### Overall Prediction")
                    st.metric("Average Predicted Score", f"{avg_prediction}")
                    
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
        st.title("🌟 AI Learning Platform")
        st.subheader("Features of Product")
        
        features = [
            "✅ Personalized Learning Paths",
            "✅ Smart Study Material Recommendations",
            "✅ Performance History & Analytics",
            "✅ AI-Powered Exam Predictions",
            "✅ Secure Login & User Profiles"
        ]
        
        for feature in features:
            st.write(feature)

    # Right Side - Login/Signup Form
    with col2:
        st.markdown("<div class='login-box'>", unsafe_allow_html=True)
        
        if st.session_state["page"] == "login":
            st.subheader("Login")
            username = st.text_input("User ID", placeholder="Enter User ID", key="login_username")
            password = st.text_input("Password", type="password", placeholder="Enter Password", key="login_password")
            
            col_login, col_signup = st.columns([1, 1])
            
            with col_login:
                if st.button("Login"):
                    user = users_collection.find_one({"username": username})
                    if user and verify_password(password, user['password']):
                        st.session_state["page"] = "dashboard"
                        st.session_state["username"] = username
                        st.rerun()
                    else:
                        st.error("Invalid User ID or Password.")
            
            with col_signup:
                if st.button("Sign Up"):
                    st.session_state["page"] = "signup"
                    st.rerun()
        
        elif st.session_state["page"] == "signup":
            st.subheader("Sign Up")
            full_name = st.text_input("Full Name", placeholder="Enter Full Name", key="signup_full_name")
            class_grade = st.selectbox("Class/Grade", ["6", "7", "8", "9", "10", "11 Science", "11 Commerce", "12 Science", "12 Commerce"], key="signup_class")
            username = st.text_input("User ID", placeholder="Enter User ID", key="signup_username")
            password = st.text_input("Create Password", type="password", placeholder="Enter Password", key="signup_password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm Password", key="signup_confirm_password")
            
            if st.button("Create Account"):
                if password == confirm_password:
                    if users_collection.find_one({"username": username}):
                        st.error("User ID already exists. Choose a different one.")
                    else:
                        hashed_password = hash_password(password)
                        users_collection.insert_one({"full_name": full_name, "class_grade": class_grade, "username": username, "password": hashed_password})
                        st.success("Account created successfully! Please log in.")
                        st.session_state["page"] = "login"
                        st.rerun()
                else:
                    st.error("Passwords do not match.")
            
            if st.button("Back to Login"):
                st.session_state["page"] = "login"
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
