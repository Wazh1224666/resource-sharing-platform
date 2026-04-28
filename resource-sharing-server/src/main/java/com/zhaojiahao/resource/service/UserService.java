package com.zhaojiahao.resource.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.zhaojiahao.resource.entity.User;

public interface UserService extends IService<User> {
    // 根据用户名查找用户
    User getByUsername(String username);
    // 用户注册逻辑
    boolean register(User user);
}