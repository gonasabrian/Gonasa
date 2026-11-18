# GONASA - 5 Agents - Render + Google Sheet + GitHub
# KEYS ARE IN RENDER, NOT HERE - EDIT IN RENDER DASHBOARD
import os, uuid, time, requests
from flask import Flask, request, render_template_string, session, redirect, jsonify

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "gonasa-secret-123")

# --- YOUR 5 AGENTS ---
AGENTS = {
    "agent1": {"password": "1234", "name": "Agent 1", "phone": "0764004072"},
    "agent2": {"password": "1234", "name": "Agent 2", "phone": "0765721544"},
    "agent3": {"password": "1234", "name": "Agent 3", "phone": "0774815047"},
    "agent4": {"password": "1234", "name": "Agent 4", "phone": "0783733968"},
    "agent5": {"password": "1234", "name": "Agent 5", "phone": "0779394542"},
}
# --- MTN CONFIG - FROM RENDER ENV VARS ---
CFG = {
    "ENV": os.environ.get("MTN_ENV", "sandbox"),
    "BASE_URL": os.environ.get("MTN_BASE_URL", "https://sandbox.momodeveloper.mtn.com"),
    "COLLECTION_KEY": os.environ.get("COLLECTION_KEY", ""),
    "DISBURSEMENT_KEY": os.environ.get("DISBURSEMENT_KEY", ""),
    "API_USER_ID": os.environ.get("API_USER_ID", ""),
    "API_KEY": os.environ.get("API_KEY", ""),
    "SHEET_ID": os.environ.get("GOOGLE_SHEET_ID", ""),
}
BUSINESS_NUMBER = "0766756708"
history = []

def get_token(is_collection=True):
    key = CFG["COLLECTION_KEY"] if is_collection else CFG["DISBURSEMENT_KEY"]
    prod = "collection" if is_collection else "disbursement"
    r = requests.post(f"{CFG['BASE_URL']}/{prod}/token/",
        headers={"Ocp-Apim-Subscription-Key": key},
        json={"grant_type": "client_credentials"},
        auth=(CFG["API_USER_ID"], CFG["API_KEY"]))
    return r.json().get("access_token") if r.status_code == 200 else None

def fmt(p):
    p = p.strip().replace(" ", "").replace("+", "")
    if p.startswith("0"): p = "256" + p[1:]
    return p

def save_to_sheet(agent, type_, phone, amount, status, ref):
    # Google Sheet - will work after you add GOOGLE_CREDENTIALS in Render
    # For now saves to memory, Sheet sync in next step
    history.insert(0, {"date": time.strftime("%Y-%m-%d %H:%M"), "agent": agent, "type": type_, "phone": phone, "amount": amount, "status": status, "ref": ref})
    try:
        import gspread, json
        creds = os.environ.get("GOOGLE_CREDENTIALS")
        if creds and CFG["SHEET_ID"]:
            gc = gspread.service_account_from_dict(json.loads(creds))
            sh = gc.open_by_key(CFG["SHEET_ID"])
            ws = sh.worksheet("Transactions")
            ws.append_row([time.strftime("%Y-%m-%d %H:%M"), agent, type_, phone, amount, status, ref])
    except Exception as e:
        print("Sheet error:", e)

LOGIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{font-family:Arial;background:#f4f4f4;padding:20px} .c{background:#fff;padding:25px;border-radius:15px;max-width:400px;margin:50px auto} input{width:100%;padding:12px;margin:8px 0;border:1px solid #ddd;border-radius:8px;box-sizing:border-box} button{width:100%;padding:14px;background:#FFCC00;border:none;border-radius:10px;font-weight:bold} h2{text-align:center}</style></head><body>
<div class="c"><h2>GONASA</h2><p style="text-align:center">Login - 5 Agents</p>
<form method="POST"><input name="username" placeholder="Username e.g. agent1" required><input name="password" type="password" placeholder="Password" required><button>Login</button></form>
<p style="font-size:12px;text-align:center">agent1 / 1234<br>agent2 / 1234<br>agent3 / 1234<br>agent4 / 1234<br>agent5 / 1234</p></div></body></html>
"""

MAIN_HTML = """
<!DOCTYPE html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GONASA</title>
<style>body{font-family:Arial;background:#f4f4f4;margin:0;padding:12px}.card{background:#fff;padding:18px;border-radius:14px;margin-bottom:12px}.top{background:#000;color:#FFCC00;padding:15px;border-radius:12px;text-align:center}.top b{font-size:22px}.top span{color:#fff;font-size:13px;display:block}input{width:100%;padding:12px;margin:7px 0;border:1px solid #ddd;border-radius:8px;font-size:16px;box-sizing:border-box}button{width:100%;padding:14px;border:none;border-radius:10px;font-size:16px;font-weight:bold}.y{background:#FFCC00}.b{background:#000;color:#FFCC00}.g{background:green;color:#fff}.grey{background:#eee}.res{padding:10px;background:#e8f5e9;border-radius:8px;margin-top:8px;display:none}table{width:100%;font-size:12px}td{padding:7px;border-bottom:1px solid #eee}a{color:#fff}</style></head><body>
<div class="top"><b>GONASA</b><span>Hi {{name}} • {{phone}} • {{env}} • <a href="/logout">Logout</a></span></div>
<div class="card"><h3>💰 Balance - 0766756708</h3><button class="grey" onclick="bal()">Check Balance</button><div id="balRes" class="res"></div></div>
<div class="card"><h3>🔍 Name Lookup</h3><input id="lPhone" placeholder="Number"><button class="g" onclick="lookup()">Check Name</button><div id="lRes" class="res"></div></div>
<div class="card"><h3>⬇️ Deposit</h3><input id="dPhone" placeholder="Customer Number"><input id="dAmt" type="number" placeholder="Amount UGX"><button class="y" onclick="pay('deposit')">Request Deposit</button><div id="dRes" class="res"></div></div>
<div class="card"><h3>⬆️ Withdraw</h3><input id="wPhone" placeholder="Customer Number"><input id="wAmt" type="number" placeholder="Amount UGX"><button class="b" onclick="pay('withdraw')">Send Withdraw</button><div id="wRes" class="res"></div></div>
<div class="card"><h3>📋 My Transactions</h3><div id="hist">Loading...</div><button class="grey" onclick="loadHist()">Refresh</button></div>
<script>
async function call(url,body,elId){let r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});let d=await r.json();let el=document.getElementById(elId);el.style.display='block';el.innerHTML=d.success?`✅ ${d.msg||''} ${d.ref?'Ref: '+d.ref:''} ${d.data?JSON.stringify(d.data):''}`:`❌ ${d.error}`;return d;}
function lookup(){call('/api/lookup',{phone:document.getElementById('lPhone').value},'lRes')}
function bal(){call('/api/balance',{},'balRes')}
function pay(t){let p=document.getElementById(t=='deposit'?'dPhone':'wPhone').value;let a=document.getElementById(t=='deposit'?'dAmt':'wAmt').value;call('/api/'+t,{phone:p,amount:a},t=='deposit'?'dRes':'wRes').then(()=>loadHist())}
async function loadHist(){let r=await fetch('/api/history');let d=await r.json();if(!d.length){document.getElementById('hist').innerHTML='No transactions';return;}document.getElementById('hist').innerHTML='<table>'+d.map(x=>`<tr><td>${x.date}</td><td>${x.agent}</td><td>${x.type}</td><td>${x.phone}</td><td>${x.amount}</td><td>${x.status}</td></tr>`).join('')+'</table>'}
loadHist();
</script></body></html>
"""

@app.route("/", methods=["GET","POST"])
def login():
    if request.method=="POST":
        u=request.form.get("username"); p=request.form.get("password")
        if u in AGENTS and AGENTS[u]["password"]==p:
            session["user"]=u; return redirect("/app")
        return LOGIN_HTML + "<p style='text-align:center;color:red'>Wrong login</p>"
    if "user" in session: return redirect("/app")
    return LOGIN_HTML

@app.route("/app")
def main():
    if "user" not in session: return redirect("/")
    a=AGENTS[session["user"]]
    return render_template_string(MAIN_HTML, name=a["name"], phone=a["phone"], env=CFG["ENV"].upper())

@app.route("/logout")
def logout(): session.clear(); return redirect("/")

@app.route("/api/balance", methods=["POST"])
def balance():
    if "user" not in session: return jsonify({"success":False,"error":"Login first"})
    t=get_token(True)
    if not t: return jsonify({"success":False,"error":"Token failed - Check Keys in Render"})
    r=requests.get(f"{CFG['BASE_URL']}/collection/v1_0/account/balance", headers={"Authorization":f"Bearer {t}","X-Target-Environment":CFG["ENV"],"Ocp-Apim-Subscription-Key":CFG["COLLECTION_KEY"]})
    return jsonify({"success":r.status_code==200,"data":r.json() if r.status_code==200 else None,"error":r.text[:200] if r.status_code!=200 else "","msg":"Balance: "})

@app.route("/api/lookup", methods=["POST"])
def lookup():
    if "user" not in session: return jsonify({"success":False,"error":"Login first"})
    phone=fmt(request.json.get("phone","")); t=get_token(True)
    if not t: return jsonify({"success":False,"error":"Token failed"})
    r=requests.get(f"{CFG['BASE_URL']}/collection/v1_0/accountholder/msisdn/{phone}/active", headers={"Authorization":f"Bearer {t}","X-Target-Environment":CFG["ENV"],"Ocp-Apim-Subscription-Key":CFG["COLLECTION_KEY"]})
    return jsonify({"success":r.status_code==200,"data":r.json() if r.status_code==200 else None,"error":r.text[:200] if r.status_code!=200 else "","msg":f"Number {request.json.get('phone')} is Active"})

@app.route("/api/deposit", methods=["POST"])
def dep(): return transact("deposit", request.json)
@app.route("/api/withdraw", methods=["POST"])
def wd(): return transact("withdraw", request.json)

def transact(type_, data):
    if "user" not in session: return jsonify({"success":False,"error":"Login first"})
    phone=fmt(data.get("phone","")); amt=str(data.get("amount","")); is_dep=type_=="deposit"
    t=get_token(is_dep)
    if not t: return jsonify({"success":False,"error":"Token failed - Check Keys in Render"})
    ref=str(uuid.uuid4()); key=CFG["COLLECTION_KEY"] if is_dep else CFG["DISBURSEMENT_KEY"]
    prod="collection" if is_dep else "disbursement"; ep="requesttopay" if is_dep else "transfer"; party="payer" if is_dep else "payee"
    body={"amount":amt,"currency":"UGX","externalId":f"GONASA-{type_.upper()}-{int(time.time())}",party:{"partyIdType":"MSISDN","partyId":phone},"payerMessage":f"GONASA {type_}","payeeNote":f"GONASA {type_}"}
    r=requests.post(f"{CFG['BASE_URL']}/{prod}/v1_0/{ep}", headers={"Authorization":f"Bearer {t}","X-Reference-Id":ref,"X-Target-Environment":CFG["ENV"],"Ocp-Apim-Subscription-Key":key}, json=body)
    if r.status_code in [200,202]:
        save_to_sheet(session["user"], type_.upper(), data.get("phone"), amt, "PENDING", ref)
        return jsonify({"success":True,"ref":ref,"msg":f"{type_} sent - Customer must approve"})
    return jsonify({"success":False,"error":f"{r.status_code} - {r.text[:300]}"})

@app.route("/api/history")
def hist(): return jsonify(history)

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
