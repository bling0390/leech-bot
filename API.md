# Web API 文档

- Base URL: `http://<host>:8000`
- Auth: 可选 `X-API-Key: <API_KEY>`（设置 `API_KEY` 环境变量时必需）
- Idempotency: 可选 `Idempotency-Key: <unique-key>`，命中后直接返回已存在的 task

## POST /leech
提交解析并入队下载任务

### Headers
- `Content-Type: application/json`
- `X-API-Key`（可选，开启 API_KEY 时必填）
- `Idempotency-Key`（可选，开启幂等）

### Request Body
```json
{
  "link": "https://example.com/file",
  "target": "alist",
  "path": "/tmp",
  "headers": { "User-Agent": "demo" },
  "dry_run": true
}
```
- link: 必填，http/https/magnet，长度 <= 4096
- 其余字段可选；`dry_run` 默认 true（设为 false 会在解析阶段触发内部队列逻辑）

### Success Response 200
```json
{
  "request_id": "f3b7c4e4-0f7c-4f92-9c1e-2a8a5b75e6a2",
  "task_id": "celery-task-id",
  "status": "queued",
  "files": [ ... ]
}
```
- files: 解析得到的 LeechFile 列表，原样可序列化返回

### Error Responses
- 400: `PARSE_FAILED` 或 `BAD_REQUEST`
- 401: `UNAUTHORIZED`
- 503: `QUEUE_UNAVAILABLE`
- 500: `INTERNAL_ERROR`
```json
{
  "request_id": "uuid",
  "error": { "code": "PARSE_FAILED", "message": "Failed to parse link" }
}
```

### 示例
```bash
curl -X POST http://localhost:8000/leech \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your_api_key' \
  -H 'Idempotency-Key: demo-123' \
  -d '{"link":"https://example.com/file","target":"alist","path":"/tmp","headers":{"User-Agent":"demo"},"dry_run":true}'
```

## GET /healthz
健康检查
```json
{ "status": "ok" }
```
