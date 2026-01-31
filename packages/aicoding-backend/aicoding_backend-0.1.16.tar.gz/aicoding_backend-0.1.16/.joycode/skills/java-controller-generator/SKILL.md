name: Java Controller 生成器
description: Spring Boot Controller 生成规范，对齐项目既有响应、异常、UMP 等约定

# Java Controller 生成器

## 目标与场景

生成 RESTful Controller，沿用**项目既有**响应类型与异常处理。适用于：新建接口、为 Service/Domain 补 Controller、统一/重构现有 Controller。**先看现有 Controller 再落盘。**

---

## 约定速查

| 项 | 约定 |
|----|------|
| 分层 | 仅做参数校验、调 Service/Domain、封装响应；不写业务逻辑、不直接依赖 infra |
| 响应 | 只用项目已有的 Result/ResultVO/XxxResult；京东项目常见 `Result<T>`、`XxxResult.success/paramError/serverError` |
| 异常 | 优先 @ControllerAdvice，否则方法内 try-catch 转统一错误响应，并打日志 |
| 命名 | 包 `xxx.controller`，类 `XxxController`，路径用项目前缀（如 `/api/模块名`） |
| HTTP | 查用 GetMapping、提交用 PostMapping；@RequestBody/@RequestParam/@PathVariable；入参 DTO/VO |
| 京东补充 | Web 模块约定包；UMP 用 `UmpUtil.getCallerInfo` + `Profiler.functionError` + `Profiler.registerInfoEnd`；@Slf4j、脱敏打参；敏感接口用 LoginContext/拦截器校验 |

---

## 生成步骤

1. **分析**：参考现有 Controller，确认统一响应、@ControllerAdvice、UMP 用法。
2. **生成**：约定包下建类，@Slf4j + @RestController + @RequestMapping；入参 DTO/VO 做必要校验；调 Service/Domain 返回统一结果；异常 catch 转错误响应（需 UMP 时按上表打点）。
3. **收尾**（可选）：补 Javadoc、Swagger 注解、Controller 测试。

---

## 检查清单

- [ ] 包/类名/路径与现有 Controller 一致
- [ ] 返回值为项目统一响应类型
- [ ] 敏感接口有权限校验
- [ ] 异常已转统一错误响应并打日志；用 UMP 时含 getCallerInfo / functionError / registerInfoEnd
