package com.zhaojiahao.resource.utils;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.stereotype.Component;
import java.security.Key;
import java.util.Date;

@Component
public class JwtUtils {

    // 密钥：注意！在实际项目中，KEY 必须固定，不能每次重启都生成新的，否则重启后旧 Token 会失效
    // 这里为了演示方便使用 secretKeyFor，建议开发中使用固定字符串的 Keys.hmacShaKeyFor
    private static final Key KEY = Keys.secretKeyFor(SignatureAlgorithm.HS256);

    // 过期时间：24小时
    private static final long EXPIRE = 86400000;

    /**
     * 生成 Token
     * 增加 userId 参数，方便后续关联资源上传者
     */
    public String createToken(Long userId, String username) {
        Date now = new Date();
        Date expiration = new Date(now.getTime() + EXPIRE);
        return Jwts.builder()
                .claim("userId", userId) // 将用户ID存入载荷
                .setSubject(username)
                .setIssuedAt(now)
                .setExpiration(expiration)
                .signWith(KEY)
                .compact();
    }

    public String createToken(Long userId, String username, String role) {
        Date now = new Date();
        Date expiration = new Date(now.getTime() + EXPIRE);
        return Jwts.builder()
                .claim("userId", userId)
                .claim("role", role)
                .setSubject(username)
                .setIssuedAt(now)
                .setExpiration(expiration)
                .signWith(KEY)
                .compact();
    }

    /**
     * 校验 Token 是否有效 (新增)
     * 供 LoginInterceptor 调用
     */
    public static boolean validateToken(String token) {
        try {
            Jwts.parserBuilder()
                    .setSigningKey(KEY)
                    .build()
                    .parseClaimsJws(token);
            return true;
        } catch (Exception e) {
            // Token 过期、签名错误、格式不对都会返回 false
            return false;
        }
    }

    /**
     * 从 Token 中获取用户 ID (新增)
     * 供 ResourceController 调用
     */
    public static Long getUserIdFromToken(String token) {
        Claims claims = parseClaims(token);
        // 注意：从 claim 获取的是 Integer，需要转成 Long
        return Long.valueOf(claims.get("userId").toString());
    }

    public static String getRoleFromToken(String token) {
        Claims claims = parseClaims(token);
        Object role = claims.get("role");
        return role == null ? null : role.toString();
    }

    /**
     * 解析 Token 获取用户名
     */
    public String getUsernameFromToken(String token) {
        Claims claims = parseClaims(token);
        return claims.getSubject();
    }

    private static Claims parseClaims(String token) {
        return Jwts.parserBuilder()
                .setSigningKey(KEY)
                .build()
                .parseClaimsJws(token)
                .getBody();
    }
}