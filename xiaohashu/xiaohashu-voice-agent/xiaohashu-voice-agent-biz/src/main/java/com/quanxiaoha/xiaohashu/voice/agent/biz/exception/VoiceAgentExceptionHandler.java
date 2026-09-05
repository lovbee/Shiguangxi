package com.quanxiaoha.xiaohashu.voice.agent.biz.exception;

import com.quanxiaoha.framework.common.exception.BizException;
import com.quanxiaoha.framework.common.response.Response;
import com.quanxiaoha.xiaohashu.voice.agent.biz.enums.VoiceAgentResponseCodeEnum;
import feign.FeignException;
import jakarta.servlet.http.HttpServletRequest;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * Keeps facade failures in the response envelope consumed by the Vue client.
 */
@RestControllerAdvice
@Slf4j
public class VoiceAgentExceptionHandler {

    @ExceptionHandler(BizException.class)
    public Response<Object> handleBizException(HttpServletRequest request, BizException exception) {
        log.warn("Voice agent request rejected: path={}, code={}", request.getRequestURI(), exception.getErrorCode());
        return Response.fail(exception);
    }

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public Response<Object> handleValidationException(HttpServletRequest request, MethodArgumentNotValidException exception) {
        BindingResult bindingResult = exception.getBindingResult();
        String message = bindingResult.getFieldErrors().stream()
                .findFirst()
                .map(error -> error.getField() + " " + error.getDefaultMessage())
                .orElse(VoiceAgentResponseCodeEnum.PARAM_NOT_VALID.getErrorMessage());
        log.warn("Voice agent request validation failed: path={}", request.getRequestURI());
        return Response.fail(VoiceAgentResponseCodeEnum.PARAM_NOT_VALID.getErrorCode(), message);
    }

    @ExceptionHandler(IllegalArgumentException.class)
    public Response<Object> handleIllegalArgumentException(HttpServletRequest request, IllegalArgumentException exception) {
        log.warn("Voice agent request validation failed: path={}", request.getRequestURI());
        return Response.fail(VoiceAgentResponseCodeEnum.PARAM_NOT_VALID.getErrorCode(), exception.getMessage());
    }

    @ExceptionHandler(FeignException.class)
    public Response<Object> handleFeignException(HttpServletRequest request, FeignException exception) {
        log.warn("Voice agent upstream request failed: path={}, status={}", request.getRequestURI(), exception.status());
        return Response.fail(VoiceAgentResponseCodeEnum.UPSTREAM_FAILURE);
    }

    @ExceptionHandler(Exception.class)
    public Response<Object> handleUnexpectedException(HttpServletRequest request, Exception exception) {
        log.error("Voice agent request failed: path={}, exception={}", request.getRequestURI(), exception.getClass().getSimpleName());
        return Response.fail(VoiceAgentResponseCodeEnum.SYSTEM_ERROR);
    }
}
