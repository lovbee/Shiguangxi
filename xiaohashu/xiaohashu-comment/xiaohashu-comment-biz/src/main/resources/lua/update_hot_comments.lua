-- 入参说明：
-- KEYS[1]: ZSet 的键
-- ARGV: 每个评论的数据，格式为 member1, score1, member2, score2 ...

local zsetKey = KEYS[1]
local maxSize = 500 -- 最多缓存 500 条热点评论
local batchSize = #ARGV / 2 -- 有多少条评论

-- 确认 ZSet 是否存在
if redis.call("EXISTS", zsetKey) == 0 then
    return -1 -- 如果 ZSet 不存在，直接返回
end

for i = 1, batchSize do
    local member = ARGV[(i - 1) * 2 + 1] -- 获取当前评论 ID
    local score = ARGV[(i - 1) * 2 + 2]  -- 获取当前评论的热度

    -- 获取 ZSet 的大小
    local currentSize = redis.call("ZCARD", zsetKey)

    if currentSize < maxSize then
        -- 如果 ZSet 的大小小于 maxSize，直接添加
        redis.call("ZADD", zsetKey, score, member)
    else -- 若已缓存 500 条热点评论
        -- 获取当前 ZSet 中热度值最小的评论
        local minEntry = redis.call("ZRANGE", zsetKey, 0, 0, "WITHSCORES")
        -- 热度最小评论的值
        local minScore = minEntry[2]

        if score > minScore then
            -- 如果当前评论的热度大于最小热度，替换掉最小的；否则无视
            redis.call("ZREM", zsetKey, minEntry[1])
            redis.call("ZADD", zsetKey, score, member)
        end
    end
end

return 0
