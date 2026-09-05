package com.quanxiaoha.xiaohashu.voice.agent.config;

import org.springframework.context.annotation.Configuration;

/**
 * Python 智能导购服务的 Feign 客户端配置。
 *
 * <p>具体身份透传由业务模块的 RequestInterceptor 提供，避免 API 模块依赖
 * Servlet 请求上下文。</p>
 */
@Configuration
public class VoiceSaleAgentFeignConfig {
}
