from __future__ import annotations

from typing import Any, Dict, List

from fastapi.testclient import TestClient

from api.http.constants import HEADER_IDEMPOTENCY_KEY, HEADER_REQUEST_ID, ParseStatus
from api.http.deps import get_redis_client
from api.http.main import app


def _client() -> TestClient:
    app.dependency_overrides[get_redis_client] = lambda: None
    return TestClient(app)


def test_leech_success_uses_request_id_header(monkeypatch):
    captured: Dict[str, Any] = {}

    def fake_parse_link(link: str, request_id: str, options: dict[str, Any]) -> List[Any]:
        captured['request_id'] = request_id
        captured['options'] = options
        return [{'name': 'file'}]

    def fake_serialize_files(files: List[Any]) -> List[Any]:
        return files

    def fake_enqueue(self, payload: dict[str, Any]) -> str:
        captured['payload'] = payload
        return 'task-123'

    monkeypatch.setattr('api.http.routers.leech.parse_link', fake_parse_link)
    monkeypatch.setattr('api.http.routers.leech.serialize_files', fake_serialize_files)
    monkeypatch.setattr('api.http.services.queue_service.QueueService.enqueue', fake_enqueue)

    client = _client()
    response = client.post(
        '/leech',
        headers={HEADER_REQUEST_ID: 'req-abc'},
        json={'link': 'https://example.com/file', 'tool': 'alist'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['requestId'] == 'req-abc'
    assert body['data']['taskId'] == 'task-123'
    assert body['data']['status'] == ParseStatus.QUEUED.value
    assert body['data']['files'] == [{'name': 'file'}]
    assert captured['request_id'] == 'req-abc'
    assert captured['payload']['tool'] == 'alist'
    assert 'headers' not in captured['payload']
    assert 'dry_run' not in captured['options']


def test_leech_idempotency_hit_returns_cached(monkeypatch):
    def fake_get(self, key: str):
        assert key == 'idem-1'
        return {'task_id': 'task-xyz', 'files': [{'id': 1}]}

    def fake_enqueue(self, payload: dict[str, Any]) -> str:
        raise AssertionError('enqueue should not be called on idempotency hit')

    monkeypatch.setattr('api.http.services.idem_service.IdempotencyService.get', fake_get)
    monkeypatch.setattr('api.http.services.queue_service.QueueService.enqueue', fake_enqueue)

    client = _client()
    response = client.post(
        '/leech',
        headers={HEADER_IDEMPOTENCY_KEY: 'idem-1', HEADER_REQUEST_ID: 'req-1'},
        json={'link': 'https://example.com/file'},
    )

    assert response.status_code == 200
    body = response.json()
    assert body['requestId'] == 'req-1'
    assert body['data']['taskId'] == 'task-xyz'
    assert body['data']['files'] == [{'id': 1}]


def test_leech_validation_error_returns_standard_error():
    client = _client()
    response = client.post('/leech', json={})

    assert response.status_code == 400
    body = response.json()
    assert body['code'] == 10001
    assert body['message'] == 'Invalid parameter'
    assert body['data']['errors'][0]['field'] == 'link'
