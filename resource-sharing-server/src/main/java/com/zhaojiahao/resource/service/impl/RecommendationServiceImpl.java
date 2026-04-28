package com.zhaojiahao.resource.service.impl;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.zhaojiahao.resource.dto.PythonRecommendationResponse;
import com.zhaojiahao.resource.dto.RecommendationResourceDTO;
import com.zhaojiahao.resource.entity.Resource;
import com.zhaojiahao.resource.mapper.ResourceMapper;
import com.zhaojiahao.resource.service.RecommendationService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClientException;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
public class RecommendationServiceImpl implements RecommendationService {

    @Value("${recommendation.service.url:http://localhost:5000}")
    private String recommendationServiceUrl;

    @Value("${recommendation.service.enabled:true}")
    private boolean recommendationEnabled;

    @Autowired
    private RestTemplate restTemplate;

    @Autowired
    private ResourceMapper resourceMapper;

    @Autowired
    private ObjectMapper objectMapper;

    @Override
    public List<RecommendationResourceDTO> getPersonalizedRecommendations(Long userId, int limit, String algorithm) {
        if (!recommendationEnabled || !isServiceAvailable()) {
            log.warn("推荐服务不可用，返回热门资源");
            return getPopularResources(limit);
        }

        String algo = normalizeAlgorithm(algorithm);

        try {
            String url = String.format("%s/recommendations/%d?limit=%d&exclude_viewed=true&algorithm=%s",
                    recommendationServiceUrl, userId, limit, algo);

            ResponseEntity<PythonRecommendationResponse> response = restTemplate.getForEntity(
                    url, PythonRecommendationResponse.class);

            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                PythonRecommendationResponse body = response.getBody();
                if (Boolean.TRUE.equals(body.getSuccess())) {
                    log.info(
                            "Python推荐 userId={} algorithm={} count={}",
                            userId,
                            algo,
                            body.getRecommendations() != null ? body.getRecommendations().size() : 0
                    );
                    return convertToRecommendationDTOs(body.getRecommendations(), "个性化推荐");
                }
            }

            log.warn("推荐服务返回失败，使用备用方案");
            return getFallbackRecommendations(limit);

        } catch (RestClientException e) {
            log.error("调用推荐服务失败: {}", e.getMessage());
            return getFallbackRecommendations(limit);
        } catch (Exception e) {
            log.error("获取推荐发生未知错误", e);
            return getFallbackRecommendations(limit);
        }
    }

    @Override
    public List<RecommendationResourceDTO> getSimilarResources(Long resourceId, int limit) {
        if (!recommendationEnabled || !isServiceAvailable()) {
            log.warn("推荐服务不可用，返回随机资源");
            return getRandomResources(limit);
        }

        try {
            String url = String.format("%s/similar/%d?limit=%d",
                    recommendationServiceUrl, resourceId, limit);

            ResponseEntity<PythonRecommendationResponse> response = restTemplate.getForEntity(
                    url, PythonRecommendationResponse.class);

            if (response.getStatusCode() == HttpStatus.OK && response.getBody() != null) {
                PythonRecommendationResponse body = response.getBody();
                if (Boolean.TRUE.equals(body.getSuccess())) {
                    return convertToRecommendationDTOs(body.getRecommendations(), "相似资源");
                }
            }

            return getRandomResources(limit);

        } catch (RestClientException e) {
            log.error("调用相似资源推荐失败: {}", e.getMessage());
            return getRandomResources(limit);
        }
    }

    @Override
    public List<RecommendationResourceDTO> getPopularResources(int limit) {
        try {
            // 查询热门资源：按交互次数排序
            List<Resource> resources = resourceMapper.selectPopularResources(limit);
            return convertResourcesToDTOs(resources, "热门资源");

        } catch (Exception e) {
            log.error("获取热门资源失败", e);
            return getRandomResources(limit);
        }
    }

    @Override
    public boolean triggerModelRetraining() {
        if (!recommendationEnabled || !isServiceAvailable()) {
            return false;
        }

        try {
            String url = String.format("%s/train?force=true", recommendationServiceUrl);
            ResponseEntity<String> response = restTemplate.postForEntity(url, null, String.class);
            return response.getStatusCode() == HttpStatus.OK;
        } catch (Exception e) {
            log.error("触发模型训练失败: {}", e.getMessage());
            return false;
        }
    }

    @Override
    public boolean isServiceAvailable() {
        if (!recommendationEnabled) {
            return false;
        }

        try {
            String url = String.format("%s/health", recommendationServiceUrl);
            ResponseEntity<String> response = restTemplate.getForEntity(url, String.class);
            return response.getStatusCode() == HttpStatus.OK;
        } catch (Exception e) {
            log.debug("推荐服务健康检查失败: {}", e.getMessage());
            return false;
        }
    }

    // ============ 私有方法 ============

    private List<RecommendationResourceDTO> convertToRecommendationDTOs(
            List<PythonRecommendationResponse.RecommendationItem> items,
            String recommendationReason) {

        if (items == null || items.isEmpty()) {
            return Collections.emptyList();
        }

        List<RecommendationResourceDTO> dtos = new ArrayList<>();
        DateTimeFormatter formatter = DateTimeFormatter.ISO_LOCAL_DATE_TIME;

        for (PythonRecommendationResponse.RecommendationItem item : items) {
            RecommendationResourceDTO dto = new RecommendationResourceDTO();
            dto.setResourceId(item.getResourceId());
            dto.setTitle(item.getTitle());
            dto.setFileType(item.getFileType());
            dto.setFileSize(item.getFileSize());
            dto.setUploader(item.getUploader());
            dto.setRecommendationReason(recommendationReason);

            // 解析时间
            if (item.getCreateTime() != null) {
                try {
                    LocalDateTime createTime = LocalDateTime.parse(item.getCreateTime(), formatter);
                    dto.setCreateTime(createTime);
                } catch (Exception e) {
                    log.warn("解析创建时间失败: {}", item.getCreateTime());
                }
            }

            dtos.add(dto);
        }

        return dtos;
    }

    private List<RecommendationResourceDTO> convertResourcesToDTOs(
            List<Resource> resources,
            String recommendationReason) {

        return resources.stream().map(resource -> {
            RecommendationResourceDTO dto = new RecommendationResourceDTO();
            dto.setResourceId(resource.getId());
            dto.setTitle(resource.getTitle());
            dto.setFileType(resource.getFileType());
            dto.setFileSize(resource.getFileSize());
            dto.setCreateTime(resource.getCreateTime());
            dto.setRecommendationReason(recommendationReason);

            // 可以在这里添加获取上传者信息的逻辑
            // dto.setUploader(getUploaderName(resource.getUploaderId()));

            return dto;
        }).collect(Collectors.toList());
    }

    private List<RecommendationResourceDTO> getFallbackRecommendations(int limit) {
        // 备用方案：先尝试热门资源，如果失败则返回随机资源
        try {
            List<RecommendationResourceDTO> popular = getPopularResources(limit);
            if (!popular.isEmpty()) {
                return popular;
            }
        } catch (Exception e) {
            log.warn("获取热门资源失败，使用随机资源");
        }

        return getRandomResources(limit);
    }

    private static String normalizeAlgorithm(String algorithm) {
        if (algorithm == null || algorithm.isBlank()) {
            return "item_cf";
        }
        String a = algorithm.trim().toLowerCase();
        if ("user_cf".equals(a) || "svd".equals(a) || "item_cf".equals(a)) {
            return a;
        }
        return "item_cf";
    }

    private List<RecommendationResourceDTO> getRandomResources(int limit) {
        try {
            // 查询随机资源
            List<Resource> resources = resourceMapper.selectRandomResources(limit);
            return convertResourcesToDTOs(resources, "随机推荐");
        } catch (Exception e) {
            log.error("获取随机资源失败", e);
            return Collections.emptyList();
        }
    }
}