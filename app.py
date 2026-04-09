import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread

st.set_page_config(page_title="DailyForge", page_icon="🔥", layout="wide")

# ===================== GOOGLE SHEETS =====================
@st.cache_resource
def get_google_sheet():
    gc = gspread.service_account_from_dict(st.secrets["gcp_service_account"])
    return gc.open_by_url(st.secrets["spreadsheet_url"])

def load_data():
    sheet = get_google_sheet()
    data = {"tasks": [], "projects": [], "engineers": [], "users": {"manager": {}, "engineer": {}}}
    
    try:
        # Tasks
        df = pd.DataFrame(sheet.worksheet("Tasks").get_all_records())
        data["tasks"] = df.to_dict('records') if not df.empty else []
        
        # Projects
        df = pd.DataFrame(sheet.worksheet("Projects").get_all_records())
        data["projects"] = df.to_dict('records') if not df.empty else []
        
        # Engineers
        df = pd.DataFrame(sheet.worksheet("Engineers").get_all_records())
        data["engineers"] = df['name'].tolist() if not df.empty else []
        
        # Users
        df = pd.DataFrame(sheet.worksheet("Users").get_all_records())
        for _, row in df.iterrows():
            role = str(row.get('role','')).strip()
            username = str(row.get('username','')).strip()
            if role and username:
                data["users"][role][username] = {
                    "password": str(row.get('password','')),
                    "role": role,
                    "name": str(row.get('name',''))
                }
    except Exception as e:
        st.warning(f"Load issue: {str(e)[:100]}")
    
    return data

def save_data(data):
    try:
        sheet = get_google_sheet()
        
        # Tasks
        if data["tasks"]:
            df = pd.DataFrame(data["tasks"])
            ws = sheet.worksheet("Tasks")
            ws.clear()
            ws.update([df.columns.tolist()] + df.values.tolist())
        
        # Projects
        if data["projects"]:
            df = pd.DataFrame(data["projects"])
            ws = sheet.worksheet("Projects")
            ws.clear()
            ws.update([df.columns.tolist()] + df.values.tolist())
        
        # Engineers
        if data["engineers"]:
            df = pd.DataFrame({"name": data["engineers"]})
            ws = sheet.worksheet("Engineers")
            ws.clear()
            ws.update([df.columns.tolist()] + df.values.tolist())
        
        # Users
        users_list = []
        for role, udict in data["users"].items():
            for uname, info in udict.items():
                users_list.append({
                    "role": role,
                    "username": uname,
                    "password": info.get("password", ""),
                    "name": info.get("name", "")
                })
        if users_list:
            df = pd.DataFrame(users_list)
            ws = sheet.worksheet("Users")
            ws.clear()
            ws.update([df.columns.tolist()] + df.values.tolist())
        
        return True
    except Exception as e:
        st.error(f"Save Error: {str(e)}")
        return False

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
        username = st.text_input("Username", placeholder="Enter username")
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
        st.info("Contact administrator for credentials.")
    st.stop()

# ===================== SIDEBAR =====================
st.sidebar.image("https://img.icons8.com/fluency/96/fire.png", width=70)
st.sidebar.title("DailyForge")
st.sidebar.markdown(f"**{st.session_state.full_name}**")

if st.sidebar.button("Logout"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# ===================== MAIN APP =====================
if st.session_state.role == "manager":
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📊 Dashboard", "➕ Add Task", "📋 Project Master", 
                                                  "👷 Engineer Master", "👨‍💼 Manager Master", "🔑 Change Password"])

    with tab1:
        st.title("📊 Dashboard")
        st.info("Dashboard view coming soon...")

    with tab2:
        st.title("➕ Add New Task")
        with st.form("add_task", clear_on_submit=True):
            project = st.selectbox("Project", [p["name"] for p in data["projects"] if p.get("active", True)])
            desc = st.text_area("Task Description")
            eng = st.selectbox("Assign Engineer", data["engineers"])
            if st.form_submit_button("Add Task"):
                if desc:
                    new_task = {
                        "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                        "date": datetime.now().strftime("%Y-%m-%d"),
                        "project": project,
                        "description": desc,
                        "assigned": eng,
                        "progress": 0,
                        "notes": "",
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    data["tasks"].append(new_task)
                    if save_data(data):
                        st.success("✅ Task added successfully!")
                    st.rerun()

    with tab3:  # Project Master
        st.title("📋 Project Master")
        for i, p in enumerate(data["projects"]):
            col1, col2, col3 = st.columns([3,1,1])
            col1.write(f"{p['name']} {'(Active)' if p.get('active', True) else '(Ended)'}")
            if col2.button("Mark Ended", key=f"endp_{i}"):
                data["projects"][i]["active"] = False
                save_data(data)
                st.success("Project marked ended")
                st.rerun()
            if col3.button("Delete", key=f"delp_{i}"):
                st.session_state[f"cp_{i}"] = True
                st.rerun()
            if st.session_state.get(f"cp_{i}", False):
                if st.button("Confirm Delete", key=f"cdp_{i}"):
                    del data["projects"][i]
                    save_data(data)
                    st.success("Project deleted")
                    del st.session_state[f"cp_{i}"]
                    st.rerun()

        new_p = st.text_input("New Project")
        if st.button("Add Project"):
            if new_p:
                data["projects"].append({"name": new_p, "active": True})
                save_data(data)
                st.success("✅ Project added!")
                st.rerun()

    with tab4:  # Engineer Master
        st.title("👷 Engineer Master")
        for i, eng in enumerate(data["engineers"]):
            col1, col2 = st.columns([4,1])
            col1.write(eng)
            if col2.button("Delete", key=f"dele_{i}"):
                st.session_state[f"ce_{i}"] = True
                st.rerun()
            if st.session_state.get(f"ce_{i}", False):
                if st.button("Confirm Delete", key=f"cde_{i}"):
                    for u, info in list(data["users"]["engineer"].items()):
                        if info["name"] == eng:
                            del data["users"]["engineer"][u]
                            break
                    del data["engineers"][i]
                    save_data(data)
                    st.success("✅ Engineer deleted!")
                    del st.session_state[f"ce_{i}"]
                    st.rerun()

        st.subheader("Add New Engineer")
        with st.form("add_eng", clear_on_submit=True):
            name = st.text_input("Full Name")
            uname = st.text_input("Username")
            pwd = st.text_input("Password", value="123456", type="password")
            if st.form_submit_button("Add Engineer"):
                if name and uname:
                    u = uname.lower().strip()
                    if u not in data["users"]["manager"] and u not in data["users"]["engineer"]:
                        data["engineers"].append(name)
                        data["users"]["engineer"][u] = {"password": pwd, "role": "engineer", "name": name}
                        if save_data(data):
                            st.success(f"✅ Engineer **{name}** added! Username: `{u}`")
                        st.rerun()
                    else:
                        st.error("Username already exists")

    # Manager Master and Change Password tabs can be added similarly

    with tab5:
        st.title("Manager Master")
        st.info("Manager Master - Add functionality similar to Engineer Master")

    with tab6:
        st.title("Change Password")
        st.info("Change Password tab")

else:
    st.title("My Tasks")
    st.info("Engineer view coming in next update")

st.caption("DailyForge - Google Sheets Version")
