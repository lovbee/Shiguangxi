package com.quanxiaoha.xiaohashu.comment.biz.domain.mapper;

import com.quanxiaoha.xiaohashu.comment.biz.domain.dataobject.CommentDO;
import com.quanxiaoha.xiaohashu.comment.biz.model.bo.CommentBO;
import com.quanxiaoha.xiaohashu.comment.biz.model.bo.CommentHeatBO;
import org.apache.ibatis.annotations.Param;

import java.util.List;

public interface CommentDOMapper {
    int deleteByPrimaryKey(Long id);

    /**
     * 删除一级评论下，所有二级评论
     * @param commentId
     * @return
     */
    int deleteByParentId(Long commentId);

    /**
     * 批量删除评论
     * @param commentIds
     * @return
     */
    int deleteByIds(@Param("commentIds") List<Long> commentIds);

    int insert(CommentDO record);

    /**
     * 批量插入评论
     * @param comments
     * @return
     */
    int batchInsert(@Param("comments") List<CommentBO> comments);

    int insertSelective(CommentDO record);

    CommentDO selectByPrimaryKey(Long id);

    /**
     * 根据 reply_comment_id 查询
     * @param commentId
     * @return
     */
    CommentDO selectByReplyCommentId(Long commentId);

    /**
     * 根据评论 ID 批量查询
     * @param commentIds
     * @return
     */
    List<CommentDO> selectByCommentIds(@Param("commentIds") List<Long> commentIds);

    /**
     * 批量查询计数数据
     * @param commentIds
     * @return
     */
    List<CommentDO> selectCommentCountByIds(@Param("commentIds") List<Long> commentIds);

    /**
     * 查询子评论
     * @param parentId
     * @param limit
     * @return
     */
    List<CommentDO> selectChildCommentsByParentIdAndLimit(@Param("parentId") Long parentId,
                                                          @Param("limit") int limit);

    /**
     * 批量查询二级评论
     * @param commentIds
     * @return
     */
    List<CommentDO> selectTwoLevelCommentByIds(@Param("commentIds") List<Long> commentIds);

    /**
     * 查询一级评论下最早回复的评论
     * @param parentId
     * @return
     */
    CommentDO selectEarliestByParentId(Long parentId);

    /**
     * 查询评论分页数据
     * @param noteId
     * @param offset
     * @param pageSize
     * @return
     */
    List<CommentDO> selectPageList(@Param("noteId") Long noteId,
                                   @Param("offset") long offset,
                                   @Param("pageSize") long pageSize);

    /**
     * 查询二级评论分页数据
     * @param parentId
     * @param offset
     * @param pageSize
     * @return
     */
    List<CommentDO> selectChildPageList(@Param("parentId") Long parentId,
                                        @Param("offset") long offset,
                                        @Param("pageSize") long pageSize);

    /**
     * 查询热门评论
     * @param noteId
     * @return
     */
    List<CommentDO> selectHeatComments(Long noteId);

    /**
     * 查询一级评论下子评论总数
     * @param commentId
     * @return
     */
    Long selectChildCommentTotalById(Long commentId);

    int updateByPrimaryKeySelective(CommentDO record);

    int updateByPrimaryKey(CommentDO record);

    /**
     * 批量更新热度值
     * @param commentIds
     * @param commentHeatBOS
     * @return
     */
    int batchUpdateHeatByCommentIds(@Param("commentIds") List<Long> commentIds,
                                    @Param("commentHeatBOS") List<CommentHeatBO> commentHeatBOS);

    /**
     * 更新一级评论的 first_reply_comment_id
     * @param firstReplyCommentId
     * @param id
     * @return
     */
    int updateFirstReplyCommentIdByPrimaryKey(@Param("firstReplyCommentId") Long firstReplyCommentId,
                                              @Param("id") Long id);

}