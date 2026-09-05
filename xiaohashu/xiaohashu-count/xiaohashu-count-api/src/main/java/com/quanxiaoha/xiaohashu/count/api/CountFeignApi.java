package com.quanxiaoha.xiaohashu.count.api;

import com.quanxiaoha.framework.common.response.Response;
import com.quanxiaoha.xiaohashu.count.constant.ApiConstants;
import com.quanxiaoha.xiaohashu.count.dto.FindNoteCountByIdReqDTO;
import com.quanxiaoha.xiaohashu.count.dto.FindNoteCountByIdRspDTO;
import com.quanxiaoha.xiaohashu.count.dto.FindUserCountByIdReqDTO;
import com.quanxiaoha.xiaohashu.count.dto.FindUserCountByIdRspDTO;
import org.springframework.cloud.openfeign.FeignClient;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;

/**
 * @author: 犬小哈
 * @date: 2024/4/13 22:56
 * @version: v1.0.0
 * @description: TODO
 **/
@FeignClient(name = ApiConstants.SERVICE_NAME)
public interface CountFeignApi {

    String PREFIX = "/count";

    /**
     * 查询笔记计数
     *
     * @param findNoteCountByIdReqDTO
     * @return
     */
    @PostMapping(value = PREFIX + "/note/data")
    Response<FindNoteCountByIdRspDTO> findNoteCount(@RequestBody FindNoteCountByIdReqDTO findNoteCountByIdReqDTO);

    /**
     * 查询笔记计数
     *
     * @param findUserCountByIdReqDTO
     * @return
     */
    @PostMapping(value = PREFIX + "/user/data")
    Response<FindUserCountByIdRspDTO> findUserCount(@RequestBody FindUserCountByIdReqDTO findUserCountByIdReqDTO);

}
