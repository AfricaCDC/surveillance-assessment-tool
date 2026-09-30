"""Offline regression checks; optional --live runs the installed local model."""
import argparse
import json
import io
import hashlib
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from recommendation_engine import source_register, theme_batches, checked_actions, draft_report, format_audit, is_recommendation_request


def checks():
    records = source_register('Consolidated findings\n1. No centralised digital back-ups\n2. Poor network coverage\nConsolidated recommendations\n1. Digitalisation\n2. -\n3. No other recommendation since transition is in progress')
    assert [r['id'] for r in records] == ['F1', 'F2', 'R1', 'R2', 'R3']
    assert records[3]['status'] == 'placeholder/title'
    assert records[4]['status'] == 'context only'
    batches, _, _ = theme_batches(records)
    assert any(name == 'Data access, protection and recovery' and any(r['id'] == 'F1' for r in batch) for name, batch in batches)
    for raw in ['{"actions":[{"action":"Test", "source_ids":["F999"]}]}', '{"actions":',
                '{"actions":[{"action":"Create backups", "source_ids":["F2"]}]}',
                '{"actions":[{"action":"Improve network access to DHIS2", "source_ids":["F2"]}]}',
                '{"actions":[{"action":"Train 100 staff", "source_ids":["F1"]}]}']:
        try:
            checked_actions(raw, records)
        except ValueError:
            pass
        else:
            raise AssertionError('Bad model output accepted')
    packets = list(draft_report('Findings\nA concern outside any theme.', '', lambda _: '{"actions":[]}'))
    assert packets[-1]['audit']['unresolved'] == ['F1']
    assert len(packets[-1]['audit']['records']) == 1
    large = source_register('Findings\n' + 'backup ' * 2000)
    _, _, oversized = theme_batches(large)
    assert oversized == ['F1'] and len(large[0]['text']) > 8500
    structured = source_register('', json.dumps([{'comment': '', 'response': 'No', 'question': 'Backup available?'}]))
    assert '"comment": ""' in structured[0]['text']
    assert is_recommendation_request('Consolidate recommendations into themes')
    assert not is_recommendation_request('Professional report with prioritized recommendations')
    noisy = source_register('Findings\nLimited funding\nNo centralised digital back-ups')
    filtered = checked_actions('{"actions":[{"action":"Create backups", "source_ids":["F1","F2"]}]}', noisy)
    assert filtered[0]['source_ids'] == ['F2'] and filtered[0]['discarded_source_ids'] == ['F1']
    print('PASS: stable IDs, placeholders, backups, bad citations, malformed output, unmatched and oversized records, raw evidence')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('source', nargs='?')
    parser.add_argument('--live', action='store_true')
    parser.add_argument('--output', default='outputs/ai-validation-fixed')
    parser.add_argument('--replay', help='Recheck saved actual model responses without another inference run')
    args = parser.parse_args()
    checks()
    if not args.source:
        return
    report = Path(args.source).read_text(encoding='utf-8')
    records = source_register(report)
    batches, unassigned, oversized = theme_batches(records)
    assert len([r for r in records if r['kind'] == 'R']) == 43
    assert 'back-ups' in next(r for r in records if r['id'] == 'F69')['text']
    retained = {r['id'] for r in records if r['status'] == 'retained'}
    sent = {r['id'] for _, batch in batches for r in batch}
    assert retained == sent | set(unassigned) | set(oversized)
    print(f'Source: {len(records)} entries, 43 original recommendations; {len(batches)} packets; {len(unassigned)} unmatched; {len(oversized)} oversized', flush=True)
    if args.replay:
        saved = Path(args.replay)
        responses = {}
        for request_path in saved.glob('request-*.json'):
            request = json.loads(request_path.read_text(encoding='utf-8'))
            response_path = saved / request_path.name.replace('request-', 'response-')
            if response_path.exists():
                responses[json.dumps(request['messages'], sort_keys=True)] = json.loads(response_path.read_text(encoding='utf-8'))
        def replay(messages):
            result = responses.get(json.dumps(messages, sort_keys=True))
            if result is None:
                raise RuntimeError('No saved model response for this exact packet')
            if result.get('done_reason') == 'length':
                raise ValueError('Model reached its output limit')
            return result.get('message', {}).get('content', '')
        packets = list(draft_report(report, '', replay))
        output = Path(args.output); output.mkdir(parents=True, exist_ok=True)
        (output / 'actual-model-report.txt').write_text(''.join(p.get('delta','') for p in packets), encoding='utf-8')
        audit = packets[-1]['audit']
        (output / 'coverage-check.txt').write_text(format_audit(audit), encoding='utf-8')
        (output / 'audit.json').write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding='utf-8')
        assert len(audit['records']) == len(records)
        print('Saved actual model responses rechecked:',len(responses),'Actions:',audit['action_count'],'Unresolved:',len(audit['unresolved']))
        return
    if not args.live:
        return
    import server
    server.ensure_ollama_service()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=True)
    # Keep exact local model requests/responses for reproducible validation.
    real_urlopen = server.urlopen
    def recorded_urlopen(request, *a, **kw):
        if getattr(request, 'full_url', '').endswith('/api/chat'):
            body = request.data
            key = hashlib.sha256(body).hexdigest()[:16]
            (output / f'request-{key}.json').write_bytes(body)
            with real_urlopen(request, *a, **kw) as response:
                data = response.read()
            (output / f'response-{key}.json').write_bytes(data)
            return io.BytesIO(data)
        return real_urlopen(request, *a, **kw)
    server.urlopen = recorded_urlopen
    class Handler:
        def __init__(self):
            self.wfile = (output / 'stream.ndjson').open('wb')
        def send_response(self, code):
            print('HTTP', code, flush=True)
        def send_header(self, *args):
            pass
        def end_headers(self):
            pass
    handler = Handler()
    start = time.monotonic()
    try:
        server.stream_ollama_report_chat(handler, {'report': report, 'question': 'Consolidate recommendations into themes', 'section': 'gap'})
    finally:
        handler.wfile.close()
        packets = [json.loads(line) for line in (output / 'stream.ndjson').read_text(encoding='utf-8').splitlines()]
        answer = ''.join(p.get('delta', '') for p in packets)
        audit = next((p['coverage_check'] for p in packets if 'coverage_check' in p), '')
        (output / 'actual-model-report.txt').write_text(answer, encoding='utf-8')
        (output / 'coverage-check.txt').write_text(audit, encoding='utf-8')
        result = {'model': server.OLLAMA_MODEL, 'seconds': round(time.monotonic()-start, 1),
                  'done': any(p.get('done') for p in packets), 'output_characters': len(answer),
                  'source_entries': len(records), 'original_recommendations': 43, 'packets': len(batches)}
        (output / 'run.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
        print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
