# MWI 试炼分配计算器 · 二次开发包

## 一、项目定位
银河奶牛（MWI，milkywayidle.com）公会「试炼分配计算器」。给定公会成员的技能等级与装备，用算法算出 4 个试炼最优人员分配，使公会总通关数最高。

纯 Excel 公式无法实现（核心分配算法是迭代图算法 MCMF + 局部搜索），故落地为独立单页 Web 工具。

## 二、本包结构（源码 + 资源，可直接二次开发）
```
mwi_devkit/
├── README.md
├── generate_html.py              # 从素材生成计算器网页（单文件 HTML）
├── items.svg                     # 装备图标源（960 个 SVG symbol）
├── skills_sprite.svg             # 17 个纯技能图标（来自游戏 CDN）
├── buffs_sprite.svg              # 全局 BUFF 图标（gathering/efficiency/action_speed，来自游戏 CDN）
├── equip.json                    # 权威槽位→中文装备名列表（生成 EQUIP_ICONS 用）
├── item_name_map.json            # 中文名→iconId 映射（生成图标用）
└── mwi_data_export.user.js       # 油猴导出脚本（v0.6.0，源文件）
```
说明：
- `mwi_trial_calculator.html`（计算器成品）由 `generate_html.py` 生成，**不纳入本包**；用本包可随时重新生成，避免与源素材重复。
- `skill_icons.svg` 等中间产物均由 `items.svg` 派生，无需单独保留，生成方式已内置于 `generate_html.py`。
- `generate_html.py` 内的路径已扁平化：`equip.json`、`item_name_map.json` 直接从包根目录读取。

## 三、两大组件

### 1. 计算器网页（由 generate_html.py 生成的单文件 HTML）
- 单页布局：顶部 4 个试炼配置卡片（技能图标选择 + 人数上限 + 可滚动成员列表）→ 全局加成栏 → 下方成员大表格。
- 双展示分配结果：成员表「分配」列显示试炼图标 + 试炼卡片下方滚动成员列表，两处同步。
- 个人装备系统：每成员 22 个装备槽（12 防具 + 10 技能工具，已移除饰品/护符，双手并入主手）。图标为 Enhancelator 风格网格选择器，强化等级 +0~+20。装备加成影响算法（工具加成特定技能，防具加成全部技能）。
- **全局 BUFF**：顶部「全局加成」栏三项输入——采集数量（gathering）/生产效率（efficiency）/强化速度（action_speed），0=无、1~20 级，加成% = 19.5 + 等级×0.5（Enhancelator 风格公式）。采集类→双倍产出概率、生产类→效率、强化→动作速度。仅本地保存（localStorage `mwi_global_buffs`），不上传共享。
- 图标：内联 447 个 SVG（17 技能 + 427 装备 + 3 全局 BUFF），来自 `skills_sprite.svg`、`items.svg`、`buffs_sprite.svg`；装备图标经 `equip.json` + `item_name_map.json` 映射生成，无后缀猜测。
- i18n：中/英（`t(key)`，localStorage 持久化）。
- 主题：浅色/深色 CSS 变量切换。
- 算法常量：试炼 3600 秒、起始 100 级、每通关 +10 级；基础行动 10 秒、成功率 80%；每级基础 40000 点、每通关 +4000；人数膨胀系数 0.01。
- 核心算法 4 步：每人每技能指标 → 通关层数模拟（computePasses）→ 最小费用流分配（MCMF+SPFA）→ 局部搜索优化（localSearch，交换爬山）。

### 2. 数据导出油猴脚本 `mwi_data_export.user.js` v0.6.0
- 进游戏后 Hook WebSocket 抓取 `init_character_data` / `profile_shared`，缓存成员完整 profile。
- 检测到公会成员页后自动遍历成员（view_profile 经 WebSocket 直发，绕开 UI 可信校验），逐个缓存后「导出完整原始数据到 JSON」。
- 输出 JSON 数组：自己角色由 buildPayload 构建，公会成员直接用 profile 原对象。文件名 `MWI_公会_N人_日期.json`。
- 提供「自动采集」菜单命令与「重新采集」按钮。

## 四、数据流（端到端）
1. 安装 `mwi_data_export.user.js` → 进游戏/公会成员页 → 自动采集 → 点导出得到 JSON。
2. 打开生成的计算器 HTML → 点「导入」读 JSON（数组格式）→ 自动计算并显示分配。
3. 网页导入按钮旁有 📦 链接，可直接下载该油猴脚本（链接目标即 `mwi_data_export.user.js`）。

## 五、在线协作（jsonbin.io + 本地加密）
- 后端用 jsonbin.io public bin：创建须带 `X-Bin-Private:false`；写操作须带 `X-Master-Key`。
- **密钥派生**：加密密码为固定常量 `SHARE_PASSWORD = 'layu'`，`PBKDF2('layu', guild)` 派生 AES-GCM 256 密钥（兼容既有 bin）。分享链接只含 `guild` + `bin` 两个参数，不再带 `pwd`/`mk`（旧链接的 `mk` 参数仍向后兼容读取）。
- Master Key 只存创建者本地（localStorage），不进分享链接——写权限真正受控于创建者。
- gzip 压缩：免费套餐单条 100KB 上限，80 人数据经 gzip 后约 5.9KB base64；用 CompressionStream/DecompressionStream，不支持时降级不压缩。
- **导入语义**：导入 JSON = 整体替换名单，导入成员统一打 `_ts` 并立即 `forcePushToBin` 全量覆盖 bin（不走合并），防止被远端旧数据覆盖。
- **删除语义（墓碑机制）**：`deletedIds` 记录已删除成员 id，`mergeState` 合并两端墓碑并过滤，防止共享模式下删除的成员被远端旧数据"复活"。
- 并发安全：保存时先 GET 远端，按 `_ts` 时间戳逐条合并（merge-on-save）。共享模式显示 🔄 刷新按钮。
- 无 URL 参数时走 localStorage 离线模式。

## 六、构建与二次开发
- 生成计算器：在包根目录运行 `python generate_html.py`，读取 `items.svg`、`skills_sprite.svg`、`buffs_sprite.svg`、`equip.json`、`item_name_map.json`，输出 `mwi_trial_calculator.html`（单文件，可直接浏览器打开）。
- 导出脚本：直接在 `mwi_data_export.user.js` 修改即可（v0.6.0，已精简到约 976 行）。按油猴脚本规范发布，`@match` 已在文件头定义。
- 如需重新生成 `item_name_map.json`（中文名→iconId），原始数据来自游戏本地化 chunk，解析脚本为 `parse_zh_items.py`（未纳入本包，仅说明来源）。

## 七、现状要点与边界
- 当前版本：计算器 2026-07-31 版（v5.4 + 全局 BUFF + 共享修复），导出脚本 v0.6.0。
- 导入仅接受 JSON 数组（已移除 CSV、单对象、JSONL），导入即整体替换共享 bin。
- 装备仅 22 槽、无饰品/护符、双手并入主手；装备图标 427 个全部成功映射。
- 全局 BUFF 仅本地生效，不参与共享同步。
- 不兼容旧（未压缩）jsonbin 数据（v5.4b 已移除旧格式兼容）。
- 测试基线：80 人满装备约 33ms，总等级 810 / 通关 41 次。
