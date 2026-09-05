package com.quanxiaoha.xiaohashu.auth;

import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;

/**
 * @author: 犬小哈
 * @date: 2024/5/23 15:56
 * @version: v1.0.0
 * @description: TODO
 **/
@SpringBootTest
@Slf4j
public class ThreadPoolTaskExecutorTests {

    @Resource
    private ThreadPoolTaskExecutor threadPoolTaskExecutor;

    /**
     * 测试线程池
     */
    @Test
    void testSubmit() {
        threadPoolTaskExecutor.submit(() -> log.info("异步线程中说: 犬小哈专栏"));
    }
}
