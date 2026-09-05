package com.quanxiaoha.xiaohashu.count.biz;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.quanxiaoha.xiaohashu.count.biz.domain.mapper")
public class XiaohashuCountBizApplication {

    public static void main(String[] args) {
        SpringApplication.run(XiaohashuCountBizApplication.class, args);
    }

}
