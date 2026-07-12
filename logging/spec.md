## logging

### 状态
Draft

### 目标
- 统一请求生命周期日志的最小记录要求与推荐字段。
- 支撑基于 `trace_id`、`request_id` 的排障、审计与问题定位。

### 适用范围
- 服务入口处理一次请求或一次 RPC 调用时产生的生命周期日志。
- 与请求结果、耗时和错误摘要相关的结构化日志字段。

### 非目标
- 不限制具体日志库、采集管道、存储平台或检索系统。
- 不覆盖业务自定义埋点、审计平台或指标系统的全部设计。

### 请求生命周期日志

#### 必须
- 每个请求必须记录一条开始日志与一条结束日志
- 日志必须包含 trace_id 与 request_id
- 链路上下文、请求结果和错误摘要必须使用结构化字段记录，不得只拼接在 message 中

#### 推荐字段
- method：请求方法或 RPC 名称
- path：HTTP 路径或服务名
- status_code：协议层状态码
- code：业务码
- duration_ms：请求耗时
- error：错误摘要

#### 开始日志
- 开始日志应记录请求入口的链路上下文快照
- 链路上下文快照应记录以下标准字段中已解析出的值：
  - trace_id
  - request_id
  - operator
  - tenant_id
  - app_id
  - locale
  - remaining_timeout_ms
- `operator`、`tenant_id`、`app_id`、`locale`、`remaining_timeout_ms` 的语义与传播规则遵循 `tracing` 与 `resilience` 规范
- 开始日志不得记录完整原始 header；如果需要记录额外透传字段，必须使用显式白名单

#### 结束日志
- 结束日志应记录请求结果、耗时和错误摘要
- 结束日志不应重复记录完整链路上下文快照；除 `trace_id` 与 `request_id` 外，只应补充与结果定位直接相关的字段

### 请求内业务日志

- 请求处理过程中产生的业务日志应携带 `trace_id` 与 `request_id`
- 普通业务日志不应重复记录完整链路上下文快照
- 普通业务日志应优先保持 message 可读，并只补充当前事件定位所需的业务字段，例如 user_id、resource_id、conversation_id、task_id
- 当日志事件本身涉及身份解析、权限校验、租户隔离、灰度路由、计费、下游调用或跨协议传播时，可以补充对应的 `operator`、`tenant_id`、`app_id`、`locale` 或白名单透传字段

### Header 与透传字段记录边界

- 日志不得对入站或出站 header 做全量 dump
- 标准链路字段应先解析为规范语义字段，再按本规范记录；日志字段名应使用 `trace_id`、`request_id`、`operator`、`tenant_id`、`app_id`、`locale`、`remaining_timeout_ms`，不得直接依赖不同协议中的原始 header 名作为主要检索字段
- 业务自定义透传字段默认不得记录；只有当字段会影响路由、灰度、租户隔离、权限判断、审计、计费或关键排障时，才可以加入日志白名单
- 白名单字段必须有稳定名称、明确语义和脱敏策略
- 日志、trace、metrics、埋点、错误上报和审计记录不得输出原始 access token、refresh token、session cookie、query token、签名 URL、完整 credential、完整 Cookie header 或可直接复用的敏感值
- 如果为了排障需要记录凭证相关信息，应只记录 credential source、签发方、到期时间、摘要前缀或脱敏后的指纹；具体凭证约束遵循 `authentication` 与 `resource` 规范

### 级别建议
- 正常结束使用 INFO
- 业务失败使用 WARN
- 系统错误使用 ERROR
