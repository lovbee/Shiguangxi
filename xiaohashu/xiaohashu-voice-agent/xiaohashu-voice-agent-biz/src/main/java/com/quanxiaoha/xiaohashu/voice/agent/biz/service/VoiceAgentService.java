package com.quanxiaoha.xiaohashu.voice.agent.biz.service;

import com.quanxiaoha.xiaohashu.voice.agent.dto.req.StartVoiceSessionReqDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.req.VoiceChatTextReqDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.StartVoiceSessionRspDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.VoiceAgentOrderRspDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.VoiceChatTextRspDTO;

import java.util.List;

public interface VoiceAgentService {

    StartVoiceSessionRspDTO startSession(StartVoiceSessionReqDTO request);

    VoiceChatTextRspDTO chatText(VoiceChatTextReqDTO request);

    List<VoiceAgentOrderRspDTO> listMyOrders();
}
