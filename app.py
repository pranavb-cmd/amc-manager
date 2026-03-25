import streamlit as st
import json
import datetime
import os
from datetime import date

DATA_FILE = "amc_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        st.error(f"Save failed: {e}")
        return False

st.set_page_config(page_title="AMC Visit Manager", page_icon="🔧", layout="wide")
st.title("🔧 AMC Maintenance Visit Manager")
st.caption("Add clients • Track visits • Mark completed")

data = load_data()

menu = st.sidebar.selectbox(
    "Menu",
    ["Add New Client AMC", "List All Clients", "Check Due Visits", "Mark Visit Completed"]
)

if menu == "Add New Client AMC":
    st.header("➕ Add New Client AMC")
    
    with st.form("add_amc_form", clear_on_submit=True):
        name = st.text_input("Customer Name *")
        po = st.text_input("PO Number *")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("AMC Start Date *", value=date.today())
        with col2:
            end_date = st.date_input("AMC End Date *", value=date(2027, 12, 31))
        
        frequency = st.selectbox("Visit Frequency", ["quarterly", "six-monthly", "other"])
        
        st.subheader("Visit Schedule")
        num_visits = st.number_input("Number of visits in this AMC", min_value=1, max_value=20, value=4)
        
        visits = []
        for i in range(1, int(num_visits) + 1):
            st.write(f"**Visit #{i}**")
            c1, c2 = st.columns(2)
            with c1:
                due_start = st.date_input(f"Due Start (Visit {i})", key=f"vs{i}")
            with c2:
                due_end = st.date_input(f"Due End (Visit {i})", key=f"ve{i}")
            if due_start and due_end:
                visits.append({
                    "visit_number": i,
                    "due_start": due_start.strftime("%Y-%m-%d"),
                    "due_end": due_end.strftime("%Y-%m-%d"),
                    "status": "pending"
                })
        
        submitted = st.form_submit_button("💾 Save New AMC", type="primary")
        
        if submitted:
            if not name or not po or not visits:
                st.error("❌ Please fill Customer Name, PO Number and at least one visit.")
            else:
                client = {
                    "customer_name": name.strip(),
                    "po_number": po.strip(),
                    "amc_start_date": start_date.strftime("%Y-%m-%d"),
                    "amc_end_date": end_date.strftime("%Y-%m-%d"),
                    "frequency": frequency,
                    "visits": visits
                }
                data.append(client)
                if save_data(data):
                    st.success(f"✅ Client **{name}** added successfully with {len(visits)} visits!")
                    st.balloons()
                else:
                    st.error("Failed to save data.")

elif menu == "List All Clients":
    st.header("📋 All Clients")
    if not data:
        st.info("No clients added yet. Go to 'Add New Client AMC'")
    else:
        for idx, client in enumerate(data):
            with st.expander(f"👤 {client['customer_name']} | PO: {client['po_number']}"):
                st.write(f"**AMC Period:** {client['amc_start_date']} → {client['amc_end_date']}")
                st.write(f"**Frequency:** {client['frequency']}")
                st.write("**Visits:**")
                for v in client['visits']:
                    status_icon = "✅" if v.get("status") == "completed" else "⏳"
                    st.write(f"{status_icon} Visit #{v['visit_number']}: {v['due_start']} to {v['due_end']}")

elif menu == "Check Due Visits":
    st.header("📅 Check Due Visits")
    check_date = st.date_input("Select date to check", value=date.today())
    
    due_list = []
    for client in data:
        amc_start = datetime.datetime.strptime(client["amc_start_date"], "%Y-%m-%d").date()
        amc_end = datetime.datetime.strptime(client["amc_end_date"], "%Y-%m-%d").date()
        if amc_start <= check_date <= amc_end:
            for visit in client["visits"]:
                if visit.get("status") == "pending":
                    v_start = datetime.datetime.strptime(visit["due_start"], "%Y-%m-%d").date()
                    v_end = datetime.datetime.strptime(visit["due_end"], "%Y-%m-%d").date()
                    if v_start <= check_date <= v_end:
                        due_list.append((client, visit))
    
    if not due_list:
        st.success(f"No visits due on {check_date}")
    else:
        st.warning(f"🚨 {len(due_list)} visit(s) due on {check_date}")
        for client, visit in due_list:
            st.write(f"**{client['customer_name']}** (PO: {client['po_number']}) — Visit #{visit['visit_number']} due {visit['due_start']} to {visit['due_end']}")

elif menu == "Mark Visit Completed":
    st.header("✅ Mark Visit Completed")
    if not data:
        st.info("No clients yet.")
    else:
        client_names = [c["customer_name"] for c in data]
        selected = st.selectbox("Select Client", client_names)
        client = next(c for c in data if c["customer_name"] == selected)
        
        pending = [v for v in client["visits"] if v.get("status") == "pending"]
        if not pending:
            st.info("No pending visits left for this client.")
        else:
            options = [f"Visit #{v['visit_number']} ({v['due_start']} – {v['due_end']})" for v in pending]
            choice = st.selectbox("Select visit to mark complete", options)
            if st.button("Mark as Completed", type="primary"):
                visit_num = int(choice.split("#")[1].split()[0])
                for v in client["visits"]:
                    if v["visit_number"] == visit_num:
                        v["status"] = "completed"
                        if save_data(data):
                            st.success(f"Visit #{visit_num} marked ✅ Completed!")
                            st.rerun()
                        break

# Footer
st.sidebar.info("💡 Data is saved in the app. Download backup from GitHub regularly.")
