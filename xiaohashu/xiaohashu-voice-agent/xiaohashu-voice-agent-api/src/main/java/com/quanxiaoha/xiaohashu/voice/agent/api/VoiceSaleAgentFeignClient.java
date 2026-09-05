package com.quanxiaoha.xiaohashu.voice.agent.api;

import com.quanxiaoha.xiaohashu.voice.agent.config.VoiceSaleAgentFeignConfig;
import com.quanxiaoha.xiaohashu.voice.agent.dto.req.StartVoiceSessionReqDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.req.VoiceChatTextReqDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.StartVoiceSessionRspDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.VoiceAgentOrderRspDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.VoiceChatTextRspDTO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

import java.util.List;

/**
 * Python 智能导购内部 HTTP 服务契约。
 *
 * <p>此客户端只能由 Java 门面在内网调用。用户身份通过业务模块注入的
 * {@code X-Agent-User-Id} 请求头透传，不能由浏览器请求体提供。</p>
 */
@FeignClient(
        name = "voiceSaleAgent",
        url = "${voice-sale-agent.base-url}",
        path = VoiceSaleAgentFeignClient.PREFIX,
        configuration = VoiceSaleAgentFeignConfig.class
)
public interface VoiceSaleAgentFeignClient {

    String PREFIX = "/internal/v1";

    @PostMapping("/sessions/start")
    StartVoiceSessionRspDTO startSession(@RequestBody StartVoiceSessionReqDTO request);

    @PostMapping("/chat/text")
    VoiceChatTextRspDTO chatText(@RequestBody VoiceChatTextReqDTO request);

    @GetMapping("/orders/mine")
    List<VoiceAgentOrderRspDTO> listMyOrders();
}
