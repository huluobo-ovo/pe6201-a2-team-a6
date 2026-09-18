"""External transport configuration and evidence capture; frozen source stays unchanged."""
import os, sys, json, hashlib, runpy
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(__file__).resolve().parents[1]
REPO=ROOT/'work/jason_gemini_run'
OUT=ROOT/'outputs/Jason_Gemini_OpenRouter_Live'
OUT.mkdir(exist_ok=True)
MARKER=OUT/'started.json'
if MARKER.exists(): raise SystemExit('Existing run marker: refusing duplicate run')
runpy.run_path(str(ROOT/'outputs/Jason_Gemini_Launcher.py'))['verify_checkout']()
key=os.environ.get('OPENROUTER_API_KEY')
if not key: raise SystemExit('OPENROUTER_API_KEY is required')
os.environ['OPENROUTER_API_KEY']=key
os.environ['PATH']='C:/Users/admin/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/git/cmd'+os.pathsep+os.environ.get('PATH','')
os.chdir(REPO)
sys.path.insert(0,str(REPO/'A2_scaffold'))
import config, backends, harness, run_eval
config.BASE_URL='https://openrouter.ai/api/v1'
config.API_KEY=key
meta={'started_at':datetime.now(timezone.utc).isoformat(),'provider':'OpenRouter','model':'google/gemini-3.7-flash','documented_version':'Gemini 3.7 Flash','base_url':config.BASE_URL,'freeze_sha':'e36bb1b2fcad625ed944e7df863165d95c0ef53f','adapter_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'changes':'External BASE_URL/API_KEY override and append-only response/trial logging. Frozen source, prompt, cases, caps and parsing unchanged. Provider default thinking mode; no thinking override.','baseline_pricing':'USD per million baseline input 0.75, output 3.75. Provider cost retained separately.','pricing_source':'https://openrouter.ai/google/gemini-3.7-flash','retry_policy':'No retries or selective reruns'}
MARKER.write_text(json.dumps(meta,indent=2),encoding='utf-8')
original_call=backends._live_call
def captured_call(messages):
    start=datetime.now(timezone.utc).isoformat()
    payload=original_call(messages)
    with (OUT/'api_responses.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'request_started_at':start,'response_received_at':datetime.now(timezone.utc).isoformat(),'payload':payload},ensure_ascii=False)+'\n')
    return payload
backends._live_call=captured_call
original_run=harness.run_case
completed=0
def captured_run(*args,**kwargs):
    global completed
    record=original_run(*args,**kwargs)
    completed+=1
    with (OUT/'trial_checkpoints.jsonl').open('a',encoding='utf-8') as f:
        f.write(json.dumps({'sequence':completed,'case_id':args[0],'record':record},ensure_ascii=False,default=str)+'\n')
    (OUT/'progress.json').write_text(json.dumps({'completed_trials':completed,'total_trials':58,'last_case':args[0],'updated_at':datetime.now(timezone.utc).isoformat()}),encoding='utf-8')
    print('PROGRESS %d/58 %s'%(completed,args[0]),flush=True)
    return record
harness.run_case=captured_run
args=['--backend','live','--model','google/gemini-3.7-flash','--descriptor-version','v2','--approve-fixture-bookings','--price-input-per-million','0.75','--price-output-per-million','3.75','--price-source',meta['pricing_source'],'--price-date','2026-09-17','--freeze-sha',meta['freeze_sha'],'--output',str(OUT/'wang_chenyu_google_gemini-3.7-flash_v2.json')]
code=run_eval.main(args)
(OUT/'finished.json').write_text(json.dumps({'finished_at':datetime.now(timezone.utc).isoformat(),'harness_exit_code':code,'completed_trials':completed}),encoding='utf-8')
print('FINISHED; harness exit code',code,flush=True)
