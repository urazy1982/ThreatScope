"""Offline publisher-metadata / archive integration tests. No real report inference."""
import json, hashlib, shutil, tempfile, unittest, zipfile
from pathlib import Path
from corpusapt.acquire import (ARCHIVE,CANDIDATES,HOSTS,INDEX_FILES,archive_path_parts,
    checked_index,html_text,high_overlap,index_records,number_from,save,sha,
    stage_archive,summarize_index,download_archive)

BASE=Path(__file__).resolve().parent.parent


def fixture(root, count=10, sources=CANDIDATES, bad=None):
    root=Path(root);meta=root/'meta';meta.mkdir()
    index=[];entries=[]
    for si,s in enumerate(sources):
        host=HOSTS[s][0]
        for j in range(count):
            number=f'{si*1000+j+1:06d}'
            url=f'https://research.{host}/research/{s}-{j}-{number}'
            index.append({'number':number,'source':s,'url':url,'html_path':f'02_APT_publishers/{s}/html/{number}.html'})
            paras=[]
            for k in range(23):
                paras.append(f'The investigators discovered a fictional command server marked {s}_{j}_{k}_alpha deployed in the incident workspace during case {s}_{j}_{k}_beta. The research team documented infection routes, collected {s}_{j}_{k}_gamma artifacts, and validated simulated evidence from remote hosts near {s}_{j}_{k}_delta networks.')
            html='<html><head><script>bad</script></head><body><main>' + ''.join('<p>'+p+'</p>' for p in paras) + '</main></body></html>'
            entries.append((f'02_APT_publishers/{s}/html/{number}.html',html))
    if bad=='duplicate':
        entries[8*count-1]=(entries[8*count-1][0],entries[0][1])
    with zipfile.ZipFile(root/'archive.zip','w',zipfile.ZIP_DEFLATED) as z:
        for path,body in entries:z.writestr('release/'+path,body)
    contents={
      'filename_map.json':json.dumps({'records':index}),
      'classifications.json':'{}',
      'source_risks.json':'{}',
      'README.md':'fixture',
      'LICENSE':'fixture'
    }
    manifest={'repo_id':'CZLi/apt-reports','revision':'a'*40,'archive':ARCHIVE,'files':{}}
    for name,txt in contents.items():
        b=txt.encode();(meta/name).write_bytes(b)
        manifest['files'][name]={'sha256':sha(b),'bytes':len(b)}
    save(meta/'provenance.json',manifest)
    return meta,root/'archive.zip'

class ManifestCorpus(unittest.TestCase):
    def test_article_identifiers(self):
        self.assertEqual(number_from({'article_number':25}),'000025')
        self.assertEqual(number_from({'path':'02_APT_publishers/talos_apt/html/000098.html'}),'000098')
        self.assertIsNone(number_from({'number': 'not-number'}))
    def test_hard_refuse_url_domain_spoof(self):
        x=[{'number':1,'source':'talos_apt','url':'https://talosintelligence.com.evil.invalid/foo'},
           {'number':2,'source':'talos_apt','url':'https://blog.talosintelligence.com/foo'}]
        self.assertEqual(len(index_records(x)),1)
    def test_archive_path_traversal_rejected(self):
        self.assertIsNone(archive_path_parts('../02_APT_publishers/talos_apt/html/000001.html'))
        self.assertEqual(archive_path_parts('release/02_APT_publishers/talos_apt/html/000001.html'),('talos_apt','000001'))
    def test_parser_nested_and_number_key(self):
        x={'records':{'000001':{'source':'talos_apt','url':'https://blog.talosintelligence.com/x'}}}
        self.assertEqual(index_records(x)[0]['number'],'000001')
    def test_parser_skip_missing_source(self):
        self.assertEqual(index_records([{'number':1,'url':'https://blog.talosintelligence.com/x'}]),[])
    def test_html_sanitization(self):
        s=html_text(b'<html><body><nav>Noise</nav><article><p>Long and real report evidence appeared in several investigations and in additional threat reports to researchers.</p><script>secret</script></article></body></html>')
        self.assertNotIn('Noise',s);self.assertNotIn('secret',s);self.assertIn('report evidence',s)
    def test_high_overlap(self):
        x='The investigation observed a persistent malicious command server with an exploit trace and an implanted backdoor in the network'
        self.assertEqual(high_overlap(x,x),1)
        self.assertLess(high_overlap(x,'Completely unrelated paragraphs about data processing and languages are shown here'),0.2)
    def test_index_hash_tamper(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,_=fixture(tmp)
            (meta/'filename_map.json').write_text('[]')
            with self.assertRaisesRegex(RuntimeError,'INDEX_SHA_MISMATCH'):checked_index(meta)
    def test_index_inventory_12_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,_=fixture(tmp)
            o=summarize_index(meta)
            self.assertEqual(o['record_count_verified'],120)
            self.assertTrue(o['gate_pass'])
            self.assertEqual(o['eligible_sources_with_8_indexed'],12)
    def test_index_inventory_insufficient_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta,_=fixture(tmp,sources=CANDIDATES[:9])
            self.assertFalse(summarize_index(meta)['gate_pass'])
    def test_download_requires_large_explicit_consent(self):
        with self.assertRaisesRegex(RuntimeError,'confirm-large'):download_archive('a','b')
    def test_full_zip_corpus_72_reports_144_windows(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root)
            out=stage_archive(meta,archive,root/'workspace',BASE)
            self.assertEqual(out['selected_reports'],72)
            self.assertEqual(out['input_windows'],144)
            self.assertEqual(out['planned_gpu_calls'],6912)
            self.assertEqual(out['gpu_gate'],'CLOSED')
            from crosscti.analyze import verify_prepared
            _,m,windows=verify_prepared(root/'workspace')
            self.assertEqual(len(windows),144)
            self.assertEqual(len({w['report_id'] for w in windows}),72)
            self.assertEqual(len({w['source'] for w in windows}),9)
    def test_realistic_metadata_12_archive_only_9_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root)
            nine_sources=set(CANDIDATES[:9])
            partial=root/'partial.zip'
            with zipfile.ZipFile(archive) as src, zipfile.ZipFile(partial,'w',zipfile.ZIP_DEFLATED) as target:
                for item in src.infolist():
                    from corpusapt.acquire import archive_path_parts
                    pair=archive_path_parts(item.filename)
                    if pair and pair[0] in nine_sources:
                        target.writestr(item,src.read(item.filename))
            out=stage_archive(meta,partial,root/'work',BASE)
            self.assertEqual(len(out['selected_sources']),9)
            self.assertEqual(out['planned_gpu_calls'],6912)
            self.assertEqual(out['selected_reports'],72)
            self.assertEqual(out['input_windows'],144)
            from scripts.cpu_replay import fill_fake
            from crosscti.analyze import analyze
            self.assertEqual(fill_fake(root/'work'),6912)
            result=analyze(root/'work')
            self.assertTrue(result)

    def test_realistic_archive_only_8_sources_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root)
            eight_sources=set(CANDIDATES[:8])
            partial=root/'partial.zip'
            with zipfile.ZipFile(archive) as src, zipfile.ZipFile(partial,'w',zipfile.ZIP_DEFLATED) as target:
                for item in src.infolist():
                    pair=archive_path_parts(item.filename)
                    if pair and pair[0] in eight_sources:
                        target.writestr(item,src.read(item.filename))
            with self.assertRaisesRegex(RuntimeError,'REAL_CONTENT_SOURCE_COVERAGE_FAIL'):
                stage_archive(meta,partial,root/'work',BASE)

    def test_archive_without_manifest_match_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root)
            j=__import__('json').loads((meta/'filename_map.json').read_text());j['records'][0]['url']='https://attacker.invalid/x'
            (meta/'filename_map.json').write_text(json.dumps(j))
            p=__import__('json').loads((meta/'provenance.json').read_text())
            p['files']['filename_map.json']['sha256']=sha((meta/'filename_map.json').read_bytes())
            save(meta/'provenance.json',p)
            # There should be enough other entries; one unmatched record is skipped, not invented
            o=stage_archive(meta,archive,root/'work',BASE)
            prov=json.loads((root/'work/dataset/corpus_provenance.json').read_text())
            self.assertEqual(prov['discard_counts']['missing_or_ambiguous_index_link'],1)
    def test_stage_existing_workspace_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root)
            stage_archive(meta,archive,root/'work',BASE)
            with self.assertRaisesRegex(RuntimeError,'WORKSPACE_ALREADY_EXISTS'):stage_archive(meta,archive,root/'work',BASE)
    def test_missing_index_records_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root)
            (meta/'filename_map.json').write_text('{}')
            p=json.loads((meta/'provenance.json').read_text())
            p['files']['filename_map.json']['sha256']=sha((meta/'filename_map.json').read_bytes())
            save(meta/'provenance.json',p)
            self.assertFalse(summarize_index(meta)['gate_pass'])
            with self.assertRaisesRegex(RuntimeError,'INDEX_SOURCE_COVERAGE_GATE_FAIL'):
                stage_archive(meta,archive,root/'work',BASE)
    def test_selected_cross_publisher_duplicate_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root,count=8,sources=CANDIDATES[:10],bad='duplicate')
            with self.assertRaisesRegex(RuntimeError,'DUPLICATE_SELECTED_TEXT'):
                stage_archive(meta,archive,root/'work',BASE)
    def test_download_archive_pinned_cache(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root)
            with patch('huggingface_hub.hf_hub_download',return_value=str(archive)) as dl:
                dest=root/'copy.zip'
                a=download_archive(meta,dest,confirm_large=True)
                self.assertTrue(a['zip_ok'])
                self.assertTrue(dest.exists())
                self.assertEqual(dl.call_args.kwargs['revision'],'a'*40)
    def test_metadata_fetch_pins_revision(self):
        from unittest.mock import patch
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);sample=root/'original';sample.mkdir()
            for name in INDEX_FILES:(sample/name).write_text('[]' if name.endswith('.json') else 'test')
            def fake_dl(repo,filename,repo_type,revision):
                self.assertEqual(revision,'b'*40)
                return str(sample/filename)
            from corpusapt.acquire import fetch_indexes
            with patch('huggingface_hub.HfApi') as api, patch('huggingface_hub.hf_hub_download',side_effect=fake_dl):
                api.return_value.dataset_info.return_value=SimpleNamespace(sha='b'*40)
                prov=fetch_indexes(root/'meta')
            self.assertEqual(prov['revision'],'b'*40)
            self.assertEqual(len(prov['files']),len(INDEX_FILES))
            checked_index(root/'meta')

    def test_zero_gpu_models_on_cpu(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);meta,archive=fixture(root)
            stage_archive(meta,archive,root/'work',BASE)
            from crosscti.runner import run_cell
            with self.assertRaisesRegex(RuntimeError,'GPU_AUTHORIZATION_MISSING'):
                run_cell(root/'work','Qwen/Qwen2.5-3B-Instruct','bf16')

if __name__=='__main__': unittest.main()
