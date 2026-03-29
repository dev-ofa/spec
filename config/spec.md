## config

### 状态
Draft

### 配置来源与优先级

#### 必须
- 配置必须来自默认配置、环境变量、本地覆盖文件或启动参数之一
  示例：`config.default.yaml` + `APP_PORT=8080` + `config.local.yaml` + `--app.port=9090`
- 加载顺序固定为：默认配置 → 环境变量 → 本地覆盖文件 → 命令行参数
  示例：`APP_PORT=8080` 且 `--app.port=9090` 时，最终端口为 `9090`
- 同名配置必须遵循后者覆盖前者的规则
  示例：`config.default.yaml` 中 `db.uri` 被 `DB_URI` 覆盖
- 支持按环境读取差异化配置文件
  示例：`ENV=dev` 时读取 `config.dev.yaml`，不存在则忽略


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
  示例：`DB_PASSWORD` 从环境变量读取
- 禁止在日志中输出敏感配置明文
  示例：日志仅记录 `db.uri` 的主机名，不记录密码
- 示例配置必须使用占位符，不得包含真实凭据
  示例：`DB_PASSWORD=******`

### 校验与默认值

#### 必须
- 启动时必须进行完整性与类型校验
  示例：`APP_HTTP_PORT` 必须为整数
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
