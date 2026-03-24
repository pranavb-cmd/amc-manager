import streamlit as st
import json
import datetime
import os
from datetime import date

DATA_FILE = "amc_data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f)
        except:
            return []
    return []

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_date_input(label):
    d = st.date_input(label)
    return d.strftime("%Y-%m-%d") if d else None

st.set_page_config(page_title="AMC Visit Manager", page_icon="🔧", layout="wide")
st.title("🔧 AMC Maintenance Visit Manager")
st.markdown("Manage AMC contracts, visit schedules & due visits for all clients")

data = load_data()

# Sidebar Menu
menu = st.sidebar.selectbox(
    "Choose Action",
    ["Add New Client AMC", "List All Clients", "Check Due Visits", "Mark Visit Completed"]
)

if menu == "Add New Client AMC":
    st.header("Add New Client AMC")
    name = st.text_input("Customer Name")
    po = st.text_input("PO Number")
    col1, col2 = st.columns(2)
    with col1:
        start = st.date_input("AMC Start Date")
    with col2:
        end = st.date_input("AMC End Date")
    frequency = st.selectbox("Visit Frequency", ["quarterly", "six-monthly", "other"])

    visits = []
    st.subheader("Add Visits (Due Periods)")
    num_visits = st.number_input("How many visits in this AMC?", min_value=1, value=4, step=1)

    for i in range(1, num_visits + 1):
        st.write(f"**Visit #{i}**")
        col3, col4 = st.columns(2)
        with col3:
            due_start = st.date_input(f"Due Start Date (Visit {i})", key=f"start{i}")
        with col4:
            due_end = st.date_input(f"Due End Date (Visit {i})", key=f"end{i}")
        if due_start and due_end:
            visits.append({
                "visit_number": i,
                "due_start": due_start.strftime("%Y-%m-%d"),
                "due_end": due_end.strftime("%Y-%m-%d"),
                "status": "pending"
            })

    if st.button("Save New AMC", type="primary"):
        if name and po and start and end and visits:
            client = {
                "customer_name": name,
                "po_number": po,
                "amc_start_date": start.strftime("%Y-%m-%d"),
                "amc_end_date": end.strftime("%Y-%m-%d"),
                "frequency": frequency,
                "visits": visits
            }
            data.append(client)
            save_data(data)
            st.success("✅ Client AMC added successfully!")
            st.rerun()
        else:
            st.error("Please fill all required fields")

elif menu == "List All Clients":
    st.header("All Clients")
    if not data:
        st.info("No clients added yet.")
    else:
        for i, client in enumerate(data, 1):
            with st.expander(f"{i}. {client['customer_name']} | PO: {client['po_number']}"):
                st.write(f"**AMC Period:** {client['amc_start_date']} to {client['amc_end_date']}")
                st.write(f"**Frequency:** {client['frequency']}")
                st.write(f"**Total Visits:** {len(client['visits'])}")
                for v in client['visits']:
                    status = "✅ Completed" if v['status'] == "completed" else "⏳ Pending"
                    st.write(f"Visit #{v['visit_number']}: {v['due_start']} to {v['due_end']} — {status}")

elif menu == "Check Due Visits":
    st.header("Check Due Visits")
    check_date = st.date_input("Check date", value=date.today())
    check_date_str = check_date.strftime("%Y-%m-%d")
    check_d = check_date

    due_list = []
    for client in data:
        amc_start = datetime.datetime.strptime(client["amc_start_date"], "%Y-%m-%d").date()
        amc_end = datetime.datetime.strptime(client["amc_end_date"], "%Y-%m-%d").date()
        if amc_start <= check_d <= amc_end:
            for visit in client["visits"]:
                if visit["status"] == "pending":
                    v_start = datetime.datetime.strptime(visit["due_start"], "%Y-%m-%d").date()
                    v_end = datetime.datetime.strptime(visit["due_end"], "%Y-%m-%d").date()
                    if v_start <= check_d <= v_end:
                        due_list.append({
                            "client": client["customer_name"],
                            "po": client["po_number"],
                            "visit_no": visit["visit_number"],
                            "period": f"{visit['due_start']} to {visit['due_end']}"
                        })

    if not due_list:
        st.success(f"✅ No visits due on {check_date_str}")
    else:
        st.warning(f"🚨 {len(due_list)} visit(s) due on {check_date_str}")
        for item in due_list:
            st.write(f"**{item['client']}** (PO: {item['po']}) — Visit #{item['visit_no']} due {item['period']}")

elif menu == "Mark Visit Completed":
    st.header("Mark Visit as Completed")
    if not data:
        st.info("No clients yet.")
    else:
        client_names = [c["customer_name"] for c in data]
        selected_client = st.selectbox("Select Client", client_names)
        client = next(c for c in data if c["customer_name"] == selected_client)

        pending = [v for v in client["visits"] if v["status"] == "pending"]
        if not pending:
            st.info("No pending visits for this client.")
        else:
            options = [f"Visit #{v['visit_number']} ({v['due_start']} to {v['due_end']})" for v in pending]
            choice = st.selectbox("Select Visit to Complete", options)
            if st.button("Mark as Completed", type="primary"):
                visit_num = int(choice.split("#")[1].split()[0])
                for v in client["visits"]:
                    if v["visit_number"] == visit_num:
                        v["status"] = "completed"
                        save_data(data)
                        st.success(f"✅ Visit #{visit_num} marked COMPLETED!")
                        st.rerun()

st.sidebar.info("Data is saved automatically in the cloud.")