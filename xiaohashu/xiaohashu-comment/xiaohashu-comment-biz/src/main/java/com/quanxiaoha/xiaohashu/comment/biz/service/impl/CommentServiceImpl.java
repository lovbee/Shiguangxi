package com.quanxiaoha.xiaohashu.comment.biz.service.impl;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.RandomUtil;
import com.github.benmanes.caffeine.cache.Cache;
import com.github.benmanes.caffeine.cache.Caffeine;
import com.google.common.base.Preconditions;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.google.common.collect.Sets;
import com.quanxiaoha.framework.biz.context.holder.LoginUserContextHolder;
import com.quanxiaoha.framework.common.constant.DateConstants;
import com.quanxiaoha.framework.common.exception.BizException;
import com.quanxiaoha.framework.common.response.PageResponse;
import com.quanxiaoha.framework.common.response.Response;
import com.quanxiaoha.framework.common.util.DateUtils;
import com.quanxiaoha.framework.common.util.JsonUtils;
import com.quanxiaoha.xiaohashu.comment.biz.constant.MQConstants;
import com.quanxiaoha.xiaohashu.comment.biz.constant.RedisKeyConstants;
import com.quanxiaoha.xiaohashu.comment.biz.domain.dataobject.CommentDO;
import com.quanxiaoha.xiaohashu.comment.biz.domain.dataobject.CommentLikeDO;
import com.quanxiaoha.xiaohashu.comment.biz.domain.mapper.CommentDOMapper;
import com.quanxiaoha.xiaohashu.comment.biz.domain.mapper.CommentLikeDOMapper;
import com.quanxiaoha.xiaohashu.comment.biz.domain.mapper.NoteCountDOMapper;
import com.quanxiaoha.xiaohashu.comment.biz.enums.*;
import com.quanxiaoha.xiaohashu.comment.biz.model.dto.LikeUnlikeCommentMqDTO;
import com.quanxiaoha.xiaohashu.comment.biz.model.dto.PublishCommentMqDTO;
import com.quanxiaoha.xiaohashu.comment.biz.model.vo.*;
import com.quanxiaoha.xiaohashu.comment.biz.retry.SendMqRetryHelper;
import com.quanxiaoha.xiaohashu.comment.biz.rpc.DistributedIdGeneratorRpcService;
import com.quanxiaoha.xiaohashu.comment.biz.rpc.KeyValueRpcService;
import com.quanxiaoha.xiaohashu.comment.biz.rpc.UserRpcService;
import com.quanxiaoha.xiaohashu.comment.biz.service.CommentService;
import com.quanxiaoha.xiaohashu.kv.dto.req.FindCommentContentReqDTO;
import com.quanxiaoha.xiaohashu.kv.dto.rsp.FindCommentContentRspDTO;
import com.quanxiaoha.xiaohashu.user.dto.resp.FindUserByIdRspDTO;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.apache.logging.log4j.util.Strings;
import org.apache.rocketmq.client.producer.SendCallback;
import org.apache.rocketmq.client.producer.SendResult;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.springframework.core.io.ClassPathResource;
import org.springframework.data.redis.core.*;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.scripting.support.ResourceScriptSource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

import java.time.LocalDateTime;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.stream.Collectors;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:41
 * @version: v1.0.0
 * @description: 评论业务
 **/
@Service
@Slf4j
public class CommentServiceImpl implements CommentService {

    @Resource
    private SendMqRetryHelper sendMqRetryHelper;
    @Resource
    private DistributedIdGeneratorRpcService distributedIdGeneratorRpcService;
    @Resource
    private KeyValueRpcService keyValueRpcService;
    @Resource
    private UserRpcService userRpcService;
    @Resource
    private CommentDOMapper commentDOMapper;
    @Resource
    private NoteCountDOMapper noteCountDOMapper;
    @Resource
    private RedisTemplate<String, Object> redisTemplate;
    @Resource(name = "taskExecutor")
    private ThreadPoolTaskExecutor threadPoolTaskExecutor;
    @Resource
    private RocketMQTemplate rocketMQTemplate;
    @Resource
    private CommentLikeDOMapper commentLikeDOMapper;
    @Resource
    private TransactionTemplate transactionTemplate;

    /**
     * 评论详情本地缓存
     */
    private static final Cache<Long, String> LOCAL_CACHE = Caffeine.newBuilder()
            .initialCapacity(10000) // 设置初始容量为 10000 个条目
            .maximumSize(10000) // 设置缓存的最大容量为 10000 个条目
            .expireAfterWrite(1, TimeUnit.HOURS) // 设置缓存条目在写入后 1 小时过期
            .build();

    /**
     * 发布评论
     *
     * @param publishCommentReqVO
     * @return
     */
    @Override
    public Response<?> publishComment(PublishCommentReqVO publishCommentReqVO) {
        // 评论正文
        String content = publishCommentReqVO.getContent();
        // 附近图片
        String imageUrl = publishCommentReqVO.getImageUrl();

        // 评论内容和图片不能同时为空
        Preconditions.checkArgument(StringUtils.isNotBlank(content) || StringUtils.isNotBlank(imageUrl),
                "评论正文和图片不能同时为空");

        // 发布者 ID
        Long creatorId = LoginUserContextHolder.getUserId();

        // RPC: 调用分布式 ID 生成服务，生成评论 ID
        String commentId = distributedIdGeneratorRpcService.generateCommentId();

        // 发送 MQ
        // 构建消息体 DTO
        PublishCommentMqDTO publishCommentMqDTO = PublishCommentMqDTO.builder()
                .commentId(Long.valueOf(commentId))
                .noteId(publishCommentReqVO.getNoteId())
                .content(content)
                .imageUrl(imageUrl)
                .replyCommentId(publishCommentReqVO.getReplyCommentId())
                .createTime(LocalDateTime.now())
                .creatorId(creatorId)
                .build();

        sendMqRetryHelper.asyncSend(MQConstants.TOPIC_PUBLISH_COMMENT, JsonUtils.toJsonString(publishCommentMqDTO));

        // 将评论 ID 返给前端
        return Response.success(commentId);
    }

    /**
     * 评论列表分页查询
     *
     * @param findCommentPageListReqVO
     * @return
     */
    @Override
    public PageResponse<FindCommentItemRspVO> findCommentPageList(FindCommentPageListReqVO findCommentPageListReqVO) {
        // 笔记 ID
        Long noteId = findCommentPageListReqVO.getNoteId();
        // 当前页码
        Integer pageNo = findCommentPageListReqVO.getPageNo();
        // 每页展示一级评论数
        long pageSize = 7;

        // 构建评论总数 Redis Key
        String noteCommentTotalKey = RedisKeyConstants.buildNoteCommentTotalKey(noteId);
        // 先从 Redis 中查询该笔记的评论总数
        Number commentTotal = (Number) redisTemplate.opsForHash()
                .get(noteCommentTotalKey, RedisKeyConstants.FIELD_COMMENT_TOTAL);
        long count = Objects.isNull(commentTotal) ? 0L : commentTotal.longValue();

        // 若缓存不存在，则查询数据库
        if (Objects.isNull(commentTotal)) {
            // 查询评论总数 (从 t_note_count 笔记计数表查，提升查询性能, 避免 count(*))
            Long dbCount = noteCountDOMapper.selectCommentTotalByNoteId(noteId);

            // 若数据库中也不存在，可能计数表中的记录还未初始化
            // if (Objects.isNull(dbCount)) {
            //     throw new BizException(ResponseCodeEnum.COMMENT_NOT_FOUND);
            // }

            count = Objects.isNull(dbCount) ? 0L : dbCount;
            // count = dbCount;
            // 异步将评论总数同步到 Redis 中
            long finalCount = count;
            threadPoolTaskExecutor.execute(() ->
                syncNoteCommentTotal2Redis(noteCommentTotalKey, finalCount)
            );
        }

        // 若评论总数为 0，则直接响应
        if (count == 0) {
            return PageResponse.success(null, pageNo, 0);
        }

        // 分页返参
        List<FindCommentItemRspVO> commentRspVOS = Lists.newArrayList();

        // 计算分页查询的偏移量 offset
        long offset = PageResponse.getOffset(pageNo, pageSize);

        // 评论分页缓存使用 ZSET + STRING 实现
        // 构建评论 ZSET Key
        String commentZSetKey = RedisKeyConstants.buildCommentListKey(noteId);
        // 先判断 ZSET 是否存在
        boolean hasKey = redisTemplate.hasKey(commentZSetKey);

        // 若不存在
        if (!hasKey) {
            // 异步将热点评论同步到 redis 中（最多同步 500 条）
            threadPoolTaskExecutor.execute(() ->
                    syncHeatComments2Redis(commentZSetKey, noteId));
        }

        // 若 ZSET 缓存存在, 并且查询的是前 50 页的评论
        if (hasKey && offset < 500) {
            // 使用 ZRevRange 获取某篇笔记下，按热度降序排序的一级评论 ID
            Set<Object> commentIds = redisTemplate.opsForZSet()
                    .reverseRangeByScore(commentZSetKey, -Double.MAX_VALUE, Double.MAX_VALUE, offset, pageSize);

            // 若结果不为空
            if (CollUtil.isNotEmpty(commentIds)) {
                // Set 转 List
                List<Object> commentIdList = Lists.newArrayList(commentIds);

                // 先查询本地缓存
                // 新建一个集合，用于存储本地缓存中不存在的评论 ID
                List<Long> localCacheExpiredCommentIds = Lists.newArrayList();

                // 构建查询本地缓存的 Key 集合
                List<Long> localCacheKeys = commentIdList.stream()
                        .map(commentId -> Long.valueOf(commentId.toString()))
                        .toList();

                // 批量查询本地缓存
                Map<Long, String> commentIdAndDetailJsonMap = LOCAL_CACHE.getAll(localCacheKeys, missingKeys -> {
                    // 对于本地缓存中缺失的 key，返回空字符串
                    Map<Long, String> missingData = Maps.newHashMap();
                    missingKeys.forEach(key -> {
                        localCacheExpiredCommentIds.add(key);
                        missingData.put(key, Strings.EMPTY);
                    });
                    return missingData;
                });

                // 若 localCacheExpiredCommentIds 的大小不等于 commentIdList 的大小，说明本地缓存中有数据
                if (CollUtil.size(localCacheExpiredCommentIds) != commentIdList.size()) {
                    // 将本地缓存中的评论详情 Json, 转换为实体类，添加到 VO 返参集合中
                    for (String value : commentIdAndDetailJsonMap.values()) {
                        if (StringUtils.isBlank(value)) continue;
                        FindCommentItemRspVO commentRspVO = JsonUtils.parseObject(value, FindCommentItemRspVO.class);
                        commentRspVOS.add(commentRspVO);
                    }
                }

                // 若 localCacheExpiredCommentIds 大小等于 0，说明评论详情数据都在本地缓存中，直接响应返参
                if (CollUtil.size(localCacheExpiredCommentIds) == 0) {
                    // 计数数据需要从 Redis 中查
                    if (CollUtil.isNotEmpty(commentRspVOS)) {
                        setCommentCountData(commentRspVOS, localCacheExpiredCommentIds);
                    }

                    return PageResponse.success(commentRspVOS, pageNo, count, pageSize);
                }

                // 构建 MGET 批量查询评论详情的 Key 集合
                List<String> commentIdKeys = localCacheExpiredCommentIds.stream()
                        .map(RedisKeyConstants::buildCommentDetailKey)
                        .toList();

                // MGET 批量获取评论数据
                List<Object> commentsJsonList = redisTemplate.opsForValue().multiGet(commentIdKeys);

                // 可能存在部分评论不在缓存中，已经过期被删除，这些评论 ID 需要提取出来，等会查数据库
                List<Long> expiredCommentIds = Lists.newArrayList();

                for (int i = 0; i < commentsJsonList.size(); i++) {
                    String commentJson = (String) commentsJsonList.get(i);
                    Long commentId = Long.valueOf(localCacheExpiredCommentIds.get(i).toString());
                    if (Objects.nonNull(commentJson)) {
                        // 缓存中存在的评论 Json，直接转换为 VO 添加到返参集合中
                        FindCommentItemRspVO commentRspVO = JsonUtils.parseObject(commentJson, FindCommentItemRspVO.class);
                        commentRspVOS.add(commentRspVO);
                    } else {
                        // 评论失效，添加到失效评论列表
                        expiredCommentIds.add(commentId);
                    }
                }

                // 对于缓存中存在的评论详情, 需要再次查询其计数数据
                if (CollUtil.isNotEmpty(commentRspVOS)) {
                    setCommentCountData(commentRspVOS, expiredCommentIds);
                }

                // 对于不存在的一级评论，需要批量从数据库中查询，并添加到 commentRspVOS 中
                if (CollUtil.isNotEmpty(expiredCommentIds)) {
                    List<CommentDO> commentDOS = commentDOMapper.selectByCommentIds(expiredCommentIds);
                    getCommentDataAndSync2Redis(commentDOS, noteId, commentRspVOS);
                }
            }

            // 按热度值进行降序排列
            commentRspVOS = commentRspVOS.stream()
                    .sorted(Comparator.comparing(FindCommentItemRspVO::getHeat).reversed())
                    .collect(Collectors.toList());

            // 异步将评论详情，同步到本地缓存
            syncCommentDetail2LocalCache(commentRspVOS);

            return PageResponse.success(commentRspVOS, pageNo, count, pageSize);
        }

        // 缓存中没有，则查询数据库
        // 查询一级评论
        List<CommentDO> oneLevelCommentDOS = commentDOMapper.selectPageList(noteId, offset, pageSize);
        getCommentDataAndSync2Redis(oneLevelCommentDOS, noteId, commentRspVOS);

        // 异步将评论详情，同步到本地缓存
        syncCommentDetail2LocalCache(commentRspVOS);

        return PageResponse.success(commentRspVOS, pageNo, count, pageSize);
    }

    /**
     * 同步笔记评论总数到 Redis 中
     * @param noteCommentTotalKey
     * @param dbCount
     */
    private void syncNoteCommentTotal2Redis(String noteCommentTotalKey, Long dbCount) {
        redisTemplate.executePipelined(new SessionCallback<>() {
            @Override
            public Object execute(RedisOperations operations) {
                // 同步 hash 数据
                operations.opsForHash()
                        .put(noteCommentTotalKey, RedisKeyConstants.FIELD_COMMENT_TOTAL, dbCount);

                // 随机过期时间 (保底1小时 + 随机时间)，单位：秒
                long expireTime = 60*60 + RandomUtil.randomInt(4*60*60);
                operations.expire(noteCommentTotalKey, expireTime, TimeUnit.SECONDS);
                return null;
            }
        });
    }

    /**
     * 二级评论分页查询
     *
     * @param findChildCommentPageListReqVO
     * @return
     */
    @Override
    public PageResponse<FindChildCommentItemRspVO> findChildCommentPageList(FindChildCommentPageListReqVO findChildCommentPageListReqVO) {
        // 父评论 ID
        Long parentCommentId = findChildCommentPageListReqVO.getParentCommentId();
        // 当前页码
        Integer pageNo = findChildCommentPageListReqVO.getPageNo();
        // 每页展示的二级评论数 (小红书 APP 中是一次查询 6 条)
        long pageSize = 6;

        // 先从缓存中查
        String countCommentKey = RedisKeyConstants.buildCountCommentKey(parentCommentId);
        // 子评论总数
        Number redisCount = (Number) redisTemplate.opsForHash()
                .get(countCommentKey, RedisKeyConstants.FIELD_CHILD_COMMENT_TOTAL);
        long count = Objects.isNull(redisCount) ? 0L : redisCount.longValue();

        // 若缓存不存在，走数据库查询
        if (Objects.isNull(redisCount)) {
            // 查询一级评论下子评论的总数 (直接查询 t_comment 表的 child_comment_total 字段，提升查询性能, 避免 count(*))
            Long dbCount = commentDOMapper.selectChildCommentTotalById(parentCommentId);

            // 若数据库中也不存在，则抛出业务异常
            if (Objects.isNull(dbCount)) {
                throw new BizException(ResponseCodeEnum.PARENT_COMMENT_NOT_FOUND);
            }

            count = dbCount;
            // 异步将子评论总数同步到 Redis 中
            threadPoolTaskExecutor.execute(() -> {
                syncCommentCount2Redis(countCommentKey, dbCount);
            });
        }

        // 若子评论总数为 0，直接返参
        if (count == 0) {
            return PageResponse.success(null, pageNo, 0);
        }

        // 分页返参 VO
        List<FindChildCommentItemRspVO> childCommentRspVOS = Lists.newArrayList();

        // 计算分页查询的偏移量 offset (需要 +1，因为最早回复的二级评论已经被展示了)
        long offset = PageResponse.getOffset(pageNo, pageSize) + 1;

        // 子评论分页缓存使用 ZSET + STRING 实现
        // 构建子评论 ZSET Key
        String childCommentZSetKey = RedisKeyConstants.buildChildCommentListKey(parentCommentId);
        // 先判断 ZSET 是否存在
        boolean hasKey = redisTemplate.hasKey(childCommentZSetKey);

        // 若不存在
        if (!hasKey) {
            // 异步将子评论同步到 Redis 中（最多同步 6*10 条）
            threadPoolTaskExecutor.execute(() -> {
                syncChildComments2Redis(parentCommentId, childCommentZSetKey);
            });
        }

        // 若子评论 ZSET 缓存存在, 并且查询的是前 10 页的子评论
        if (hasKey && offset < 6*10) {
            // 使用 ZRevRange 获取某个一级评论下的子评论，按回复时间升序排列
            Set<Object> childCommentIds = redisTemplate.opsForZSet()
                    .rangeByScore(childCommentZSetKey, 0, Double.MAX_VALUE, offset, pageSize);

            // 若结果不为空
            if (CollUtil.isNotEmpty(childCommentIds)) {
                // Set 转 List
                List<Object> childCommentIdList = Lists.newArrayList(childCommentIds);

                // 构建 MGET 批量查询子评论详情的 Key 集合
                List<String> commentIdKeys = childCommentIds.stream()
                        .map(RedisKeyConstants::buildCommentDetailKey)
                        .toList();

                // MGET 批量获取评论数据
                List<Object> commentsJsonList = redisTemplate.opsForValue().multiGet(commentIdKeys);

                // 可能存在部分评论不在缓存中，已经过期被删除，这些评论 ID 需要提取出来，等会查数据库
                List<Long> expiredChildCommentIds = Lists.newArrayList();

                for (int i = 0; i < commentsJsonList.size(); i++) {
                    String commentJson = (String) commentsJsonList.get(i);
                    Long commentId = Long.valueOf(childCommentIdList.get(i).toString());
                    if (Objects.nonNull(commentJson)) {
                        // 缓存中存在的评论 Json，直接转换为 VO 添加到返参集合中
                        FindChildCommentItemRspVO childCommentRspVO = JsonUtils.parseObject(commentJson, FindChildCommentItemRspVO.class);
                        childCommentRspVOS.add(childCommentRspVO);
                    } else {
                        // 评论失效，添加到失效评论列表
                        expiredChildCommentIds.add(commentId);
                    }
                }

                // 对于缓存中存在的子评论, 需要再次查询 Hash, 获取其计数数据
                if (CollUtil.isNotEmpty(childCommentRspVOS)) {
                    setChildCommentCountData(childCommentRspVOS, expiredChildCommentIds);
                }

                // 对于不存在的子评论，需要批量从数据库中查询，并添加到 commentRspVOS 中
                if (CollUtil.isNotEmpty(expiredChildCommentIds)) {
                    List<CommentDO> commentDOS = commentDOMapper.selectByCommentIds(expiredChildCommentIds);
                    getChildCommentDataAndSync2Redis(commentDOS, childCommentRspVOS);
                }

                // 按评论 ID 升序排列（等同于按回复时间升序）
                childCommentRspVOS = childCommentRspVOS.stream()
                        .sorted(Comparator.comparing(FindChildCommentItemRspVO::getCommentId))
                        .collect(Collectors.toList());

                return PageResponse.success(childCommentRspVOS, pageNo, count, pageSize);
            }

        }

        // 分页查询子评论
        List<CommentDO> childCommentDOS = commentDOMapper.selectChildPageList(parentCommentId, offset, pageSize);

        getChildCommentDataAndSync2Redis(childCommentDOS, childCommentRspVOS);

        return PageResponse.success(childCommentRspVOS, pageNo, count, pageSize);
    }

    /**
     * 评论点赞
     *
     * @param likeCommentReqVO
     * @return
     */
    @Override
    public Response<?> likeComment(LikeCommentReqVO likeCommentReqVO) {
        // 被点赞的评论 ID
        Long commentId = likeCommentReqVO.getCommentId();

        // 1. 校验被点赞的评论是否存在
        checkCommentIsExist(commentId);

        // 2. 判断目标评论，是否已经被点赞
        // 当前登录用户ID
        Long userId = LoginUserContextHolder.getUserId();
        // 布隆过滤器 Key
        String bloomUserCommentLikeListKey = RedisKeyConstants.buildBloomCommentLikesKey(userId);

        DefaultRedisScript<Long> script = new DefaultRedisScript<>();
        // Lua 脚本路径
        script.setScriptSource(new ResourceScriptSource(new ClassPathResource("/lua/bloom_comment_like_check.lua")));
        // 返回值类型
        script.setResultType(Long.class);

        // 执行 Lua 脚本，拿到返回结果
        Long result = redisTemplate.execute(script, Collections.singletonList(bloomUserCommentLikeListKey), commentId);

        CommentLikeLuaResultEnum commentLikeLuaResultEnum = CommentLikeLuaResultEnum.valueOf(result);

        if (Objects.isNull(commentLikeLuaResultEnum)) {
            throw new BizException(ResponseCodeEnum.PARAM_NOT_VALID);
        }

        switch (commentLikeLuaResultEnum) {
            // Redis 中布隆过滤器不存在
            case NOT_EXIST -> {
                // 从数据库中校验评论是否被点赞，并异步初始化布隆过滤器，设置过期时间
                int count = commentLikeDOMapper.selectCountByUserIdAndCommentId(userId, commentId);

                // 保底1小时 + 随机秒数
                long expireSeconds = 60*60 + RandomUtil.randomInt(60*60);

                // 目标评论已经被点赞
                if (count > 0) {
                    // 异步初始化布隆过滤器
                    threadPoolTaskExecutor.submit(() ->
                            batchAddCommentLike2BloomAndExpire(userId, expireSeconds, bloomUserCommentLikeListKey));
                    throw new BizException(ResponseCodeEnum.COMMENT_ALREADY_LIKED);
                }

                // 若目标评论未被点赞，查询当前用户是否有点赞其他评论，有则同步初始化布隆过滤器
                batchAddCommentLike2BloomAndExpire(userId, expireSeconds, bloomUserCommentLikeListKey);

                // 添加当前点赞评论 ID 到布隆过滤器中
                // Lua 脚本路径
                script.setScriptSource(new ResourceScriptSource(new ClassPathResource("/lua/bloom_add_comment_like_and_expire.lua")));
                // 返回值类型
                script.setResultType(Long.class);
                redisTemplate.execute(script, Collections.singletonList(bloomUserCommentLikeListKey), commentId, expireSeconds);
            }
            // 目标评论已经被点赞 (可能存在误判，需要进一步确认)
            case COMMENT_LIKED -> {
                // 查询数据库校验是否点赞
                int count = commentLikeDOMapper.selectCountByUserIdAndCommentId(userId, commentId);

                if (count > 0) {
                    throw new BizException(ResponseCodeEnum.COMMENT_ALREADY_LIKED);
                }
            }
        }

        // 3. 发送 MQ, 异步将评论点赞记录落库
        // 构建消息体 DTO
        LikeUnlikeCommentMqDTO likeUnlikeCommentMqDTO = LikeUnlikeCommentMqDTO.builder()
                .userId(userId)
                .commentId(commentId)
                .type(LikeUnlikeCommentTypeEnum.LIKE.getCode()) // 点赞评论
                .createTime(LocalDateTime.now())
                .build();

        // 构建消息对象，并将 DTO 转成 Json 字符串设置到消息体中
        Message<String> message = MessageBuilder.withPayload(JsonUtils.toJsonString(likeUnlikeCommentMqDTO))
                .build();

        // 通过冒号连接, 可让 MQ 发送给主题 Topic 时，携带上标签 Tag
        String destination = MQConstants.TOPIC_COMMENT_LIKE_OR_UNLIKE + ":" + MQConstants.TAG_LIKE;

        // MQ 分区键
        String hashKey = String.valueOf(userId);

        // 异步发送 MQ 消息，提升接口响应速度
        rocketMQTemplate.asyncSendOrderly(destination, message, hashKey, new SendCallback() {
            @Override
            public void onSuccess(SendResult sendResult) {
                log.info("==> 【评论点赞】MQ 发送成功，SendResult: {}", sendResult);
            }

            @Override
            public void onException(Throwable throwable) {
                log.error("==> 【评论点赞】MQ 发送异常: ", throwable);
            }
        });

        return Response.success();
    }

    /**
     * 取消评论点赞
     *
     * @param unLikeCommentReqVO
     * @return
     */
    @Override
    public Response<?> unlikeComment(UnLikeCommentReqVO unLikeCommentReqVO) {
        // 被取消点赞的评论 ID
        Long commentId = unLikeCommentReqVO.getCommentId();

        // 1. 校验评论是否存在
        checkCommentIsExist(commentId);

        // 2. 校验评论是否被点赞过
        // 当前登录用户ID
        Long userId = LoginUserContextHolder.getUserId();
        // 布隆过滤器 Key
        String bloomUserCommentLikeListKey = RedisKeyConstants.buildBloomCommentLikesKey(userId);

        DefaultRedisScript<Long> script = new DefaultRedisScript<>();
        // Lua 脚本路径
        script.setScriptSource(new ResourceScriptSource(new ClassPathResource("/lua/bloom_comment_unlike_check.lua")));
        // 返回值类型
        script.setResultType(Long.class);

        // 执行 Lua 脚本，拿到返回结果
        Long result = redisTemplate.execute(script, Collections.singletonList(bloomUserCommentLikeListKey), commentId);

        CommentUnlikeLuaResultEnum commentUnlikeLuaResultEnum = CommentUnlikeLuaResultEnum.valueOf(result);

        if (Objects.isNull(commentUnlikeLuaResultEnum)) {
            throw new BizException(ResponseCodeEnum.PARAM_NOT_VALID);
        }

        switch (commentUnlikeLuaResultEnum) {
            // 布隆过滤器不存在
            case NOT_EXIST -> {
                // 异步初始化布隆过滤器
                threadPoolTaskExecutor.submit(() -> {
                    // 保底1小时+随机秒数
                    long expireSeconds = 60*60 + RandomUtil.randomInt(60*60);
                    batchAddCommentLike2BloomAndExpire(userId, expireSeconds, bloomUserCommentLikeListKey);
                });

                // 从数据库中校验评论是否被点赞
                int count = commentLikeDOMapper.selectCountByUserIdAndCommentId(userId, commentId);

                // 未点赞，无法取消点赞操作，抛出业务异常
                if (count == 0) throw new BizException(ResponseCodeEnum.COMMENT_NOT_LIKED);
            }
            // 布隆过滤器校验目标评论未被点赞（判断绝对正确）
            case COMMENT_NOT_LIKED -> throw new BizException(ResponseCodeEnum.COMMENT_NOT_LIKED);
        }

        // 3. 发送顺序 MQ，删除评论点赞记录
        // 构建消息体 DTO
        LikeUnlikeCommentMqDTO likeUnlikeCommentMqDTO = LikeUnlikeCommentMqDTO.builder()
                .userId(userId)
                .commentId(commentId)
                .type(LikeUnlikeCommentTypeEnum.UNLIKE.getCode()) // 取消点赞评论
                .createTime(LocalDateTime.now())
                .build();

        // 构建消息对象，并将 DTO 转成 Json 字符串设置到消息体中
        Message<String> message = MessageBuilder.withPayload(JsonUtils.toJsonString(likeUnlikeCommentMqDTO))
                .build();

        // 通过冒号连接, 可让 MQ 发送给主题 Topic 时，携带上标签 Tag
        String destination = MQConstants.TOPIC_COMMENT_LIKE_OR_UNLIKE + ":" + MQConstants.TAG_UNLIKE;

        // MQ 分区键
        String hashKey = String.valueOf(userId);

        // 异步发送 MQ 顺序消息，提升接口响应速度
        rocketMQTemplate.asyncSendOrderly(destination, message, hashKey, new SendCallback() {
            @Override
            public void onSuccess(SendResult sendResult) {
                log.info("==> 【评论取消点赞】MQ 发送成功，SendResult: {}", sendResult);
            }

            @Override
            public void onException(Throwable throwable) {
                log.error("==> 【评论取消点赞】MQ 发送异常: ", throwable);
            }
        });

        return Response.success();
    }

    /**
     * 删除评论
     *
     * @param deleteCommentReqVO
     * @return
     */
    @Override
    public Response<?> deleteComment(DeleteCommentReqVO deleteCommentReqVO) {
        // 被删除的评论 ID
        Long commentId = deleteCommentReqVO.getCommentId();

        // 1. 校验评论是否存在
        CommentDO commentDO = commentDOMapper.selectByPrimaryKey(commentId);

        if (Objects.isNull(commentDO)) {
            throw new BizException(ResponseCodeEnum.COMMENT_NOT_FOUND);
        }

        // 2. 校验是否有权限删除
        Long currUserId = LoginUserContextHolder.getUserId();
        if (!Objects.equals(currUserId, commentDO.getUserId())) {
            throw new BizException(ResponseCodeEnum.COMMENT_CANT_OPERATE);
        }

        // 3. 物理删除评论、评论内容
        // 编程式事务，保证多个操作的原子性
        transactionTemplate.execute(status -> {
            try {
                // 删除评论元数据
                commentDOMapper.deleteByPrimaryKey(commentId);

                // 删除评论内容
                keyValueRpcService.deleteCommentContent(commentDO.getNoteId(),
                        commentDO.getCreateTime(),
                        commentDO.getContentUuid());

                return null;
            } catch (Exception ex) {
                status.setRollbackOnly(); // 标记事务为回滚
                log.error("", ex);
                throw ex;
            }
        });

        // 4. 删除 Redis 缓存（ZSet 和 String）
        Integer level = commentDO.getLevel();
        Long noteId = commentDO.getNoteId();
        Long parentCommentId = commentDO.getParentId();

        // 根据评论级别，构建对应的 ZSet Key
        String redisZSetKey = Objects.equals(level, 1) ?
                RedisKeyConstants.buildCommentListKey(noteId) : RedisKeyConstants.buildChildCommentListKey(parentCommentId);

        // 使用 RedisTemplate 执行管道操作
        redisTemplate.executePipelined(new SessionCallback<>() {
            @Override
            public Object execute(RedisOperations operations) {
                // 删除 ZSet 中对应评论 ID
                operations.opsForZSet().remove(redisZSetKey, commentId);

                // 删除评论详情
                operations.delete(RedisKeyConstants.buildCommentDetailKey(commentId));
                return null;
            }
        });

        // 5. 发布广播 MQ, 将本地缓存删除
        rocketMQTemplate.asyncSend(MQConstants.TOPIC_DELETE_COMMENT_LOCAL_CACHE, commentId, new SendCallback() {
            @Override
            public void onSuccess(SendResult sendResult) {
                log.info("==> 【删除评论详情本地缓存】MQ 发送成功，SendResult: {}", sendResult);
            }

            @Override
            public void onException(Throwable throwable) {
                log.error("==> 【删除评论详情本地缓存】MQ 发送异常: ", throwable);
            }
        });

        // 6. 发送 MQ, 异步去更新计数、删除关联评论、热度值等
        // 构建消息对象，并将 DO 转成 Json 字符串设置到消息体中
        Message<String> message = MessageBuilder.withPayload(JsonUtils.toJsonString(commentDO))
                .build();

        // 异步发送 MQ 消息，提升接口响应速度
        rocketMQTemplate.asyncSend(MQConstants.TOPIC_DELETE_COMMENT, message, new SendCallback() {
            @Override
            public void onSuccess(SendResult sendResult) {
                log.info("==> 【评论删除】MQ 发送成功，SendResult: {}", sendResult);
            }

            @Override
            public void onException(Throwable throwable) {
                log.error("==> 【评论删除】MQ 发送异常: ", throwable);
            }
        });

        return Response.success();
    }

    /**
     * 删除本地评论缓存
     *
     * @param commentId
     */
    @Override
    public void deleteCommentLocalCache(Long commentId) {
        LOCAL_CACHE.invalidate(commentId);
    }

    /**
     * 初始化评论点赞布隆过滤器
     * @param userId
     * @param expireSeconds
     * @param bloomUserCommentLikeListKey
     * @return
     */
    private void batchAddCommentLike2BloomAndExpire(Long userId, long expireSeconds, String bloomUserCommentLikeListKey) {
        try {
            // 查询该用户点赞的所有评论
            List<CommentLikeDO> commentLikeDOS = commentLikeDOMapper.selectByUserId(userId);

            // 若不为空，批量添加到布隆过滤器中
            if (CollUtil.isNotEmpty(commentLikeDOS)) {
                DefaultRedisScript<Long> script = new DefaultRedisScript<>();
                // Lua 脚本路径
                script.setScriptSource(new ResourceScriptSource(new ClassPathResource("/lua/bloom_batch_add_comment_like_and_expire.lua")));
                // 返回值类型
                script.setResultType(Long.class);

                // 构建 Lua 参数
                List<Object> luaArgs = Lists.newArrayList();
                commentLikeDOS.forEach(commentLikeDO ->
                        luaArgs.add(commentLikeDO.getCommentId())); // 将每个点赞的评论 ID 传入
                luaArgs.add(expireSeconds);  // 最后一个参数是过期时间（秒）
                redisTemplate.execute(script, Collections.singletonList(bloomUserCommentLikeListKey), luaArgs.toArray());
            }
        } catch (Exception e) {
            log.error("## 异步初始化【评论点赞】布隆过滤器异常: ", e);
        }
    }

    /**
     * 校验被点赞的评论是否存在
     *
     * @param commentId
     */
    private void checkCommentIsExist(Long commentId) {
        // 先从本地缓存校验
        String localCacheJson = LOCAL_CACHE.getIfPresent(commentId);

        // 若本地缓存中，该评论不存在
        if (StringUtils.isBlank(localCacheJson)) {
            // 再从 Redis 中校验
            String commentDetailRedisKey = RedisKeyConstants.buildCommentDetailKey(commentId);

            boolean hasKey = redisTemplate.hasKey(commentDetailRedisKey);

            // 若 Redis 中也不存在
            if (!hasKey) {
                // 从数据库中校验
                CommentDO commentDO = commentDOMapper.selectByPrimaryKey(commentId);

                // 若数据库中，该评论也不存在，抛出业务异常
                if (Objects.isNull(commentDO)) {
                    throw new BizException(ResponseCodeEnum.COMMENT_NOT_FOUND);
                }
            }
        }
    }

    /**
     * 设置子评论 VO 的计数
     *
     * @param commentRspVOS 返参 VO 集合
     * @param expiredCommentIds 缓存中已失效的评论 ID 集合
     */
    private void setChildCommentCountData(List<FindChildCommentItemRspVO> commentRspVOS,
                                          List<Long> expiredCommentIds) {
        // 准备从评论 Hash 中查询计数 (被点赞数)
        // 缓存中存在的子评论 ID
        List<Long> notExpiredCommentIds = Lists.newArrayList();

        // 遍历从缓存中解析出的 VO 集合，提取二级评论 ID
        commentRspVOS.forEach(commentRspVO -> {
            Long childCommentId = commentRspVO.getCommentId();
            notExpiredCommentIds.add(childCommentId);
        });

        // 从 Redis 中查询评论计数 Hash 数据
        Map<Long, Map<Object, Object>> commentIdAndCountMap = getCommentCountDataAndSync2RedisHash(notExpiredCommentIds);

        // 遍历 VO, 设置对应子评论的点赞数
        for (FindChildCommentItemRspVO commentRspVO : commentRspVOS) {
            // 评论 ID
            Long commentId = commentRspVO.getCommentId();

            // 若当前这条评论是从数据库中查询出来的, 则无需设置点赞数，以数据库查询出来的为主
            if (CollUtil.isNotEmpty(expiredCommentIds)
                    && expiredCommentIds.contains(commentId)) {
                continue;
            }

            // 设置子评论的点赞数
            Map<Object, Object> hash = commentIdAndCountMap.get(commentId);
            if (CollUtil.isNotEmpty(hash)) {
                Long likeTotal = Long.valueOf(hash.get(RedisKeyConstants.FIELD_LIKE_TOTAL).toString());
                commentRspVO.setLikeTotal(likeTotal);
            }
        }
    }

    /**
     * 获取评论计数数据，并同步到 Redis 中
     * @param notExpiredCommentIds
     * @return
     */
    private Map<Long, Map<Object, Object>> getCommentCountDataAndSync2RedisHash(List<Long> notExpiredCommentIds) {
        // 已失效的 Hash 评论 ID
        List<Long> expiredCountCommentIds = Lists.newArrayList();
        // 构建需要查询的 Hash Key 集合
        List<String> commentCountKeys = notExpiredCommentIds.stream()
                .map(RedisKeyConstants::buildCountCommentKey).toList();

        // 使用 RedisTemplate 执行管道批量操作
        List<Object> results = redisTemplate.executePipelined(new SessionCallback<>() {
            @Override
            public Object execute(RedisOperations operations) {
                // 遍历需要查询的评论计数的 Hash 键集合
                commentCountKeys.forEach(key ->
                        // 在管道中执行 Redis 的 hash.entries 操作
                        // 此操作会获取指定 Hash 键中所有的字段和值
                        operations.opsForHash().entries(key));
                return null;
            }
        });

        // 评论 ID - 计数数据字典
        Map<Long, Map<Object, Object>> commentIdAndCountMap = Maps.newHashMap();
        // 遍历未过期的评论 ID 集合
        for (int i = 0; i < notExpiredCommentIds.size(); i++) {
            // 当前评论 ID
            Long currCommentId = Long.valueOf(notExpiredCommentIds.get(i).toString());
            // 从缓存查询结果中，获取对应 Hash
            Map<Object, Object> hash = (Map<Object, Object>) results.get(i);
            // 若 Hash 结果为空，说明缓存中不存在，添加到 expiredCountCommentIds 中，保存一下
            if (CollUtil.isEmpty(hash)) {
                expiredCountCommentIds.add(currCommentId);
                continue;
            }
            // 若存在，则将数据添加到 commentIdAndCountMap 中，方便后续读取
            commentIdAndCountMap.put(currCommentId, hash);
        }

        // 若已过期的计数评论 ID 集合大于 0，说明部分计数数据不在 Redis 缓存中
        // 需要查询数据库，并将这部分的评论计数 Hash 同步到 Redis 中
        if (CollUtil.size(expiredCountCommentIds) > 0) {
            // 查询数据库
            List<CommentDO> commentDOS = commentDOMapper.selectCommentCountByIds(expiredCountCommentIds);

            commentDOS.forEach(commentDO -> {
                Integer level = commentDO.getLevel();
                Map<Object, Object> map = Maps.newHashMap();
                map.put(RedisKeyConstants.FIELD_LIKE_TOTAL, commentDO.getLikeTotal());
                // 只有一级评论需要统计子评论总数
                if (Objects.equals(level, CommentLevelEnum.ONE.getCode())) {
                    map.put(RedisKeyConstants.FIELD_CHILD_COMMENT_TOTAL, commentDO.getChildCommentTotal());
                }
                // 统一添加到 commentIdAndCountMap 字典中，方便后续查询
                commentIdAndCountMap.put(commentDO.getId(), map);
            });

            // 异步同步到 Redis 中
            threadPoolTaskExecutor.execute(() -> {
                redisTemplate.executePipelined(new SessionCallback<>() {
                    @Override
                    public Object execute(RedisOperations operations) {
                        commentDOS.forEach(commentDO -> {
                            // 构建 Hash Key
                            String key = RedisKeyConstants.buildCountCommentKey(commentDO.getId());
                            // 评论级别
                            Integer level = commentDO.getLevel();
                            // 设置 Field 数据
                            Map<String, Long> fieldsMap = Objects.equals(level, CommentLevelEnum.ONE.getCode()) ?
                                    Map.of(RedisKeyConstants.FIELD_CHILD_COMMENT_TOTAL, commentDO.getChildCommentTotal(),
                                            RedisKeyConstants.FIELD_LIKE_TOTAL, commentDO.getLikeTotal()) : Map.of(RedisKeyConstants.FIELD_LIKE_TOTAL, commentDO.getLikeTotal());
                            // 添加 Hash 数据
                            operations.opsForHash().putAll(key, fieldsMap);

                            // 设置随机过期时间 (5小时以内)
                            long expireTime = RandomUtil.randomInt(5 * 60 * 60);
                            operations.expire(key, expireTime, TimeUnit.SECONDS);
                        });
                        return null;
                    }
                });
            });
        }
        return commentIdAndCountMap;
    }

    /**
     * 获取子评论列表，并同步到 Redis 中
     * @param childCommentDOS
     * @param childCommentRspVOS
     */
    private void getChildCommentDataAndSync2Redis(List<CommentDO> childCommentDOS, List<FindChildCommentItemRspVO> childCommentRspVOS) {
        // 调用 KV 服务需要的入参
        List<FindCommentContentReqDTO> findCommentContentReqDTOS = Lists.newArrayList();
        // 调用用户服务的入参
        Set<Long> userIds = Sets.newHashSet();

        // 归属的笔记 ID
        Long noteId = null;

        // 循环提取 RPC 调用需要的入参数据
        for (CommentDO childCommentDO : childCommentDOS) {
            noteId = childCommentDO.getNoteId();
            // 构建调用 KV 服务批量查询评论内容的入参
            boolean isContentEmpty = childCommentDO.getIsContentEmpty();
            if (!isContentEmpty) {
                FindCommentContentReqDTO findCommentContentReqDTO = FindCommentContentReqDTO.builder()
                        .contentId(childCommentDO.getContentUuid())
                        .yearMonth(DateConstants.DATE_FORMAT_Y_M.format(childCommentDO.getCreateTime()))
                        .build();
                findCommentContentReqDTOS.add(findCommentContentReqDTO);
            }

            // 构建调用用户服务批量查询用户信息的入参 (包含评论发布者、回复的目标用户)
            userIds.add(childCommentDO.getUserId());

            Long parentId = childCommentDO.getParentId();
            Long replyCommentId = childCommentDO.getReplyCommentId();
            // 若当前评论的 replyCommentId 不等于 parentId，则前端需要展示回复的哪个用户，如  “回复 犬小哈：”
            if (!Objects.equals(parentId, replyCommentId)) {
                userIds.add(childCommentDO.getReplyUserId());
            }
        }

        // RPC: 调用 KV 服务，批量获取评论内容
        List<FindCommentContentRspDTO> findCommentContentRspDTOS =
                keyValueRpcService.batchFindCommentContent(noteId, findCommentContentReqDTOS);

        // DTO 集合转 Map, 方便后续拼装数据
        Map<String, String> commentUuidAndContentMap = null;
        if (CollUtil.isNotEmpty(findCommentContentRspDTOS)) {
            commentUuidAndContentMap = findCommentContentRspDTOS.stream()
                    .collect(Collectors.toMap(FindCommentContentRspDTO::getContentId, FindCommentContentRspDTO::getContent));
        }

        // RPC: 调用用户服务，批量获取用户信息（头像、昵称等）
        List<FindUserByIdRspDTO> findUserByIdRspDTOS = userRpcService.findByIds(userIds.stream().toList());

        // DTO 集合转 Map, 方便后续拼装数据
        Map<Long, FindUserByIdRspDTO> userIdAndDTOMap = null;
        if (CollUtil.isNotEmpty(findUserByIdRspDTOS)) {
            userIdAndDTOMap = findUserByIdRspDTOS.stream()
                    .collect(Collectors.toMap(FindUserByIdRspDTO::getId, dto -> dto));
        }

        // DO 转 VO
        for (CommentDO childCommentDO : childCommentDOS) {
            // 构建 VO 实体类
            Long userId = childCommentDO.getUserId();
            FindChildCommentItemRspVO childCommentRspVO = FindChildCommentItemRspVO.builder()
                    .userId(userId)
                    .commentId(childCommentDO.getId())
                    .imageUrl(childCommentDO.getImageUrl())
                    .createTime(DateUtils.formatRelativeTime(childCommentDO.getCreateTime()))
                    .likeTotal(childCommentDO.getLikeTotal())
                    .build();

            // 填充用户信息(包括评论发布者、回复的用户)
            if (CollUtil.isNotEmpty(userIdAndDTOMap)) {
                FindUserByIdRspDTO findUserByIdRspDTO = userIdAndDTOMap.get(userId);
                // 评论发布者用户信息(头像、昵称)
                if (Objects.nonNull(findUserByIdRspDTO)) {
                    childCommentRspVO.setAvatar(findUserByIdRspDTO.getAvatar());
                    childCommentRspVO.setNickname(findUserByIdRspDTO.getNickName());
                }

                // 评论回复的哪个
                Long replyCommentId = childCommentDO.getReplyCommentId();
                Long parentId = childCommentDO.getParentId();

                if (Objects.nonNull(replyCommentId)
                        && !Objects.equals(replyCommentId, parentId)) {
                    Long replyUserId = childCommentDO.getReplyUserId();
                    FindUserByIdRspDTO replyUser = userIdAndDTOMap.get(replyUserId);
                    childCommentRspVO.setReplyUserName(replyUser.getNickName());
                    childCommentRspVO.setReplyUserId(replyUser.getId());
                }
            }

            // 评论内容
            if (CollUtil.isNotEmpty(commentUuidAndContentMap)) {
                String contentUuid = childCommentDO.getContentUuid();
                if (StringUtils.isNotBlank(contentUuid)) {
                    childCommentRspVO.setContent(commentUuidAndContentMap.get(contentUuid));
                }
            }

            childCommentRspVOS.add(childCommentRspVO);
        }

        // 异步将笔记详情，同步到 Redis 中
        threadPoolTaskExecutor.execute(() -> {
            // 准备批量写入的数据
            Map<String, String> data = Maps.newHashMap();
            childCommentRspVOS.forEach(commentRspVO -> {
                // 评论 ID
                Long commentId = commentRspVO.getCommentId();
                // 构建 Key
                String key = RedisKeyConstants.buildCommentDetailKey(commentId);
                data.put(key, JsonUtils.toJsonString(commentRspVO));
            });

            batchAddCommentDetailJson2Redis(data);
        });
    }

    /**
     * 批量添加评论详情 Json 到 Redis 中
     * @param data
     */
    private void batchAddCommentDetailJson2Redis(Map<String, String> data) {
        // 使用 Redis Pipeline 提升写入性能
        redisTemplate.executePipelined((RedisCallback<?>) (connection) -> {
            for (Map.Entry<String, String> entry : data.entrySet()) {
                // 将 Java 对象序列化为 JSON 字符串
                String jsonStr = JsonUtils.toJsonString(entry.getValue());

                // 随机生成过期时间 (5小时以内)
                int randomExpire = 60*60 + RandomUtil.randomInt(4 * 60 * 60);

                // 批量写入并设置过期时间
                connection.setEx(
                        redisTemplate.getStringSerializer().serialize(entry.getKey()),
                        randomExpire,
                        redisTemplate.getStringSerializer().serialize(jsonStr)
                );
            }
            return null;
        });
    }

    /**
     * 同步子评论到 Redis 中
     * @param parentCommentId
     * @param childCommentZSetKey
     */
    private void syncChildComments2Redis(Long parentCommentId, String childCommentZSetKey) {
        List<CommentDO> childCommentDOS = commentDOMapper.selectChildCommentsByParentIdAndLimit(parentCommentId, 6*10);
        if (CollUtil.isNotEmpty(childCommentDOS)) {
            // 使用 Redis Pipeline 提升写入性能
            redisTemplate.executePipelined((RedisCallback<Object>) connection -> {
                ZSetOperations<String, Object> zSetOps = redisTemplate.opsForZSet();

                // 遍历子评论数据并批量写入 ZSet
                for (CommentDO childCommentDO : childCommentDOS) {
                    Long commentId = childCommentDO.getId();
                    // create_time 转时间戳
                    long commentTimestamp = DateUtils.localDateTime2Timestamp(childCommentDO.getCreateTime());
                    zSetOps.add(childCommentZSetKey, commentId, commentTimestamp);
                }

                // 设置随机过期时间，（保底1小时 + 随机时间），单位：秒
                int randomExpiryTime = 60*60 + RandomUtil.randomInt(4 * 60 * 60); // 5小时以内
                redisTemplate.expire(childCommentZSetKey, randomExpiryTime, TimeUnit.SECONDS);
                return null; // 无返回值
            });
        }
    }

    /**
     * 同步评论计数到 Redis 中
     * @param countCommentKey
     * @param dbCount
     */
    private void syncCommentCount2Redis(String countCommentKey, Long dbCount) {
        redisTemplate.executePipelined(new SessionCallback<>() {
            @Override
            public Object execute(RedisOperations operations) {
                // 同步 hash 数据
                operations.opsForHash()
                        .put(countCommentKey, RedisKeyConstants.FIELD_CHILD_COMMENT_TOTAL, dbCount);

                // 随机过期时间 (保底1小时 + 随机时间)，单位：秒
                long expireTime = 60*60 + RandomUtil.randomInt(4*60*60);
                operations.expire(countCommentKey, expireTime, TimeUnit.SECONDS);
                return null;
            }
        });
    }


    /**
     * 设置评论 VO 的计数
     *
     * @param commentRspVOS 返参 VO 集合
     * @param expiredCommentIds 缓存中已失效的评论 ID 集合
     */
    private void setCommentCountData(List<FindCommentItemRspVO> commentRspVOS,
                                     List<Long> expiredCommentIds) {
        // 准备从评论 Hash 中查询计数 (子评论总数、被点赞数)
        // 缓存中存在的评论 ID
        List<Long> notExpiredCommentIds = Lists.newArrayList();

        // 遍历从缓存中解析出的 VO 集合，提取一级、二级评论 ID
        commentRspVOS.forEach(commentRspVO -> {
            Long oneLevelCommentId = commentRspVO.getCommentId();
            notExpiredCommentIds.add(oneLevelCommentId);
            List<FindCommentItemRspVO> childComments = commentRspVO.getChildComments();
            if (CollUtil.isNotEmpty(childComments)) {
                childComments.forEach(childCommentRspVO ->
                        notExpiredCommentIds.add(childCommentRspVO.getCommentId()));
            }
        });

        // 已失效的 Hash 评论 ID
        Map<Long, Map<Object, Object>> commentIdAndCountMap = getCommentCountDataAndSync2RedisHash(notExpiredCommentIds);

        // 遍历 VO, 设置对应评论的二级评论数、点赞数
        for (FindCommentItemRspVO commentRspVO : commentRspVOS) {
            // 评论 ID
            Long commentId = commentRspVO.getCommentId();

            // 若当前这条评论是从数据库中查询出来的, 则无需设置二级评论数、点赞数，以数据库查询出来的为主
            if (CollUtil.isNotEmpty(expiredCommentIds)
                    && expiredCommentIds.contains(commentId)) {
                continue;
            }

            // 设置一级评论的子评论总数、点赞数
            Map<Object, Object> hash = commentIdAndCountMap.get(commentId);
            if (CollUtil.isNotEmpty(hash)) {
                Object childCommentTotalObj = hash.get(RedisKeyConstants.FIELD_CHILD_COMMENT_TOTAL);
                Long childCommentTotal = Objects.isNull(childCommentTotalObj) ? 0 : Long.parseLong(childCommentTotalObj.toString());
                Object likeTotalObj = hash.get(RedisKeyConstants.FIELD_LIKE_TOTAL);
                Long likeTotal = Objects.isNull(likeTotalObj) ? 0 : Long.parseLong(likeTotalObj.toString());
                commentRspVO.setChildCommentTotal(childCommentTotal);
                commentRspVO.setLikeTotal(likeTotal);
                // 最初回复的二级评论
                List<FindCommentItemRspVO> childComments = commentRspVO.getChildComments();
                if (CollUtil.isNotEmpty(childComments)) {
                    childComments.forEach(childCommentRspVO -> {
                        Long firstCommentId = childCommentRspVO.getCommentId();
                        Map<Object, Object> firstCommentHash = commentIdAndCountMap.get(firstCommentId);
                        if (CollUtil.isNotEmpty(firstCommentHash)) {
                            Long firstCommentLikeTotal = Long.valueOf(firstCommentHash.get(RedisKeyConstants.FIELD_LIKE_TOTAL).toString());
                            childCommentRspVO.setLikeTotal(firstCommentLikeTotal);
                        }
                    });
                }
            }
        }
    }


    /**
     * 同步评论详情到本地缓存中
     *
     * @param commentRspVOS
     */
    private void syncCommentDetail2LocalCache(List<FindCommentItemRspVO> commentRspVOS) {
        // 开启一个异步线程
        threadPoolTaskExecutor.execute(() -> {
            // 构建缓存所需的键值
            Map<Long, String> localCacheData = Maps.newHashMap();
            commentRspVOS.forEach(commentRspVO -> {
                Long commentId = commentRspVO.getCommentId();
                localCacheData.put(commentId, JsonUtils.toJsonString(commentRspVO));
            });

            // 批量写入本地缓存
            LOCAL_CACHE.putAll(localCacheData);
        });
    }

    /**
     * 获取全部评论数据，并将评论详情同步到 Redis 中
     * @param oneLevelCommentDOS
     * @param noteId
     * @param commentRspVOS
     */
    private void getCommentDataAndSync2Redis(List<CommentDO> oneLevelCommentDOS, Long noteId, List<FindCommentItemRspVO> commentRspVOS) {
        // 过滤出所有最早回复的二级评论 ID
        List<Long> twoLevelCommentIds = oneLevelCommentDOS.stream()
                .map(CommentDO::getFirstReplyCommentId)
                .filter(firstReplyCommentId -> firstReplyCommentId != 0)
                .toList();

        // 查询二级评论
        Map<Long, CommentDO> commentIdAndDOMap = null;
        List<CommentDO> twoLevelCommonDOS = null;
        if (CollUtil.isNotEmpty(twoLevelCommentIds)) {
            twoLevelCommonDOS = commentDOMapper.selectTwoLevelCommentByIds(twoLevelCommentIds);

            // 转 Map 集合，方便后续拼装数据
            commentIdAndDOMap = twoLevelCommonDOS.stream()
                    .collect(Collectors.toMap(CommentDO::getId, commentDO -> commentDO));
        }

        // 调用 KV 服务需要的入参
        List<FindCommentContentReqDTO> findCommentContentReqDTOS = Lists.newArrayList();
        // 调用用户服务的入参
        List<Long> userIds = Lists.newArrayList();

        // 将一级评论和二级评论合并到一起
        List<CommentDO> allCommentDOS = Lists.newArrayList();
        CollUtil.addAll(allCommentDOS, oneLevelCommentDOS);
        CollUtil.addAll(allCommentDOS, twoLevelCommonDOS);

        // 循环提取 RPC 调用需要的入参数据
        allCommentDOS.forEach(commentDO -> {
            // 构建调用 KV 服务批量查询评论内容的入参
            boolean isContentEmpty = commentDO.getIsContentEmpty();
            if (!isContentEmpty) {
                FindCommentContentReqDTO findCommentContentReqDTO = FindCommentContentReqDTO.builder()
                        .contentId(commentDO.getContentUuid())
                        .yearMonth(DateConstants.DATE_FORMAT_Y_M.format(commentDO.getCreateTime()))
                        .build();
                findCommentContentReqDTOS.add(findCommentContentReqDTO);
            }

            // 构建调用用户服务批量查询用户信息的入参
            userIds.add(commentDO.getUserId());
        });

        // RPC: 调用 KV 服务，批量获取评论内容
        List<FindCommentContentRspDTO> findCommentContentRspDTOS =
                keyValueRpcService.batchFindCommentContent(noteId, findCommentContentReqDTOS);

        // DTO 集合转 Map, 方便后续拼装数据
        Map<String, String> commentUuidAndContentMap = null;
        if (CollUtil.isNotEmpty(findCommentContentRspDTOS)) {
            commentUuidAndContentMap = findCommentContentRspDTOS.stream()
                    .collect(Collectors.toMap(FindCommentContentRspDTO::getContentId, FindCommentContentRspDTO::getContent));
        }

        // RPC: 调用用户服务，批量获取用户信息（头像、昵称等）
        List<FindUserByIdRspDTO> findUserByIdRspDTOS = userRpcService.findByIds(userIds);

        // DTO 集合转 Map, 方便后续拼装数据
        Map<Long, FindUserByIdRspDTO> userIdAndDTOMap = null;
        if (CollUtil.isNotEmpty(findUserByIdRspDTOS)) {
            userIdAndDTOMap = findUserByIdRspDTOS.stream()
                    .collect(Collectors.toMap(FindUserByIdRspDTO::getId, dto -> dto));
        }

        // DO 转 VO, 组合拼装一二级评论数据
        for (CommentDO commentDO : oneLevelCommentDOS) {
            // 一级评论
            Long userId = commentDO.getUserId();
            FindCommentItemRspVO oneLevelCommentRspVO = FindCommentItemRspVO.builder()
                    .userId(userId)
                    .commentId(commentDO.getId())
                    .imageUrl(commentDO.getImageUrl())
                    .createTime(DateUtils.formatRelativeTime(commentDO.getCreateTime()))
                    .likeTotal(commentDO.getLikeTotal())
                    .childCommentTotal(commentDO.getChildCommentTotal())
                    .heat(commentDO.getHeat())
                    .build();

            // 用户信息
            setUserInfo(commentIdAndDOMap, userIdAndDTOMap, userId, oneLevelCommentRspVO);
            // 笔记内容
            setCommentContent(commentUuidAndContentMap, commentDO, oneLevelCommentRspVO);


            // 二级评论
            Long firstReplyCommentId = commentDO.getFirstReplyCommentId();
            if (CollUtil.isNotEmpty(commentIdAndDOMap)) {
                CommentDO firstReplyCommentDO = commentIdAndDOMap.get(firstReplyCommentId);
                if (Objects.nonNull(firstReplyCommentDO)) {
                    Long firstReplyCommentUserId = firstReplyCommentDO.getUserId();
                    FindCommentItemRspVO firstReplyCommentRspVO = FindCommentItemRspVO.builder()
                            .userId(firstReplyCommentDO.getUserId())
                            .commentId(firstReplyCommentDO.getId())
                            .imageUrl(firstReplyCommentDO.getImageUrl())
                            .createTime(DateUtils.formatRelativeTime(firstReplyCommentDO.getCreateTime()))
                            .likeTotal(firstReplyCommentDO.getLikeTotal())
                            .heat(firstReplyCommentDO.getHeat())
                            .build();

                    setUserInfo(commentIdAndDOMap, userIdAndDTOMap, firstReplyCommentUserId, firstReplyCommentRspVO);

                    // 子评论（需要带上最早回复的那条评论）
                    oneLevelCommentRspVO.setChildComments(Collections.singletonList(firstReplyCommentRspVO));
                    // 笔记内容
                    setCommentContent(commentUuidAndContentMap, firstReplyCommentDO, firstReplyCommentRspVO);
                }
            }
            commentRspVOS.add(oneLevelCommentRspVO);
        }

        // 异步将笔记详情，同步到 Redis 中
        threadPoolTaskExecutor.execute(() -> {
            // 准备批量写入的数据
            Map<String, String> data = Maps.newHashMap();
            commentRspVOS.forEach(commentRspVO -> {
                // 评论 ID
                Long commentId = commentRspVO.getCommentId();
                // 构建 Key
                String key = RedisKeyConstants.buildCommentDetailKey(commentId);
                data.put(key, JsonUtils.toJsonString(commentRspVO));
            });

            // 使用 Redis Pipeline 提升写入性能
            batchAddCommentDetailJson2Redis(data);
        });
    }

    /**
     * 同步热点评论至 Redis
     * @param key
     * @param noteId
     */
    private void syncHeatComments2Redis(String key, Long noteId) {
        List<CommentDO> commentDOS = commentDOMapper.selectHeatComments(noteId);
        if (CollUtil.isNotEmpty(commentDOS)) {
            // 使用 Redis Pipeline 提升写入性能
            redisTemplate.executePipelined((RedisCallback<Object>) connection -> {
                ZSetOperations<String, Object> zSetOps = redisTemplate.opsForZSet();

                // 遍历评论数据并批量写入 ZSet
                for (CommentDO commentDO : commentDOS) {
                    Long commentId = commentDO.getId();
                    Double commentHeat = commentDO.getHeat();
                    zSetOps.add(key, commentId, commentHeat);
                }

                // 设置随机过期时间，单位：秒
                int randomExpiryTime = RandomUtil.randomInt(5 * 60 * 60); // 5小时以内
                redisTemplate.expire(key, randomExpiryTime, TimeUnit.SECONDS);
                return null; // 无返回值
            });
        }
    }

    /**
     * 设置评论内容
     * @param commentUuidAndContentMap
     * @param commentDO1
     * @param firstReplyCommentRspVO
     */
    private static void setCommentContent(Map<String, String> commentUuidAndContentMap, CommentDO commentDO1, FindCommentItemRspVO firstReplyCommentRspVO) {
        if (CollUtil.isNotEmpty(commentUuidAndContentMap)) {
            String contentUuid = commentDO1.getContentUuid();
            if (StringUtils.isNotBlank(contentUuid)) {
                firstReplyCommentRspVO.setContent(commentUuidAndContentMap.get(contentUuid));
            }
        }
    }

    /**
     * 设置用户信息
     * @param commentIdAndDOMap
     * @param userIdAndDTOMap
     * @param userId
     * @param oneLevelCommentRspVO
     */
    private static void setUserInfo(Map<Long, CommentDO> commentIdAndDOMap, Map<Long, FindUserByIdRspDTO> userIdAndDTOMap, Long userId, FindCommentItemRspVO oneLevelCommentRspVO) {
        // if (CollUtil.isNotEmpty(commentIdAndDOMap)) {
            FindUserByIdRspDTO findUserByIdRspDTO = userIdAndDTOMap.get(userId);
            if (Objects.nonNull(findUserByIdRspDTO)) {
                oneLevelCommentRspVO.setAvatar(findUserByIdRspDTO.getAvatar());
                oneLevelCommentRspVO.setNickname(findUserByIdRspDTO.getNickName());
            }
        // }
    }


}
