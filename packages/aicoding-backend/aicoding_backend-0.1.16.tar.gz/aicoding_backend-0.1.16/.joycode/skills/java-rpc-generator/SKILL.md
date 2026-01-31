name: Java JSF RPC 导入规范
description: 通用的 JSF/DongBoot RPC 导入步骤与规范，适用于使用该类框架的 Java 项目

# Java JSF RPC 导入规范

## 功能与目标

按统一规范完成「导入一个外部 JSF RPC 服务」：在**接口层**定义对内的 Facade/Service 接口（不依赖 JSF 类型），在**实现层**用 `@BootReference` 注入并封装调用，在**环境配置**中管理别名、超时、认证等；**先识别项目既有分层与配置约定再落盘。**

## 适用场景

新增外部 JSF 调用、将已有调用迁到「接口 + 实现 + 配置」分层、多环境切换同一 RPC 的别名与参数。

---

## 一、分层与位置约定

| 层级 | 职责 |
|------|------|
| 接口层 | 定义对内的 RPC 封装接口，方法签名用项目内 BO/DO/DTO，**不暴露** JSF 自有 Request/Response |
| 实现层 | 用 `@BootReference` 注入外部 JSF 接口，实现上述接口并做参数/结果转换 |
| 配置 | 按环境配置 `jsf.<serviceKey>.*`，不写死别名与密钥 |

**命名**：serviceKey 与 `@BootReference` 的 `uniqueId` 及配置前缀一致（小驼峰）；实现类建议 XxxRpcServiceImpl / XxxServiceImpl，包与目录按项目现有结构放置。

---

## 二、导入步骤

1. **接口层**：在项目约定的 facade/service 包下定义或复用接口，签名只用项目内类型。
2. **实现层**：在项目约定的实现层包下建实现类，对「外部 JSF 接口」字段用 `@BootReference` 注入；binding 内用 `@BootReferenceBinding` 配别名、超时、重试等。必填：`uniqueId`（= 配置 serviceKey）、`alias`（占位符如 `jsf.<serviceKey>.alias`）、`bindingType = "jsf"`。
3. **配置**：在环境配置文件（如 application-{env}.properties）中增加 `jsf.<serviceKey>.<项>`（alias、timeOut、authToken、clientName 等），与注解占位符一致；不同环境用不同文件或 profile。
4. **可选组合**：按需选用 — 仅别名+超时（只读）、别名+认证（parameters 中 authToken/clientName，敏感项 `hidden = true`）、超时+重试（非幂等慎用）、集群/序列化（按 JSF 与项目约定）。

---

## 三、注意事项与检查清单

- **接口与实现分离**：接口层不依赖 JSF 与运行时注解，便于单测与替换。
- **uniqueId 与 serviceKey 统一**：`uniqueId` 与 `jsf.<serviceKey>` 一一对应。
- **敏感参数**：authToken、含密钥的 clientName/alias 等用 `hidden = true`，避免进通用日志。
- **超时与重试**：按业务与链路设定超时；非幂等接口慎用 retries。
- **请求构建**：JSF SDK 有 Builder 时优先用 Builder；BO/DO 与请求对象的转换在实现层内完成。
- **日志与监控**：实现类内按项目既有约定打日志、打点、抛业务/技术异常。

**检查清单**：
- [ ] 接口层已定义/复用接口，且未暴露 JSF 专有类型
- [ ] 实现类在约定包下，`uniqueId` 与 `jsf.<serviceKey>` 一致
- [ ] alias、timeoutStr、retries 及必要 parameters 均从配置读取（`jsf.<serviceKey>.*`）
- [ ] 各环境配置已补齐对应项；敏感项 `hidden = true`；非幂等未盲目加大 retries
- [ ] 实现类已按项目惯例打日志、打点，并在需要时抛业务/技术异常
