package com.quanxiaoha.xiaohashu.gateway.filter;

import cn.dev33.satoken.reactor.context.SaReactorSyncHolder;
import cn.dev33.satoken.stp.StpUtil;
import com.quanxiaoha.framework.common.constant.GlobalConstants;
import lombok.extern.slf4j.Slf4j;
import org.springframework.cloud.gateway.filter.GatewayFilterChain;
import org.springframework.cloud.gateway.filter.GlobalFilter;
import org.springframework.core.Ordered;
import org.springframework.http.HttpHeaders;
import org.springframework.stereotype.Component;
import org.springframework.web.server.ServerWebExchange;
import reactor.core.publisher.Mono;

import java.util.UUID;

/**
 * @author: 犬小哈
 * @date: 2024/4/9 15:52
 * @version: v1.0.0
 * @description: 向下游服务透传经过 Sa-Token 校验的用户身份。
 **/
@Component
@Slf4j
public class AddUserId2HeaderFilter implements GlobalFilter, Ordered {

    private static final String AGENT_PATH_PREFIX = "/agent/";
    private static final String AGENT_HEADER_PREFIX = "X-Agent-";
    private static final String AGENT_USER_ID_HEADER = "X-Agent-User-Id";
    private static final String AGENT_REQUEST_ID_HEADER = "X-Agent-Request-Id";

    @Override
    public Mono<Void> filter(ServerWebExchange exchange, GatewayFilterChain chain) {
        // GlobalFilter runs after the Sa-Token WebFilter. Rebind its reactive request
        // context briefly so the token can be read from either Authorization or Cookie.
        SaReactorSyncHolder.setContext(exchange);
        Long userId;
        try {
            Object loginId = StpUtil.getLoginIdDefaultNull();
            userId = loginId == null ? null : Long.valueOf(loginId.toString());
        } finally {
            SaReactorSyncHolder.clearContext();
        }

        boolean agentRequest = exchange.getRequest().getPath().value().startsWith(AGENT_PATH_PREFIX);
        String requestId = agentRequest && userId != null ? UUID.randomUUID().toString() : null;

        ServerWebExchange downstreamExchange = exchange.mutate()
                .request(builder -> builder.headers(headers -> rewriteIdentityHeaders(headers, userId, agentRequest, requestId)))
                .build();
        return chain.filter(downstreamExchange);
    }

    private void rewriteIdentityHeaders(HttpHeaders headers, Long userId, boolean agentRequest, String requestId) {
        // Browser-provided identity headers must never reach any downstream service.
        headers.keySet().removeIf(name -> name.regionMatches(true, 0, AGENT_HEADER_PREFIX, 0, AGENT_HEADER_PREFIX.length()));
        headers.remove(GlobalConstants.USER_ID);

        if (userId == null) {
            return;
        }

        String userIdValue = String.valueOf(userId);
        // Existing Java services rely on this legacy header to populate LoginUserContextHolder.
        headers.set(GlobalConstants.USER_ID, userIdValue);

        if (agentRequest) {
            headers.set(AGENT_USER_ID_HEADER, userIdValue);
            headers.set(AGENT_REQUEST_ID_HEADER, requestId);
            log.debug("Injected trusted agent identity for user {}, request {}", userId, requestId);
        }
    }

    @Override
    public int getOrder() {
        // Must run before the Gateway HTTP and WebSocket routing filters copy headers upstream.
        return Ordered.HIGHEST_PRECEDENCE;
    }
}
