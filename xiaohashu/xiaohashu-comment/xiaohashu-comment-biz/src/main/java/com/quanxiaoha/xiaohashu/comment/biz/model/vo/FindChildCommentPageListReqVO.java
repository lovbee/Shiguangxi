package com.quanxiaoha.xiaohashu.comment.biz.model.vo;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:17
 * @version: v1.0.0
 * @description: 查询二级评论分页数据
 **/
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class FindChildCommentPageListReqVO {

    @NotNull(message = "父评论 ID 不能为空")
    private Long parentCommentId;

    @NotNull(message = "页码不能为空")
    private Integer pageNo = 1;
}
