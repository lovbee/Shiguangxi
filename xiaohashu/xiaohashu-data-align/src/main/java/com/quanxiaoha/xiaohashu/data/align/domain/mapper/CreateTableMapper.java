package com.quanxiaoha.xiaohashu.data.align.domain.mapper;

/**
 * 自动创建表
 */
public interface CreateTableMapper {

    /**
     * 创建日增量表：关注数计数变更
     * @param tableNameSuffix
     */
    void createDataAlignFollowingCountTempTable(String tableNameSuffix);

    /**
     * 创建日增量表：粉丝数计数变更
     * @param tableNameSuffix
     */
    void createDataAlignFansCountTempTable(String tableNameSuffix);

    /**
     * 创建日增量表：笔记收藏数计数变更
     * @param tableNameSuffix
     */
    void createDataAlignNoteCollectCountTempTable(String tableNameSuffix);

    /**
     * 创建日增量表：用户被收藏数计数变更
     * @param tableNameSuffix
     */
    void createDataAlignUserCollectCountTempTable(String tableNameSuffix);

    /**
     * 创建日增量表：用户被点赞数计数变更
     * @param tableNameSuffix
     */
    void createDataAlignUserLikeCountTempTable(String tableNameSuffix);

    /**
     * 创建日增量表：笔记点赞数计数变更
     * @param tableNameSuffix
     */
    void createDataAlignNoteLikeCountTempTable(String tableNameSuffix);

    /**
     * 创建日增量表：笔记发布数计数变更
     * @param tableNameSuffix
     */
    void createDataAlignNotePublishCountTempTable(String tableNameSuffix);
}