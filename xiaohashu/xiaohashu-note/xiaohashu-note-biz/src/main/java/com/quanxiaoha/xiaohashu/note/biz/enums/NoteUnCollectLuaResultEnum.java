package com.quanxiaoha.xiaohashu.note.biz.enums;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.Objects;

/**
 * @author: 犬小哈
 * @url: www.quanxiaoha.com
 * @date: 2023-08-15 10:33
 * @description: 笔记取消收藏：执行 Lua 脚本返回结果
 **/
@Getter
@AllArgsConstructor
public enum NoteUnCollectLuaResultEnum {
    // 布隆过滤器不存在
    NOT_EXIST(-1L),
    // 笔记已收藏
    NOTE_COLLECTED(1L),
    // 笔记未收藏
    NOTE_NOT_COLLECTED(0L),
    ;

    private final Long code;

    /**
     * 根据类型 code 获取对应的枚举
     *
     * @param code
     * @return
     */
    public static NoteUnCollectLuaResultEnum valueOf(Long code) {
        for (NoteUnCollectLuaResultEnum noteUnCollectLuaResultEnum : NoteUnCollectLuaResultEnum.values()) {
            if (Objects.equals(code, noteUnCollectLuaResultEnum.getCode())) {
                return noteUnCollectLuaResultEnum;
            }
        }
        return null;
    }
}
