package com.quanxiaoha.xiaohashu.note.biz.service.impl;

import cn.hutool.core.collection.CollUtil;
import com.google.common.collect.Lists;
import com.google.common.collect.Maps;
import com.quanxiaoha.framework.biz.context.holder.LoginUserContextHolder;
import com.quanxiaoha.framework.common.response.PageResponse;
import com.quanxiaoha.xiaohashu.note.biz.domain.dataobject.NoteCountDO;
import com.quanxiaoha.xiaohashu.note.biz.domain.dataobject.NoteDO;
import com.quanxiaoha.xiaohashu.note.biz.domain.mapper.NoteCollectionDOMapper;
import com.quanxiaoha.xiaohashu.note.biz.domain.mapper.NoteCountDOMapper;
import com.quanxiaoha.xiaohashu.note.biz.domain.mapper.NoteDOMapper;
import com.quanxiaoha.xiaohashu.note.biz.domain.mapper.NoteLikeDOMapper;
import com.quanxiaoha.xiaohashu.note.biz.enums.NoteTypeEnum;
import com.quanxiaoha.xiaohashu.note.biz.enums.ProfileNoteTypeEnum;
import com.quanxiaoha.xiaohashu.note.biz.model.vo.FindDiscoverNoteRspVO;
import com.quanxiaoha.xiaohashu.note.biz.model.vo.FindProfileNotePageListReqVO;
import com.quanxiaoha.xiaohashu.note.biz.model.vo.FindProfileNoteRspVO;
import com.quanxiaoha.xiaohashu.note.biz.rpc.UserRpcService;
import com.quanxiaoha.xiaohashu.note.biz.service.ProfileService;
import com.quanxiaoha.xiaohashu.user.dto.resp.FindUserByIdRspDTO;
import jakarta.annotation.Resource;
import lombok.extern.slf4j.Slf4j;
import org.apache.commons.lang3.StringUtils;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;
import java.util.stream.Collectors;


/**
 * @author: 犬小哈
 * @date: 2024/4/7 15:41
 * @version: v1.0.0
 * @description: 个人主页业务
 **/
@Service
@Slf4j
public class ProfileServiceImpl implements ProfileService {

    @Resource
    private NoteDOMapper noteDOMapper;
    @Resource
    private NoteCountDOMapper noteCountDOMapper;
    @Resource
    private UserRpcService userRpcService;
    @Resource
    private NoteCollectionDOMapper noteCollectionDOMapper;
    @Resource
    private NoteLikeDOMapper noteLikeDOMapper;

    @Override
    public PageResponse<FindProfileNoteRspVO> findNoteList(FindProfileNotePageListReqVO findProfileNotePageListReqVO) {
        Integer queryType = findProfileNotePageListReqVO.getType();
        Integer pageNo = findProfileNotePageListReqVO.getPageNo();
        Long userId = findProfileNotePageListReqVO.getUserId();

        // 每页展示的数据量
        long pageSize = 10;

        // TODO: 为快速完成前后端联调，目前走数据库查询

        ProfileNoteTypeEnum profileNoteTypeEnum = ProfileNoteTypeEnum.valueOf(queryType);

        List<FindProfileNoteRspVO> noteRspVOS = Lists.newArrayList();
        List<NoteDO> noteDOS = null;
        int count = 0;
        switch (profileNoteTypeEnum) {
            case ALL -> { // 查询所有笔记
                count = noteDOMapper.selectTotalCountByCreatorId(userId);

                // 计算分页查询的偏移量 offset
                long offset = PageResponse.getOffset(pageNo, pageSize);

                PageResponse<FindProfileNoteRspVO> checkResponse = checkCountAndPageNo(count, pageNo, pageSize);
                if (Objects.nonNull(checkResponse)) return checkResponse;

                noteDOS = noteDOMapper.selectPageListByCreatorId(userId, offset, pageSize);
            }
            case COLLECTED -> { // 查询用户收藏的笔记
                count = noteCollectionDOMapper.selectTotalCountByUserId(userId);

                // 计算分页查询的偏移量 offset
                long offset = PageResponse.getOffset(pageNo, pageSize);

                PageResponse<FindProfileNoteRspVO> checkResponse = checkCountAndPageNo(count, pageNo, pageSize);
                if (Objects.nonNull(checkResponse)) return checkResponse;

                List<Long> noteIds = noteCollectionDOMapper.selectPageListByUserId(userId, offset, pageSize);

                if (CollUtil.isNotEmpty(noteIds)) {
                    List<NoteDO> notes = noteDOMapper.selectByNoteIds(noteIds);
                    Map<Long, NoteDO> noteIdAndDOMap = notes.stream().collect(Collectors.toMap(NoteDO::getId, noteDO -> noteDO));
                    noteDOS = noteIds.stream()
                            .map(noteIdAndDOMap::get).collect(Collectors.toList());
                }
            }
            case LIKED -> { // 查询用户点赞的笔记
                count = noteLikeDOMapper.selectTotalCountByUserId(userId);

                // 计算分页查询的偏移量 offset
                long offset = PageResponse.getOffset(pageNo, pageSize);

                PageResponse<FindProfileNoteRspVO> checkResponse = checkCountAndPageNo(count, pageNo, pageSize);
                if (Objects.nonNull(checkResponse)) return checkResponse;

                List<Long> noteIds = noteLikeDOMapper.selectPageListByUserId(userId, offset, pageSize);

                if (CollUtil.isNotEmpty(noteIds)) {
                    List<NoteDO> notes = noteDOMapper.selectByNoteIds(noteIds);
                    Map<Long, NoteDO> noteIdAndDOMap = notes.stream().collect(Collectors.toMap(NoteDO::getId, noteDO -> noteDO));
                    noteDOS = noteIds.stream()
                            .map(noteIdAndDOMap::get).collect(Collectors.toList());
                }
            }
        }

        if (CollUtil.isNotEmpty(noteDOS)) {
            List<Long> creatorIds = noteDOS.stream().map(NoteDO::getCreatorId).toList();

            // RPC: 调用用户服务，批量获取用户信息（头像、昵称等）
            List<FindUserByIdRspDTO> findUserByIdRspDTOS = userRpcService.findByIds(creatorIds);
            Map<Long, FindUserByIdRspDTO> userIdAndDTOMap = findUserByIdRspDTOS.stream()
                    .collect(Collectors.toMap(FindUserByIdRspDTO::getId, dto -> dto));

            // 批量查询笔记计数 TODO: 快速完成前后端联调，后续需要改成走 RPC 查询
            List<Long> noteIds = noteDOS.stream().map(NoteDO::getId).toList();
            List<NoteCountDO> noteCountDOS = noteCountDOMapper.selectByNoteIds(noteIds);
            Map<Long, NoteCountDO> noteIdAndDOMap = Maps.newHashMap();
            if (CollUtil.isNotEmpty(noteCountDOS)) {
                noteIdAndDOMap = noteCountDOS.stream()
                        .collect(Collectors.toMap(NoteCountDO::getNoteId, noteCountDO -> noteCountDO));
            }

            // 分页返参
            for (NoteDO noteDO : noteDOS) {
                Integer type = noteDO.getType();
                FindProfileNoteRspVO findProfileNoteRspVO = FindProfileNoteRspVO.builder()
                        .id(String.valueOf(noteDO.getId()))
                        .title(noteDO.getTitle())
                        .type(type)
                        .build();

                NoteTypeEnum noteTypeEnum = NoteTypeEnum.valueOf(type);

                switch (noteTypeEnum) {
                    case IMAGE_TEXT -> {
                        // 提取第一张图片作为封面图
                        String cover = Optional.ofNullable(noteDO.getImgUris())
                                .map(uris -> StringUtils.split(uris, ",")[0])
                                .orElse(null);
                        findProfileNoteRspVO.setCover(cover);
                    }
                    case VIDEO -> findProfileNoteRspVO.setVideoUri(noteDO.getVideoUri());
                }

                // 设置发布者信息
                Long noteCreatorId = noteDO.getCreatorId();
                FindUserByIdRspDTO findUserByIdRspDTO = userIdAndDTOMap.get(noteCreatorId);
                if (Objects.nonNull(findUserByIdRspDTO)) {
                    findProfileNoteRspVO.setCreatorId(noteCreatorId);
                    findProfileNoteRspVO.setNickname(findUserByIdRspDTO.getNickName());
                    findProfileNoteRspVO.setAvatar(findUserByIdRspDTO.getAvatar());
                }

                // 设置点赞数据
                NoteCountDO noteCountDO = noteIdAndDOMap.get(noteDO.getId());
                findProfileNoteRspVO.setLikeTotal(Objects.nonNull(noteCountDO)
                        ? String.valueOf(noteCountDO.getLikeTotal()) : "0");

                noteRspVOS.add(findProfileNoteRspVO);
            }
        }

        return PageResponse.success(noteRspVOS, pageNo, count, pageSize);
    }

    private static PageResponse<FindProfileNoteRspVO> checkCountAndPageNo(int count, Integer pageNo, long pageSize) {
        // 若评论总数为 0，则直接响应
        if (count == 0) {
            return PageResponse.success(null, pageNo, 0);
        }

        long totalPage = PageResponse.getTotalPage(count, pageSize);

        // 若请求的页码大于总页数，直接响应
        if (pageNo > totalPage) {
            return PageResponse.success(null, pageNo, totalPage);
        }
        return null;
    }

    // private PageResponse<FindProfileNoteRspVO> selectAllNotes(List<FindDiscoverNoteRspVO> noteRspVOS, Integer pageNo, long pageSize) {
    //
    // }
}
