package com.quanxiaoha.xiaohashu.voice.agent.dto.rsp;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.time.LocalDateTime;

/**
 * Python Agent 演示订单视图。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class VoiceAgentOrderRspDTO {

    private Long id;

    private String orderNo;

    private Long userId;

    private Long merchantId;

    private String sessionId;

    private Long productId;

    private String skuCode;

    private Integer quantity;

    private BigDecimal unitPrice;

    private BigDecimal totalAmount;

    private String status;

    private LocalDateTime createdAt;
}
