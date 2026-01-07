# REST API 设计规范（项目级）

## 1. 目标与适用范围

**目标**

* 统一 API 风格，降低前后端/服务间联调成本
* 提升接口可读性、可维护性、可演进性
* 让错误“可诊断、可追踪、可治理”

**适用范围**

* 所有 HTTP API（对外 / 对内 / BFF / 网关后服务）

---

## 2. 基础约定

### 2.1 Base URL 与版本

* Base URL：

  ```
  /api/v1
  ```

* **版本升级原则**

  * 仅当存在 **不兼容变更**（字段删除、语义变化）才升级版本
  * 新增字段 / 新增接口 **不升级版本**

---

### 2.2 命名规范

| 项目      | 规范                                |
| ------- | --------------------------------- |
| URL     | 名词 + 复数                           |
| JSON 字段 | camelCase                         |
| 时间字段    | createdAt / updatedAt / deletedAt |
| 主键      | id                                |
| 外键      | userId / orderId                  |

**示例**

```http
GET /api/v1/users
GET /api/v1/users/{userId}/orders
```

---

### 2.3 Content-Type

* Request：

  ```
  application/json; charset=utf-8
  ```
* Response：

  ```
  application/json; charset=utf-8
  ```

---

## 3. URL 与 HTTP Method 规范

### 3.1 CRUD 映射

| 操作   | Method | URL             |
| ---- | ------ | --------------- |
| 列表   | GET    | /resources      |
| 创建   | POST   | /resources      |
| 详情   | GET    | /resources/{id} |
| 全量更新 | PUT    | /resources/{id} |
| 部分更新 | PATCH  | /resources/{id} |
| 删除   | DELETE | /resources/{id} |

---

### 3.2 子资源与动作接口

**子资源**

```http
GET /users/{userId}/orders
```

**动作接口（谨慎使用）**

```http
POST /orders/{orderId}:cancel
```

> 仅用于无法抽象为资源的业务“命令”

---

## 4. 请求（Request）设计

### 4.1 参数位置约定

| 类型    | 位置     |
| ----- | ------ |
| 资源 ID | Path   |
| 查询条件  | Query  |
| 业务数据  | Body   |
| 鉴权/幂等 | Header |

---

### 4.2 Query 参数规范（统一）

#### 分页（强制统一）

```text
page      从 1 开始，默认 1
pageSize  默认 20，最大 100
```

#### 排序

```text
sort=field,(asc|desc)
```

示例：

```http
GET /users?sort=createdAt,desc
```

#### 搜索与过滤

```http
GET /users?keyword=alice&status=ACTIVE
```

* 多值：`status=ACTIVE,DISABLED`
* 时间范围：

  * `createdAtFrom`
  * `createdAtTo`

---

### 4.3 Body 参数规范

#### 创建（POST）

* 禁止传入：

  * `id`
  * `createdAt`
  * `updatedAt`

```json
{
  "name": "Alice",
  "email": "alice@example.com"
}
```

---

#### 更新（PUT / PATCH）

**PUT（全量）**

```json
{
  "name": "Alice",
  "email": "alice@example.com",
  "status": "ACTIVE"
}
```

**PATCH（部分，推荐）**

```json
{
  "status": "DISABLED"
}
```

---

## 5. 响应（Response）设计

### 5.1 统一响应结构（强制）

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req_xxx",
  "data": {}
}
```

| 字段        | 说明          |
| --------- | ----------- |
| code      | 业务码（0 = 成功） |
| message   | 提示信息        |
| requestId | 链路追踪 ID     |
| data      | 业务数据        |

---

### 5.2 列表分页响应（强制）

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req_xxx",
  "data": {
    "list": [],
    "page": 1,
    "pageSize": 20,
    "total": 135
  }
}
```

---

### 5.3 空结果约定

| 场景     | 返回           |
| ------ | ------------ |
| 成功但无数据 | `data: null` |
| 空列表    | `list: []`   |
| ❌ 不允许  | `{}` / 缺字段   |

---

## 6. 错误处理规范

### 6.1 HTTP 状态码使用

| 状态码 | 场景    |
| --- | ----- |
| 200 | 成功    |
| 201 | 创建成功  |
| 400 | 参数错误  |
| 401 | 未认证   |
| 403 | 无权限   |
| 404 | 不存在   |
| 409 | 冲突    |
| 429 | 限流    |
| 500 | 服务异常  |
| 503 | 服务不可用 |

---

### 6.2 错误响应结构（强制）

```json
{
  "code": 10001,
  "message": "Invalid parameter",
  "requestId": "req_xxx",
  "data": {
    "errors": [
      {
        "field": "email",
        "reason": "format error"
      }
    ]
  }
}
```

---

### 6.3 错误码分段规范

| 段位    | 含义      |
| ----- | ------- |
| 0     | 成功      |
| 1xxxx | 通用 / 鉴权 |
| 2xxxx | 用户域     |
| 3xxxx | 订单域     |
| 9xxxx | 系统异常    |

**最低必备**

```text
0       success
10001   Invalid parameter
10002   Unauthorized
10003   Forbidden
10004   Not found
10009   Conflict
10029   Rate limited
20000   Internal error
```

---

## 7. 鉴权与权限

### 7.1 JWT 鉴权（默认）

```http
Authorization: Bearer <token>
```

| 场景          | 返回  |
| ----------- | --- |
| token 缺失/无效 | 401 |
| 权限不足        | 403 |

---

## 8. 幂等性（创建类接口强制）

适用场景：

* 下单
* 支付
* 发放
* 批量创建

### 8.1 Header

```http
Idempotency-Key: <uuid>
```

### 8.2 行为

* 相同 Key + 相同参数 → 返回相同结果
* Key 冲突 → 409（或返回首次结果）

---

## 9. 并发更新控制

### 9.1 version 字段（推荐）

* 资源返回：

```json
{
  "id": "123",
  "version": 3
}
```

* 更新必须携带：

```json
{
  "version": 3,
  "status": "ACTIVE"
}
```

* 不匹配 → `409 Conflict`

---

## 10. 文件上传（如使用）

### 10.1 上传接口

```http
POST /files
Content-Type: multipart/form-data
```

字段：

* `file`：binary
* `bizType`：avatar / invoice / attachment

返回：

```json
{
  "code": 0,
  "message": "success",
  "requestId": "req_xxx",
  "data": {
    "fileId": "f_123",
    "url": "https://..."
  }
}
```

---

## 11. 兼容性与演进策略（强制）

* ✅ 新增字段必须 **可选**
* ❌ 禁止直接删除字段
* 字段废弃：

  * 保留 ≥ 1 个版本周期
  * OpenAPI 标记 `deprecated: true`
* 枚举新增：

  * 客户端必须能容忍未知值

---

## 12. OpenAPI（Swagger）要求

* 每个服务必须提供：

  * `/api/v1/openapi.yaml`
  * `/swagger.json`
* 必须包含：

  * securitySchemes
  * 统一 BaseResponse / ErrorResponse
  * requestId 字段
  * 统一分页 schema

---
