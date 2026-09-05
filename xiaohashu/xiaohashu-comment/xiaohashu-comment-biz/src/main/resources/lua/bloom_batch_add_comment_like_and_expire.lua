-- 操作的 Key
local key = KEYS[1]

for i = 1, #ARGV - 1 do
    redis.call("BF.ADD", key, ARGV[i])
end

---- 最后一个参数为过期时间
local expireTime = ARGV[#ARGV]
-- 设置过期时间
redis.call("EXPIRE", key, expireTime)
return 0