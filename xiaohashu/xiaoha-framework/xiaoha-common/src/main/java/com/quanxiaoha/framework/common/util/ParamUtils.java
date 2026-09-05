package com.quanxiaoha.framework.common.util;

import java.util.regex.Pattern;

/**
 * @author: 犬小哈
 * @date: 2024/4/15 16:42
 * @version: v1.0.0
 * @description: 参数条件工具
 **/
public final class ParamUtils {
    private ParamUtils() {
    }

    // ============================== 校验昵称 ==============================
    private static final int NICK_NAME_MIN_LENGTH = 2;
    private static final int NICK_NAME_MAX_LENGTH = 24;
    private static final String NICK_NAME_REGEX = "[!@#$%^&*(),.?\":{}|<>]";

    public static boolean checkNickname(String nickname) {
        if (nickname.length() < NICK_NAME_MIN_LENGTH || nickname.length() > NICK_NAME_MAX_LENGTH) {
            return false;
        }

        Pattern pattern = Pattern.compile(NICK_NAME_REGEX);
        return !pattern.matcher(nickname).find();
    }

    // ============================== 校验小哈书号 ==============================
    private static final int ID_MIN_LENGTH = 6;
    private static final int ID_MAX_LENGTH = 15;
    private static final String ID_REGEX = "^[a-zA-Z0-9_]+$";

    public static boolean checkXiaohashuId(String xiaohashuId) {
        if (xiaohashuId.length() < ID_MIN_LENGTH || xiaohashuId.length() > ID_MAX_LENGTH) {
            return false;
        }

        Pattern pattern = Pattern.compile(ID_REGEX);
        return pattern.matcher(xiaohashuId).matches();
    }

    public static boolean checkLength(String str, int length) {
        return !str.isEmpty() && str.length() <= length;
    }
}
