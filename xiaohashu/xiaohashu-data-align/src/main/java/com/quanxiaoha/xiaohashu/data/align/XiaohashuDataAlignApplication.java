package com.quanxiaoha.xiaohashu.data.align;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.cloud.openfeign.EnableFeignClients;

@SpringBootApplication
@MapperScan("com.quanxiaoha.xiaohashu.data.align.domain.mapper")
@EnableFeignClients(basePackages = "com.quanxiaoha.xiaohashu")
public class XiaohashuDataAlignApplication {

    public static void main(String[] args) {
        SpringApplication.run(XiaohashuDataAlignApplication.class, args);
    }

}
