local key = KEYS[1] -- 操作的 Redis Key
local followUserId = ARGV[1] -- 关注的用户ID
local timestamp = ARGV[2] -- 时间戳
local expireSeconds = ARGV[3] -- 过期时间（秒）

-- ZADD 添加关注关系
redis.call('ZADD', key, timestamp, followUserId)
-- 设置过期时间
redis.call('EXPIRE', key, expireSeconds)
return 0