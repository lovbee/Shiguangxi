package com.quanxiaoha.framework.common.validator;

import jakarta.validation.Constraint;
import jakarta.validation.Payload;

import java.lang.annotation.*;

/**
 * @author: 犬小哈
 * @date: 2024/4/15 22:22
 * @version: v1.0.0
 * @description: 自定义手机号校验注解
 **/
@Target({ ElementType.METHOD, ElementType.FIELD, ElementType.ANNOTATION_TYPE, ElementType.PARAMETER })
@Retention(RetentionPolicy.RUNTIME)
@Constraint(validatedBy = PhoneNumberValidator.class)
public @interface PhoneNumber {

    String message() default "手机号格式不正确, 需为 11 位数字";

    Class<?>[] groups() default {};

    Class<? extends Payload>[] payload() default {};
}
