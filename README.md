# 高校资源共享平台

基于 Spring Boot + Vue3 的高校资源共享平台，支持资源上传/下载、用户管理、个性化推荐等功能。

## 系统架构

```
┌─────────────────┐     ┌──────────────────┐     ┌──────────────────┐
│   Vue3 前端      │────▶│  Spring Boot 后端 │────▶│     MySQL 数据库   │
│  (Vite + Axios)  │◀────│  (RESTful API)   │◀────│                  │
└─────────────────┘     └────────┬─────────┘     └──────────────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Flask 推荐服务    │
                        │ (协同过滤算法)      │
                        └──────────────────┘
```

## 技术栈

### 后端 (resource-sharing-server)
- **框架**: Spring Boot 3.4.3, Spring Security, MyBatis Plus 3.5.10.1
- **数据库**: MySQL 8.0+
- **认证**: JWT (jjwt 0.11.5)
- **构建工具**: Maven
- **Java 版本**: 17
- **其他**: Lombok, Spring Validation

### 前端 (resource-share-web)
- **框架**: Vue 3 + Vue Router 5
- **构建**: Vite 8
- **UI 组件库**: Element Plus 2.13
- **HTTP 客户端**: Axios
- **图表**: ECharts 6

### 推荐系统 (recommendation-system)
- **框架**: Flask (Python)
- **算法**: 基于物品的协同过滤 (scikit-learn)
- **缓存**: Redis
- **部署**: Docker / Docker Compose

## 项目结构

```
resource-sharing-platform/
├── resource-sharing-server/    # Spring Boot 后端
│   └── src/main/java/com/zhaojiahao/resource/
│       ├── config/             # 安全配置、跨域配置等
│       ├── controller/         # 控制器层
│       │   ├── AuthController.java      # 认证接口
│       │   ├── UserController.java      # 用户管理
│       │   ├── ResourceController.java  # 资源管理
│       │   ├── CategoryController.java  # 分类管理
│       │   └── RecommendationController.java  # 推荐接口
│       ├── entity/             # 实体类
│       │   ├── User.java               # 用户实体
│       │   ├── Resource.java           # 资源实体
│       │   ├── Category.java           # 分类实体
│       │   └── ResourceUserBehavior.java  # 用户行为
│       ├── service/            # 业务逻辑层
│       ├── mapper/             # MyBatis Plus 映射层
│       ├── dto/                # 数据传输对象
│       ├── common/             # 通用工具类、响应封装
│       └── utils/              # 工具类
│       └── sql/                # SQL 脚本
├── resource-share-web/         # Vue 3 前端
│   └── src/
│       ├── views/              # 页面组件
│       ├── router/             # 路由配置
│       ├── components/         # 公共组件
│       ├── utils/              # 工具函数
│       └── styles/             # 样式文件
├── recommendation-system/      # Python 推荐服务
│   ├── app.py                  # Flask 应用
│   ├── Dockerfile              # Docker 配置
│   └── docker-compose.yml      # Docker Compose 编排
├── chinakaoyan_scraper.py      # 考研资料爬虫
└── uploads/                    # 文件上传目录
```

## 功能特性

### 用户系统
- 注册/登录（支持 STUDENT、TEACHER、ADMIN 三种角色）
- JWT 认证
- 用户信息管理

### 资源管理
- 资源上传/下载
- 资源分类浏览
- 资源搜索
- 资源可见性控制（公开/私有）

### 推荐系统
- **个性化推荐**: 基于用户历史行为（浏览/下载）推荐相关资源
- **相似资源推荐**: 查找与指定资源相似的其他资源
- **热门推荐**: 用户行为数据不足时，返回热门资源
- **智能缓存**: Redis 缓存推荐结果

### 数据模拟（毕设演示用）
- 支持一键生成模拟数据（教师、学生、资源、行为记录）
- 配置项：`seed.*` 开头的 application.yml 配置

### 考研资料爬虫
- 自动注册/登录 `download.chinakaoyan.com`
- 自动爬取资源列表和下载链接
- 自动下载文件到 `downloads/` 目录

## 快速开始

### 环境要求
- JDK 17+
- Maven 3.8+
- Node.js 18+
- MySQL 8.0+
- Python 3.10+（推荐服务）
- Redis（推荐服务）

### 1. 配置数据库

```sql
-- 创建数据库
CREATE DATABASE resource_db DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 执行建表脚本（按顺序）
-- resource-sharing-server/sql/ 目录下的脚本
```

### 2. 启动后端

```bash
cd resource-sharing-server

# 修改 application.yml 中的数据库连接信息
# 修改 auth.admin-register-key 为安全的密钥

# 编译运行
mvn spring-boot:run
```

后端默认运行在 `http://localhost:8080/api`

### 3. 启动前端

```bash
cd resource-share-web

npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`

### 4. 启动推荐服务（可选）

```bash
cd recommendation-system

pip install -r requirements.txt
python app.py --host 0.0.0.0 --port 5000
```

推荐服务默认运行在 `http://localhost:5000`

或使用 Docker 部署：

```bash
cd recommendation-system
docker-compose up -d
```

## API 概览

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/register` | POST | 用户注册 |
| `/api/user/{id}` | GET | 获取用户信息 |
| `/api/resource/list` | GET | 资源列表 |
| `/api/resource/upload` | POST | 上传资源 |
| `/api/resource/download/{id}` | GET | 下载资源 |
| `/api/category/list` | GET | 分类列表 |
| `/api/recommendation/for-user/{userId}` | GET | 获取推荐资源 |

完整 API 文档请参考各 Controller 中的注解。

## 推荐服务 API

| 端点 | 方法 | 说明 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/recommendations/{user_id}` | GET | 获取用户推荐 |
| `/similar/{resource_id}` | GET | 获取相似资源 |
| `/train` | POST | 训练推荐模型 |
| `/stats` | GET | 系统统计信息 |

## 许可证

本项目仅供学习交流与毕业设计使用，遵循学术诚信原则。
