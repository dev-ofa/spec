## api

### 状态
Draft

本项目的 API 设计遵循 **资源导向设计 (Resource Oriented Design)** 原则，主要参考 [Google API Design Guide (AIP)](https://google.aip.dev/1)。

> **注意**：本规范提炼了最核心的设计原则。更详细的内容请访问谷歌云的规范定义：[Google Cloud API Design Guide](https://cloud.google.com/apis/design) 或 [AIP.dev](https://google.aip.dev)。

### 核心原则

#### 资源导向
API 应围绕**资源 (Resources)** 及其**集合 (Collections)** 进行建模，而非围绕动作。
- **资源 (Resource)**: 具有类型、数据、关系和操作方法的实体。例如：`User`, `Book`。
- **资源名 (Resource Name)**: 资源的唯一标识符，通常采用分层路径结构。例如：`users/u123`, `publishers/p1/books/b1`。
- **集合 (Collection)**: 相同类型资源的列表。例如：`users`, `books`。

#### URL 结构
URL 应清晰地表达资源层级关系：
`GET /v1/publishers/{publisher_id}/books/{book_id}`

- **版本号**: API 版本应包含在 URL 中（如 `/v1/`）。
- **集合名**: 使用复数名词（如 `users`, `books`）。
- **资源 ID**: 紧随集合名之后。

### 标准方法

遵循 HTTP 动词的标准语义：

| 方法 | HTTP 动词 | URL 模式 | 请求体 | 描述 |
| :--- | :--- | :--- | :--- | :--- |
| **List** | `GET` | `/v1/{collection}` | N/A | 列出资源集合。支持分页、过滤。 |
| **Get** | `GET` | `/v1/{resource}` | N/A | 获取单个资源详情。 |
| **Create** | `POST` | `/v1/{collection}` | 资源对象 | 在集合中创建新资源。 |
| **Update** | `PATCH` | `/v1/{resource}` | 资源对象 (部分) | 更新资源（通常为部分更新）。 |
| **Delete** | `DELETE` | `/v1/{resource}` | N/A | 删除资源。 |

### 自定义方法

对于无法映射到标准 CRUD 的操作，使用自定义方法。
- **格式**: `POST /v1/{resource}:{verb}`
- **示例**:
  - `POST /v1/books/b1:checkout` (借书)
  - `POST /v1/books/b1:return` (还书)
  - `GET /v1/books:search` (复杂搜索)

### 命名规范

- **URI**: 使用小写字母，单词间用连字符分隔（kebab-case）。例如：`/v1/user-settings`。
- **JSON 字段**: 请求和响应体中的字段名使用下划线分隔（snake_case）。例如：`first_name`, `user_id`。
- **枚举值**: 使用全大写下划线分隔。例如：`STATE_Active`, `COLOR_RED`。

---

### 统一响应 Wrapper

所有应用层响应（HTTP Status 200 OK）必须包裹在统一的 Wrapper 中。

#### 结构定义
```json
{
  "code": 0,
  "message": "success",
  "request_id": "req_123456789",
  "data": { ... }
}
```

#### 必须字段
- **code** (`integer`): 业务状态码。
  - `0`: 成功。
  - `!= 0`: 失败（业务错误或系统错误）。
- **message** (`string`): 开发者可读的状态描述或错误提示。
- **request_id** (`string`): 请求唯一标识，用于链路追踪。必须贯穿一次请求与其所有下游调用。

#### 可选字段
- **data** (`object` | `array`): 业务数据载荷。
  - 如果无数据返回，建议不返回该字段或返回 `null`。
  - 对于列表接口，空数组必须返回 `[]`，不得返回 `null`。

### 错误码规范

#### 错误码分段
- **code < 20000**: 非预期错误或需要告警的系统级错误（System Errors）。
- **code >= 20000**: 预期内的业务逻辑错误（Business Errors），通常不需要告警，但需提示用户。

#### 推荐保留码段
| 错误码 | 类型 | 描述 |
| :--- | :--- | :--- |
| **0** | Success | 成功 |
| **10000** | System | 内部通用错误 (Internal Server Error) |
| **10001** | System | 资源不存在 (Not Found) |
| **10002** | System | 资源冲突 (Conflict) |
| **20000** | Business | 参数校验失败 (Bad Request) |
| **20001** | Business | 业务提示 (通用) |

### 协议关系

- **应用层响应**: 必须返回 Wrapper 结构。
- **传输层失败**: 如 HTTP 401, 403, 502 等，可直接返回协议错误码与错误体（或由网关处理）。
