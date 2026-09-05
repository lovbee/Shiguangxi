package com.quanxiaoha.xiaohashu.voice.agent.dto.req;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 创建或复用智能导购会话的请求参数。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class StartVoiceSessionReqDTO {

    @NotBlank(message = "会话 ID 不能为空")
    private String sessionId;

    @NotNull(message = "导购入口不能为空")
    private VoiceSessionChannel channel;

    private Long merchantId;

    private Long boundProductId;
}
