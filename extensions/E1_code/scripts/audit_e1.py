#!/usr/bin/env python3
"""Independent CPU checkpoint replay and validity audit for ThreatScope E1 v1.1.2.

Invalid JSON is NOT the same outcome as a valid empty selection. Does not
measure new inference. Source text is read only for prompt hash re-creation.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from e1_neutral_gpu import (canonical, sha, SYS, build_messages, parse_output,
                            verify_frozen_inputs, PROTOCOL_ID)
from orchestrate_e1 import MODELS, cells
ROOT = Path(__file__).resolve().parents[1]


def verify_cell(out, model, precision, condition, windows, manifest, config, expected_count,
                manifest_sha256=None, subset_ok=False):
    out = Path(out)
    if not out.is_dir():
        raise RuntimeError('MISSING_CELL ' + str(out))
    identity = json.loads((out / 'identity.json').read_text(encoding='utf-8'))
    if identity.get('protocol') != PROTOCOL_ID:
        raise RuntimeError('WRONG_PROTOCOL_VERSION')
    if any(identity.get(k) != v for k, v in [('model', model), ('precision', precision),
                                             ('condition', condition),
                                             ('revision', config['models'][model]),
                                             ('inputs_sha256', manifest['input_sha256']),
                                             ('sys_sha256', sha(SYS)),
                                             ('code_sha256', hashlib.sha256((ROOT / 'scripts/e1_neutral_gpu.py').read_bytes()).hexdigest())]):
        raise RuntimeError('WRONG_CELL_IDENTITY_OR_CODE')
    if manifest_sha256 is not None and identity.get('manifest_sha256') != manifest_sha256:
        raise RuntimeError('MANIFEST_IDENTITY_MISMATCH')
    if identity.get('generation') != {'do_sample': False, 'num_beams': 1,
                                      'max_new_tokens': config['max_new_tokens'],
                                      'pad_token_id': 'eos'}:
        raise RuntimeError('GENERATION_IDENTITY_MISMATCH')
    expected = {w['window_id'] for w in windows[:expected_count]}
    actual = {p.stem for p in out.glob('*.json')} - {'identity', 'cell_status', 'load_provenance'}
    if not (expected.issubset(actual) if subset_ok else expected == actual):
        raise RuntimeError('INCOMPLETE_OR_EXTRA_CHECKPOINTS expected=' + str(len(expected)) +
                           ' actual=' + str(len(actual)) + ' missing=' + str(len(expected - actual)) +
                           ' extra=' + str(len(actual - expected)))
    provenance = json.loads((out / 'load_provenance.json').read_text(encoding='utf-8'))
    if any(provenance.get(k) != v for k, v in [('model', model),
                                                 ('revision', config['models'][model]),
                                                 ('precision', precision)]):
        raise RuntimeError('LOAD_PROVENANCE_DRIFT')
    if not isinstance(provenance.get('verified_4bit_linear_modules'), int):
        raise RuntimeError('MISSING_PRECISION_VERIFICATION')
    if precision == 'nf4' and provenance['verified_4bit_linear_modules'] <= 0:
        raise RuntimeError('NF4_NOT_VERIFIED')
    if precision == 'bf16' and provenance['verified_4bit_linear_modules'] != 0:
        raise RuntimeError('BF16_UNEXPECTED_4BIT_MODULE')
    for key in ('tokenizer_chat_template_sha256', 'cuda_device', 'pytorch', 'transformers', 'bitsandbytes'):
        if not provenance.get(key):
            raise RuntimeError('INCOMPLETE_LOAD_PROVENANCE ' + key)
    if 'additional_dependencies' not in provenance or 'additional_dependencies' not in identity:
        raise RuntimeError('MISSING_SUPPLEMENTARY_DEPENDENCY_VERSIONS')
    if provenance['additional_dependencies'] != identity['additional_dependencies']:
        raise RuntimeError('RUNTIME_DEPENDENCY_DRIFT')
    for key,source in [('pytorch','torch'),('transformers','transformers'),('bitsandbytes','bitsandbytes')]:
        if provenance[key] != identity[source]:
            raise RuntimeError('GPU_RUNTIME_PROVENANCE_DRIFT '+key)
    if provenance.get('model_config_commit') not in (None,identity['revision']):
        raise RuntimeError('MODEL_COMMIT_DRIFT')
    if provenance.get('tokenizer_init_commit') not in (None,identity['revision']):
        raise RuntimeError('TOKENIZER_COMMIT_DRIFT')
    ident_sha = sha(canonical(identity))
    invalid, cardinalities, valid_empty, cap_reached = [], [], 0, 0
    for w in windows[:expected_count]:
        item = json.loads((out / (w['window_id'] + '.json')).read_text(encoding='utf-8'))
        content = {k: v for k, v in item.items() if k != 'record_sha256'}
        if (item.get('window_id') != w['window_id'] or
            item.get('input_sha256') != w['input_sha256'] or
            item.get('identity') != ident_sha or
            item.get('prompt_sha256') != sha(canonical(build_messages(model, w, condition))) or
            item.get('raw_sha256') != sha(item.get('raw', '')) or
            item.get('record_sha256') != sha(canonical(content))):
            raise RuntimeError('CHECKPOINT_CONTENT_DRIFT ' + w['window_id'])
        good, selected, error = parse_output(item.get('raw', ''))
        if (item.get('valid'), item.get('indices'), item.get('error')) != (good, selected, error):
            raise RuntimeError('PARSER_REPLAY_MISMATCH ' + w['window_id'])
        if not isinstance(item.get('prompt_tokens'), int) or item['prompt_tokens'] < 64:
            raise RuntimeError('PROMPT_TOKEN_COUNT_INVALID ' + w['window_id'])
        if not isinstance(item.get('generated_tokens'), int) or item['generated_tokens'] < 0:
            raise RuntimeError('GENERATION_TOKEN_COUNT_INVALID ' + w['window_id'])
        cap = item['generated_tokens'] >= config['max_new_tokens']
        if item.get('generation_cap_reached') != cap:
            raise RuntimeError('GENERATION_CAP_FLAG_DRIFT ' + w['window_id'])
        cap_reached += int(cap)
        if good:
            cardinalities.append(len(selected))
            valid_empty += int(not selected)
        else:
            invalid.append(w['window_id'])
    status = json.loads((out / 'cell_status.json').read_text(encoding='utf-8'))
    if subset_ok:
        if status.get('completed_windows',0) < expected_count or status.get('identity') != ident_sha:
            raise RuntimeError('PARTIAL_SMOKE_STATUS_INCONSISTENT')
    else:
     for key, value in [('model', model), ('precision', precision), ('condition', condition),
                       ('requested_windows', expected_count), ('completed_windows', expected_count),
                       ('valid_windows', len(cardinalities)), ('invalid_windows', len(invalid)),
                       ('complete_full_cell', expected_count == 144), ('identity', ident_sha)]:
        if status.get(key) != value:
            raise RuntimeError('CELL_STATUS_INCONSISTENT ' + key)
    return dict(model=model, precision=precision, condition=condition,
                total=expected_count, valid=len(cardinalities), invalid=len(invalid),
                invalid_ids=invalid, valid_empty_windows=valid_empty,
                valid_empty_fraction=valid_empty / len(cardinalities) if cardinalities else None,
                all_window_valid_empty_fraction=valid_empty / expected_count,
                mean_selected_given_valid=sum(cardinalities) / len(cardinalities) if cardinalities else None,
                mean_usable_selected_per_window=sum(cardinalities) / expected_count,
                generation_cap_reached=cap_reached, output=str(out))


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--inputs',type=Path,required=True);p.add_argument('--manifest',type=Path,required=True)
    p.add_argument('--results',type=Path,required=True);p.add_argument('--mode',choices=['smoke','full'],required=True)
    p.add_argument('--out',type=Path,required=True);p.add_argument('--require-valid',action='store_true')
    a=p.parse_args()
    manifest,windows,cfg=verify_frozen_inputs(a.inputs,a.manifest)
    mdig=hashlib.sha256(a.manifest.read_bytes()).hexdigest()
    items=[]
    for model,prec,cond in cells(a.mode):
        folder=a.results/'E1'/MODELS[model]/prec/cond
        items.append(verify_cell(folder,model,prec,cond,windows,manifest,cfg,
                                 2 if a.mode=='smoke' else 144,manifest_sha256=mdig))
    report={'status':'AUDIT_PASS' if all(x['invalid']==0 for x in items) else 'AUDIT_COMPLETED_WITH_INVALID_OUTPUTS',
            'protocol':PROTOCOL_ID,'input_sha256':manifest['input_sha256'],
            'manifest_sha256':mdig,'mode':a.mode,'cells':items,
            'total':sum(x['total'] for x in items),
            'valid':sum(x['valid'] for x in items),
            'invalid':sum(x['invalid'] for x in items),
            'note':'Valid empty outputs and malformed outputs are separate categories.'}
    a.out.parent.mkdir(parents=True,exist_ok=True)
    a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print('E1_CHECKPOINT_AUDIT',report['status'],'total=',report['total'],'valid=',report['valid'])
    if a.require_valid and report['invalid']:raise SystemExit(3)
if __name__=='__main__':main()
