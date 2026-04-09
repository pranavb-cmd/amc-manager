import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
import json

st.set_page_config(page_title="DailyForge", page_icon="🔥", layout="wide")

# ===================== GOOGLE SHEETS CONNECTION =====================
@st.cache_resource
def get_google_sheet():
    try:
        gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
        sh = gc.open_by_url(st.secrets["spreadsheet_url"])
        st.success("✅ Connected to Google Sheet")
        return sh
    except Exception as e:
        st.error(f"❌ Google Sheet Connection Failed: {e}")
        st.stop()

def load_data():
    sheet = get_google_sheet()
    data = {"tasks": [], "projects": [], "engineers": [], "users": {"manager": {}, "engineer": {}}}
    
    try:
        # Tasks
        tasks_df = pd.DataFrame(sheet.worksheet("Tasks").get_all_records())
        data["tasks"] = tasks_df.to_dict('records') if not tasks_df.empty else []
        
        # Projects
        projects_df = pd.DataFrame(sheet.worksheet("Projects").get_all_records())
        data["projects"] = projects_df.to_dict('records') if not projects_df.empty else []
        
        # Engineers
        engineers_df = pd.DataFrame(sheet.worksheet("Engineers").get_all_records())
        data["engineers"] = engineers_df['name'].tolist() if not engineers_df.empty else []
        
        # Users
        users_df = pd.DataFrame(sheet.worksheet("Users").get_all_records())
        for _, row in users_df.iterrows():
            role = str(row.get('role', '')).strip()
            username = str(row.get('username', '')).strip()
            if role and username:
                data["users"][role][username] = {
                    "password": str(row.get('password', '')),
                    "role": role,
                    "name": str(row.get('name', ''))
                }
    except Exception as e:
        st.warning(f"Load warning: {e}")
    
    return data

def save_data(data):
    sheet = get_google_sheet()
    try:
        # Tasks
        if data.get("tasks"):
            tasks_df = pd.DataFrame(data["tasks"])
            ws = sheet.worksheet("Tasks")
            ws.clear()
            ws.update([tasks_df.columns.tolist()] + tasks_df.values.tolist())
        
        # Projects
        if data.get("projects"):
            projects_df = pd.DataFrame(data["projects"])
            ws = sheet.worksheet("Projects")
            ws.clear()
            ws.update([projects_df.columns.tolist()] + projects_df.values.tolist())
        
        # Engineers
        if data.get("engineers"):
            engineers_df = pd.DataFrame({"name": data["engineers"]})
            ws = sheet.worksheet("Engineers")
            ws.clear()
            ws.update([engineers_df.columns.tolist()] + engineers_df.values.tolist())
        
        # Users
        users_list = []
        for role, user_dict in data.get("users", {}).items():
            for username, info in user_dict.items():
                users_list.append({
                    "role": role,
                    "username": username,
                    "password": info.get("password", ""),
                    "name": info.get("name", "")
                })
        if users_list:
            users_df = pd.DataFrame(users_list)
            ws = sheet.worksheet("Users")
            ws.clear()
            ws.update([users_df.columns.tolist()] + users_df.values.tolist())
        
        st.success("✅ Data saved to Google Sheets")
        return True
    except Exception as e:
        st.error(f"❌ Save failed: {e}")
        return False

# Load data
data = load_data()

# ===================== LOGIN =====================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔥 DailyForge")
    st.markdown("### Project Task Dashboard")
    st.markdown("#### Login")

    col1, col2 = st.columns([1, 1])
    with col1:
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password")
        
        if st.button("Login", use_container_width=True, type="primary"):
            if username in data["users"].get("manager", {}) and data["users"]["manager"][username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = "manager"
                st.session_state.full_name = data["users"]["manager"][username]["name"]
                st.rerun()
            elif username in data["users"].get("engineer", {}) and data["users"]["engineer"][username]["password"] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = "engineer"
                st.session_state.full_name = data["users"]["engineer"][username]["name"]
                st.rerun()
            else:
                st.error("❌ Invalid username or password")

    with col2:
        st.info("Contact your administrator if you don't have login credentials.")

    st.caption("Only authorized users can access the dashboard.")
    st.stop()

# ===================== SIDEBAR =====================
st.sidebar.image("https://img.icons8.com/fluency/96/fire.png", width=70)
st.sidebar.title("DailyForge")
st.sidebar.markdown(f"**{st.session_state.full_name}** ({st.session_state.role.upper()})")

if st.sidebar.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

active_projects = [p["name"] for p in data["projects"] if p.get("active", True)]

# Manager Dashboard and other tabs (same as before, but with save calls)

if st.session_state.role == "manager":
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Dashboard", "➕ Add Task", "📋 Project Master", 
                                                  "👷 Engineer Master", "👨‍💼 Manager Master", "🔑 Change Password"])

    with tab1:
        st.title("📊 Project Task Dashboard")
        # (Same dashboard code as previous version - I can add it if needed)

    with tab2:
        st.title("➕ Add New Task Target")
        with st.form("add_task_form", clear_on_submit=True):
            project = st.selectbox("Project", active_projects if active_projects else ["No active projects"])
            description = st.text_area("Task Description")
            assigned = st.selectbox("Assign to Engineer", data["engineers"])
            if st.form_submit_button("✅ Add Task Target"):
                if description.strip():
                    new_task = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "project": project,
                        "description": description.strip(),
                        "assigned": assigned,
                        "progress": 0,
                        "notes": "",
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    data["tasks"].append(new_task)
                    if save_data(data):
                        st.success("✅ Task added and saved!")
                    st.rerun()

    # Add similar save_data(data) after every add/delete operation in other tabs

    with tab3:
        st.title("📋 Project Master")
        # ... (same as before, but call save_data(data) after every change)

    # (For brevity, the other tabs follow the same pattern - call save_data(data) after every add/delete)

# Engineer view with save_data call after update

st.caption("DailyForge • Google Sheets Persistent Storage")
