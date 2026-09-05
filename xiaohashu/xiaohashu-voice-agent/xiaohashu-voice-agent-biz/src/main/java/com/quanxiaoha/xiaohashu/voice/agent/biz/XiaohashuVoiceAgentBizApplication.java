package com.quanxiaoha.xiaohashu.voice.agent.biz;

import com.quanxiaoha.framework.biz.context.config.FeignContextAutoConfiguration;
import com.quanxiaoha.xiaohashu.voice.agent.api.VoiceSaleAgentFeignClient;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

/**
 * Java facade for the independently deployed Python voice sale agent.
 */
@SpringBootApplication(exclude = FeignContextAutoConfiguration.class)
@EnableFeignClients(basePackageClasses = VoiceSaleAgentFeignClient.class)
public class XiaohashuVoiceAgentBizApplication {

    public static void main(String[] args) {
        SpringApplication.run(XiaohashuVoiceAgentBizApplication.class, args);
    }
}
