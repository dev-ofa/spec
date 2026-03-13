## logging

### 状态
Draft

### 请求生命周期日志

#### 必须
- 每个请求必须记录一条开始日志与一条结束日志
- 日志必须包含 trace_id 与 request_id

#### 推荐字段
- method：请求方法或 RPC 名称
- path：HTTP 路径或服务名
- status_code：协议层状态码
- code：业务码
- duration_ms：请求耗时
- error：错误摘要

### 级别建议
- 正常结束使用 INFO
- 业务失败使用 WARN
- 系统错误使用 ERROR
