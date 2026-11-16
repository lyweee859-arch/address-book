# 代码规范与结对协作约定 (Code Standards & Collaboration Guide)

> **课程**：Software Engineering (FZU–MU) — EE308FZ  
> **项目**：Extreme Programming Address Book (星云智能通讯录)

本文档定义了本团队在极限编程（Extreme Programming）通讯录项目中的前后端编码规范、数据库命名准则、Git 分支管理以及 Pull Request 协作流程。

---

## 1. Python 后端编码规范 (PEP 8)

1. **排版与缩进**
   - 统一使用 **4 个空格** 进行缩进，严禁混用 Tab 与空格。
   - 每行代码长度原则上不超过 **100 个字符**。
   - 文件编码统一采用 **UTF-8**。

2. **命名规范**
   - **模块与文件名**：使用全小写字母 + 下划线（`snake_case`），例如 `excel_service.py`、`db.py`。
   - **函数与变量名**：使用 `snake_case`，函数名应以动词开头清晰表达意图，例如 `list_contacts()`、`toggle_bookmark()`、`export_contacts_to_excel()`。
   - **类名**：使用大驼峰（`PascalCase`），例如 `Config`。
   - **常量名**：使用全大写字母 + 下划线（`UPPER_SNAKE_CASE`），例如 `EXPORT_HEADERS`、`BASE_DIR`。

3. **类型注解与异常处理**
   - 核心业务函数应使用 `typing` 模块提供明确的参数和返回值类型注解（如 `List[Dict[str, Any]]`、`Optional[str]`）。
   - API 层统一捕获 `ValueError` 等业务校验异常，并返回标准 JSON 格式与语义化 HTTP 状态码（`200`、`201`、`400`、`404`）。

---

## 2. 前端编码规范 (HTML / CSS / JavaScript)

1. **HTML5 语义化**
   - 使用语义化标签（`<header>`、`<main>`、`<section>`、`<article>`），并为交互控件提供无障碍属性（`aria-label`、`role`）。

2. **CSS 样式规范**
   - 统一在 `:root` 中使用 **CSS 自定义属性（CSS Variables）** 管理主题色、圆角与阴影（如 `--primary`、`--amber`、`--radius-lg`）。
   - 类名采用短横线连接（`kebab-case`），如 `.contact-card`、`.bookmark-btn`、`.method-row`。

3. **JavaScript 规范 (ES6+)**
   - 优先使用 `const` 和 `let`，禁止使用 `var`。
   - 变量与函数采用小驼峰（`camelCase`），常量配置采用全大写（如 `METHOD_META`）。
   - 所有动态渲染到 DOM 的用户输入必须经过 `escapeHTML()` 转义，防止 XSS 注入风险。

---

## 3. 数据库设计规范 (SQLite)

- 表名统一使用复数形式小写下划线命名：`contacts`（联系人主表）、`contact_methods`（多种联系方式从表）。
- 主键统一命名为 `id`，外键命名为 `<单数表名>_id`（如 `contact_id`），并开启 `PRAGMA foreign_keys = ON` 保证级联删除完整性。
- 布尔状态字段（如 `bookmarked`）在 SQLite 中使用 `INTEGER NOT NULL DEFAULT 0`（`0` 表示未收藏，`1` 表示已收藏）。

---

## 4. Git 提交与分支协作规范

### 4.1 分支策略
- `main`：主分支，始终保持可构建、可部署状态。
- 功能/文档分支：按模块划分（如 `docs/standards`、`feat/base-ui`、`feat/multi-methods-ui`、`style/ui-polish`、`feat/bookmark-ui`、`test/suite-and-docs`），开发完成后通过 **Pull Request (PR)** 合并回 `main`。

### 4.2 Commit Message 规范 (Conventional Commits)
每次提交信息格式为：`<type>: <description>`

| 类型 (`type`) | 说明 | 示例 |
| :--- | :--- | :--- |
| `feat` | 新增功能（如收藏、多联系方式、Excel 导入导出） | `feat: implement bookmark API and favorites prioritization` |
| `style` | 样式美化与布局调整（不影响逻辑） | `style: polish page styling, responsive layout and visual theme` |
| `docs` | 文档新增或更新（README、代码规范、部署手册） | `docs: add code standards and initial README` |
| `test` | 自动化测试与测试数据补充 | `test: add unit tests, sample Excel file and update README` |
| `chore` | 项目构建、依赖配置、Docker 部署脚本 | `chore: add Dockerfile, docker-compose and Gunicorn config` |
| `fix` | 缺陷修复 | `fix: handle empty rows during Excel import` |
