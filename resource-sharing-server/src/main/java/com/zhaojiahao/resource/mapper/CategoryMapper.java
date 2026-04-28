package com.zhaojiahao.resource.mapper;

import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import com.zhaojiahao.resource.entity.Category;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface CategoryMapper extends BaseMapper<Category> {
    // MyBatis Plus 会自动实现基础增删改查
}