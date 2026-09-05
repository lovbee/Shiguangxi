package com.quanxiaoha.xiaohashu.auth.alarm;

/**
 * @author: 犬小哈
 * @date: 2024/6/7 15:24
 * @version: v1.0.0
 * @description: 告警接口
 **/
public interface AlarmInterface {

    /**
     * 发送告警信息
     *
     * @param message
     * @return
     */
    boolean send(String message);
}
