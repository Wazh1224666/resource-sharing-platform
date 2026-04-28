package com.zhaojiahao.resource.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.zhaojiahao.resource.common.Result;
import com.zhaojiahao.resource.dto.PageResult;
import com.zhaojiahao.resource.entity.User;
import com.zhaojiahao.resource.mapper.UserMapper;
import com.zhaojiahao.resource.service.UserService;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@CrossOrigin
@RestController
@RequestMapping("/user")
public class UserController {

    @Autowired
    private UserMapper userMapper;

    @Autowired
    private UserService userService;

    @GetMapping("/list")
    public Result list(@RequestParam(required = false) String role,
                       @RequestParam(defaultValue = "1") long current,
                       @RequestParam(defaultValue = "15") long size,
                       HttpServletRequest request) {
        String userRole = (String) request.getAttribute("userRole");
        if (!"ADMIN".equals(userRole)) {
            return Result.forbidden("仅管理员可查看用户列表");
        }

        QueryWrapper<User> qw = new QueryWrapper<User>().orderByDesc("create_time");
        if (role != null && !role.isEmpty()) {
            qw.eq("role", role);
        }

        long total = userMapper.selectCount(qw);
        long offset = (current - 1) * size;
        qw.last("LIMIT " + offset + ", " + size);
        List<User> users = userMapper.selectList(qw);
        List<User> safeUsers = users.stream().peek(u -> u.setPassword(null)).collect(Collectors.toList());

        PageResult<User> body = new PageResult<>(safeUsers, total, current, size);
        return Result.success(body);
    }

    @DeleteMapping("/delete/{id}")
    public Result delete(@PathVariable Long id, HttpServletRequest request) {
        String role = (String) request.getAttribute("userRole");
        Long currentUserId = (Long) request.getAttribute("userId");
        if (!"ADMIN".equals(role)) {
            return Result.forbidden("仅管理员可删除用户");
        }
        if (currentUserId != null && currentUserId.equals(id)) {
            return Result.error("不能删除当前登录的管理员账号");
        }

        User user = userService.getById(id);
        if (user == null) {
            return Result.error("用户不存在");
        }

        userService.removeById(id);
        return Result.success("删除用户成功");
    }
}
