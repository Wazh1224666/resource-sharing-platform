package com.zhaojiahao.resource.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    // --- 重点：这就是你缺少的跨域配置 Bean ---
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        // 允许的前端来源，使用通配符支持所有本地端口
        configuration.setAllowedOriginPatterns(Arrays.asList("http://localhost:*"));
        // 允许的请求方法
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        // 允许的请求头
        configuration.setAllowedHeaders(Arrays.asList("Authorization", "Content-Type"));
        // 是否允许携带 Cookie
        configuration.setAllowCredentials(true);
        // 暴露的响应头，让前端可以访问
        configuration.setExposedHeaders(Arrays.asList("Content-Disposition"));

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }

    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                // 1. 开启跨域支持，引用上面的 corsConfigurationSource
                .cors(cors -> cors.configurationSource(corsConfigurationSource()))
                // 2. 禁用 CSRF
                .csrf(csrf -> csrf.disable())
                // 3. 设置无状态 Session
                .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                // 4. 配置权限控制
                .authorizeHttpRequests(auth -> auth
                        .requestMatchers("/auth/**", "/resource/**", "/user/**", "/recommendation/**").permitAll() // 业务权限交由拦截器和控制器处理
                        .anyRequest().authenticated()           // 其他都要 Token
                );

        return http.build();
    }
}