package com.zhaojiahao.resource.config;

import org.springframework.boot.web.client.RestTemplateBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

import java.time.Duration;

@Configuration
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate(RestTemplateBuilder builder) {
        return builder
                .setConnectTimeout(Duration.ofSeconds(5))  // 连接超时5秒
                .setReadTimeout(Duration.ofSeconds(120))   // 读取超时（含离线评估 /evaluation/compare）
                .build();
    }
}