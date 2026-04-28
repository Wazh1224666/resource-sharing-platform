# 高校资源共享平台 - 个性化推荐系统

基于物品的协同过滤算法，为资源分享平台提供个性化推荐服务。

## 功能特性

- **个性化推荐**: 基于用户历史行为（浏览/下载）推荐相关资源
- **相似资源推荐**: 查找与指定资源相似的其他资源
- **热门推荐**: 当用户行为数据不足时，返回热门资源
- **智能缓存**: 使用Redis缓存推荐结果，提高响应速度
- **自动训练**: 支持定时重新训练模型，适应数据变化
- **RESTful API**: 提供标准的HTTP接口，易于集成

## 系统架构

```
用户请求 → Java后端 → 推荐服务API → 返回推荐结果
                     ↓
                Redis缓存（加速）
                     ↓
                MySQL数据库（行为数据）
                     ↓
             协同过滤模型（scikit-learn）
```

## 技术栈

- **后端框架**: Flask (Python)
- **机器学习**: scikit-learn, pandas, numpy
- **数据库**: MySQL (行为数据), Redis (缓存)
- **容器化**: Docker, Docker Compose

## 快速开始

### 1. 环境准备

```bash
# 克隆项目
cd recommendation-system

# 复制环境变量文件
cp .env.example .env

# 编辑.env文件，配置数据库连接信息
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 启动服务

```bash
# 开发模式
python app.py --host 0.0.0.0 --port 5000 --debug

# 或使用Docker Compose（推荐）
docker-compose up -d
```

### 4. 训练模型

```bash
# 手动训练模型
python app.py --train

# 或通过API训练
curl -X POST "http://localhost:5000/train"
```

## API文档

### 健康检查
```
GET /health
```
检查服务状态

### 获取用户推荐
```
GET /recommendations/{user_id}
```
参数：
- `limit` (可选): 返回推荐数量，默认10
- `exclude_viewed` (可选): 是否排除已查看资源，默认true

响应示例：
```json
{
  "success": true,
  "user_id": 1,
  "recommendations": [
    {
      "resource_id": 15,
      "title": "高等数学课件PPT",
      "file_type": "pdf",
      "file_size": 2048576,
      "create_time": "2024-03-15T10:30:00",
      "uploader": "张老师"
    }
  ],
  "count": 1
}
```

### 训练模型
```
POST /train
```
参数：
- `force` (可选): 强制重新训练，默认false

### 获取相似资源
```
GET /similar/{resource_id}
```
参数：
- `limit` (可选): 返回相似资源数量，默认10

### 系统统计
```
GET /stats
```
获取系统运行状态和统计信息

## 集成到Java后端

### 1. 添加推荐服务客户端

在Java项目中创建推荐服务客户端类：

```java
@Service
public class RecommendationServiceClient {
    
    @Value("${recommendation.service.url:http://localhost:5000}")
    private String recommendationServiceUrl;
    
    private final RestTemplate restTemplate;
    
    public List<Resource> getRecommendations(Long userId, int limit) {
        String url = String.format("%s/recommendations/%d?limit=%d", 
            recommendationServiceUrl, userId, limit);
        
        ResponseEntity<RecommendationResponse> response = restTemplate.getForEntity(
            url, RecommendationResponse.class);
        
        if (response.getStatusCode().is2xxSuccessful() && 
            response.getBody() != null && 
            response.getBody().isSuccess()) {
            return convertToResources(response.getBody().getRecommendations());
        }
        
        return Collections.emptyList();
    }
    
    // 其他方法...
}
```

### 2. 添加配置文件

在`application.yml`中添加配置：

```yaml
recommendation:
  service:
    url: http://localhost:5000
    timeout: 5000
    cache-enabled: true
    cache-ttl: 3600
```

### 3. 创建推荐API接口

```java
@RestController
@RequestMapping("/recommendation")
public class RecommendationController {
    
    @Autowired
    private RecommendationServiceClient recommendationService;
    
    @GetMapping("/for-user/{userId}")
    public Result getRecommendations(@PathVariable Long userId,
                                     @RequestParam(defaultValue = "10") int limit) {
        try {
            List<Resource> recommendations = recommendationService.getRecommendations(userId, limit);
            return Result.success(recommendations);
        } catch (Exception e) {
            return Result.error("获取推荐失败: " + e.getMessage());
        }
    }
}
```

## 算法说明

### 基于物品的协同过滤

1. **数据收集**: 收集用户-资源交互行为（浏览、下载）
2. **权重计算**: 
   - 下载行为权重 = 2.0
   - 浏览行为权重 = 1.0
   - 时间衰减：最近行为权重更高
3. **相似度计算**: 使用余弦相似度计算资源间的相似性
4. **推荐生成**: 
   - 找到用户历史交互资源的相似资源
   - 聚合相似度得分
   - 排序返回Top-N推荐

### 冷启动处理

- **新用户**: 返回热门资源
- **新资源**: 基于内容相似性（文件类型、标题关键词）
- **数据稀疏**: 使用混合推荐（协同过滤+热门+随机）

## 部署说明

### 生产环境部署

1. **数据库配置**:
   - 确保MySQL数据库可访问
   - 创建只读用户用于推荐服务
   - 定期备份行为数据

2. **Redis配置**:
   - 设置合适的内存大小
   - 配置持久化策略
   - 监控缓存命中率

3. **服务监控**:
   - 使用Prometheus监控指标
   - 设置日志收集（ELK Stack）
   - 配置告警规则

### 性能优化

1. **缓存策略**:
   - 用户推荐结果缓存1小时
   - 热门资源列表缓存30分钟
   - 模型缓存24小时

2. **批量处理**:
   - 离线训练模型
   - 批量更新缓存
   - 异步计算推荐

3. **数据库优化**:
   - 为行为表添加合适索引
   - 定期清理旧数据
   - 使用读写分离

## 故障排除

### 常见问题

1. **连接数据库失败**
   - 检查数据库配置（.env文件）
   - 验证网络连接
   - 检查数据库用户权限

2. **推荐质量差**
   - 检查行为数据质量
   - 调整算法参数
   - 增加训练数据量

3. **服务响应慢**
   - 检查Redis连接
   - 优化数据库查询
   - 增加服务实例

### 日志查看

```bash
# 查看服务日志
docker-compose logs recommendation-service

# 查看模型训练日志
docker-compose logs model-trainer

# 查看Redis日志
docker-compose logs redis
```

## 开发指南

### 添加新特征

1. 在`app.py`的`prepare_interaction_matrix`方法中添加新特征
2. 更新模型训练逻辑
3. 测试特征效果

### 扩展算法

1. 创建新的算法类，继承基础接口
2. 在配置中选择算法
3. 测试算法性能

### 添加API端点

1. 在`setup_routes`方法中添加路由
2. 实现对应的业务逻辑
3. 更新API文档

## 许可证

本项目仅供毕业设计使用，遵循学术诚信原则。