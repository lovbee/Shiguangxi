package com.quanxiaoha.xiaohashu.auth;

import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.redis.core.RedisTemplate;


@SpringBootTest
@Slf4j
class RedisTests {

    @Resource
    private RedisTemplate<String, Object> redisTemplate;

    /**
     * 添加 key value
     */
    @Test
    void testSetKeyValue() {
        redisTemplate.opsForValue().set("name", "犬小哈");
    }

    /**
     * 判断某个 key 是否存在
     */
    @Test
    void testHasKey() {
        log.info("key 是否存在：{}", Boolean.TRUE.equals(redisTemplate.hasKey("name")));
    }

    /**
     * 获取某个 key 的 value
     */
    @Test
    void testGetValue() {
        log.info("value 值：{}", redisTemplate.opsForValue().get("name"));
    }

    /**
     * 删除某个 key
     */
    @Test
    void testDelete() {
        redisTemplate.delete("name");
    }



}
