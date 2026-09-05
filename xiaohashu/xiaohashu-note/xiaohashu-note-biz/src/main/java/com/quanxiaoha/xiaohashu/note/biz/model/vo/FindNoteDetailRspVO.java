package com.quanxiaoha.xiaohashu.note.biz.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigInteger;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:17
 * @version: v1.0.0
 * @description: 查询笔记详情
 **/
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class FindNoteDetailRspVO {

    private Long id;

    private Integer type;

    private String title;

    private String content;

    private List<String> imgUris;

    /**
     * 话题集合
     */
    List<FindTopicRspVO> topics;

    private Long creatorId;

    private String creatorName;

    private String avatar;

    private String videoUri;

    /**
     * 编辑时间
     */
    private String updateTime;

    /**
     * 是否可见
     */
    private Integer visible;

    /**
     * 被点赞数
     */
    private String likeTotal;

    /**
     * 被收藏数
     */
    private String collectTotal;

    /**
     * 被评论数
     */
    private String commentTotal;

}
