package com.zhaojiahao.resource.service.impl;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.zhaojiahao.resource.entity.User;
import com.zhaojiahao.resource.mapper.UserMapper;
import com.zhaojiahao.resource.service.UserService;
import org.springframework.stereotype.Service;

@Service
public class UserServiceImpl extends ServiceImpl<UserMapper, User> implements UserService {

    @Override
    public User getByUsername(String username) {
        return this.getOne(new LambdaQueryWrapper<User>().eq(User::getUsername, username));
    }

    @Override
    public boolean register(User user) {
        // 后续我们要在这里加入 BCrypt 密码加密
        return this.save(user);
    }
}