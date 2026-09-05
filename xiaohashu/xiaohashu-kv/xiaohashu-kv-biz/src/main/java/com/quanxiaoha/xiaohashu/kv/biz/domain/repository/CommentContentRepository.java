package com.quanxiaoha.xiaohashu.kv.biz.domain.repository;

import com.quanxiaoha.xiaohashu.kv.biz.domain.dataobject.CommentContentDO;
import com.quanxiaoha.xiaohashu.kv.biz.domain.dataobject.CommentContentPrimaryKey;
import org.springframework.data.cassandra.repository.CassandraRepository;

import java.util.List;
import java.util.UUID;

/**
 * @author: 犬小哈
 * @date: 2024/7/14 16:21
 * @version: v1.0.0
 * @description: TODO
 **/
public interface CommentContentRepository extends CassandraRepository<CommentContentDO, CommentContentPrimaryKey> {

    /**
     * 查询评论内容
     * @param noteId
     * @param yearMonths
     * @param contentIds
     * @return
     */
    List<CommentContentDO> findByPrimaryKeyNoteIdAndPrimaryKeyYearMonthInAndPrimaryKeyContentIdIn(
            Long noteId, List<String> yearMonths, List<UUID> contentIds
    );

    /**
     * 删除评论正文
     * @param noteId
     * @param yearMonth
     * @param contentId
     */
    void deleteByPrimaryKeyNoteIdAndPrimaryKeyYearMonthAndPrimaryKeyContentId(Long noteId, String yearMonth, UUID contentId);

}
