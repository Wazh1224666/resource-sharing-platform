package com.zhaojiahao.resource.service;

import com.zhaojiahao.resource.dto.RecommendationResourceDTO;
import com.zhaojiahao.resource.entity.Resource;

import java.util.List;

/**
 * 推荐服务接口
 */
public interface RecommendationService {

    /**
     * 获取用户个性化推荐
     *
     * @param userId 用户ID
     * @param limit 推荐数量
     * @return 推荐资源列表
     */
    List<RecommendationResourceDTO> getPersonalizedRecommendations(Long userId, int limit, String algorithm);

    /**
     * 获取相似资源推荐
     *
     * @param resourceId 资源ID
     * @param limit 推荐数量
     * @return 相似资源列表
     */
    List<RecommendationResourceDTO> getSimilarResources(Long resourceId, int limit);

    /**
     * 获取热门资源推荐
     *
     * @param limit 推荐数量
     * @return 热门资源列表
     */
    List<RecommendationResourceDTO> getPopularResources(int limit);

    /**
     * 触发模型重新训练
     *
     * @return 是否成功
     */
    boolean triggerModelRetraining();

    /**
     * 检查推荐服务是否可用
     *
     * @return 服务状态
     */
    boolean isServiceAvailable();
}