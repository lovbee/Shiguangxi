package com.quanxiaoha.xiaohashu.search.biz;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
@MapperScan("com.quanxiaoha.xiaohashu.search.biz.domain.mapper")
public class XiaohashuSearchBizApplication {

    public static void main(String[] args) {
        SpringApplication.run(XiaohashuSearchBizApplication.class, args);
    }

}
