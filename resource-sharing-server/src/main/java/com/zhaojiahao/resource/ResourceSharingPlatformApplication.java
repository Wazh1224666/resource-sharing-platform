package com.zhaojiahao.resource;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.zhaojiahao.resource.mapper")
public class ResourceSharingPlatformApplication {

    public static void main(String[] args) {
        SpringApplication.run(ResourceSharingPlatformApplication.class, args);
    }

}

