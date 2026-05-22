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
- 当接口支持分页查询时，请求字段名应统一对齐 `core-go` 当前实现，使用 `page_size`、`page_num`、`page_token`。
- `page_size` 表示每页数量，`page_num` 表示页码，`page_token` 表示基于游标翻页时使用的续页标识。
- 本规范不强制页码分页与游标分页二选一；若接口支持其中某一种，可只使用对应字段，但字段名不得另起别名。
- 当接口返回分页结果时，结果字段名应统一使用 `rows` 与 `total_count`。
