package com.quanxiaoha.xiaohashu.data.align.domain.mapper;

/**
 * 删除表
 */
public interface DeleteTableMapper {

    /**
     * 删除日增量表：关注数计数变更
     * @param tableNameSuffix
     */
    void deleteDataAlignFollowingCountTempTable(String tableNameSuffix);

    /**
     * 删除日增量表：粉丝数计数变更
     * @param tableNameSuffix
     */
    void deleteDataAlignFansCountTempTable(String tableNameSuffix);

    /**
     * 删除日增量表：笔记收藏数计数变更
     * @param tableNameSuffix
     */
    void deleteDataAlignNoteCollectCountTempTable(String tableNameSuffix);

    /**
     * 删除日增量表：用户被收藏数计数变更
     * @param tableNameSuffix
     */
    void deleteDataAlignUserCollectCountTempTable(String tableNameSuffix);

    /**
     * 删除日增量表：用户被点赞数计数变更
     * @param tableNameSuffix
     */
    void deleteDataAlignUserLikeCountTempTable(String tableNameSuffix);

    /**
     * 删除日增量表：笔记点赞数计数变更
     * @param tableNameSuffix
     */
    void deleteDataAlignNoteLikeCountTempTable(String tableNameSuffix);

    /**
     * 删除日增量表：笔记发布数计数变更
     * @param tableNameSuffix
     */
    void deleteDataAlignNotePublishCountTempTable(String tableNameSuffix);
}