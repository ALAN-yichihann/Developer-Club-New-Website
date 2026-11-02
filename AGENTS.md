# AGENTS.md

面向在本仓库工作的 AI 代理与开发者。**动手前先读本文件**，它描述项目结构、关键业务规则、命令和已知陷阱；产品功能说明见 [README.md](README.md)。

## 1. 项目速览

南京师范大学附属中学开发者社团官网。Django 单体应用，无前后端分离、无 JS 构建步骤。

| 项目 | 取值 |
| --- | --- |
| Python | 3.14+（仓库 `.venv` 为 3.14.6） |
| Django | 6.1 |
| 数据库 | 开发 SQLite，生产 PostgreSQL（psycopg 3） |
| 图片 | Pillow 12.3（验证码、Moment 图片） |
| 环境变量 | python-dotenv 读取项目根 `.env` |
| 生产部署 | gunicorn + WSGI，静态/媒体文件由外部 Web 服务器提供 |
| 语言 | 界面、注释、文档、报错文案统一 **简体中文** |

## 2. 快速开始

```powershell
# 1. 激活仓库既有虚拟环境
.\.venv\Scripts\Activate.ps1

# 2. 提供密钥（development.py 缺此变量会直接 RuntimeError）
$env:DJANGO_SECRET_KEY = "随机密钥"
# 或写入项目根 .env：DJANGO_SECRET_KEY=...

# 3. 建库、建管理员、启动
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- 站点：<http://127.0.0.1:8000/>，后台：<http://127.0.0.1:8000/admin/>
- 生成密钥：`python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- 不要提交 `.env`、`db.sqlite3`、`media/`、`private_media/`、`staticfiles/`（已在 `.gitignore`）

## 3. 目录结构与文件职责

```text
manage.py                        默认 settings = development
developer_club_website/
  settings/base.py               公共配置（应用、中间件、i18n、静态/媒体、日志）
  settings/development.py        DEBUG=True、SQLite、本地 ALLOWED_HOSTS
  settings/production.py         DEBUG=False、PostgreSQL、必需环境变量、安全头、CSP 草案
  urls.py                        挂载 admin 与四个应用，配置后台品牌文案
  wsgi.py / asgi.py              默认 settings = production
website_index/                   首页、社团简介、大事记、活动规划、加入我们、彩蛋、错误页
  templates/website_index/base.html  全站布局（导航、页脚、主题切换、返回顶部）
  templates/400|403|404|500.html 全局错误页
  templates/admin/base_site.html 后台品牌与 admin.css 注入
  static/website_index/{css,js,images}  site.css / admin.css / site.js、社徽与校徽
products/                        作品集与作品的核心业务
  models.py                     Series / Product / AuditLog
  views.py                      列表、详情、新建、编辑、下载
  forms.py                      SeriesForm、EditSeriesForm、ProductForm、EditProductForm、后台表单
  admin.py                      审核后台、权限裁剪、审计日志写入
  validators.py                 上传路径、SHA-256、EXE/ZIP 校验
  storage.py                    PrivateProductStorage（无 URL 的私有文件存储）
  scanning.py                   ClamAV（clamdscan）扫描
  rate_limits.py                上传频率限制
  signals.py                    删除 Product 时清理私有文件
  management/commands/          check_product_integrity、scan_pending_products
  migrations/                   0001–0013（0012 为删除历史公开副本的数据迁移）
users/                           注册、登录、验证码、UserProfile、自定义 UserAdmin
comments/                        社员评论（只读列表 + 后台）
media/                           运行时公开上传目录（Moment 图片）
private_media/                   运行时作品私有目录（不入库、不可直链）
```

## 4. 数据模型

| 模型 | 关键字段与约束 |
| --- | --- |
| `products.Series` | `name` 唯一；`bango` 可选，仅允许 `[a-zA-Z_]`，**非空时唯一**；`owner` 可空（用户删除后 SET_NULL）；`is_approved`。约束：`unique_nonempty_series_bango`、`series_approval_requires_bango`（已审核必须有 bango） |
| `products.Product` | 外键 `series`；`file` 使用私有存储，落盘为 `products/quarantine/YYYY/MM/<uuid>.<ext>`；`original_filename` 保留下载名；`file_sha256`；`scan_status`（`pending/clean/infected/error`）；`scanned_at`；`is_approved` |
| `products.AuditLog` | `actor`、`action`、`model_name`、`object_id`、`details`(JSON)、`ip_address`、`created_at`，后台只读 |
| `users.UserProfile` | 与 `User` 一对一，`related_name='profile'`；`real_name`；`student_id` 唯一 |
| `website_index` | `Intro`、`Development`(大事记)、`Moment`(图片)、`Activity`、`Info`、`Link` |
| `comments.Comment` | `content`、`created_at`(CharField 20)、`creator`(CharField 20) |

## 5. 核心业务规则（改动必须遵守）

### 5.1 用户审核
1. 注册创建 `is_active=False` 的账号 + `UserProfile`，不自动登录，跳转 `register_pending`。
2. 管理员在后台勾选“有效”后才能登录；未激活用户输对密码会看到“你的账户还未被管理员确认，请等候”（`ApprovalAuthenticationForm.clean`）。
3. 密码错误时不暴露审核状态；登录只接受用户名，不接受邮箱。
4. 会话固定 1 小时（`SESSION_COOKIE_AGE`），不随浏览器关闭失效。

### 5.2 审核状态机
- 新建作品集：`is_approved=False`、`bango=None`；由管理员设置唯一 `bango` 并勾选已审核。
- 用户编辑作品集：`form.has_changed()` 为假则保持原状；为真则 `is_approved=False`，**保留旧 bango**，因此旧公开链接立即 404。
- 只能向**已审核**作品集的**所有者**上传作品；其他情况 404。
- 新作品默认未审核；编辑作品或替换文件后重新进入待审核；内容未变化则保持原审核状态。
- 审核作品的前置条件（`AdminProductForm.clean`）：所属作品集已审核且有 `bango`，且 `scan_status == clean`。
- 公开可见性统一为 `product.is_approved && series.is_approved`；个人页只显示已审核内容，并展示待审核数量。

### 5.3 私有文件
- 作品文件**只能**经 `products:download_file`（需已审核）或 `products:admin_download_file`（需 staff）获取；`FileResponse` 附带 `X-Content-Type-Options: nosniff`。
- `PrivateProductStorage` 的 `base_url` 为 `None`，访问 `product.file.url` 会抛 `ValueError`——不要给作品文件拼媒体 URL。
- 替换文件时删除旧文件；删除 `Product` 时由 `post_delete` 信号删除文件。
- `Moment` 图片仍走公开 `MEDIA_ROOT`（开发环境由 `static()` 提供）。

### 5.4 上传校验（`products/validators.py`）
- 白名单扩展名 `.exe` / `.zip`；EXE 校验 `MZ` 头；ZIP 校验结构、路径穿越、盘符、符号链接、加密成员、重复名、危险后缀、文件数量、解压体积、压缩比与 CRC。
- 上限常量 `MAX_PRODUCT_UPLOAD_SIZE = 150 MB`（提示文案写的是 100 MB，见第 12 节）。
- 上传时计算 SHA-256 存入 `file_sha256`，并记录 `original_filename`。

### 5.5 扫描与限流
- `products.scanning.ClamAVScanner` 调用 `clamdscan --fdpass --no-summary`，退出码 0=clean、1=infected、其他=error；找不到命令或超时记为 `error`，**绝不当作 clean**。
- 批量扫描：`python manage.py scan_pending_products --limit N`。
- 上传限流 `upload_rate_limited`：每用户每小时 10 次，返回 429。使用默认 LocMemCache（单进程有效，生产未配置 `CACHES`）。

### 5.6 后台权限矩阵

| 角色 | 用户 | Series | Product | AuditLog | Link / Moment |
| --- | --- | --- | --- | --- | --- |
| superuser | 全权 | 全权 | 全权 | 只读 | 全权 |
| staff | 只能看/改 `is_active`（不能改自己或其他 staff，不能操作 superuser） | 只能改 `bango`、`is_approved`，不能增删 | 只能改 `is_approved`，不能增删 | 只读 | 增删改查 |
| 普通用户 | 无 | 无 | 无 | 无 | 无 |

- `users/admin.py` 会先 `unregister(User)` 再注册自定义 `UserAdmin`，并提供 `UserProfileInline`（真实姓名、学籍号只读）。
- Series/Product 的审核或 `bango` 变化会写入 `AuditLog`（`products/admin.py:log_audit`）。

## 6. URL 一览

| 路径 | 视图 | 说明 |
| --- | --- | --- |
| `/` | `website_index:index` | 首页，随机 3 张 Moment + 最新 3 个已审核作品 |
| `/intros/`、`/history/`、`/activities/`、`/joinus/` | `website_index:*` | 社团信息页 |
| `/haruhi/`、`/haruhi/cn/` | `website_index:haruhi*` | 彩蛋页 |
| `/comments/` | `comments:comment_list` | 社员评论列表 |
| `/products/` | `products:all_products` | 公开作品集列表 |
| `/products/my_works/` | `products:my_works` | 个人已审核作品集（登录） |
| `/products/new_series/` | `products:new_series` | 新建作品集（登录） |
| `/products/<bango>/` | `products:single_series` | 公开作品集详情 |
| `/products/my_works/<bango>/` | `products:my_single_series` | 个人作品集详情（所有者） |
| `/products/my_works/<bango>/edit` | `products:edit_single_series` | 编辑作品集（注意无尾斜杠） |
| `/products/my_works/<bango>/new_work/` | `products:new_product` | 上传作品 |
| `/products/my_works/<bango>/<id>/edit/` | `products:edit_product` | 编辑作品 |
| `/products/download/<id>/` | `products:download_file` | 公开下载（需审核） |
| `/products/admin-download/<id>/` | `products:admin_download_file` | 审核下载（staff） |
| `/users/register/`、`/users/login/`、`/users/captcha/` | `users:*` | 注册、登录、验证码 |
| `/admin/` | Django admin | 管理后台 |

模板中请始终用 `{% url %}` 反向解析，不要硬编码路径（`edit_single_series` 无尾斜杠这类细节尤其明显）。

## 7. 前端约定

- 模板放在各应用 `templates/<app>/`；页面继承 `website_index/base.html`，自定义控件模板放 `templates/<app>/widgets/`。
- 样式全部手写在 `website_index/static/website_index/css/site.css` 与 `admin.css`，**没有** npm/打包流程；新增交互写在 `site.js`（IIFE + 可选链，无框架）。
- 主题通过 `<html data-theme="light|dark">` + CSS 变量实现，`localStorage.theme` 记忆；深色模式改动要同时验证两套配色。
- 后台品牌在 `developer_club_website/urls.py`（`site_header` 等）与 `website_index/templates/admin/base_site.html`。
- 所有面向用户的文案使用简体中文，并沿用现有措辞风格。

## 8. 设置与部署

- `manage.py` 用 `development`；`wsgi.py`/`asgi.py` 用 `production`（gunicorn 默认即生产配置）。
- 开发必需环境变量：`DJANGO_SECRET_KEY`。
- 生产必需环境变量（缺一即启动失败）：`DJANGO_SECRET_KEY`、`DJANGO_ALLOWED_HOSTS`、`DJANGO_CSRF_TRUSTED_ORIGINS`、`DB_NAME`、`DB_USER`、`DB_PASSWORD`、`DB_HOST`、`DB_PORT`（可选，默认 5432）、`DJANGO_STATIC_ROOT`、`DJANGO_MEDIA_ROOT`、`DJANGO_PRIVATE_MEDIA_ROOT`。
- 生产已启用 SSL 重定向、安全 Cookie、HSTS 一年、`X_FRAME_OPTIONS=DENY` 等；`CSP_REPORT_ONLY`/`CSP_POLICY` 只是草案，**未接中间件，不会发送响应头**。启用前需验证后台内联脚本与媒体图片。
- 生产不得使用 SQLite，`private_media` 必须位于 Web 根目录之外。

## 9. 常用命令

```powershell
python manage.py check
python manage.py test
python manage.py test products users website_index
python manage.py makemigrations
python manage.py migrate
python manage.py check_product_integrity     # 有问题退出码 1，只报告不修改
python manage.py scan_pending_products --limit 20
python -m pip_audit -r requirements.txt      # 依赖漏洞扫描（需 requirements-dev.txt）
```

`check_product_integrity` 检查：重复 bango、已审核但缺 bango 的作品集、丢失的私有文件、缺少 `UserProfile` 的用户。

## 10. 测试

- 测试文件：`products/tests.py`、`users/tests.py`、`website_index/tests.py`；`comments/tests.py` 仍为空。
- 覆盖：注册/激活提示/邮箱必填/学籍号唯一/验证码、登录会话、后台资料展示与 staff 权限边界、作品上传与编辑、审核状态与可见性、下载与私有文件、校验器、扫描结果、限流、审计日志、后台样式与链接。
- 测试用 `TemporaryDirectory` + `override_settings(PRIVATE_MEDIA_ROOT=...)` 隔离文件；新增涉及私有存储的测试请沿用该写法，并在 `tearDown` 中清理。
- 修改审核/可见性逻辑后，至少跑 `products` 与 `users` 两组测试；只改前台模板时至少跑 `website_index`。
- 注意：在受限沙箱（如 DSH 只读/工作区沙箱）中 `manage.py test` 可能因 `tempfile` 需要 `chmod` 而报 `PermissionError`，这是执行环境限制而非代码缺陷；本地或放开权限的环境运行即可。

## 11. 修改代码的约定

1. **先读后写**：改模型/视图前先读 `models.py`、`views.py`、`admin.py` 与对应模板，保持现有分层（视图瘦、表单校验、后台审计）。
2. **迁移**：改字段必须 `makemigrations`，并检查生成的约束名与 `RunPython` 反向操作；不要手工改已提交的迁移历史。
3. **审核相关改动**：任何可能让未审核内容泄漏到公开页的分支都是缺陷；公开查询请复用 `is_approved=True` + `bango` 非空的条件。
4. **文件相关改动**：作品文件只能走私有存储与两个下载视图，禁止新增公开直链。
5. **安全**：不要降低上传校验、限流、staff 权限裁剪或审计日志的强度；新增后台操作要同步记录 `AuditLog`。
6. **中文**：注释、文档、表单 `label`、校验错误、模板文案一律简体中文；代码标识符保持英文。
7. **提交**：沿用历史风格，简短中文说明（如“上传作品必须附加文件”）；提交前跑 `manage.py check` 与相关测试。

## 12. 已知问题与陷阱（改到相关代码时一并处理或至少不要加深）

| 现象 | 位置 | 说明 |
| --- | --- | --- |
| 大小上限不一致 | `products/validators.py` | 常量是 150 MB，错误文案与 README 写 100 MB |
| 路径文档不一致 | README vs `product_upload_path` | 实际落盘为 `private_media/products/quarantine/YYYY/MM/`，README 少写了 `quarantine` |
| 重复赋值 | `Series.author = author = models.CharField(...)` | 冗余写法，改动时可清理 |
| 评论模型弱类型 | `comments/models.py` | `created_at`、`creator` 是 `CharField(20)`，且站点只有只读列表，没有提交入口 |
| 默认登录跳转 | `settings/base.py` | 未设 `LOGIN_REDIRECT_URL`；登录模板用隐藏域固定 `next=首页`，直连 POST 无 `next` 时会落到默认 `/accounts/profile/`（404） |
| 限流不如预期 | `products/rate_limits.py` | 依赖默认 LocMemCache，多进程/多实例下失效；生产未配置 `CACHES` |
| 上传体积 | `settings/base.py` | `DATA_UPLOAD_MAX_MEMORY_SIZE=160 MB`、`FILE_UPLOAD_MAX_MEMORY_SIZE=2 MB`，改动上限需同步三处常量与文案 |
| CSP 未生效 | `settings/production.py` | 仅保留策略字典，未接入中间件 |
| 未使用导入 | `products/views.py` | 残留未使用的 `IntegrityError` 导入，触及时顺手清理 |
| SQLite 残留 | 仓库根 | `db.sqlite3` 已忽略，不要提交；本地数据缺失时先 `migrate` |
