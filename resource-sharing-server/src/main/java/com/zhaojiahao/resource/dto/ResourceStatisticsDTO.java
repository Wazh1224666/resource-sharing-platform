package com.zhaojiahao.resource.dto;

import lombok.Data;
import java.util.List;
import java.util.Map;

@Data
public class ResourceStatisticsDTO {
    // 基础统计
    private Long totalResources;
    private Long totalFileSize; // 总文件大小（字节）
    private Long totalDownloads;
    private Long totalViews;

    // 按文件类型统计
    private List<FileTypeStat> fileTypeStats;

    // 按上传者统计
    private List<UploaderStat> uploaderStats;

    // 时间趋势（最近30天）
    private List<DailyStat> dailyStats;

    // 热门资源（下载量前10）
    private List<PopularResource> popularResources;

    // 文件大小分布
    private FileSizeDistribution fileSizeDistribution;

    @Data
    public static class FileTypeStat {
        private String fileType;
        private Long count;
        private Long totalSize;
        private Double percentage;
    }

    @Data
    public static class UploaderStat {
        private Long userId;
        private String username;
        private Long resourceCount;
        private Long totalSize;
        private Double percentage;
    }

    @Data
    public static class DailyStat {
        private String date; // 格式: YYYY-MM-DD
        private Long resourceCount;
        private Long downloadCount;
        private Long viewCount;
    }

    @Data
    public static class PopularResource {
        private Long resourceId;
        private String title;
        private String fileType;
        private Long fileSize;
        private Long downloadCount;
        private Long viewCount;
        private String uploaderName;
        private String createTime;
    }

    @Data
    public static class FileSizeDistribution {
        private Long smallCount;     // < 1MB
        private Long mediumCount;    // 1MB - 10MB
        private Long largeCount;     // 10MB - 100MB
        private Long hugeCount;      // > 100MB
    }
}