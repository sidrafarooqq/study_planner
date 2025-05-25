import streamlit as st
import json
from pathlib import Path
from typing import List

# -------- File path for users --------
USER_FILE = Path("users.json")

# -------- Load users from file --------
def load_users():
    if USER_FILE.exists():
        with open(USER_FILE, "r") as f:
            return json.load(f)
    return {}

# -------- Save users to file --------
def save_users(users):
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# ------------ OOP Classes ---------------------
class User:
    def __init__(self, username): # Corrected: __init__
        self.username = username
        self.study_plans = []

class Subject:
    def __init__(self, name, hours_needed): # Corrected: __init__
        self.name = name
        self.hours_needed = hours_needed

class StudyPlan:
    def __init__(self, subjects: List[Subject], days: int):
        self.subjects = subjects
        self.days = days

    def generate_plan(self):
        total_hours = sum(sub.hours_needed for sub in self.subjects)
        
        # Avoid division by zero if days is 0 or less
        if self.days <= 0:
            return {"Error": "Number of days must be at least 1."}
        
        # Calculate hours per day, ensuring at least 1 hour if subjects are present
        hours_per_day = max(1, total_hours // self.days) if total_hours > 0 else 0

        plan = {}
        current_subject_index = 0
        
        for day_num in range(1, self.days + 1):
            day_key = f'Day {day_num}'
            plan[day_key] = []
            
            hours_assigned_today = 0
            while hours_assigned_today < hours_per_day and current_subject_index < len(self.subjects):
                subject = self.subjects[current_subject_index]
                
                # Assign remaining hours for the subject or fill up hours_per_day for this day
                hours_to_assign = min(subject.hours_needed, hours_per_day - hours_assigned_today)
                
                plan[day_key].append(f"{subject.name} - {hours_to_assign} hrs")
                
                subject.hours_needed -= hours_to_assign # Deduct assigned hours from subject
                hours_assigned_today += hours_to_assign
                
                if subject.hours_needed <= 0: # If subject is completed
                    current_subject_index += 1 # Move to next subject
                
                # If we've assigned all hours for this day, break and move to next day
                if hours_assigned_today >= hours_per_day:
                    break
            
            # If there are still subjects left but we couldn't assign more today, and it's the last day,
            # assign remaining hours to the last day's plan.
            if day_num == self.days and current_subject_index < len(self.subjects):
                remaining_total_hours = sum(sub.hours_needed for sub in self.subjects[current_subject_index:])
                if remaining_total_hours > 0:
                    plan[day_key].append(f"Remaining Subjects - {remaining_total_hours} hrs (Adjusted)")

        plan = {}
        subject_cycle_index = 0
        for day_num in range(1, self.days + 1):
            if not self.subjects:
                break # No subjects to plan
            
            # Assign the next subject in a round-robin fashion
            subject_to_assign = self.subjects[subject_cycle_index % len(self.subjects)]
            
            # For simplicity, let's just assign the subject with its total hours needed for that "slot"
            # A truly smart planner would break down hours per day per subject.
            # Given your initial `f"{subject.name} - {hours} hrs"`, this seems closer to intent.
            plan[f'Day {day_num}'] = f"{subject_to_assign.name} - {subject_to_assign.hours_needed} hrs"
            
            subject_cycle_index += 1

        return plan


# ------------ Streamlit App ---------------------
st.set_page_config(page_title="StudyNest", page_icon="📘")

st.title("📘 StudyNest - Study Plan Generator")

# ------------ Authentication System ------------
users_db = load_users()

auth_choice = st.sidebar.selectbox("Login / Signup", ["Signup", "Login"])
username = st.sidebar.text_input("Username")
password = st.sidebar.text_input("Password", type="password")

# Initialize session state variables
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# Signup process
if auth_choice == "Signup":
    if st.sidebar.button("Create Account"):
        if username.strip() == "" or password.strip() == "":
            st.sidebar.error("Username and password cannot be empty.")
        elif username in users_db:
            st.sidebar.error("Username already exists.")
        else:
            users_db[username] = password
            save_users(users_db)
            st.sidebar.success("Account created! You can now login.")

# Login process
elif auth_choice == "Login":
    if st.sidebar.button("Login"):
        if username in users_db and users_db[username] == password:
            st.sidebar.success("Login successful!")
            st.session_state.logged_in = True
            st.session_state.current_user = username
        else:
            st.sidebar.error("Invalid username or password")

# ------------ Main App After Login ------------
if st.session_state.logged_in:
    st.success(f"Welcome, {st.session_state.current_user}!")
    st.subheader("📌 Add Your Subjects")

    subject_list = []
    # Using session state to store num_subjects to avoid resetting on re-runs
    if "num_subjects" not in st.session_state:
        st.session_state.num_subjects = 1

    st.session_state.num_subjects = st.number_input(
        "How many subjects?",
        min_value=1, max_value=10, step=1,
        value=st.session_state.num_subjects,
        key="num_subjects_input"
    )
    
    # Store subject inputs in session state to persist across reruns
    if "subject_inputs" not in st.session_state:
        st.session_state.subject_inputs = {}

    for i in range(st.session_state.num_subjects):
        # Initialize default values if not present
        if f"name_{i}" not in st.session_state.subject_inputs:
            st.session_state.subject_inputs[f"name_{i}"] = ""
        if f"hours_{i}" not in st.session_state.subject_inputs:
            st.session_state.subject_inputs[f"hours_{i}"] = 1

        name = st.text_input(
            f"Subject {i+1} name:", 
            value=st.session_state.subject_inputs[f"name_{i}"],
            key=f"name_{i}_input" # Use a unique key for the widget
        )
        hours = st.number_input(
            f"Hours needed for {name}:", 
            min_value=1, step=1, 
            value=st.session_state.subject_inputs[f"hours_{i}"],
            key=f"hours_{i}_input" # Use a unique key for the widget
        )
        
        # Update session state
        st.session_state.subject_inputs[f"name_{i}"] = name
        st.session_state.subject_inputs[f"hours_{i}"] = hours

        if name and hours: # Ensure both inputs are valid before adding
            subject_list.append(Subject(name, hours))

    days = st.number_input("In how many days you want to complete it?", min_value=1, step=1)

    if st.button("🧠 Generate Study Plan"):
        if not subject_list:
            st.warning("Please enter your subjects first.")
        elif days <= 0:
            st.warning("Number of days must be at least 1.")
        else:
            plan_generator = StudyPlan(subject_list, days) # Changed variable name from 'plan' to 'plan_generator' to avoid confusion
            study_plan_output = plan_generator.generate_plan() # Changed variable name from 'study_plan'
            
            if "Error" in study_plan_output:
                st.error(study_plan_output["Error"])
            else:
                st.success("✅ Your Study Plan is Ready!")
                for day, task in study_plan_output.items():
                    st.write(f"*{day}:* {task}")

            if st.checkbox("💳 Simulate Premium Payment ($10)"):
                st.info("✅ Payment Successful! Premium unlocked (PDF download coming soon)")

else:
    st.info("Please login to use the app.")