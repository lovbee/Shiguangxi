-- 操作的 Key
local zsetKey = KEYS[1]
-- 获取传入的成员和分数列表
local membersScores = ARGV
-- ZSet 最多缓存 500 条评论
local sizeLimit = 500

-- 检查 ZSet 是否存在
if redis.call('EXISTS', zsetKey) == 0 then
    return -1 -- 若不存在，直接 return
end

-- 获取当前 ZSet 的大小
local currentSize = redis.call('ZCARD', zsetKey)

-- 遍历传入的成员和分数，添加到 ZSet 中
for i = 1, #membersScores, 2 do
    -- 评论 ID
    local member = membersScores[i]
    -- 热度值
    local score = membersScores[i + 1]

    -- 检查当前 ZSet 的大小是否小于 500 条
    if currentSize < sizeLimit then
        -- 若是，则添加缓存
        redis.call('ZADD', zsetKey, score, member)
        currentSize = currentSize + 1  -- 更新 ZSet 大小
    else
        break  -- 否则，则达到最大限制，停止添加
    end
end

return 0
