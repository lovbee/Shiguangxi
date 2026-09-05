local key = KEYS[1] -- Redis Key
local noteId = ARGV[1] -- 笔记ID
local timestamp = ARGV[2] -- 时间戳

-- 使用 EXISTS 命令检查 ZSET 笔记点赞列表是否存在
local exists = redis.call('EXISTS', key)
if exists == 0 then
    return -1
end

-- 获取笔记点赞列表大小
local size = redis.call('ZCARD', key)

-- 若已经点赞了 100 篇笔记，则移除最早点赞的那篇
if size >= 100 then
    redis.call('ZPOPMIN', key)
end

-- 添加新的笔记点赞关系
redis.call('ZADD', key, timestamp, noteId)
return 0