package com.quanxiaoha.xiaohashu.search.biz.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:17
 * @version: v1.0.0
 * @description: 搜索笔记
 **/
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class SearchNoteRspVO {

    /**
     * 笔记ID
     */
    private String id;

    private Integer type;

    /**
     * 封面
     */
    private String cover;

    private String videoUri;

    /**
     * 标题
     */
    private String title;

    /**
     * 标题：关键词高亮
     */
    private String highlightTitle;

    /**
     * 发布者头像
     */
    private String avatar;

    /**
     * 发布者昵称
     */
    private String nickname;

    private Long creatorId;

    /**
     * 最后一次编辑时间
     */
    private String updateTime;

    /**
     * 被评论数
     */
    private String commentTotal;

    /**
     * 被收藏数
     */
    private String collectTotal;

    /**
     * 被点赞总数
     */
    private String likeTotal;

}
