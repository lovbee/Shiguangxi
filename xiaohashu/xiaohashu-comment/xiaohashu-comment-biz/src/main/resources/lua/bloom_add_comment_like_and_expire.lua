-- 操作的 Key
local key = KEYS[1]
local commentId = ARGV[1] -- 评论ID
local expireSeconds = ARGV[2] -- 过期时间（秒）

redis.call("BF.ADD", key, commentId)

-- 设置过期时间
redis.call("EXPIRE", key, expireSeconds)
return 0