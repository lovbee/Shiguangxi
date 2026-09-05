package com.quanxiaoha.xiaohashu.voice.agent.biz.controller;

import com.quanxiaoha.framework.common.response.Response;
import com.quanxiaoha.xiaohashu.voice.agent.biz.service.VoiceAgentService;
import com.quanxiaoha.xiaohashu.voice.agent.dto.req.StartVoiceSessionReqDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.req.VoiceChatTextReqDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.StartVoiceSessionRspDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.VoiceAgentOrderRspDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.VoiceChatTextRspDTO;
import jakarta.annotation.Resource;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/**
 * Public HTTP facade. Gateway strips the /agent prefix before forwarding here.
 */
@RestController
public class VoiceAgentController {

    @Resource
    private VoiceAgentService voiceAgentService;

    @PostMapping("/sessions")
    public Response<StartVoiceSessionRspDTO> startSession(@Valid @RequestBody StartVoiceSessionReqDTO request) {
        return Response.success(voiceAgentService.startSession(request));
    }

    @PostMapping("/chat/text")
    public Response<VoiceChatTextRspDTO> chatText(@Valid @RequestBody VoiceChatTextReqDTO request) {
        return Response.success(voiceAgentService.chatText(request));
    }

    @GetMapping("/orders/mine")
    public Response<List<VoiceAgentOrderRspDTO>> listMyOrders() {
        return Response.success(voiceAgentService.listMyOrders());
    }
}
