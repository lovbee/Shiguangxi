package com.quanxiaoha.xiaohashu.voice.agent.biz.config;

import com.quanxiaoha.framework.biz.context.holder.LoginUserContextHolder;
import com.quanxiaoha.framework.common.exception.BizException;
import com.quanxiaoha.xiaohashu.voice.agent.biz.enums.VoiceAgentResponseCodeEnum;
import feign.RequestInterceptor;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.util.UUID;

/**
 * Sends only the trusted gateway identity to the Python internal service.
 */
@Configuration(proxyBeanMethods = false)
public class VoiceAgentFeignConfiguration {

    private static final String AGENT_USER_ID_HEADER = "X-Agent-User-Id";
    private static final String AGENT_REQUEST_ID_HEADER = "X-Agent-Request-Id";
    private static final String LEGACY_USER_ID_HEADER = "userId";

    @Bean
    public RequestInterceptor voiceAgentIdentityRequestInterceptor() {
        return requestTemplate -> {
            Long userId = LoginUserContextHolder.getUserId();
            if (userId == null || userId <= 0) {
                throw new BizException(VoiceAgentResponseCodeEnum.USER_CONTEXT_MISSING);
            }

            // Feign configurations may be composed. Remove every identity header before
            // adding the authenticated identity from the servlet request context.
            requestTemplate.removeHeader(LEGACY_USER_ID_HEADER);
            requestTemplate.removeHeader(AGENT_USER_ID_HEADER);
            requestTemplate.removeHeader(AGENT_REQUEST_ID_HEADER);
            requestTemplate.header(AGENT_USER_ID_HEADER, userId.toString());
            requestTemplate.header(AGENT_REQUEST_ID_HEADER, requestId());
        };
    }

    private String requestId() {
        ServletRequestAttributes attributes = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attributes != null) {
            HttpServletRequest request = attributes.getRequest();
            String requestId = request.getHeader(AGENT_REQUEST_ID_HEADER);
            if (isUuid(requestId)) {
                return requestId;
            }
        }
        return UUID.randomUUID().toString();
    }

    private boolean isUuid(String value) {
        if (value == null || value.isBlank()) {
            return false;
        }
        try {
            UUID.fromString(value);
            return true;
        } catch (IllegalArgumentException ignored) {
            return false;
        }
    }
}
