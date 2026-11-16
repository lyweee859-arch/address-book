# 📒 星云智能通讯录 (XP Address Book)

> **Course**: EE308FZ Software Engineering — Software Engineering (FZU–MU)  
> **Assignment**: Extreme Programming (Address Book Application)

基于 **Python Flask + SQLite + OpenPyXL + 原生响应式前端 + Docker** 开发的现代化云端通讯录系统，完整实现了课程要求的星标收藏、多联系方式管理、Excel 批量导入导出以及公网云端容器化部署。

---

## ✨ 核心功能特性

1. **⭐ 收藏/星标联系人 (Bookmark Contacts)**
   - 支持一键标记/取消星标收藏联系人，星标联系人在列表中自动置顶高亮展示。
   - 提供顶部统计卡片与 **“⭐ 收藏夹 (Favorites)”** 专属筛选标签页，方便快速定位重要联系人。

2. **📇 多种联系方式管理 (Multiple Contact Methods)**
   - 单个联系人支持绑定任意数量的 **电话号码**、**电子邮箱**、**社交账号（微信/GitHub/QQ 等）** 与 **联系地址**。
   - 每条联系方式均可自定义标签（如“工作手机”、“备用号”、“学校邮箱”、“办公地址”），前端表单支持动态增删行。

3. **📊 Excel 导入与导出 (Excel Import & Export)**
   - **导出 (`.xlsx`)**：将所有（或当前筛选的）联系人按“一人一行、一类信息一列”导出为带样式排版的 Excel 表格。
   - **导入 (`.xlsx`)**：支持上传标准格式 Excel 表格批量导入联系人及多条联系方式，并提供 **标准导入模板下载**。

4. **☁️ 云端容器化部署 (Cloud Deployment)**
   - 内置 `Dockerfile`、`docker-compose.yml` 与 `Gunicorn` 生产级配置，支持挂载持久化 SQLite 数据卷一键部署至阿里云 / 华为云 ECS。

---

## 📂 项目目录结构

```text
xp-address-book/
├── app.py                  # Flask 应用主入口与 RESTful API 路由
├── config.py               # 环境配置与数据库路径管理
├── db.py                   # SQLite 数据库表结构定义、种子数据与 CRUD 封装
├── services/
│   └── excel_service.py    # 基于 OpenPyXL 的 Excel 导出、模板生成与导入解析服务
├── templates/
│   └── index.html          # 响应式单页前端界面模板
├── static/
│   ├── css/style.css       # 现代化主题样式与移动端响应式布局
│   └── js/app.js           # 前端状态管理、多联系方式动态表单与异步接口调用
├── tests/
│   └── test_app.py         # Pytest 自动化单元测试套件
├── sample_contacts.xlsx    # 供导入测试使用的示例 Excel 文件
├── CODE_STANDARD.md        # 团队代码规范与 Git 协作约定文档
├── DEPLOY.md               # 阿里云 / 华为云 Docker 部署指南
├── Dockerfile              # Docker 镜像构建文件
├── docker-compose.yml      # Docker Compose 容器编排配置
└── requirements.txt        # Python 依赖包列表
```

---

## 🚀 本地快速运行

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动服务
python app.py
```

浏览器访问：`http://localhost:8080`

---

## 🧪 运行单元测试

```bash
pytest -v
```

---

## 📖 相关文档链接

- [代码规范与协作约定 (CODE_STANDARD.md)](./CODE_STANDARD.md)
- [云服务器部署指南 (DEPLOY.md)](./DEPLOY.md)
