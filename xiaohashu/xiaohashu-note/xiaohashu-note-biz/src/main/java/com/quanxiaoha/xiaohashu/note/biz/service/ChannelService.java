package com.quanxiaoha.xiaohashu.note.biz.service;


import com.quanxiaoha.framework.common.response.Response;
import com.quanxiaoha.xiaohashu.note.biz.model.vo.FindChannelRspVO;

import java.util.List;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:41
 * @version: v1.0.0
 * @description: 频道业务
 **/
public interface ChannelService {

    /**
     * 查询所有频道
     * @return
     */
    Response<List<FindChannelRspVO>> findChannelList();
}
