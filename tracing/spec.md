## tracing

### 状态
Draft

### 目标
- 本规范定义跨服务、跨协议、跨异步边界的链路透传字段。
- 目标是让日志、错误排查、权限审计与租户定位在整条调用链上保持可关联。

### 适用范围
- 跨服务调用、跨协议调用、消息投递与异步任务调度等需要透传链路上下文的场景。
- 跨语言统一的链路 header、语义字段与传播规则。

### 非目标
- 不约束具体框架、SDK 或语言内部的 context 实现方式。
- 不覆盖业务自定义透传字段的完整设计，只约束标准链路字段与保留名称。

### 透传字段

#### 命名层次
- `trace_id`、`request_id`、`remaining_timeout`、`operator`、`tenant_id`、`app_id`、`locale` 是语义字段名，用于描述字段含义。
- `OFA_PASS_*`、`OFA_DIRECT_*` 是实际在链路上传输的标准 header 名。
- `OFA_*` 也可以用于表示由其他领域 spec 显式注册的标准 context value；这类名字不是标准 header 名。
- 除其他 spec 已显式注册的标准 context value 外，语言实现中的内存 context key、局部变量名、常量名不在本规范约束范围内，只要语义不冲突即可。
- `trace_id`、`request_id`、`remaining_timeout`、`operator`、`tenant_id`、`app_id`、`locale` 及其大小写/下划线等等价形式是规范保留语义字段，业务程序不得将这些名称用于自定义透传变量或赋予不同业务含义。
- 本规范列出的标准 header 名为保留 header，业务程序不得自行占用、覆盖、复用或以不同语义解释这些 header；业务自定义透传字段必须使用不会与标准字段冲突的名称。

#### 标准链路 Header

| 语义字段 | 标准 header | 传播范围 | 语义 | 生成/补齐规则 |
| --- | --- | --- | --- | --- |
| trace_id | OFA_PASS_TRACE_ID | 全链路 | 全局链路标识。用于关联同一条业务链路上的所有服务调用与异步任务。 | 由请求发起方在发起请求前负责设置；已有值时必须沿用，无值时视为链路起点并生成新的 16 字节随机值。 |
| request_id | OFA_DIRECT_REQUEST_ID | 单跳 | 单跳请求标识。用于标识当前服务收到或发起的一次具体调用，主要用于定位某一跳请求、响应与日志。 | 由请求发起方在每次发起请求前生成新值，不跨服务复用；格式为时间前缀加随机后缀。 |
| remaining_timeout | OFA_DIRECT_REMAINING_TIMEOUT_MS | 单跳 | 单跳剩余超时时间。用于表达当前调用在发送瞬间还能继续分配给下游的剩余 timeout。 | 由请求发起方在发送请求瞬间基于本地 deadline 重新计算并写入；接收方收到后按当前时刻重建本地 deadline。 |
| operator | OFA_PASS_OPERATOR | 全链路 | 操作者标识。用于标识发起当前业务动作的用户、账号或系统主体。 | 上游提供时直接透传；上游未提供但入口服务可从鉴权或上下文解析时，可以补齐。 |
| tenant_id | OFA_PASS_TENANT_ID | 全链路 | 租户标识。用于表达当前请求所属的租户隔离维度。 | 上游提供时直接透传；上游未提供但入口服务可以确定租户时，可以补齐。 |
| app_id | OFA_PASS_APP_ID | 全链路 | 应用标识。用于标识发起请求的应用、业务系统或接入方。 | 上游提供时直接透传；上游未提供但入口服务可以确定来源应用时，可以补齐。 |
| locale | OFA_PASS_LOCALE | 全链路 | 当前请求已决策的 effective locale。用于保持服务间语言和格式化语义一致。 | 入口服务完成 locale 解析、归一化和 fallback 后可以补齐；上游已提供时直接透传。具体 locale 语义与决策优先级由 `i18n` 规范定义。 |

#### ID 格式
- `trace_id` 必须使用 `32位小写十六进制` 格式，例如 `8f14e45fceea167a5a36dedd4bea2543`
- `trace_id` 必须由 `16` 字节加密安全随机数编码而成，不带 `trace_` 前缀，不嵌入时间、机器标识或业务含义
- `request_id` 必须使用 `req_<YYYYMMDD_HHMMSS>_<suffix>` 格式，例如 `req_20260420_153045_7k2m9q4x8c1v6b3n`
- `request_id` 中的时间前缀推荐使用 `UTC` 时间；如果实现选择非 `UTC`，则必须在同一条链路内保持统一
- `request_id` 中的 `<suffix>` 必须由加密安全随机数生成，推荐使用 `10` 字节随机数编码为 `16` 位小写 base32 字符串
- 如果语言实现暂时没有统一的 base32 方案，`request_id` 的 `<suffix>` 也可以退化为 `20` 位小写十六进制字符串
- `request_id` 的 `<suffix>` 不得依赖中心发号器、机器 IP、进程号、线程号或普通伪随机数生成器
- 生成结果必须仅包含小写字母、数字与下划线，便于在不同协议、日志系统与网关中稳定传递

#### 生成责任
- 链路 ID 的标准生成方是请求发起方（client），而不是请求接收方（server）
- 发起任意一次对外请求前，client 必须生成新的 `OFA_DIRECT_REQUEST_ID`
- 发起请求前如果已经持有 `OFA_PASS_TRACE_ID`，必须继续沿用；如果没有，则视为链路起点并生成新的 `OFA_PASS_TRACE_ID`
- server 端不应把“收到请求后再补生成 ID”作为标准机制；标准链路应依赖 client 在发送前完成生成
- 如果为了兼容存量调用方而在 server 端做缺失兜底，该行为仅属于兼容措施，不改变本规范的责任边界

#### 传播规则
- 所有对外请求必须携带 `OFA_PASS_TRACE_ID` 与 `OFA_DIRECT_REQUEST_ID`
- `OFA_PASS_TRACE_ID`、`OFA_PASS_OPERATOR`、`OFA_PASS_TENANT_ID`、`OFA_PASS_APP_ID`、`OFA_PASS_LOCALE` 视为全链路透传字段
- 请求发起方必须在发送前完成 `OFA_PASS_TRACE_ID` 与 `OFA_DIRECT_REQUEST_ID` 的生成或补齐
- 服务在发起下游调用时，必须沿用当前 `OFA_PASS_TRACE_ID`，并在发送前为该次下游调用生成新的 `OFA_DIRECT_REQUEST_ID`
- 如果当前上下文启用了超时控制，且目标下游支持 OFA 超时传播模型，则请求发起方在发送前必须同时写入 `OFA_DIRECT_REMAINING_TIMEOUT_MS`
- 如果目标下游不支持 OFA 超时传播模型，则超时应按 `resilience` 规范在本地基于 authoritative deadline 映射到该下游调用自己的 timeout 参数
- `OFA_PASS_OPERATOR`、`OFA_PASS_TENANT_ID`、`OFA_PASS_APP_ID`、`OFA_PASS_LOCALE` 在有值时不得被下游服务随意丢弃、清空或改写
- 所有下游调用必须透传当前上下文中已有的 `OFA_PASS_*` 字段，并携带该次调用自己的 `OFA_DIRECT_REQUEST_ID`
- `OFA_DIRECT_REMAINING_TIMEOUT_MS` 的具体计算、裁剪与重试约束由 `resilience` 规范定义
- 跨协议调用、消息投递、异步任务调度等场景同样适用上述传播规则

#### 前缀约定
- `OFA_PASS_` 表示全链路透传 header
- `OFA_DIRECT_` 表示单跳直传 header
- `OFA_` 且不带 `PASS` / `DIRECT` 前缀的名字，表示由对应领域 spec 单独定义的标准 context value；它们不是标准链路 header 名
- 不带前缀的名字仅用于表达语义字段名，或供各语言实现作为内部 context key / 常量名参考；它们不是标准链路 header 名
- 本规范统一的是链路 header 名；标准 context value 的注册由对应领域 spec 单独定义
- `OFA_DIRECT_REQUEST_ID` 与 `OFA_DIRECT_REMAINING_TIMEOUT_MS` 是本规范中定义的通用 `OFA_DIRECT_*` 字段
- 除上述字段外，其他 `OFA_DIRECT_*` 字段由服务按需自行约定
- 业务自定义 `OFA_PASS_*` 或 `OFA_DIRECT_*` 扩展字段时，不得使用与标准语义字段等价的名称，例如 `TRACE_ID`、`REQUEST_ID`、`REMAINING_TIMEOUT_MS`、`OPERATOR`、`TENANT_ID`、`APP_ID`、`LOCALE`。
