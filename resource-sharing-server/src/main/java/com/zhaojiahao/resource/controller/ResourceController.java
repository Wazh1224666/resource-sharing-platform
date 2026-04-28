package com.zhaojiahao.resource.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.zhaojiahao.resource.common.Result;
import com.zhaojiahao.resource.dto.PageResult;
import com.zhaojiahao.resource.dto.ResourceStatisticsDTO;
import com.zhaojiahao.resource.entity.Resource;
import com.zhaojiahao.resource.entity.ResourceUserBehavior;
import com.zhaojiahao.resource.entity.User;
import com.zhaojiahao.resource.mapper.ResourceMapper;
import com.zhaojiahao.resource.mapper.ResourceUserBehaviorMapper;
import com.zhaojiahao.resource.mapper.UserMapper;
import com.zhaojiahao.resource.service.impl.ResourceUserBehaviorServiceImpl;
import com.zhaojiahao.resource.utils.JwtUtils; // 确保你有这个工具类
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.File;
import java.io.IOException;
import java.net.URLEncoder;
import java.nio.file.Files;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.stream.Collectors;

@CrossOrigin
@RestController
@RequestMapping("/resource")
public class ResourceController {

    @Value("${file.upload-path}")
    private String uploadPath;

    @Autowired
    private ResourceMapper resourceMapper;

    @Autowired
    private ResourceUserBehaviorServiceImpl behaviorService;

    @Autowired
    private ResourceUserBehaviorMapper resourceUserBehaviorMapper;

    @Autowired
    private UserMapper userMapper;

    /**
     * 上传资源 - 关联当前登录用户
     */
    @PostMapping("/upload")
    public Result upload(@RequestParam("file") MultipartFile file,
                         @RequestParam(value = "title", required = false) String title,
                         @RequestParam(value = "visibility", required = false) String visibility,
                         HttpServletRequest request) { // 注入 request 获取 Header

        if (file.isEmpty()) return Result.error("文件不能为空");

        String role = (String) request.getAttribute("userRole");
        if (!"TEACHER".equals(role) && !"ADMIN".equals(role)) {
            return Result.forbidden("当前角色无上传权限");
        }

        // 1. 从请求头解析当前登录的用户ID
        String token = request.getHeader("Authorization");
        Long userId;
        try {
            token = normalizeToken(token);
            // 注意：这里调用你 JwtUtils 中解析 ID 的方法
            userId = JwtUtils.getUserIdFromToken(token);
        } catch (Exception e) {
            return Result.unauthorized("登录已过期，请重新登录");
        }

        try {
            File folder = new File(uploadPath);
            if (!folder.exists()) folder.mkdirs();

            String originalFilename = file.getOriginalFilename();
            String suffix = "";
            if (originalFilename != null && originalFilename.contains(".")) {
                suffix = originalFilename.substring(originalFilename.lastIndexOf("."));
            }

            String newFileName = UUID.randomUUID().toString() + suffix;
            File dest = new File(folder, newFileName);
            file.transferTo(dest);

            // 2. 封装实体类存入数据库
            Resource res = new Resource();
            res.setTitle((title == null || title.trim().isEmpty()) ? originalFilename : title);
            res.setFileName(newFileName);
            res.setFilePath(dest.getAbsolutePath());
            res.setFileSize(file.getSize());
            res.setFileType(suffix.replace(".", "").toLowerCase());
            res.setUploaderId(userId); // 使用解析出的真实用户ID
            resourceMapper.insert(res);
            return Result.success("上传成功");
        } catch (IOException e) {
            e.printStackTrace();
            return Result.error("文件保存异常");
        }
    }

    /**
     * 获取资源列表
     */
    /**
     * 获取资源列表（支持搜索和个人筛选）
     */
    @GetMapping("/list")
    public Result list(@RequestParam(required = false) String query,
                       @RequestParam(required = false) Boolean onlyMine,
                       @RequestParam(required = false) String type,
                       @RequestParam(required = false) String sort,
                       @RequestParam(defaultValue = "1") long current,
                       @RequestParam(defaultValue = "15") long size,
                       HttpServletRequest request) {
        System.out.println("[DEBUG] /resource/list called: query=" + query + ", onlyMine=" + onlyMine + ", type=" + type + ", sort=" + sort + ", current=" + current + ", size=" + size);
        Long userId = (Long) request.getAttribute("userId");
        String userRole = (String) request.getAttribute("userRole");
        System.out.println("[DEBUG] Request attributes - userId: " + userId + ", userRole: " + userRole);
        String authHeader = request.getHeader("Authorization");
        System.out.println("[DEBUG] Authorization header present: " + (authHeader != null));

        if (current < 1) {
            current = 1;
        }
        if (size < 1) {
            size = 15;
        }
        if (size > 100) {
            size = 100;
        }
        QueryWrapper<Resource> wrapper = buildResourceQueryWrapper(query, onlyMine, type, sort, request);
        long total = resourceMapper.selectCount(wrapper);
        long offset = (current - 1) * size;
        wrapper.last("LIMIT " + offset + ", " + size);
        List<Resource> records = resourceMapper.selectList(wrapper);
        PageResult<Resource> body = new PageResult<>(records, total, current, size);
        return Result.success(body);
    }

    private QueryWrapper<Resource> buildResourceQueryWrapper(String query, Boolean onlyMine, String type, String sort, HttpServletRequest request) {
        QueryWrapper<Resource> wrapper = new QueryWrapper<>();
        Long currentUserId = (Long) request.getAttribute("userId");
        System.out.println("[DEBUG] buildResourceQueryWrapper: query=" + query + ", onlyMine=" + onlyMine + ", type=" + type + ", sort=" + sort + ", currentUserId=" + currentUserId);

        if (query != null && !query.trim().isEmpty()) {
            wrapper.like("title", query);
        }

        if (onlyMine != null && onlyMine) {
            Long userId = currentUserId;
            if (userId == null) {
                try {
                    String token = request.getHeader("Authorization");
                    System.out.println("[DEBUG] Authorization header: " + (token != null ? "present" : "null"));
                    if (token != null) {
                        token = normalizeToken(token);
                        userId = JwtUtils.getUserIdFromToken(token);
                        System.out.println("[DEBUG] Extracted userId from token: " + userId);
                    }
                } catch (Exception e) {
                    System.out.println("[DEBUG] Error extracting userId from token: " + e.getMessage());
                    e.printStackTrace();
                    // 如果无法获取用户ID，返回空查询结果而不是抛出异常
                    wrapper.eq("uploader_id", -1); // 返回空结果
                    return wrapper;
                }
            }
            if (userId != null) {
                wrapper.eq("uploader_id", userId);
                System.out.println("[DEBUG] Filtering by uploader_id: " + userId);
            } else {
                System.out.println("[DEBUG] No userId available for onlyMine filter");
                wrapper.eq("uploader_id", -1); // 返回空结果
            }
        }

        if (type != null && !type.isEmpty()) {
            if (type.equals("other")) {
                wrapper.notIn("file_type", "pdf", "docx", "doc", "txt", "jpg", "png", "gif", "zip", "rar", "7z");
            } else {
                String[] types = type.split(",");
                wrapper.in("file_type", (Object[]) types);
            }
        }

        // 排序逻辑
        System.out.println("[DEBUG] Sorting logic: sort=" + sort);
        boolean orderApplied = false;
        if (sort != null && !sort.trim().isEmpty()) {
            // sort格式: field_order, 例如 create_time_desc, file_size_asc
            // 从最后一个下划线分割，因为字段名本身可能包含下划线
            int lastUnderscoreIndex = sort.lastIndexOf('_');
            if (lastUnderscoreIndex > 0) {
                String field = sort.substring(0, lastUnderscoreIndex);
                String order = sort.substring(lastUnderscoreIndex + 1);
                System.out.println("[DEBUG] Parsed sort: field=" + field + ", order=" + order);
                if ("create_time".equals(field) || "file_size".equals(field)) {
                    if ("asc".equalsIgnoreCase(order)) {
                        wrapper.orderByAsc(field);
                    } else {
                        wrapper.orderByDesc(field);
                    }
                    orderApplied = true;
                    System.out.println("[DEBUG] Applied sorting: field=" + field + ", order=" + order);
                }
            }
        }
        if (!orderApplied) {
            // 默认按创建时间降序
            System.out.println("[DEBUG] Applied default sorting: create_time desc");
            wrapper.orderByDesc("create_time");
        }
        return wrapper;
    }

    /**
     * 下载资源
     */
    @GetMapping("/download/{id}")
    public void download(@PathVariable Long id, HttpServletRequest request, HttpServletResponse response) {
        System.out.println("[DEBUG] Download request for resource id: " + id);
        Long userId = (Long) request.getAttribute("userId");
        String userRole = (String) request.getAttribute("userRole");
        System.out.println("[DEBUG] User ID from request: " + userId);
        System.out.println("[DEBUG] User Role from request: " + userRole);
        try {
            Resource res = resourceMapper.selectById(id);
            if (res == null) {
                System.out.println("[DEBUG] Resource not found for id: " + id);
                response.setStatus(404);
                response.setContentType("text/plain;charset=UTF-8");
                response.getOutputStream().write("Resource not found".getBytes("UTF-8"));
                return;
            }

            File file = new File(res.getFilePath());
            System.out.println("[DEBUG] File path: " + res.getFilePath());
            System.out.println("[DEBUG] File exists: " + file.exists());
            System.out.println("[DEBUG] File can read: " + file.canRead());
            System.out.println("[DEBUG] File absolute path: " + file.getAbsolutePath());
            System.out.println("[DEBUG] Is directory: " + file.isDirectory());
            if (!file.exists()) {
                response.setStatus(404);
                response.setContentType("text/plain;charset=UTF-8");
                response.getOutputStream().write("File not found on server".getBytes("UTF-8"));
                return;
            }

            if (!file.canRead()) {
                System.out.println("[DEBUG] File cannot be read, user role: " + userRole);
                // 如果是管理员，允许继续尝试下载（可能文件被锁定但仍有访问权限）
                if (!"ADMIN".equals(userRole)) {
                    response.setStatus(403);
                    response.setContentType("text/plain;charset=UTF-8");
                    response.getOutputStream().write("File cannot be read (permission denied)".getBytes("UTF-8"));
                    return;
                }
                // 管理员继续尝试下载
                System.out.println("[DEBUG] Admin override: attempting download despite canRead() false");
            }

            // 设置下载头（注意：不能调用 response.reset()，否则会清除 CORS 头）
            String fileName = URLEncoder.encode(res.getTitle(), "UTF-8").replaceAll("\\+", "%20");
            response.setHeader("Content-Disposition", "attachment; filename=\"" + fileName + "\"");
            response.setContentType("application/octet-stream");
            response.setContentLength((int) file.length());

            // CORS头部由SecurityConfig统一处理，无需手动设置
            // response.setHeader("Access-Control-Allow-Origin", "http://localhost:5173");
            // response.setHeader("Access-Control-Allow-Credentials", "true");
            // response.setHeader("Access-Control-Expose-Headers", "Content-Disposition");

            Files.copy(file.toPath(), response.getOutputStream());
            response.getOutputStream().flush();

            // 记录用户下载行为（用于推荐系统）
            recordUserBehavior(id, request, "DOWNLOAD");
            System.out.println("[DEBUG] Download completed successfully for id: " + id);
        } catch (Exception e) {
            e.printStackTrace();
            try {
                response.setStatus(500);
                response.setContentType("text/plain;charset=UTF-8");
                response.getOutputStream().write(("Download failed: " + e.getMessage()).getBytes("UTF-8"));
            } catch (IOException ex) {
                ex.printStackTrace();
            }
        }
    }

    /**
     * 浏览资源（记录VIEW行为）
     */
    @GetMapping("/view/{id}")
    public Result view(@PathVariable Long id, HttpServletRequest request) {
        System.out.println("[DEBUG] View request for resource id: " + id);
        Long userId = (Long) request.getAttribute("userId");
        String userRole = (String) request.getAttribute("userRole");
        System.out.println("[DEBUG] View - userId: " + userId + ", userRole: " + userRole);
        Resource res = resourceMapper.selectById(id);
        if (res == null) {
            return Result.error("资源不存在");
        }

        // 记录用户浏览行为（用于推荐系统）
        recordUserBehavior(id, request, "VIEW");

        return Result.success(res);
    }

    /**
     * 删除资源
     */
    @DeleteMapping("/delete/{id}")
    public Result delete(@PathVariable Long id, HttpServletRequest request) {
        Resource res = resourceMapper.selectById(id);
        if (res == null) return Result.error("资源不存在");

        String role = (String) request.getAttribute("userRole");
        Long currentUserId = (Long) request.getAttribute("userId");
        if (currentUserId == null) {
            return Result.unauthorized("未获取到登录用户信息");
        }

        // 管理员可删除全部；教师仅可删除自己上传的资源；学生不可删除
        boolean canDelete = "ADMIN".equals(role) || ("TEACHER".equals(role) && currentUserId.equals(res.getUploaderId()));
        if (!canDelete) {
            return Result.forbidden("当前角色无删除权限");
        }

        // 1. 删除磁盘物理文件
        File file = new File(res.getFilePath());
        if (file.exists()) {
            file.delete();
        }

        // 2. 删除数据库记录
        resourceMapper.deleteById(id);
        return Result.success("删除成功");
    }

    /**
     * 记录用户行为（浏览或下载）
     */
    private void recordUserBehavior(Long resourceId, HttpServletRequest request, String actionType) {
        try {
            Long userId = (Long) request.getAttribute("userId");
            if (userId == null) {
                // 如果未获取到用户ID，尝试从token解析
                String token = request.getHeader("Authorization");
                if (token != null) {
                    token = normalizeToken(token);
                    userId = JwtUtils.getUserIdFromToken(token);
                }
            }

            if (userId != null) {
                ResourceUserBehavior behavior = new ResourceUserBehavior();
                behavior.setUserId(userId);
                behavior.setResourceId(resourceId);
                behavior.setActionType(actionType);
                behavior.setCreateTime(java.time.LocalDateTime.now());
                behaviorService.save(behavior);
            }
        } catch (Exception e) {
            // 行为记录失败不应影响主要功能，只记录日志
            e.printStackTrace();
        }
    }

    private String normalizeToken(String token) {
        if (token != null && token.startsWith("Bearer ")) {
            return token.substring(7);
        }
        return token;
    }

    /**
     * 管理员端点：随机化现有资源的上传日期（过去30天内）
     */
    @PostMapping("/admin/randomize-create-time")
    public Result randomizeCreateTime(HttpServletRequest request) {
        String role = (String) request.getAttribute("userRole");
        if (!"ADMIN".equals(role)) {
            return Result.forbidden("需要管理员权限");
        }
        try {
            List<Resource> resources = resourceMapper.selectList(null);
            java.util.Random random = new java.util.Random();
            for (Resource res : resources) {
                long randomDays = random.nextInt(30);
                long randomHours = random.nextInt(24);
                long randomMinutes = random.nextInt(60);
                java.time.LocalDateTime randomCreateTime = java.time.LocalDateTime.now()
                        .minusDays(randomDays)
                        .minusHours(randomHours)
                        .minusMinutes(randomMinutes);
                res.setCreateTime(randomCreateTime);
                resourceMapper.updateById(res);
            }
            return Result.success("成功更新 " + resources.size() + " 个资源的上传日期");
        } catch (Exception e) {
            e.printStackTrace();
            return Result.error("更新失败: " + e.getMessage());
        }
    }

    /**
     * 获取资源统计信息
     */
    @GetMapping("/statistics")
    public Result<ResourceStatisticsDTO> getStatistics(HttpServletRequest request) {
        try {
            ResourceStatisticsDTO statistics = new ResourceStatisticsDTO();

            // 1. 基础统计
            Long totalResources = resourceMapper.selectCount(null);
            statistics.setTotalResources(totalResources);

            // 计算总文件大小
            List<Resource> allResources = resourceMapper.selectList(null);
            Long totalFileSize = allResources.stream()
                    .mapToLong(Resource::getFileSize)
                    .sum();
            statistics.setTotalFileSize(totalFileSize);

            // 总下载和浏览次数
            Long totalDownloads = resourceUserBehaviorMapper.selectCount(
                    new QueryWrapper<ResourceUserBehavior>().eq("action_type", "DOWNLOAD")
            );
            Long totalViews = resourceUserBehaviorMapper.selectCount(
                    new QueryWrapper<ResourceUserBehavior>().eq("action_type", "VIEW")
            );
            statistics.setTotalDownloads(totalDownloads);
            statistics.setTotalViews(totalViews);

            // 2. 按文件类型统计
            List<ResourceStatisticsDTO.FileTypeStat> fileTypeStats = calculateFileTypeStats(allResources);
            statistics.setFileTypeStats(fileTypeStats);

            // 3. 按上传者统计
            List<ResourceStatisticsDTO.UploaderStat> uploaderStats = calculateUploaderStats(allResources);
            statistics.setUploaderStats(uploaderStats);

            // 4. 时间趋势（最近30天）
            List<ResourceStatisticsDTO.DailyStat> dailyStats = calculateDailyStats();
            statistics.setDailyStats(dailyStats);

            // 5. 热门资源
            List<ResourceStatisticsDTO.PopularResource> popularResources = calculatePopularResources();
            statistics.setPopularResources(popularResources);

            // 6. 文件大小分布
            ResourceStatisticsDTO.FileSizeDistribution fileSizeDistribution = calculateFileSizeDistribution(allResources);
            statistics.setFileSizeDistribution(fileSizeDistribution);

            return Result.success(statistics);
        } catch (Exception e) {
            e.printStackTrace();
            return Result.error("获取统计信息失败: " + e.getMessage());
        }
    }

    private List<ResourceStatisticsDTO.FileTypeStat> calculateFileTypeStats(List<Resource> resources) {
        Map<String, Long> countByType = resources.stream()
                .collect(Collectors.groupingBy(
                        Resource::getFileType,
                        Collectors.counting()
                ));

        Map<String, Long> sizeByType = resources.stream()
                .collect(Collectors.groupingBy(
                        Resource::getFileType,
                        Collectors.summingLong(Resource::getFileSize)
                ));

        Long total = (long) resources.size();

        return countByType.entrySet().stream()
                .map(entry -> {
                    ResourceStatisticsDTO.FileTypeStat stat = new ResourceStatisticsDTO.FileTypeStat();
                    stat.setFileType(entry.getKey());
                    stat.setCount(entry.getValue());
                    stat.setTotalSize(sizeByType.getOrDefault(entry.getKey(), 0L));
                    stat.setPercentage(total > 0 ? (entry.getValue() * 100.0 / total) : 0.0);
                    return stat;
                })
                .sorted((a, b) -> Long.compare(b.getCount(), a.getCount()))
                .collect(Collectors.toList());
    }

    private List<ResourceStatisticsDTO.UploaderStat> calculateUploaderStats(List<Resource> resources) {
        Map<Long, Long> countByUploader = resources.stream()
                .collect(Collectors.groupingBy(
                        Resource::getUploaderId,
                        Collectors.counting()
                ));

        Map<Long, Long> sizeByUploader = resources.stream()
                .collect(Collectors.groupingBy(
                        Resource::getUploaderId,
                        Collectors.summingLong(Resource::getFileSize)
                ));

        Long total = (long) resources.size();

        return countByUploader.entrySet().stream()
                .map(entry -> {
                    ResourceStatisticsDTO.UploaderStat stat = new ResourceStatisticsDTO.UploaderStat();
                    stat.setUserId(entry.getKey());

                    // 获取用户名
                    User user = userMapper.selectById(entry.getKey());
                    stat.setUsername(user != null ? user.getUsername() : "未知用户");

                    stat.setResourceCount(entry.getValue());
                    stat.setTotalSize(sizeByUploader.getOrDefault(entry.getKey(), 0L));
                    stat.setPercentage(total > 0 ? (entry.getValue() * 100.0 / total) : 0.0);
                    return stat;
                })
                .sorted((a, b) -> Long.compare(b.getResourceCount(), a.getResourceCount()))
                .limit(10) // 只显示前10个上传者
                .collect(Collectors.toList());
    }

    private List<ResourceStatisticsDTO.DailyStat> calculateDailyStats() {
        List<ResourceStatisticsDTO.DailyStat> dailyStats = new ArrayList<>();
        DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy-MM-dd");

        // 获取最近30天的日期
        for (int i = 29; i >= 0; i--) {
            LocalDate date = LocalDate.now().minusDays(i);
            String dateStr = date.format(formatter);

            ResourceStatisticsDTO.DailyStat stat = new ResourceStatisticsDTO.DailyStat();
            stat.setDate(dateStr);

            // 查询当天的资源数量
            QueryWrapper<Resource> resourceWrapper = new QueryWrapper<>();
            resourceWrapper.apply("DATE(create_time) = '" + dateStr + "'");
            stat.setResourceCount(resourceMapper.selectCount(resourceWrapper));

            // 查询当天的下载和浏览次数
            QueryWrapper<ResourceUserBehavior> behaviorWrapper = new QueryWrapper<>();
            behaviorWrapper.apply("DATE(create_time) = '" + dateStr + "'");

            QueryWrapper<ResourceUserBehavior> downloadWrapper = new QueryWrapper<>();
            downloadWrapper.apply("DATE(create_time) = '" + dateStr + "'");
            downloadWrapper.eq("action_type", "DOWNLOAD");
            stat.setDownloadCount(resourceUserBehaviorMapper.selectCount(downloadWrapper));

            QueryWrapper<ResourceUserBehavior> viewWrapper = new QueryWrapper<>();
            viewWrapper.apply("DATE(create_time) = '" + dateStr + "'");
            viewWrapper.eq("action_type", "VIEW");
            stat.setViewCount(resourceUserBehaviorMapper.selectCount(viewWrapper));

            dailyStats.add(stat);
        }

        return dailyStats;
    }

    private List<ResourceStatisticsDTO.PopularResource> calculatePopularResources() {
        // 获取下载量前10的资源
        QueryWrapper<ResourceUserBehavior> wrapper = new QueryWrapper<>();
        wrapper.select("resource_id, COUNT(*) as download_count")
               .eq("action_type", "DOWNLOAD")
               .groupBy("resource_id")
               .orderByDesc("download_count")
               .last("LIMIT 10");

        List<Map<String, Object>> popularDownloads = resourceUserBehaviorMapper.selectMaps(wrapper);

        return popularDownloads.stream()
                .map(map -> {
                    Long resourceId = ((Number) map.get("resource_id")).longValue();
                    Long downloadCount = ((Number) map.get("download_count")).longValue();

                    Resource resource = resourceMapper.selectById(resourceId);
                    if (resource == null) {
                        return null;
                    }

                    // 获取浏览次数
                    QueryWrapper<ResourceUserBehavior> viewWrapper = new QueryWrapper<ResourceUserBehavior>();
                    viewWrapper.eq("resource_id", resourceId)
                              .eq("action_type", "VIEW");
                    Long viewCount = resourceUserBehaviorMapper.selectCount(viewWrapper);

                    // 获取上传者信息
                    User uploader = userMapper.selectById(resource.getUploaderId());

                    ResourceStatisticsDTO.PopularResource popular = new ResourceStatisticsDTO.PopularResource();
                    popular.setResourceId(resourceId);
                    popular.setTitle(resource.getTitle());
                    popular.setFileType(resource.getFileType());
                    popular.setFileSize(resource.getFileSize());
                    popular.setDownloadCount(downloadCount);
                    popular.setViewCount(viewCount);
                    popular.setUploaderName(uploader != null ? uploader.getUsername() : "未知用户");
                    popular.setCreateTime(resource.getCreateTime().toString());

                    return popular;
                })
                .filter(Objects::nonNull)
                .collect(Collectors.toList());
    }

    private ResourceStatisticsDTO.FileSizeDistribution calculateFileSizeDistribution(List<Resource> resources) {
        ResourceStatisticsDTO.FileSizeDistribution distribution = new ResourceStatisticsDTO.FileSizeDistribution();

        distribution.setSmallCount(resources.stream()
                .filter(r -> r.getFileSize() < 1024 * 1024) // < 1MB
                .count());

        distribution.setMediumCount(resources.stream()
                .filter(r -> r.getFileSize() >= 1024 * 1024 && r.getFileSize() < 10 * 1024 * 1024) // 1MB - 10MB
                .count());

        distribution.setLargeCount(resources.stream()
                .filter(r -> r.getFileSize() >= 10 * 1024 * 1024 && r.getFileSize() < 100 * 1024 * 1024) // 10MB - 100MB
                .count());

        distribution.setHugeCount(resources.stream()
                .filter(r -> r.getFileSize() >= 100 * 1024 * 1024) // > 100MB
                .count());

        return distribution;
    }
}