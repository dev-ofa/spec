# authentication

### 状态
Draft

### 目标
- 统一 HTTP 场景下认证凭证的来源、适用边界、冲突处理与最小安全要求。
- 降低前后端、网关、BFF、资源接口与异步入口之间的认证语义分歧，避免同一套会话在不同服务中被以不同方式解释。

### 适用范围
- 面向浏览器、服务端、移动端或脚本客户端的 HTTP/HTTPS 请求认证。
- 访问受保护业务 API、资源读取接口、下载链接与浏览器原生资源请求的认证规则。
- Bearer token、浏览器会话 cookie、受限 query token 等凭证来源及其安全边界。

### 非目标
- 不定义 OAuth 2.0 / OIDC 的完整授权流程、授权码交换、刷新令牌轮换或单点登录协议细节。
- 不绑定具体身份提供方、网关产品、BFF 部署方式、session 存储实现或 SDK。
- 不定义业务权限模型、角色模型、scope 设计或租户隔离策略。

### 术语

#### Bearer Token
- `Bearer Token` 指通过 `Authorization: Bearer <token>` 传递的访问凭证。
- Bearer token 的安全语义是“持有者即可使用”，因此其泄露风险高于普通业务参数。

#### Session Cookie
- `Session Cookie` 指浏览器自动携带、由服务端解释为登录态或会话标识的 cookie。
- Session cookie 是浏览器会话机制，不等同于 Bearer token 标准传输方式。

#### Credential Source
- `Credential Source` 指服务端用于恢复调用者身份的单一凭证来源，例如 `authorization_header`、`session_cookie`、`query_token`。
- 认证处理 **必须** 能明确判断本次请求实际命中了哪个 credential source。

### 核心规则

#### 1. 默认认证来源
- 受保护 HTTP API 的默认认证来源 **必须** 是 `Authorization: Bearer <token>`。
- 服务端对 Bearer token 的处理 **必须** 与业务参数解析分离， **不得** 把 token 视为普通 query 参数、普通 JSON 字段或普通 header 字段。
- 新增受保护 API 如果未显式声明其他认证方式，调用方 **必须** 使用 `Authorization` header。

#### 2. 认证来源 **必须** 按路由声明
- 每个受保护入口 **必须** 明确声明允许的 credential source 集合。
- 未被路由契约显式声明的 credential source **不得** 被该入口隐式接受。
- 服务端 **不得** 对所有路由启用“从多个来源自动兜底恢复身份”的全局宽松模式。

#### 3. 多来源冲突处理
- 调用方 **应当** 在单个请求中只发送一种认证凭证。
- 如果请求同时携带多个可识别的 credential source，服务端 **必须** 拒绝该请求，除非该路由契约显式定义了稳定优先级。
- 如果路由契约显式定义了优先级，服务端 **应当** 在审计日志、调试日志或等效诊断信息中记录实际命中的 credential source，但 **不得** 记录原始凭证值。

#### 4. Query Token 只允许作受限兼容
- `query_token` 只可用于无法稳定注入 `Authorization` header 的兼容场景，例如浏览器原生资源请求、下载链接或媒体标签加载。
- `query_token` **必须** 仅用于显式白名单的只读接口；新增业务 API、写操作接口与通用 RPC 风格接口 **不得** 接受 `query_token`。
- 接受 `query_token` 的接口 **必须** 明确限制为 `GET`、`HEAD` 或其他只读语义等价的方法。
- 对可编程客户端，接受 `query_token` 的调用方 **应当** 发送 `Cache-Control: no-store`；浏览器原生资源请求等无法稳定设置请求头的场景，可不要求调用方满足此项。
- 接受 `query_token` 的服务端成功响应 **应当** 返回 `Cache-Control: private` 或更严格缓存策略。
- 接受 `query_token` 的系统 **必须** 对访问日志、埋点、错误上报与跳转链路中的 URL 做脱敏，避免明文 token 外泄。

#### 5. Cookie 用于浏览器会话，不作为通用 Bearer 来源
- 浏览器场景 **可以** 使用 session cookie 恢复用户会话。
- Session cookie 适用于浏览器到同站点服务的会话认证， **不应** 被泛化为所有 HTTP 客户端的通用 Bearer token 替代来源。
- 如果某路由支持 session cookie，该能力 **必须** 在路由契约中显式声明。
- 服务端 **应当** 优先在 BFF、同源 Web 宿主或浏览器会话入口使用 session cookie，而不是要求前端在原生资源请求中注入 Bearer token。

#### 6. Cookie 安全要求
- 用于认证的 session cookie **必须** 设置 `HttpOnly` 与 `Secure`。
- 用于认证的 session cookie **必须** 设置明确的 `Path`，并具备明确的生存期策略； **不得** 依赖未声明的浏览器默认行为。
- 如果场景允许，session cookie **应当** 使用 `SameSite=Lax` 或更严格策略；需要跨站携带时，设计方 **必须** 额外评估 CSRF 与第三方 cookie 限制。
- 认证 cookie **应当** 使用宿主级约束，避免被更宽泛域名或子域覆盖。

#### 7. Cookie 场景的 CSRF 约束
- 任何依赖 session cookie 完成认证的状态变更接口 **必须** 具备 CSRF 防护。
- CSRF 防护 **可以** 通过一次性 CSRF token、`Origin` 校验、`Referer` 校验或等效机制实现，但 **不得** 完全依赖“调用方是自家前端”的假设。
- 只读接口即使使用 cookie，也 **应当** 评估是否会暴露敏感资源给跨站请求。

#### 8. 资源读取接口的特殊要求
- 面向浏览器原生资源请求的受保护资源接口 **应当** 优先使用同站点 session cookie 或短时效签名 URL。
- 如果资源读取接口出于兼容目的接受 `query_token`，该能力 **必须** 单独声明， **不得** 自动扩展到同服务的其他业务接口。
- 资源标识符、下载 URL 与临时访问地址 **不得** 持久携带长期 access token、refresh token、cookie 或其他长期凭证；相关约束同时遵循 `resource` 规范。

#### 9. 凭证传输与存储安全
- 所有认证凭证 **必须** 仅通过 HTTPS 传输。
- 系统 **不得** 在日志、trace、metrics、埋点、错误上报或审计记录中输出原始 access token、refresh token、session cookie、query token 或其可直接复用的完整值。
- 如果为了排障需要记录凭证相关信息，系统 **应当** 只记录 credential source、签发方、到期时间、摘要前缀或脱敏后的指纹。

#### 10. 生命周期与最小暴露面
- Access token **应当** 短时效，并与 refresh token、session id 使用不同的存储与暴露策略。
- Refresh token **不得** 出现在浏览器可复制 URL、资源标识符或前端可见日志中。
- 认证设计 **应当** 让浏览器仅持有完成当前交互所需的最小凭证；长期凭证或可刷新凭证 **应当** 优先保留在服务端。

### 设计建议

以下内容为推荐项，不构成强制规范：

- 浏览器应用优先使用同站点 session cookie 维持登录态，由服务端、BFF 或网关管理下游 access token。
- 资源访问、媒体加载、下载链接等浏览器原生请求优先使用 session cookie 或短时效签名 URL，而不是长期 query token。
- 需要同时支持浏览器与非浏览器客户端时，建议把 `Authorization` header 与 session cookie 视为两种不同接入模型，并分别声明适用路由。

### 与其他规范的关系
- API 入口的资源建模、资源表示、HTTP 方法语义与统一响应结构遵循 `api` 规范。
- 认证失败、鉴权失败与下游认证错误的错误分类遵循 `error` 规范。
- 请求生命周期日志中的最小记录字段与级别建议遵循 `logging` 规范；凭证脱敏与审计日志要求以本规范自身约束为准。
- 链路透传字段中的 `operator`、`tenant_id`、`app_id` 等语义遵循 `tracing` 规范；认证模块负责恢复身份，不负责重新定义这些字段的透传规则。
- 二进制资源标识符与临时访问地址的凭证约束遵循 `resource` 规范。
