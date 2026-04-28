package com.zhaojiahao.resource.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;
import java.util.List;

/**
 * Python推荐服务响应DTO（Flask jsonify 字段为 snake_case，需显式映射）
 */
@Data
public class PythonRecommendationResponse {
    private Boolean success;
    @JsonProperty("user_id")
    private Long userId;
    private String algorithm;
    private List<RecommendationItem> recommendations;
    private Integer count;

    @Data
    public static class RecommendationItem {
        @JsonProperty("resource_id")
        private Long resourceId;
        private String title;
        @JsonProperty("file_type")
        private String fileType;
        @JsonProperty("file_size")
        private Long fileSize;
        @JsonProperty("create_time")
        private String createTime;
        private String uploader;
    }
}