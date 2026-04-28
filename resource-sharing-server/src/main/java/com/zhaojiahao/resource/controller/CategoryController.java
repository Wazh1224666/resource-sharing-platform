package com.zhaojiahao.resource.controller;

import com.zhaojiahao.resource.common.Result;
import com.zhaojiahao.resource.entity.Category;
import com.zhaojiahao.resource.service.CategoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import java.util.List;

@RestController
@RequestMapping("/category")
public class CategoryController {

    @Autowired
    private CategoryService categoryService;

    @GetMapping("/list")
    public Result<List<Category>> list() {
        return Result.success(categoryService.getAllCategories());
    }
}