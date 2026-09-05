package com.quanxiaoha.xiaohashu.voice.agent.dto.rsp;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.math.BigDecimal;
import java.util.Map;

/**
 * Agent 返回的一张商品推荐卡片。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class RecommendedProductRspDTO {

    private Long productId;

    private String name;

    private BigDecimal price;

    private String reason;

    private Double matchScore;

    private Map<String, Object> attributes;
}
