package com.zhaojiahao.resource.controller;

import com.zhaojiahao.resource.common.Result;
import com.zhaojiahao.resource.dto.RecommendationResourceDTO;
import com.zhaojiahao.resource.service.RecommendationService;
//import io.swagger.v3.oas.annotations.Operation;
//import io.swagger.v3.oas.annotations.Parameter;
//import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@Slf4j
@CrossOrigin
@RestController
@RequestMapping("/recommendation")
//@Tag(name = "推荐管理", description = "个性化资源推荐接口")
public class RecommendationController {

    @Autowired
    private RecommendationService recommendationService;

    /**
     * 获取当前用户的个性化推荐
     */
    //@Operation(summary = "获取个性化推荐", description = "根据当前用户的浏览和下载历史，推荐相关资源")
    @GetMapping("/personalized")
    public Result getPersonalizedRecommendations(
            @RequestParam(defaultValue = "10") int limit,
            @RequestParam(defaultValue = "item_cf") String algorithm,
            HttpServletRequest request) {

        Long userId = getCurrentUserId(request);
        if (userId == null) {
            return Result.unauthorized("用户未登录");
        }

        try {
            log.info("为用户 {} 获取个性化推荐，数量: {}，算法: {}", userId, limit, algorithm);
            List<RecommendationResourceDTO> recommendations = recommendationService
                    .getPersonalizedRecommendations(userId, limit, algorithm);

            return Result.success("获取推荐成功", recommendations);
        } catch (Exception e) {
            log.error("获取个性化推荐失败，用户ID: {}", userId, e);
            return Result.error("获取推荐失败: " + e.getMessage());
        }
    }

    /**
     * 获取相似资源推荐
     */
    //@Operation(summary = "获取相似资源", description = "根据指定资源，推荐相似的其他资源")
    @GetMapping("/similar/{resourceId}")
    public Result getSimilarResources(
            @PathVariable Long resourceId,
            @RequestParam(defaultValue = "10") int limit) {

        try {
            log.info("获取资源 {} 的相似推荐，数量: {}", resourceId, limit);
            List<RecommendationResourceDTO> recommendations = recommendationService
                    .getSimilarResources(resourceId, limit);

            return Result.success("获取相似资源成功", recommendations);
        } catch (Exception e) {
            log.error("获取相似资源失败，资源ID: {}", resourceId, e);
            return Result.error("获取相似资源失败: " + e.getMessage());
        }
    }

    /**
     * 获取热门资源推荐
     */
    //@Operation(summary = "获取热门资源", description = "获取当前最受欢迎的资源")
    @GetMapping("/popular")
    public Result getPopularResources(
            @RequestParam(defaultValue = "10") int limit) {

        try {
            log.info("获取热门资源推荐，数量: {}", limit);
            List<RecommendationResourceDTO> recommendations = recommendationService
                    .getPopularResources(limit);

            return Result.success("获取热门资源成功", recommendations);
        } catch (Exception e) {
            log.error("获取热门资源失败", e);
            return Result.error("获取热门资源失败: " + e.getMessage());
        }
    }

    /**
     * 手动触发模型重新训练
     * 注意：需要管理员权限
     */
    //@Operation(summary = "重新训练模型", description = "手动触发推荐模型重新训练（需要管理员权限）")
    @PostMapping("/retrain")
    public Result retrainModel(HttpServletRequest request) {
        // 检查权限
        String role = (String) request.getAttribute("userRole");
        if (!"ADMIN".equals(role)) {
            return Result.forbidden("需要管理员权限");
        }

        try {
            log.info("管理员触发模型重新训练");
            boolean success = recommendationService.triggerModelRetraining();

            if (success) {
                return Result.success("模型训练任务已触发");
            } else {
                return Result.error("模型训练触发失败，请检查推荐服务状态");
            }
        } catch (Exception e) {
            log.error("触发模型训练失败", e);
            return Result.error("触发模型训练失败: " + e.getMessage());
        }
    }

    /**
     * 检查推荐服务状态
     */
    //@Operation(summary = "检查服务状态", description = "检查推荐服务是否可用")
    @GetMapping("/status")
    public Result checkServiceStatus() {
        try {
            boolean available = recommendationService.isServiceAvailable();
            return Result.success("服务状态检查完成", available ? "可用" : "不可用");
        } catch (Exception e) {
            log.error("检查服务状态失败", e);
            return Result.error("检查服务状态失败");
        }
    }

    /**
     * 从请求中获取当前用户ID
     */
    private Long getCurrentUserId(HttpServletRequest request) {
        try {
            Object userIdAttr = request.getAttribute("userId");
            return userIdAttr != null ? (Long) userIdAttr : null;
        } catch (Exception e) {
            log.warn("获取用户ID失败", e);
            return null;
        }
    }
}