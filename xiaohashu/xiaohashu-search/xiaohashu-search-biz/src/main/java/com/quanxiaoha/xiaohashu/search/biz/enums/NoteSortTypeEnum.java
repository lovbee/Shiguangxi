package com.quanxiaoha.xiaohashu.search.biz.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.Objects;

/**
 * @author: 犬小哈
 * @url: www.quanxiaoha.com
 * @date: 2023-08-15 10:33
 * @description: 笔记排序类型
 **/
@Getter
@AllArgsConstructor
public enum NoteSortTypeEnum {

    // 最新
    LATEST(0),
    // 最新点赞
    MOST_LIKE(1),
    // 最多评论
    MOST_COMMENT(2),
    // 最多收藏
    MOST_COLLECT(3),
    ;

    private final Integer code;

    /**
     * 根据类型 code 获取对应的枚举
     *
     * @param code
     * @return
     */
    public static NoteSortTypeEnum valueOf(Integer code) {
        for (NoteSortTypeEnum noteSortTypeEnum : NoteSortTypeEnum.values()) {
            if (Objects.equals(code, noteSortTypeEnum.getCode())) {
                return noteSortTypeEnum;
            }
        }
        return null;
    }

}
