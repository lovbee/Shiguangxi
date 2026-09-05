local key = KEYS[1] -- 操作的 Redis Key
local commentId = ARGV[1] -- 评论ID

-- 使用 EXISTS 命令检查布隆过滤器是否存在
local exists = redis.call('EXISTS', key)
if exists == 0 then
    return -1
end

-- 校验该评论是否被点赞过(1 表示已经点赞，0 表示未点赞)
return redis.call('BF.EXISTS', key, commentId)
