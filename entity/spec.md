## entity

### 状态
Draft

### 目标
entity 规范用于定义持久化对象的落地规范，包括但不限于审计、软删、环境隔离与环境持久化。

### 适用范围
- 需要持久化保存的实体、记录或文档模型。
- 需要统一处理审计字段、软删语义与隔离字段的存储对象。

### 非目标
- 不定义具体 ORM、DDL、索引或存储引擎实现。
- 不规定业务领域专有字段，只约束通用落地基线。

### 字段规范

| 分组 | 字段 | 说明 | 规则 |
| --- | --- | --- | --- |
| 主键 | id | 主键标识 | 必须 |
| 创建审计 | created_at, created_by | 创建时间与创建者 | 必须成对出现，创建时写入 |
| 更新审计 | updated_at, updated_by | 更新时间与更新者 | 必须成对出现，更新时写入 |
| 删除审计 | deleted_at, deleted_by | 删除时间与删除者 | 必须成对出现，删除时写入 |
| 租户隔离 | tenant_id, app_id | 租户与应用隔离 | 必须成对出现，按隔离策略写入 |

### 软删语义
- deleted_at 为空表示有效
- deleted_at 非空表示逻辑删除

### 查询与分页命名
- 当 CRUD 查询包含时间范围条件时，应统一使用 `<field>_before` 与 `<field>_after` 作为查询字段名，例如 `created_at_before`、`created_at_after`。
- 对本规范中的常见审计时间字段，查询命名应对应为 `created_at_before` / `created_at_after`、`updated_at_before` / `updated_at_after`、`deleted_at_before` / `deleted_at_after`。
- 为避免连续区间筛选在边界值上出现 overlap，时间范围应默认按左闭右开语义解释：`*_after` 表示“大于等于该时间点之后”的下界条件，`*_before` 表示“小于该时间点之前”的上界条件。
- 当同时提供 `*_after` 与 `*_before` 时，区间语义等价于 `[after, before)`；同一接口内不得混用其他命名方式。
- 本规范只约束通用字段命名，不要求所有实体或接口都必须提供时间范围查询能力。
- 普通页码分页适用于后台列表、订单列表、可跳页或需要展示总数的 CRUD 查询；请求字段应使用 `page_size` 与 `page_num`，响应字段应使用 `rows` 与 `total_count`。
- 普通页码分页不得返回 `next_page_num` 或 `next_page_token`；客户端应根据 `page_num`、`page_size`、`rows` 与 `total_count` 判断是否还有下一页。
- Feed/Cursor 分页适用于时间线、消息流、推荐流、无限滚动等不要求跳页且需要稳定续页的场景；请求字段应使用 `page_size` 与 `page_token`，响应字段应使用 `rows` 与 `next_page_token`。
- 首次 Feed/Cursor 查询必须允许只传 `page_size`；后续查询必须使用服务端上一次返回的 `next_page_token`，客户端不得自行拼接或伪造 token。
- `page_token` 不得只是 `page_size + page_num` 的包装；这种做法仍然是页码分页，不能解决深分页性能、列表漂移和稳定续页问题。
- Feed/Cursor 分页必须基于稳定排序锚点生成 token，例如 `created_at + id`、`seq`、`score + id`；排序字段必须能形成唯一且稳定的顺序。
- Feed/Cursor 排序字段的数据库比较语义必须与接口声明的顺序语义一致；如果字段以字符串存储，必须确认其字典序是否等同于期望的时间序、数值序或业务排序。
- 当主键 ID 的对外字符串表达不具备稳定排序语义时，不应直接把该字段作为 Feed/Cursor 锚点；应使用数值型存储字段、固定宽度排序键、ULID、UUIDv7 或业务定义的 `feed_cursor` 等稳定字段。
- 支持 Feed/Cursor 分页的接口必须显式声明 cursor 定义，包括排序字段、方向、唯一 tie-breaker、过滤条件是否参与 token 校验，以及 token 版本。
- 同一个接口不得同时混用普通页码分页和 Feed/Cursor 分页；如果确实需要两种查询能力，应拆分接口或显式区分查询模式。
