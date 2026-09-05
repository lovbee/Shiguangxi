package com.quanxiaoha.xiaohashu.count.biz.domain.mapper;

import com.quanxiaoha.xiaohashu.count.biz.domain.dataobject.NoteCountDO;
import org.apache.ibatis.annotations.Param;

public interface NoteCountDOMapper {
    int deleteByPrimaryKey(Long id);

    int insert(NoteCountDO record);

    int insertSelective(NoteCountDO record);

    /**
     * 添加记录或更新笔记点赞数
     * @param count
     * @param noteId
     * @return
     */
    int insertOrUpdateLikeTotalByNoteId(@Param("count") Integer count, @Param("noteId") Long noteId);

    /**
     * 添加记录或更新笔记收藏数
     * @param count
     * @param noteId
     * @return
     */
    int insertOrUpdateCollectTotalByNoteId(@Param("count") Integer count, @Param("noteId") Long noteId);

    /**
     * 添加记录或更新笔记评论数
     * @param count
     * @param noteId
     * @return
     */
    int insertOrUpdateCommentTotalByNoteId(@Param("count") int count, @Param("noteId") Long noteId);

    NoteCountDO selectByPrimaryKey(Long id);

    NoteCountDO selectByNoteId(Long noteId);

    int updateByPrimaryKeySelective(NoteCountDO record);

    int updateByPrimaryKey(NoteCountDO record);

}