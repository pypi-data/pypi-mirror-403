name: Java DTO 生成器
description: 快速生成数据传输对象（DTO），包括请求/响应对象、参数验证、序列化配置等

# Java DTO 生成器

## 功能描述

自动生成符合项目规范的 DTO 类，包括：
- 请求对象（Request DTO）
- 响应对象（Response DTO）
- 参数验证注解（Bean Validation）
- 序列化配置（Jackson）
- 文档注解（Swagger）

## 使用场景

- 创建 API 接口的请求/响应对象
- 定义数据传输格式
- 实现参数验证

## 生成步骤

1. **分析项目结构**
   - 查找现有的 DTO 类作为参考模板
   - 识别项目的 DTO 命名规范
   - 检查验证注解使用方式

2. **生成 DTO 类**
   - 创建 Request DTO（包含验证注解）
   - 创建 Response DTO（包含序列化配置）
   - 添加必要的文档注解

3. **集成验证**
   - 在 Controller 中使用 @Valid 注解
   - 确保验证规则正确

## 注意事项

- 遵循项目的 DTO 命名规范
- 合理使用验证注解
- 注意序列化性能
- 保持 DTO 的简洁性
