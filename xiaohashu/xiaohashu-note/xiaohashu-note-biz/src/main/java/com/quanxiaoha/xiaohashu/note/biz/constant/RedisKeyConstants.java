package com.quanxiaoha.xiaohashu.note.biz.constant;

/**
 * @author: 犬小哈
 * @date: 2024/5/21 15:04
 * @version: v1.0.0
 * @description: TODO
 **/
public class RedisKeyConstants {

    /**
     * 笔记详情 KEY 前缀
     */
    public static final String NOTE_DETAIL_KEY = "note:detail:";

    /**
     * 布隆过滤器：用户笔记点赞 前缀
     */
    public static final String BLOOM_USER_NOTE_LIKE_LIST_KEY = "bloom:note:likes:";

    /**
     * Roaring Bitmap：用户笔记点赞 前缀
     */
    public static final String R_BITMAP_USER_NOTE_LIKE_LIST_KEY = "rbitmap:note:likes:";

    /**
     * 布隆过滤器：用户笔记收藏 前缀
     */
    public static final String BLOOM_USER_NOTE_COLLECT_LIST_KEY = "bloom:note:collects:";

    /**
     * Roaring Bitmap：用户笔记收藏 前缀
     */
    public static final String R_BITMAP_USER_NOTE_COLLECT_LIST_KEY = "rbitmap:note:collects:";


    /**
     * 用户笔记点赞列表 ZSet 前缀
     */
    public static final String USER_NOTE_LIKE_ZSET_KEY = "user:note:likes:";

    /**
     * 用户笔记收藏列表 ZSet 前缀
     */
    public static final String USER_NOTE_COLLECT_ZSET_KEY = "user:note:collects:";

    /**
     * 笔记计数 KEY 前缀
     */
    public static final String NOTE_COUNT_KEY = "count:note:";

    /**
     * Hash Field: 点赞总数
     */
    public static final String FIELD_LIKE_TOTAL = "likeTotal";

    /**
     * Hash Field: 收藏总数
     */
    public static final String FIELD_COLLECT_TOTAL = "collectTotal";

    /**
     * Hash Field: 评论总数
     */
    public static final String FIELD_COMMENT_TOTAL = "commentTotal";

    /**
     * 构建完整的 Roaring Bitmap：用户笔记点赞 KEY
     * @param userId
     * @return
     */
    public static String buildRBitmapUserNoteLikeListKey(Long userId) {
        return R_BITMAP_USER_NOTE_LIKE_LIST_KEY + userId;
    }

    /**
     * 构建完整的 Roaring Bitmap：用户笔记收藏 KEY
     * @param userId
     * @return
     */
    public static String buildRBitmapUserNoteCollectListKey(Long userId) {
        return R_BITMAP_USER_NOTE_COLLECT_LIST_KEY + userId;
    }

    /**
     * 构建完整的笔记计数 KEY
     * @param noteId
     * @return
     */
    public static String buildNoteCountKey(Long noteId) {
        return NOTE_COUNT_KEY + noteId;
    }


    /**
     * 构建完整的笔记详情 KEY
     * @param noteId
     * @return
     */
    public static String buildNoteDetailKey(Long noteId) {
        return NOTE_DETAIL_KEY + noteId;
    }


    /**
     * 构建完整的布隆过滤器：用户笔记点赞 KEY
     * @param userId
     * @return
     */
    public static String buildBloomUserNoteLikeListKey(Long userId) {
        return BLOOM_USER_NOTE_LIKE_LIST_KEY + userId;
    }

    /**
     * 构建完整的布隆过滤器：用户笔记收藏 KEY
     * @param userId
     * @return
     */
    public static String buildBloomUserNoteCollectListKey(Long userId) {
        return BLOOM_USER_NOTE_COLLECT_LIST_KEY + userId;
    }

    /**
     * 构建完整的用户笔记点赞列表 ZSet KEY
     * @param userId
     * @return
     */
    public static String buildUserNoteLikeZSetKey(Long userId) {
        return USER_NOTE_LIKE_ZSET_KEY + userId;
    }

    /**
     * 构建完整的用户笔记收藏列表 ZSet KEY
     * @param userId
     * @return
     */
    public static String buildUserNoteCollectZSetKey(Long userId) {
        return USER_NOTE_COLLECT_ZSET_KEY + userId;
    }

}
