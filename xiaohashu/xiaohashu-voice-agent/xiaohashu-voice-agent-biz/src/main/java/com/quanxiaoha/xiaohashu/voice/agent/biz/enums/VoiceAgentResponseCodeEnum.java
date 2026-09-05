package com.quanxiaoha.xiaohashu.voice.agent.biz.enums;

import com.quanxiaoha.framework.common.exception.BaseExceptionInterface;
import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public enum VoiceAgentResponseCodeEnum implements BaseExceptionInterface {

    SYSTEM_ERROR("VOICE-10000", "Voice agent request failed."),
    PARAM_NOT_VALID("VOICE-10001", "Voice agent request is invalid."),
    USER_CONTEXT_MISSING("VOICE-20001", "Authenticated user context is missing."),
    UNSUPPORTED_SESSION_SCOPE("VOICE-20002", "This voice agent entry is not supported."),
    UPSTREAM_FAILURE("VOICE-30001", "Voice agent service is temporarily unavailable.");

    private final String errorCode;
    private final String errorMessage;
}
