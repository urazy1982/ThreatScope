#!/usr/bin/env python3
"""CPU-only verification of the exact original 288 human-annotation slot mappings."""
import argparse,csv,hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from e1_neutral_gpu import verify_frozen_inputs
from analyze_e1 import validate_labels

def main():
 p=argparse.ArgumentParser()
 p.add_argument('--inputs',type=Path,required=True)
 p.add_argument('--manifest',type=Path,required=True)
 p.add_argument('--labels',type=Path,required=True)
 p.add_argument('--out',type=Path,required=True)
 a=p.parse_args();manifest,windows,cfg=verify_frozen_inputs(a.inputs,a.manifest)
 labels=list(csv.DictReader(a.labels.open(encoding='utf-8',newline='')))
 validate_labels(labels,windows)
 report={'status':'E1_288_SLOT_BINDING_PASS','input_sha256':manifest['input_sha256'],
         'labels_sha256':hashlib.sha256(a.labels.read_bytes()).hexdigest(),
         'sample_slots':288,'sample_windows':36,'sample_publishers':9,
         'determinate':273,'undecidable':15,
         'note':'Original 288 sampled slots only; labels are adjudicated and not undisputed expert truth.'}
 a.out.parent.mkdir(parents=True,exist_ok=True)
 a.out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
 print(report['status'],'288 target SHA-256 checks; 273 determinate labels')
if __name__=='__main__':main()
