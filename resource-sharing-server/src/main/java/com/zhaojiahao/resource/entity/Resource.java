package com.zhaojiahao.resource.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("resource")
public class Resource {
    @TableId(type = IdType.AUTO)
    private Long id;

    private String title;      // 资源标题
    private String fileName;   // 磁盘文件名
    private String filePath;   // 物理路径
    private Long fileSize;     // 文件大小
    private String fileType;   // 文件类型
    private Long uploaderId;   // 上传者ID
    @TableField(exist = false)
    private String visibility; // PUBLIC / PRIVATE
    private LocalDateTime createTime; // 上传时间
}