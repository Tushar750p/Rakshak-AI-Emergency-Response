from datetime import datetime, timezone, timedelta
from math import radians, sin, cos, asin, sqrt
import json
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .main import conn, hub

router = APIRouter(prefix="/api")

class WomenSOSIn(BaseModel):
    latitude: float | None = None
    longitude: float | None = None
    accuracy: float | None = None
    silent: bool = False
    trusted_contacts: list[str] = Field(default_factory=list, max_length=10)
    description: str = Field(default="Women safety SOS", max_length=2000)

class ResourceIn(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    type: str = Field(min_length=1, max_length=40)
    latitude: float
    longitude: float
    phone: str | None = Field(default=None, max_length=40)
    integration_status: str = "MANUAL"

class ResponderIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    role: str = Field(min_length=1, max_length=60)
    unit: str = Field(default="", max_length=120)
    latitude: float | None = None
    longitude: float | None = None

class WarningIn(BaseModel):
    event_type: str = Field(min_length=1, max_length=60)
    severity: str = Field(default="HIGH", max_length=20)
    message: str = Field(min_length=1, max_length=1000)
    source: str = Field(min_length=1, max_length=200)
    source_url: str | None = Field(default=None, max_length=500)
    latitude: float | None = None
    longitude: float | None = None
    radius_km: float = Field(default=100, gt=0, le=5000)
    issued_at: str | None = None
    expires_at: str | None = None

def ensure_tables():
    c=conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS resources(id TEXT PRIMARY KEY,name TEXT NOT NULL,type TEXT NOT NULL,latitude REAL NOT NULL,longitude REAL NOT NULL,phone TEXT,integration_status TEXT NOT NULL DEFAULT 'MANUAL');
    CREATE TABLE IF NOT EXISTS responders(id TEXT PRIMARY KEY,name TEXT NOT NULL,role TEXT NOT NULL,unit TEXT,status TEXT NOT NULL DEFAULT 'AVAILABLE',latitude REAL,longitude REAL,last_seen TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS warnings(id TEXT PRIMARY KEY,event_type TEXT NOT NULL,severity TEXT NOT NULL,message TEXT NOT NULL,source TEXT NOT NULL,source_url TEXT,latitude REAL,longitude REAL,radius_km REAL NOT NULL,issued_at TEXT NOT NULL,expires_at TEXT NOT NULL);
    """)
    cols={r[1] for r in c.execute("PRAGMA table_info(incidents)").fetchall()}
    for name,typ in [("women_safety","INTEGER NOT NULL DEFAULT 0"),("silent_sos","INTEGER NOT NULL DEFAULT 0"),("trusted_contacts","TEXT DEFAULT '[]'"),("assigned_responder_id","TEXT")]:
        if name not in cols: c.execute(f"ALTER TABLE incidents ADD COLUMN {name} {typ}")
    c.commit(); c.close()

ensure_tables()

def dist(a,b,c,d):
    p1,p2=radians(a),radians(c); dp=radians(c-a); dl=radians(d-b)
    x=sin(dp/2)**2+cos(p1)*cos(p2)*sin(dl/2)**2
    return 6371*2*asin(sqrt(x))

def incident_dict(r):
    d=dict(r); d["live_video"]=bool(d.get("live_video")); d["women_safety"]=bool(d.get("women_safety")); d["silent_sos"]=bool(d.get("silent_sos")); d["trusted_contacts"]=json.loads(d.get("trusted_contacts") or "[]"); return d

def nearest(lat,lon,types,radius=25):
    c=conn(); rows=c.execute("SELECT * FROM resources WHERE type IN (%s)" % ",".join("?"*len(types)),types).fetchall(); c.close(); out=[]
    for r in rows:
        d=dist(lat,lon,r["latitude"],r["longitude"])
        if d<=radius: out.append({**dict(r),"distance_km":round(d,2)})
    return sorted(out,key=lambda x:x["distance_km"])

@router.post("/women-safety/sos")
async def women_safety_sos(payload: WomenSOSIn):
    now=datetime.now(timezone.utc).isoformat(); iid="RK-"+uuid.uuid4().hex[:8].upper()
    c=conn(); c.execute("INSERT INTO incidents(id,type,status,priority,latitude,longitude,accuracy,description,reporter_id,live_video,evidence_name,evidence_hash,created_at,updated_at,women_safety,silent_sos,trusted_contacts) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(iid,"Women Safety","OPEN","CRITICAL",payload.latitude,payload.longitude,payload.accuracy,payload.description,"women-safety",0,None,None,now,now,1,int(payload.silent),json.dumps(payload.trusted_contacts))); c.execute("INSERT INTO events(incident_id,event,details,created_at) VALUES(?,?,?,?)",(iid,"WOMEN_SOS_TRIGGERED",json.dumps({"silent":payload.silent,"trusted_contacts_count":len(payload.trusted_contacts)}),now)); c.commit(); c.close()
    c=conn(); incident=incident_dict(c.execute("SELECT * FROM incidents WHERE id=?",(iid,)).fetchone()); c.close(); await hub.broadcast({"event":"women.sos","incident":incident}); return {"incident":incident,"dispatch":"REQUIRES_AUTHORIZED_OPERATOR"}

@router.get("/resources/nearby")
def nearby_resources(lat:float,lon:float,radius_km:float=25,resource_type:str|None=None,limit:int=10):
    c=conn();
    if resource_type: rows=c.execute("SELECT * FROM resources WHERE type=?",(resource_type,)).fetchall()
    else: rows=c.execute("SELECT * FROM resources").fetchall()
    c.close(); out=[]
    for r in rows:
        d=dist(lat,lon,r["latitude"],r["longitude"])
        if d<=radius_km: out.append({**dict(r),"distance_km":round(d,2)})
    return sorted(out,key=lambda x:x["distance_km"])[:min(max(limit,1),50)]

@router.get("/incidents/{incident_id}/resources")
def incident_resources(incident_id:str):
    c=conn(); r=c.execute("SELECT type,latitude,longitude,women_safety FROM incidents WHERE id=?",(incident_id,)).fetchone(); c.close()
    if not r: raise HTTPException(404,"Incident not found")
    if r["latitude"] is None: return {"resources":[]}
    types={"Fire":["fire_station","ambulance_base","police_station"],"Medical Emergency":["hospital","ambulance_base"],"Violence":["police_station","hospital","ambulance_base"],"Women Safety":["police_station","hospital","ambulance_base"]}.get(r["type"],["police_station","ambulance_base","hospital","fire_station"])
    return {"resources":nearest(r["latitude"],r["longitude"],types)}

@router.post("/resources")
def add_resource(p:ResourceIn):
    rid="RS-"+uuid.uuid4().hex[:8].upper(); c=conn(); c.execute("INSERT INTO resources VALUES(?,?,?,?,?,?,?)",(rid,p.name,p.type,p.latitude,p.longitude,p.phone,p.integration_status)); c.commit(); c.close(); return {"id":rid,**p.model_dump()}

@router.get("/responders")
def responders():
    c=conn(); r=c.execute("SELECT * FROM responders ORDER BY status,name").fetchall(); c.close(); return [dict(x) for x in r]

@router.post("/responders")
def add_responder(p:ResponderIn):
    rid="RP-"+uuid.uuid4().hex[:8].upper(); now=datetime.now(timezone.utc).isoformat(); c=conn(); c.execute("INSERT INTO responders VALUES(?,?,?,?,?,?,?,?)",(rid,p.name,p.role,p.unit,"AVAILABLE",p.latitude,p.longitude,now)); c.commit(); c.close(); return {"id":rid,"status":"AVAILABLE","last_seen":now,**p.model_dump()}

@router.post("/incidents/{incident_id}/assign/{responder_id}")
async def assign(incident_id:str,responder_id:str):
    now=datetime.now(timezone.utc).isoformat(); c=conn(); inc=c.execute("SELECT id FROM incidents WHERE id=?",(incident_id,)).fetchone(); rp=c.execute("SELECT * FROM responders WHERE id=?",(responder_id,)).fetchone()
    if not inc or not rp: c.close(); raise HTTPException(404,"Incident or responder not found")
    c.execute("UPDATE incidents SET assigned_responder_id=?,status='DISPATCHED',updated_at=? WHERE id=?",(responder_id,now,incident_id)); c.execute("UPDATE responders SET status='BUSY',last_seen=? WHERE id=?",(now,responder_id)); c.execute("INSERT INTO events(incident_id,event,details,created_at) VALUES(?,?,?,?)",(incident_id,"RESPONDER_ASSIGNED",json.dumps({"responder_id":responder_id}),now)); c.commit(); c.close(); await hub.broadcast({"event":"assignment.created","incident_id":incident_id,"responder_id":responder_id}); return {"ok":True,"incident_id":incident_id,"responder_id":responder_id,"status":"DISPATCHED"}

@router.post("/responders/{responder_id}/location")
async def responder_location(responder_id:str,lat:float,lon:float):
    now=datetime.now(timezone.utc).isoformat(); c=conn(); cur=c.execute("UPDATE responders SET latitude=?,longitude=?,last_seen=? WHERE id=?",(lat,lon,now,responder_id)); c.commit(); c.close()
    if not cur.rowcount: raise HTTPException(404,"Responder not found")
    await hub.broadcast({"event":"responder.location","responder_id":responder_id,"latitude":lat,"longitude":lon,"last_seen":now}); return {"ok":True,"last_seen":now}

@router.post("/warnings")
async def add_warning(p:WarningIn):
    now=datetime.now(timezone.utc).isoformat(); wid="WR-"+uuid.uuid4().hex[:8].upper(); issued=p.issued_at or now; expires=p.expires_at or (datetime.now(timezone.utc)+timedelta(days=1)).isoformat(); c=conn(); c.execute("INSERT INTO warnings VALUES(?,?,?,?,?,?,?,?,?,?,?)",(wid,p.event_type,p.severity,p.message,p.source,p.source_url,p.latitude,p.longitude,p.radius_km,issued,expires)); c.commit(); c.close(); payload={"id":wid,**p.model_dump(),"issued_at":issued,"expires_at":expires}; await hub.broadcast({"event":"warning.created","warning":payload}); return payload

@router.get("/warnings/active")
def active_warnings(lat:float|None=None,lon:float|None=None):
    now=datetime.now(timezone.utc).isoformat(); c=conn(); rows=c.execute("SELECT * FROM warnings WHERE expires_at>? ORDER BY CASE severity WHEN 'CRITICAL' THEN 1 WHEN 'HIGH' THEN 2 ELSE 3 END,issued_at DESC",(now,)).fetchall(); c.close(); out=[]
    for r in rows:
        d=dict(r); d["relevant"]=True
        if lat is not None and lon is not None and d["latitude"] is not None and d["longitude"] is not None: d["distance_km"]=round(dist(lat,lon,d["latitude"],d["longitude"]),2); d["relevant"]=d["distance_km"]<=d["radius_km"]
        if d["relevant"]: out.append(d)
    return out
