package com.quanxiaoha.xiaohashu.comment.biz.enums;

import com.quanxiaoha.framework.common.exception.BaseExceptionInterface;
import lombok.AllArgsConstructor;
import lombok.Getter;

/**
 * @author: 犬小哈
 * @url: www.quanxiaoha.com
 * @date: 2023-08-15 10:33
 * @description: 响应异常码
 **/
@Getter
@AllArgsConstructor
public enum ResponseCodeEnum implements BaseExceptionInterface {

    // ----------- 通用异常状态码 -----------
    SYSTEM_ERROR("COMMENT-10000", "出错啦，后台小哥正在努力修复中..."),
    PARAM_NOT_VALID("COMMENT-10001", "参数错误"),

    // ----------- 业务异常状态码 -----------
    PARENT_COMMENT_NOT_FOUND("COMMENT-20000", "此父评论不存在"),
    COMMENT_NOT_FOUND("COMMENT-20001", "此评论不存在"),
    COMMENT_ALREADY_LIKED("COMMENT-20002", "您已经点赞过该评论"),
    COMMENT_NOT_LIKED("COMMENT-20003", "您未点赞该评论，无法取消点赞"),
    COMMENT_CANT_OPERATE("COMMENT-20004", "您无法操作该评论"),
    ;

    // 异常码
    private final String errorCode;
    // 错误信息
    private final String errorMessage;

}
