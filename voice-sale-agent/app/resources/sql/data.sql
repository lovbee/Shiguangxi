-- ============================================================================
-- jc-voice-shopping 测试数据
-- 使用：psql -d jc_voice_shopping -f data.sql
--
-- 设计思路：
--   - 3 家商家（头部 / 腰部 / 新入驻）→ 验证隔离
--   - 5 个用户（不同画像）→ 验证个性化与冷启动
--   - 30 件商品，覆盖跑鞋 / 手表 / 耳机 / 口红 4 个二级类目
--   - 12 条 FAQ（物流 / 售后 / 支付 / 发票）→ 可直接命中
--   - 2 个历史会话（含消息、状态、订单）
-- ============================================================================

-- ------- 清库（仅用于开发环境反复导入，生产千万别留）-------
TRUNCATE TABLE
    order_record,
    session_state,
    session_message,
    session,
    user_profile_dynamic,
    user_profile_static,
    faq_entry,
    product,
    app_user,
    merchant
RESTART IDENTITY CASCADE;


-- ============================================================================
-- 一、商家
-- ============================================================================
INSERT INTO merchant (id, name, status, scale_level, contact_email) VALUES
                                                                        (1, '飞跃运动旗舰店',   'ACTIVE', 'HEAD', 'flyover@demo.com'),
                                                                        (2, '恒时腕表精品店',   'ACTIVE', 'MID',  'hengshi@demo.com'),
                                                                        (3, '新声音频严选',     'ACTIVE', 'NEW',  'newsound@demo.com');

SELECT setval('merchant_id_seq', 3);


-- ============================================================================
-- 二、用户
-- ============================================================================
INSERT INTO app_user (id, username, nickname, status) VALUES
                                                          (1, 'alice',   '爱丽丝',     'ACTIVE'),    -- 女/25/上海，爱跑步
                                                          (2, 'bob',     '鲍勃',       'ACTIVE'),    -- 男/32/北京，手表爱好者
                                                          (3, 'carol',   '卡罗尔',     'ACTIVE'),    -- 女/28/深圳，数码 + 美妆
                                                          (4, 'david',   '大卫',       'ACTIVE'),    -- 男/45/广州，冷启动新用户
                                                          (5, 'eric',    '埃里克',     'ACTIVE');    -- 男/22/成都，数码爱好者

SELECT setval('app_user_id_seq', 5);

-- 静态画像
INSERT INTO user_profile_static
(user_id, gender, age, city, height_cm, weight_kg, skin_type, tech_savvy, budget_band, locale) VALUES
                                                                                                   (1, 'female', 25, '上海', 168, 55, 'normal',    'mid',    'mid',     'zh_cn'),
                                                                                                   (2, 'male',   32, '北京', 178, 75, NULL,        'expert', 'premium', 'zh_cn'),
                                                                                                   (3, 'female', 28, '深圳', 165, 50, 'dry',       'expert', 'premium', 'zh_cn'),
                                                                                                   (4, 'male',   45, '广州', 172, 70, NULL,        'novice', 'budget',  'zh_cn'),
                                                                                                   (5, 'male',   22, '成都', 180, 68, NULL,        'mid',    'mid',     'zh_cn');

-- 动态画像
INSERT INTO user_profile_dynamic
(user_id, category_affinity, brand_affinity, recent_viewed, recent_purchased,
 price_sensitivity, avg_order_amount) VALUES
                                          (1, '{"跑鞋":0.88,"T恤":0.42}'::jsonb,          '{"Nike":0.75,"Adidas":0.5}'::jsonb,
                                           ARRAY[1,2,3]::bigint[], ARRAY[1]::bigint[], 0.60, 520.00),
                                          (2, '{"手表":0.92,"皮具":0.35}'::jsonb,         '{"Seiko":0.8,"Casio":0.55}'::jsonb,
                                           ARRAY[11,12,13]::bigint[], ARRAY[11]::bigint[], 0.25, 2800.00),
                                          (3, '{"口红":0.78,"耳机":0.65}'::jsonb,         '{"YSL":0.70,"Sony":0.60}'::jsonb,
                                           ARRAY[21,22,26]::bigint[], ARRAY[21,26]::bigint[], 0.30, 980.00),
                                          (4, '{}'::jsonb,                                  '{}'::jsonb,
                                           ARRAY[]::bigint[],      ARRAY[]::bigint[], 0.85, 150.00),     -- 冷启动
                                          (5, '{"耳机":0.70}'::jsonb,                       '{"Sony":0.55}'::jsonb,
                                           ARRAY[21,22]::bigint[], ARRAY[]::bigint[], 0.50, 400.00);


-- ============================================================================
-- 三、商品（30 件，4 个二级类目）
-- ============================================================================

-- 跑鞋（商家 1，头部）
INSERT INTO product (id, merchant_id, sku_code, name, category_l1, category_l2, brand,
                     price, original_price, stock, attributes, description, selling_points,
                     status, is_new_arrival) VALUES
                                                 (1,  1, 'RUN-001', 'Nike Pegasus 40 缓震跑鞋', '运动', '跑鞋', 'Nike',  899.00, 1099.00, 50,
                                                  '{"cushion":"high","weight":"medium","gender":"unisex","size_range":[36,46],"terrain":"road"}'::jsonb,
                                                  '经典路跑系列，Air Zoom 中底提供出色缓震，适合日常慢跑到长距离训练。',
                                                  '缓震强／回弹适中／透气鞋面／日常百搭', 'ON_SALE', FALSE),

                                                 (2,  1, 'RUN-002', 'Adidas Ultraboost 22 缓震跑鞋', '运动', '跑鞋', 'Adidas', 1299.00, 1499.00, 30,
                                                  '{"cushion":"high","weight":"medium","gender":"unisex","size_range":[38,46],"terrain":"road"}'::jsonb,
                                                  'Boost 中底带来柔软回弹，Primeknit+ 鞋面贴合自然。',
                                                  '极致缓震／回弹澎湃／长距离首选', 'ON_SALE', FALSE),

                                                 (3,  1, 'RUN-003', 'Saucony Endorphin Speed 3 竞速跑鞋', '运动', '跑鞋', 'Saucony', 1399.00, 1599.00, 20,
                                                  '{"cushion":"medium","weight":"light","gender":"unisex","size_range":[39,45],"terrain":"road"}'::jsonb,
                                                  '尼龙碳板 + PWRRUN PB 泡棉，兼顾日常训练与比赛节奏。',
                                                  '轻量／碳板推进感／速度型', 'ON_SALE', TRUE),

                                                 (4,  1, 'RUN-004', 'Asics Gel-Kayano 30 稳定跑鞋', '运动', '跑鞋', 'Asics', 1599.00, 1699.00, 25,
                                                  '{"cushion":"high","weight":"heavy","gender":"unisex","size_range":[38,46],"terrain":"road"}'::jsonb,
                                                  '4D 稳定系统 + FF Blast Plus Eco 中底，适合扁平足和大体重跑者。',
                                                  '顶级稳定／缓震持久／支撑到位', 'ON_SALE', FALSE),

                                                 (5,  1, 'RUN-005', 'HOKA Clifton 9 轻量缓震跑鞋', '运动', '跑鞋', 'HOKA', 1180.00, 1380.00, 40,
                                                  '{"cushion":"high","weight":"light","gender":"unisex","size_range":[38,46],"terrain":"road"}'::jsonb,
                                                  '超厚中底 + 轻量化设计，走路也舒服。',
                                                  '厚底舒适／通勤跑步两相宜', 'ON_SALE', FALSE),

                                                 (6,  1, 'RUN-006', '入门款 Pegasus 39', '运动', '跑鞋', 'Nike', 599.00, 799.00, 60,
                                                  '{"cushion":"medium","weight":"medium","gender":"unisex","size_range":[36,45],"terrain":"road"}'::jsonb,
                                                  '上一代经典，清仓价格。','价格实惠／经典款', 'ON_SALE', FALSE),

                                                 (7,  1, 'RUN-007', '女款粉色轻量跑鞋', '运动', '跑鞋', 'New Balance', 699.00, 899.00, 15,
                                                  '{"cushion":"medium","weight":"light","gender":"female","color":"pink","size_range":[35,40]}'::jsonb,
                                                  'FuelCell 中底，女性专属鞋楦。','颜值高／女性鞋楦／轻量', 'ON_SALE', FALSE),

                                                 (8,  1, 'RUN-008', '越野跑鞋 Speedgoat 5', '运动', '跑鞋', 'HOKA', 1580.00, 1780.00, 10,
                                                  '{"cushion":"high","weight":"medium","gender":"unisex","size_range":[39,46],"terrain":"trail"}'::jsonb,
                                                  '强抓地 Vibram 大底，专业越野。','越野专用／抓地强', 'ON_SALE', FALSE),

                                                 (9,  1, 'RUN-009', '超轻竞速 Vaporfly 3', '运动', '跑鞋', 'Nike', 1999.00, 2299.00, 8,
                                                  '{"cushion":"medium","weight":"ultralight","gender":"unisex","size_range":[39,45],"terrain":"road"}'::jsonb,
                                                  '全碳板，PEBA 中底，PB 利器。','破 PB 神器／极致轻量', 'ON_SALE', TRUE),

                                                 (10, 1, 'RUN-010', '日常训练鞋 Cumulus 25', '运动', '跑鞋', 'Asics', 899.00, 1099.00, 35,
                                                  '{"cushion":"medium","weight":"medium","gender":"unisex","size_range":[38,46],"terrain":"road"}'::jsonb,
                                                  '中性支撑，日常训练首选。','日常百搭／中性支撑', 'ON_SALE', FALSE);

-- 手表（商家 2，腰部）
INSERT INTO product (id, merchant_id, sku_code, name, category_l1, category_l2, brand,
                     price, original_price, stock, attributes, description, selling_points,
                     status, is_new_arrival) VALUES
                                                 (11, 2, 'WAT-001', 'Seiko 5 Sports 机械腕表',   '配饰', '手表', 'Seiko',  2280.00, 2580.00, 40,
                                                  '{"movement":"automatic","material":"steel","gender":"male","water_resist":"100m"}'::jsonb,
                                                  '4R36 机芯，24 钻，41mm 表径。','入门机械／性价比高／100 米防水', 'ON_SALE', FALSE),

                                                 (12, 2, 'WAT-002', 'Casio G-Shock GA-2100',     '配饰', '手表', 'Casio',  899.00, 1099.00, 50,
                                                  '{"movement":"quartz","material":"resin","gender":"unisex","water_resist":"200m"}'::jsonb,
                                                  '经典农家橡树造型，200 米防水。','抗震／防水／街头潮流', 'ON_SALE', FALSE),

                                                 (13, 2, 'WAT-003', 'Citizen 光动能 AT8020',     '配饰', '手表', 'Citizen', 3680.00, 4280.00, 20,
                                                  '{"movement":"eco-drive","material":"titanium","gender":"male","water_resist":"200m"}'::jsonb,
                                                  '光动能无需换电，钛金属表壳。','光能驱动／钛金属／电波校时', 'ON_SALE', FALSE),

                                                 (14, 2, 'WAT-004', 'Tissot 力洛克 T006',        '配饰', '手表', 'Tissot', 3880.00, 4280.00, 15,
                                                  '{"movement":"automatic","material":"steel","gender":"male","water_resist":"50m"}'::jsonb,
                                                  'Powermatic 80 机芯，80 小时动储。','瑞表性价比／80 小时动储', 'ON_SALE', FALSE),

                                                 (15, 2, 'WAT-005', '入门石英女表',               '配饰', '手表', 'Casio',  399.00, 599.00, 80,
                                                  '{"movement":"quartz","material":"steel","gender":"female","water_resist":"30m"}'::jsonb,
                                                  '简约优雅，日常百搭。','通勤佳选／价格亲民', 'ON_SALE', FALSE),

                                                 (16, 2, 'WAT-006', '智能手表 GW-B5600',           '配饰', '手表', 'Casio',  1680.00, 1880.00, 25,
                                                  '{"movement":"digital","material":"resin","gender":"unisex","water_resist":"200m"}'::jsonb,
                                                  '蓝牙校时 + 多功能电子表。','蓝牙联机／多功能', 'ON_SALE', TRUE),

                                                 (17, 2, 'WAT-007', '机械女表 Presage',           '配饰', '手表', 'Seiko',  4580.00, 4980.00, 10,
                                                  '{"movement":"automatic","material":"steel","gender":"female","water_resist":"50m"}'::jsonb,
                                                  '琺瑯面盘，优雅复古。','琺瑯工艺／女性优雅', 'ON_SALE', FALSE),

                                                 (18, 2, 'WAT-008', '大表径运动表 Prospex',       '配饰', '手表', 'Seiko',  5280.00, 5680.00, 12,
                                                  '{"movement":"automatic","material":"steel","gender":"male","water_resist":"200m","diameter":44}'::jsonb,
                                                  '潜水表传承，44mm 大表径。','潜水规格／44mm 表径', 'ON_SALE', FALSE),

                                                 (19, 2, 'WAT-009', '经典三针 TW1001',            '配饰', '手表', 'Tissot', 2480.00, 2980.00, 18,
                                                  '{"movement":"quartz","material":"steel","gender":"male","water_resist":"30m"}'::jsonb,
                                                  '简约三针，商务通勤。','商务款／经典三针', 'ON_SALE', FALSE),

                                                 (20, 2, 'WAT-010', '限量款 GMT',                 '配饰', '手表', 'Seiko',  7880.00, 8880.00, 5,
                                                  '{"movement":"automatic","material":"steel","gender":"male","water_resist":"100m"}'::jsonb,
                                                  '限量 500 块，GMT 双时区。','限量／GMT／收藏级', 'ON_SALE', TRUE);

-- 耳机（商家 3，新入驻）
INSERT INTO product (id, merchant_id, sku_code, name, category_l1, category_l2, brand,
                     price, original_price, stock, attributes, description, selling_points,
                     status, is_new_arrival) VALUES
                                                 (21, 3, 'HDP-001', 'Sony WH-1000XM5 降噪耳机',   '数码', '耳机', 'Sony',   2399.00, 2899.00, 30,
                                                  '{"type":"over-ear","noise_cancel":"high","battery_hours":30,"connectivity":"bluetooth"}'::jsonb,
                                                  '业界标杆降噪，30 小时续航。','顶级降噪／长续航／通话清晰', 'ON_SALE', TRUE),

                                                 (22, 3, 'HDP-002', 'Apple AirPods Pro 2',        '数码', '耳机', 'Apple',  1899.00, 1999.00, 40,
                                                  '{"type":"in-ear","noise_cancel":"high","battery_hours":6,"connectivity":"bluetooth"}'::jsonb,
                                                  'H2 芯片，自适应降噪。','iOS 生态／自适应降噪', 'ON_SALE', TRUE),

                                                 (23, 3, 'HDP-003', 'Bose QC45',                  '数码', '耳机', 'Bose',   2199.00, 2499.00, 20,
                                                  '{"type":"over-ear","noise_cancel":"high","battery_hours":24,"connectivity":"bluetooth"}'::jsonb,
                                                  'Bose 经典降噪，佩戴舒适。','轻量佩戴／舒适长时间', 'ON_SALE', FALSE),

                                                 (24, 3, 'HDP-004', '森海塞尔 Momentum 4',         '数码', '耳机', 'Sennheiser', 2599.00, 2999.00, 15,
                                                  '{"type":"over-ear","noise_cancel":"medium","battery_hours":60,"connectivity":"bluetooth"}'::jsonb,
                                                  '60 小时续航，Hi-Fi 音质。','超长续航／音质发烧', 'ON_SALE', FALSE),

                                                 (25, 3, 'HDP-005', '入门蓝牙耳机',                '数码', '耳机', 'Edifier', 299.00, 499.00, 100,
                                                  '{"type":"in-ear","noise_cancel":"low","battery_hours":8,"connectivity":"bluetooth"}'::jsonb,
                                                  '入门级蓝牙耳机，通勤够用。','价格亲民／日常通勤', 'ON_SALE', FALSE);

-- 口红（商家 3）
INSERT INTO product (id, merchant_id, sku_code, name, category_l1, category_l2, brand,
                     price, original_price, stock, attributes, description, selling_points,
                     status, is_new_arrival) VALUES
                                                 (26, 3, 'LIP-001', 'YSL 小金条口红 #52',          '美妆', '口红', 'YSL',    380.00, 420.00, 80,
                                                  '{"color":"温柔豆沙","finish":"matte","skin_type":"all"}'::jsonb,
                                                  '温柔豆沙色，哑光妆感。','温柔显白／哑光高级', 'ON_SALE', FALSE),

                                                 (27, 3, 'LIP-002', 'Dior 烈艳蓝金 #999',          '美妆', '口红', 'Dior',   360.00, 400.00, 60,
                                                  '{"color":"正红","finish":"satin","skin_type":"all"}'::jsonb,
                                                  '经典正红，任何场合都合适。','正红百搭／经典色号', 'ON_SALE', FALSE),

                                                 (28, 3, 'LIP-003', '3CE 云朵雾面 #908',           '美妆', '口红', '3CE',    140.00, 180.00, 120,
                                                  '{"color":"奶茶色","finish":"matte","skin_type":"normal"}'::jsonb,
                                                  '韩妆奶茶色，学生党友好。','价格友好／温柔奶茶', 'ON_SALE', FALSE),

                                                 (29, 3, 'LIP-004', 'MAC 子弹头 #ruby woo',        '美妆', '口红', 'MAC',    220.00, 260.00, 90,
                                                  '{"color":"复古红","finish":"matte","skin_type":"all"}'::jsonb,
                                                  '复古红丝绒哑光。','复古红／丝绒质感', 'ON_SALE', FALSE),

                                                 (30, 3, 'LIP-005', 'Armani 红管 #405',            '美妆', '口红', 'Armani', 320.00, 360.00, 50,
                                                  '{"color":"番茄红","finish":"matte","skin_type":"all"}'::jsonb,
                                                  '番茄红丝绒哑光。','鲜活番茄红／显白', 'ON_SALE', TRUE);

SELECT setval('product_id_seq', 30);


-- ============================================================================
-- 四、FAQ（12 条，可直接命中）
-- ============================================================================
INSERT INTO faq_entry (merchant_id, question, answer, category) VALUES
-- 平台通用（merchant_id = 0）
(0, '发货时间是多久？',       '工作日 48 小时内发货，节假日会适当顺延。具体请在订单详情页查看物流进度。', '物流'),
(0, '多久能收到货？',         '一般下单后 3-5 个工作日内送达，偏远地区可能需要 5-7 天。', '物流'),
(0, '怎么申请退货？',         '商品签收 7 天内可无理由退货，在"我的订单"页面点击申请退货即可，客服会在 24 小时内处理。', '售后'),
(0, '怎么申请换货？',         '商品质量问题 15 天内可换货，请在订单详情提交换货申请并上传凭证。', '售后'),
(0, '支持哪些支付方式？',     '支持支付宝、微信支付、银行卡支付、以及 Apple Pay。', '支付'),
(0, '怎么开发票？',           '在订单完成后可在订单详情页申请电子发票，10 个工作日内开具完成。', '发票'),
(0, '可以修改收货地址吗？',   '订单未发货前可在"我的订单"→"修改地址"自助更新；已发货请联系客服协助。', '物流'),
(0, '订单怎么取消？',         '未支付订单 30 分钟自动取消；已支付未发货的可申请取消，发货后请走退货流程。', '售后'),

-- 商家 1 的物流承诺
(1, '你们家多久发货？',       '飞跃运动旗舰店承诺下单后 24 小时内发货，全国包邮。', '物流'),
(1, '鞋子尺码怎么选？',       '建议按脚长对照鞋码表选择；Nike / Adidas 偏大半码建议拍小；New Balance / Asics 偏正码。', '售后'),

-- 商家 2 的售后
(2, '手表进水了怎么办？',     '请立刻关停龙头，48 小时内联系我们走售后；不同型号防水等级不同，详情页会标明。', '售后'),

-- 商家 3 的保修
(3, '耳机保修多久？',         '新声音频严选所售耳机一律提供 12 个月全国联保，非人为损坏免费维修或换新。', '售后');


-- ============================================================================
-- 五、历史会话示例（2 条，一条下单 / 一条越权兜底）
-- ============================================================================

-- 会话 1：Alice 找跑鞋、成功下单
INSERT INTO session (id, user_id, merchant_id, started_at, ended_at, channel, locale, outcome, total_tokens) VALUES
    ('sess-demo-001', 1, 1, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '90 minutes',
     'HOME_ENTRY', 'zh_cn', 'ORDERED', 1820);

INSERT INTO session_message (session_id, turn, role, agent_name, content_text, tokens) VALUES
                                                                                           ('sess-demo-001', 1, 'USER',      NULL,            '帮我找一双缓震好的跑鞋',                 18),
                                                                                           ('sess-demo-001', 2, 'ASSISTANT', 'ClarifyAgent',  '好呀，你的预算大概在多少？脚型怎么样？',   32),
                                                                                           ('sess-demo-001', 3, 'USER',      NULL,            '一千以内吧，扁平足',                     15),
                                                                                           ('sess-demo-001', 4, 'ASSISTANT', 'RecommendAgent','给你推荐 Asics Gel-Kayano 30 和 HOKA Clifton 9', 45),
                                                                                           ('sess-demo-001', 5, 'USER',      NULL,            '第一双怎么样',                          12),
                                                                                           ('sess-demo-001', 6, 'ASSISTANT', 'EmotionAgent',  'Kayano 30 对扁平足的支撑做得很到位，4D 稳定系统...',  180),
                                                                                           ('sess-demo-001', 7, 'USER',      NULL,            '那就要这个',                            10),
                                                                                           ('sess-demo-001', 8, 'ASSISTANT', 'OrderAgent',    '好的，为你下单 Asics Kayano 30 一双，共 1599 元', 40);

INSERT INTO session_state (session_id, phase, current_intent, slots, last_recommendations) VALUES
    ('sess-demo-001', 'ENDED', 'ORDER_CONFIRM',
     '{"category":"跑鞋","budget":1000,"foot_type":"flat"}'::jsonb,
     ARRAY[4,5]::bigint[]);

INSERT INTO order_record (order_no, idempotency_key, user_id, merchant_id, session_id, product_id, sku_code,
                          quantity, unit_price, total_amount, status, agent_attribution,
                          receiver_name) VALUES
    ('VS20260101000001', 'seed-order-sess-demo-001', 1, 1, 'sess-demo-001', 4, 'RUN-004', 1, 1599.00, 1599.00, 'PAID', TRUE, '爱丽丝');

-- 会话 2：David 越权 / 异常输入兜底（OUT_OF_SCOPE 分支）
INSERT INTO session (id, user_id, merchant_id, started_at, ended_at, channel, locale, outcome, total_tokens) VALUES
    ('sess-demo-002', 4, NULL, NOW() - INTERVAL '1 hour', NOW() - INTERVAL '50 minutes',
     'SEARCH_FALLBACK', 'zh_cn', 'ABANDONED', 120);

INSERT INTO session_message (session_id, turn, role, agent_name, content_text, tokens) VALUES
                                                                                           ('sess-demo-002', 1, 'USER',      NULL,            '帮我写一份周报',                                                  10),
                                                                                           ('sess-demo-002', 2, 'ASSISTANT', 'EmotionAgent',  '鸡哥现在只负责帮你挑商品，这个问题回头可以找客服处理哈。我们继续聊想买什么？',  30);

INSERT INTO session_state (session_id, phase, current_intent, slots) VALUES
    ('sess-demo-002', 'ENDED', 'OUT_OF_SCOPE', '{}'::jsonb);


-- ============================================================================
-- 完
-- ============================================================================
-- 验证：导入后应看到
--   SELECT COUNT(*) FROM product;             -- 30
--   SELECT COUNT(*) FROM faq_entry;           -- 12
--   SELECT COUNT(*) FROM merchant;            -- 3
--   SELECT COUNT(*) FROM app_user;            -- 5
--   SELECT COUNT(*) FROM session;             -- 2
--   SELECT COUNT(*) FROM order_record;        -- 1
-- ============================================================================
