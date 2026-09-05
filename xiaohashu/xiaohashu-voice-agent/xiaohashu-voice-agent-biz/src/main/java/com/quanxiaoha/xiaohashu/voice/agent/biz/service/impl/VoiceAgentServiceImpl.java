package com.quanxiaoha.xiaohashu.voice.agent.biz.service.impl;

import com.quanxiaoha.framework.common.exception.BizException;
import com.quanxiaoha.xiaohashu.voice.agent.api.VoiceSaleAgentFeignClient;
import com.quanxiaoha.xiaohashu.voice.agent.biz.enums.VoiceAgentResponseCodeEnum;
import com.quanxiaoha.xiaohashu.voice.agent.biz.service.VoiceAgentService;
import com.quanxiaoha.xiaohashu.voice.agent.dto.req.StartVoiceSessionReqDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.req.VoiceChatTextReqDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.req.VoiceSessionChannel;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.StartVoiceSessionRspDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.VoiceAgentOrderRspDTO;
import com.quanxiaoha.xiaohashu.voice.agent.dto.rsp.VoiceChatTextRspDTO;
import jakarta.annotation.Resource;
import org.springframework.stereotype.Service;

import java.util.List;

/**
 * Keeps the first release scoped to the home-entry agent flow.
 */
@Service
public class VoiceAgentServiceImpl implements VoiceAgentService {

    @Resource
    private VoiceSaleAgentFeignClient voiceSaleAgentFeignClient;

    @Override
    public StartVoiceSessionRspDTO startSession(StartVoiceSessionReqDTO request) {
        validateHomeEntryScope(request);
        return voiceSaleAgentFeignClient.startSession(request);
    }

    @Override
    public VoiceChatTextRspDTO chatText(VoiceChatTextReqDTO request) {
        return voiceSaleAgentFeignClient.chatText(request);
    }

    @Override
    public List<VoiceAgentOrderRspDTO> listMyOrders() {
        return voiceSaleAgentFeignClient.listMyOrders();
    }

    private void validateHomeEntryScope(StartVoiceSessionReqDTO request) {
        boolean unsupportedChannel = request.getChannel() != VoiceSessionChannel.HOME_ENTRY;
        boolean hasMerchantScope = request.getMerchantId() != null;
        boolean hasProductScope = request.getBoundProductId() != null;
        if (unsupportedChannel || hasMerchantScope || hasProductScope) {
            throw new BizException(VoiceAgentResponseCodeEnum.UNSUPPORTED_SESSION_SCOPE);
        }
    }
}
