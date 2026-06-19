## config

### 状态
Draft

### 目标
- 定义运行时配置的来源、优先级、命名、校验、安全与生效行为。
- 保证不同服务在配置覆盖、优先级裁决与敏感信息处理上保持一致，避免实现走偏。

### 适用范围
- 服务或应用在启动与运行期读取的配置。
- 默认基础配置文件、环境差异配置文件、本地覆盖文件、环境变量等标准配置来源及其组合关系。

### 非目标
- 不限制具体配置库、序列化框架或内部实现方式。
- 不覆盖业务领域自身的配置语义，只约束通用配置管理行为。

### 配置来源与优先级

#### 必须
- 规范只定义不同标准配置来源发生同路径冲突时的最终覆盖优先级，不强制实现的实际读取顺序
  示例：实现可以先读取环境变量再读取文件，但最终结果必须符合本节优先级
- 标准配置来源的覆盖优先级从低到高为：默认基础配置文件 → 环境差异配置文件 → 本地覆盖文件 → 环境变量
  示例：`config.yaml`、`config.dev.yaml`、`config.local.yaml` 与 `APP__HTTP__PORT` 同时声明 `http.port` 时，最终使用 `APP__HTTP__PORT`
- 同一路径配置必须由优先级更高的来源覆盖优先级更低的来源
  示例：`configs/config.yaml` 中 `db.uri` 被 `APP__DB__URI` 覆盖
- 支持按环境变量中的部署环境选择器引入差异化配置文件
  示例：`APP__ENV=dev` 时读取 `config.dev.yaml`，不存在则忽略
- 启动参数不属于标准配置来源；实现可以支持启动参数，但不得要求业务依赖启动参数完成标准配置覆盖
  示例：实现可支持 `--http.port=9090` 作为调试能力，但标准部署不应依赖该参数
- 若实现支持启动参数，必须在实现文档中明确其覆盖优先级、安全限制与可观测行为
  示例：实现文档明确启动参数是否高于环境变量，以及是否禁止传入敏感配置

#### 文件读取约定
- 默认基础配置文件名应为 `config.yaml`
  示例：以 `configs/config.yaml` 作为默认基础配置来源
- 未显式指定配置文件路径时，必须以 `config.yaml` 作为基础配置来源，并按本规范优先级计算最终配置
  示例：文件来源内部按 `config.yaml < config.dev.yaml < config.local.yaml` 计算覆盖关系
- 部署环境选择器必须仅从环境变量读取，用于决定是否加载 `config.<env>.yaml`；文件不存在时可忽略
  示例：`APP__ENV=staging` 时，`configs/config.staging.yaml` 作为环境差异配置来源
- 部署环境选择器的环境变量名由 `EnvPrefix + EnvSeparator + DeployEnvKey` 组成；默认 `EnvPrefix=APP`、`EnvSeparator=__`、`DeployEnvKey=ENV`，因此默认读取 `APP__ENV`
  示例：`APP__ENV=staging` 作为默认部署环境选择器
- 部署环境选择器必须同时参与最终配置覆盖，其最终规范路径由 `lower(EnvPrefix) + "." + lower(DeployEnvKey)` 派生
  示例：`APP__ENV=staging` 对应最终配置中的 `app.env=staging`
- 若实现允许自定义 `EnvPrefix`、`EnvSeparator` 或 `DeployEnvKey`，必须明确这些选项会同时影响部署环境选择器的环境变量名与最终配置路径
  示例：`EnvPrefix=SERVICE`、`DeployEnvKey=PROFILE` 时，`SERVICE__PROFILE=dev` 对应最终配置路径 `service.profile`
- 即使未设置部署环境选择器，只要存在 `config.local.yaml`，也必须作为本地覆盖来源参与最终配置计算
  示例：本地开发默认按 `config.yaml < config.local.yaml` 计算文件覆盖关系
- `config.local.yaml` 的定位是本地覆盖文件，不得被当作完整独立配置替代 `config.yaml`
  示例：`config.local.yaml` 中只写 `llm.providers.volcengine.api_key` 仍应与 `config.yaml` 合并后得到完整配置
- `config.local.yaml` 必须作为本地私有文件处理，不得提交到代码仓库；仓库必须通过 `.gitignore` 或等效机制排除该文件
  示例：`.gitignore` 中包含 `config.local.yaml`

#### Merge 规则
- 多个来源按覆盖优先级做深度 merge，优先级更高的来源覆盖优先级更低来源的同名路径
  示例：`config.yaml` 中 `llm.providers.deepseek.base_url` 被 `config.local.yaml` 中同路径值覆盖
- 对象（map/dict）类型必须递归 merge，而不是整段替换
  示例：基础配置已有 `llm.providers.volcengine.base_url`，本地文件只写 `api_key` 时，最终应同时保留两个字段
- 标量、数组与非对象值采用整值覆盖，不做元素级 merge
  示例：`cors.allow_origins` 在覆盖文件中出现后，应整体替换基础配置中的数组
- 较高优先级来源中未出现的字段必须继承较低优先级结果，不得因“未声明”而丢失
  示例：`config.local.yaml` 未声明 `server.port` 时，最终仍使用 `config.yaml` 的 `server.port`
- 若实现支持显式传入配置文件路径，应在文档中明确该能力属于实现扩展，并明确该路径是“完整配置文件”还是“覆盖文件”；不得保留歧义
  示例：实现文档明确自定义配置路径是否仍会与 `config.local.yaml` 合并计算最终配置


### 命名与结构

#### 必须
- 配置项必须具有稳定的规范路径，规范路径使用小写单词与 `.` 表示层级
  示例：`http.port`、`db.uri`、`logging.level`
- 环境变量必须使用统一应用前缀，并使用 `__` 表示层级分隔
  示例：`APP__HTTP__PORT=8080` 对应规范路径 `http.port`
- 部署环境选择器必须遵循相同命名规则，其最终配置路径由环境变量映射规则派生
  示例：`APP__ENV=dev` 对应规范路径 `app.env`；`SERVICE__PROFILE=dev` 对应规范路径 `service.profile`
- 环境变量名必须使用大写 ASCII 字母、数字与下划线，不得使用 `.` 作为环境变量层级分隔符
  示例：使用 `APP__LOGGING__LEVEL=INFO`，不使用 `APP.LOGGING.LEVEL=INFO`
- 实现必须将环境变量名显式映射到规范路径，不得依赖配置库的默认环境变量解析行为
  示例：`APP__DB__URI` 必须映射到 `db.uri`
- 配置项必须归类到稳定的领域分组
  示例：数据库配置统一放在 `db` 组

#### 推荐
- 领域分组建议包含 app、http、db、auth、ai、logging、tracing、feature
  示例：`feature` 中定义 `feature.resume_parser=true`

### 安全与敏感信息

#### 必须
- 生产、测试、预发等共享环境中的密钥、密码、Token 必须仅从环境变量或安全存储读取，不得要求通过文件配置或启动参数传入
  示例：`APP__DB__PASSWORD` 从环境变量读取
- 本地开发可以通过 `config.local.yaml` 提供密钥、密码、Token；实现和仓库配置必须保证该文件不会被提交到代码仓库，已被版本控制跟踪的 `config.local.yaml` 不得作为合规敏感配置来源
  示例：本地调试使用 `configs/config.local.yaml` 写入 `db.password`，但该文件必须被 `.gitignore` 排除
- 禁止在日志中输出敏感配置明文
  示例：日志仅记录 `db.uri` 的主机名，不记录密码
- 示例配置必须使用占位符，不得包含真实凭据
  示例：`APP__DB__PASSWORD=******`
- 占位符不得作为运行时有效敏感值通过校验
  示例：`db.password=******` 仅可用于示例，不得作为实际密码启动服务

### 校验与默认值

#### 必须
- 启动时必须进行完整性与类型校验
  示例：`APP__HTTP__PORT` 对应的 `http.port` 必须为整数
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
- 启动时必须记录参与最终配置计算的来源与摘要
  示例：输出 “config sources: default, env-file, local, env”
- 摘要必须脱敏处理
  示例：`db.uri` 显示为 `mongodb://user:***@host:27017`

#### 推荐
- 支持配置版本或哈希用于排查差异
  示例：`config_hash=8f3c1b...`
