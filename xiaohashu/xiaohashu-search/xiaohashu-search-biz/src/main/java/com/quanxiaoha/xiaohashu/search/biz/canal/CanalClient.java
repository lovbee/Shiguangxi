package com.quanxiaoha.xiaohashu.search.biz.canal;

import com.alibaba.otter.canal.client.CanalConnector;
import com.alibaba.otter.canal.client.CanalConnectors;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Component;

import java.net.InetSocketAddress;
import java.util.Objects;

/**
 * @author: 犬小哈
 * @date: 2024/12/14 16:23
 * @version: v1.0.0
 * @description: TODO
 **/
@Component
@Slf4j
public class CanalClient implements DisposableBean {

    @Resource
    private CanalProperties canalProperties;

    private CanalConnector canalConnector;

    /**
     * 实例化 Canal 链接对象
     * @return
     */
    @Bean
    public CanalConnector getCanalConnector() {
        // Canal 链接地址
        String address = canalProperties.getAddress();
        String[] addressArr = address.split(":");
        // IP 地址
        String host = addressArr[0];
        // 端口
        int port = Integer.parseInt(addressArr[1]);

        // 创建一个 CanalConnector 实例，连接到指定的 Canal 服务端
        canalConnector = CanalConnectors.newSingleConnector(
                        new InetSocketAddress(host, port),
                canalProperties.getDestination(),
                canalProperties.getUsername(),
                canalProperties.getPassword());

        // 连接到 Canal 服务端
        canalConnector.connect();
        // 订阅 Canal 中的数据变化，指定要监听的数据库和表（可以使用表名、数据库名的通配符）
        canalConnector.subscribe(canalProperties.getSubscribe());
        // 回滚 Canal 消费者的位点，回滚到上次提交的消费位置
        canalConnector.rollback();
        return canalConnector;
    }

    /**
     * 在 Spring 容器销毁时释放资源
     * @throws Exception
     */
    @Override
    public void destroy() throws Exception {
        if (Objects.nonNull(canalConnector)) {
            // 断开 canalConnector 与 Canal 服务的连接
            canalConnector.disconnect();
        }
    }
}
