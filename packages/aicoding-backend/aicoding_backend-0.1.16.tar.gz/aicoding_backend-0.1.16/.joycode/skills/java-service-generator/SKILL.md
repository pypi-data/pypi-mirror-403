name: Java Service 生成器
description: Spring Boot Service 层生成规范，对齐项目分层（app/domain）、事务、异常与命名约定

# Java Service 生成器

## 目标与场景

生成 Service 层：流程编排或领域逻辑，沿用**项目既有**分层（app/domain）、事务与异常约定。适用于：新建业务服务、为 Controller/Domain 补 Service、重构现有 Service。**先看现有 Service 再落盘。**

---

## 约定速查

| 项 | 约定 |
|----|------|
| 分层 | app 做流程编排、调 Domain；domain 放核心业务规则；禁止 app 写领域逻辑、domain 直接依赖 infra-impl |
| 依赖 | app → domain → infra-api ← infra-impl；禁止循环与跨层；可依赖 common |
| 包 | app 模块下约定包（如 `agent.app.{业务}.impl`）；domain 下按子域（如 `agent.domain.{子域}.service` 及 impl） |
| 命名 | 接口 XxxService / XxxDomainService，实现 XxxServiceImpl / XxxDomainServiceImpl；方法查用 get/query/find/list、改用 update/modify、删用 delete/remove、增用 add/insert/save |
| 事务 | 写库/多表写方法加 @Transactional，rollbackFor 按项目约定（如 Exception.class） |
| 异常与日志 | 用项目自定义异常（BaseException/AgentBizException），不吞异常；@Slf4j，异常处 log.error 带 requestId 等上下文；关键入参/结果打日志 |
| 其它 | 依赖注入按项目（构造器或 @Resource）；类与公共方法需 Javadoc |

---

## 生成步骤

1. **分析**：判断能力落在 app 还是 domain；参考现有 Service；确认包、命名、事务与异常约定。
2. **接口**（若用接口模式）：约定包下定义接口，方法用项目内 BO/DO/DTO，不暴露外部 SDK 类型。
3. **实现**：约定包下建实现类，@Service + @Slf4j；注入 Repository/DomainService/门面等；写库/多表写加 @Transactional；异常抛自定义异常并打日志。
4. **收尾**（可选）：补 Javadoc、单测（Mock 依赖，覆盖主流程与异常）。

---

## 检查清单

- [ ] 模块与包符合分层（app 编排、domain 领域逻辑），无跨层与循环依赖
- [ ] 接口/实现命名符合约定（XxxService/XxxServiceImpl 或 XxxDomainService/XxxDomainServiceImpl）
- [ ] 需事务方法已加 @Transactional，rollbackFor 与项目一致
- [ ] 异常用项目自定义类型，不吞异常，异常处有日志与上下文；类与公共方法有 Javadoc
