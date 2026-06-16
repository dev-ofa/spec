## api

### 状态
Draft

### 目标
- 统一 HTTP API 的资源建模、URL 结构、标准方法、自定义方法与应用层响应约束。
- 降低跨语言接入与文档理解成本，使不同服务在资源命名和响应结构上保持一致。

### 适用范围
- 面向服务间或客户端访问的 HTTP/HTTPS 请求-响应式 API。
- 基于资源导向设计的应用层接口，以及其统一响应 Wrapper。

### 非目标
- 不覆盖 gRPC、消息订阅、双向流等非 HTTP 协议的接口设计。
- 不替代具体业务领域模型设计，也不逐条重述外部完整 AIP 规范。

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
  - `!= 0`: 失败，取值应来自原始错误的 `code`，错误码分段与分类遵循 `error` 规范。
- **message** (`string`): 开发者可读的状态描述或错误提示。
- **request_id** (`string`): 当前服务处理该次请求的唯一标识，用于定位单跳请求、响应与日志。不同服务间可以变化；跨服务关联应主要依赖 `trace_id`。

#### 可选字段
- **data** (`object` | `array` | `null`): 业务数据载荷。
  - 如果无数据返回，建议返回 `null`。
  - 对于列表接口，空数组必须返回 `[]`，不得返回 `null`。

### 协议关系

- **应用层响应**: 必须返回 Wrapper 结构。
- **传输层失败**: 如 HTTP 401, 403, 502 等，可直接返回协议错误码与错误体（或由网关处理）。
- **错误码来源**: Wrapper 中的失败 `code` 是原始错误的 `code`；错误分类、默认码和码段定义不在 API 规范中重复定义，统一遵循 `error` 规范。
