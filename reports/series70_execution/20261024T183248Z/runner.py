"""Execute the seven research notebooks sequentially with durable checkpoints."""
import ast
import hashlib
import json
import logging
import os
from pathlib import Path
import sys
import time
import traceback
from datetime import datetime, timezone

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

REPO = Path(sys.argv[1]).resolve()
BATCH = Path(sys.argv[2]).resolve()
os.chdir(REPO)
os.environ['MPLBACKEND'] = 'Agg'
os.environ['PYTHONUTF8'] = '1'
os.environ['OMP_NUM_THREADS'] = '8'
os.environ['MKL_NUM_THREADS'] = '8'
os.environ['OPENBLAS_NUM_THREADS'] = '8'
os.environ['NUMEXPR_NUM_THREADS'] = '8'
os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s', handlers=[logging.FileHandler(BATCH/'runner.log',encoding='utf-8'),logging.StreamHandler(sys.stdout)])
logger = logging.getLogger('series70')
STATE = {'started_utc': datetime.now(timezone.utc).isoformat(), 'status': 'running', 'python': sys.executable, 'threads': 8, 'items': []}

def atomic_json(path, value):
    """Persist a complete status document without truncating the previous one."""
    temp = path.with_suffix(path.suffix+'.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(path)

def sources(notebook):
    """Return a notebook's source cells independently from execution outputs."""
    return [(cell.cell_type,cell.source) for cell in notebook.cells]

class LoggedClient(NotebookClient):
    """Stream kernel messages and checkpoint every completed cell."""
    def process_message(self, msg, cell, cell_index):
        """Preserve normal notebook outputs and expose incremental run progress."""
        result = super().process_message(msg,cell,cell_index)
        kind = msg.get('msg_type',msg.get('header',{}).get('msg_type'))
        if kind == 'stream':
            value = msg.get('content',{}).get('text','')
            with (self.run_dir/'kernel.log').open('a',encoding='utf-8') as stream:
                stream.write(value)
            self.item['last_message'] = value[-600:].strip()
            self.item['last_update_utc'] = datetime.now(timezone.utc).isoformat()
            if time.monotonic()-getattr(self,'_last_status_write',0)>3:
                atomic_json(BATCH/'status.json',STATE)
                self._last_status_write=time.monotonic()
        return result

    async def async_execute_cell(self, cell, cell_index, execution_count=None, store_history=True):
        """Checkpoint both normal execution and a cell that raises an error."""
        self.item['cell_index'] = cell_index
        self.item['cell_started_utc'] = datetime.now(timezone.utc).isoformat()
        atomic_json(BATCH/'status.json',STATE)
        try:
            return await super().async_execute_cell(cell,cell_index,execution_count,store_history)
        finally:
            nbformat.write(self.nb,self.run_dir/'executed.ipynb')
            self.item['last_update_utc'] = datetime.now(timezone.utc).isoformat()
            atomic_json(BATCH/'status.json',STATE)

for path in sorted((REPO/'notebooks').glob('7*.ipynb')):
    nb=nbformat.read(path,as_version=4)
    original_sources=sources(nb)
    run_dir=BATCH/path.stem
    run_dir.mkdir()
    nbformat.write(nb,run_dir/'input.ipynb')
    for cell in nb.cells:
        if cell.cell_type=='code':
            cell.outputs=[]
            cell.execution_count=None
    item={'notebook':str(path.relative_to(REPO)),'status':'running','started_utc':datetime.now(timezone.utc).isoformat(),'source_sha256':hashlib.sha256(json.dumps(original_sources,ensure_ascii=False).encode()).hexdigest(),'execution_dir':str(run_dir.relative_to(REPO))}
    STATE['items'].append(item)
    atomic_json(BATCH/'status.json',STATE)
    logger.info('START %s',path.name)
    km=KernelManager(kernel_name='python3')
    km.kernel_spec.argv=[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}']
    client=LoggedClient(nb,km=km,resources={'metadata':{'path':str(REPO)}},timeout=None,startup_timeout=120,iopub_timeout=120,raise_on_iopub_timeout=True,allow_errors=False)
    client.run_dir=run_dir
    client.item=item
    started=time.monotonic()
    try:
        client.execute()
        item['status']='completed'
        logger.info('DONE %s (%.1f seconds)',path.name,time.monotonic()-started)
    except BaseException as exc:
        item['status']='failed'
        item['error']=f'{type(exc).__name__}: {exc}'
        (run_dir/'error.txt').write_text(traceback.format_exc(),encoding='utf-8')
        logger.exception('FAILED %s',path.name)
    finally:
        nbformat.write(nb,run_dir/'executed.ipynb')
        item['elapsed_seconds']=round(time.monotonic()-started,2)
        item['finished_utc']=datetime.now(timezone.utc).isoformat()
        # Preserve any source edits made in the editor while the kernel was running.
        current=nbformat.read(path,as_version=4)
        if sources(current)==original_sources:
            nbformat.write(nb,path)
            item['outputs_saved_in_original']=True
        else:
            item['outputs_saved_in_original']=False
            logger.warning('Source changed during execution; kept outputs only in %s',run_dir)
        atomic_json(BATCH/'status.json',STATE)
        try:
            if km.has_kernel:
                km.shutdown_kernel(now=True)
        except Exception:
            logger.exception('Kernel cleanup failed for %s',path.name)

STATE['status']='completed' if all(x['status']=='completed' for x in STATE['items']) else 'completed_with_errors'
STATE['finished_utc']=datetime.now(timezone.utc).isoformat()
atomic_json(BATCH/'status.json',STATE)
logger.info('BATCH %s',STATE['status'])
