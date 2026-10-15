import os, sqlite3, secrets, hashlib, hmac

from datetime import datetime, date

from functools import wraps

from flask import Flask, request, jsonify, session, g, send_from_directory



BASE = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(BASE, "estateflow.db"))

app = Flask(__name__, static_folder="static")

app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")

app.config.update(SESSION_COOKIE_HTTPONLY=True, SESSION_COOKIE_SAMESITE="Lax")



def db():

    if "db" not in g:

        g.db = sqlite3.connect(DB_PATH, timeout=15, isolation_level=None)

        g.db.row_factory = sqlite3.Row

        g.db.execute("PRAGMA foreign_keys = ON")

        g.db.execute("PRAGMA journal_mode = WAL")

    return g.db



@app.teardown_appcontext

def close_db(exc):

    conn = g.pop("db", None)

    if conn: conn.close()



def pw_hash(password, salt=None):

    salt = salt or secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180000).hex()

    return salt + "$" + digest



def pw_check(password, stored):

    try:

        salt, digest = stored.split("$", 1)

        candidate = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 180000).hex()

        return hmac.compare_digest(candidate, digest)

    except Exception:

        return False



def init_db():

    conn = sqlite3.connect(DB_PATH)

    conn.execute("PRAGMA foreign_keys = ON")

    conn.executescript("""

    CREATE TABLE IF NOT EXISTS users (

      id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL,

      password_hash TEXT NOT NULL, role TEXT NOT NULL CHECK(role IN ('Admin','Sales Employee')),

      active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

    );

    CREATE TABLE IF NOT EXISTS leads (

      id INTEGER PRIMARY KEY, name TEXT NOT NULL, email TEXT, phone TEXT NOT NULL,

      source TEXT NOT NULL DEFAULT 'Website', stage TEXT NOT NULL DEFAULT 'New'

        CHECK(stage IN ('New','Contacted','Site Visit','Interested','Negotiation','Booked','Lost')),

      assigned_to INTEGER REFERENCES users(id), follow_up TEXT, budget REAL,

      property_interest TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

      updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

    );

    CREATE TABLE IF NOT EXISTS lead_notes (

      id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,

      user_id INTEGER NOT NULL REFERENCES users(id), note TEXT NOT NULL,

      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

    );

    CREATE TABLE IF NOT EXISTS projects (

      id INTEGER PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL,

      description TEXT DEFAULT '', created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP

    );

    CREATE TABLE IF NOT EXISTS buildings (

      id INTEGER PRIMARY KEY, project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,

      name TEXT NOT NULL

    );

    CREATE TABLE IF NOT EXISTS units (

      id INTEGER PRIMARY KEY, building_id INTEGER NOT NULL REFERENCES buildings(id) ON DELETE CASCADE,

      unit_number TEXT NOT NULL, type TEXT NOT NULL, area_sqft INTEGER,

      price REAL NOT NULL CHECK(price >= 0),

      status TEXT NOT NULL DEFAULT 'Available' CHECK(status IN ('Available','Booked','Blocked')),

      UNIQUE(building_id, unit_number)

    );

    CREATE TABLE IF NOT EXISTS bookings (

      id INTEGER PRIMARY KEY, lead_id INTEGER NOT NULL REFERENCES leads(id),

      unit_id INTEGER NOT NULL REFERENCES units(id), created_by INTEGER NOT NULL REFERENCES users(id),

      status TEXT NOT NULL DEFAULT 'Confirmed' CHECK(status IN ('Confirmed','Cancelled')),

      amount REAL NOT NULL, booked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,

      cancelled_at TEXT

    );

    CREATE UNIQUE INDEX IF NOT EXISTS one_active_booking_per_unit

      ON bookings(unit_id) WHERE status = 'Confirmed';

    CREATE INDEX IF NOT EXISTS lead_stage_idx ON leads(stage);

    CREATE INDEX IF NOT EXISTS lead_followup_idx ON leads(follow_up);

    """)

    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]

    if count == 0:

        conn.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",

                     ("Aarav Sharma","admin@estateflow.local",pw_hash("ChangeMe123!"),"Admin"))

        conn.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",

                     ("Priya Nair","sales@estateflow.local",pw_hash("ChangeMe123!"),"Sales Employee"))

        conn.execute("INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)",

                     ("Rahul Menon","rahul@estateflow.local",pw_hash("ChangeMe123!"),"Sales Employee"))

        conn.execute("INSERT INTO projects(name,location,description) VALUES(?,?,?)",

                     ("The Grove Residences","OMR, Chennai","Contemporary homes with landscaped open spaces."))

        conn.execute("INSERT INTO projects(name,location,description) VALUES(?,?,?)",

                     ("Azure Heights","Porur, Chennai","Connected city living with thoughtful amenities."))

        conn.execute("INSERT INTO buildings(project_id,name) VALUES(1,'Block A')")

        conn.execute("INSERT INTO buildings(project_id,name) VALUES(1,'Block B')")

        conn.execute("INSERT INTO buildings(project_id,name) VALUES(2,'Tower 1')")

        units = [

          (1,"A-101","2 BHK",1120,7850000),(1,"A-102","2 BHK",1180,8250000),

          (1,"A-201","3 BHK",1540,11200000),(1,"A-202","3 BHK",1600,11900000),

          (2,"B-101","1 BHK",720,5100000),(2,"B-204","2 BHK",1210,8600000),

          (3,"T1-301","2 BHK",1100,7400000),(3,"T1-302","3 BHK",1490,10300000)]

        conn.executemany("INSERT INTO units(building_id,unit_number,type,area_sqft,price) VALUES(?,?,?,?,?)",units)

        conn.execute("""INSERT INTO leads(name,email,phone,source,stage,assigned_to,follow_up,budget,property_interest)

          VALUES('Meera Krishnan','meera@example.com','9876543210','Website','Interested',2,date('now','+1 day'),9000000,'2 BHK')""")

        conn.execute("""INSERT INTO leads(name,email,phone,source,stage,assigned_to,follow_up,budget,property_interest)

          VALUES('Arjun Kumar','arjun@example.com','9876501234','Referral','Site Visit',2,date('now'),12000000,'3 BHK')""")

        conn.execute("""INSERT INTO leads(name,email,phone,source,stage,assigned_to,follow_up,budget,property_interest)

          VALUES('Nisha Patel','nisha@example.com','9890011223','Property Portal','New',3,date('now','+3 day'),8000000,'2 BHK')""")

    conn.commit()

    conn.close()



STAGES = ['New','Contacted','Site Visit','Interested','Negotiation','Booked','Lost']

def current_user():

    uid = session.get("user_id")

    return db().execute("SELECT id,name,email,role FROM users WHERE id=? AND active=1",(uid,)).fetchone() if uid else None



def login_required(fn):

    @wraps(fn)

    def wrapped(*args, **kwargs):

        if not current_user(): return jsonify(error="Please sign in to continue."), 401

        return fn(*args, **kwargs)

    return wrapped



def admin_required(fn):

    @wraps(fn)

    def wrapped(*args, **kwargs):

        u=current_user()

        if not u: return jsonify(error="Please sign in to continue."),401

        if u["role"]!="Admin": return jsonify(error="Administrator access is required."),403

        return fn(*args, **kwargs)

    return wrapped



def rowdict(row): return dict(row) if row else None

def body(): return request.get_json(silent=True) or {}

def err(message, code=400): return jsonify(error=message), code



@app.get("/")

def index(): return send_from_directory("static","index.html")

@app.get("/api/health")

def health(): return jsonify(status="ok", app="EstateFlow CRM")



@app.post("/api/auth/login")

def login():

    data=body(); email=(data.get("email") or "").strip().lower(); password=data.get("password") or ""

    user=db().execute("SELECT * FROM users WHERE email=? AND active=1",(email,)).fetchone()

    if not user or not pw_check(password,user["password_hash"]): return err("Email or password is incorrect.",401)

    session.clear(); session["user_id"]=user["id"]

    return jsonify(user={"id":user["id"],"name":user["name"],"email":user["email"],"role":user["role"]})



@app.post("/api/auth/logout")

def logout(): session.clear(); return jsonify(ok=True)

@app.get("/api/auth/me")

def me():

    u=current_user()

    return (jsonify(user=rowdict(u)) if u else err("Not signed in.",401))



@app.get("/api/users")

@login_required

def users():

    return jsonify(users=[rowdict(r) for r in db().execute("SELECT id,name,email,role FROM users WHERE active=1 ORDER BY name")])



@app.get("/api/dashboard")

@login_required

def dashboard():

    d=db(); u=current_user()

    where="" if u["role"]=="Admin" else " WHERE assigned_to=?"

    params=() if u["role"]=="Admin" else (u["id"],)

    total=d.execute("SELECT COUNT(*) FROM leads"+where,params).fetchone()[0]

    stages=[dict(r) for r in d.execute("SELECT stage,COUNT(*) count FROM leads"+where+" GROUP BY stage",params)]

    follow_where=(" WHERE " if not where else " AND ")+"follow_up IS NOT NULL AND follow_up<=date('now','+7 day') AND stage NOT IN ('Booked','Lost')"

    followups=d.execute("SELECT COUNT(*) FROM leads"+where+follow_where,params).fetchone()[0]

    booked=d.execute("SELECT COUNT(*) FROM bookings WHERE status='Confirmed'"+("" if u["role"]=="Admin" else " AND created_by=?"),(() if u["role"]=="Admin" else (u["id"],))).fetchone()[0]

    revenue=d.execute("SELECT COALESCE(SUM(amount),0) FROM bookings WHERE status='Confirmed'"+("" if u["role"]=="Admin" else " AND created_by=?"),(() if u["role"]=="Admin" else (u["id"],))).fetchone()[0]

    recent=d.execute("""SELECT l.id,l.name,l.stage,l.follow_up,l.phone,u.name assigned_name FROM leads l

      LEFT JOIN users u ON u.id=l.assigned_to"""+where+" ORDER BY l.updated_at DESC LIMIT 6",params).fetchall()

    return jsonify(total_leads=total, stages=stages, followups=followups, bookings=booked, booked_value=revenue,

                   available_units=d.execute("SELECT COUNT(*) FROM units WHERE status='Available'").fetchone()[0],

                   recent=[rowdict(r) for r in recent])



@app.get("/api/leads")

@login_required

def list_leads():

    u=current_user(); q=(request.args.get("q") or "").strip(); stage=request.args.get("stage",""); owner=request.args.get("owner","")

    sql="""SELECT l.*,u.name assigned_name FROM leads l LEFT JOIN users u ON u.id=l.assigned_to WHERE 1=1"""

    p=[]

    if u["role"]!="Admin": sql+=" AND l.assigned_to=?"; p.append(u["id"])

    if q:

        sql+=" AND (l.name LIKE ? OR l.email LIKE ? OR l.phone LIKE ? OR l.property_interest LIKE ?)"

        p += [f"%{q}%"]*4

    if stage: sql+=" AND l.stage=?"; p.append(stage)

    if owner and u["role"]=="Admin": sql+=" AND l.assigned_to=?"; p.append(owner)

    sql+=" ORDER BY l.updated_at DESC"

    return jsonify(leads=[rowdict(r) for r in db().execute(sql,p)], stages=STAGES)



def can_access_lead(lead):

    u=current_user()

    return lead and (u["role"]=="Admin" or lead["assigned_to"]==u["id"])



@app.post("/api/leads")

@login_required

def create_lead():

    x=body(); name=(x.get("name") or "").strip(); phone=(x.get("phone") or "").strip()

    if not name or not phone: return err("Name and phone number are required.")

    stage=x.get("stage","New")

    if stage not in STAGES: return err("Choose a valid lead stage.")

    u=current_user(); assigned=x.get("assigned_to") if u["role"]=="Admin" else u["id"]

    if assigned and not db().execute("SELECT id FROM users WHERE id=? AND active=1",(assigned,)).fetchone(): return err("Assigned employee was not found.")

    try:

        cur=db().execute("""INSERT INTO leads(name,email,phone,source,stage,assigned_to,follow_up,budget,property_interest)

          VALUES(?,?,?,?,?,?,?,?,?)""",(name,(x.get("email") or "").strip() or None,phone,x.get("source") or "Website",stage,assigned,

          x.get("follow_up") or None,float(x["budget"]) if x.get("budget") not in (None,"") else None,(x.get("property_interest") or "").strip() or None))

        return jsonify(id=cur.lastrowid),201

    except (ValueError,sqlite3.IntegrityError): return err("Please check the lead details.")



@app.patch("/api/leads/<int:lid>")

@login_required

def update_lead(lid):

    d=db(); lead=d.execute("SELECT * FROM leads WHERE id=?",(lid,)).fetchone()

    if not can_access_lead(lead): return err("Lead not found or access denied.",404)

    x=body(); allowed={"name","email","phone","source","stage","assigned_to","follow_up","budget","property_interest"}

    values={k:v for k,v in x.items() if k in allowed}

    if "name" in values and not str(values["name"]).strip(): return err("Name is required.")

    if "phone" in values and not str(values["phone"]).strip(): return err("Phone is required.")

    if "stage" in values and values["stage"] not in STAGES: return err("Choose a valid lead stage.")

    u=current_user()

    if u["role"]!="Admin": values.pop("assigned_to",None)

    if "assigned_to" in values and values["assigned_to"] and not d.execute("SELECT id FROM users WHERE id=? AND active=1",(values["assigned_to"],)).fetchone(): return err("Assigned employee was not found.")

    if "budget" in values:

        try: values["budget"]=float(values["budget"]) if values["budget"] not in ("",None) else None

        except: return err("Budget must be a number.")

    for k in ("email","follow_up","property_interest"):

        if k in values and values[k]=="": values[k]=None

    if not values: return jsonify(ok=True)

    sql=", ".join(f"{k}=?" for k in values)+" , updated_at=CURRENT_TIMESTAMP"

    try: d.execute(f"UPDATE leads SET {sql} WHERE id=?",list(values.values())+[lid])

    except sqlite3.IntegrityError: return err("Could not update lead.")

    return jsonify(ok=True)



@app.get("/api/leads/<int:lid>/notes")

@login_required

def get_notes(lid):

    lead=db().execute("SELECT * FROM leads WHERE id=?",(lid,)).fetchone()

    if not can_access_lead(lead): return err("Lead not found or access denied.",404)

    rows=db().execute("""SELECT n.*,u.name user_name FROM lead_notes n JOIN users u ON u.id=n.user_id

      WHERE lead_id=? ORDER BY created_at DESC""",(lid,))

    return jsonify(notes=[rowdict(r) for r in rows])



@app.post("/api/leads/<int:lid>/notes")

@login_required

def add_note(lid):

    lead=db().execute("SELECT * FROM leads WHERE id=?",(lid,)).fetchone()

    if not can_access_lead(lead): return err("Lead not found or access denied.",404)

    note=(body().get("note") or "").strip()

    if not note: return err("Write a note before saving.")

    if len(note)>2000: return err("Notes must be 2,000 characters or fewer.")

    cur=db().execute("INSERT INTO lead_notes(lead_id,user_id,note) VALUES(?,?,?)",(lid,current_user()["id"],note))

    db().execute("UPDATE leads SET updated_at=CURRENT_TIMESTAMP WHERE id=?",(lid,))

    return jsonify(id=cur.lastrowid),201



@app.get("/api/properties")

@login_required

def properties():

    q=(request.args.get("q") or "").strip(); status=request.args.get("status","")

    sql="""SELECT un.*,b.name building_name,p.name project_name,p.location FROM units un

      JOIN buildings b ON b.id=un.building_id JOIN projects p ON p.id=b.project_id WHERE 1=1"""

    args=[]

    if q:

        sql+=" AND (un.unit_number LIKE ? OR un.type LIKE ? OR b.name LIKE ? OR p.name LIKE ? OR p.location LIKE ?)"

        args += [f"%{q}%"]*5

    if status: sql+=" AND un.status=?"; args.append(status)

    sql+=" ORDER BY p.name,b.name,un.unit_number"

    return jsonify(units=[rowdict(r) for r in db().execute(sql,args)],

      projects=[rowdict(r) for r in db().execute("SELECT * FROM projects ORDER BY name")])



@app.post("/api/properties/projects")

@admin_required

def create_project():

    x=body(); name=(x.get("name") or "").strip(); location=(x.get("location") or "").strip()

    if not name or not location: return err("Project name and location are required.")

    cur=db().execute("INSERT INTO projects(name,location,description) VALUES(?,?,?)",(name,location,(x.get("description") or "").strip()))

    return jsonify(id=cur.lastrowid),201



@app.post("/api/properties/units")

@admin_required

def create_unit():

    x=body()

    try:

        building=int(x.get("building_id")); price=float(x.get("price")); area=int(x.get("area_sqft") or 0)

    except: return err("Building, price and area must be valid numbers.")

    if not (x.get("unit_number") or "").strip() or not (x.get("type") or "").strip() or price<0: return err("Unit number, type and a valid price are required.")

    try:

        cur=db().execute("INSERT INTO units(building_id,unit_number,type,area_sqft,price) VALUES(?,?,?,?,?)",

          (building,x["unit_number"].strip(),x["type"].strip(),area,price))

        return jsonify(id=cur.lastrowid),201

    except sqlite3.IntegrityError: return err("Unit could not be created. Check the building and unit number.")



@app.get("/api/bookings")

@login_required

def bookings():

    u=current_user()

    sql="""SELECT bk.*,l.name customer_name,l.phone,un.unit_number,un.type,b.name building_name,p.name project_name,p.location,usr.name booked_by

      FROM bookings bk JOIN leads l ON l.id=bk.lead_id JOIN units un ON un.id=bk.unit_id

      JOIN buildings b ON b.id=un.building_id JOIN projects p ON p.id=b.project_id JOIN users usr ON usr.id=bk.created_by"""

    args=[]

    if u["role"]!="Admin": sql+=" WHERE bk.created_by=?"; args.append(u["id"])

    sql+=" ORDER BY bk.booked_at DESC"

    return jsonify(bookings=[rowdict(r) for r in db().execute(sql,args)])



@app.post("/api/bookings")

@login_required

def create_booking():

    x=body(); u=current_user()

    try: lead_id=int(x.get("lead_id")); unit_id=int(x.get("unit_id"))

    except: return err("Select a lead and a property unit.")

    d=db()

    lead=d.execute("SELECT * FROM leads WHERE id=?",(lead_id,)).fetchone()

    if not can_access_lead(lead): return err("Lead not found or access denied.",404)

    # BEGIN IMMEDIATE serializes competing writers; the unique index is a second line of defense.

    try:

        d.execute("BEGIN IMMEDIATE")

        unit=d.execute("SELECT * FROM units WHERE id=?",(unit_id,)).fetchone()

        if not unit: d.execute("ROLLBACK"); return err("Property unit was not found.",404)

        if unit["status"]!="Available":

            d.execute("ROLLBACK"); return err("This unit is no longer available. Refresh inventory and choose another unit.",409)

        cur=d.execute("INSERT INTO bookings(lead_id,unit_id,created_by,amount) VALUES(?,?,?,?)",(lead_id,unit_id,u["id"],unit["price"]))

        d.execute("UPDATE units SET status='Booked' WHERE id=? AND status='Available'",(unit_id,))

        d.execute("UPDATE leads SET stage='Booked',updated_at=CURRENT_TIMESTAMP WHERE id=?",(lead_id,))

        d.execute("COMMIT")

        return jsonify(id=cur.lastrowid),201

    except sqlite3.IntegrityError:

        try: d.execute("ROLLBACK")

        except: pass

        return err("This unit has already been booked. Refresh inventory.",409)

    except Exception:

        try: d.execute("ROLLBACK")

        except: pass

        app.logger.exception("Booking failed")

        return err("Booking could not be completed. Please try again.",500)



@app.post("/api/bookings/<int:bid>/cancel")

@admin_required

def cancel_booking(bid):

    d=db()

    try:

        d.execute("BEGIN IMMEDIATE")

        bk=d.execute("SELECT * FROM bookings WHERE id=?",(bid,)).fetchone()

        if not bk: d.execute("ROLLBACK"); return err("Booking not found.",404)

        if bk["status"]=="Cancelled": d.execute("ROLLBACK"); return err("Booking is already cancelled.",409)

        d.execute("UPDATE bookings SET status='Cancelled',cancelled_at=CURRENT_TIMESTAMP WHERE id=?",(bid,))

        d.execute("UPDATE units SET status='Available' WHERE id=?",(bk["unit_id"],))

        d.execute("UPDATE leads SET stage='Interested',updated_at=CURRENT_TIMESTAMP WHERE id=? AND stage='Booked'",(bk["lead_id"],))

        d.execute("COMMIT")

        return jsonify(ok=True)

    except Exception:

        try: d.execute("ROLLBACK")

        except: pass

        return err("Could not cancel booking.",500)



@app.errorhandler(404)

def not_found(e):

    if request.path.startswith("/api/"): return jsonify(error="Endpoint not found."),404

    return send_from_directory("static","index.html")

@app.errorhandler(500)

def server_error(e): return jsonify(error="Unexpected server error. Please try again."),500



init_db()

if __name__ == "__main__":

    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)), debug=False)
