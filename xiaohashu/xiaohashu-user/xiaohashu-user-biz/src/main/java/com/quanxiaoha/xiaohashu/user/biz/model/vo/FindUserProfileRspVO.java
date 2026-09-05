package com.quanxiaoha.xiaohashu.user.biz.model.vo;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:17
 * @version: v1.0.0
 * @description: 获取用户主页信息
 **/
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class FindUserProfileRspVO {

    private Long userId;
    private String avatar;
    private String nickname;
    private String xiaohashuId;
    private Integer sex;
    private Integer age;
    private LocalDate birthday;
    private String introduction;
    private String followingTotal = "0";
    private String fansTotal = "0";
    private String likeAndCollectTotal = "0";
}
