# 测试用例示例集合

本目录包含了各种类型的测试用例示例，帮助您快速上手自动化测试框架。

## 目录结构

```
data/examples/
├── api/                    # API测试示例
│   ├── basic_api_test.yaml        # 基础API测试
│   └── template_based_test.yaml   # 模板化API测试
├── web/                    # Web测试示例
│   └── basic_web_test.yaml        # 基础Web测试
├── excel/                  # Excel测试示例
│   ├── api_test_cases.xlsx        # API测试Excel文件
│   ├── template_test_cases.xlsx   # 模板化Excel文件
│   └── README.md                  # Excel使用说明
├── datasets/               # 测试数据集
│   └── user_test_data.yaml        # 用户测试数据
├── templates/              # 测试模板
│   └── api_templates.yaml         # API测试模板
└── README.md              # 本文件
```

## 快速开始

### 1. 运行基础API测试

```bash
# 执行基础API测试示例
python main.py --type api --file data/examples/api/basic_api_test.yaml

# 按标签过滤执行
python main.py --type api --file data/examples/api/basic_api_test.yaml --tags positive
```

### 2. 运行模板化测试

```bash
# 执行模板化API测试
python main.py --type api --file data/examples/api/template_based_test.yaml

# 执行特定模板测试
python main.py --type api --file data/examples/api/template_based_test.yaml --tags template
```

### 3. 运行Web测试

```bash
# 执行Web自动化测试
python main.py --type web --file data/examples/web/basic_web_test.yaml
```

### 4. 运行Excel测试

```bash
# 创建Excel示例文件（首次运行）
python create_excel_examples.py

# 执行Excel API测试
python main.py --excel data/examples/excel/api_test_cases.xlsx

# 执行Excel模板测试
python main.py --excel data/examples/excel/template_test_cases.xlsx --modules login_module
```

## 示例说明

### API测试示例

#### 1. basic_api_test.yaml
- **功能**: 演示基本的HTTP请求测试
- **包含**: GET、POST、PUT、DELETE请求示例
- **特点**: 直接定义请求和断言，适合简单场景
- **学习重点**: 
  - 请求配置
  - 断言类型
  - 数据提取

#### 2. template_based_test.yaml
- **功能**: 演示模板化数据驱动测试
- **包含**: 文件内模板定义和使用
- **特点**: 减少重复代码，支持批量数据测试
- **学习重点**:
  - 模板定义
  - 变量替换
  - 数据驱动
  - 配置覆盖

### Web测试示例

#### basic_web_test.yaml
- **功能**: 演示Web页面自动化测试
- **包含**: 页面导航、表单操作、元素等待
- **特点**: 支持复杂的页面交互
- **学习重点**:
  - 页面操作
  - 元素定位
  - 等待策略
  - 断言验证

### Excel测试示例

#### api_test_cases.xlsx
- **功能**: 非技术人员友好的API测试
- **包含**: 基础HTTP请求测试用例
- **特点**: 表格化管理，易于维护
- **适用人群**: 测试人员、业务人员

#### template_test_cases.xlsx
- **功能**: Excel格式的模板化测试
- **包含**: 登录模块、用户管理模块
- **特点**: 结合模板和Excel的优势
- **适用场景**: 大量相似测试用例

### 数据集示例

#### user_test_data.yaml
- **功能**: 提供各种测试数据
- **包含**: 正向、负向、边界、性能测试数据
- **特点**: 分类清晰，覆盖全面
- **使用方式**: 在模板中引用数据集

### 模板示例

#### api_templates.yaml
- **功能**: 可复用的API测试模板
- **包含**: 认证、用户管理、通用CRUD模板
- **特点**: 高度可复用，参数化配置
- **使用方式**: 在测试用例中引用模板

## 学习路径

### 初学者
1. 从 `basic_api_test.yaml` 开始，学习基本概念
2. 尝试修改示例中的URL和断言
3. 运行测试并观察结果

### 进阶用户
1. 学习 `template_based_test.yaml` 中的模板使用
2. 创建自己的模板和数据集
3. 尝试Excel格式的测试用例

### 高级用户
1. 结合多种测试类型（API + Web）
2. 设计复杂的测试流程
3. 集成到CI/CD流水线

## 最佳实践

### 1. 文件组织
- 按功能模块组织测试文件
- 使用清晰的命名规范
- 分离测试数据和测试逻辑

### 2. 模板设计
- 设计通用性强的模板
- 合理使用变量和条件
- 提供清晰的模板文档

### 3. 数据管理
- 分类管理测试数据
- 使用环境变量管理敏感信息
- 定期清理过时数据

### 4. 标签使用
- 使用一致的标签规范
- 支持多维度过滤
- 便于测试分类执行

## 扩展示例

### 自定义断言
```yaml
assertions:
  - type: "json_path"
    path: "$.data.items"
    operator: "length_equals"
    expected: 10
    message: "返回的项目数量应为10"
```

### 条件执行
```yaml
test_cases:
  - case_name: "环境相关测试"
    condition: "${ENV} == 'test'"
    request:
      method: "GET"
      url: "/api/test-endpoint"
```

### 依赖关系
```yaml
test_cases:
  - case_name: "登录"
    # ... 登录逻辑
    extract:
      - name: "token"
        type: "json_path"
        path: "$.token"
        
  - case_name: "使用token访问"
    depends_on: "登录"
    request:
      headers:
        Authorization: "Bearer ${token}"
```

## 故障排除

### 常见问题
1. **模板路径错误**: 检查模板路径是否正确
2. **变量未定义**: 确保所有变量都有值
3. **断言失败**: 检查期望值是否正确
4. **网络问题**: 确认测试环境网络连通性

### 调试技巧
1. 启用调试模式查看详细日志
2. 使用简单的测试用例验证环境
3. 逐步增加测试复杂度
4. 检查响应数据格式

## 贡献指南

欢迎贡献更多的测试示例：
1. 遵循现有的文件结构
2. 提供清晰的注释和说明
3. 包含正向和负向测试场景
4. 更新相关文档

## 相关文档

- [测试用例编写指南](../../docs/test_case_writing_guide.md)
- [快速入门指南](../../docs/quick_start_guide.md)
- [框架配置说明](../../docs/configuration_guide.md)
