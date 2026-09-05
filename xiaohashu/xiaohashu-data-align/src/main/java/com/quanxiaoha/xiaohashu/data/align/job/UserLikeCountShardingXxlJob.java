package com.quanxiaoha.xiaohashu.data.align.job;

import cn.hutool.core.collection.CollUtil;
import com.quanxiaoha.xiaohashu.data.align.constant.RedisKeyConstants;
import com.quanxiaoha.xiaohashu.data.align.constant.TableConstants;
import com.quanxiaoha.xiaohashu.data.align.domain.mapper.DeleteMapper;
import com.quanxiaoha.xiaohashu.data.align.domain.mapper.SelectMapper;
import com.quanxiaoha.xiaohashu.data.align.domain.mapper.UpdateMapper;
import com.xxl.job.core.context.XxlJobHelper;
import com.xxl.job.core.handler.annotation.XxlJob;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;


/**
 * @author: 犬小哈
 * @date: 2024/4/6 15:51
 * @version: v1.0.0
 * @description: 定时分片广播任务：对当日发生变更用户获得的点赞数进行对齐
 **/
@Component
@Slf4j
public class UserLikeCountShardingXxlJob {

    @Resource
    private SelectMapper selectMapper;
    @Resource
    private UpdateMapper updateMapper;
    @Resource
    private DeleteMapper deleteMapper;
    @Resource
    private RedisTemplate<String, Object> redisTemplate;

    /**
     * 分片广播任务
     */
    @XxlJob("userLikeCountShardingJobHandler")
    public void userLikeCountShardingJobHandler() throws Exception {
        // 获取分片参数
        // 分片序号
        int shardIndex = XxlJobHelper.getShardIndex();
        // 分片总数
        int shardTotal = XxlJobHelper.getShardTotal();

        XxlJobHelper.log("=================> 开始定时分片广播任务：对当日发生变更用户获得的点赞数进行对齐");
        XxlJobHelper.log("分片参数：当前分片序号 = {}, 总分片数 = {}", shardIndex, shardTotal);

        log.info("分片参数：当前分片序号 = {}, 总分片数 = {}", shardIndex, shardTotal);

        // 表后缀
        String date = LocalDate.now().minusDays(1) // 昨日的日期
                .format(DateTimeFormatter.ofPattern("yyyyMMdd")); // 转字符串
        // 表名后缀
        String tableNameSuffix = TableConstants.buildTableNameSuffix(date, shardIndex);

        // 一批次 1000 条
        int batchSize = 1000;
        // 共对齐了多少条记录，默认为 0
        int processedTotal = 0;

        // 死循环
        for (;;) {
            // 1. 分批次查询 t_data_align_user_like_count_temp_日期_分片序号，如一批次查询 1000 条，直到全部查询完成
            List<Long> userIds = selectMapper.selectBatchFromDataAlignUserLikeCountTempTable(tableNameSuffix, batchSize);

            // 若记录为空，终止循环
            if (CollUtil.isEmpty(userIds)) break;

            // 循环这一批发生变更的用户 ID
            userIds.forEach(userId -> {
                // 2: 对 t_user_like 用户点赞表执行 count(*) 操作，获取用户获得的点赞总数
                int userLikeTotal = selectMapper.selectUserLikeCountFromNoteLikeTableByUserId(userId);

                // 3: 更新 t_user_count 表
                int count = updateMapper.updateUserLikeTotalByUserId(userId, userLikeTotal);
                // 更新对应 Redis 缓存
                if (count > 0) {
                    String redisKey = RedisKeyConstants.buildCountUserKey(userId);
                    // 判断 Hash 是否存在
                    boolean hashKey = redisTemplate.hasKey(redisKey);
                    // 若存在
                    if (hashKey) {
                        // 更新 Hash 中的 Field 点赞总数
                        redisTemplate.opsForHash().put(redisKey, RedisKeyConstants.FIELD_LIKE_TOTAL, userLikeTotal);
                    }
                }
            });

            // 4. 批量物理删除这一批次记录
            deleteMapper.batchDeleteDataAlignUserLikeCountTempTable(tableNameSuffix, userIds);

            // 当前已处理的记录数
            processedTotal += userIds.size();
        }

        XxlJobHelper.log("=================> 结束定时分片广播任务：对当日发生变更用户获得的点赞数进行对齐，共对齐记录数：{}", processedTotal);
    }

}
