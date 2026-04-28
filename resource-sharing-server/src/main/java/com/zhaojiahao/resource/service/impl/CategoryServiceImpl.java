package com.zhaojiahao.resource.service.impl;

import com.baomidou.mybatisplus.extension.service.impl.ServiceImpl;
import com.zhaojiahao.resource.entity.Category;
import com.zhaojiahao.resource.mapper.CategoryMapper;
import com.zhaojiahao.resource.service.CategoryService;
import org.springframework.stereotype.Service;
import java.util.List;

@Service
public class CategoryServiceImpl extends ServiceImpl<CategoryMapper, Category> implements CategoryService {
    @Override
    public List<Category> getAllCategories() {
        return this.list(); // 调用 MyBatis Plus 提供的查询所有方法
    }
}