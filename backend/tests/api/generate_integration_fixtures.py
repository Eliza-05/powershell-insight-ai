"""Regenerate inert UI fixtures through the real app and synthetic transport only."""
import json
from pathlib import Path
import tempfile

from fastapi.testclient import TestClient
from tests.api.integration_server import make_app

CASES = {
    'kept': ('B', "# á🧪\r\nGet-Process\r\nInvoke-RestMethod -Uri 'https://example.invalid/test' -Method Post -Body 'academic'"),
    'dropped': ('B', "Write-Output 'CASE:drop'\nWrite-Output \"Get-Process\""),
    'incoherent': ('B', "Write-Output 'CASE:incoherent'\nGet-Process; Get-Credential"),
    'opaque': ('B', "Write-Output --% # opaque remains"),
    'recovered': ('C', "Write-Output 'CASE:recovered'\n$s='Get-' + 'Process'; Write-Output $s"),
    'invalid_json': ('B', "Write-Output 'CASE:invalid-json'"),
    'bad_citation': ('C', "Write-Output 'CASE:bad-citation'"),
    'empty': ('B', "Write-Output 'synthetic empty report'"),
    'comparison': ('ABC', "# á🧪\r\nGet-Process\r\nInvoke-RestMethod -Uri 'https://example.invalid/test' -Method Post -Body 'academic'"),
}


def packets():
    app = make_app()
    result = {}
    with TestClient(app, base_url='http://127.0.0.1') as client:
        for name, (mode, script) in CASES.items():
            response = client.post('/api/compare' if mode == 'ABC' else '/api/analyze/' + mode, json={'script': script})
            assert response.status_code == 200, response.text
            result[name] = {'mode': mode, 'script': script, 'response': response.json()}
    return result


if __name__ == '__main__':
    destination = Path(__file__).resolve().parents[3] / 'frontend/src/test/fixtures/integrated-qwen3.json'
    destination.write_text(json.dumps(packets(), ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    print(destination)
