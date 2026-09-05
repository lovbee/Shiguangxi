package com.quanxiaoha.xiaohashu.data.align.consumer;

import com.quanxiaoha.framework.common.util.JsonUtils;
import com.quanxiaoha.xiaohashu.data.align.constant.MQConstants;
import com.quanxiaoha.xiaohashu.data.align.constant.RedisKeyConstants;
import com.quanxiaoha.xiaohashu.data.align.constant.TableConstants;
import com.quanxiaoha.xiaohashu.data.align.domain.mapper.InsertMapper;
import com.quanxiaoha.xiaohashu.data.align.model.dto.FollowUnfollowMqDTO;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.apache.rocketmq.spring.annotation.RocketMQMessageListener;
import org.apache.rocketmq.spring.core.RocketMQListener;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.data.redis.core.script.RedisScript;
import org.springframework.scripting.support.ResourceScriptSource;
import org.springframework.stereotype.Component;
import org.springframework.beans.factory.annotation.Value;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.Collections;
import java.util.Objects;

/**
 * @author: 犬小哈
 * @date: 2024/8/9 11:52
 * @version: v1.0.0
 * @description: 日增量数据落库：用户关注、取消关注
 **/
@Component
@RocketMQMessageListener(consumerGroup = "xiaohashu_group_data_align_" + MQConstants.TOPIC_COUNT_FOLLOWING, // Group 组
        topic = MQConstants.TOPIC_COUNT_FOLLOWING // 主题 Topic
        )
@Slf4j
public class TodayUserFollowIncrementData2DBConsumer implements RocketMQListener<String> {

    @Resource
    private RedisTemplate<String, Object> redisTemplate;
    @Resource
    private InsertMapper insertRecordMapper;

    /**
     * 表总分片数
     */
    @Value("${table.shards}")
    private int tableShards;

    @Override
    public void onMessage(String body) {
        log.info("## TodayUserFollowIncrementData2DBConsumer 消费到了 MQ: {}", body);

        // 消息体 JSON 字符串转 DTO
        FollowUnfollowMqDTO followUnfollowMqDTO = JsonUtils.parseObject(body, FollowUnfollowMqDTO.class);

        if (Objects.isNull(followUnfollowMqDTO)) return;

        // 关注/取关操作
        // 源用户 ID
        Long userId = followUnfollowMqDTO.getUserId();
        // 目标用户 ID
        Long targetUserId = followUnfollowMqDTO.getTargetUserId();

        // 今日日期
        String date = LocalDate.now()
                .format(DateTimeFormatter.ofPattern("yyyyMMdd")); // 转字符串

        // ------------------------- 源用户的关注数变更记录 -------------------------
        // 源用户 ID 对应的 Bloom Key
        String userBloomKey = RedisKeyConstants.buildBloomUserFollowListKey(date);

        // 1. 布隆过滤器判断该日增量数据是否已经记录
        DefaultRedisScript<Long> script = new DefaultRedisScript<>();
        // Lua 脚本路径
        script.setScriptSource(new ResourceScriptSource(new ClassPathResource("/lua/bloom_today_user_follow_check.lua")));
        // 返回值类型
        script.setResultType(Long.class);

        // 执行 Lua 脚本，拿到返回结果
        Long result = redisTemplate.execute(script, Collections.singletonList(userBloomKey), userId);

        // Lua 脚本：添加到布隆过滤器
        RedisScript<Long> bloomAddScript = RedisScript.of("return redis.call('BF.ADD', KEYS[1], ARGV[1])", Long.class);

        // 若布隆过滤器判断不存在（绝对正确）
        if (Objects.equals(result, 0L)) {
            // 若无，才会落库，减轻数据库压力
            // 根据分片总数，取模，分别获取对应的分片序号
            long userIdHashKey = userId % tableShards;

            try {
                // 将日增量变更数据，写入表 t_data_align_following_count_temp_日期_分片序号
                insertRecordMapper.insert2DataAlignUserFollowingCountTempTable(
                        TableConstants.buildTableNameSuffix(date, userIdHashKey), userId);
            } catch (Exception e) {
                log.error("", e);
            }

            // 数据库写入成功后，再添加布隆过滤器中
            redisTemplate.execute(bloomAddScript, Collections.singletonList(userBloomKey), userId);
        }

        // ------------------------- 目标用户的粉丝数变更记录 -------------------------
        // 目标用户 ID 对应的 Bloom Key
        String targetUserBloomKey = RedisKeyConstants.buildBloomUserFansListKey(date);
        // 布隆过滤器判断该日增量数据是否已经记录
        result = redisTemplate.execute(script, Collections.singletonList(targetUserBloomKey), targetUserId);

        // 若布隆过滤器判断不存在（绝对正确）
        if (Objects.equals(result, 0L)) {
            // 若无，才会落库，减轻数据库压力
            // 根据分片总数，取模，分别获取对应的分片序号
            long targetUserIdHashKey = targetUserId % tableShards;

            try {
                // 将日增量变更数据，写入表 t_data_align_fans_count_temp_日期_分片序号
                insertRecordMapper.insert2DataAlignUserFansCountTempTable(
                        TableConstants.buildTableNameSuffix(date, targetUserIdHashKey), targetUserId);
            } catch (Exception e) {
                log.error("", e);
            }

            // 数据库写入成功后，再添加布隆过滤器中
            redisTemplate.execute(bloomAddScript, Collections.singletonList(targetUserBloomKey), targetUserId);
        }
    }
}
