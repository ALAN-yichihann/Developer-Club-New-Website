# 开发者社团网站

这是南京师范大学附属中学开发者社团网站，基于 Django 6.1 开发，提供社团信息展示、成员注册、作品上传、作品审核和文件下载等功能。

## 功能概览

- 首页、社团介绍、大事记、活动规划和加入我们页面
- 用户注册、登录和退出
- 注册时填写用户名、电子邮箱、真实姓名和学籍号
- 新注册账号需要管理员激活后才能登录
- Series（作品集）和 Product（作品）支持文件上传与编辑
- 作品集和作品需要管理员审核后才会出现在个人页面和公开页面
- 编辑内容后，只有实际发生变化时才需要重新审核
- 作品集的 `bango` 由管理员设置，审核时必须填写唯一代号
- 已审核作品支持文件下载
- Django 管理后台支持用户资料和作品审核

## 技术环境

- Python 3.14+
- Django 6.1
- Pillow 12.3+
- SQLite（默认配置）

项目当前未提供 `requirements.txt`。仓库中的 `.venv` 是本地虚拟环境，不建议直接提交或在生产环境复用。

## 本地运行

在项目根目录执行以下命令。

### 1. 创建或激活虚拟环境

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

安装依赖：

```powershell
python -m pip install "Django>=6.1,<6.2" "Pillow>=12.3,<13"
```

如果使用仓库中已有的环境，可直接运行：

```powershell
.\.venv\Scripts\Activate.ps1
```

### 2. 执行数据库迁移

```powershell
python manage.py migrate
```

迁移会创建用户资料、作品审核字段及相关约束。已有作品会在审核机制迁移中保留为已审核状态。

### 3. 创建管理员

```powershell
python manage.py createsuperuser
```

### 4. 启动开发服务器

```powershell
python manage.py runserver
```

访问：

- 网站首页：<http://127.0.0.1:8000/>
- 管理后台：<http://127.0.0.1:8000/admin/>

开发模式下，上传到 `MEDIA_ROOT` 的文件由 Django 提供访问；生产环境应由 Nginx 或其他 Web 服务器提供媒体文件。

## 主要 URL

| 地址 | 说明 |
| --- | --- |
| `/` | 网站首页 |
| `/products/` | 公开作品集列表 |
| `/products/my_works/` | 当前用户的已审核作品集 |
| `/products/new_series/` | 新建作品集 |
| `/users/register/` | 用户注册 |
| `/users/login/` | 用户登录 |
| `/admin/` | 管理员后台 |
| `/products/download/<product_id>/` | 下载已审核作品文件 |

## 用户与审核流程

### 用户审核

1. 用户提交注册信息。
2. 账号创建为未激活状态，不会自动登录。
3. 管理员在后台“用户”页面查看用户名、真实姓名、学籍号，并在用户详情中查看邮箱。
4. 管理员勾选“有效”后，用户才可以登录并上传或修改作品。

未激活用户使用正确密码登录时，会看到“你的账户还未被管理员确认，请等候”。

### 作品集审核

1. 用户新建作品集时，作品集默认为未审核，`bango` 为空。
2. 管理员在“Series”后台填写唯一的 `bango` 并勾选“已审核”。
3. 审核通过后，作品集才会出现在公开作品页和个人作品页。
4. 用户编辑作品集后，如果内容实际发生变化，作品集会重新变为未审核；原 `bango` 保留，但审核期间不能通过该地址访问。

### 作品审核

1. 用户只能向已审核的作品集上传作品。
2. 新作品默认为未审核，不会出现在作品列表中。
3. 管理员在“Product”后台审核作品。
4. 只有所属作品集已审核且设置了 `bango` 后，作品才能审核通过。
5. 用户编辑作品或替换文件后，作品会重新进入待审核状态；如果提交内容完全没有变化，则保持原审核状态。

## 文件与静态资源

配置位于 `developer_club_website/settings.py`：

```python
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATIC_URL = "/static/"
```

- Product 文件保存到 `media/products/年/月/`
- Moment 图片保存到 `media/website_index/年/月/`
- 静态图片位于应用的 `static/` 目录
- `media/` 中可能包含用户上传内容，不应提交到公开代码仓库

## 测试与检查

```powershell
python manage.py check
python manage.py test
```

当前测试覆盖用户注册、账号激活提示、邮箱必填、登录、后台资料展示、作品上传、作品编辑、审核状态、可见性、文件下载和权限校验。

## 项目结构

```text
developer_club_website/  Django 项目配置、URL 和设置
website_index/           首页及社团信息
products/                作品集、作品、上传、审核和下载
users/                   注册、登录、用户资料和账号审核
comments/                社员评论
media/                   用户上传文件（运行时生成）
manage.py                Django 管理命令入口
db.sqlite3               默认 SQLite 数据库
```

## 生产环境注意事项

- 修改 `SECRET_KEY`，不要使用仓库中的开发密钥。
- 设置 `DEBUG = False`，配置正确的 `ALLOWED_HOSTS`。
- 使用 PostgreSQL 等生产数据库替代 SQLite。
- 使用 Nginx、Apache 或对象存储提供 `STATIC_ROOT` 和 `MEDIA_ROOT` 文件。
- 限制上传文件大小和类型，并定期备份数据库及媒体文件。
- 不要公开展示真实姓名、学籍号等个人信息。
