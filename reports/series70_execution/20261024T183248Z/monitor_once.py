"""Read the current notebook execution progress without changing the experiment."""
import json
import logging
from pathlib import Path
import re
import sys
from datetime import datetime

logging.basicConfig(level=logging.INFO,format="%(message)s",stream=sys.stdout)
b=Path(__file__).resolve().parent
repo=b.parents[2]
s=json.loads((b/"status.json").read_text(encoding="utf-8"))
plan=json.loads((b/"plan.json").read_text(encoding="utf-8"))
x=s["items"][-1]
key=Path(x["notebook"]).name[:2]
planned=next(v["planned_fits"] for v in plan["notebooks"] if v["notebook"]==x["notebook"])
log=b/Path(x["notebook"]).stem/"kernel.log"
t=log.read_text(encoding="utf-8",errors="replace") if log.is_file() else ""
markers={"70":"Ajustando K-Means:","71":"Ajustando mpnet_k","72":"Ajustando DBSCAN","73":"Ajustando DBSCAN","74":"Ajustando HDBSCAN","75":"Ajustando HDBSCAN","76":"Ajustando HDBSCAN"}
count=t.count(markers[key])
kind="ajustes iniciados"
if key=="70":
    m=re.search(r"RUN_ID: ([^ |]+)",t)
    if m:
        count=len(list((repo/"models/tfidf_kmeans"/("202501-202512_"+m.group(1))).glob("*_seed*.pkl")))
        kind="modelos salvos"
logging.info(json.dumps({"time":datetime.now().strftime("%H:%M:%S"),"batch_status":s["status"],"notebook":key,"item_status":x["status"],"progress":count,"planned":planned,"kind":kind,"cell":x.get("cell_index"),"last_message":x.get("last_message","")[-240:],"items":[{"notebook":v["notebook"],"status":v["status"]} for v in s["items"]]},ensure_ascii=False))
