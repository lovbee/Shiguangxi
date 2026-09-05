package com.quanxiaoha.xiaohashu.comment.biz.consumer;

import cn.hutool.core.collection.CollUtil;
import com.google.common.collect.Lists;
import com.google.common.util.concurrent.RateLimiter;
import com.quanxiaoha.framework.common.util.JsonUtils;
import com.quanxiaoha.xiaohashu.comment.biz.constant.MQConstants;
import com.quanxiaoha.xiaohashu.comment.biz.domain.mapper.CommentLikeDOMapper;
import com.quanxiaoha.xiaohashu.comment.biz.enums.LikeUnlikeCommentTypeEnum;
import com.quanxiaoha.xiaohashu.comment.biz.model.dto.LikeUnlikeCommentMqDTO;
import jakarta.annotation.PreDestroy;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.apache.rocketmq.client.consumer.DefaultMQPushConsumer;
import org.apache.rocketmq.client.consumer.listener.ConsumeOrderlyStatus;
import org.apache.rocketmq.client.consumer.listener.MessageListenerOrderly;
import org.apache.rocketmq.client.exception.MQClientException;
import org.apache.rocketmq.common.consumer.ConsumeFromWhere;
import org.apache.rocketmq.common.protocol.heartbeat.MessageModel;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import java.util.Collection;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.function.Function;
import java.util.stream.Collectors;

/**
 * @author: 犬小哈
 * @date: 2024/8/9 11:52
 * @version: v1.0.0
 * @description: 评论点赞、取消点赞批量写库
 **/
@Component
@Slf4j
public class LikeUnlikeComment2DBConsumer {

    @Value("${rocketmq.name-server}")
    private String namesrvAddr;

    @Resource
    private CommentLikeDOMapper commentLikeDOMapper;

    private DefaultMQPushConsumer consumer;

    // 每秒创建 5000 个令牌
    private RateLimiter rateLimiter = RateLimiter.create(5000);

    @Bean(name = "LikeUnlikeComment2DBConsumer")
    public DefaultMQPushConsumer mqPushConsumer() throws MQClientException {
        // Group 组
        String group = "xiaohashu_group_" + MQConstants.TOPIC_COMMENT_LIKE_OR_UNLIKE;

        // 创建一个新的 DefaultMQPushConsumer 实例，并指定消费者的消费组名
        consumer = new DefaultMQPushConsumer(group);

        // 设置 RocketMQ 的 NameServer 地址
        consumer.setNamesrvAddr(namesrvAddr);

        // 订阅指定的主题，并设置主题的订阅规则（"*" 表示订阅所有标签的消息）
        consumer.subscribe(MQConstants.TOPIC_COMMENT_LIKE_OR_UNLIKE, "*");

        // 设置消费者消费消息的起始位置，如果队列中没有消息，则从最新的消息开始消费。
        consumer.setConsumeFromWhere(ConsumeFromWhere.CONSUME_FROM_LAST_OFFSET);

        // 设置消息消费模式，这里使用集群模式 (CLUSTERING)
        consumer.setMessageModel(MessageModel.CLUSTERING);

        // 最大重试次数, 以防消息重试过多次仍然没有成功，避免消息卡在消费队列中。
        consumer.setMaxReconsumeTimes(3);
        // 设置每批次消费的最大消息数量，这里设置为 30，表示每次拉取时最多消费 30 条消息。
        consumer.setConsumeMessageBatchMaxSize(30);

        // 注册消息监听器
        consumer.registerMessageListener((MessageListenerOrderly) (msgs, context) -> {
            log.info("==> 【评论点赞、取消点赞】本批次消息大小: {}", msgs.size());
            try {
                // 令牌桶流控, 以控制数据库能够承受的 QPS
                rateLimiter.acquire();

                // 将批次 Json 消息体转换 DTO 集合
                List<LikeUnlikeCommentMqDTO> likeUnlikeCommentMqDTOS = Lists.newArrayList();

                msgs.forEach(msg -> {
                    String tag = msg.getTags(); // Tag 标签
                    String msgJson = new String(msg.getBody()); // 消息体 Json 字符串
                    log.info("==> 【评论点赞、取消点赞】Consumer - Tag: {}, Received message: {}", tag, msgJson);

                    // Json 转 DTO
                    likeUnlikeCommentMqDTOS.add(JsonUtils.parseObject(msgJson, LikeUnlikeCommentMqDTO.class));

                });

                // 按评论 ID 分组
                Map<Long, List<LikeUnlikeCommentMqDTO>> commentIdAndListMap = likeUnlikeCommentMqDTOS.stream()
                        .collect(Collectors.groupingBy(LikeUnlikeCommentMqDTO::getCommentId));

                List<LikeUnlikeCommentMqDTO> finalLikeUnlikeCommentMqDTOS = Lists.newArrayList();

                commentIdAndListMap.forEach((commentId, ops) -> {
                    // 优化：若某个用户对某评论，多次操作，如点赞 -> 取消点赞 -> 点赞，需进行操作合并，只提取最后一次操作，进一步降低操作数据库的频率
                    Map<Long, LikeUnlikeCommentMqDTO> userLastOp = ops.stream()
                            .collect(Collectors.toMap(
                                    LikeUnlikeCommentMqDTO::getUserId, // 以发布评论的用户 ID 作为 Map 的键
                                    Function.identity(), // 直接使用 DTO 对象本身作为 Map 的值
                                    // 合并策略：当出现重复键（同一用户多次操作）时，保留时间更晚的记录
                                    (oldValue, newValue) ->
                                            oldValue.getCreateTime().isAfter(newValue.getCreateTime()) ? oldValue : newValue
                            ));


                    finalLikeUnlikeCommentMqDTOS.addAll(userLastOp.values());
                });

                // 批量操作数据库
                executeBatchSQL(finalLikeUnlikeCommentMqDTOS);

                // 手动 ACK，告诉 RocketMQ 这批次消息消费成功
                return ConsumeOrderlyStatus.SUCCESS;
            } catch (Exception e) {
                log.error("", e);
                // 这样 RocketMQ 会暂停当前队列的消费一段时间，再重试
                return ConsumeOrderlyStatus.SUSPEND_CURRENT_QUEUE_A_MOMENT;
            }
        });

        // 启动消费者
        consumer.start();
        return consumer;
    }

    /**
     * 批量操作数据库
     * @param values
     */
    private void executeBatchSQL(Collection<LikeUnlikeCommentMqDTO> values) {
        // 过滤出点赞操作
        List<LikeUnlikeCommentMqDTO> likes = values.stream()
                .filter(op -> Objects.equals(op.getType(), LikeUnlikeCommentTypeEnum.LIKE.getCode()))
                .toList();

        // 过滤出取消点赞操作
        List<LikeUnlikeCommentMqDTO> unlikes = values.stream()
                .filter(op -> Objects.equals(op.getType(), LikeUnlikeCommentTypeEnum.UNLIKE.getCode()))
                .toList();

        // 取消点赞：批量删除
        if (CollUtil.isNotEmpty(unlikes)) {
            commentLikeDOMapper.batchDelete(unlikes);
        }

        // 点赞：批量新增
        if (CollUtil.isNotEmpty(likes)) {
            commentLikeDOMapper.batchInsert(likes);
        }
    }

    @PreDestroy
    public void destroy() {
        if (Objects.nonNull(consumer)) {
            try {
                consumer.shutdown();  // 关闭消费者
            } catch (Exception e) {
                log.error("", e);
            }
        }
    }

}
