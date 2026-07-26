# Python 工程化落地指南

本指南描述 Python 项目在目录分层、包/环境管理与基础命令方面的推荐做法，用于把 [spec](../../README.md) 落地到 Python 实现中。

## 目录分层（推荐）

适用场景：服务端应用、脚本/Worker、带领域逻辑的中大型项目。
本分层是推荐而非强制，也 **可以** 采用传统三层分层方式（如 controller/service/repo 或 handler/service/dao）。

推荐使用 `src/` 布局，避免本地路径污染与导入歧义：

```
.
├── pyproject.toml
├── src/
│   └── <package_name>/
│       ├── __init__.py
│       ├── app/
│       ├── domain/
│       ├── infra/
│       └── handler/
├── tests/
├── scripts/
└── README.md
```

约定：
- `app/` 放应用层编排、用例流程、事务边界
- `domain/` 仅包含领域与业务规则，避免直接依赖框架与 IO
- `infra/` 负责外部依赖适配（DB、缓存、MQ、第三方 API），通过接口注入到 app/domain
- `handler/` 放 API/协议入口（HTTP/CLI/消息消费入口），小型项目可与 `app/` 合并

## 示范项目结构（仅文件夹示例）

```
.
├── pyproject.toml
├── src/
│   └── orders/
│       ├── app/
│       ├── domain/
│       ├── infra/
│       └── handler/
├── tests/
├── scripts/
│   └── make/
└── README.md
```

建议把统一命令入口放在 `scripts/` 或仓库根目录（例如 Makefile）。

## 本目录内示范项目

示范项目已放在 [example](./example/) 目录，包含真实文件夹结构与 Makefile 脚本。

## 包管理与环境管理

**必须** 目标：可复现安装（开发机与 CI 一致），并能明确区分“运行时依赖”和“开发依赖”。

- 包管理工具（择一即可，推荐统一到团队标准）：
  - 推荐：`uv`（锁文件 + 环境创建/同步一体化）
  - 可选：`poetry`（生态成熟，锁文件明确）
  - 可选：`pip-tools`（`requirements.in`/`requirements.txt` 锁定）
- Python 版本管理（择一即可）：
  - `mise` / `asdf` / `pyenv`
- 虚拟环境：
  - **必须** 使用虚拟环境（工具自带或 `venv`），避免污染系统 Python

## 代码风格与工具链（推荐）
- 缩进：4 空格； **禁止** Tab
- 格式化：推荐 `ruff format`（或 `black`），并在 CI 中强制执行
- Lint：推荐 `ruff check`（覆盖基础风格、易错点、复杂度）
- 类型检查（按项目类型选择）：
  - `pyright`（速度快，适合 CI）
  - `mypy`（生态成熟）
- 测试：推荐 `pytest`；保证测试可重复、可并行

## 项目 **应当** 具备的基本命令

建议在仓库根目录提供统一入口（例如 Makefile），至少包含以下命令语义：
- `fmt`：格式化代码（例如 `ruff format`）
- `lint`：静态检查（例如 `ruff check`）
- `type`：类型检查（例如 `pyright` 或 `mypy`）
- `test`：运行测试（例如 `pytest`）
- `lock`：生成/更新锁文件（按所选包管理工具）
- `sync`：根据锁文件安装/同步依赖（开发机与 CI 用同一条命令）

一个可直接复用的命令组合（示例）：
```
make sync fmt lint type test
```

## 与 spec 的对齐要点（落地提醒）
- API：实现资源表示、DTO 边界与统一响应包装，参见 [api/spec.md](../../api/spec.md)；错误码映射遵循 [error/spec.md](../../error/spec.md)
- Logging：实现请求生命周期日志与字段规范，参见 [logging/spec.md](../../logging/spec.md)
- Service：实现跨系统域名入口、系统内服务发现与默认协议约束，参见 [service/spec.md](../../service/spec.md)
- Tracing：实现透传字段与跨协议传播，参见 [tracing/spec.md](../../tracing/spec.md)
