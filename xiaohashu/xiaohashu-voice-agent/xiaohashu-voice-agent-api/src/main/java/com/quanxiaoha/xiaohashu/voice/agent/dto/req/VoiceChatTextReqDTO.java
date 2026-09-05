package com.quanxiaoha.xiaohashu.voice.agent.dto.req;

import jakarta.validation.constraints.NotBlank;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 文本导购的一轮用户输入。
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@Builder
public class VoiceChatTextReqDTO {

    @NotBlank(message = "会话 ID 不能为空")
    private String sessionId;

    @NotBlank(message = "导购问题不能为空")
    private String utterance;
}
