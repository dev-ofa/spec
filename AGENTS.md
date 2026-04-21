# spec AGENTS.md

本文件为 AI 编码 Agent 提供基于 dev-ofa 规范的执行标准。
在编写或修改任何遵循本规范体系的代码前，Agent 应阅读本文件并遵守以下规则。

## 前置要求

1. 开始编码前，先确认当前任务涉及哪些规范领域（API / Config / Logging / Tracing / Resilience / Entity / Patterns），并阅读对应的 spec 文件
2. 确认目标语言（Go / Python），阅读对应的落地指南（`guides/go/README.md` 或 `guides/python/README.md`）以及通用编码规范（`guides/coding.md`）
3. 查看项目已有代码的风格与模式，优先保持一致

## API 规范要点

> 完整规范：[api/spec.md](./api/spec.md)

- 所有应用层响应必须使用统一 Wrapper：`{ code, message, request_id, data }`
- `code = 0` 表示成功，`code < 20000` 为系统错误，`code >= 20000` 为业务错误
- URL 使用 kebab-case，JSON 字段使用 snake_case
- 遵循资源导向设计：标准方法用 HTTP 动词（GET/POST/PATCH/DELETE），自定义方法用 `POST /resource:verb`
- 列表接口空数据必须返回 `[]`，不得返回 `null`

## 配置规范要点

> 完整规范：[config/spec.md](./config/spec.md)

- 加载优先级：默认配置 → 环境变量 → 本地覆盖文件 → 命令行参数
- 密钥/密码/Token 只能从环境变量或安全存储读取，禁止硬编码、禁止明文日志
- 启动时必须做完整性与类型校验，缺失关键配置必须阻止启动
- 配置命名使用统一前缀与分组（如 `APP.HTTP.PORT`、`APP.DB.URI`）

## 日志规范要点

> 完整规范：[logging/spec.md](./logging/spec.md)

- 每个请求必须记录一条开始日志与一条结束日志
- 日志必须包含 `trace_id` 与 `request_id`
- 日志级别：正常 INFO、业务失败 WARN、系统错误 ERROR
- 推荐记录字段：method、path、status_code、code、duration_ms、error

## 链路透传规范要点

> 完整规范：[tracing/spec.md](./tracing/spec.md)

- 全链路透传 header 使用 `OFA_PASS_` 前缀：`OFA_PASS_TRACE_ID`、`OFA_PASS_OPERATOR`、`OFA_PASS_TENANT_ID`、`OFA_PASS_APP_ID`
- 单跳直传 header 使用 `OFA_DIRECT_` 前缀：`OFA_DIRECT_REQUEST_ID`、`OFA_DIRECT_REMAINING_TIMEOUT_MS`
- `trace_id` 格式：32 位小写十六进制（16 字节随机数）
- `request_id` 格式：`req_<YYYYMMDD_HHMMSS>_<suffix>`，suffix 为 16 位小写 base32 或 20 位小写十六进制
- 链路 ID 由请求发起方（client）负责生成，不是接收方（server）
- 对外请求必须携带 `OFA_PASS_TRACE_ID` 与 `OFA_DIRECT_REQUEST_ID`
- 已有的 `OFA_PASS_*` 字段不得被下游丢弃、清空或改写

## 弹性（超时与重试）规范要点

> 完整规范：[resilience/spec.md](./resilience/spec.md)

### 超时
- 链路总超时由 `timeout quota` 控制，不得各跳独立设完整 timeout
- 进程内使用 `authoritative deadline`（绝对时间），跨服务传播使用 `remaining timeout`（相对时间）
- remaining timeout <= 0 时必须立即失败，不得继续调用下游
- 禁止无界等待、禁止放大/重置上游 quota

### 重试
- 仅幂等操作或确认未被处理的请求才允许重试
- 默认最多重试 2 次（总尝试 3 次）
- 必须使用带 jitter 的指数退避，禁止固定间隔
- 所有重试共享同一个 timeout quota

## 实体规范要点

> 完整规范：[entity/spec.md](./entity/spec.md)

- 主键字段：`id`（必须）
- 审计字段必须成对：`created_at/created_by`、`updated_at/updated_by`、`deleted_at/deleted_by`
- 租户隔离字段必须成对：`tenant_id`、`app_id`
- 软删语义：`deleted_at` 为空 = 有效，非空 = 逻辑删除

## 常用模式要点

> 完整规范：[patterns/spec.md](./patterns/spec.md)

- CRUD：资源名词复数，Create/Update 返回统一 Wrapper，Delete 返回被删资源 id
- 异步 Worker：任务必须幂等，失败支持重试与死信，记录开始/结束日志
- 唯一 ID：全局唯一且趋势递增，支持多节点并发

## 编码通用规则

> 完整规范：[guides/coding.md](./guides/coding.md)

- 函数和结构体字段都应该有注释
- 业务错误与系统错误分层处理，禁止吞错误
- 关键逻辑必须有单元测试
- 入口层必须打请求生命周期日志并透传 trace 标识

## 语言落地指南

### Go
> 完整指南：[guides/go/README.md](./guides/go/README.md)

- 目录分层：`cmd/` → `internal/{app,domain,infra,handler}` → `configs/` → `scripts/`
- `cmd/<app>/main.go` 只做启动与装配，不承载业务逻辑
- 使用 Go Modules，CI 使用 `-mod=readonly`
- 必须执行 `gofmt`，推荐 `golangci-lint`
- 项目必须提供 Makefile：fmt / tidy / lint / test / build / run

### Python
> 完整指南：[guides/python/README.md](./guides/python/README.md)

- 目录分层：`src/<package>/{app,domain,infra,handler}` → `tests/` → `scripts/`
- 必须使用虚拟环境，推荐 `uv` 管理依赖
- 缩进 4 空格，禁止 Tab
- 推荐 `ruff format` + `ruff check` + `pyright`/`mypy`
- 项目必须提供 Makefile：fmt / lint / type / test / lock / sync

## 编码前 Checklist

- [ ] 确认涉及哪些规范模块，已阅读对应 spec
- [ ] 确认目标语言，已阅读对应落地指南
- [ ] 确认项目已有代码风格，保持一致

## 编码后 Checklist

- [ ] 所有 API 响应使用统一 Wrapper
- [ ] 错误码遵循分段规范（系统 < 20000，业务 >= 20000）
- [ ] 请求入口有生命周期日志（开始 + 结束），包含 trace_id 和 request_id
- [ ] 对外调用携带 OFA_PASS_TRACE_ID 和 OFA_DIRECT_REQUEST_ID
- [ ] 对外调用设置了 timeout quota，无无界等待
- [ ] 实体包含完整审计字段与租户隔离字段
- [ ] 敏感信息未出现在日志、配置文件或代码中
- [ ] 关键逻辑有单元测试
- [ ] 通过 lint / fmt / type 检查
