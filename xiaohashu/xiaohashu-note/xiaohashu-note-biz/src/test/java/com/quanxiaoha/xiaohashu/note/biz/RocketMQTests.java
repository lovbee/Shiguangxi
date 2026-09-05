package com.quanxiaoha.xiaohashu.note.biz;

import com.alibaba.druid.filter.config.ConfigTools;
import jakarta.annotation.Resource;
import lombok.SneakyThrows;
import lombok.extern.slf4j.Slf4j;
import org.apache.rocketmq.spring.core.RocketMQTemplate;
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;

import java.util.concurrent.TimeUnit;


@SpringBootTest
@Slf4j
class RocketMQTests {

    @Resource
    private RocketMQTemplate rocketMQTemplate;

    @Test
    @SneakyThrows
    void testSendMQ() {
        String topic = "test_topic";
        rocketMQTemplate.convertAndSend(topic, "Hello World");
        log.info("MQ 发送成功...");
        TimeUnit.SECONDS.sleep(3);
    }

    @Test
    void testSendDelayMQ() {
        String topic = "test_topic";

        Message<String> message = MessageBuilder.withPayload("延时消息").build();
        rocketMQTemplate.syncSend(topic, message, 6000, 3);
        log.info("MQ 发送成功...");
    }

}
