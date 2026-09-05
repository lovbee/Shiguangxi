package com.quanxiaoha.xiaohashu.voice.agent.dto.rsp;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

/**
 * 文本导购的一轮执行结果。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class VoiceChatTextRspDTO {

    private String speechText;

    private List<RecommendedProductRspDTO> displayBlocks;

    private String intent;

    private String phase;
}
