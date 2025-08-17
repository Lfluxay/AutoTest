# 自动化测试框架设计文档

## 框架概述

本框架是一个基于Python的自动化测试框架，支持接口自动化测试和Web自动化测试。采用关键字驱动思想，支持YAML/Excel格式的用例编写，具备丰富的断言方式和数据驱动能力。

## 技术栈

- **Python** - 主要开发语言
- **requests** - HTTP请求库，用于接口测试
- **pytest** - 测试框架
- **pyyaml** - YAML文件解析
- **loguru** - 日志管理
- **playwright** - Web自动化测试
- **faker** - 测试数据生成
- **allure-pytest** - Allure报告生成
- **pytest-html** - HTML报告生成
- **pymysql/psycopg2** - 数据库连接
- **jsonpath-ng** - JSON数据提取
- **openpyxl** - Excel文件处理

## 框架特性

### 1. 关键字驱动
- 采用关键字驱动的测试设计思想
- 用例编写简单，维护成本低
- 支持自定义关键字扩展

### 2. 多格式用例支持
- **YAML格式** - 结构清晰，易于编写和维护
- **Excel格式** - 适合非技术人员编写用例

### 3. 多种用例类型
- **单接口用例** - 独立的接口测试
- **业务流程接口用例** - 多个接口组合的业务场景
- **数据驱动接口用例** - 使用不同数据集执行相同测试逻辑

### 4. 丰富的断言方式
- **响应状态码断言**
- **响应内容断言**
- **JSON路径断言**
- **正则表达式断言**
- **数据库断言**
- **响应时间断言**

### 5. 数据提取功能
- **JSONPath提取** - 从JSON响应中提取数据
- **正则表达式提取** - 从任意文本中提取数据
- **数据库查询提取** - 从数据库中获取验证数据

### 6. 测试报告
- **Allure报告** - 美观详细的测试报告
- **pytest-html报告** - 简洁的HTML报告
- **可配置报告类型** - 通过配置文件选择生成的报告类型

### 7. 灵活的配置管理
- **测试类型配置** - 指定执行API测试还是Web测试
- **用例范围配置** - 指定执行用例的标签、模块等
- **环境配置** - 支持多环境切换

### 8. 自动清理功能
- 执行前自动删除历史测试报告
- 清理临时文件

### 9. 测试结果通知
- **飞书通知** - 支持飞书机器人消息通知
- **邮箱通知** - 支持邮件发送测试结果
- **企业微信通知** - 支持企业微信群机器人通知
- **可配置通知方式** - 支持多种通知方式组合

### 10. 全局登录管理
- **API测试** - 执行前全局登录，避免重复登录
- **Web测试** - 每个用例执行前返回首页，全局登录状态保持

## 项目结构

```
auto_case/
├── README.md                   # 项目说明文档
├── requirements.txt           # 依赖包列表
├── config/                    # 配置文件目录
│   ├── config.yaml           # 主配置文件
│   ├── env_config.yaml       # 环境配置
│   └── database.yaml         # 数据库配置
├── core/                     # 核心模块
│   ├── __init__.py
│   ├── api/                  # API测试核心
│   │   ├── __init__.py
│   │   ├── client.py         # HTTP客户端
│   │   ├── assertions.py     # API断言
│   │   └── keywords.py       # API关键字
│   ├── web/                  # Web测试核心
│   │   ├── __init__.py
│   │   ├── browser.py        # 浏览器管理
│   │   ├── page_base.py      # 页面基类
│   │   ├── assertions.py     # Web断言
│   │   └── keywords.py       # Web关键字
│   └── base/                 # 基础模块
│       ├── __init__.py
│       ├── test_base.py      # 测试基类
│       └── keywords_base.py  # 关键字基类
├── utils/                    # 工具模块
│   ├── __init__.py
│   ├── logger.py             # 日志工具
│   ├── config_parser.py      # 配置解析
│   ├── data_parser.py        # 数据解析
│   ├── db_helper.py          # 数据库工具
│   ├── faker_helper.py       # 假数据生成
│   ├── extractor.py          # 数据提取工具
│   ├── assertion_helper.py   # 断言辅助工具
│   ├── report_helper.py      # 报告生成工具
│   ├── notify_helper.py      # 通知工具
│   └── file_helper.py        # 文件操作工具
├── data/                     # 测试数据目录
│   ├── api/                  # API测试用例
│   │   ├── login/
│   │   │   ├── login_cases.yaml
│   │   │   └── login_cases.xlsx
│   │   └── user/
│   │       └── user_cases.yaml
│   ├── web/                  # Web测试用例
│   │   ├── login/
│   │   │   └── login_cases.yaml
│   │   └── dashboard/
│   │       └── dashboard_cases.yaml
│   └── common/               # 公共数据
│       ├── test_data.yaml
│       └── users.yaml
├── reports/                  # 测试报告目录
│   ├── allure-results/       # Allure原始数据
│   ├── allure-report/        # Allure报告
│   └── html/                 # HTML报告
├── logs/                     # 日志目录
├── screenshots/              # 截图目录
├── temp/                     # 临时文件目录
├── tests/                    # pytest测试文件
│   ├── __init__.py
│   ├── conftest.py           # pytest配置
│   ├── test_api.py           # API测试执行器
│   └── test_web.py           # Web测试执行器
├── pages/                    # 页面对象(POM)
│   ├── __init__.py
│   ├── login_page.py
│   └── dashboard_page.py
└── main.py                   # 主入口程序
```

## 用例格式示例

### YAML格式 - API用例
```yaml
test_info:
  title: "用户登录接口测试"
  description: "测试用户登录功能的各种场景"
  tags: ["smoke", "login"]

test_cases:
  - case_name: "正常登录"
    request:
      method: "POST"
      url: "/api/login"
      headers:
        Content-Type: "application/json"
      data:
        username: "admin"
        password: "123456"
    assertions:
      - type: "status_code"
        expected: 200
      - type: "json_path"
        path: "$.code"
        expected: 0
      - type: "json_path"
        path: "$.data.token"
        operator: "not_empty"
    extract:
      - name: "token"
        type: "json_path"
        path: "$.data.token"
```

### YAML格式 - Web用例
```yaml
test_info:
  title: "用户登录页面测试"
  description: "测试登录页面的各种操作"
  tags: ["ui", "login"]

test_cases:
  - case_name: "正常登录流程"
    steps:
      - action: "navigate"
        params:
          url: "https://example.com/login"
      - action: "input"
        params:
          locator: "#username"
          value: "admin"
      - action: "input"
        params:
          locator: "#password"
          value: "123456"
      - action: "click"
        params:
          locator: "#login-btn"
      - action: "wait_for_url"
        params:
          url: "*/dashboard"
    assertions:
      - type: "url_contains"
        expected: "dashboard"
      - type: "element_visible"
        locator: ".user-info"
```

## 配置文件示例

### 主配置文件 (config/config.yaml)
```yaml
# 测试类型配置
test_type: "api"  # api/web/both

# 执行配置
execution:
  case_tags: ["smoke"]  # 执行的用例标签
  case_modules: []      # 执行的用例模块
  parallel: false       # 是否并行执行
  max_workers: 4        # 最大并行数

# 报告配置
report:
  type: "pytest-html"   # allure/pytest-html/both
  clean_history: true   # 是否清理历史报告
  
# 通知配置
notification:
  enabled: true
  types: ["feishu"]     # feishu/email/wechat
  feishu:
    webhook: "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"
  email:
    smtp_server: "smtp.qq.com"
    smtp_port: 587
    sender: "test@example.com"
    password: "xxx"
    receivers: ["admin@example.com"]

# API配置
api:
  base_url: "https://api.example.com"
  timeout: 30
  retry_times: 3
  
# Web配置
web:
  browser: "chromium"   # chromium/firefox/webkit
  headless: false
  viewport:
    width: 1920
    height: 1080
  timeout: 30000
```

## 使用方法

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境
编辑 `config/config.yaml` 文件，配置测试环境和参数。

### 3. 编写用例
在 `data/` 目录下编写YAML或Excel格式的测试用例。

### 4. 执行测试
```bash
# 执行所有测试
python main.py

# 执行API测试
python main.py --type api

# 执行Web测试
python main.py --type web

# 执行指定标签的用例
python main.py --tags smoke,regression

# 生成Allure报告
python main.py --report allure
```

### 5. 查看报告
- HTML报告：`reports/html/report.html`
- Allure报告：使用 `allure serve reports/allure-results` 启动服务

## 扩展功能

### 自定义关键字
在 `core/api/keywords.py` 或 `core/web/keywords.py` 中添加自定义关键字。

### 自定义断言
在 `core/api/assertions.py` 或 `core/web/assertions.py` 中添加自定义断言方法。

### 数据库支持
在 `config/database.yaml` 中配置数据库连接，支持MySQL、PostgreSQL等。

## 最佳实践

1. **用例组织** - 按业务模块组织用例文件
2. **数据分离** - 将测试数据与用例逻辑分离
3. **环境管理** - 使用不同配置文件管理多环境
4. **错误处理** - 充分利用重试和错误恢复机制
5. **报告分析** - 定期分析测试报告，优化测试策略

## 常见问题

### Q: 如何处理动态数据？
A: 使用faker_helper生成随机数据，或使用数据提取功能获取运行时数据。

### Q: 如何处理依赖用例？
A: 使用业务流程用例，或通过数据提取和变量传递实现用例间数据共享。

### Q: 如何调试失败的用例？
A: 查看详细日志文件，Web测试会自动截图保存到screenshots目录。