"""Loopback-only integration harness. Real app/engines, synthetic transport, no LLM.

Run only as an explicit test factory; app.main never imports this module. Test
control endpoints and data are transient and contain synthetic specimens only.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit

from fastapi import Body

from app.api.application import create_app
from app.services.llm import qwen3coder_prototype as profile
from app.services.llm.qwen3coder import DIGEST, MODEL
from app.services.pipelines.resources import InferenceGate, OperationalFailure
from app.services.pipelines.service import AnalysisService
from app.services.pipelines.strategy import DeterministicLayersStrategy


def finding(bid, snippet, source='original'):
    return {'behavior_id': bid, 'confidence': 'medium', 'explanation': 'SIMULATED local integration response.',
            'evidence': [{'source_id': source, 'snippet': snippet}]}


def report(behaviors, risk='unknown'):
    return {'behaviors': behaviors, 'obfuscation_techniques': [], 'recovered_content': [],
        'risk_label': risk, 'risk_rationale': 'SIMULATED model attribution; no empirical inference.',
        'uncertainty': {'level': 'high', 'notes': 'SIMULATED fixture; static subset only.', 'uninterpretable_fragments': []},
        'prompt_injection': {'detected': False, 'snippets': [], 'notes': 'SIMULATED fixture.'},
        'limitations': ['SIMULATED transport. No real model called.']}


class SyntheticTransport:
    def __init__(self):
        self.calls, self.residents, self.mode = [], [], 'ready'

    def json(self, endpoint, payload=None):
        self.calls.append((endpoint, deepcopy(payload)))
        if self.mode == 'offline':
            raise OperationalFailure('ollama_unavailable', 'SIMULATED offline provider')
        if endpoint == 'version': return {'version': '0.40.14-simulated'}
        if endpoint == 'tags': return {'models': [{'name': MODEL, 'digest': DIGEST}]}
        if endpoint == 'ps': return {'models': deepcopy(self.residents)}
        if endpoint == 'show': return {'capabilities': ['completion'], 'model_info': {'qwen3.context_length': 262144}}
        if endpoint != 'chat' or payload.get('model') != MODEL:
            raise AssertionError('Test harness only accepts the authorized synthetic chat')
        if self.mode == 'timeout': raise OperationalFailure('timeout', 'SIMULATED timeout; never retry')
        data = json.loads(payload['messages'][1]['content'])
        script = data['original']
        behaviors = []
        if 'CASE:incoherent' in script:
            behaviors = [finding('B05', 'Get-Process'), finding('B07', 'Get-Credential')]
        elif 'CASE:drop' in script:
            behaviors = [finding('B05', 'Write-Output "Get-Process"')]
        elif 'CASE:recovered' in script:
            texts = data.get('deterministic_recovery', {}).get('verified_texts', [])
            step = next((t for t in texts if t['text'] == 'Get-Process'), None)
            if step: behaviors = [finding('B05', 'Get-Process', step['source_id'])]
        elif 'CASE:bad-citation' in script:
            behaviors = [finding('B05', 'fabricated evidence')]
        else:
            for line in script.splitlines():
                if line.strip() == 'Get-Process': behaviors.append(finding('B05', 'Get-Process'))
                if line.startswith('Invoke-RestMethod '): behaviors.append(finding('B06', line))
        answer = report(behaviors, 'high_risk' if 'CASE:incoherent' in script else 'unknown')
        content = '{invalid JSON' if 'CASE:invalid-json' in script else json.dumps(answer, ensure_ascii=False)
        self.residents = [{'name': MODEL, 'digest': DIGEST, 'context_length': 8192, 'size_vram': 0}]
        return {'model': MODEL, 'done': True, 'done_reason': 'stop', 'message': {'content': content},
                'prompt_eval_count': 1200, 'eval_count': 300}

    def cancel(self): pass


def make_app():
    root = Path(os.environ.get('PSI_TEST_TEMP') or tempfile.mkdtemp(prefix='psi-integration-'))
    root.mkdir(parents=True, exist_ok=True)
    transport = SyntheticTransport()
    settings = profile.load_settings()
    memory = lambda: {'available_bytes': (1 if transport.mode == 'memory' else 32 * 1024**3),
        'commit_available_bytes': 40 * 1024**3, 'commit_limit_bytes': 64 * 1024**3,
        'physical_total_bytes': 64 * 1024**3}
    adapter = profile.PrototypeAdapter(settings, transport_factory=lambda: transport, sampler=memory,
                                       gate_factory=lambda: InferenceGate(root / 'integration.lock'))
    service = AnalysisService(settings, adapter=adapter, strategy=DeterministicLayersStrategy())
    app = create_app(service=service, frontend_dir=root / 'no-dist')
    origin = os.environ.get('PSI_TEST_ORIGIN', 'http://127.0.0.1:8765')
    parsed = urlsplit(origin)
    if parsed.scheme != 'http' or parsed.hostname not in {'127.0.0.1', 'localhost'}:
        raise ValueError('Integration harness requires a loopback HTTP origin')
    for middleware in app.user_middleware:
        if middleware.cls.__name__ == 'LocalBoundary': middleware.kwargs['origins'].append(origin)
        if middleware.cls.__name__ == 'CORSMiddleware': middleware.kwargs['allow_origins'].append(origin)
    app.state.synthetic_transport = transport

    @app.get('/__test/state')
    async def state():
        return {'synthetic': True, 'mode': transport.mode,
                'chats': sum(endpoint == 'chat' for endpoint, _ in transport.calls),
                'requests': [payload for endpoint, payload in transport.calls if endpoint == 'chat']}

    @app.post('/__test/mode')
    async def mode(value: dict = Body(...)):
        selected = value.get('mode')
        if selected not in {'ready', 'offline', 'memory', 'timeout'}: raise ValueError('Unknown test mode')
        transport.mode = selected
        return {'synthetic': True, 'mode': selected}
    # Mount last: otherwise '/' captures the test controls before their routes.
    from fastapi.staticfiles import StaticFiles
    dist = Path(__file__).resolve().parents[3] / 'frontend/dist'
    if (dist / 'index.html').is_file(): app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
    return app
