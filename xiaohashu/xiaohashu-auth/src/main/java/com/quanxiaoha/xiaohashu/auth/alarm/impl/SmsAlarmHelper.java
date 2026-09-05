package com.quanxiaoha.xiaohashu.auth.alarm.impl;

import com.quanxiaoha.xiaohashu.auth.alarm.AlarmInterface;
import lombok.extern.slf4j.Slf4j;

/**
 * @author: 犬小哈
 * @date: 2024/6/7 15:26
 * @version: v1.0.0
 * @description: 短信告警
 **/
@Slf4j
public class SmsAlarmHelper implements AlarmInterface {

    /**
     * 发送告警信息
     *
     * @param message
     * @return
     */
    @Override
    public boolean send(String message) {
        log.info("==> 【短信告警】：{}", message);

        // 业务逻辑...

        return true;
    }
}
