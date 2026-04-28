package com.zhaojiahao.resource.controller;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.zhaojiahao.resource.common.Result;
import com.zhaojiahao.resource.entity.User;
import com.zhaojiahao.resource.service.UserService;
import com.zhaojiahao.resource.utils.JwtUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;
import java.util.regex.Pattern;

@RestController
@RequestMapping("/auth")
public class AuthController {
    private static final Pattern EMAIL_PATTERN = Pattern.compile("^[A-Za-z0-9+_.-]+@[A-Za-z0-9.-]+$");
    private static final String PASSWORD_REG = "^(?=.*[A-Za-z])(?=.*\\d)[A-Za-z\\d]{6,}$";

    @Autowired
    private UserService userService;
    @Autowired
    private PasswordEncoder passwordEncoder;
    @Autowired
    private JwtUtils jwtUtils;
    @Value("${auth.admin-register-key:}")
    private String adminRegisterKey;

    @PostMapping("/login")
    public Result login(@RequestBody User user) {
        // 1. 根据用户名查询用户（假设你已经写好了这部分逻辑）
        User dbUser = userService.getOne(new QueryWrapper<User>().eq("username", user.getUsername()));

        // 2. 校验密码
        if (dbUser != null && dbUser.getPassword().equals(user.getPassword())) {
            String role = dbUser.getRole() == null ? "STUDENT" : dbUser.getRole();
            String token = jwtUtils.createToken(dbUser.getId(), dbUser.getUsername(), role);

            Map<String, Object> loginResult = new HashMap<>();
            loginResult.put("token", token);

            Map<String, Object> userInfo = new HashMap<>();
            userInfo.put("id", dbUser.getId());
            userInfo.put("username", dbUser.getUsername());
            userInfo.put("nickname", dbUser.getNickname());
            userInfo.put("role", role);
            loginResult.put("userInfo", userInfo);

            return Result.success(loginResult);
        }

        return Result.error("用户名或密码错误");
    }

    @GetMapping("/me")
    public Result me(@RequestHeader("Authorization") String authorization) {
        String token = authorization;
        if (token != null && token.startsWith("Bearer ")) {
            token = token.substring(7);
        }

        if (token == null || !JwtUtils.validateToken(token)) {
            return Result.error("未登录或登录已过期");
        }

        Long userId = JwtUtils.getUserIdFromToken(token);
        User dbUser = userService.getById(userId);
        if (dbUser == null) {
            return Result.error("用户不存在");
        }

        Map<String, Object> userInfo = new HashMap<>();
        userInfo.put("id", dbUser.getId());
        userInfo.put("username", dbUser.getUsername());
        userInfo.put("nickname", dbUser.getNickname());
        userInfo.put("role", dbUser.getRole() == null ? "STUDENT" : dbUser.getRole());
        return Result.success(userInfo);
    }
    /**
     * 注册接口
     */
    @PostMapping("/register")
    public Result register(@RequestBody User user) {
        // 1. 强校验：非空 + 长度 + 复杂度
        if (user.getUsername() == null || user.getUsername().length() < 3) {
            return Result.error("用户名长度至少为3位");
        }

        // 正则表达式：至少6位，包含字母和数字
        if (user.getPassword() == null || !user.getPassword().matches(PASSWORD_REG)) {
            return Result.error("密码必须至少6位且包含字母和数字");
        }
        if (user.getEmail() == null || !EMAIL_PATTERN.matcher(user.getEmail()).matches()) {
            return Result.error("请输入有效邮箱，找回密码需要绑定邮箱");
        }
        String role = user.getRole() == null ? "STUDENT" : user.getRole().trim().toUpperCase();
        if (!"STUDENT".equals(role) && !"TEACHER".equals(role) && !"ADMIN".equals(role)) {
            return Result.error("角色参数非法");
        }

        // 2. 查重
        User existUser = userService.getOne(new QueryWrapper<User>().eq("username", user.getUsername()));
        if (existUser != null) {
            return Result.error("用户名已存在");
        }

        // 3. 高权限角色注册保护
        if ("TEACHER".equals(role) || "ADMIN".equals(role)) {
            String inputKey = user.getNickname();
            if (adminRegisterKey == null || adminRegisterKey.isBlank()) {
                return Result.error("系统未配置管理密钥，暂不支持创建教师/管理员账号");
            }
            if (inputKey == null || !adminRegisterKey.equals(inputKey.trim())) {
                return Result.error("管理密钥错误，无法创建高权限账号");
            }
        }

        // 4. 保存
        user.setRole(role);
        user.setNickname(null); // nickname 字段不用于注册密钥，避免脏数据入库
        if (user.getStatus() == null) {
            user.setStatus(1);
        }
        userService.save(user);
        return Result.success("注册成功");
    }

    @PostMapping("/forgot-password")
    public Result forgotPassword(@RequestBody Map<String, String> body) {
        String username = body.get("username");
        String email = body.get("email");
        String newPassword = body.get("newPassword");

        if (username == null || username.trim().isEmpty()) {
            return Result.error("用户名不能为空");
        }
        if (email == null || !EMAIL_PATTERN.matcher(email).matches()) {
            return Result.error("请输入正确的邮箱");
        }
        if (newPassword == null || !newPassword.matches(PASSWORD_REG)) {
            return Result.error("新密码必须至少6位且包含字母和数字");
        }

        User dbUser = userService.getOne(new QueryWrapper<User>().eq("username", username.trim()));
        if (dbUser == null) {
            return Result.error("用户不存在");
        }
        if (dbUser.getEmail() == null || !dbUser.getEmail().equalsIgnoreCase(email.trim())) {
            return Result.error("用户名与邮箱不匹配");
        }

        dbUser.setPassword(newPassword);
        userService.updateById(dbUser);
        return Result.success("密码重置成功，请使用新密码登录");
    }
}