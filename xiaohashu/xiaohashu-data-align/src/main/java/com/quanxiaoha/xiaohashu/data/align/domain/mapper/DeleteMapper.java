package com.quanxiaoha.xiaohashu.data.align.domain.mapper;

import org.apache.ibatis.annotations.Param;

import java.util.List;

/**
 * 删除
 */
public interface DeleteMapper {

    /**
     * 日增量表：关注数计数变更 - 批量删除
     * @param userIds
     */
    void batchDeleteDataAlignFollowingCountTempTable(@Param("tableNameSuffix") String tableNameSuffix,
                                                     @Param("userIds") List<Long> userIds);

    /**
     * 日增量表：粉丝数计数变更 - 批量删除
     * @param userIds
     */
    void batchDeleteDataAlignFansCountTempTable(@Param("tableNameSuffix") String tableNameSuffix,
                                                     @Param("userIds") List<Long> userIds);

    /**
     * 日增量表：用户获得的点赞数变更 - 批量删除
     * @param userIds
     */
    void batchDeleteDataAlignUserLikeCountTempTable(@Param("tableNameSuffix") String tableNameSuffix,
                                                @Param("userIds") List<Long> userIds);

    /**
     * 日增量表：用户获得的收藏数变更 - 批量删除
     * @param userIds
     */
    void batchDeleteDataAlignUserCollectCountTempTable(@Param("tableNameSuffix") String tableNameSuffix,
                                                    @Param("userIds") List<Long> userIds);

    /**
     * 日增量表：笔记点赞计数变更 - 批量删除
     */
    void batchDeleteDataAlignNoteLikeCountTempTable(@Param("tableNameSuffix") String tableNameSuffix,
                                                     @Param("noteIds") List<Long> noteIds);

    /**
     * 日增量表：用户发布笔记数变更 - 批量删除
     */
    void batchDeleteDataAlignNotePublishCountTempTable(@Param("tableNameSuffix") String tableNameSuffix,
                                                       @Param("userIds") List<Long> userIds);

    /**
     * 日增量表：笔记收藏计数变更 - 批量删除
     */
    void batchDeleteDataAlignNoteCollectCountTempTable(@Param("tableNameSuffix") String tableNameSuffix,
                                                    @Param("noteIds") List<Long> noteIds);
}