package com.quanxiaoha.xiaohashu.note.biz.config;

import org.apache.rocketmq.spring.autoconfigure.RocketMQAutoConfiguration;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Import;

/**
 * @author: 犬小哈
 * @url: www.quanxiaoha.com
 * @date: 2024/8/30 11:16
 * @description: RocketMQ 配置
 **/
@Configuration
@Import(RocketMQAutoConfiguration .class)
public class RocketMQConfig {
}
