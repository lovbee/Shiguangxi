-- LUA 脚本：日增量笔记发布、删除变更数据布隆过滤器

local key = KEYS[1] -- 操作的 Redis Key
local userId = ARGV[1] -- Redis Value

-- 使用 EXISTS 命令检查布隆过滤器是否存在
local exists = redis.call('EXISTS', key)
if exists == 0 then
    -- 创建布隆过滤器
    redis.call('BF.ADD', key, '')
    -- 设置过期时间，一天后过期
    redis.call("EXPIRE", key, 20*60*60)
end

-- 校验该变更数据是否已经存在(1 表示已存在，0 表示不存在)
return redis.call('BF.EXISTS', key, userId)
