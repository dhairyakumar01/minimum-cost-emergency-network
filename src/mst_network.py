"""MST algorithms for facility locations; edge weights are Haversine km."""
import math, heapq
from itertools import combinations
import pandas as pd
EARTH_KM = 6371.0088
REQUIRED = {'facility_id','facility_name','facility_type','latitude','longitude'}

def haversine_km(lat1, lon1, lat2, lon2):
    p1,p2=math.radians(lat1),math.radians(lat2)
    dp=math.radians(lat2-lat1); dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*EARTH_KM*math.asin(min(1,math.sqrt(a)))

def load_facilities(path):
    df=pd.read_csv(path)
    missing=REQUIRED-set(df.columns)
    if missing: raise ValueError(f'Missing columns: {sorted(missing)}')
    for c in ['latitude','longitude']: df[c]=pd.to_numeric(df[c],errors='coerce')
    if df[['latitude','longitude']].isna().any().any(): raise ValueError('Missing or invalid coordinates; review data first.')
    if (~df.latitude.between(-90,90)).any() or (~df.longitude.between(-180,180)).any(): raise ValueError('Out-of-range coordinates found.')
    if df.facility_id.duplicated().any(): raise ValueError('Duplicate facility IDs found.')
    return df.reset_index(drop=True)

def build_complete_edges(nodes):
    rows=[]; r=nodes.to_dict('records')
    for i,j in combinations(range(len(r)),2):
        a,b=r[i],r[j]
        rows.append({'u':a['facility_id'],'v':b['facility_id'],'u_name':a['facility_name'],'v_name':b['facility_name'],'u_type':a['facility_type'],'v_type':b['facility_type'],'weight_km':haversine_km(a['latitude'],a['longitude'],b['latitude'],b['longitude'])})
    return pd.DataFrame(rows,columns=['u','v','u_name','v_name','u_type','v_type','weight_km'])

def prim_mst(nodes, edges, track_decisions=False):
    ids=nodes.facility_id.tolist()
    if not ids:
        empty_df = pd.DataFrame(columns=['u','v','u_name','v_name','u_type','v_type','weight_km'])
        return (empty_df, 0.0, {}) if track_decisions else (empty_df, 0.0)
    adj={x:[] for x in ids}
    for e in edges.itertuples(index=False):
        adj[e.u].append((e.weight_km,e.u,e.v,e.u_name,e.v_name,e.u_type,e.v_type))
        adj[e.v].append((e.weight_km,e.v,e.u,e.v_name,e.u_name,e.v_type,e.u_type))
    visited={ids[0]}; heap=[]; chosen=[]
    def push(node):
        for w,s,t,sn,tn,st,tt in adj[node]:
            if t not in visited: heapq.heappush(heap,(w,str(s),str(t),s,t,sn,tn,st,tt))
    push(ids[0])
    while heap and len(visited)<len(ids):
        w,_,__,s,t,sn,tn,st,tt=heapq.heappop(heap)
        if t in visited: continue
        visited.add(t); chosen.append((s,t,sn,tn,st,tt,w)); push(t)
    if len(visited)!=len(ids): raise ValueError('Graph is disconnected.')
    out=pd.DataFrame(chosen,columns=['u','v','u_name','v_name','u_type','v_type','weight_km'])
    if track_decisions:
        return out, float(out.weight_km.sum()), {"accepted": chosen, "rejected": []}
    return out,float(out.weight_km.sum())

def kruskal_mst(nodes, edges, track_decisions=False):
    parent={x:x for x in nodes.facility_id}; rank={x:0 for x in parent}
    def find(x):
        while parent[x]!=x: parent[x]=parent[parent[x]]; x=parent[x]
        return x
    def union(a,b):
        a,b=find(a),find(b)
        if a==b:return False
        if rank[a]<rank[b]:a,b=b,a
        parent[b]=a
        if rank[a]==rank[b]:rank[a]+=1
        return True
    chosen=[]; rejected=[]; target=max(0,len(nodes)-1)
    for e in edges.sort_values(['weight_km','u','v'],kind='mergesort').itertuples(index=False):
        if union(e.u,e.v):
            chosen.append((e.u,e.v,getattr(e,'u_name',''),getattr(e,'v_name',''),getattr(e,'u_type',''),getattr(e,'v_type',''),float(e.weight_km)))
            if not track_decisions and len(chosen)==target: break
        else:
            if track_decisions:
                rejected.append({
                    "u": e.u,
                    "v": e.v,
                    "u_name": getattr(e, "u_name", ""),
                    "v_name": getattr(e, "v_name", ""),
                    "u_type": getattr(e, "u_type", ""),
                    "v_type": getattr(e, "v_type", ""),
                    "weight_km": float(e.weight_km),
                    "reason": "Rejected: Adding edge would close a cycle in Kruskal's spanning forest.",
                })
    if len(chosen)!=target: raise ValueError('Could not construct spanning tree.')
    out=pd.DataFrame(chosen,columns=['u','v','u_name','v_name','u_type','v_type','weight_km'])
    if track_decisions:
        return out, float(out.weight_km.sum()), {"accepted": chosen, "rejected": rejected}
    return out,float(out.weight_km.sum())
