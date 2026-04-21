# spec
dev-ofa（全称：dev-one-for-all）致力于构建统一的软件工程开发规范与实现。
本目录专注于规范定义（specification），作为所有语言实现的唯一依赖与权威来源。

## 使用范围
- 规范定义仅包含跨语言通用约束，不包含实现细节
- 所有实现必须以 spec 为唯一依赖，不得反向修改规范
- 规范以 MUST/SHOULD/MAY 形式定义兼容性要求

## 目录结构
- [_meta](./_meta/spec.md)：术语、命名风格与版本策略
- [api](./api/spec.md)：统一响应 Wrapper 与错误码规范
- [config](./config/spec.md)：配置来源、命名、校验与安全规范
- [logging](./logging/spec.md)：日志格式与请求生命周期日志
- [resilience](./resilience/spec.md)：超时预算、跨服务传播与重试约束
- [tracing](./tracing/spec.md)：链路透传字段与跨协议传播规范
- [entity](./entity/spec.md)：持久化对象落地规范
- [patterns](./patterns/spec.md)：常用开发模式（CRUD、选主、异步 Worker、唯一 ID）

## 实现指南（按语言）
- 本目录不包含实现细节；语言/框架落地建议请参见 [guides](../guides/README.md)
- [Go](../guides/go/README.md)
- [Python](../guides/python/README.md)

## 规范状态
- Draft：可变更且可能出现破坏性调整
- Stable：仅允许向后兼容的演进
- Deprecated：保留但不再推荐使用

## 版本策略
规范使用语义化版本管理，详见 [_meta/spec.md](./_meta/spec.md)
