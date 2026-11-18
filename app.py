from flask import Flask, request, redirect, session, render_template_string

app = Flask(__name__)
app.secret_key = "gonasa123"

BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box} body{font-family:Arial;margin:0;background:#f4f4f4;padding-bottom:80px}
.top{background:#FFCC00;padding:18px 16px 12px;display:flex;justify-content:space-between;align-items:center}
.top b{font-size:20px} .top span{font-size:13px;background:#000;color:#FFCC00;padding:5px 10px;border-radius:20px}
.balance{background:#111;color:#fff;margin:15px;border-radius:16px;padding:20px}
.balance small{color:#aaa} .balance h1{font-size:34px;margin:8px 0;color:#FFCC00}
.balance p{margin:0;color:#ccc;font-size:13px}
.card{background:#fff;margin:15px;border-radius:16px;padding:16px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.action{background:#fff;border-radius:16px;padding:18px 10px;text-align:center;border:1px solid #eee;cursor:pointer}
.action div{font-size:28px} .action b{font-size:14px}
input,select{width:100%;padding:15px;margin:8px 0;border-radius:12px;border:1px solid #ddd;font-size:16px}
.btn{width:100%;padding:16px;background:#FFCC00;border:none;border-radius:12px;font-size:17px;font-weight:bold}
.nav{position:fixed;bottom:0;left:0;right:0;background:#fff;display:flex;border-top:1px solid #eee;padding:10px 0}
.nav div{flex:1;text-align:center;font-size:12px;color:#888} .nav .active{color:#000;font-weight:bold}
.tx{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #f0f0f0;font-size:14px}
</style>
"""

LOGIN_HTML = """
<html><head>""" + BASE_STYLE + """</head><body>
<div style="padding:30px 20px;text-align:center"><h1 style="font-size:32px">GONASA</h1><p>Agent App</p></div>
<div class="card"><form method="POST">
<input name="user" placeholder="Username - agent1">
<input name="pass" type="password" placeholder="Password - 1234">
<button class="btn">LOGIN</button><p style="color:red;text-align:center">{{error}}</p></form></div>
</body></html>
"""

DASH_HTML = """
<html><head>""" + BASE_STYLE + """</head><body>
<div class="top"><div><b>GONASA</b><br><small>Agent 1 • 0764004072</small></div><span>SANDBOX</span></div>

<div class="balance"><small>Available Balance</small><h1>UGX 0</h1><p>Tap to refresh • Last updated now</p></div>

<div class="grid" style="margin:0 15px">
  <div class="action" onclick="window.location='/deposit'"><div>⬇️</div><b>Deposit</b><br><small>Cash In</small></div>
  <div class="action" onclick="window.location='/withdraw'"><div>⬆️</div><b>Withdraw</b><br><small>Cash Out</small></div>
  <div class="action" onclick="window.location='/share-float'"><div>🔄</div><b>Share Float</b><br><small>Send Float</small></div>
  <div class="action" onclick="window.location='/history'"><div>📄</div><b>History</b><br><small>Today</small></div>
</div>

<div class="card"><h3 style="margin:0 0 10px">Recent Transactions</h3>
<div class="tx"><span>MTN Deposit<br><small>0788401754 • Today</small></span><b>UGX 5,000</b></div>
<div class="tx"><span>MTN Withdraw<br><small>077xxxxxxx • Today</small></span><b>UGX 10,000</b></div>
<p style="text-align:center;color:#888;font-size:13px">No more transactions</p></div>

<div class="nav"><div class="active">🏠<br>Home</div><div>💰<br>Float</div><div>📊<br>Report</div><div>👤<br>Profile</div></div>
</body></html>
"""

FORM_HTML = """
<html><head>""" + BASE_STYLE + """</head><body>
<div class="top"><b>← {{title}}</b><span>SANDBOX</span></div>
<div class="card"><h3>{{title}}</h3>
<form method="POST" action="/validate">
<input type="hidden" name="tx_type" value="{{title}}">
<input name="cust_no" placeholder="Customer No. e.g 0788401754" required>
<input name="amount" type="number" placeholder="Amount UGX e.g 5000" required>
<button class="btn">Validate →</button></form>
<p style="font-size:13px;color:#888;text-align:center">Name will be fetched automatically after Validate</p></div>
</body></html>
"""

SHARE_FLOAT_HTML = """
<html><head>""" + BASE_STYLE + """</head><body>
<div class="top"><b>← Share Float</b><span>SANDBOX</span></div>
<div class="card"><h3>Share Float</h3>
<form method="POST" action="/validate">
<input type="hidden" name="tx_type" value="Share Float">
<input name="cust_no" placeholder="Receiver Agent No. e.g 077xxxxxxx" required>
<input name="amount" type="number" placeholder="Amount UGX e.g 50000" required>
<button class="btn">Validate →</button></form>
<p style="font-size:13px;color:#888;text-align:center">Send float to another agent</p></div>
</body></html>
"""

HISTORY_HTML = """
<html><head>""" + BASE_STYLE + """</head><body>
<div class="top"><b>← History</b><span>SANDBOX</span></div>
<div class="card"><h3>Today's History</h3>
<div class="tx"><span>MTN Deposit<br><small>0788401754 • 10:15 AM</small></span><b>UGX 5,000</b></div>
<div class="tx"><span>MTN Withdraw<br><small>077xxxxxxx • 09:40 AM</small></span><b>UGX 10,000</b></div>
<div class="tx"><span>Share Float<br><small>076xxxxxxx • 09:00 AM</small></span><b>UGX 50,000</b></div>
</div>
<div style="text-align:center"><a href="/dashboard">← Back to Home</a></div>
</body></html>
"""

CONFIRM_HTML = """
<html><head><meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:Arial;background:#1a1a2e;color:#fff;padding:20px;margin:0}
h3{text-align:center;font-size:22px;margin:20px 0 30px}
.row{display:flex;justify-content:space-between;padding:14px 0;border-bottom:1px solid #333;font-size:16px}
.row span:first-child{color:#aaa} .row span:last-child{font-weight:bold;text-align:right}
.total{background:#2a2a45;padding:15px;border-radius:10px;margin-top:20px}
.btns{display:flex;gap:10px;margin-top:25px}
.cancel{flex:1;background:#e63946;color:#fff;padding:16px;border:none;border-radius:10px;font-size:18px;font-weight:bold}
.confirm{flex:1;background:#1d3557;color:#fff;padding:16px;border:none;border-radius:10px;font-size:18px;font-weight:bold}
</style></head>
<body><h3>Confirm Payment</h3>
<div class="row"><span>Customer No.</span><span>{{cust_no}}</span></div>
<div class="row"><span>Customer Name</span><span>{{cust_name}}</span></div>
<div class="row"><span>Item</span><span>{{tx_type}}</span></div>
<div class="row"><span>Biller</span><span>MTN Mobile Money</span></div>
<div class="row"><span>Payment Mode</span><span>Cash</span></div>
<div class="total">
<div class="row" style="border:none"><span>Amount UGX</span><span>{{amount}}</span></div>
<div class="row" style="border:none"><span>Excise Duty UGX</span><span>0</span></div>
<div class="row" style="border:none"><span>Surcharge UGX</span><span>0</span></div>
<div class="row" style="border:none"><span>Total UGX</span><span>{{amount}}</span></div>
</div>
<div class="btns">
<button class="cancel" onclick="window.location='/dashboard'">Cancel</button>
<form method="POST" action="/confirm" style="flex:1"><button class="confirm">Confirm</button></form>
</div></body></html>
"""

@app.route("/", methods=["GET","POST"])
def login():
    error=""
    if request.method=="POST":
        if request.form.get("user")=="agent1" and request.form.get("pass")=="1234":
            session["logged"]=True
            return redirect("/dashboard")
        error="Wrong login"
    return render_template_string(LOGIN_HTML, error=error)

@app.route("/dashboard")
def dashboard():
    if not session.get("logged"): return redirect("/")
    return render_template_string(DASH_HTML)

@app.route("/deposit")
def deposit():
    return render_template_string(FORM_HTML, title="MTN Deposit")

@app.route("/withdraw")
def withdraw():
    return render_template_string(FORM_HTML, title="MTN Withdraw")

@app.route("/share-float")
def share_float():
    return render_template_string(SHARE_FLOAT_HTML)

@app.route("/history")
def history():
    return render_template_string(HISTORY_HTML)

@app.route("/validate", methods=["POST"])
def validate():
    cust_no=request.form.get("cust_no"); amount=request.form.get("amount"); tx_type=request.form.get("tx_type")
    cust_name="BRIAN GONASA" if cust_no=="0788401754" else "CUSTOMER NAME"
    return render_template_string(CONFIRM_HTML, cust_no=cust_no, cust_name=cust_name, tx_type=tx_type, amount=amount)

@app.route("/confirm", methods=["POST"])
def confirm():
    return "<h2 style='font-family:Arial;text-align:center'>✅ Transaction Sent to MTN...</h2><p style='text-align:center'><a href='/dashboard'>Back to Home</a></p>"

if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000)
