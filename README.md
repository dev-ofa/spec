# spec
dev-ofa（全称：dev-one-for-all）致力于构建统一的软件工程开发规范与实现。
本目录专注于规范定义（specification），作为所有语言实现的统一规范来源与权威来源。

`spec/AGENTS.md` 规定 Agent 在本仓库中编写和维护规范文档时的工作方式；本文件只提供规范导航、目录说明与接入原则。

## 使用范围
- 本目录维护跨语言通用规范，不承载具体业务实现。
- 具体规则以各 `spec/**/*.md` 正文为准。

## 规范实施指导原则

以下原则用于说明 dev-ofa 规范体系的组织方式、接入方式与配套关系。

### 原则 1：规范中心化
- `spec` **应当** 独立作为统一的规范接入项目，集中维护规范本身、接入方式、应用原则，以及规范与对应实现/基础库之间的关系与选用原则
- 规范源记录 **必须** 放在固定、可版本化、可审阅的位置， **不应** 绑定某一种具体分发方式
- 业务项目和基础库项目都 **应当** 以 `spec` 为唯一规范来源， **不得** 反向修改规范定义

### 原则 2：规范本地化
- 项目接入规范后， **应当** 在接入方仓库内形成 repo-local 的索引入口，供 Agent 直接感知
- 当前优先采用接入方仓库根目录下的 `AGENTS.md` 作为索引入口；未来可按工具需要扩展到其他本地入口形式
- Agent 执行任务时， **应当** 从编辑目标所在路径向上优先查找最近的 `AGENTS.md`，按目录层级叠加规则；若存在冲突，以更接近编辑目标的文件为准
- 分发方式不做唯一限定；当前推荐将 `spec` 以 git submodule 的方式接入到目标项目的 `docs/spec` 目录中，但体系设计 **不应** 依赖于某一种接入方式
- 接入方仓库中的 `docs/spec/` 只是规范分发副本和只读引用源，不是当前项目的本地规范目录；项目自有规则 **应当** 写在 `docs/spec/` 之外的合适位置
- 当前 `bootstrap.py` 仅支持 `docs/spec` 这一目录布局；如果采用其他接入路径，需要手动维护 repo-local 索引入口，或自行扩展接入脚本

### 原则 3：基础库通过脚手架表达推荐用法
- 对于 `core-go`、未来的 `core-py`，以及其他遵从 `spec` 的基础库，其组织级推荐用法 **应当** 主要通过脚手架暴露
- 脚手架 **应当** 通过接入方仓库中的 `AGENTS.md`、示例代码和任务视角的 playbook，提供充足、覆盖主路径的 case，帮助 Agent 学会多个基础库的组合使用方式
- 脚手架中的 case 默认就是权威示例；如果某个 case 不是推荐写法，就 **不应** 保留在脚手架中

### 原则 4：基础库自身维护事实来源，并建立演进机制
- 基础库自身仓库中的 `README`、代码注释和必要 docs，是单库级使用说明的事实来源
- 脚手架、repo-local 索引与基础库说明之间 **应当** 建立可持续的演进机制，确保随着基础库和规范演进，相关示例、索引和说明能够被自动提醒、同步或生成
- 后续 **应当** 逐步通过自动化流程完成提醒、同步、生成和必要校验，降低人工维护成本

## 推荐接入方式
- 建议将 `spec` 仓库放在目标项目的 `docs/spec` 目录下
- 如果希望由父仓库显式管理版本并方便后续更新，建议以 git submodule 的方式接入
- 体系设计允许采用其他分发方式，但当前 `bootstrap.py` 只支持 `docs/spec`
- 以 git submodule 接入

```bash
git submodule add https://github.com/dev-ofa/spec.git docs/spec
python docs/spec/bootstrap.py
```

- 如果是首次 clone 一个已经接入了该 submodule 的项目，需要先初始化 submodule

```bash
git submodule update --init --recursive
python docs/spec/bootstrap.py
```

- 更新 submodule 到远端最新提交后，需要在父仓库中提交 submodule 引用变更

```bash
git submodule update --remote docs/spec
python docs/spec/bootstrap.py
git add docs/spec
git commit -m "chore: update dev-ofa spec"
```

- `bootstrap.py` 当前会基于 `docs/spec` 的目录约定，初始化或更新目标项目根目录下的 `AGENTS.md`，作为接入方仓库中的 repo-local 索引入口
- 如果目标项目不存在 `AGENTS.md`，脚本会生成一个简洁的仓库级模板，并写入 dev-ofa 托管区块；模板默认强调先澄清假设、优先简单方案、最小化改动和可验证交付；默认使用中文，也可通过 `python docs/spec/bootstrap.py --init-language en` 指定英文
- 如果目标项目已经存在 `AGENTS.md`，脚本会以托管区块的方式插入或更新 dev-ofa 相关内容，而不会整文件覆盖；已有内容包含中文时，托管区块使用中文，否则保留英文
- 托管区块会明确要求 Agent 以编辑目标为起点向上查找最近的 `AGENTS.md`，从而支持分模块、分层级地声明规则，而不必把所有约束都堆在仓库根文件中
- 托管区块会明确要求把 `docs/spec/` 视为只读规范来源；如果当前项目需要新增本地规则， **应当** 放到项目自己的 `AGENTS.md`、模块文档或设计文档里，而不是直接修改 `docs/spec/`

## 目录结构
- [_meta](./_meta/spec.md)：术语、命名风格与版本策略
- [api](./api/spec.md)：HTTP API 资源建模、资源表示与统一响应 Wrapper
- [authentication](./authentication/spec.md)：认证凭证来源、适用边界与最小安全要求
- [config](./config/spec.md)：配置来源、命名、校验与安全规范
- [dependency](./dependency/spec.md)：依赖生命周期、依赖发现方式与 service locator 治理规范
- [error](./error/spec.md)：错误分类、错误码、传播、上下文、记录与对外表达规范
- [logging](./logging/spec.md)：日志格式与请求生命周期日志
- [service](./service/spec.md)：服务间调用、系统边界、默认协议与服务发现规范
- [resilience](./resilience/spec.md)：超时预算、跨服务传播与重试约束
- [tracing](./tracing/spec.md)：链路透传字段与跨协议传播规范
- [entity](./entity/spec.md)：持久化对象落地规范
- [i18n](./i18n/spec.md)：国际化基础规范，覆盖 locale 选择、传播、资源回退、响应结构和地区化边界
- [resource](./resource/spec.md)：二进制资源标识符、直传与旁路传输规范
- [patterns](./patterns/spec.md)：常用开发模式（CRUD、唯一 ID、分布式锁、选主、心跳、异步 Worker、并发控制、分布式事务）

## 实现指南（按语言）
- 语言/框架落地建议请参见 [guides](./guides/README.md)
- [通用编码规范](./guides/coding.md)
- [Go](./guides/go/README.md)
- [Python](./guides/python/README.md)

## 配套说明
- [DKit](./patterns/dkit.md)：patterns 规范的一种工程化实现思路，重点说明如何复用事务数据库实现轻量分布式原语
- [bootstrap.py](./bootstrap.py)：推荐接入脚本，用于在目标项目根目录初始化或更新 `AGENTS.md`

## 规范状态
- Draft：可变更且可能出现破坏性调整
- Stable：仅允许向后兼容的演进
- Deprecated：保留但不再推荐使用

## 版本策略
规范使用语义化版本管理，详见 [_meta/spec.md](./_meta/spec.md)
