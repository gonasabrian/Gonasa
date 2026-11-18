import streamlit as st
import gspread
import pandas as pd
import random
from google.oauth2.service_account import Credentials
from datetime import datetime

st.set_page_config(page_title="GONASA Agent App", page_icon="💰", layout="centered")
SHEET_ID = "1uqacKdD5Sr4HXQC2EjuZUH9xmLHdqirXVRaMX6U9Y9A"

st.markdown("""
<style>
.top-box { background:#FFCC00; padding:18px; border-radius:16px; display:flex; justify-content:space-between; align-items:center; }
.balance-box { background:#111; color:#fff; border-radius:16px; padding:20px; margin-top:15px; }
.balance-box h1 { color:#FFCC00; font-size:34px; margin:5px 0; }
.card { background:#fff; border-radius:16px; padding:16px; margin-top:15px; }
.stButton > button { width:100%; background:#FFCC00; color:#000; font-weight:bold; padding:12px; border-radius:12px; border:none; font-size:17px; }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    return gspread.authorize(creds)

def get_settings():
    # Settings tab: Key | value
    ws = get_client().open_by_key(SHEET_ID).worksheet("Settings")
    rows = ws.get_all_values()
    d = {}
    for r in rows[1:]:
        if len(r) >= 2 and r[0].strip() != "":
            d[r[0].strip()] = r[1].strip()
    return d

def get_users():
    # Users tab: Row2 header Password | Name | Phone, data from Row3
    ws = get_client().open_by_key(SHEET_ID).worksheet("Users")
    rows = ws.get_all_values()
    users = []
    for r in rows[2:]:
        vals = [x.strip() for x in r if x.strip() != ""]
        if len(vals) >= 3:
            users.append({"Password": vals[0], "Name": vals[1], "Phone": vals[2]})
    return pd.DataFrame(users)

def save_transaction(agent, tx_type, cust_phone, amount):
    # Transactions: Date | Agent | Type | Customer_phone | Amount | Status | Ref
    ws = get_client().open_by_key(SHEET_ID).worksheet("Transactions")
    ref = f"GON{random.randint(100000,999999)}"
    ws.append_row([
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        agent, tx_type, str(cust_phone), int(amount), "Success", ref
    ])
    return ref

def get_history():
    ws = get_client().open_by_key(SHEET_ID).worksheet("Transactions")
    return pd.DataFrame(ws.get_all_records())

# Settings - from your Sheet
try:
    SETTINGS = get_settings()
    ENV = SETTINGS.get("env", "sandbox").upper()
    BUSINESS_NO = SETTINGS.get("Business_number", "766756708")
except:
    ENV = "SANDBOX"
    BUSINESS_NO = "766756708"

if "logged" not in st.session_state: st.session_state.logged = False
if "user" not in st.session_state: st.session_state.user = ""
if "phone" not in st.session_state: st.session_state.phone = ""
if "page" not in st.session_state: st.session_state.page = "dashboard"
if "pending" not in st.session_state: st.session_state.pending = None

# --- LOGIN ---
if not st.session_state.logged:
    st.markdown("<h1 style='text-align:center'>GONASA</h1><p style='text-align:center'>Agent App</p>", unsafe_allow_html=True)
    st.caption(f"Business: {BUSINESS_NO} • Env: {ENV}")
    user = st.text_input("Username", placeholder="e.g amulamu")
    password = st.text_input("Password", type="password", placeholder="1234")
    if st.button("LOGIN"):
        df = get_users()
        match = df[(df['Name'].str.lower() == user.lower()) & (df['Password'].astype(str) == str(password))]
        if not match.empty:
            st.session_state.logged = True
            st.session_state.user = match.iloc[0]['Name']
            st.session_state.phone = match.iloc[0]['Phone']
            st.rerun()
        else:
            st.error("Wrong login")
    st.stop()

# --- TOP BAR ---
st.markdown(f"""
<div class="top-box"><div><b style="font-size:20px">GONASA</b><br><small>{st.session_state.user} • {st.session_state.phone}</small></div>
<span style="font-size:13px;background:#000;color:#FFCC00;padding:5px 10px;border-radius:20px">{ENV}</span></div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("Menu", ["🏠 Dashboard", "⬇️ Deposit", "⬆️ Withdraw", "🔄 Share Float", "📄 History", "🚪 Logout"])
if menu == "🚪 Logout":
    st.session_state.logged = False; st.rerun()
elif "Dashboard" in menu: st.session_state.page = "dashboard"
elif "Deposit" in menu: st.session_state.page = "deposit"
elif "Withdraw" in menu: st.session_state.page = "withdraw"
elif "Share Float" in menu: st.session_state.page = "share"
elif "History" in menu: st.session_state.page = "history"

if st.session_state.page == "dashboard":
    st.markdown("""<div class="balance-box"><small style="color:#aaa">Available Balance</small>
    <h1>UGX 0</h1><p style="color:#ccc;font-size:13px">Tap to refresh • Last updated now</p></div>""", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("⬇️ Deposit"): st.session_state.page="deposit"; st.rerun()
    if c2.button("⬆️ Withdraw"): st.session_state.page="withdraw"; st.rerun()
    c3, c4 = st.columns(2)
    if c3.button("🔄 Share Float"): st.session_state.page="share"; st.rerun()
    if c4.button("📄 History"): st.session_state.page="history"; st.rerun()
    st.markdown("<div class='card'><h3>Recent Transactions</h3>", unsafe_allow_html=True)
    df = get_history()
    if not df.empty:
        for _, r in df.tail(5).iloc[::-1].iterrows():
            st.write(f"**{r['Type']}** - {r['Customer_phone']} - UGX {r['Amount']} - {r['Status']}")
    else:
        st.write("No transactions yet")
    st.markdown("</div>", unsafe_allow_html=True)

elif st.session_state.page in ["deposit", "withdraw", "share"]:
    titles = {"deposit": "MTN Deposit", "withdraw": "MTN Withdraw", "share": "Share Float"}
    title = titles[st.session_state.page]
    st.markdown(f'<div class="card"><h3>{title}</h3>', unsafe_allow_html=True)
    cust_no = st.text_input("Customer No.", placeholder="e.g 0788401754" if title!="Share Float" else "Receiver Agent No.")
    amount = st.number_input("Amount UGX", min_value=0, step=1000)
    st.markdown('</div>', unsafe_allow_html=True)
    if st.button("Validate →"):
        if cust_no and amount > 0:
            cust_name = "BRIAN GONASA" if cust_no=="0788401754" else "CUSTOMER NAME"
            st.session_state.pending = {"cust_no":cust_no, "amount":amount, "tx_type":title, "cust_name":cust_name}
            st.session_state.page="confirm"; st.rerun()
        else: st.error("Enter customer number and amount")
    st.caption("Name will be fetched automatically after Validate")
    if st.button("← Back to Home"): st.session_state.page="dashboard"; st.rerun()

elif st.session_state.page == "confirm":
    p = st.session_state.pending
    st.markdown(f"""
    <div style="background:#1a1a2e;color:#fff;padding:20px;border-radius:16px">
    <h3 style="text-align:center">Confirm Payment</h3>
    <p>Customer No.: <b style="float:right">{p['cust_no']}</b></p>
    <p>Customer Name: <b style="float:right">{p['cust_name']}</b></p>
    <p>Item: <b style="float:right">{p['tx_type']}</b></p>
    <p>Biller: <b style="float:right">MTN Mobile Money</b></p>
    <p>Business No.: <b style="float:right">{BUSINESS_NO}</b></p>
    <p>Payment Mode: <b style="float:right">Cash</b></p><hr>
    <p>Amount UGX: <b style="float:right">{p['amount']}</b></p>
    <p>Total UGX: <b style="float:right">{p['amount']}</b></p></div>
    """, unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    if c1.button("Cancel"): st.session_state.page="dashboard"; st.rerun()
    if c2.button("Confirm"):
        ref = save_transaction(st.session_state.user, p['tx_type'], p['cust_no'], p['amount'])
        st.session_state.last_ref = ref
        st.session_state.page="done"; st.rerun()

elif st.session_state.page == "done":
    st.success(f"✅ Transaction Sent to MTN... Ref: {st.session_state.get('last_ref','')}")
    st.info("Saved to Google Sheet -> Transactions tab")
    if st.button("Back to Home"): st.session_state.page="dashboard"; st.rerun()

elif st.session_state.page == "history":
    st.markdown("<div class='card'><h3>Today's History</h3>", unsafe_allow_html=True)
    df = get_history()
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.write("No history yet")
    st.markdown("</div>", unsafe_allow_html=True)
    if st.button("← Back to Home"): st.session_state.page="dashboard"; st.rerun()
