"""Validate completed series 70 runs and retain a compact audit artifact."""
import json,logging
from pathlib import Path
import numpy as np
import pandas as pd
BATCH=Path(__file__).resolve().parent
REPO=BATCH.parents[2]
ROOTS={'70':'tfidf_kmeans','71':'mpnet_kmeans','72':'tfidf_dbscan','73':'mpnet_dbscan','74':'tfidf_hdbscan','75':'mpnet_hdbscan','76':'tfidf_mpnet_hdbscan'}
EXPECTED={'70':160,'71':4,'72':3520,'73':88,'74':640,'75':16,'76':640}
HASH='d2bbde012c3e1f6b5d5f51882c85b701a3df931d1a3720e36f32290cf5c1cbf7'
logging.basicConfig(level=logging.INFO,format='%(message)s')
state=json.loads((BATCH/'status.json').read_text(encoding='utf-8'))
audit_path=BATCH/'validated_runs.json'
audit=json.loads(audit_path.read_text(encoding='utf-8')) if audit_path.exists() else {}
for item in state['items']:
 key=Path(item['notebook']).name[:2]
 if item['status']!='completed' or key in audit:continue
 leaf=REPO/item['execution_dir'];n=json.loads((leaf/'executed.ipynb').read_text(encoding='utf-8'))
 assert not any(o.get('output_type')=='error' for c in n['cells'] for o in c.get('outputs',[])),key
 assert all(c.get('execution_count') is not None for c in n['cells'] if c['cell_type']=='code' and ''.join(c['source']).strip()),key
 candidates=[]
 for p in (REPO/'reports'/ROOTS[key]).glob('202501*/run.json'):
  meta=json.loads(p.read_text(encoding='utf-8'))
  if meta.get('comparison',{}).get('training_sample_sha256')==HASH:candidates.append((p,meta))
 assert len(candidates)==1,(key,[str(p) for p,_ in candidates])
 metadata_path,meta=candidates[0];folder=metadata_path.parent
 comparison=meta['comparison']
 assert comparison==audit['70']['comparison'],key
 metrics=pd.read_csv(folder/'metrics.csv');ranking=pd.read_csv(folder/'ranking.csv')
 assert len(metrics)==EXPECTED[key],(key,len(metrics))
 assert not ranking.empty,key
 assert ranking['cluster_count_excluding_noise'].between(10,1000).all(),key
 assert np.isfinite(ranking['silhouette_cosine_without_noise']).all(),key
 assert metrics['silhouette_base_sample_size'].eq(20000).all(),key
 png_count=len(list((folder/'tsne_plots').glob('*.png')))
 html_count=len(list((folder/'tsne_3d_html').glob('*.html')))
 assert png_count==html_count==EXPECTED[key],(key,png_count,html_count)
 assignment_candidates=list(folder.glob('*assignments*.csv'))
 if assignment_candidates:
  assignments=pd.read_csv(assignment_candidates[0]);assert len(assignments)==20000,key
 audit[key]={'status':'validated','metrics_rows':len(metrics),'ranking_rows':len(ranking),'report_dir':str(folder.relative_to(REPO)),'executed_notebook':str((leaf/'executed.ipynb').relative_to(REPO)),'comparison':comparison,'manual_labeling_pending':False,'best_rank':json.loads(ranking.head(1).to_json(orient='records'))[0],'tsne_png_count':png_count,'tsne_html_count':html_count}
 logging.info('Notebook %s validated: %s fits, %s ranked, %s PNG/HTML pairs',key,len(metrics),len(ranking),png_count)
audit_path.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
logging.info('Validated notebooks: %s',', '.join(audit))
