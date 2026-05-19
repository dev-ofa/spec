## config

### 状态
Draft

### 目标
- 定义运行时配置的来源、优先级、命名、校验、安全与生效行为。
- 保证不同服务在配置覆盖、加载顺序与敏感信息处理上保持一致，避免实现走偏。

### 适用范围
- 服务或应用在启动与运行期读取的配置。
- 文件配置、环境变量、本地覆盖文件与启动参数等配置来源及其组合关系。

### 非目标
- 不限制具体配置库、序列化框架或内部实现方式。
- 不覆盖业务领域自身的配置语义，只约束通用配置管理行为。

### 配置来源与优先级

#### 必须
- 配置必须来自默认配置、环境变量、本地覆盖文件或启动参数之一
  示例：`configs/config.yaml` + `APP.HTTP.PORT=8080` + `config.local.yaml` + `--http.port=9090`
- 加载顺序固定为：默认配置 → 环境变量 → 本地覆盖文件 → 命令行参数
  示例：`APP.HTTP.PORT=8080` 且 `--http.port=9090` 时，最终端口为 `9090`
- 同名配置必须遵循后者覆盖前者的规则
  示例：`configs/config.yaml` 中 `db.uri` 被 `APP.DB.URI` 覆盖
- 支持按环境读取差异化配置文件
  示例：`ENV=dev` 时读取 `config.dev.yaml`，不存在则忽略

#### 文件读取约定
- 默认基础配置文件名应为 `config.yaml`
  示例：服务启动时先读取 `configs/config.yaml`
- 未显式指定配置文件路径时，必须先加载 `config.yaml` 作为基线，再按顺序叠加其他来源
  示例：`config.yaml` -> `config.dev.yaml` -> `config.local.yaml`
- 当存在 `ENV=<name>` 时，约定读取 `config.<name>.yaml` 作为环境差异配置；文件不存在时可忽略
  示例：`ENV=staging` 时尝试读取 `configs/config.staging.yaml`
- 即使未设置 `ENV`，只要存在 `config.local.yaml`，也必须自动读取并叠加到 `config.yaml` 之上
  示例：本地开发默认按 `config.yaml` -> `config.local.yaml` 计算最终配置
- `config.local.yaml` 的定位是本地覆盖文件，不得被当作完整独立配置替代 `config.yaml`
  示例：`config.local.yaml` 中只写 `llm.providers.volcengine.api_key` 仍应与 `config.yaml` 合并后得到完整配置

#### Merge 规则
- 多个文件按加载顺序做深度 merge，后加载文件覆盖先加载文件的同名路径
  示例：`config.yaml` 中 `llm.providers.deepseek.base_url` 被 `config.local.yaml` 中同路径值覆盖
- 对象（map/dict）类型必须递归 merge，而不是整段替换
  示例：基础配置已有 `llm.providers.volcengine.base_url`，本地文件只写 `api_key` 时，最终应同时保留两个字段
- 标量、数组与非对象值采用整值覆盖，不做元素级 merge
  示例：`cors.allow_origins` 在覆盖文件中出现后，应整体替换基础配置中的数组
- 覆盖文件中未出现的字段必须继承前一层结果，不得因“未声明”而丢失
  示例：`config.local.yaml` 未声明 `server.port` 时，最终仍使用 `config.yaml` 的 `server.port`
- 若实现支持显式传入配置文件路径，应在文档中明确该路径是“完整配置文件”还是“覆盖文件”；不得保留歧义
  示例：CLI `--config /path/to/config.yaml` 应明确说明是否还会继续自动叠加 `config.local.yaml`


### 命名与结构

#### 必须
- 配置项命名必须使用统一前缀与分组规则
  示例：`APP.HTTP.PORT`、`APP.DB.URI`
- 层级配置必须使用一致的分隔符表达
  示例：文件配置使用 `.` 表示层级，`http.port=8080`
  示例：环境变量使用 `.` 表示层级，`APP.LOGGING.LEVEL=INFO`
- 配置项必须归类到稳定的领域分组
  示例：数据库配置统一放在 `db` 组

#### 推荐
- 领域分组建议包含 app、http、db、auth、ai、logging、tracing、feature
  示例：`feature` 中定义 `feature.resume_parser=true`

### 安全与敏感信息

#### 必须
- 密钥、密码、Token 必须仅从环境变量或安全存储读取
  示例：`APP.DB.PASSWORD` 从环境变量读取
- 禁止在日志中输出敏感配置明文
  示例：日志仅记录 `db.uri` 的主机名，不记录密码
- 示例配置必须使用占位符，不得包含真实凭据
  示例：`APP.DB.PASSWORD=******`

### 校验与默认值

#### 必须
- 启动时必须进行完整性与类型校验
  示例：`APP.HTTP.PORT` 必须为整数
- 缺失关键配置必须阻止服务启动并返回明确错误
  示例：缺少 `db.uri` 时输出 “missing db.uri” 并退出

#### 推荐
- 为可选配置提供明确默认值
  示例：`logging.level` 默认 `INFO`
- 约束数值范围与枚举取值
  示例：`http.timeout_ms` 范围 `1000-30000`

### 运行时行为

#### 必须
- 文档必须声明配置是否支持热更新
  示例：`logging.level` 支持热更新
- 配置变更的生效范围与时机必须明确
  示例：`db.pool.max` 仅在进程重启后生效

#### 推荐
- 需要重启的配置项应标记为重启生效
  示例：`ai.model` 标注为“重启生效”

### 可观测性

#### 必须
- 启动时必须记录配置加载来源与摘要
  示例：输出 “loaded from env, local, flags”
- 摘要必须脱敏处理
  示例：`db.uri` 显示为 `mongodb://user:***@host:27017`

#### 推荐
- 支持配置版本或哈希用于排查差异
  示例：`config_hash=8f3c1b...`
