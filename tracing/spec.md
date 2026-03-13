## tracing

### 状态
Draft

### 透传字段

#### 规范字段名
- OFA_TRACE_ID
- OFA_REQUEST_ID
- OFA_OPERATOR
- OFA_TENANT_ID
- OFA_APP_ID

#### 传播规则
- 所有对外请求必须携带 OFA_TRACE_ID 与 OFA_REQUEST_ID
- 上游未提供时，服务必须生成并补齐
- 所有下游调用必须透传上述字段

#### 前缀约定
- 透传存储使用 OFA_PASS_ 前缀
- 直传存储使用 OFA_DIRECT_ 前缀
- 前缀仅用于上下文或内部存储，不改变对外字段名
