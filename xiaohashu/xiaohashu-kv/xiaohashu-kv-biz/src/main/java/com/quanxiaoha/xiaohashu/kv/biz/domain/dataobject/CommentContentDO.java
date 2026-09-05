package com.quanxiaoha.xiaohashu.kv.biz.domain.dataobject;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.cassandra.core.mapping.PrimaryKey;
import org.springframework.data.cassandra.core.mapping.Table;

/**
 * @author: 犬小哈
 * @date: 2024/7/14 16:19
 * @version: v1.0.0
 * @description: 评论内容
 **/
@Table("comment_content")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class CommentContentDO {

    @PrimaryKey
    private CommentContentPrimaryKey primaryKey;

    private String content;
}
