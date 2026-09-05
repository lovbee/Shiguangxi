package com.quanxiaoha.xiaohashu.note.biz;

import cn.hutool.core.util.RandomUtil;
import com.google.common.collect.Lists;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.data.redis.core.script.RedisScript;

import java.util.Collections;
import java.util.List;


@SpringBootTest
@Slf4j
class RedisTests {

    @Resource
    private RedisTemplate redisTemplate;

    /**
     * Set 测试
     */
    @Test
    void testAddSet() {
        // Redis 键
        String key = "myset";

        // 循环添加
        for (int i = 0; i < 10000; i++) {
            // Redis 值，随机一个数值
            int randomNum = RandomUtil.randomInt(90000000);

            redisTemplate.opsForSet().add(key, randomNum);
        }
    }

    /**
     * Bloom 测试
     */
    @Test
    void testAddBloom() {
        // Redis 键
        String key = "mybloom";

        // Lua 脚本
        RedisScript<Long> bfAddScript = new DefaultRedisScript<>(
                "return redis.call('BF.ADD', KEYS[1], ARGV[1])",
                Long.class
        );

        // 循环添加
        for (int i = 0; i < 10000; i++) {
            // Redis 值，随机一个数值
            int randomNum = RandomUtil.randomInt(90000000);

            Long result = (Long) redisTemplate.execute(
                    bfAddScript,
                    Collections.singletonList(key),
                    randomNum
            );
            System.out.println(result);
        }
    }

    /**
     * Bitmap 测试
     */
    @Test
    void testAddBitmap() {
        // Redis 键
        String key = "mybitmap";

        // Lua 脚本
        RedisScript<Long> bfAddScript = new DefaultRedisScript<>(
                "return redis.call('SETBIT', KEYS[1], ARGV[1], ARGV[2])",
                Long.class
        );

        // 循环添加
        for (int i = 0; i < 10000; i++) {
            // 构建脚本参数
            List<Long> args = Lists.newArrayList();
            args.add(RandomUtil.randomLong(10000000));
            args.add(1L);

            Long result = (Long) redisTemplate.execute(
                    bfAddScript,
                    Collections.singletonList(key),
                    args.toArray()
            );

            System.out.println(result);
        }
    }

    /**
     * Roaring Bitmap 测试
     */
    @Test
    void testAddRBitmap() {
        // Redis 键
        String key = "myrbitmap";

        // Lua 脚本
        RedisScript<Long> bfAddScript = new DefaultRedisScript<>(
                "return redis.call('R.SETBIT', KEYS[1], ARGV[1], ARGV[2])",
                Long.class
        );

        // 循环添加
        for (int i = 0; i < 10000; i++) {
            // 构建脚本参数
            List<Long> args = Lists.newArrayList();
            args.add(RandomUtil.randomLong(10000000));
            args.add(1L);

            Long result = (Long) redisTemplate.execute(
                    bfAddScript,
                    Collections.singletonList(key),
                    args.toArray()
            );
            System.out.println(result);
        }
    }
}
