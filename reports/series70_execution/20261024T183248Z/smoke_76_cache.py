import hashlib,json,logging,os,tempfile
from pathlib import Path
os.environ['OMP_NUM_THREADS']='1'
os.environ['MKL_NUM_THREADS']='1'
os.environ['MPLBACKEND']='Agg'
import numpy as np,pandas as pd
b=Path('reports/series70_execution/20261024T183248Z')
p=Path('notebooks/76_tfidf_mpnet_hdbscan.ipynb');n=json.loads(p.read_text(encoding='utf-8'))
ns={};exec(compile(''.join(n['cells'][2]['source']),str(p),'exec'),ns);exec(''.join(n['cells'][4]['source']),ns)
root=Path(tempfile.mkdtemp(prefix='76_smoke_',dir=b)).resolve()
raw=pd.DataFrame({ns['DESCRIPTION_NORMALIZED']:[f'produto categoria{g:02} variante{j}' for g in range(20) for j in range(4)],ns['FREQUENCY']:1})
ns.update(OUTPUT_ROOT=root/'reports',MODEL_ROOT=root/'models',ANALYZER_CONFIGS={'char_wb_2_4':('char_wb',(2,4)),'word_1_3':('word',(1,3))},MIN_DF_VALUES=[1,2],MIN_CLUSTER_FOR_RANKING=2,TSNE_MAX_POINTS=30,TSNE_SVD_COMPONENTS=5,TSNE_MAX_ITER=250,display=lambda *a:None)
reader=pd.read_parquet
pd.read_parquet=lambda *a,**k:raw.copy()
try:exec(''.join(n['cells'][6]['source']),ns)
finally:pd.read_parquet=reader
class SyntheticEncoder:
 def __init__(self,*a):pass
 def encode(self,texts,**kwargs):
  rng=np.random.default_rng(42);x=np.eye(20)[[int(t.split('categoria')[1][:2]) for t in texts]]+rng.normal(0,.002,(len(texts),20));return x/np.linalg.norm(x,axis=1,keepdims=True)
 def save(self,path):Path(path).mkdir();(Path(path)/'SYNTHETIC.txt').write_text('Smoke test encoder only',encoding='utf-8')
ns['SentenceTransformer']=SyntheticEncoder
exec(''.join(n['cells'][8]['source']),ns)
exec(''.join(n['cells'][10]['source']),ns)
checks=0
for record in ns['records']:
 matrix=ns['hybrid_matrices'][record['tfidf_config']]
 labels=ns['HDBSCAN'](min_cluster_size=record['min_cluster_size'],min_samples=record['min_samples'],metric='cosine',algorithm='brute',n_jobs=1,copy=True).fit_predict(matrix)
 assert np.array_equal(labels,ns['labels_by_run'][record['run_id']]),record['run_id']
 original=ns['score_configuration'](matrix,labels,ns['SILHOUETTE_SAMPLE_SIZE'],42)
 assert np.isclose(original['silhouette_cosine_without_noise'],record['silhouette_cosine_without_noise'],equal_nan=True,atol=1e-12)
 checks+=1
assert all(not x.data.flags.writeable for x in ns['hybrid_matrices'].values())
exec(''.join(n['cells'][12]['source']),ns)
# Run reporting with real t-SNE and rendering on this small synthetic dataset.
exec(''.join(n['cells'][14]['source']),ns)
exec(''.join(n['cells'][16]['source']),ns)
saved=pd.read_pickle(ns['model_output_dir']/'hdbscan_model.pkl')
assert saved.metric=='cosine'
assert np.array_equal(saved.labels_,ns['artifact_labels'])
assert not list(ns['distance_cache_dir'].glob('*.npy'))
result={'status':'passed','synthetic_rows':len(raw),'exact_label_checks':checks,'silhouette_equivalence_checks':checks,'model_roundtrip':True,'read_only_features':True,'temporary_distances_removed':True,'output_dir':str(root.relative_to(Path.cwd()))}
(b/'76_cache_smoke.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
plan=json.loads((b/'plan.json').read_text(encoding='utf-8'))
for item in plan['notebooks']:
 if Path(item['notebook']).name==p.name:item['source_sha256']=hashlib.sha256(json.dumps([(c['cell_type'],''.join(c['source'])) for c in n['cells']],ensure_ascii=False).encode()).hexdigest()
(b/'plan.json').write_text(json.dumps(plan,indent=2)+'\n',encoding='utf-8')
logging.info('SMOKE RESULT %s',result)
