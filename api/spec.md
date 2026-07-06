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

#### 暴露层级与入口前缀

HTTP API 应明确区分调用方可见范围，避免把用户侧、服务侧和内部运营能力混挂在同一个外部入口下。

API 的暴露层级至少应区分：

- **产品 API**：面向 Web 前端、移动客户端、开放集成方或其他被授权外部调用方的 API。
- **内部 API**：面向集群内服务、受控运维入口、后台运营系统或人工调试工具的 API；例如批处理、运营发放、内部修复、诊断和低频管理能力。

路径前缀规则：

- 当 Web 页面与 HTTP API 共用同一个主域名或同一个网关入口时，产品 API 应使用 `/api` 作为路径命名空间，例如 `POST /api/v1/books`。
- 当使用独立 API 域名承载产品 API 时，可以省略 `/api` 前缀，例如 `POST https://api.example.com/v1/books`；此时 API 域名本身承担 API 入口语义。
- 内部 API 如果通过路径前缀区分，默认使用 `/internal-api`，并在其后继续沿用领域资源路径与方法命名，例如 `POST /internal-api/v1/metering/redeem-codes:batchCreate`。
- `/api`、`/internal-api` 等入口前缀只表达暴露层级，不替代版本号、资源集合名或自定义方法命名。

暴露与访问控制规则：

- 面向公网或外部调用方的网关、Ingress、负载均衡和反向代理不得默认转发 `/internal-api/**`。
- 内部 API 不得只依赖网络隔离；服务端仍必须执行身份认证与权限校验。
- 内部运营、批处理、诊断或人工修复能力不应挂载在产品 API 前缀下再仅靠 handler/controller 内部判断拦截。
- 如果某个系统采用独立内部域名而不是 `/internal-api` 前缀，例如 `https://internal-api.example.com/v1/...`，也必须在网关、认证和文档中明确该入口的内部暴露层级。

#### 资源表示与 DTO 边界

RESTful API 的响应载荷应优先表达资源本身，而不是为接口机械创建额外数据结构。

- 没有明确必要理由时，响应 `data` 应直接使用领域实体、资源对象或值对象的结构作为资源表示，不应仅因“API 返回需要一层 DTO/View”而创建独立 DTO。
- 创建响应 DTO 的理由必须来自稳定的 API 契约需要，例如隐藏内部字段或敏感字段、裁剪审计字段、组合多个资源形成特定读模型、维护版本兼容、适配对外字段格式或隔离内部模型演进。
- DTO 属于 API 边界模型。采用传统分层时，DTO 应控制在 handler/controller 等协议入口层；采用 DDD 分层时，DTO 应控制在 application 层或更外侧边界。
- DTO 转换也属于 API 边界逻辑。DTO 在哪一层定义，其转换函数、mapper、assembler 或等价组装逻辑也应控制在同一层或更外侧边界，不应下沉到业务层、领域层、domain service、业务 service 或 repository。
- 业务层、领域层、domain service、业务 service 与 repository 不应依赖 API DTO 作为核心入参、返回值或持久化模型；这些层的业务编码应基于领域实体、资源对象或值对象。
- 如果确需在 API 边界进行 DTO 转换，转换逻辑应保持资源语义清晰，不应把领域对象扁平化、重命名或重组为难以追溯原资源含义的结构，除非该变化本身已经是明确的对外 API 契约。

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
  - 可用于帮助服务、SDK、前端应用等调用方理解结果，但不等同于终端用户展示文案。
  - 默认不作为终端用户展示文案；尤其在非预期错误场景下，不得直接向终端用户展示。
  - 终端用户提示如需细分，应由产品层通用兜底文案或基于稳定错误码的映射规则提供。
- **request_id** (`string`): 当前服务处理该次请求的唯一标识，用于定位单跳请求、响应与日志。不同服务间可以变化；跨服务关联应主要依赖 `trace_id`。

#### 可选字段
- **data** (`object` | `array` | `null`): 业务数据载荷。
  - 如果无数据返回，建议返回 `null`。
  - 对于列表接口，空数组必须返回 `[]`，不得返回 `null`。

### 服务端耗时

HTTP API 如需向调用方暴露服务端处理耗时，应优先使用标准 `Server-Timing` 响应头，不应为 HTTP API 在业务 Wrapper 中新增必填耗时字段。

#### 最小格式

```http
Server-Timing: app;dur=<duration_ms>
```

- **app**: 当前服务的应用层处理耗时指标名。
- **dur**: 耗时值，单位为毫秒，可以包含小数，例如 `37` 或 `37.2`。

#### 语义约束

- `app;dur=<duration_ms>` 表示当前服务从进入应用层请求处理到生成应用层响应的耗时。
- 该值不代表客户端端到端耗时，不包含 DNS、建连、TLS、网络传输、响应体下载、客户端反序列化或客户端渲染耗时。
- 服务端仍应在请求生命周期日志中记录 `duration_ms`，日志字段要求遵循 `logging` 规范。
- 如需暴露更细粒度阶段，可以在同一个 `Server-Timing` 中追加指标，例如：

```http
Server-Timing: auth;dur=4.2, db;dur=18.6, app;dur=37.0
```

### 协议关系

- **应用层响应**: 必须返回 Wrapper 结构。
- **传输层失败**: 如 HTTP 401, 403, 502 等，可直接返回协议错误码与错误体（或由网关处理）。
- **错误码来源**: Wrapper 中的失败 `code` 是原始错误的 `code`；错误分类、默认码和码段定义不在 API 规范中重复定义，统一遵循 `error` 规范。
