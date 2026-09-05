package com.quanxiaoha.xiaohashu.count.dto;

import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:17
 * @version: v1.0.0
 * @description: 根据笔记 ID 查询计数
 **/
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class FindNoteCountByIdReqDTO {

    /**
     * 笔记 ID
     */
    @NotNull(message = "笔记 ID 不能为空")
    private Long noteId;

}
