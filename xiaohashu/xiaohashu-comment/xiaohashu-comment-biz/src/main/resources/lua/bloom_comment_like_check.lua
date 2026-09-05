-- LUA 脚本：评论点赞布隆过滤器

local key = KEYS[1] -- 操作的 Redis Key
local commentId = ARGV[1] -- 笔记ID

-- 使用 EXISTS 命令检查布隆过滤器是否存在
local exists = redis.call('EXISTS', key)
if exists == 0 then
    return -1
end

-- 校验该评论是否被点赞过(1 表示已经点赞，0 表示未点赞)
local isLiked = redis.call('BF.EXISTS', key, commentId)
if isLiked == 1 then
    return 1
end

-- 未被点赞，添加点赞数据
redis.call('BF.ADD', key, commentId)
return 0





