# 论坛社区 Forum Community

一个基于 **Django 5** 开发的论坛社区网站，包含用户系统、版块发帖、回复互动、站内通知与后台管理等完整功能。

> 本项目配套《技术选型与开发清单》文档，见 [`docs/`](docs/) 目录。

---

## 功能特性

| 模块 | 说明 |
| --- | --- |
| 👤 用户系统 | 自定义用户模型、注册 / 登录 / 退出、个人主页、编辑资料（含头像上传）、积分 |
| 📁 版块 | 版块列表、版块内主题帖列表、分页 |
| 📝 主题帖 | 发帖、编辑、删除、**Markdown 渲染**（代码块 / 表格 / 引用）、标签、置顶 / 加精 / 关闭 |
| 💬 回复 | 楼层编号、引用回复、`@提及`、删除 |
| ❤️ 互动 | 点赞（主题 + 回复）、收藏、关注用户、举报 |
| 🔔 通知 | 被回复 / 被 @ / 被赞 / 被关注自动通知，导航栏未读角标 |
| 🔍 搜索 | 标题 + 正文关键词搜索 |
| 🛡️ 后台 | Django Admin：内容管理、举报处理、用户封禁 |

---

## 技术栈

- **后端**：Python 3.13 + Django 5.2
- **数据库**：SQLite（开发环境零配置；上线可平滑切换 PostgreSQL）
- **模板**：Django Template + 原生 CSS（响应式）
- **内容渲染**：`markdown` + `bleach`（白名单过滤，防 XSS）
- **图片处理**：Pillow（头像上传）

---

## 快速开始

### 1. 环境要求

- Python 3.11 及以上
- Git

### 2. 克隆项目

```bash
git clone https://github.com/wanshunzhong-ai/forum-community.git
cd forum-community
```

### 3. 创建虚拟环境并安装依赖

**Windows（PowerShell / CMD）**

```bat
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. 初始化数据库

```bash
python manage.py migrate
```

### 5. 生成演示数据（可选，推荐新手先跑一遍）

```bash
python manage.py seed_demo
```

### 6. 启动服务

```bash
python manage.py runserver
```

浏览器打开 <http://127.0.0.1:8000> 即可访问。

后台管理地址：<http://127.0.0.1:8000/admin>

---

## 演示账号

> ⚠️ 以下账号由 `seed_demo` 命令生成，**仅用于本地演示，请勿在任何正式环境使用**。

| 角色 | 用户名 | 密码 |
| --- | --- | --- |
| 管理员 | `admin` | `admin123456` |
| 普通用户 | `zhangsan` | `test123456` |

---

## 常用命令

```bash
python manage.py runserver      # 启动开发服务器
python manage.py migrate        # 应用数据库迁移
python manage.py makemigrations # 模型改动后生成迁移文件
python manage.py seed_demo      # 生成演示数据
python manage.py createsuperuser # 创建新的管理员账号
python manage.py check          # 检查项目配置
```

---

## 目录结构

```
forum-community/
├── apps/                  # 业务应用
│   ├── users/             # 用户系统（自定义 User 模型、关注关系）
│   └── forum/             # 论坛核心（版块 / 主题 / 回复 / 互动 / 通知）
├── config/                # 项目配置
│   ├── settings.py        # 总配置
│   └── urls.py            # 路由入口
├── docs/                  # 项目文档（技术选型与开发清单）
├── templates/             # HTML 模板
│   ├── base.html          # 全站公共骨架
│   ├── forum/             # 论坛页面
│   └── users/             # 用户页面
├── static/css/style.css   # 全站样式
├── manage.py              # Django 管理命令入口
└── requirements.txt       # 依赖清单
```

---

## 开发路线图

- [x] **M1** 项目脚手架与基础设施
- [x] **M2** 用户系统（注册 / 登录 / 资料 / 权限）
- [x] **M3** 版块与主题帖（发帖 / 回帖主流程）
- [x] **M4** 互动与社交（点赞 / 收藏 / 关注 / 通知 / 举报）
- [x] **M5** 搜索与信息流（基础关键词搜索）
- [ ] **M6** 内容审核增强（敏感词过滤、图片机审）
- [ ] **M7** 前端体验优化（深色模式、SEO、移动端细节）
- [ ] **M8** 性能与稳定性（缓存、索引、CDN）
- [ ] **M9** 部署上线（PostgreSQL + Docker + Nginx）

---

## 许可证

本项目暂未指定开源许可证。如需他人自由使用，建议补充 `LICENSE` 文件（例如 MIT）。
