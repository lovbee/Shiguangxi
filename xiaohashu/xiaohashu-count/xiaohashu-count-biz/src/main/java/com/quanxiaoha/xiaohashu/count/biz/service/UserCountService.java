package com.quanxiaoha.xiaohashu.count.biz.service;

import com.quanxiaoha.framework.common.response.Response;
import com.quanxiaoha.xiaohashu.count.dto.FindNoteCountByIdReqDTO;
import com.quanxiaoha.xiaohashu.count.dto.FindNoteCountByIdRspDTO;
import com.quanxiaoha.xiaohashu.count.dto.FindUserCountByIdReqDTO;
import com.quanxiaoha.xiaohashu.count.dto.FindUserCountByIdRspDTO;

/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:41
 * @version: v1.0.0
 * @description: 用户计数业务
 **/
public interface UserCountService {

    Response<FindUserCountByIdRspDTO> findUserCountData(FindUserCountByIdReqDTO findUserCountByIdReqDTO);
}
