local key = KEYS[1] -- 操作的 Redis Key
local noteId = ARGV[1] -- 笔记ID

-- 使用 EXISTS 命令检查 Roaring Bitmap 是否存在
local exists = redis.call('EXISTS', key)
if exists == 0 then
    return -1
end

-- 校验该篇笔记是否被收藏过(1 表示已经收藏，0 表示未收藏)
local isCollected = redis.call('R.GETBIT', key, noteId)
if isCollected == 0 then
    return 0
end

-- 取消收藏笔记
return redis.call('R.SETBIT', key, noteId, 0)
