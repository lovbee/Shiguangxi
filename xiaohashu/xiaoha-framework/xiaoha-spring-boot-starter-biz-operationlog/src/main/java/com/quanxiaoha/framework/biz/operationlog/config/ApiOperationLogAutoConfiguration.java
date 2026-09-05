package com.quanxiaoha.framework.biz.operationlog.config;

import com.quanxiaoha.framework.biz.operationlog.aspect.ApiOperationLogAspect;
import org.springframework.boot.autoconfigure.AutoConfiguration;
import org.springframework.context.annotation.Bean;

/**
 * @author: 犬小哈
 * @date: 2024/4/15 13:50
 * @version: v1.0.0
 * @description: TODO
 **/
@AutoConfiguration
public class ApiOperationLogAutoConfiguration {

    @Bean
    public ApiOperationLogAspect apiOperationLogAspect() {
        return new ApiOperationLogAspect();
    }
}
