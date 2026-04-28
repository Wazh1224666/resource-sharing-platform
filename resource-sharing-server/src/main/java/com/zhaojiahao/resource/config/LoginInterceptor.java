package com.zhaojiahao.resource.config;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.zhaojiahao.resource.common.Result;
import com.zhaojiahao.resource.utils.JwtUtils; // 假设你之前已有 JwtUtils
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class LoginInterceptor implements HandlerInterceptor {
    private static final ObjectMapper OBJECT_MAPPER = new ObjectMapper();

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 1. 放行 OPTIONS 请求（跨域预检）
        if ("OPTIONS".equalsIgnoreCase(request.getMethod())) {
            return true;
        }

        // 2. 从请求头获取 Token
        String token = request.getHeader("Authorization");

        // 3. 校验 Token
        // 在 preHandle 方法内

        if (token != null) {
            // 如果 Token 带有 Bearer 前缀，先截取掉
            if (token.startsWith("Bearer ")) {
                token = token.substring(7);
            }

            // 现在再调用校验方法
            if (JwtUtils.validateToken(token)) {
                Long userId = JwtUtils.getUserIdFromToken(token);
                String userRole = JwtUtils.getRoleFromToken(token);
                System.out.println("[DEBUG] LoginInterceptor: userId=" + userId + ", userRole=" + userRole);
                request.setAttribute("userId", userId);
                request.setAttribute("userRole", userRole);
                return true;
            }
        }

        // 4. 校验失败，返回 401 状态码
        response.setStatus(401);
        response.setCharacterEncoding("UTF-8");
        response.setContentType("application/json;charset=UTF-8");
        response.getWriter().write(OBJECT_MAPPER.writeValueAsString(Result.unauthorized("未登录或登录已过期")));
        return false;
    }
}