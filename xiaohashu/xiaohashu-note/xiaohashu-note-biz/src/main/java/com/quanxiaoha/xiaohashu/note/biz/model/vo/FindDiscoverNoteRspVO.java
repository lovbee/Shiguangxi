package com.quanxiaoha.xiaohashu.note.biz.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;


/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:17
 * @version: v1.0.0
 * @description: 查询发现页笔记
 **/
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class FindDiscoverNoteRspVO {

    /**
     * 笔记 ID
     */
    private String id;

    /**
     * 笔记类型
     */
    private Integer type;

    /**
     * 封面图
     */
    private String cover;

    /**
     * 视频连接
     */
    private String videoUri;

    /**
     * 标题
     */
    private String title;

    /**
     * 发布者用户 ID
     */
    private Long creatorId;

    /**
     * 昵称
     */
    private String nickname;

    /**
     * 头像
     */
    private String avatar;

    /**
     * 被点赞量
     */
    private String likeTotal;

}
