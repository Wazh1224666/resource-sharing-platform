package com.zhaojiahao.resource.config;

import com.zhaojiahao.resource.service.SimulatedDataSeedService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.Component;

/**
 * 毕设用：批量生成模拟用户、资源与浏览/下载行为（供协同过滤等实验）。
 * 使用前在 MySQL 执行 sql/resource_user_behavior.sql，并设置 seed.enabled=true。
 */
@Slf4j
@Component
@Order(100)
@RequiredArgsConstructor
@ConditionalOnProperty(prefix = "seed", name = "enabled", havingValue = "true")
public class DataSeedRunner implements ApplicationRunner {

    private final SimulatedDataSeedService simulatedDataSeedService;

    @Override
    public void run(ApplicationArguments args) {
        try {
            simulatedDataSeedService.runSeed();

            // 初始化真实用户行为数据（无论模拟数据是否导入）
            // 这确保真实用户（如admin）也能获得个性化推荐
            try {
                simulatedDataSeedService.initRealUserBehaviors();
            } catch (Exception e) {
                log.warn("初始化真实用户行为数据失败（可忽略，不影响主要功能）", e);
            }
        } catch (Exception e) {
            log.error("模拟数据导入失败（请确认已执行 sql/resource_user_behavior.sql 且库连接正确）", e);
            throw new IllegalStateException(e);
        }
    }
}
