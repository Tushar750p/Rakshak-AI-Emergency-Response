from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from hashlib import sha256
import json
import sqlite3
import uuid

from fastapi import FastAPI, File, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "backend" / "data"
UPLOADS = DATA / "uploads"
DB = DATA / "rakshak.db"
UPLOADS.mkdir(parents=True, exist_ok=True)

class IncidentIn(BaseModel):
    type: str = Field(min_length=1, max_length=80)
    latitude: float | None = None
    longitude: float | None = None
    accuracy: float | None = None
    description: str = Field(default="", max_length=2000)
    reporter_id: str | None = None
    live_video: bool = False

class StatusIn(BaseModel):
    status: str

class LocationIn(BaseModel):
    latitude: float
    longitude: float
    accuracy: float | None = None

class Hub:
    def __init__(self): self.clients: set[WebSocket] = set()
    async def broadcast(self, payload):
        dead=[]
        for ws in self.clients:
            try: await ws.send_json(payload)
            except Exception: dead.append(ws)
        for ws in dead: self.clients.discard(ws)

hub = Hub()

def conn():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    return c

def init_db():
    c=conn()
    c.executescript('''
    CREATE TABLE IF NOT EXISTS incidents(
      id TEXT PRIMARY KEY, type TEXT NOT NULL, status TEXT NOT NULL,
      priority TEXT NOT NULL, latitude REAL, longitude REAL, accuracy REAL,
      description TEXT, reporter_id TEXT, live_video INTEGER NOT NULL DEFAULT 0,
      evidence_name TEXT, evidence_hash TEXT, created_at TEXT NOT NULL,
      updated_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS locations(
      id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL,
      latitude REAL NOT NULL, longitude REAL NOT NULL, accuracy REAL,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS events(
      id INTEGER PRIMARY KEY AUTOINCREMENT, incident_id TEXT NOT NULL,
      event TEXT NOT NULL, details TEXT, created_at TEXT NOT NULL
    );
    ''')
    c.commit(); c.close()

def priority(t):
    return "CRITICAL" if t in {"Violence","Fire"} else "HIGH" if t in {"Accident","Medical Emergency"} else "MEDIUM"

def row(r):
    if not r: return None
    d=dict(r); d["live_video"]=bool(d["live_video"]); return d

def public_row(r):
    d=row(r)
    if not d: return None
    return {k:d[k] for k in ("id","type","status","priority","latitude","longitude","created_at","updated_at","live_video")}

@asynccontextmanager
async def lifespan(app):
    init_db(); yield

app=FastAPI(title="Rakshak AI Emergency API", version="1.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.get("/api/health")
def health(): return {"ok":True,"service":"rakshak-api","time":datetime.now(timezone.utc).isoformat()}

@app.post("/api/incidents")
async def create_incident(payload: IncidentIn):
    now=datetime.now(timezone.utc).isoformat(); iid="RK-"+uuid.uuid4().hex[:8].upper()
    p=priority(payload.type)
    c=conn(); c.execute("INSERT INTO incidents VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(iid,payload.type,"OPEN",p,payload.latitude,payload.longitude,payload.accuracy,payload.description,payload.reporter_id,int(payload.live_video),None,None,now,now)); c.execute("INSERT INTO events(incident_id,event,details,created_at) VALUES(?,?,?,?)",(iid,"INCIDENT_CREATED",json.dumps({"source":"public"}),now)); c.commit(); c.close()
    c=conn(); incident=row(c.execute("SELECT * FROM incidents WHERE id=?",(iid,)).fetchone()); c.close()
    await hub.broadcast({"event":"incident.created","incident":incident})
    return incident

@app.post("/api/incidents/{incident_id}/evidence")
async def upload_evidence(incident_id: str, file: UploadFile = File(...)):
    if file.content_type not in {"image/jpeg","image/png","image/webp","image/gif","video/mp4","video/webm","video/quicktime"}:
        raise HTTPException(400,"Unsupported evidence type")
    data=await file.read()
    if len(data)>25*1024*1024: raise HTTPException(413,"Evidence exceeds 25 MB")
    digest=sha256(data).hexdigest(); ext=Path(file.filename or "evidence.bin").suffix.lower()[:10]; name=f"{incident_id}-{uuid.uuid4().hex}{ext}"
    (UPLOADS/name).write_bytes(data)
    now=datetime.now(timezone.utc).isoformat(); c=conn(); cur=c.execute("UPDATE incidents SET evidence_name=?, evidence_hash=?, updated_at=? WHERE id=?",(name,digest,now,incident_id)); c.execute("INSERT INTO events(incident_id,event,details,created_at) VALUES(?,?,?,?)",(incident_id,"EVIDENCE_UPLOADED",json.dumps({"sha256":digest,"filename":file.filename}),now)); c.commit(); c.close()
    if cur.rowcount==0: raise HTTPException(404,"Incident not found")
    c=conn(); incident=row(c.execute("SELECT * FROM incidents WHERE id=?",(incident_id,)).fetchone()); c.close()
    await hub.broadcast({"event":"incident.updated","incident":incident})
    return {"incident":incident,"sha256":digest}

@app.get("/api/incidents")
def list_incidents(limit:int=50, active_only:bool=False):
    c=conn(); q="SELECT * FROM incidents" + (" WHERE status NOT IN ('RESOLVED','CANCELLED')" if active_only else "") + " ORDER BY created_at DESC LIMIT ?"; rows=c.execute(q,(min(max(limit,1),200),)).fetchall(); c.close(); return [row(x) for x in rows]

@app.get("/api/incidents/{incident_id}")
def get_incident(incident_id:str):
    c=conn(); r=c.execute("SELECT * FROM incidents WHERE id=?",(incident_id,)).fetchone(); events=c.execute("SELECT * FROM events WHERE incident_id=? ORDER BY created_at",(incident_id,)).fetchall(); c.close()
    if not r: raise HTTPException(404,"Incident not found")
    d=row(r); d["events"]= [dict(x) for x in events]; return d

@app.get("/api/public/summary")
def public_summary():
    c=conn()
    today=datetime.now(timezone.utc).date().isoformat()
    totals=c.execute("SELECT COUNT(*) total, SUM(CASE WHEN status NOT IN ('RESOLVED','CANCELLED') THEN 1 ELSE 0 END) active, SUM(CASE WHEN priority='CRITICAL' AND status NOT IN ('RESOLVED','CANCELLED') THEN 1 ELSE 0 END) critical FROM incidents").fetchone()
    daily=c.execute("SELECT type, COUNT(*) count FROM incidents WHERE substr(created_at,1,10)=? GROUP BY type ORDER BY count DESC",(today,)).fetchall()
    recent=c.execute("SELECT * FROM incidents WHERE substr(created_at,1,10)=? ORDER BY created_at DESC LIMIT 100",(today,)).fetchall()
    c.close()
    return {"date":today,"totals":{"all":totals["total"] or 0,"active":totals["active"] or 0,"critical_active":totals["critical"] or 0},"by_type":[dict(x) for x in daily],"incidents":[public_row(x) for x in recent]}

@app.patch("/api/incidents/{incident_id}/status")
async def update_status(incident_id:str, payload:StatusIn):
    allowed={"OPEN","ACKNOWLEDGED","DISPATCHED","ON_SCENE","RESOLVED","CANCELLED"}
    if payload.status not in allowed: raise HTTPException(400,"Invalid status")
    now=datetime.now(timezone.utc).isoformat(); c=conn(); cur=c.execute("UPDATE incidents SET status=?,updated_at=? WHERE id=?",(payload.status,now,incident_id)); c.execute("INSERT INTO events(incident_id,event,details,created_at) VALUES(?,?,?,?)",(incident_id,"STATUS_CHANGED",json.dumps({"status":payload.status}),now)); c.commit(); c.close()
    if cur.rowcount==0: raise HTTPException(404,"Incident not found")
    c=conn(); incident=row(c.execute("SELECT * FROM incidents WHERE id=?",(incident_id,)).fetchone()); c.close(); await hub.broadcast({"event":"incident.updated","incident":incident}); return incident

@app.post("/api/incidents/{incident_id}/location")
async def add_location(incident_id:str,payload:LocationIn):
    now=datetime.now(timezone.utc).isoformat(); c=conn(); exists=c.execute("SELECT id FROM incidents WHERE id=?",(incident_id,)).fetchone()
    if not exists: c.close(); raise HTTPException(404,"Incident not found")
    c.execute("INSERT INTO locations(incident_id,latitude,longitude,accuracy,created_at) VALUES(?,?,?,?,?)",(incident_id,payload.latitude,payload.longitude,payload.accuracy,now)); c.execute("UPDATE incidents SET latitude=?,longitude=?,accuracy=?,updated_at=? WHERE id=?",(payload.latitude,payload.longitude,payload.accuracy,now,incident_id)); c.commit(); c.close()
    event={"event":"location.updated","incident_id":incident_id,"latitude":payload.latitude,"longitude":payload.longitude,"accuracy":payload.accuracy,"created_at":now}; await hub.broadcast(event); return event

@app.websocket("/ws")
async def websocket(ws:WebSocket):
    await ws.accept(); hub.clients.add(ws)
    try:
        await ws.send_json({"event":"connected","clients":len(hub.clients)})
        while True: await ws.receive_text()
    except WebSocketDisconnect: hub.clients.discard(ws)
    except Exception: hub.clients.discard(ws)

@app.get("/evidence/{filename}")
def evidence(filename:str):
    safe=UPLOADS / Path(filename).name
    if not safe.exists(): raise HTTPException(404,"Evidence not found")
    return FileResponse(safe)
