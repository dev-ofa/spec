# resource

### 状态
Draft

### 目标
resource 规范用于定义全链路传输中的二进制资源标识符。

本规范不定义资源中台、资源对象模型或上传接口；它只约束服务间、工作流、模型调用与 SDK 之间如何用一个字符串表达二进制资源，并如何基于该字符串选择传输方式。

### 适用范围
- 图片、音频、视频、PDF、压缩包、模型输入文件等二进制资源
- 来自外部 URL 的资源
- 已上传到内部对象存储、资源系统或业务系统中的资源
- 请求体中需要短距离直接传输的小型二进制内容

### 非目标
- 不定义结构化资源协议，业务请求与响应中只传递字符串形式的资源标识符
- 不定义统一资源中台、资源生命周期、内容审核、转码、压缩或归档策略
- 不绑定具体存储产品、CDN、上传协议或下载协议
- 不要求所有业务系统使用同一个资源存储

### 资源标识符

资源标识符是一个字符串，使用固定前缀包裹原始资源 URI，并在前缀区表达认证上下文、媒体类型等元信息。

```text
ofa-res[?<param>=<value>&...]#<source_uri>
```

其中：
- `ofa-res` 是固定前缀，用于将本规范定义的资源标识符与普通 URL、普通业务 ID 区分开
- `param` 表示可选元信息或解析提示，例如 `auth_id`、`media_type`
- `#` 是固定分隔符，用于隔离本规范元信息与原始资源 URI
- `source_uri` 是原始资源 URI，例如 `https://example.com/a.png`、`aws_s3://bucket/path/a.png`、`gcs://bucket/path/a.png`、`data:image/png;base64,...`

这种格式保留 `source_uri` 的原始协议形态，避免将 `https`、`aws_s3`、`data` 等协议重写成另一个路径结构。

实现 **必须** 将资源标识符视为不透明字符串。除 SDK 或规范明确允许的解析逻辑外，调用方 **不得** 解析或拼接 `source_uri` 的具体存储路径。

#### 通用规则
- 资源标识符 **必须** 是字符串
- 资源标识符 **必须** 以 `ofa-res` 开头
- 资源标识符 **必须** 包含 `#` 分隔符
- `#` 前的 query string 只属于 `ofa-res` 元信息区
- `#` 后的内容为 `source_uri`，保留原始资源协议语义
- 资源标识符 **应当** 可被 SDK 解析并获取资源内容或可访问地址
- 资源标识符 **不得** 包含长期明文密钥、访问 token、cookie 或其他敏感凭证
- 资源标识符 **应当** 能在日志中安全记录；如果包含临时签名或敏感查询参数，日志中 **必须** 脱敏
- 不以 `ofa-res` 开头的字符串 **不得** 被默认视为本规范资源标识符

### 编码与解析规则

- SDK **必须** 将第一个未编码的 `#` 视为 `ofa-res` 元信息区与 `source_uri` 的分隔符
- 如果 `source_uri` 自身包含 `#`，该字符 **必须** 在 `source_uri` 内编码为 `%23`
- 在 JSON、RPC 请求体或其他不按 URL 解析的协议中，资源标识符整体不要求 percent-encoding
- 如果资源标识符需要嵌入 URL、浏览器地址栏、`application/x-www-form-urlencoded` 表单或其他会按 URL 语义解析的上下文，调用方 **必须** 按该上下文对整个资源标识符进行编码
- 元信息参数值默认允许使用可读形式，不要求整体 percent-encoding
- 如果元信息参数值中包含 `&`、`=` 或 `#`，这些字符 **必须** 在参数值内部进行 percent-encoding，避免与参数区分隔符冲突
- `source_uri` **必须** 保持原始协议语义， **不得** 因为 `ofa-res` 包装而改写其 scheme、path、query 或 fragment 语义

### source_uri

`source_uri` 表示真实资源来源。SDK 根据 `source_uri` 的 scheme 选择解析驱动。

本规范当前定义并标准化的 scheme 为 `https`、`http`、`data`。
未列出的 scheme 不属于本规范的标准兼容范围；实现 **可以** 按插件或注册表机制扩展私有 scheme，但跨服务、跨 SDK 或跨团队协作时 **不得** 默认依赖这些私有 scheme 互通，除非相关协议另有明确约定。

| scheme | 语义 | 示例 | 默认传输方式 |
| --- | --- | --- | --- |
| `https` | 外部或内部 HTTPS 可访问资源 | `ofa-res#https://example.com/a.png` | 旁路 |
| `http` | HTTP 可访问资源 | `ofa-res#http://example.com/a.png` | 旁路，不推荐 |
| `data` | 内联二进制内容 | `ofa-res#data:image/png;base64,...` | 直传 |

#### https
- `https` **应当** 作为外部 URL 的首选 scheme
- SDK 获取 `https` 资源时 **必须** 执行 SSRF 防护、重定向限制与大小限制
- `https` 资源如果需要在内部多次流转， **应当** 先转存为内部可控资源标识符

#### http
- `http` **可以** 用于兼容已有系统
- 新增链路 **不应** 使用 `http`
- SDK 获取 `http` 资源时 **必须** 使用与 `https` 相同的安全限制

#### data
- `data` 用于小型资源的内联传输
- `data` 的 `source_uri` **必须** 遵循 RFC 2397 的 Data URL 形式
- `data` **应当** 只用于小文件、测试样例或短链路一次性传输
- `data` **不得** 用于大图片、视频、长音频、压缩包或批量资源

#### 私有扩展 scheme
- 私有扩展 scheme 不属于本规范的标准兼容范围，但 **可以** 由 SDK、网关或业务协议按注册机制扩展
- 私有扩展 scheme **应当** 使用稳定且可读的 lowercase 命名；如需多词， **应当** 使用下划线分隔
- 涉及具体云厂商或私有资源系统时，推荐使用显式命名，避免使用含义过宽的泛化名称
- 例如 `aws_s3://bucket/path/to/a.png` 可表示 AWS S3 对象，`gcs://bucket/path/to/a.png` 可表示 Google Cloud Storage 对象，`azure_blob://account/container/path/to/a.png` 可表示 Azure Blob Storage 对象
- 如果协议显式约定，也 **可以** 使用面向内部系统的私有 scheme，例如 `x_resource://image/123456`

### 标准参数

资源标识符 **可以** 携带可选参数。标准参数由本规范定义，扩展参数由 SDK、scheme 或业务系统定义。

#### 参数通用规则
- 参数名 **必须** 使用 snake_case
- 参数名 **必须** 只包含小写字母、数字与下划线，并匹配正则 `^[a-z0-9_]+$`
- 参数名大小写敏感；例如 `auth_id` 与 `AUTH_ID` 不等价
- 同一个参数名 **不得** 重复出现；如果重复出现，SDK **必须** 将其视为非法输入并返回错误
- 标准参数名为保留名称，业务扩展 **不得** 复用 `auth_id`、`media_type`、`filename`、`expires_at`、`sha256`
- 扩展参数 **应当** 使用 `x_` 前缀，避免与未来新增标准参数冲突
- 参数值 **必须** 是 UTF-8 字符串
- 参数值如果包含 `&`、`=` 或 `#`， **必须** 在参数值内部进行 percent-encoding

| 参数 | 语义 | 示例 | 规则 |
| --- | --- | --- | --- |
| `auth_id` | 认证上下文标识 | `auth_id=tenant-storage` | 可选 |
| `media_type` | 资源媒体类型 | `media_type=image/png` | 可选 |
| `filename` | 原始文件名或展示文件名 | `filename=input.png` | 可选 |
| `expires_at` | 标识符或临时访问语义的过期时间 | `expires_at=2026-05-20T00%3A00%3A00Z` | 可选 |
| `sha256` | 资源内容摘要 | `sha256=abc...` | 可选 |

#### auth_id
- `auth_id` 表示 SDK 获取资源时使用的认证上下文，不是访问凭证本身
- `auth_id` **可以** 指向租户、应用、服务账号、凭据模板或资源提供方定义的认证配置
- SDK **必须** 通过 `auth_id` 与运行环境换取完整凭据并注入到具体 scheme 的解析逻辑
- 对私有扩展 scheme，`auth_id` 也可用于映射不同云厂商或资源系统的凭据上下文；例如同一 SDK 可约定 `auth_id=aws-prod` 对应 `aws_s3` 凭据，`auth_id=gcp-ml` 对应 `gcs` 凭据，`auth_id=azure-archive` 对应 `azure_blob` 凭据
- `auth_id` **不得** 直接包含密钥、token、cookie 或签名串
- `auth_id` **应当** 只包含大小写字母、数字、点号、下划线、连字符与斜杠
- 如果缺少 `auth_id`，SDK **可以** 使用 scheme 默认认证配置，但 **不得** 绕过权限校验

#### media_type
- `media_type` 表示资源的 MIME 类型，例如 `image/png`、`video/mp4`
- `media_type` **必须** 遵循 IANA Media Types 格式，即 `type/subtype`
- `media_type` **可以** 携带 MIME 参数，例如 `text/plain;charset=utf-8`
- `media_type` 在资源标识符参数中不要求整体 percent-encoding；如果其参数值内部包含 `&`、`=` 或 `#`，仍 **必须** 按参数区规则编码
- 未知或无法识别的二进制资源 **应当** 使用 `application/octet-stream`
- 自定义业务类型 **应当** 使用 IANA vendor tree，例如 `application/vnd.example.asset+json`
- `media_type` 仅作为解析提示， **不得** 作为唯一可信来源
- SDK 获取资源后 **可以** 通过响应头、文件头或内容探测校验 `media_type`
- 对 `data` scheme，`source_uri` 中的 media type 与 `media_type` 参数同时存在时 **必须** 保持一致

#### filename
- `filename` 表示原始文件名或展示文件名
- `filename` **不得** 包含路径分隔符 `/`、`\`、控制字符或空字节
- `filename` **不应** 包含 `..` 等路径穿越片段
- 如果 `filename` 包含 `&`、`=` 或 `#`， **必须** 按参数区规则编码

#### 扩展参数
- SDK **可以** 为不同 scheme 注册自定义扩展参数
- 调用方 **不得** 依赖其他服务透传未知扩展参数，除非协议显式声明
- 未识别的扩展参数 **应当** 被 SDK 保留；这里的“保留”是指 SDK 在解析后重新序列化同一资源标识符时 **应当** 尽量不丢失这些参数，但这不构成跨服务透传承诺，且 **不得** 影响标准参数语义

### 示例

```text
ofa-res?auth_id=asset-service&media_type=image/png#aws_s3://ml-inputs/path/to/input.png
```

```text
ofa-res?auth_id=tenant-storage&media_type=image/png#gcs://bucket/path/to/a.png
```

```text
ofa-res?media_type=image/png#https://example.com/input.png?version=1
```

```text
ofa-res#data:image/png;base64,iVBORw0KGgo...
```

### 传输方式

资源传输分为直传与旁路两类。

#### 直传
直传表示资源内容随业务请求体一起传输，例如 `ofa-res#data:...` 标识符。

直传适用于：
- 资源体积较小
- 资源只在当前链路中使用一次
- 调用链路较短且无复用需求
- 测试、调试或兼容已有协议

直传要求：
- 实现 **必须** 设置单个资源与请求整体大小上限
- 实现 **必须** 避免将完整内容写入日志
- 实现 **应当** 避免在跨多个服务的链路中持续传递内联内容

#### 旁路
旁路表示业务请求只传递资源标识符，资源内容由 SDK、资源提供方或存储系统在需要时获取。

旁路适用于：
- 图片、视频、音频等多媒体资源
- 大文件或批量文件
- 资源需要被多个服务复用
- 资源需要鉴权、审计、缓存、过期控制或跨链路追踪
- 外部 URL 需要先转存到内部存储后再继续流转

旁路要求：
- 业务协议 **必须** 只传递资源标识符， **不得** 同时传递大体积二进制内容
- SDK **应当** 提供统一解析、下载、临时访问地址生成或转存能力
- 资源获取失败时，SDK **必须** 返回明确错误， **不得** 静默降级为空内容

### 传输选择规则

- 新增多模态链路默认 **应当** 使用旁路
- 大于实现方默认阈值的资源 **必须** 使用旁路
- 视频、长音频、压缩包和批量资源 **必须** 使用旁路
- `data` scheme 只允许用于小型资源，默认上限 **应当** 不超过 1 MiB
- SDK 和网关 **可以** 设置更严格的大小、类型、域名与超时限制
- 跨服务转发资源时 **应当** 保持原始资源标识符不变，除非需要转存、脱敏或权限边界切换

### SDK 责任

资源 SDK 用于解析资源标识符并获取资源，不承担资源中台职责。

SDK **应当** 提供：
- 解析资源标识符
- 校验 `source_uri` 的 scheme 是否受支持
- 按 `auth_id` 查找认证上下文并为对应 scheme 注入访问凭据
- 获取资源流或字节内容
- 生成临时可访问地址
- 将外部 URL 转存为内部标识符
- 执行大小限制、超时限制、重定向限制与 SSRF 防护
- 对敏感标识符进行日志脱敏

SDK **不得** 要求业务方构造结构化资源对象。

### 安全要求

- 获取外部 URL 时 **必须** 阻止访问内网地址、链路本地地址、本机地址与云元数据地址
- 获取外部 URL 时 **必须** 限制重定向次数，并对每次重定向后的地址重新执行安全校验
- 获取资源时 **必须** 设置超时、最大响应体大小与内容类型限制
- 实现 **必须** 对资源标识符中的临时签名、敏感查询参数和内联内容执行日志脱敏， **不得** 在日志、错误信息与 tracing 字段中输出完整敏感值
- 对来自用户输入的资源标识符，接收方 **必须** 进行 scheme 白名单校验

### 推荐字段命名

当业务协议需要表达单个资源时，字段名 **应当** 使用 `*_ofa_res_id`。

```json
{
  "image_ofa_res_id": "ofa-res?auth_id=asset-service&media_type=image/png#aws_s3://ml-inputs/path/to/input.png"
}
```

当业务协议需要表达多个资源时，字段名 **应当** 使用 `*_ofa_res_ids`。

```json
{
  "image_ofa_res_ids": [
    "ofa-res?auth_id=asset-service&media_type=image/png#aws_s3://ml-inputs/path/to/input.png",
    "ofa-res?media_type=image/png#https://example.com/input.png"
  ]
}
```

字段名 **可以** 使用业务语义前缀，例如 `input_image_ofa_res_id`、`reference_video_ofa_res_id`。

### 兼容性

- 已有字段中使用普通 URL 的协议 **可以** 继续使用，但新增资源字段 **应当** 使用 `*_ofa_res_id` 或 `*_ofa_res_ids`
- 已有 Base64 字段 **应当** 逐步迁移为 `ofa-res#data:...` 标识符或旁路标识符
- 服务端 **应当** 同时支持旧格式与资源标识符一段时间，并在边界层完成格式归一
