local key = KEYS[1] -- Redis Key
local fansUserId = ARGV[1] -- 粉丝ID
local timestamp = ARGV[2] -- 时间戳

-- 使用 EXISTS 命令检查 ZSET 粉丝列表是否存在
local exists = redis.call('EXISTS', key)
if exists == 0 then
    return -1
end

-- 获取粉丝列表大小
local size = redis.call('ZCARD', key)

-- 若超过 5000 个粉丝，则移除最早关注的粉丝
if size >= 1 then
    redis.call('ZPOPMIN', key)
end

-- 添加新的粉丝关系
redis.call('ZADD', key, timestamp, fansUserId)
return 0