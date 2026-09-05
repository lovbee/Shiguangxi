package com.quanxiaoha.xiaohashu.voice.agent.dto.rsp;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 智能导购会话可访问范围。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class StartVoiceSessionRspDTO {

    private Long userId;

    private List<Long> allowedMerchantIds;

    private Long boundProductId;
}
