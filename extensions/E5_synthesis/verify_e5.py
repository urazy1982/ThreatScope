import csv, json, hashlib, collections
from pathlib import Path
p=Path(__file__).resolve().parent
def csvrows(name):
 with (p/'evidence'/name).open(newline='',encoding='utf8') as f:return list(csv.DictReader(f))
a=csvrows('E1_window_decisions_1728.csv');b=csvrows('E2_per_prompt_decisions_2304.csv');c=csvrows('E3_decisions_textfree.csv');d=csvrows('E4_decisions_textfree.csv')
assert (len(a),len(b),len(c),len(d))==(1728,2304,3456,1152)
assert sum(x['valid']=='1' for x in a)==1675
assert sum(x['valid'].lower()=='true' for x in d)==1105
assert len({x['window_id'] for x in c})==72
assert {x['window_id'] for x in d}=={x['window_id'] for x in c}
e2=json.loads((p/'evidence/E2_summary.json').read_text()); e3=json.loads((p/'evidence/E3_summary.json').read_text()); e4=json.loads((p/'evidence/E4_summary.json').read_text())
for precision,expected in [('bf16',e2['greedy_vs_scoring_agreement_bf16']),('nf4',e2['greedy_vs_scoring_agreement_nf4'])]:
 s=[x for x in b if x['precision']==precision];assert len(s)==1152;assert abs(sum(x['greedy_choice']==x['scoring_choice'] for x in s)/len(s)-expected)<1e-12
assert abs(e2['greedy_precision_delta_pp_publisher_equal']-e2['scoring_precision_delta_pp_publisher_equal']-e2['difference_of_precision_deltas_pp'])<1e-9
for model in {x['model'] for x in e4['effects']}:
 contrasts={x['contrast']:x['effect_pp'] for x in e4['effects'] if x['model']==model}
 assert abs(contrasts['FP4_minus_BF16']-contrasts['NF4_minus_BF16']-contrasts['FP4_minus_NF4'])<1e-6
 matching=[x for x in e3['rows'] if x['model']==model];assert len(matching)==1;assert abs(matching[0]['nf4_minus_bf16_pp']-contrasts['NF4_minus_BF16'])<1e-5
print('THREATSCOPE_E5_CROSS_STUDY_REPLAY_PASS E1=1728 E2=2304 E3=3456 E4=1152')
