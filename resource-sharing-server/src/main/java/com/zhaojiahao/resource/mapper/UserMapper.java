package com.zhaojiahao.resource.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhaojiahao.resource.entity.User;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface UserMapper extends BaseMapper<User> {
    // MyBatis Plus 会自动帮我们实现 findByUsername 等基本操作
}