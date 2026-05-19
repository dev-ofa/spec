## resilience

### 状态
Draft

### 目标
- 本规范定义跨服务调用中的超时预算、传播规则与重试约束。
- 目标是避免无界等待、超时膨胀与失败放大，并让整条链路在有限预算内失败得更早、更可控。

### 适用范围
- 服务间请求-响应式调用及其下游重试行为。
- 需要在链路中传播剩余超时并统一处理 quota 的调用场景。

### 非目标
- 不覆盖长连接、流式传输与持续订阅场景的细节，相关规则需另行约定。

### 术语

#### connect timeout
- 建连超时，指 TCP/TLS/HTTP2 连接建立阶段允许消耗的最长时间。

#### timeout quota
- 一次请求在整条链路上可消耗的总超时预算，单位为毫秒。

#### remaining timeout
- 某一跳在当前时刻尚可继续消耗、并可传播给下一跳的剩余超时时间。

#### authoritative deadline
- 当前服务在本进程内认定的绝对过期时间点；它由入口初始化或由上游传播而来，用于本地计算 remaining timeout。

#### retry
- 在一次请求失败后，由调用方重新发起同一语义请求的行为。

#### per-try timeout
- 某一次重试尝试单独可使用的超时时间；其上限必须受当前 remaining timeout 约束。

### 超时预算

#### 核心原则
- 链路总超时必须由 timeout quota 控制，而不是由每一跳各自独立设置完整 request timeout。
- 链路中的 client 不得放大 timeout quota；下游请求的总等待时间必须小于等于当前 remaining timeout。
- 进程内的权威超时控制应由 authoritative deadline 驱动，而跨服务传播统一使用 remaining timeout。
- 任意调用方都可以使用统一的 quota header 发起请求；接收方必须在收到请求时基于该 quota 重建本地 authoritative deadline。
- 如果调用方未传 quota，则接收方应以本接口定义的默认 timeout quota 初始化 authoritative deadline。

#### connect timeout
- client 可以单独定义 connect timeout。
- connect timeout 推荐默认值为 `3s`。
- 低延迟内网或已知网络环境稳定的场景可以收紧 connect timeout，但不应大于当前 remaining timeout。
- connect timeout 仅约束建连阶段，不得替代整条链路的 timeout quota。

#### 进程内表示
- server 在收到请求后，必须在当前进程内保存本次请求的开始处理时间与 authoritative deadline。
- server 在进程内传播时，应优先使用绝对 deadline 表达；remaining timeout 仅作为基于 deadline 的派生值。
- 当 remaining timeout 已小于本地最小可执行阈值时，server 应尽早失败，而不是继续调用下游。

### 传播规则

#### 标准链路 Header

| 语义字段 | 标准 header | 作用范围 | 说明 |
| --- | --- | --- | --- |
| remaining_timeout_ms | OFA_DIRECT_REMAINING_TIMEOUT_MS | 单跳 | 当前服务在发送请求瞬间计算出的 remaining timeout，单位毫秒。 |

#### 统一传播模型
- 所有调用方应采用统一的 gRPC 风格传播模型：本地保存 absolute deadline，跨服务传播 remaining timeout。
- 对外发起请求时，如果当前上下文存在 authoritative deadline，则必须先计算当前 remaining timeout，再注入 `OFA_DIRECT_REMAINING_TIMEOUT_MS`。
- `OFA_DIRECT_REMAINING_TIMEOUT_MS` 的值必须是请求发送瞬间计算得到的 remaining timeout，而不是初始 quota。
- server 收到 `OFA_DIRECT_REMAINING_TIMEOUT_MS` 后，必须以“收到请求的当前时刻”为基准重建本地 authoritative deadline。
- server 发起下游调用时，必须基于当前 authoritative deadline 重新计算 remaining timeout，而不是直接复用入站 header 的原值。
- 任意一跳都不得把入站 quota 重置为自身默认超时。
- 如果入站请求未携带 quota，则接收方可以按本接口定义的默认 timeout quota 初始化 authoritative deadline。
- 如果入站 quota 大于本接口允许的最大 quota，server 可以按本接口上限对其进行裁剪。
- server 对入站 quota 的裁剪只允许收紧，不允许放大。

#### 计算规则
- 设当前服务在 `t0` 时刻收到请求，入站 quota 为 `Q`。
- 如果本接口定义的最大 quota 为 `Qmax`，则当前服务应先计算 `Qeffective = min(Q, Qmax)`；若未配置 `Qmax`，则 `Qeffective = Q`。
- 当前服务必须立即建立 `authoritative_deadline = t0 + Qeffective`。
- 当前时刻为 `t1` 时，`remaining_timeout = max(authoritative_deadline - t1, 0)`。
- 发起下游调用前，必须基于当前时刻重新计算 `remaining_timeout`；如果结果小于等于 `0`，则不得继续调用下游。
- 如果实现支持 per-try timeout，则单次尝试超时必须小于等于当前 `remaining_timeout`。

#### RTT 与时钟漂移
- 跨服务传播选择传递 remaining timeout，而不是跨服务直接传递绝对 deadline 时间点。
- 该设计主要用于规避不同主机之间的时钟漂移问题，不依赖调用方与被调用方的系统时钟严格一致。
- 该设计不能精确扣除 header 在网络上传输过程中的耗时，因此会引入一定 RTT 误差。
- 本规范接受该 RTT 误差，作为换取跨主机时钟无关性与实现稳定性的工程取舍。
- timeout quota 较小的接口应预留必要的安全余量，不应把预算设计得过于贴近理论极限。

### 重试

#### 允许条件
- 只有在下游调用被明确定义为幂等，或可以证明请求尚未被下游处理时，才允许重试。
- 以下场景通常可以视为可重试：
  - connect timeout 或连接建立失败
  - 请求写出前连接已断开
  - 明确声明为幂等的读操作，例如 `GET`、`HEAD`
  - 显式支持幂等键的写操作
- 以下场景默认不可重试：
  - 未声明幂等的 `POST`、`PATCH`、`DELETE`
  - 已经无法确认下游是否完成处理的写请求
  - 业务语义可能产生重复副作用的操作

#### 次数与节奏
- 重试次数默认不应超过 `2` 次，即总尝试次数不应超过 `3` 次。
- 重试必须使用退避策略，并附加 jitter，避免失败放大与惊群。
- 推荐使用 capped exponential backoff with jitter。
- 所有重试必须共享同一个 timeout quota，不得在每次重试时重新获得完整超时。
- 当 remaining timeout 已不足以支撑下一次尝试时，必须立即停止重试。

#### 超时与重试的关系
- connect timeout、首包等待、响应读取与重试退避时间都必须计入同一个 timeout quota。
- 如果第一次尝试已消耗掉大部分 quota，后续重试只允许使用剩余 timeout。
- 不得通过“每次重试重新设置一个完整 request timeout”的方式规避 timeout quota。
- server timeout 或下游过载不应被重试策略长期掩盖；应优先修复慢请求与容量问题。

### 禁止事项
- 禁止在无 timeout quota 的情况下发起无界等待的请求。
- 禁止在链路中途放大、重置或忽略上游已传入的 timeout quota。
- 禁止对未声明幂等的写请求默认开启自动重试。
- 禁止使用固定间隔或无 jitter 的重试策略。
- 禁止依赖重试掩盖长期存在的性能问题、容量不足或错误配置。

### 示例

#### 示例一：quota 传播
- 调用方向服务 A 发起请求，并携带 `OFA_DIRECT_REMAINING_TIMEOUT_MS=5000`。
- 服务 A 在收到请求的时刻，根据入站 quota 与本接口最大 quota 计算 `Qeffective`，并立即初始化 authoritative deadline。
- A 在本地处理 `800ms` 后调用服务 B，此时注入 `OFA_DIRECT_REMAINING_TIMEOUT_MS=4200`。
- B 在收到请求时立即重建自己的 authoritative deadline；B 再处理 `700ms` 后调用服务 C，此时注入 `OFA_DIRECT_REMAINING_TIMEOUT_MS=3500`。
- 如果 A 之前的网络传输已经消耗了部分时间，该部分损耗不会被精确扣除；这是统一传播模型接受的 RTT 误差。
- 如果 B 在准备调用 C 时发现 remaining timeout 已小于等于 `0`，则应直接返回超时，而不是继续调用 C。

#### 示例二：重试
- 某次 `GET` 调用的初始 quota 为 `3000ms`，第一次尝试在 `300ms` 时发生 connect timeout。
- client 经过一次带 jitter 的短暂退避后，可以在剩余 quota 内发起第二次尝试。
- 如果第二次尝试结束后仅剩 `150ms`，且不足以完成下一次调用，则不得继续第三次尝试。
