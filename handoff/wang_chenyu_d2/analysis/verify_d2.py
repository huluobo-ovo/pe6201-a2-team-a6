"""Offline verification and paired metrics regeneration. No API calls."""
from pathlib import Path
import json,csv,hashlib
R=Path(__file__).resolve().parents[1]; E=R/'artifacts'; rows=[]; loaded=[]
for name in ['fan_yupei_openai_gpt-5.4_v1.json','fan_yupei_openai_gpt-5.4_v2.json','wang_chenyu_google_gemini-3.7-flash_v2.json']:
 d=json.loads((E/name).read_text(encoding='utf-8'));loaded.append(d)
 s=d['summary'];ts=d['trial_results'];r=d['run']
 assert len(ts)==s['trials']==58
 assert sum(t['passed'] for t in ts)==s['passed']
 for k in ('tokens_in','tokens_out'):assert sum(t['record'][k] for t in ts)==s[k]
 assert r['freeze_commit_sha']==r['source_commit_sha']=='e36bb1b2fcad625ed944e7df863165d95c0ef53f'
 if 'gpt-5.4' in name:
  p=r['pricing'];cost=s['tokens_in']*p['input_usd_per_million']/1e6+s['tokens_out']*p['output_usd_per_million']/1e6
  rows.append({'model':r['model_id'],'descriptor':r['descriptor_version'],'trials':58,'passed':s['passed'],'pass_rate':s['passed']/58,'negative_passed':s['negative_passed'],'negative_trials':42,'input_tokens':s['tokens_in'],'output_tokens':s['tokens_out'],'total_tokens':s['tokens_in']+s['tokens_out'],'median_turns':s['median_turns'],'worst_turns':s['worst_case_turns'],'error_trials':s['error_trials'],'harness_rounded_cost_usd':s['cost_usd'],'exact_price_book_cost_usd':cost,'provider_reported_cost_usd':s['provider_reported_cost_usd']})
for d in loaded[1:]:assert d['evaluation_set']==loaded[0]['evaluation_set']
for k in ['prompt_sha256','descriptor_bundle_sha256','tool_version','max_output_tokens_per_response','trial_policy','fixture_booking_approval','token_measurement']:
 assert loaded[1]['run'][k]==loaded[2]['run'][k],k
with (R/'analysis/d2_paired_metrics.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
g=loaded[2]; rs=[json.loads(x)['payload'] for x in (E/'api_responses.jsonl').read_text(encoding='utf-8').splitlines()]
assert all(x['model']=='google/gemini-3.7-flash' for x in rs)
assert sum(x['usage']['prompt_tokens'] for x in rs)==g['summary']['tokens_in']
assert sum(x['usage']['completion_tokens'] for x in rs)==g['summary']['tokens_out']
assert abs(sum(x['usage'].get('cost',0) for x in rs)-g['summary']['provider_reported_cost_usd'])<1e-8
manifest=R/'SHA256SUMS.json'
if manifest.exists():
 for name,digest in json.loads(manifest.read_text(encoding='utf-8')).items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
print('PASS: 3 x 58-trial records reconciled; Gemini API tokens/cost and v2 compatibility checked; paired CSV regenerated.')
