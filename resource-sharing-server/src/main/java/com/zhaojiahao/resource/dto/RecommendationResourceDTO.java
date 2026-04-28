package com.zhaojiahao.resource.dto;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 推荐资源DTO
 */
@Data
public class RecommendationResourceDTO {
    private Long resourceId;
    private String title;
    private String fileType;
    private Long fileSize;
    private LocalDateTime createTime;
    private String uploader;

    // 推荐相关字段
    private Double similarityScore;  // 相似度得分
    private String recommendationReason;  // 推荐理由
}