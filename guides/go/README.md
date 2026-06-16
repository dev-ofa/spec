# Go 工程化落地指南

本指南描述 Go 项目在目录分层、依赖管理、环境管理与基础命令方面的推荐做法，用于把 [spec](../../README.md) 落地到 Go 实现中。

## 目录分层（推荐）

适用场景：中大型服务端项目（HTTP/gRPC/异步 Worker），需要清晰边界与可测试性。
本分层是推荐而非强制，也可以采用传统三层分层方式（如 controller/service/repo 或 handler/service/dao）。

```
.
├── cmd/
│   └── <app>/
│       └── main.go
├── internal/
│   ├── app/
│   ├── domain/
│   ├── infra/
│   └── handler/
├── pkg/                (可选：仅放跨仓库复用的公共库)
├── api/                (可选：OpenAPI/Proto/IDL 与生成物入口)
├── configs/            (配置样例、默认配置)
├── scripts/            (CI/本地开发脚本)
├── build/              (产物与打包配置，如 docker/)
├── tools/              (可选：工具依赖与工具 main 包)
├── go.mod
└── go.sum
```

约定：
- `cmd/<app>/main.go` 只做启动与装配（读取配置、组装依赖、启动服务），不承载业务逻辑
- `internal/app` 放应用层编排、用例流程、事务边界
- `internal/domain` 放领域模型、领域服务、领域事件
- `internal/infra` 放外部依赖适配（DB、缓存、MQ、第三方 HTTP 等）
- `internal/handler` 放 API/协议入口（HTTP/gRPC/消息消费），小型项目可与 `app` 合并
- `pkg/` 仅用于“跨仓库复用”的公共库；仅在确有复用需求时启用

## 示范项目结构（仅文件夹示例）

```
.
├── cmd/
│   └── orderd/
├── internal/
│   ├── app/
│   ├── domain/
│   ├── infra/
│   └── handler/
├── api/
├── configs/
├── scripts/
│   └── make/
├── build/
└── tools/
```

建议把统一命令入口放在 `scripts/` 或仓库根目录（例如 Makefile）。

## 本目录内示范项目

示范项目已放在 [example](./example/) 目录，包含真实文件夹结构与 Makefile 脚本。

## 包与依赖管理
- 使用 Go Modules：维护 `go.mod/go.sum`
- 依赖升级策略：按小步升级，保持可回滚；CI 里固定 `-mod=readonly`，避免隐式变更
- 多模块仓库：优先评估是否真的需要；确需多模块时使用 `go.work` 管理本地联调

## 环境与版本管理
- 必须固定 Go 版本，并让开发机/CI 使用同一版本
- 推荐使用版本管理工具统一安装（择一即可）：
  - `mise`（在 `mise.toml` 固定版本）
  - `asdf`（在 `.tool-versions` 固定版本）

## 代码风格与工具链（推荐）
- 格式化：`gofmt` 必须执行；推荐 `goimports` 统一 import 分组
- 质量检查（择一或组合）：
  - `golangci-lint` 作为聚合 lint
  - `staticcheck` 作为补充
- 测试：优先 `go test ./...`；对关键逻辑补齐单元测试，并保证可并行运行

## 项目应具备的基本命令

建议在仓库根目录提供统一入口（例如 Makefile），至少包含以下命令语义：
- `fmt`：格式化代码（`gofmt` + `goimports`）
- `tidy`：整理依赖（`go mod tidy`）并校验 `go.mod/go.sum` 无脏改动
- `lint`：静态检查（建议覆盖风格、复杂度、潜在 bug）
- `test`：运行测试（含 race/覆盖率按团队需求开启）
- `build`：构建可执行文件（输出到 `./dist` 或 `./build`）
- `run`：本地启动（显式选择配置/环境变量）

一个可直接复用的命令组合（示例）：
```
make tidy fmt lint test
```

## 与 spec 的对齐要点（落地提醒）
- API：实现统一响应包装，参见 [api/spec.md](../../api/spec.md)；错误码映射遵循 [error/spec.md](../../error/spec.md)
- Logging：实现请求生命周期日志与字段规范，参见 [logging/spec.md](../../logging/spec.md)
- Service：实现跨系统域名入口、系统内服务发现与默认协议约束，参见 [service/spec.md](../../service/spec.md)
- Tracing：实现透传字段与跨协议传播，参见 [tracing/spec.md](../../tracing/spec.md)
