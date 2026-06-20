import streamlit as st
import pandas as pd
import json
import gspread
from google.oauth2.service_account import Credentials

# --- PAGE SETUP ---
st.set_page_config(
    page_title="AR Enterprises | Inventory Portal",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- STREAMLIT VERSION SAFETY NET ---
def safe_rerun():
    """Automatically detects Streamlit environment version to prevent crashes"""
    try:
        st.rerun()
    except AttributeError:
        st.experimental_rerun()

# --- PREMIUM iOS ANIMATED THEME (LIGHT MODE) ---
st.markdown("""
    <style>
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes pulseBorder {
            0% { box-shadow: 0 4px 15px rgba(52, 199, 89, 0.2); }
            50% { box-shadow: 0 4px 25px rgba(52, 199, 89, 0.5); }
            100% { box-shadow: 0 4px 15px rgba(52, 199, 89, 0.2); }
        }

        html, body, [data-testid="stAppViewContainer"] {
            background-color: #F2F2F7 !important; 
            color: #1C1C1E !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        }
        
        section[data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #E5E5EA !important;
        }
        
        .main-header {
            background-color: #FFFFFF;
            padding: 24px;
            border-radius: 16px;
            color: #1C1C1E;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
            margin-bottom: 25px;
            border: 1px solid #E5E5EA;
            animation: fadeInUp 0.4s ease-out;
        }
        
        .stExpander {
            border: 1px solid #E5E5EA !important;
            background-color: #FFFFFF !important;
            border-radius: 14px !important;
            margin-bottom: 12px !important;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
            overflow: hidden;
            transition: all 0.2s ease;
        }
        .stExpander:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06) !important;
        }
        
        div[data-baseweb="input"], div[data-baseweb="select"] {
            border-radius: 10px !important;
            background-color: #F2F2F7 !important;
        }
        
        div.stButton > button {
            background-color: #007AFF !important; 
            color: #FFFFFF !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 10px 20px !important;
            font-weight: 600 !important;
            transition: all 0.2s ease !important;
        }
        div.stButton > button:hover {
            background-color: #0056B3 !important;
            transform: scale(1.02);
        }
        
        div[data-testid="stMetricValue"] {
            font-size: 28px !important;
            font-weight: 700 !important;
            color: #007AFF !important; 
        }
        div[data-testid="stMetric"] {
            background-color: #FFFFFF !important;
            padding: 18px;
            border-radius: 16px;
            border: 1px solid #E5E5EA;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
            animation: fadeInUp 0.5s ease-out;
        }
        
        .invoice-box {
            background-color: #FFFFFF;
            padding: 25px;
            border-radius: 16px;
            border-left: 5px solid #34C759;
            font-family: monospace;
            color: #1C1C1E;
            margin-top: 15px;
            margin-bottom: 25px;
            animation: pulseBorder 2s infinite ease-in-out;
        }
    </style>
""", unsafe_allow_html=True)

# --- LIVE GOOGLE SHEET URL CONNECTION ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/1V20nMjBeSn4Neyli1S6CWptiDDSKYf4-62-q2HVEyU8"

# Establish secure cloud sheet connection
conn = st.connection("gsheets", type=GSheetsConnection)

ADMIN_PASSWORD = "admin123"
EMPLOYEE_PASSWORD = "staff123"

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = None
if "user_role" not in st.session_state:
    st.session_state["user_role"] = None
if "success_alert" not in st.session_state:
    st.session_state["success_alert"] = None
if "latest_invoice" not in st.session_state:
    st.session_state["latest_invoice"] = None

if not st.session_state["authenticated"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div style="background-color: #FFFFFF; padding: 35px; border-radius: 24px; 
                        text-align: center; color: #1C1C1E; box-shadow: 0 10px 30px rgba(0,0,0,0.08);
                        border: 1px solid #E5E5EA;">
                <h1 style='margin: 0; font-weight: 700; letter-spacing: -1px; color:#007AFF;'>🏢 AR ENTERPRISES</h1>
                <p style='color: #8E8E93; margin-top: 5px; font-size: 14px;'>Sign in with your Operator Identity</p>
            </div>
        """, unsafe_allow_html=True)
        with st.container(border=True):
            role = st.selectbox("🔐 Required Clearance Level", ["Employee", "Admin"])
            uid = st.text_input("👤 Operator Identity Name", placeholder="e.g., Harsh")
            pwd = st.text_input("🔒 Authorization Password", type="password", placeholder="••••••••")
            if st.button("🔓 Sign In", use_container_width=True):
                if uid.strip() != "":
                    if (role == "Admin" and pwd == ADMIN_PASSWORD) or (role == "Employee" and pwd == EMPLOYEE_PASSWORD):
                        st.session_state["authenticated"] = True
                        st.session_state["current_user"] = f"{uid.strip()} ({role})"
                        st.session_state["user_role"] = role
                        safe_rerun()
                    else:
                        st.error("❌ Invalid password Context.")
                else:
                    st.error("⚠️ Username is mandatory.")
else:
    if st.session_state.get("success_alert"):
        st.success(st.session_state["success_alert"])
        st.session_state["success_alert"] = None

    active_user = str(st.session_state["current_user"]).upper()

    st.markdown(f"""
        <div class="main-header">
            <h1 style="margin: 0; font-size: 28px; font-weight: 700; letter-spacing: -0.8px;">🏢 AR Enterprises Portal</h1>
            <p style="margin: 4px 0 0 0; color: #34C759; font-weight: 600; font-size: 14px;">
                ● Operator: {active_user}
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    col_space, col_logout = st.columns([6, 1])
    with col_logout:
        if st.button("🚪 Sign Out", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["latest_invoice"] = None
            safe_rerun()

    def load_data_from_db():
        try:
            df = conn.read(spreadsheet=SHEET_URL, worksheet="inventory", ttl="0d")
            df = df.dropna(subset=["item_id", "item_name"])
            return df
        except Exception:
            return pd.DataFrame(columns=["item_id", "item_name", "category", "stock", "price"])

    def load_audit_log():
        try:
            df = conn.read(spreadsheet=SHEET_URL, worksheet="audit_log", ttl="0d")
            return df.dropna(subset=["action"])
        except Exception:
            return pd.DataFrame(columns=["id", "user_id", "action", "timestamp"])

    def log_change(user, action_desc):
        try:
            df_log = load_audit_log()
            new_id = len(df_log) + 1
            new_row = pd.DataFrame([{
                "id": str(new_id),
                "user_id": str(user),
                "action": str(action_desc),
                "timestamp": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            }])
            df_updated = pd.concat([df_log, new_row], ignore_index=True)
            conn.update(worksheet="audit_log", data=df_updated)
        except Exception:
            pass

    def process_inwards(in_cat, in_name, in_qty, in_price):
        # Load credentials
        creds_dict = json.loads(st.secrets["connections"]["gsheets"]["secrets_json"])
        creds = Credentials.from_service_account_info(creds_dict)
        client = gspread.authorize(creds)
            
        # Open sheet and append
        sh = client.open_by_url("https://docs.google.com/spreadsheets/d/1V20nMjBeSn4Neyli1S6CWptiDDSKYf4-62-q2HVEyU8")
        worksheet = sh.worksheet("inventory")
    
        new_row = [in_cat.strip(), in_name.strip(), in_qty, in_price]
        worksheet.append_row(new_row)
        

    def process_outwards(cat, name, qty):
        df_inv = load_data_from_db()
        if not df_inv.empty and "item_name" in df_inv.columns and "category" in df_inv.columns:
            mask = (df_inv["item_name"] == name) & (df_inv["category"] == cat)
        else:
            mask = pd.Series([False])
        
        if mask.any():
            idx = df_inv[mask].index[0]
            current_stock = int(df_inv.at[idx, "stock"])
            if current_stock >= int(qty):
                df_inv.at[idx, "stock"] = current_stock - int(qty)
                unit_price = float(df_inv.at[idx, "price"])
                
                conn.update(worksheet="inventory", data=df_inv)
                log_change(st.session_state["current_user"], f"Outwards: Dispatched -{qty} units from '{name}'.")
                
                total_amount = int(qty) * unit_price
                st.session_state["latest_invoice"] = {
                    "item_name": name,
                    "category": cat,
                    "qty": qty,
                    "price": unit_price,
                    "total": total_amount,
                    "operator": st.session_state["current_user"]
                }
                return True
        return False

    def delete_item_completely(item_name, cat):
        df_inv = load_data_from_db()
        if not df_inv.empty and "item_name" in df_inv.columns and "category" in df_inv.columns:
            df_inv = df_inv[~((df_inv["item_name"].str.lower() == item_name.lower()) & (df_inv["category"].str.lower() == cat.lower()))]
            conn.update(worksheet="inventory", data=df_inv)
        log_change(st.session_state["current_user"], f"🗑 ... Deleted item row '{item_name}'.")

    def delete_category_completely(cat):
        df_inv = load_data_from_db()
        if not df_inv.empty and "category" in df_inv.columns:
            df_inv = df_inv[df_inv["category"].str.lower() != cat.lower()]
            conn.update(worksheet="inventory", data=df_inv)
        log_change(st.session_state["current_user"], f"💥 Wiped entire category '{cat}'.")

    def get_latest_modifier():
        df_log = load_audit_log()
        if not df_log.empty and "user_id" in df_log.columns and "action" in df_log.columns:
            last_row = df_log.iloc[-1]
            return f"💬 **System Status:** `{str(last_row['user_id']).upper()}` — *{last_row['action']}*"
        return "⚙️ System idling cleanly."

    inventory_df = load_data_from_db()
    db_categories = sorted(inventory_df["category"].unique().tolist()) if (not inventory_df.empty and "category" in inventory_df.columns) else []

    # --- RENDER GENERATED DIGITAL INVOICE SHEET ---
    if st.session_state.get("latest_invoice"):
        inv = st.session_state["latest_invoice"]
        st.markdown("### 🧾 Latest Outwards Invoice Generated")
        st.markdown(f"""
            <div class="invoice-box">
                <strong>AR ENTERPRISES - DISPATCH RECEIPT</strong><br>
                ------------------------------------------------<br>
                <strong>Operator Identity:</strong> {inv['operator']}<br>
                <strong>Category Segment:</strong> {inv['category']}<br>
                <strong>Product Dispatched:</strong> {inv['item_name']}<br>
                ------------------------------------------------<br>
                <strong>Quantity Released:</strong> {inv['qty']} units<br>
                <strong>Unit Base Price:</strong> ${inv['price']:,.2f}<br>
                ================================================<br>
                <span style="color:#34C759; font-size:16px; font-weight:bold;">NET TOTAL AMOUNT: ${inv['total']:,.2f}</span><br>
                ------------------------------------------------<br>
                <em>Status: Stock ledger cleared successfully.</em>
            </div>
        """, unsafe_allow_html=True)
        if st.button("Clear Invoice View"):
            st.session_state["latest_invoice"] = None
            safe_rerun()

    # --- SIDEBAR CONTROL DECKS ---
    st.sidebar.markdown("### 🛠️ Workstation Decks")
    
    # 📥 INWARDS
    with st.sidebar.expander("📥 Inwards Deck", expanded=False):
        in_mode = st.radio("Sourcing Method", ["Existing Item Profile", "Create Brand New Product"], key="in_mode")
        
        if in_mode == "Existing Item Profile":
            in_cat = st.selectbox("Select Target Category", db_categories if db_categories else ["None Available"], key="in_cat_select")
            if not inventory_df.empty and "category" in inventory_df.columns and "item_name" in inventory_df.columns:
                items = inventory_df[inventory_df["category"] == in_cat]["item_name"].unique().tolist()
            else:
                items = []
            in_name = st.selectbox("Select Product", items, key="in_select_name") if items else ""
        else:
            use_custom_cat = st.checkbox("➕ Add to a Brand New Category?", value=False)
            if use_custom_cat or not db_categories:
                in_cat = st.text_input("Type Brand New Category Name", placeholder="e.g., Hardware", key="in_cat_text")
            else:
                in_cat = st.selectbox("Choose Existing Category Base", db_categories, key="in_cat_select_new")
                
            in_name = st.text_input("Type Item Title", key="in_text_name", placeholder="e.g., Hammer")
            
        in_qty = st.number_input("Units to Add (+)", min_value=1, step=1, value=1, key="in_qty")
        in_price = st.number_input("Unit Price ($)", min_value=0.0, step=0.01, value=10.0, key="in_price")
        
        if st.button("Process Inwards Registry", use_container_width=True, key="in_submit_fixed"):
            if in_name and in_cat and in_cat != "None Available":
                process_inwards(in_cat.strip(), in_name.strip(), in_qty, in_price)
                st.session_state["success_alert"] = f"✅ Success! Added {in_qty}x '{in_name}' to category '{in_cat}'."
                safe_rerun()
            else:
                st.error("Error: Please provide both Category and Item Name.")

    # 📤 OUTWARDS
    with st.sidebar.expander("📤 Outwards Deck", expanded=False):
        out_cat = st.selectbox("Select Category", db_categories if db_categories else ["None Available"], key="out_cat")
        if not inventory_df.empty and "category" in inventory_df.columns and "item_name" in inventory_df.columns:
            items = inventory_df[inventory_df["category"] == out_cat]["item_name"].unique().tolist()
        else:
            items = []
        out_name = st.selectbox("Select Product to Dispatch", items, key="out_name") if items else None
        out_qty = st.number_input("Units to Release (-)", min_value=1, step=1, value=1, key="out_qty")
        
        if st.button("Process Outwards Dispatch", use_container_width=True, key="out_submit_fixed"):
            if out_name and process_outwards(out_cat, out_name, out_qty):
                st.session_state["success_alert"] = f"✅ Success! Ledger updated for '{out_name}'."
                safe_rerun()
            else:
                st.error("❌ Outwards Denied: Item unavailable or insufficient stock.")

    # 🗑️ ERASURE PIPELINE
    with st.sidebar.expander("🗑️ Delete Inventory", expanded=False):
        st.markdown("<p style='color: #FF3B30; font-size:12px;'>Warning: Double-check selection before confirming deletion.</p>", unsafe_allow_html=True)
        del_type = st.radio("What do you want to delete?", ["Single Row Item", "Entire Stock Category"], key="del_type")
        
        if del_type == "Single Row Item":
            d_cat = st.selectbox("Target Item Category", db_categories if db_categories else ["None"], key="d_cat")
            if not inventory_df.empty and "category" in inventory_df.columns and "item_name" in inventory_df.columns:
                d_items = inventory_df[inventory_df["category"] == d_cat]["item_name"].unique().tolist()
            else:
                d_items = []
            target_item = st.selectbox("Choose Item to Erase", d_items, key="target_item") if d_items else None
            
            if st.button("🗑️ Wipe Item Row Permanently", use_container_width=True):
                if target_item:
                    delete_item_completely(target_item, d_cat)
                    st.session_state["success_alert"] = f"🗑️ Item '{target_item}' removed permanently."
                    safe_rerun()
        else:
            target_cat = st.selectbox("Select Entire Category to Delete", db_categories if db_categories else ["None"], key="target_cat")
            if st.button("💥 WIPE ENTIRE CATEGORY", use_container_width=True):
                delete_category_completely(target_cat)
                st.session_state["success_alert"] = f"💥 Category group '{target_cat}' deleted permanently."
                safe_rerun()

    # --- MAIN CENTRAL CONTAINER ---
    st.markdown("## 📊 Storage Register")
    
    # 1. SEE ALL INVENTORY EXPANDER BAR
    with st.expander("🔍 See All Inventory", expanded=False):
        if not db_categories:
            st.info("The inventory registry is completely empty. Use the Inwards Deck to add items!")
        else:
            st.markdown("### 📁 Step 1: Choose a Stock Category")
            selected_category = st.radio("Categories Available:", db_categories, horizontal=True)
            
            if selected_category and not inventory_df.empty and "category" in inventory_df.columns and "item_name" in inventory_df.columns:
                st.markdown(f"### 📦 Step 2: Items under *{selected_category.upper()}*")
                cat_items_df = inventory_df[inventory_df["category"] == selected_category]
                item_names_list = cat_items_df["item_name"].unique().tolist()
                
                if not item_names_list:
                    st.write("No active item profiles found inside this category group.")
                else:
                    selected_item_profile = st.selectbox("Live balances inspection picker:", ["-- Choose Item --"] + item_names_list)
                    
                    if selected_item_profile != "-- Choose Item --" and selected_item_profile in item_names_list:
                        profile_row = cat_
