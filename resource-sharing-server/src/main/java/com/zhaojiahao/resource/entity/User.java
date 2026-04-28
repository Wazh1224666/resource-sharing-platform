package com.zhaojiahao.resource.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;
import java.time.LocalDateTime;

@Data
@TableName("user")
public class User {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String username;
    private String password;
    private String nickname;
    private String role; // STUDENT, TEACHER, ADMIN
    private String avatar;
    private String email;
    private Integer status; // 1-启用, 0-禁用
    private LocalDateTime createTime;
}