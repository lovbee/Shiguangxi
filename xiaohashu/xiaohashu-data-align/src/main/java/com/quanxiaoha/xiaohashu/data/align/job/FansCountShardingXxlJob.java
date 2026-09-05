package com.quanxiaoha.xiaohashu.data.align.job;

import cn.hutool.core.collection.CollUtil;
import com.quanxiaoha.xiaohashu.api.SearchFeignApi;
import com.quanxiaoha.xiaohashu.data.align.constant.RedisKeyConstants;
import com.quanxiaoha.xiaohashu.data.align.constant.TableConstants;
import com.quanxiaoha.xiaohashu.data.align.domain.mapper.DeleteMapper;
import com.quanxiaoha.xiaohashu.data.align.domain.mapper.SelectMapper;
import com.quanxiaoha.xiaohashu.data.align.domain.mapper.UpdateMapper;
import com.quanxiaoha.xiaohashu.data.align.rpc.SearchRpcService;
import com.xxl.job.core.context.XxlJobHelper;
import com.xxl.job.core.handler.annotation.XxlJob;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.stereotype.Component;

import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;


/**
 * @author: 犬小哈
 * @date: 2024/4/6 15:51
 * @version: v1.0.0
 * @description: 定时分片广播任务：对当日发生变更的用户粉丝数进行对齐
 **/
@Component
@Slf4j
public class FansCountShardingXxlJob {

    @Resource
    private SelectMapper selectMapper;
    @Resource
    private UpdateMapper updateMapper;
    @Resource
    private DeleteMapper deleteMapper;
    @Resource
    private RedisTemplate<String, Object> redisTemplate;
    @Resource
    private SearchFeignApi searchFeignApi;
    @Autowired
    private SearchRpcService searchRpcService;

    /**
     * 分片广播任务
     */
    @XxlJob("fansCountShardingJobHandler")
    public void fansCountShardingJobHandler() throws Exception {
        // 获取分片参数
        // 分片序号
        int shardIndex = XxlJobHelper.getShardIndex();
        // 分片总数
        int shardTotal = XxlJobHelper.getShardTotal();

        XxlJobHelper.log("=================> 开始定时分片广播任务：对当日发生变更的用户粉丝数进行对齐");
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
            // 1. 分批次查询 t_data_align_fans_count_temp_日期_分片序号，如一批次查询 1000 条，直到全部查询完成
            List<Long> userIds = selectMapper.selectBatchFromDataAlignFansCountTempTable(tableNameSuffix, batchSize);

            // 若记录为空，终止循环
            if (CollUtil.isEmpty(userIds)) break;

            // 循环这一批发生变更的用户 ID
            userIds.forEach(userId -> {
                // 2: 对 t_fans 关注表执行 count(*) 操作，获取关注总数
                int fansTotal = selectMapper.selectCountFromFansTableByUserId(userId);

                // 3: 更新 t_user_count 表
                int count = updateMapper.updateUserFansTotalByUserId(userId, fansTotal);
                // 更新对应 Redis 缓存
                if (count > 0) {
                    String redisKey = RedisKeyConstants.buildCountUserKey(userId);
                    // 判断 Hash 是否存在
                    boolean hashKey = redisTemplate.hasKey(redisKey);
                    // 若存在
                    if (hashKey) {
                        // 更新 Hash 中的 Field 粉丝总数
                        redisTemplate.opsForHash().put(redisKey, RedisKeyConstants.FIELD_FANS_TOTAL, fansTotal);
                    }
                }

                // 远程 RPC, 调用搜索服务，重新构建索引
                searchRpcService.rebuildUserDocument(userId);
            });

            // 4. 批量物理删除这一批次记录
            deleteMapper.batchDeleteDataAlignFansCountTempTable(tableNameSuffix, userIds);

            // 当前已处理的记录数
            processedTotal += userIds.size();
        }

        XxlJobHelper.log("=================> 结束定时分片广播任务：对当日发生变更的用户粉丝数进行对齐，共对齐记录数：{}", processedTotal);
    }

}
