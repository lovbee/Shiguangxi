package com.quanxiaoha.xiaohashu.note.biz.model.vo;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:17
 * @version: v1.0.0
 * @description: 查询个人主页笔记列表
 **/
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class FindProfileNotePageListReqVO {

    /**
     * 类型：1：所有，2：收藏，3：点赞
     */
    private Integer type = 0;

    @NotNull(message = "页码不能为空")
    private Integer pageNo = 1;

    @NotNull(message = "用户 ID 不能为空")
    private Long userId;

}
