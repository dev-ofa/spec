## tracing

### 状态
Draft

### 目标
- 本规范定义跨服务、跨协议、跨异步边界的链路透传字段。
- 目标是让日志、错误排查、权限审计与租户定位在整条调用链上保持可关联。

### 适用范围
- 跨服务调用、跨协议调用、消息投递与异步任务调度等需要透传链路上下文的场景。
- 跨语言统一的语义字段、HTTP header 与传播规则。

### 非目标
- 不约束具体框架、SDK 或语言内部的 context 实现方式。
- 不覆盖业务自定义透传字段的完整设计，只约束标准链路字段与保留名称。

### 透传字段

#### 命名层次
- `trace_id`、`request_id`、`remaining_timeout_ms`、`operator`、`tenant_id`、`app_id`、`locale` 是语义字段名，用于描述字段含义。
- `ofa-pass-*`、`ofa-direct-*` 是实际在 HTTP 链路上传输的标准 header 名。
- 标准 HTTP header 名 **必须** 使用小写字母、数字与连字符， **不得** 使用下划线或大写字母；接收方解析时 **必须** 按 HTTP 语义进行大小写不敏感匹配。
- HTTP 以外的协议如果支持字符串 metadata key， **应当** 优先复用对应的标准 HTTP header 名；如果协议不支持该命名形式， **必须** 提供等价字段并保持相同语义。
- 进程内 string ContextKey **必须** 使用小写字母、数字与连字符， **不得** 使用下划线或大写字母。
- 对于本规范中已有标准 HTTP header 的字段，进程内 string ContextKey **必须** 复用对应的标准 HTTP header 名。
- 对于仅在进程内传播、没有对应标准 HTTP header 的字段，进程内 string ContextKey **必须** 使用 `ofa-*` 前缀，且 **不得** 使用 `ofa-pass-*` 或 `ofa-direct-*`。
- 如果语言实现需要使用强类型 key 或私有 key， **可以** 自行封装，但其调试名、导出字符串值或映射关系 **必须** 明确对应到本规范定义的标准 string ContextKey。
- `trace_id`、`request_id`、`remaining_timeout_ms`、`operator`、`tenant_id`、`app_id`、`locale` 及其大小写、下划线、连字符等等价形式是规范保留语义字段，业务程序 **不得** 将这些名称用于自定义透传变量或赋予不同业务含义。
- 本规范列出的标准 header 名为保留 header，业务程序 **不得** 自行占用、覆盖、复用或以不同语义解释这些 header；业务自定义透传字段 **必须** 使用不会与标准字段冲突的名称。

#### 标准链路 Header

| 语义字段 | 标准 header | 传播范围 | 语义 | 生成/补齐规则 |
| --- | --- | --- | --- | --- |
| trace_id | ofa-pass-trace-id | 全链路 | 全局链路标识。用于关联同一条业务链路上的所有服务调用与异步任务。 | 由请求发起方在发起请求前负责设置；已有值时 **必须** 沿用，无值时视为链路起点并生成新的 16 字节随机值。 |
| request_id | ofa-direct-request-id | 单跳 | 单跳请求标识。用于标识当前服务收到或发起的一次具体调用，主要用于定位某一跳请求、响应与日志。 | 由请求发起方在每次发起请求前生成新值，不跨服务复用；格式为时间前缀加随机后缀。 |
| remaining_timeout_ms | ofa-direct-remaining-timeout-ms | 单跳 | 单跳剩余超时时间，单位毫秒。用于表达当前调用在发送瞬间还能继续分配给下游的剩余 timeout。 | 由请求发起方在发送请求瞬间基于本地 deadline 重新计算并写入；接收方收到后按当前时刻重建本地 deadline。 |
| operator | ofa-pass-operator | 全链路 | 操作者标识。用于标识发起当前业务动作的用户、账号或系统主体。 | 上游提供时直接透传；上游未提供但入口服务可从鉴权或上下文解析时， **可以** 补齐。 |
| tenant_id | ofa-pass-tenant-id | 全链路 | 租户标识。用于表达当前请求所属的租户隔离维度。 | 上游提供时直接透传；上游未提供但入口服务 **可以** 确定租户时， **可以** 补齐。 |
| app_id | ofa-pass-app-id | 全链路 | 应用标识。用于标识发起请求的应用、业务系统或接入方。 | 上游提供时直接透传；上游未提供但入口服务 **可以** 确定来源应用时， **可以** 补齐。 |
| locale | ofa-pass-locale | 全链路 | 当前请求已决策的 effective locale。用于保持服务间语言和格式化语义一致。 | 入口服务完成 locale 解析、归一化和 fallback 后 **可以** 补齐；上游已提供时直接透传。具体 locale 语义与决策优先级由 `i18n` 规范定义。 |

#### ID 格式
- `trace_id` **必须** 使用 `32位小写十六进制` 格式，例如 `8f14e45fceea167a5a36dedd4bea2543`
- `trace_id` **必须** 由 `16` 字节加密安全随机数编码而成，不带 `trace_` 前缀，不嵌入时间、机器标识或业务含义
- `request_id` **必须** 使用 `req_<YYYYMMDD_HHMMSS>_<suffix>` 格式，例如 `req_20260726_133502_e4cswh5f2whjd4ah`
- `request_id` 中的时间前缀 **必须** 使用 UTC 时间
- `request_id` 中的 `<suffix>` **必须** 由加密安全随机数生成，推荐使用 `10` 字节随机数编码为 `16` 位小写 base32 字符串
- 如果语言实现暂时没有统一的 base32 方案，`request_id` 的 `<suffix>` 也 **可以** 退化为 `20` 位小写十六进制字符串
- `request_id` 的 `<suffix>` **不得** 依赖中心发号器、机器 IP、进程号、线程号或普通伪随机数生成器
- 生成结果 **必须** 仅包含小写字母、数字与下划线，便于在不同协议、日志系统与网关中稳定传递

#### 生成责任
- 链路 ID 的标准生成方是请求发起方（client），而不是请求接收方（server）
- 发起任意一次对外请求前，client **必须** 生成新的 `request_id`，并通过 `ofa-direct-request-id` 发送
- 发起请求前如果已经持有 `trace_id`， **必须** 继续沿用，并通过 `ofa-pass-trace-id` 发送；如果没有，则视为链路起点并生成新的 `trace_id`
- server 端 **不应** 把“收到请求后再补生成 ID”作为标准机制；标准链路 **应当** 依赖 client 在发送前完成生成
- 如果为了兼容存量调用方而在 server 端做缺失兜底，该行为仅属于兼容措施，不改变本规范的责任边界

#### 传播规则
- 所有对外请求 **必须** 携带 `ofa-pass-trace-id` 与 `ofa-direct-request-id`
- `ofa-pass-trace-id`、`ofa-pass-operator`、`ofa-pass-tenant-id`、`ofa-pass-app-id`、`ofa-pass-locale` 视为全链路透传字段
- 请求发起方 **必须** 在发送前完成 `trace_id` 与 `request_id` 的生成或补齐，并写入对应标准 HTTP header
- 服务在发起下游调用时， **必须** 沿用当前 `trace_id`，并在发送前为该次下游调用生成新的 `request_id`
- 如果当前上下文启用了超时控制，且目标下游支持 OFA 超时传播模型，则请求发起方在发送前 **必须** 同时写入 `ofa-direct-remaining-timeout-ms`
- 如果目标下游不支持 OFA 超时传播模型，则超时 **应当** 按 `resilience` 规范在本地基于 authoritative deadline 映射到该下游调用自己的 timeout 参数
- `operator`、`tenant_id`、`app_id`、`locale` 在有值时 **不得** 被下游服务随意丢弃、清空或改写
- 所有下游调用 **必须** 透传当前上下文中已有的 `ofa-pass-*` 字段，并携带该次调用自己的 `ofa-direct-request-id`
- `ofa-direct-remaining-timeout-ms` 的具体计算、裁剪与重试约束由 `resilience` 规范定义
- 跨协议调用、消息投递、异步任务调度等场景同样适用上述传播规则

#### `operator` 写入边界
- `operator` 表示发起当前业务动作的已确定主体，不表示被访问资源的 owner、creator 或其他业务归属字段。
- 普通业务处理链路 **不得** 为了匹配资源归属、数据隔离、审计写入或持久化查询而覆盖已解析出的 `operator`。
- 资源归属与权限校验 **应当** 读取当前 `operator`，再与资源自身的 owner、creator 或访问控制字段比较； **不得** 通过改写 `operator` 来绕过校验。
- 只有明确建立执行主体的可信边界才 **可以** 写入或补齐 `operator`，包括认证入口、会话解析入口、服务间可信网关、异步 worker、webhook、补偿任务，以及登录或账号创建等自举流程。
- 系统主动发起且没有终端用户主体的任务 **必须** 使用可识别的系统主体，例如 `system:{module}`；如果系统任务代表某个用户执行， **应当** 在任务定义中显式说明代表关系与审计口径。
- 下游服务收到已有 `operator` 时 **必须** 默认沿用；除非进入新的可信身份边界并完成重新认证或重新解析，否则 **不得** 清空、替换或降级该值。

#### 前缀约定
- `ofa-pass-` 表示全链路透传 header
- `ofa-direct-` 表示单跳直传 header
- `ofa-` 且不带 `pass` / `direct` 子前缀的名字，表示仅在进程内传播、没有对应标准 HTTP header 的 string ContextKey
- 不带前缀的名字仅用于表达语义字段名；它们不是标准 HTTP header 名，也不是标准 string ContextKey
- 本规范统一的是链路语义字段、HTTP header 名与 string ContextKey 名
- `ofa-direct-request-id` 与 `ofa-direct-remaining-timeout-ms` 是本规范中定义的通用 `ofa-direct-*` 字段
- 除上述字段外，其他 `ofa-direct-*` 字段由服务按需自行约定
- 业务自定义 `ofa-pass-*` 或 `ofa-direct-*` 扩展字段时， **不得** 使用与标准语义字段等价的名称，例如 `trace-id`、`request-id`、`remaining-timeout-ms`、`operator`、`tenant-id`、`app-id`、`locale`。
