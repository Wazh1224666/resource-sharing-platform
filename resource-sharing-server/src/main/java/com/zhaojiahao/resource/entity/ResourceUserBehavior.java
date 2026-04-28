package com.zhaojiahao.resource.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("resource_user_behavior")
public class ResourceUserBehavior {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long userId;
    private Long resourceId;
    /** VIEW or DOWNLOAD */
    private String actionType;
    private LocalDateTime createTime;
}
