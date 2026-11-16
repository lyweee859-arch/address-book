# 阿里云 / 华为云 部署指南 (Cloud Deployment Guide)

本文档提供将 **星云智能通讯录 (XP Address Book)** 部署到 **阿里云 ECS** 或 **华为云 ECS** 云服务器的完整傻瓜式步骤（对应作业 **1.4 Web Deployment +15 分** 加分项）。

---

## 第一步：领取云服务器并开放端口（安全组设置）

1. 在 **阿里云（高校学生免费领 / 试用中心）** 或 **华为云（免费体验中心）** 领取一台 Linux 云服务器（推荐系统镜像选择 **Ubuntu 22.04 LTS** 或 **Ubuntu 24.04 LTS**）。
2. 在云服务器控制台找到你的实例，记录下它的 **公网 IP 地址**（例如 `120.xx.xx.xx`）。
3. **关键一步 — 放行 `8080` 端口**：
   - 进入云服务器控制台的 **安全组 (Security Group)** -> **配置规则** -> **入方向 (Inbound Rules)** -> **添加规则**：
   - **协议类型**：自定义 TCP
   - **端口范围**：`8080`（或 `8080/8080`）
   - **授权对象（源地址）**：`0.0.0.0/0`（允许所有公网访问）
   - 点击保存。

---

## 第二步：登录云服务器

在阿里云 / 华为云网页控制台直接点击 **“远程连接 (Workbench / VNC)”** 登录，或者在你自己电脑的 PowerShell 中运行：

```bash
ssh root@你的云服务器公网IP
```

---

## 第三步：拉取仓库并启动网站（二选一）

### 方式一：使用 Docker 一键启动（推荐）

1. 如果云服务器上还没有安装 Docker，运行以下一键安装命令：
   ```bash
   apt update && apt install -y git docker.io docker-compose-v2
   systemctl enable --now docker
   ```

2. 克隆你们的 GitHub 仓库并一键后台启动：
   ```bash
   git clone https://github.com/<你的GitHub用户名>/<你的仓库名>.git
   cd <你的仓库名>
   docker compose up -d --build
   ```

3. 查看运行状态：
   ```bash
   docker compose ps
   ```

---

### 方式二：不使用 Docker，直接用 Python + Gunicorn 后台运行（备用极简方案）

如果云服务器拉取 Docker 镜像较慢，也可以直接用系统自带的 Python 启动（只需 3 条命令）：

```bash
apt update && apt install -y git python3-pip python3-venv
git clone https://github.com/<你的GitHub用户名>/<你的仓库名>.git
cd <你的仓库名>
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
nohup ./venv/bin/gunicorn -w 2 -b 0.0.0.0:8080 app:app > server.log 2>&1 &
```

---

## 第四步：公网访问验证

打开任意浏览器，访问：

```text
http://你的云服务器公网IP:8080
```

即可看到已上线的通讯录系统！将此链接填入你们的 CSDN 作业博客与 GitHub 仓库简介中即可拿下 **15 分云部署加分**。
