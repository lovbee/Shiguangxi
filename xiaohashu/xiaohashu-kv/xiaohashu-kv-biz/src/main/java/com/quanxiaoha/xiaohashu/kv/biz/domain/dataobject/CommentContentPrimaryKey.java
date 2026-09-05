package com.quanxiaoha.xiaohashu.kv.biz.domain.dataobject;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.cassandra.core.cql.PrimaryKeyType;
import org.springframework.data.cassandra.core.mapping.PrimaryKeyClass;
import org.springframework.data.cassandra.core.mapping.PrimaryKeyColumn;

import java.util.UUID;

/**
 * @author: 犬小哈
 * @date: 2024/7/14 16:19
 * @version: v1.0.0
 * @description: 评论内容主键
 **/
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@PrimaryKeyClass
public class CommentContentPrimaryKey {

    @PrimaryKeyColumn(name = "note_id", type = PrimaryKeyType.PARTITIONED)
    private Long noteId; // 分区键1

    @PrimaryKeyColumn(name = "year_month", type = PrimaryKeyType.PARTITIONED)
    private String yearMonth; // 分区键2

    @PrimaryKeyColumn(name = "content_id", type = PrimaryKeyType.CLUSTERED)
    private UUID contentId; // 聚簇键

}
