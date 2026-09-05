package com.quanxiaoha.xiaohashu.oss.biz.service;

import com.quanxiaoha.framework.common.response.Response;
import org.springframework.web.multipart.MultipartFile;

/**
 * @author: 犬小哈
 * @date: 2024/4/11 17:12
 * @version: v1.0.0
 * @description: TODO
 **/
public interface FileService {

    /**
     * 上传文件
     *
     * @param file
     * @return
     */
    Response<?> uploadFile(MultipartFile file);
}
