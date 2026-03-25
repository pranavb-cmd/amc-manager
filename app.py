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
st.caption("Manage AMC contracts & scheduled maintenance visits")

data = load_data()

menu = st.sidebar.selectbox(
    "Menu",
    ["Add New Client AMC", "List All Clients", "Check Due Visits", "Mark Visit Completed"]
)

if menu == "Add New Client AMC":
    st.header("➕ Add New Client AMC")
    
    with st.form("add_amc_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Customer Name *")
            po = st.text_input("PO Number *")
        with col2:
            start_date = st.date_input("AMC Start Date *", value=date.today())
            end_date = st.date_input("AMC End Date *", value=date(2027, 12, 31))
        
        frequency = st.selectbox("Visit Frequency", ["quarterly", "six-monthly", "other"])
        
        # Dynamic Number of Visits
        num_visits = st.number_input("Number of Visits in this AMC", 
                                     min_value=1, max_value=24, value=4, step=1)
        
        st.subheader(f"📅 Visit Schedule ({num_visits} visits)")
        
        visits = []
        for i in range(1, int(num_visits) + 1):
            st.markdown(f"**Visit #{i}**")
            c1, c2 = st.columns(2)
            with c1:
                due_start = st.date_input(f"Due Start Date", key=f"start_{i}")
            with c2:
                due_end = st.date_input(f"Due End Date", key=f"end_{i}")
            
            if due_start and due_end:
                visits.append({
                    "visit_number": i,
                    "due_start": due_start.strftime("%Y-%m-%d"),
                    "due_end": due_end.strftime("%Y-%m-%d"),
                    "status": "pending"
                })

        submitted = st.form_submit_button("💾 Save New AMC", type="primary")
        
        if submitted:
            if not name or not po or len(visits) == 0:
                st.error("❌ Please fill Customer Name, PO Number, and all visit dates.")
            elif len(visits) != num_visits:
                st.error("❌ Please select dates for all visits.")
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
                    st.success(f"✅ **{name}** AMC added successfully with {num_visits} visits!")
                    st.balloons()
                else:
                    st.error("Failed to save data.")

# ====================== Other Menus (unchanged but improved) ======================

elif menu == "List All Clients":
    st.header("📋 All Clients")
    if not data:
        st.info("No clients added yet.")
    else:
        for client in data:
            with st.expander(f"👤 {client['customer_name']} | PO: {client['po_number']}"):
                st.write(f"**AMC:** {client['amc_start_date']} to {client['amc_end_date']}")
                st.write(f"**Frequency:** {client['frequency']}")
                st.write("**Visits:**")
                for v in client['visits']:
                    icon = "✅" if v.get("status") == "completed" else "⏳"
                    st.write(f"{icon} Visit #{v['visit_number']}: {v['due_start']} — {v['due_end']}")

elif menu == "Check Due Visits":
    st.header("📅 Check Due Visits")
    check_date = st.date_input("Select date", value=date.today())
    
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
        st.success(f"✅ No visits due on {check_date}")
    else:
        st.warning(f"🚨 {len(due_list)} visit(s) due on {check_date}")
        for client, visit in due_list:
            st.write(f"**{client['customer_name']}** (PO: {client['po_number']}) — Visit #{visit['visit_number']} due {visit['due_start']} to {visit['due_end']}")

elif menu == "Mark Visit Completed":
    st.header("✅ Mark Visit as Completed")
    if not data:
        st.info("No clients yet.")
    else:
        client_list = [c["customer_name"] for c in data]
        selected_client = st.selectbox("Select Client", client_list)
        client = next(c for c in data if c["customer_name"] == selected_client)
        
        pending_visits = [v for v in client["visits"] if v.get("status") == "pending"]
        
        if not pending_visits:
            st.info("All visits are already completed for this client.")
        else:
            options = [f"Visit #{v['visit_number']} ({v['due_start']} to {v['due_end']})" for v in pending_visits]
            selected_visit = st.selectbox("Select Visit to Mark Complete", options)
            
            if st.button("Mark as Completed", type="primary"):
                visit_num = int(selected_visit.split("#")[1].split()[0])
                for v in client["visits"]:
                    if v["visit_number"] == visit_num:
                        v["status"] = "completed"
                        save_data(data)
                        st.success(f"Visit #{visit_num} marked as ✅ Completed!")
                        st.rerun()
                        break

st.sidebar.info("💡 Tip: Data is saved automatically. Download backup from GitHub regularly.")
