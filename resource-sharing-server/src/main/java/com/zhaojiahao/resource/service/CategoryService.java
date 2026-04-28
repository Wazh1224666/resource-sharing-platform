package com.zhaojiahao.resource.service;

import com.baomidou.mybatisplus.extension.service.IService;
import com.zhaojiahao.resource.entity.Category;
import java.util.List;

public interface CategoryService extends IService<Category> {
    List<Category> getAllCategories();
}