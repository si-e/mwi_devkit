#!/usr/bin/env python3
"""Generate MWI Trial Calculator HTML v4 - i18n, themes, correct skill icons, reqNext."""

import re, json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Load Chinese item name -> icon ID mapping (generated from game localization)
ITEM_NAME_MAP_PATH = os.path.join(BASE_DIR, 'item_name_map.json')
ITEM_NAME_MAP = {}
if os.path.exists(ITEM_NAME_MAP_PATH):
    with open(ITEM_NAME_MAP_PATH, 'r', encoding='utf-8') as f:
        ITEM_NAME_MAP = json.load(f)

# 游戏数据（装备/工具/房屋/公会加成 + 游戏 client 定义），与生成逻辑分离，单独维护。
GAME_DATA_PATH = os.path.join(BASE_DIR, 'mwi_data.json')
GAME_DATA = {}
if os.path.exists(GAME_DATA_PATH):
    with open(GAME_DATA_PATH, 'r', encoding='utf-8') as f:
        GAME_DATA = json.load(f)
else:
    print('WARNING: mwi_data.json not found, game data will be missing')

SKILL_KEYS = ['milking','foraging','woodcutting','cheesesmithing','crafting','tailoring','cooking','brewing','alchemy','enhancing']
SKILL_LABELS = ['挤奶','采摘','伐木','奶酪锻造','制作','缝纫','烹饪','冲泡','炼金','强化']

EQUIP_TYPES = [
    '主手','副手','头部','身体','手部','腿部','脚部',
    '项链','耳环','戒指','袋子','背部',
    '挤奶工具','采摘工具','伐木工具','奶酪锻造工具','制作工具','缝纫工具','烹饪工具','冲泡工具','炼金工具','强化工具'
]

# ============================================================
# Categorization
# ============================================================

def categorize_item(sid):
    """Returns equipment type for a symbol ID, or None if not equipment."""
    base = sid.replace('_refined', '')
    sl = base.lower()

    # 1. Skill tools (most specific)
    tool_map = {
        'brush': '挤奶工具', 'shears': '采摘工具', 'hatchet': '伐木工具',
        'hammer': '奶酪锻造工具', 'chisel': '制作工具', 'needle': '缝纫工具',
        'spatula': '烹饪工具', 'pot': '冲泡工具', 'alembic': '炼金工具',
        'enhancer': '强化工具',
    }
    for suffix, cat in tool_map.items():
        if sl == suffix or sl.endswith('_' + suffix):
            return cat

    # 2. Charm / Accessory — removed (not used)

    # 3. Ring
    if 'ring_of' in sl or sl.endswith('_ring') or sl == 'ring':
        return '戒指'

    # 4. Earring
    if 'earring' in sl:
        return '耳环'

    # 5. Necklace
    if 'necklace' in sl:
        return '项链'

    # 6. Cape/Cloak
    if sl.endswith('_cape') or sl == 'cape' or sl.endswith('_cloak') or sl == 'cloak':
        return '背部'

    # 7. Bag
    if sl.endswith('_pouch') or sl == 'pouch':
        return '袋子'

    # 8. Main hand weapons
    weapon_suffixes = ['sword','mace','spear','bow','crossbow','staff',
                       'slasher','stabber','smasher','trident','dirk','boomstick']
    for suffix in weapon_suffixes:
        if sl == suffix or sl.endswith('_' + suffix):
            return '主手'

    # 9. Off hand
    offhand_suffixes = ['shield','buckler','bulwark','codex','scroll']
    for suffix in offhand_suffixes:
        if sl == suffix or sl.endswith('_' + suffix):
            return '副手'

    # 10. Head
    for suffix in ['helmet','hat','hood']:
        if sl == suffix or sl.endswith('_' + suffix):
            return '头部'

    # 11. Body
    if sl.endswith('_plate_body') or sl.endswith('_robe_top') or \
       sl.endswith('_tunic') or sl.endswith('_vest') or sl.endswith('_top'):
        return '身体'

    # 12. Legs
    if sl.endswith('_plate_legs') or sl.endswith('_robe_bottoms') or \
       sl.endswith('_chaps') or sl.endswith('_bottoms'):
        return '腿部'

    # 13. Hands
    for suffix in ['gauntlets','gloves','bracers']:
        if sl == suffix or sl.endswith('_' + suffix):
            return '手部'

    # 14. Feet
    for suffix in ['boots','shoes']:
        if sl == suffix or sl.endswith('_' + suffix):
            return '脚部'

    # 15. Accessory — removed (not used)
    # tome_of_* and seal_of_* also fall through to None
    return None


def extract_symbol(content, sid):
    pattern = r'<symbol[^>]*id="' + re.escape(sid) + r'"[^>]*>.*?</symbol>'
    m = re.search(pattern, content, re.DOTALL)
    return m.group() if m else None


def pretty_name(sid):
    return sid.replace('_', ' ').title()


# ============================================================
# CSS
# ============================================================

CSS = r'''
* { margin:0; padding:0; box-sizing:border-box; }
:root {
  --bg:#f5f5f5; --surface:#fff; --border:#ddd; --text:#333; --text-muted:#666; --text-faint:#999;
  --header-bg:#fff; --hover:#f0f0f0; --accent:#4a90d9; --accent-hover:#3a7bc8;
  --table-header:#f8f8f8; --table-hover:#f9f9f9; --input-bg:#fff; --shadow:rgba(0,0,0,.15);
  --modal-bg:#fff; --modal-overlay:rgba(0,0,0,.4); --list-bg:#fafafa; --list-border:#eee;
  --scrollbar-thumb:#ccc; --scrollbar-track:#f0f0f0;
  --assign-t1-bg:#e3f2fd; --assign-t1-fg:#1565c0;
  --assign-t2-bg:#e8f5e9; --assign-t2-fg:#2e7d32;
  --assign-t3-bg:#fff3e0; --assign-t3-fg:#e65100;
  --assign-t4-bg:#fce4ec; --assign-t4-fg:#c62828;
  --enhance-badge-bg:rgba(0,0,0,0.7); --enhance-badge-fg:#ffd700;
  --equip-hover:#f0f7ff; --icon-name-bg:#333; --icon-name-fg:#fff;
  --enhance-sel-bg:#4a90d9; --enhance-sel-fg:#fff;
  --conn-bg:#f0f0f0; --danger:#d9534f; --search-border:#ccc;
}
[data-theme="dark"] {
  --bg:#1a1a2e; --surface:#16213e; --border:#30475e; --text:#e0e0e0; --text-muted:#a0a0a0; --text-faint:#666;
  --header-bg:#16213e; --hover:#1a1a2e; --accent:#4a90d9; --accent-hover:#5a9fe8;
  --table-header:#1a1a2e; --table-hover:#1e2746; --input-bg:#1a1a2e; --shadow:rgba(0,0,0,.4);
  --modal-bg:#16213e; --modal-overlay:rgba(0,0,0,.6); --list-bg:#0f1623; --list-border:#30475e;
  --scrollbar-thumb:#30475e; --scrollbar-track:#0f1623;
  --assign-t1-bg:#0d2538; --assign-t1-fg:#64b5f6;
  --assign-t2-bg:#0d2e1d; --assign-t2-fg:#66bb6a;
  --assign-t3-bg:#3e2510; --assign-t3-fg:#ffa726;
  --assign-t4-bg:#3e0d1e; --assign-t4-fg:#ef5350;
  --enhance-badge-bg:rgba(255,255,255,0.85); --enhance-badge-fg:#b8860b;
  --equip-hover:#1a2744; --icon-name-bg:#e0e0e0; --icon-name-fg:#16213e;
  --enhance-sel-bg:#4a90d9; --enhance-sel-fg:#fff;
  --conn-bg:#0f1623; --danger:#ef5350; --search-border:#30475e;
}
body { font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; background:var(--bg); color:var(--text); font-size:14px; transition:background .2s,color .2s; }
h1 { font-size:20px; }
h2 { font-size:16px; margin:10px 0 8px; color:var(--text-muted); }

/* Header */
.header { background:var(--header-bg); padding:10px 20px; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; flex-wrap:wrap; gap:8px; position:sticky; top:0; z-index:100; }
.header-left { display:flex; align-items:center; gap:10px; }
.header-right { display:flex; gap:6px; flex-wrap:wrap; align-items:center; }
.btn { padding:6px 14px; border:1px solid var(--border); border-radius:4px; background:var(--surface); color:var(--text); cursor:pointer; font-size:13px; transition:all .15s; }
.btn:hover { background:var(--hover); border-color:var(--text-muted); }
.btn-primary { background:var(--accent); color:#fff; border-color:var(--accent); }
.btn-primary:hover { background:var(--accent-hover); }
.btn-danger { color:var(--danger); }
.btn-sm { padding:3px 8px; font-size:12px; }
.btn-icon { padding:6px 10px; font-size:16px; line-height:1; }
.connection-status { font-size:12px; color:var(--text-muted); padding:2px 8px; border-radius:3px; background:var(--conn-bg); }

/* Global Buff */
.global-buff-section { padding:8px 20px 0 20px; }
.global-buff-section h3 { font-size:13px; font-weight:600; margin:0 0 6px 0; color:var(--text-muted); display:flex; align-items:center; gap:6px; }
.global-buff-hint { font-size:11px; color:var(--text-faint); font-weight:400; cursor:help; }
.global-buff-hint::before { content:'ℹ'; display:inline-block; width:14px; height:14px; line-height:14px; text-align:center; border:1px solid var(--border); border-radius:50%; }
.global-buff-bar { display:flex; flex-wrap:wrap; gap:14px; align-items:center; }
/* 公会建筑栏：三块（功能/生活/战斗）各占一行 */
.global-buff-bar.is-stacked { flex-direction:column; gap:8px; align-items:stretch; }
/* 三块（功能/生活类/战斗类）各自占一行；行内是「每行最多 5 个」的等宽网格
   —— 等宽列让字数不同的建筑名也自动按最宽的那一列对齐 */
.global-buff-row { display:flex; align-items:flex-start; gap:10px; }
.global-buff-grid { flex:1; min-width:0; display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:6px 10px; }
@media(max-width:1100px){ .global-buff-grid { grid-template-columns:repeat(4,minmax(0,1fr)); } }
@media(max-width:860px){ .global-buff-grid { grid-template-columns:repeat(3,minmax(0,1fr)); } }
@media(max-width:640px){ .global-buff-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.global-buff-item { display:flex; align-items:center; gap:6px; min-width:0; padding:4px 10px; border:1px solid var(--border); border-radius:4px; background:var(--conn-bg); font-size:12px; color:var(--text); cursor:pointer; }
/* 网格里标签占满剩余宽度 → 等级输入框右对齐（不同字数也能对齐） */
.global-buff-grid .global-buff-label { flex:1; min-width:0; word-break:break-word; }
.global-buff-item .global-buff-icon { width:18px; height:18px; flex:0 0 auto; vertical-align:middle; }
.global-buff-item input { width:48px; padding:2px 6px; border:1px solid var(--border); border-radius:3px; background:var(--input-bg); color:var(--text); font-size:12px; text-align:center; }
.global-buff-item input:focus { outline:none; border-color:var(--accent); }
.global-buff-item .global-buff-unit { color:var(--text-faint); font-size:11px; }
.global-buff-item.is-utility { opacity:.85; }
.global-buff-item.is-inactive { opacity:.55; }
.global-buff-item.is-inactive .global-buff-label { text-decoration:line-through; }
.global-buff-item.is-life { border-color:var(--border); }
.global-buff-item.is-combat { opacity:.8; }
.global-buff-tag { font-size:10px; line-height:1; color:var(--accent); border:1px solid var(--accent); border-radius:3px; padding:2px 4px; }
.global-buff-group-label { font-size:11px; color:var(--text-faint); flex:0 0 auto; width:64px; padding-top:6px; text-align:right; }
.global-buff-subhint { font-size:11px; font-weight:400; color:var(--text-faint); }

/* Trial Config */
.trial-section { padding:10px 20px; }
.trial-cards { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
@media(max-width:1000px){ .trial-cards{grid-template-columns:repeat(2,1fr);} }
@media(max-width:600px){ .trial-cards{grid-template-columns:1fr;} }
.trial-card { background:var(--surface); border:1px solid var(--border); border-radius:8px; padding:12px; display:flex; flex-direction:column; gap:8px; }
.trial-card-header { display:flex; align-items:center; gap:8px; }
.trial-skill-icon { width:40px; height:40px; cursor:pointer; border:2px solid transparent; border-radius:6px; transition:border-color .15s; }
.trial-skill-icon:hover { border-color:var(--accent); }
.trial-skill-icon svg { width:100%; height:100%; }
.trial-card-info { flex:1; }
.trial-card-title { font-size:14px; font-weight:600; }
.trial-skill-name { font-size:12px; color:var(--text-muted); }
.trial-max-row { display:flex; align-items:center; gap:6px; font-size:12px; }
.trial-max-row input { width:50px; padding:2px 4px; border:1px solid var(--border); border-radius:3px; font-size:12px; background:var(--input-bg); color:var(--text); }
.trial-max-value { font-weight:600; color:var(--text); }
.trial-max-hint { font-size:10px; color:var(--text-faint); border:1px solid var(--border); border-radius:3px; padding:1px 4px; }
.trial-member-list { max-height:100px; overflow-y:auto; border:1px solid var(--list-border); border-radius:4px; padding:4px; background:var(--list-bg); font-size:12px; }
.trial-member-list:empty::after { content:attr(data-empty); color:var(--text-faint); display:block; text-align:center; padding:10px; }
.trial-member-item { padding:2px 6px; border-radius:3px; display:flex; justify-content:space-between; }
.trial-member-item:hover { background:var(--hover); }
.trial-member-item .ml { color:var(--text-muted); }
.trial-member-item .mr { color:var(--text-faint); }
.trial-result { font-size:11px; font-weight:600; color:var(--accent); padding-top:4px; border-top:1px solid var(--list-border); line-height:1.5; }

/* Member Table */
.member-section { padding:10px 20px; }
.table-wrap { overflow-x:auto; background:var(--surface); border:1px solid var(--border); border-radius:8px; }
table.member-table { border-collapse:collapse; width:max-content; min-width:100%; }
table.member-table th, table.member-table td { border:1px solid var(--border); padding:4px 6px; text-align:center; white-space:nowrap; }
table.member-table th { background:var(--table-header); font-size:11px; font-weight:600; color:var(--text-muted); position:sticky; top:0; z-index:5; }
table.member-table th.assign-col { min-width:44px; }
table.member-table th.name-col { min-width:150px; text-align:left; }
table.member-table td.name-cell { text-align:left; }
table.member-table td input { width:100%; border:1px solid transparent; background:transparent; font-size:13px; padding:2px 4px; border-radius:3px; color:var(--text); }
table.member-table td input:focus { border-color:var(--accent); background:var(--input-bg); outline:none; }
/* 「详情」列：专业 / 装备 / 房屋 / 神龛 / 成就 等全部个人数据移入成员详情弹窗 */
table.member-table th.detail-col { min-width:52px; }
table.member-table td.detail-cell { text-align:center; }
/* 成员详情弹窗正文（专业 / 装备 / 房屋 / 神龛 / 成就，按分组网格排布） */
.detail-body { overflow-y:auto; min-height:0; }
.detail-section { border-top:1px solid var(--border); padding-top:8px; }
.detail-section:first-child { border-top:none; padding-top:0; }
.detail-section-title { font-size:12px; font-weight:600; color:var(--text-muted); margin-bottom:6px; cursor:help; }
/* 分组网格：每行最多 5 个；页面（或缩放）变窄时自动降到 4 / 3 / 2 个 */
.detail-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr)); gap:6px; }
.detail-grid.cols-5 { grid-template-columns:repeat(5,minmax(0,1fr)); }
@media(max-width:1100px){ .detail-grid, .detail-grid.cols-5 { grid-template-columns:repeat(4,minmax(0,1fr)); } }
@media(max-width:860px){ .detail-grid, .detail-grid.cols-5 { grid-template-columns:repeat(3,minmax(0,1fr)); } }
@media(max-width:640px){ .detail-grid, .detail-grid.cols-5 { grid-template-columns:repeat(2,minmax(0,1fr)); } }
.detail-item { display:flex; align-items:center; gap:6px; padding:4px 6px; border:1px solid var(--border); border-radius:6px; }
.detail-item.is-inactive { opacity:.55; }
.detail-item svg { width:20px; height:20px; flex:none; }
.detail-item .di-label { flex:1; min-width:0; font-size:10px; line-height:1.15; color:var(--text-muted); word-break:break-word; }
.detail-item .di-sub { display:block; color:var(--text-faint); }
.detail-item input[type=number] { width:46px; flex:none; text-align:center; border:1px solid var(--border); background:var(--input-bg); border-radius:4px; color:var(--text); font-size:12px; padding:1px 2px; }
.detail-item input[type=checkbox] { width:auto; margin:0; cursor:pointer; accent-color:var(--accent); flex:none; }
/* 详情里的装备槽：图标 + 强化角标，点击打开装备选择器 */
.detail-item .equip-cell { width:30px; height:30px; flex:none; margin-left:auto; }
.detail-item .equip-cell svg { width:24px; height:24px; }
/* 神龛分两行：上行「生活类」、下行「战斗类」 */
.detail-rows { display:flex; flex-direction:column; gap:6px; }
.detail-row { display:flex; align-items:center; gap:8px; }
.detail-row-label { flex:none; width:40px; font-size:10px; color:var(--text-faint); text-align:right; }
.detail-row .detail-grid { flex:1; min-width:0; }
/* 生活装备区：与工具 / 战斗装备同款的方格，每行最多 5 个（格子只有图标，物品名在悬停提示里）。
   方格的「未拥有 / 已拥有」样式见下方 .equip-cell.own-cell。 */
.own-rows { display:flex; flex-direction:column; gap:6px; }
.own-row { display:flex; align-items:flex-start; gap:8px; }
.own-row-label { flex:none; width:64px; padding-top:10px; font-size:11px; color:var(--text-muted); text-align:right; }
.own-chips { flex:1; min-width:0; display:grid; grid-template-columns:repeat(5,36px); gap:6px; justify-content:start; }
/* 强化等级小面板（点 chip 正文弹出，挂在 body 上，不被弹窗滚动容器裁切） */
.enh-pop { position:fixed; z-index:400; width:214px; background:var(--modal-bg); border:1px solid var(--border); border-radius:8px; padding:8px; box-shadow:0 6px 18px var(--shadow); display:flex; flex-direction:column; gap:6px; }
.enh-pop-title { font-size:12px; font-weight:600; color:var(--text); }
.enh-pop-title .enh-pop-slot { font-weight:400; color:var(--text-faint); font-size:10px; }
.enh-pop-row { display:flex; align-items:center; gap:4px; }
.enh-pop-step { width:26px; height:26px; flex:none; border:1px solid var(--border); background:var(--input-bg); color:var(--text); border-radius:5px; cursor:pointer; font-size:14px; line-height:1; }
.enh-pop-step:hover { border-color:var(--accent); }
.enh-pop-input { width:56px; flex:none; text-align:center; border:1px solid var(--border); background:var(--input-bg); border-radius:5px; color:var(--text); font-size:13px; padding:3px 2px; }
.enh-pop-unit { font-size:10px; color:var(--text-faint); }
.enh-pop-star { display:flex; align-items:center; gap:6px; font-size:11px; color:var(--text-muted); cursor:pointer; }
.enh-pop-star input { margin:0; cursor:pointer; accent-color:var(--accent); }
.enh-pop-actions { display:flex; justify-content:space-between; gap:6px; }
table.member-table tr:hover { background:var(--table-hover); }
table.member-table td.assign-cell { font-weight:600; font-size:12px; }
table.member-table td.assign-cell svg { width:22px; height:22px; }
.assign-T1 { background:var(--assign-t1-bg); }
.assign-T2 { background:var(--assign-t2-bg); }
.assign-T3 { background:var(--assign-t3-bg); }
.assign-T4 { background:var(--assign-t4-bg); }
.assign-none { color:var(--text-faint); }

/* Equipment cell */
.equip-cell { width:36px; height:36px; position:relative; cursor:pointer; border:1px solid var(--border); border-radius:4px; display:flex; align-items:center; justify-content:center; }
.equip-cell:hover { border-color:var(--accent); background:var(--equip-hover); }
.equip-cell svg { width:30px; height:30px; }
.equip-cell .enhance-badge { position:absolute; top:-2px; left:-2px; background:var(--enhance-badge-bg); color:var(--enhance-badge-fg); font-size:9px; font-weight:700; border-radius:3px; padding:0 2px; line-height:12px; }
.equip-cell.empty::after { content:'+'; color:var(--text-faint); font-size:16px; }
/* 生活装备「拥有制」方格：只有图标（物品名在悬停提示里，与工具 / 战斗装备一致）。
   未拥有 → 虚线框 + 图标灰度（点一下即以 +0 拥有并打开强化面板）；已拥有 → 实线高亮 + 左上角标「★ +N」。 */
.equip-cell.own-cell svg { width:26px; height:26px; }
.equip-cell.own-cell.is-off { border-style:dashed; }
.equip-cell.own-cell.is-off svg { filter:grayscale(1); opacity:.4; }
.equip-cell.own-cell.is-owned { border-color:var(--accent); background:var(--equip-hover); }
.equip-cell .own-badges { position:absolute; top:-4px; left:-4px; display:flex; align-items:center; gap:2px; }
.equip-cell .own-badges .enhance-badge { position:static; top:auto; left:auto; }
.equip-cell .own-badges .refine-star { color:#e8b339; font-size:11px; line-height:1; }

/* Skill picker popup */
.skill-picker-popup { position:absolute; background:var(--modal-bg); border:1px solid var(--border); border-radius:8px; padding:8px; z-index:200; display:grid; grid-template-columns:repeat(5,1fr); gap:6px; box-shadow:0 4px 12px var(--shadow); }
.skill-picker-popup .skill-option { width:36px; height:36px; cursor:pointer; border:2px solid transparent; border-radius:6px; }
.skill-picker-popup .skill-option:hover { border-color:var(--accent); }
.skill-picker-popup .skill-option svg { width:100%; height:100%; }
.skill-picker-popup .skill-option.selected { border-color:var(--accent); background:var(--equip-hover); }

/* Equipment Picker Modal */
.modal-overlay { position:fixed; top:0; left:0; right:0; bottom:0; background:var(--modal-overlay); z-index:300; display:flex; align-items:center; justify-content:center; }
.modal-dialog { background:var(--modal-bg); border-radius:12px; padding:20px; max-width:560px; width:90%; max-height:80vh; display:flex; flex-direction:column; gap:12px; box-shadow:0 8px 32px var(--shadow); color:var(--text); }
.modal-title { font-size:16px; font-weight:600; display:flex; justify-content:space-between; align-items:center; }
.modal-close { cursor:pointer; font-size:20px; color:var(--text-faint); border:none; background:none; }
.modal-close:hover { color:var(--text); }
.equip-search { padding:6px 10px; border:1px solid var(--search-border); border-radius:6px; font-size:13px; width:100%; background:var(--input-bg); color:var(--text); }
.equip-icon-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(44px, 1fr)); gap:6px; overflow-y:auto; max-height:300px; padding:4px; border:1px solid var(--list-border); border-radius:6px; }
.equip-icon-option { width:40px; height:40px; cursor:pointer; border:2px solid transparent; border-radius:6px; display:flex; align-items:center; justify-content:center; position:relative; }
.equip-icon-option:hover { border-color:var(--accent); }
.equip-icon-option.selected { border-color:var(--accent); background:var(--equip-hover); }
.equip-icon-option svg { width:32px; height:32px; }
.equip-icon-option .icon-name { display:none; position:absolute; bottom:100%; left:50%; transform:translateX(-50%); background:var(--icon-name-bg); color:var(--icon-name-fg); padding:2px 6px; border-radius:3px; font-size:10px; white-space:nowrap; z-index:10; }
.equip-icon-option:hover .icon-name { display:block; }
.enhance-selector { display:flex; flex-wrap:wrap; gap:4px; }
.enhance-btn { padding:3px 8px; border:1px solid var(--border); border-radius:4px; background:var(--surface); color:var(--text); cursor:pointer; font-size:12px; }
.enhance-btn:hover { background:var(--hover); }
.enhance-btn.selected { background:var(--enhance-sel-bg); color:var(--enhance-sel-fg); border-color:var(--accent); }
.modal-actions { display:flex; gap:8px; justify-content:flex-end; }
.equip-preview { display:flex; align-items:center; gap:8px; padding:8px; background:var(--list-bg); border-radius:6px; }
.equip-preview .equip-cell { border:1px solid var(--border); }
.equip-preview-label { font-size:12px; color:var(--text-muted); }

/* Summary */
.summary-bar { padding:8px 20px; background:var(--surface); border-top:1px solid var(--border); display:flex; gap:20px; font-size:13px; flex-wrap:wrap; color:var(--text); }
.summary-bar span { font-weight:600; }
.summary-bar .summary-num { color:var(--accent); }

/* Share Dialog */
.share-field { margin-bottom:8px; }
.share-field label { display:block; font-size:12px; color:var(--text-muted); margin-bottom:2px; }
.share-field input { width:100%; padding:6px 8px; border:1px solid var(--search-border); border-radius:4px; font-size:13px; background:var(--input-bg); color:var(--text); }
.share-url { padding:8px; background:var(--list-bg); border-radius:4px; font-size:12px; word-break:break-all; cursor:pointer; color:var(--text); }
.share-url:hover { background:var(--hover); }

.hidden { display:none !important; }
/* Scrollbar */
::-webkit-scrollbar { width:8px; height:8px; }
::-webkit-scrollbar-thumb { background:var(--scrollbar-thumb); border-radius:4px; }
::-webkit-scrollbar-track { background:var(--scrollbar-track); }
'''

# ============================================================
# JavaScript
# ============================================================

JS = r'''
// === i18n ===
const I18N = {
  zh: {
    title:'MWI 试炼计算器', trialConfig:'试炼配置', memberData:'成员数据',
    addMember:'添加成员', share:'共享设置', importData:'导入', exportData:'导出',
    exportScriptTitle:'下载油猴脚本，自动采集公会成员数据导出为 JSON',
    exportEmpty:'暂无可导出的成员数据',
    exportSuccess:'已导出',
    importFormatUnknown:'无法识别的 JSON：应为「本计算器导出的备份」或「游戏成员 profile 数组」',
    calculate:'计算最优分配', assignCol:'分配', nameCol:'角色名', maxMembers:'人数上限',
    trialSlotsAuto:'由生活营地决定', trialSlotsFromCamp:'生活营地 Lv{level}：{base} + {level}×{per} = {cap}',
    noAssign:'(暂无分配)', noMembers:'暂无成员数据，请添加成员或导入 JSON',
    totalFinalLv:'总最终等级', totalPasses:'总通关', assigned:'已分配', unassigned:'未分配',
    deleteBtn:'删', selectEquip:'选择装备', searchEquip:'搜索装备...',
    enhanceLevel:'强化等级', clear:'清除', cancel:'取消', confirm:'确认',
    noEquip:'未选择装备', passes:'次通关', people:'人', offlineMode:'离线模式',
    connected:'已连接', guildName:'公会名称', password:'访问密码 (用于加密数据)',
    masterKey:'jsonbin.io Master Key (会长填写)',
    shareHint:'会长创建共享空间后，生成分享链接发给成员。成员打开链接即可查看/更新数据，无需注册。',
    currentUrl:'当前共享链接', createShare:'创建共享', closeBtn:'关闭',
    shareCreated:'共享空间已创建！复制链接发给公会成员。', linkCopied:'链接已复制',
    enterPassword:'请输入访问密码:', fillAll:'请填写所有字段',
    createFailed:'创建失败，请检查 Master Key', addMembersFirst:'请先添加成员数据',
    importSuccess:'导入成功', importFailed:'未找到有效数据',
    importMergeReport:'导入完成：更新 {upd} 人 · 新增 {add} 人 · 保留 {keep} 人（本地已有、采集数据中未包含）',
    teamWork:'团队工作能力', nextClearNeeds:'下1次还需', pts:'点', perSec:'点/秒',
    trial:'试炼', language:'中/EN', theme:'🌙',
    globalBuffs:'全局加成',
    globalBuffsTip:'手动输入你所在服务器/账号的社区大厅全局 buff 等级：0 = 无 buff，1~20 级启用。加成 = 19.5 + 等级×0.5（%），仅本地保存，每个玩家按自己实际情况填。',
    guildBuildings:'公会建筑', guildBuildingsTip:'对齐游戏 23 座建筑（上限 20 级），仅在本公会试炼期间生效。生活类/战斗类建筑为对应技能提供 +2 有效等级；功能建筑不影响试炼层数。建筑等级为公会全局，会随共享数据一起上传。',
    guildShrinePerMember:'神龛(个人)', guildShrinePerMemberTip:'神龛是「个人持久化数据」：逐成员填写，随共享数据一起上传。每座神龛分「生活」与「战斗」两种变体：生活增益计入生活试炼推演（力量 效率+0.5%/级、节奏 动作速度+0.5%/级、精神 精华掉率+2%/级、稀有 稀有掉率+1%/级、学者 智慧+0.5%/级）；战斗增益（力量 伤害+0.3%/级、节奏 攻击/施法速度+0.4%/级、精神 生命/法力上限+1%/级 等）为后续战斗试炼预留，暂不计入推演。',
    shrineKindSkilling:'生活', shrineKindCombat:'战斗',
    shrineCombatOnly:'仅影响战斗试炼（暂未模拟）',
    houseRoomsCol:'房屋', houseRoomsTip:'房屋房间是「个人持久化数据」：逐成员填写等级，随共享数据一起上传。生活房间（奶牛棚/花园/木棚 等 效率+1.5%/级；天文台 动作速度+1%/级、强化成功率+0.05%/级）计入生活试炼推演；战斗房间（道场/军械库/健身房 等）为后续战斗试炼预留。数值取自游戏 houseRoomDetailMap。',
    houseRoomsSkilling:'生活', houseRoomsCombat:'战斗',
    guildBuildingsUtility:'功能建筑', guildBuildingsLife:'生活类建筑', guildBuildingsCombat:'战斗类建筑',
    guildBuildingsShared:'公会全局 · 随共享上传',
    shrineAffectsTrial:'影响试炼层数', shrineNotAffectsTrial:'不影响试炼层数',
    shrineCol:'神龛',
    achievementsCol:'成就',
    memberDetail:'成员详情', detailBtn:'详情',
    memberDetailTip:'成员的「专业等级 / 装备 / 房屋 / 神龛 / 成就」等全部个人数据都在详情弹窗里编辑（点该行「详情」按钮），随共享数据一起上传；不影响试炼推演的项显示为灰色。',
    detailSkillSec:'专业等级', detailEquipSec:'装备', detailShrineSec:'神龛', detailAchSec:'成就完成', detailHouseSec:'房屋',
    detailShrineSkillingRow:'生活类', detailShrineCombatRow:'战斗类',
    detailSkillTip:'专业等级属于「个人持久化数据」：逐成员填写，随共享数据一起上传。',
    detailEquipTip:'装备分三区：生活装备（只加生活技能加成）、生活 · 战斗两用、战斗装备 / 生活工具。点方格设置强化等级与 ★ 精炼。',
    lifeEquipSec:'生活装备',
    lifeEquipTip:'只加生活技能加成、没有战斗加成。同一槽位里有多个互不替代的物品，勾选你拥有的即可；推演时每个试炼技能自动取该槽位里收益最高的一件。点方格设置强化等级与 ★ 精炼。',
    lifeSingleRow:'单件',
    hybridEquipSec:'生活 · 战斗两用',
    hybridEquipTip:'项链 / 耳环 / 戒指 / 袋子：同一槽位既可选生活件也可选战斗件，而你只能穿一件，点方格打开选择器二选一。袋子对试炼没有任何加成。',
    lifeToolsSec:'生活工具',
    lifeToolsTip:'生活工具存在上下位替代，只需记录当前使用的那一件。',
    combatEquipSec:'战斗装备',
    combatEquipTip:'一槽一件，与生活装备互不争抢。副手 / 头部 / 身体 / 手部 / 腿部 / 脚部 / 背部 的生活件在上方「生活装备」区勾选，这里的选择器已把它们排除。',
    lifeSlotLabels:{ '身体':'上衣', '腿部':'下装', '背部':'披风', '头部':'头部', '手部':'手部', '脚部':'脚部', '副手':'副手' },
    refineToggle:'精炼',
    unownBtn:'取消拥有',
    enhDone:'完成',
    achievementsTip:'成就档位是「个人持久化数据」：逐成员勾选「该档全部成就已完成」，随共享数据一起上传。共 6 档：初学者 采集数量+2%、新手 经验+2%、熟练者 效率+2%、老手 稀有发现+2%、精英 伤害+2%、冠军 强化成功率+0.2%。影响生活试炼推演的是 初学者/熟练者/冠军；精英为战斗增益（为后续战斗试炼预留）。数值取自游戏 achievementTierDetailMap。',
    guildHallTip:'增加公会成员上限', buildersHallTip:'提高公会点数获取', treasuryTip:'提高公会代币奖励',
    archivesTip:'提高公会经验获取', skillingCampTip:'参加生活试炼人数 +2/级（人数上限 = 20 + 等级×2）', combatCampTip:'参加战斗试炼人数 +2/级（暂未模拟战斗试炼）',
    buffGathering:'采集数量', buffGatheringTip:'仅对采集类技能（挤奶/采摘/伐木）的双倍产出概率生效；0=无，1~20 级，加成 = 19.5 + 等级×0.5（%）。',
    buffProduction:'生产效率', buffProductionTip:'仅对生产类技能（奶酪锻造/制作/缝纫/烹饪/冲泡/炼金）的效率生效；0=无，1~20 级，加成 = 19.5 + 等级×0.5（%）。',
    buffEnhancingSpeed:'强化速度', buffEnhancingSpeedTip:'仅对强化技能的动作速度生效；0=无，1~20 级，加成 = 19.5 + 等级×0.5（%）。',
    levelUnit:'级',
    skillLabels:['挤奶','采摘','伐木','奶酪锻造','制作','缝纫','烹饪','冲泡','炼金','强化'],
    equipLabels:['主手','副手','头部','身体','手部','腿部','脚部','项链','耳环','戒指','袋子','背部','挤奶工具','采摘工具','伐木工具','奶酪锻造工具','制作工具','缝纫工具','烹饪工具','冲泡工具','炼金工具','强化工具'],
  },
  en: {
    title:'MWI Trial Calculator', trialConfig:'Trial Config', memberData:'Member Data',
    addMember:'Add Member', share:'Share', importData:'Import', exportData:'Export',
    exportScriptTitle:'Download userscript to auto-collect guild member data as JSON',
    exportEmpty:'No member data to export',
    exportSuccess:'Exported',
    importFormatUnknown:'Unrecognized JSON: expected a calculator backup or a members profile array',
    calculate:'Calculate', assignCol:'Assign', nameCol:'Name', maxMembers:'Max',
    trialSlotsAuto:'set by Skilling Encampment', trialSlotsFromCamp:'Skilling Encampment Lv{level}: {base} + {level}×{per} = {cap}',
    noAssign:'(None)', noMembers:'No member data. Add members or import JSON.',
    totalFinalLv:'Total Final Lv', totalPasses:'Total Passes', assigned:'Assigned', unassigned:'Unassigned',
    deleteBtn:'Del', selectEquip:'Select Equipment', searchEquip:'Search equipment...',
    enhanceLevel:'Enhancement Level', clear:'Clear', cancel:'Cancel', confirm:'Confirm',
    noEquip:'No equipment selected', passes:'passes', people:'people', offlineMode:'Offline',
    connected:'Connected', guildName:'Guild Name', password:'Access Password (for encryption)',
    masterKey:'jsonbin.io Master Key (for guild leader)',
    shareHint:'After the leader creates a shared space, share the link with members. Members can view/update data without registration.',
    currentUrl:'Current Share URL', createShare:'Create Share', closeBtn:'Close',
    shareCreated:'Share space created! Copy the link to share with guild members.', linkCopied:'Link copied',
    enterPassword:'Enter access password:', fillAll:'Please fill in all fields',
    createFailed:'Creation failed, please check Master Key', addMembersFirst:'Please add member data first',
    importSuccess:'Imported successfully', importFailed:'No valid data found',
    importMergeReport:'Import complete: {upd} updated \u00b7 {add} added \u00b7 {keep} kept (already local, not in the exported data)',
    teamWork:'Team Work', nextClearNeeds:'Next clear needs', pts:'pts', perSec:'pts/s',
    trial:'Trial', language:'中/EN', theme:'☀️',
    globalBuffs:'Global Buffs',
    globalBuffsTip:'Enter your server/account community-hall global buff level: 0 = none, 1~20 = active. Bonus = 19.5 + level×0.5 (%), stored locally only.',
    guildBuildings:'Guild Buildings', guildBuildingsTip:'Aligned with the 23 in-game buildings (max 20), active only during your own guild trials. Life/combat buildings give the matching skill +2 effective levels; utility buildings do not affect trial tiers. Building levels are guild-wide and are uploaded with the shared data.',
    guildShrinePerMember:'Shrines (personal)', guildShrinePerMemberTip:'Shrines are per-member persistent data: fill them per member, they upload with the shared data. Each shrine has a Skilling and a Combat variant: the skilling buffs count toward the skilling-trial metrics (Force efficiency +0.5%/lv, Tempo action speed +0.5%/lv, Spirit essence find +2%/lv, Rarity rare find +1%/lv, Scholar wisdom +0.5%/lv); the combat buffs (Force damage +0.3%/lv, Tempo attack/cast speed +0.4%/lv, Spirit max HP/MP +1%/lv, ...) are reserved for future combat trials and are not simulated yet.',
    shrineKindSkilling:'Skilling', shrineKindCombat:'Combat',
    shrineCombatOnly:'combat trials only (not simulated yet)',
    houseRoomsCol:'House', houseRoomsTip:'House rooms are per-member persistent data: fill the level per member, they upload with the shared data. Skilling rooms (Dairy Barn/Garden/Log Shed etc., efficiency +1.5%/lv; Observatory action speed +1%/lv and enhance success +0.05%/lv) count toward the skilling-trial metrics; combat rooms (Dojo/Armory/Gym etc.) are reserved for future combat trials. Values come from the game\'s houseRoomDetailMap.',
    houseRoomsSkilling:'Skilling', houseRoomsCombat:'Combat',
    guildBuildingsUtility:'Utility', guildBuildingsLife:'Life Buildings', guildBuildingsCombat:'Combat Buildings',
    guildBuildingsShared:'Guild-wide · uploaded when shared',
    shrineAffectsTrial:'affects trial tiers', shrineNotAffectsTrial:'does not affect trial tiers',
    shrineCol:'Shrine',
    achievementsCol:'Achievements',
    memberDetail:'Member Details', detailBtn:'Details',
    memberDetailTip:'All per-member personal data — skill levels, equipment, house rooms, shrines and achievements — is edited in the detail dialog (click Details on the row) and uploads with the shared data. Items that do not affect trials are dimmed.',
    detailSkillSec:'Skill Levels', detailEquipSec:'Equipment', detailShrineSec:'Shrines', detailAchSec:'Achievements', detailHouseSec:'House rooms',
    detailShrineSkillingRow:'Skilling', detailShrineCombatRow:'Combat',
    detailSkillTip:'Skill levels are per-member persistent data: fill them per member; they upload with the shared data.',
    detailEquipTip:'Three areas: Life gear (skilling bonuses only), Life / Combat hybrid, and Combat gear / Life tools. Click a cell to set the enhancement level and ★ refinement.',
    lifeEquipSec:'Life gear',
    lifeEquipTip:'Skilling bonuses only, no combat bonus. A slot may hold several non-interchangeable items — tick what you own; each trial skill auto-picks the best owned one. Click a cell to set the enhancement level and ★ refinement.',
    lifeSingleRow:'Single',
    hybridEquipSec:'Life / Combat hybrid',
    hybridEquipTip:'Necklace / earrings / ring / pouch: one slot that can hold either kind, and you wear only one — click a cell to pick. Pouches give no trial bonus at all.',
    lifeToolsSec:'Life tools',
    lifeToolsTip:'Life tools have strict upgrades, so only the one currently in use needs recording.',
    combatEquipSec:'Combat gear',
    combatEquipTip:'One item per slot, never competing with life gear. Life items for the off hand / head / body / hands / legs / feet / back slots are ticked in Life gear above and are excluded from this picker.',
    lifeSlotLabels:{ '身体':'Top', '腿部':'Bottom', '背部':'Cape', '头部':'Head', '手部':'Hands', '脚部':'Feet', '副手':'Off Hand' },
    refineToggle:'Refined',
    unownBtn:'Remove',
    enhDone:'Done',
    achievementsTip:'Achievement tiers are per-member persistent data: tick "all achievements in this tier completed" per member; they upload with the shared data. There are 6 tiers: Beginner gathering +2%, Novice XP +2%, Adept efficiency +2%, Veteran rare find +2%, Elite damage +2%, Champion enhance success +0.2%. Beginner/Adept/Champion affect the skilling-trial metrics; Elite is a combat buff (reserved for future combat trials). Values come from the game\'s achievementTierDetailMap.',
    guildHallTip:'Raises max members', buildersHallTip:'Boosts Guild Points', treasuryTip:'Boosts Guild Tokens',
    archivesTip:'Boosts Guild Experience', skillingCampTip:'Skilling trial slots +2/lv (cap = 20 + level×2)', combatCampTip:'Combat trial slots +2/lv (combat trials not simulated yet)',
    buffGathering:'Gathering Qty', buffGatheringTip:'Applies only to gathering skills (Milking/Foraging/Woodcutting) as double-drop chance. 0=none, 1~20, bonus = 19.5 + level×0.5 (%).',
    buffProduction:'Production Eff', buffProductionTip:'Applies only to production skills (Cheesesmithing/Crafting/Tailoring/Cooking/Brewing/Alchemy) as efficiency. 0=none, 1~20, bonus = 19.5 + level×0.5 (%).',
    buffEnhancingSpeed:'Enhancing Spd', buffEnhancingSpeedTip:'Applies only to the Enhancing skill as action speed. 0=none, 1~20, bonus = 19.5 + level×0.5 (%).',
    levelUnit:'lv',
    skillLabels:['Milking','Foraging','Woodcutting','Cheesesmithing','Crafting','Tailoring','Cooking','Brewing','Alchemy','Enhancing'],
    equipLabels:['Main Hand','Off Hand','Head','Body','Hands','Legs','Feet','Necklace','Earring','Ring','Pouch','Back','Milking Tool','Foraging Tool','Woodcutting Tool','Cheesesmithing Tool','Crafting Tool','Tailoring Tool','Cooking Tool','Brewing Tool','Alchemy Tool','Enhancing Tool'],
  }
};
function t(key) { return (I18N[state.lang] && I18N[state.lang][key]) || key; }
// 文案占位符填充：tplFill(t('importMergeReport'), { upd:1, add:2, keep:3 }) —— 找不到的键原样保留 {key}
function tplFill(s, vars) {
  return String(s).replace(/\{(\w+)\}/g, function(m, k){ return (vars && vars[k] != null) ? vars[k] : m; });
}
function skillLabel(idx) { return I18N[state.lang].skillLabels[idx]; }
function equipLabel(idx) { return I18N[state.lang].equipLabels[idx]; }
// 生活装备「拥有制」槽位的显示名（上衣 / 下装 / 披风）
function lifeSlotLabel(slot) {
  const map = (I18N[state.lang] && I18N[state.lang].lifeSlotLabels) || {};
  return map[slot] || equipLabel(EQUIP_TYPES.indexOf(slot)) || slot;
}

// === Constants ===
const SKILL_KEYS = ['milking','foraging','woodcutting','cheesesmithing','crafting','tailoring','cooking','brewing','alchemy','enhancing'];
const EQUIP_TYPES = ['主手','副手','头部','身体','手部','腿部','脚部','项链','耳环','戒指','袋子','背部','挤奶工具','采摘工具','伐木工具','奶酪锻造工具','制作工具','缝纫工具','烹饪工具','冲泡工具','炼金工具','强化工具'];
const TOOL_SKILL_MAP = {'挤奶工具':'milking','采摘工具':'foraging','伐木工具':'woodcutting','奶酪锻造工具':'cheesesmithing','制作工具':'crafting','缝纫工具':'tailoring','烹饪工具':'cooking','冲泡工具':'brewing','炼金工具':'alchemy','强化工具':'enhancing'};
// 装备分三区：「生活装备」（纯生活件，勾选制）、「生活 · 战斗两用」（一槽一件，配装制）、
// 「战斗装备 + 生活工具」（一槽一件，配装制）。后两区都走同一个 openEquipPicker 选择器。
const TOOL_SLOTS = EQUIP_TYPES.filter(function(s){ return s.indexOf('工具') >= 0; });
const EQUIP_MAX_ENHANCE = 20;
const ITEM_LOCATION_TO_SLOT = {'/item_locations/main_hand':'主手','/item_locations/two_hand':'主手','/item_locations/off_hand':'副手','/item_locations/head':'头部','/item_locations/body':'身体','/item_locations/hands':'手部','/item_locations/legs':'腿部','/item_locations/feet':'脚部','/item_locations/neck':'项链','/item_locations/earrings':'耳环','/item_locations/ring':'戒指','/item_locations/pouch':'袋子','/item_locations/back':'背部','/item_locations/milking_tool':'挤奶工具','/item_locations/foraging_tool':'采摘工具','/item_locations/woodcutting_tool':'伐木工具','/item_locations/cheesesmithing_tool':'奶酪锻造工具','/item_locations/crafting_tool':'制作工具','/item_locations/tailoring_tool':'缝纫工具','/item_locations/cooking_tool':'烹饪工具','/item_locations/brewing_tool':'冲泡工具','/item_locations/alchemy_tool':'炼金工具','/item_locations/enhancing_tool':'强化工具'};
const GATHERING_SKILL_IDS = new Set(['milking','foraging','woodcutting']);
const PRODUCTION_SKILL_IDS = new Set(['cheesesmithing','crafting','tailoring','cooking','brewing','alchemy']);
// 全局 BUFF（参考 Enhancelator main.js 的 enhancing_buff）：0 = 无 buff；1~20 级启用。
// 加成% = 19.5 + 等级×0.5（与 MWI 社区大厅 buff 一致）；转小数乘数时 /100。
const GLOBAL_BUFF_BASE = 19.5;
const GLOBAL_BUFF_PER_LEVEL = 0.5;
function globalBuffPct(lv) {
  lv = Number(lv) || 0;
  return lv > 0 ? (GLOBAL_BUFF_BASE + GLOBAL_BUFF_PER_LEVEL * lv) : 0;
}
// __GAME_DATA_PLACEHOLDER__

// === 算法常量 ===
const TRIAL_DURATION = 3600, START_LV = 100, LV_PER_PASS = 10, COUNT_INFLATION = 0.01;
const BASE_ACTION_SEC = 10, SUCCESS_BASE = 0.80, SUCCESS_BELOW = 0.01, SUCCESS_ABOVE = 0.005, SUCCESS_MIN = 0.05;
const BASE_TOTAL_PT = 40000, PT_GROWTH = 4000, MAX_PASS_GUARD = 10000, NUM_TRIALS = 4;

// __EQUIP_ICONS_PLACEHOLDER__

// __LIFE_EQUIP_PLACEHOLDER__

// 战斗装备（配装制 · 一槽一件）= 全部装备槽 − 生活工具 − 两用槽（项链/耳环/戒指/袋子 有自己的分区）。
// 顺序按需求写死：主手 / 副手 / 头部 / 身体 / 腿部 / 手部 / 脚部 / 背部（腿部与手部相对 EQUIP_TYPES 互换）。
const COMBAT_EQUIP_SLOTS = ['主手','副手','头部','身体','腿部','手部','脚部','背部'];

// === State ===
// 说明：神龛等级是「个人属性」，直接挂在每个成员身上（member.shrines），不再有全局输入。
//      公会建筑等级是「公会全局」，放在 state.guildBuildings，随共享数据一起上传。
let state = {
  lang: 'zh',
  theme: 'light',
  guild: '',
  members: [],
  trials: [{skill:0,max:20},{skill:1,max:20},{skill:2,max:20},{skill:3,max:20}],
  assignment: null,
  result: null,
  binId: null,
  encKey: null,
  isShared: false,
  deletedIds: [],
  globalBuffs: { gathering: 0, production: 0, enhancingSpeed: 0 },
  guildBuildings: (typeof GUILD_BUILDING_ALL_KEYS !== 'undefined' ? GUILD_BUILDING_ALL_KEYS : GUILD_BUILDING_KEYS).reduce((o,k)=>(o[k]=0,o),{}),
  guildBuildingsTs: 0
};
let pickerState = { memberId:null, slot:null, iconId:null, enhance:0 };

// === Algorithm ===

function getEnhancementBonusPercent(enhLevel, slot) {
  const lv = Math.max(0, Math.floor(Number(enhLevel) || 0));
  const clamped = lv > ENH_BONUS_PERCENT_TABLE.length - 1
    ? ENH_BONUS_PERCENT_TABLE[ENH_BONUS_PERCENT_TABLE.length - 1]
    : ENH_BONUS_PERCENT_TABLE[lv];
  return ACCESSORY_ENH_SLOTS.has(String(slot)) ? clamped * 5 : clamped;
}

// 单件装备的原始加成（statKey → 数值）。与旧逻辑等价，只是把「逐件算」和「并入某技能」拆开：
// 1) 命中固定基础加成表 → 按真实装备身份精确算（0 级基础值 × 强化系数 × 物品倍率）
// 2) 未命中 → 先试生活工具 前缀_后缀 精确加成
// 3) 仍未命中 → 按槽位类型的近似公式（工具给单技能、防具给全技能微加成）
function itemStatTotals(slot, iconId, enhance) {
  const totals = {};
  const L = Number(enhance) || 0;
  const idStr = String(iconId || '');
  const effectiveName = idStr.endsWith('_refined') ? idStr.slice(0, -'_refined'.length) : idStr;
  const cfg = idStr ? EQUIPMENT_BASE_BONUSES['/items/' + effectiveName] : null;
  const isBack = (slot === '背部');
  // 精炼（★）倍率：官方 2025/8/20 调整 —— 精炼装备 +8%，背部（披风）装备 +16%；
  // 未精炼装备没有任何倍率加成（此前误把 ×1.16 也套在非精炼披风上）。
  const itemMult = idStr.endsWith('_refined') ? (isBack ? 1.16 : 1.08) : 1;
  if (cfg && cfg.base) {
    const enhPct = getEnhancementBonusPercent(L, slot);
    for (const [k, baseVal] of Object.entries(cfg.base)) {
      const v = Number(baseVal) * (1 + enhPct) * itemMult;
      if (!Number.isFinite(v) || v === 0) continue;
      totals[k] = (totals[k] || 0) + v;
    }
    return totals;
  }
  const toolRaw = idStr.replace('/items/', '');
  const toolRefined = toolRaw.endsWith('_refined');
  const toolName = toolRefined ? toolRaw.slice(0, -'_refined'.length) : toolRaw;
  const uidx = toolName.lastIndexOf('_');
  if (uidx > 0) {
    const prefix = toolName.slice(0, uidx);
    const suffix = toolName.slice(uidx + 1);
    const basePct = suffix === 'enhancer' ? (ENHANCER_PREFIX_BONUS[prefix]||0) : (TOOL_PREFIX_BONUS[prefix]||0);
    const statKey = TOOL_SUFFIX_SKILL[suffix];
    if (basePct && statKey) {
      const enhPct = getEnhancementBonusPercent(L, slot);
      totals[statKey] = (totals[statKey] || 0) + basePct * (1 + enhPct) * itemMult;
      return totals;
    }
  }
  const skill = TOOL_SKILL_MAP[slot];
  if (skill) {
    totals[skill+'Speed'] = L*0.025;
    totals[skill+'Efficiency'] = L*0.015;
    totals[skill+'Success'] = L*0.005;
    totals[skill+'Gathering'] = L*0.01;
    totals[skill+'Level'] = L*0.5;
  } else {
    // 袋子（pouch）在游戏里只提供食物 / 饮料槽位与生命 / 法力上限，对生活技能没有任何加成 —— 直接返回空。
    if (slot === '袋子') return totals;
    totals['skillingSpeed'] = L*0.002;
    totals['skillingEfficiency'] = L*0.001;
    totals['skillingLevel'] = L*0.1;
  }
  return totals;
}

// 把单件装备的加成并入「某一个技能」的加成结构（等价于旧 applyEquipStatTotals 里对该技能的那部分）
function foldStatTotalsForSkill(out, totals, skillId) {
  for (const k in totals) {
    const v = totals[k];
    if (!Number.isFinite(v) || v === 0) continue;
    if (k === 'skillingSpeed') { out.speedBonus += v; continue; }
    if (k === 'skillingEfficiency') { out.efficiencyBonus += v; continue; }
    if (k === 'skillingLevel') { out.skillLevelBonus += v; continue; }
    if (k === 'gatheringQuantity') { if (GATHERING_SKILL_IDS.has(skillId)) out.gatheringBonus += v; continue; }
    if (k.indexOf(skillId) !== 0) continue;   // {skillId}Speed / Efficiency / Success / Level / Gathering
    const suffix = k.slice(skillId.length);
    if (suffix === 'Speed') out.speedBonus += v;
    else if (suffix === 'Efficiency') out.efficiencyBonus += v;
    else if (suffix === 'Success') out.successBonus += v;
    else if (suffix === 'Level') out.skillLevelBonus += v;
    else if (suffix === 'Gathering') out.gatheringBonus += v;
  }
}
function foldItemForSkill(out, slot, iconId, enhance, skillId) {
  foldStatTotalsForSkill(out, itemStatTotals(slot, iconId, enhance), skillId);
}
function emptySkillBonus() { return {speedBonus:0,efficiencyBonus:0,successBonus:0,gatheringBonus:0,skillLevelBonus:0}; }
function cloneSkillBonus(b) { return {speedBonus:b.speedBonus,efficiencyBonus:b.efficiencyBonus,successBonus:b.successBonus,gatheringBonus:b.gatheringBonus,skillLevelBonus:b.skillLevelBonus}; }

// 装备择优用的标量：按该技能的实际产出速度比较（与推演同口径：等级 × 效率 × 采集 / 动作时间 × 成功率）
function equipChoiceScore(b, baseLevel) {
  const effLevel = Math.max(0, baseLevel + (b.skillLevelBonus||0));
  const actionSeconds = BASE_ACTION_SEC / Math.max(0.05, 1+(b.speedBonus||0));
  if (!(actionSeconds > 0)) return 0;
  const workP = Math.max(0, Math.floor(effLevel * (1+(b.efficiencyBonus||0))));
  const dblP = Math.max(0, Math.min(1, b.gatheringBonus||0));
  return (workP*(1+dblP))/actionSeconds * successRate(effLevel, START_LV, b.successBonus||0);
}

// === 装备「拥有制」槽位 ===
// OWNED_SLOTS 里的每个槽位都以「拥有集合」记录：person.ownedEquip[slot][iconId] = 强化等级。
// iconId 可以是家族的基础款，也可以是基础款 + '_refined'（★ 精炼款）；同一家族两者互斥（只能穿一件）。
// 推演时按「当前试炼技能」自动取该槽位收益最高的一件（同一槽位只能穿一件 → 是择优而不是累加）。
function ownedEquipOf(person, slot) {
  const o = person && person.ownedEquip && person.ownedEquip[slot];
  return (o && typeof o === 'object') ? o : null;
}
function clampEnhance(v) { return Math.max(0, Math.min(EQUIP_MAX_ENHANCE, Math.floor(Number(v) || 0))); }
function isOwnedSlot(slot) {
  return (typeof OWNED_SLOTS !== 'undefined') && OWNED_SLOTS.indexOf(slot) >= 0;
}
// 该槽位可勾选的装备家族（生活槽位只列生活件；两用槽位整槽列出）
function equipFamilies(slot) {
  return (typeof EQUIP_FAMILIES !== 'undefined' && EQUIP_FAMILIES[slot]) ? EQUIP_FAMILIES[slot] : [];
}
function familyOf(slot, baseId) {
  const fams = equipFamilies(slot);
  for (let i = 0; i < fams.length; i++) if (fams[i].id === baseId) return fams[i];
  return null;
}
function iconBaseId(iconId) {
  const s = String(iconId || '');
  return s.endsWith('_refined') ? s.slice(0, -'_refined'.length) : s;
}
function isOwnedFamily(slot, iconId) {
  const base = iconBaseId(iconId);
  const fams = equipFamilies(slot);
  for (let i = 0; i < fams.length; i++) if (fams[i].id === base) return true;
  return false;
}
// 家族显示名（英文界面回落到 iconId）
function familyName(baseId, zhName) {
  if (state.lang !== 'en' && zhName) return zhName;
  return String(baseId).replace(/_/g, ' ');
}
// 读取某家族当前的拥有状态：{enh, refined} 或 null
function ownedEntry(person, slot, baseId) {
  const owned = ownedEquipOf(person, slot);
  if (!owned) return null;
  if (owned[baseId] != null) return { enh: clampEnhance(owned[baseId]), refined: false };
  const rk = baseId + '_refined';
  if (owned[rk] != null) return { enh: clampEnhance(owned[rk]), refined: true };
  return null;
}
// 写入某家族（先清掉同家族的另一个键 → 普通款 / 精炼款互斥）
function setOwnedEntry(person, slot, baseId, enh, refined) {
  if (!person.ownedEquip || typeof person.ownedEquip !== 'object') person.ownedEquip = {};
  if (!person.ownedEquip[slot] || typeof person.ownedEquip[slot] !== 'object') person.ownedEquip[slot] = {};
  const owned = person.ownedEquip[slot];
  const rk = baseId + '_refined';
  delete owned[baseId];
  delete owned[rk];
  owned[refined ? rk : baseId] = clampEnhance(enh);
  person._ts = Date.now();
}
function clearOwnedEntry(person, slot, baseId) {
  const owned = ownedEquipOf(person, slot);
  if (!owned) return;
  delete owned[baseId];
  delete owned[baseId + '_refined'];
  person._ts = Date.now();
}
// 该槽位里「对这个技能收益最高」的一件（不含 cur 之外的其它槽位加成，用于同槽位横向比较）
function bestOwnedForSkill(person, slot, skillId, baseLevel, cur) {
  const owned = ownedEquipOf(person, slot);
  if (!owned) return null;
  let best = null, bestScore = -1;
  for (const iconId in owned) {
    if (!isOwnedFamily(slot, iconId)) continue;
    const enh = clampEnhance(owned[iconId]);
    const cand = cloneSkillBonus(cur);
    foldItemForSkill(cand, slot, iconId, enh, skillId);
    const sc = equipChoiceScore(cand, baseLevel);
    if (sc > bestScore) { bestScore = sc; best = { iconId: iconId, enhance: enh }; }
  }
  return best;
}
// 单个技能下的装备总加成：拥有制槽位（按该技能择优）+ 配装槽（一槽一件）
function computeBonusForSkill(person, skillId, baseLevel) {
  const out = emptySkillBonus();
  if (!person) return out;
  for (const slot of EQUIP_TYPES) {
    if (isOwnedSlot(slot)) {
      const best = bestOwnedForSkill(person, slot, skillId, baseLevel, out);
      if (best) { foldItemForSkill(out, slot, best.iconId, best.enhance, skillId); continue; }
      // 拥有集合为空 → 回落到配装槽（兼容旧数据：原来按「一槽一件」登记在这里）
    }
    const eq = person.equipment && person.equipment[slot];
    if (!eq) continue;
    if (!eq.iconId && !(eq.enhance > 0)) continue;
    foldItemForSkill(out, slot, eq.iconId, eq.enhance, skillId);
  }
  return out;
}
// 旧数据迁移（幂等）：
// ① 勾选制槽位（身体/腿部/背部/头部/手部/脚部/副手）原来按「一槽一件」记在 equipment 里 →
//    属于该槽位家族（生活件）的搬进 ownedEquip；战斗件（战斗护甲 / 头盔 / 战斗披风 等）留在配装槽。
// ② 两用槽（项链/耳环/戒指/袋子）v6.6 曾按「整槽勾选」记进 ownedEquip → 现在改回「一槽一件」的配装制，
//    取其中强化最高的一件搬回 equipment，然后清掉该槽的 ownedEquip。
function normalizeMemberEquip(p) {
  if (!p) return p;
  if (!p.ownedEquip || typeof p.ownedEquip !== 'object') p.ownedEquip = {};
  if (!p.equipment || typeof p.equipment !== 'object') p.equipment = {};
  for (const slot of OWNED_SLOTS) {
    if (!p.ownedEquip[slot] || typeof p.ownedEquip[slot] !== 'object') p.ownedEquip[slot] = {};
    const owned = p.ownedEquip[slot];
    const old = p.equipment[slot];
    if (old && old.iconId && isOwnedFamily(slot, old.iconId) && owned[old.iconId] == null) {
      owned[old.iconId] = clampEnhance(old.enhance);
      delete p.equipment[slot];
    }
    for (const k of Object.keys(owned)) {
      if (!isOwnedFamily(slot, k)) { delete owned[k]; continue; }   // 剔除非本槽位家族的脏键
      owned[k] = clampEnhance(owned[k]);
      if (k.endsWith('_refined')) {                                  // 普通款与精炼款同时存在 → 保留精炼款
        const base = k.slice(0, -'_refined'.length);
        if (owned[base] != null) delete owned[base];
      }
    }
  }
  for (const slot of HYBRID_SLOTS) {
    const owned = ownedEquipOf(p, slot);
    if (owned) {
      let bestKey = null, bestEnh = -1;
      for (const k of Object.keys(owned)) {
        const e = clampEnhance(owned[k]);
        if (e > bestEnh) { bestEnh = e; bestKey = k; }
      }
      const cur = p.equipment[slot];
      if (bestKey && !(cur && cur.iconId)) {
        p.equipment[slot] = { iconId: bestKey, enhance: bestEnh };
        p._ts = Date.now();
      }
    }
    delete p.ownedEquip[slot];
  }
  return p;
}

// === 成就 / 房屋 / 公会 加成（迁移自 Chen19970809/MWI_Trial_Calculator）===
// 读取单个 buff 对象的数值，兼容多种字段名。
function readBuffAmount(b) {
  const keys = ['ratioBoost','flatBoost','value','amount','bonus','boost','boostRatio','ratioBoostLevelBonus','flatBoostLevelBonus','levelBonus'];
  let sum = 0;
  for (const k of keys) {
    const v = b[k];
    if (typeof v === 'number' && Number.isFinite(v)) sum += v;
    else if (typeof v === 'string') { const n = Number(v); if (!Number.isNaN(n)) sum += n; }
  }
  return sum;
}

// 累加 actionTypeBuffsDict 中 /action_types/<skillId> 的全部 buff（Trial Core 口径）。
function accumulateActionTypeBuffs(dict, skillId) {
  const out = { speedBonus:0, efficiencyBonus:0, successBonus:0, gatheringBonus:0, skillLevelBonus:0 };
  if (!dict || typeof dict !== 'object') return out;
  const actionTypeHrid = '/action_types/' + skillId;
  const buffs = dict[actionTypeHrid] || dict[skillId];
  if (!Array.isArray(buffs)) return out;
  const isGathering = GATHERING_SKILL_IDS.has(skillId);
  const skillLevelType = '/buff_types/' + skillId + '_level';
  const skillSuccessType = '/buff_types/' + skillId + '_success';
  for (const b of buffs) {
    if (!b || typeof b !== 'object') continue;
    const amt = readBuffAmount(b);
    if (amt === 0) continue;
    const t = b.typeHrid || b.type || b.buffTypeHrid || b.buffType || '';
    if      (t === skillLevelType || t === '/buff_types/skill_level') out.skillLevelBonus += amt;
    else if (t === '/buff_types/efficiency') out.efficiencyBonus += amt;
    else if (t === '/buff_types/action_speed' || t === '/buff_types/speed') out.speedBonus += amt;
    else if (t === skillSuccessType || t === '/buff_types/success_rate') out.successBonus += amt;
    else if (t === '/buff_types/gathering' && isGathering) out.gatheringBonus += amt;
    else if (t === '/buff_types/gourmet' && PRODUCTION_SKILL_IDS.has(skillId)) out.gatheringBonus += amt;
  }
  return out;
}

// 成就档完成状态 → 某技能的档位 BUFF。完整 6 档（初学者/新手/熟练者/老手/精英/冠军），
// 数值与「作用技能」取自游戏 achievementTierDetailMap，且该档全部成就完成才触发。
// 战斗向增益（精英=伤害+2%）写入 damageBonus 等字段，供后续战斗试炼取用（当前生活推演不使用）。
function applyAchievementTierBuffs(out, achievementsValue, actionTypeHrid) {
  if (!achievementsValue || typeof achievementsValue !== 'object' || Array.isArray(achievementsValue)) return;
  const tierDetailMap = EMBEDDED_CLIENT_DATA && EMBEDDED_CLIENT_DATA.achievementTierDetailMap;
  if (!tierDetailMap) return;
  const skillId = actionTypeHrid ? actionTypeHrid.replace('/action_types/', '') : null;
  for (const tier of achievementTiersList()) {
    if (achievementsValue[tier.hrid] !== true) continue;
    const detail = tierDetailMap[tier.hrid];
    if (!detail || !detail.buff) continue;
    if (detail.usableInActionTypeMap && !detail.usableInActionTypeMap[actionTypeHrid]) continue;
    const b = detail.buff;
    const type = String(b.typeHrid || '').replace('/buff_types/', '');
    addBonusByType(out, type, readBuffAmount(b), skillId);
  }
}

// 把原始 achievements 布尔表压缩成 6 档完成状态 {tierHrid: bool}。
function computeAchievementsValue(achievements) {
  if (!achievements || typeof achievements !== 'object' || Array.isArray(achievements)) return null;
  const detailMap = EMBEDDED_CLIENT_DATA && EMBEDDED_CLIENT_DATA.achievementDetailMap;
  if (!detailMap) return null;
  const val = {}; let any = false;
  for (const tier of achievementTiersList()) {
    const tierHrid = tier.hrid;
    let total = 0, done = 0;
    for (const [achHrid, achDetail] of Object.entries(detailMap)) {
      if (!achDetail || achDetail.tierHrid !== tierHrid) continue;
      total++;
      if (achievements[achHrid] === true) done++;
    }
    if (total === 0) continue;
    val[tierHrid] = (done === total); any = true;
  }
  return any ? val : null;
}

// 把导出的成就信息统一成 {achievementHrid: bool} 布尔表。
// 共享资料里可能是数组形式（characterAchievements: [{achievementHrid, isCompleted, ...}]），
// 也可能是对象/Map 形式（{achHrid: true}）或包一层 data。
function normalizeAchievementsMap(raw) {
  if (!raw) return null;
  if (Array.isArray(raw)) {
    const m = {};
    for (const a of raw) {
      if (!a || typeof a !== 'object') continue;
      const hrid = a.achievementHrid || a.hrid;
      if (!hrid) continue;
      m[hrid] = (a.isCompleted !== false && a.isCompleted !== 0 && a.isCompleted !== undefined);
    }
    return m;
  }
  if (typeof raw === 'object') {
    if (raw.data && typeof raw.data === 'object' && !Array.isArray(raw.data)) return raw.data;
    return raw;
  }
  return null;
}

// 从 person.achievementsValue / achievementActionTypeBuffsDict / achievements 提取成就对某技能的加成。
// v6.1 起：成员级可编辑的成就档位（person.achievements，个人持久化数据）优先于导入时的原始 profile 字段。
function extractAchievementBonuses(person, skillId) {
  const out = { speedBonus:0, efficiencyBonus:0, successBonus:0, gatheringBonus:0, skillLevelBonus:0 };
  if (!person) return out;
  const actionTypeHrid = '/action_types/' + skillId;
  const memberVal = memberAchievementValue(person);
  if (memberVal) {
    applyAchievementTierBuffs(out, memberVal, actionTypeHrid);
    // 勾选值为权威：全空且 profile 也没带显式 buff 字典时即可返回
    if (Object.keys(memberVal).length > 0 || !person.achievementActionTypeBuffsDict) return out;
  }
  if (person.achievementsValue) {
    applyAchievementTierBuffs(out, person.achievementsValue, actionTypeHrid);
    return out;
  }
  if (person.achievementActionTypeBuffsDict && typeof person.achievementActionTypeBuffsDict === 'object' && !Array.isArray(person.achievementActionTypeBuffsDict)) {
    const buffs = person.achievementActionTypeBuffsDict[actionTypeHrid] || person.achievementActionTypeBuffsDict[skillId];
    if (Array.isArray(buffs)) {
      for (const b of buffs) {
        if (!b || typeof b !== 'object') continue;
        const amt = readBuffAmount(b);
        if (amt === 0) continue;
        const t = b.typeHrid || b.type || b.buffTypeHrid || b.buffType || '';
        if      (t === '/buff_types/skill_level' || t.endsWith('_level')) out.skillLevelBonus += amt;
        else if (t === '/buff_types/efficiency') out.efficiencyBonus += amt;
        else if (t === '/buff_types/action_speed' || t === '/buff_types/speed') out.speedBonus += amt;
        else if (t === '/buff_types/success_rate') out.successBonus += amt;
        else if (t === '/buff_types/gathering') out.gatheringBonus += amt;
      }
      return out;
    }
  }
  const rawAch = normalizeAchievementsMap(person.achievements || person.characterAchievements);
  if (EMBEDDED_CLIENT_DATA && EMBEDDED_CLIENT_DATA.achievementDetailMap && EMBEDDED_CLIENT_DATA.achievementTierDetailMap && rawAch) {
    applyAchievementTierBuffs(out, computeAchievementsValue(rawAch), actionTypeHrid);
    return out;
  }
  let dict = rawAch;
  if (dict && typeof dict === 'object' && !Array.isArray(dict)) {
    dict = dict.achievementActionTypeBuffsDict || dict.actionTypeBuffsDict || dict;
  }
  if (!dict || typeof dict !== 'object' || Array.isArray(dict)) return out;
  let buffs = dict[actionTypeHrid];
  if (!buffs) buffs = dict[skillId];
  if (!Array.isArray(buffs)) return out;
  const isGathering = GATHERING_SKILL_IDS.has(skillId);
  const skillLevelType = '/buff_types/' + skillId + '_level';
  const skillSuccessType = '/buff_types/' + skillId + '_success';
  for (const b of buffs) {
    if (!b || typeof b !== 'object') continue;
    const amt = readBuffAmount(b);
    if (amt === 0) continue;
    const t = b.typeHrid || b.type || b.buffTypeHrid || b.buffType || '';
    if      (t === skillLevelType || t === '/buff_types/skill_level') out.skillLevelBonus += amt;
    else if (t === '/buff_types/efficiency') out.efficiencyBonus += amt;
    else if (t === '/buff_types/action_speed' || t === '/buff_types/speed') out.speedBonus += amt;
    else if (t === skillSuccessType || t === '/buff_types/success_rate') out.successBonus += amt;
    else if (t === '/buff_types/gathering' && isGathering) out.gatheringBonus += amt;
  }
  return out;
}

// 计算单个房屋 buff 在当前等级下的数值 = level × flatBoostLevelBonus。
function computeBuffAtLevel(b, level) {
  if (level <= 0) return 0;
  return level * (Number(b.flatBoostLevelBonus) || 0);
}

// === 房屋房间（17 个：10 生活 + 7 战斗，成员级个人持久化数据）===
function houseRoomDefsList() {
  return (typeof HOUSE_ROOM_DEFS !== 'undefined' && HOUSE_ROOM_DEFS.length) ? HOUSE_ROOM_DEFS : [];
}
function houseRoomDef(key) {
  for (const d of houseRoomDefsList()) if (d.key === key) return d;
  return null;
}
// 读取成员某个房屋房间的等级：member.houseRooms（可直接编辑/上传）优先，
// 兼容导入 profile 的 characterHouseRoomMap / houseRoomLevels。
function houseRoomLevel(person, key) {
  if (!person) return 0;
  const cap = (typeof HOUSE_ROOM_MAX_LEVEL !== 'undefined') ? HOUSE_ROOM_MAX_LEVEL : 20;
  const clamp = (v) => Math.max(0, Math.min(cap, Math.floor(Number(v) || 0)));
  const edited = person.houseRooms && person.houseRooms[key];
  if (edited != null && edited !== '') return clamp(edited);
  const legacy = person.characterHouseRoomMap || person.houseRoomLevels;
  if (legacy && typeof legacy === 'object') {
    const raw = (legacy['/house_rooms/' + key] != null) ? legacy['/house_rooms/' + key] : legacy[key];
    if (typeof raw === 'number') return clamp(raw);
    if (raw && typeof raw === 'object') {
      const lv = (raw.level != null) ? raw.level : ((raw.roomLevel != null) ? raw.roomLevel : raw.houseRoomLevel);
      if (lv != null) return clamp(lv);
    }
  }
  return 0;
}
// 导入 profile 的房屋等级 → 成员可编辑的 houseRooms（个人持久化数据）
function materializeMemberHouseRooms(profile) {
  const out = {};
  for (const d of houseRoomDefsList()) out[d.key] = 0;
  if (!profile) return out;
  const src = { characterHouseRoomMap: profile.characterHouseRoomMap, houseRoomLevels: profile.houseRoomLevels };
  for (const d of houseRoomDefsList()) out[d.key] = houseRoomLevel(src, d.key);
  return out;
}
// 从 member.houseRooms 计算房屋加成（生活房间计入试炼推演；战斗房间由 computeCombatBonuses 聚合）。
// 兼容旧的 houseActionTypeBuffsDict / houseRoomLevels 字段。
function extractHouseBuffBonuses(person, skillId) {
  const out = { speedBonus:0, efficiencyBonus:0, successBonus:0, gatheringBonus:0, skillLevelBonus:0 };
  if (!person) return out;
  // 1) 成员级可编辑的 houseRooms（权威值）
  if (person.houseRooms && typeof person.houseRooms === 'object') {
    for (const d of houseRoomDefsList()) {
      if (!d.affectsTrial) continue;
      if (d.skill && d.skill !== skillId) continue;
      const lv = houseRoomLevel(person, d.key);
      if (lv <= 0) continue;
      for (const b of (d.actionBuffs || [])) addBonusByType(out, b.type, lv * (Number(b.perLevel) || 0), skillId);
    }
    return out;
  }
  if (person.houseActionTypeBuffsDict && Object.keys(person.houseActionTypeBuffsDict).length > 0) {
    return accumulateActionTypeBuffs(person.houseActionTypeBuffsDict, skillId);
  }
  if (EMBEDDED_CLIENT_DATA && EMBEDDED_CLIENT_DATA.houseRoomDetailMap && person.houseRoomLevels) {
    const actionTypeHrid = '/action_types/' + skillId;
    for (const [roomHrid, lv] of Object.entries(person.houseRoomLevels)) {
      if (typeof lv !== 'number' || lv <= 0) continue;
      const room = EMBEDDED_CLIENT_DATA.houseRoomDetailMap[roomHrid];
      if (!room) continue;
      for (const b of (room.actionBuffs || [])) {
        let applies = b.usableInActionTypeMap && b.usableInActionTypeMap[actionTypeHrid];
        if (!b.usableInActionTypeMap) applies = HOUSE_ROOM_SKILL_MAP[roomHrid] === actionTypeHrid;
        if (!applies) continue;
        const amt = computeBuffAtLevel(b, lv);
        const t = b.typeHrid;
        if      (t === '/buff_types/efficiency') out.efficiencyBonus += amt;
        else if (t === '/buff_types/action_speed' || t === '/buff_types/speed') out.speedBonus += amt;
        else if (t === '/buff_types/success_rate') out.successBonus += amt;
        else if (t === '/buff_types/gathering') out.gatheringBonus += amt;
        else if (t.endsWith('_level')) out.skillLevelBonus += amt;
      }
    }
    return out;
  }
  if (!person.houseRoomLevels) return out;
  const room = person.houseRoomLevels[skillId]
    || person.houseRoomLevels['/house_rooms/' + skillId + '_room']
    || person.houseRoomLevels['/house_rooms/' + skillId]
    || person.houseRoomLevels[skillId + '_room']
    || person.houseRoomLevels[skillId + 'Room'];
  if (!room) return out;
  if (typeof room === 'object') {
    const direct = {
      speedBonus: Number(room.speedBonus) || 0, efficiencyBonus: Number(room.efficiencyBonus) || 0,
      successBonus: Number(room.successBonus) || 0, gatheringBonus: Number(room.gatheringBonus) || 0, skillLevelBonus: Number(room.skillLevelBonus) || 0,
    };
    if (direct.speedBonus || direct.efficiencyBonus || direct.successBonus || direct.gatheringBonus || direct.skillLevelBonus) return direct;
  }
  let lv = 0;
  if (typeof room === 'number') lv = room;
  else if (typeof room === 'object') {
    if (typeof room.level === 'number') lv = room.level;
    else if (typeof room.roomLevel === 'number') lv = room.roomLevel;
    else if (typeof room.houseRoomLevel === 'number') lv = room.houseRoomLevel;
  }
  if (lv <= 0) return out;
  out.speedBonus = lv * HOUSE_BONUS_PER_LEVEL.speed;
  out.efficiencyBonus = lv * HOUSE_BONUS_PER_LEVEL.efficiency;
  out.successBonus = lv * HOUSE_BONUS_PER_LEVEL.success;
  out.gatheringBonus = lv * HOUSE_BONUS_PER_LEVEL.gathering;
  out.skillLevelBonus = lv * HOUSE_BONUS_PER_LEVEL.skillLevel;
  return out;
}

// 公会建筑（公会全局）：生活类/战斗类建筑每级 +GUILD_BUILDING_SKILL_PER_LEVEL 有效等级（仅在本公会试炼期间生效）。
// 6 座功能建筑（成员上限/点数/代币/经验/报名名额）不影响试炼层数。
function applyGuildBuilding(combined, skillId) {
  const out = { skillLevelBonus:0 };
  const buildings = state.guildBuildings || {};
  const lv = Math.max(0, Math.min(GUILD_BUILDING_MAX_LEVEL, Math.floor(Number(buildings[skillId]) || 0)));
  if (lv > 0) { const amt = lv * GUILD_BUILDING_SKILL_PER_LEVEL; combined.skillLevelBonus += amt; out.skillLevelBonus = amt; }
  return out;
}
// 生活试炼人数上限（对齐游戏客户端 partyCapForKind）：cap = 基准 20 + min(生活营地等级, 上限) × 每级人数 2。
function skillingTrialCap() {
  const lv = Math.max(0, Math.min(GUILD_BUILDING_MAX_LEVEL, Math.floor(Number((state.guildBuildings||{}).skilling_encampment) || 0)));
  return GUILD_BUILDING_SKILLING_BASE_CAP + lv * GUILD_BUILDING_SKILLING_SLOTS_PER_LEVEL;
}
// 战斗试炼人数上限：cap = 基准 40 + min(战斗营地等级, 上限) × 每级人数 2（暂未模拟战斗试炼）。
function combatTrialCap() {
  const lv = Math.max(0, Math.min(GUILD_BUILDING_MAX_LEVEL, Math.floor(Number((state.guildBuildings||{}).combat_encampment) || 0)));
  return GUILD_BUILDING_COMBAT_BASE_CAP + lv * GUILD_BUILDING_COMBAT_SLOTS_PER_LEVEL;
}
// 把派生的报名人数上限写回 trials（所有试炼槽位都是生活技能），保证算法用的是最新上限。
function applyTrialCaps() {
  if (!Array.isArray(state.trials)) return;
  const cap = skillingTrialCap();
  for (const cfg of state.trials) { cfg.max = cap; }
}
// === 个人神龛（5 座 × 生活/战斗 = 10 个槽位，成员级个人持久化数据）===
// 生活变体计入生活试炼推演（仅 力量=效率、节奏=动作速度）；
// 战斗变体为后续战斗试炼预留，不并入 combined（由 computeCombatBonuses 聚合）。
function shrineSlotsList() {
  if (typeof GUILD_SHRINE_SLOTS !== 'undefined' && GUILD_SHRINE_SLOTS.length) return GUILD_SHRINE_SLOTS;
  const out = [];
  for (const d of shrineDefsList()) {
    for (const v of (d.variants || [])) out.push(Object.assign({ shrine:d.key, icon:d.icon }, v));
  }
  return out;
}
function shrineSlotDef(slot) {
  for (const s of shrineSlotsList()) if (s.slot === slot) return s;
  return null;
}
// 读取成员某个神龛槽位的等级（slot = <shrine>_skilling / <shrine>_combat）：
// member.shrines（可直接编辑/上传）优先；再兼容旧 <shrine> 单键与导入的 guildBuffLevelMap。
function memberShrineLevel(person, slot) {
  if (!person) return 0;
  const shrines = person.shrines;
  if (shrines && typeof shrines === 'object') {
    const v = shrines[slot];
    if (v != null && v !== '') return Math.max(0, Math.floor(Number(v) || 0));
    if (slot.slice(-9) === '_skilling') {   // v6.1 及更早：生活档位存成 <shrine> 单键
      const legacy = shrines[slot.slice(0, -9)];
      if (legacy != null && legacy !== '') return Math.max(0, Math.floor(Number(legacy) || 0));
    }
  }
  const map = person.guildBuffLevels;
  if (map && typeof map === 'object') {
    const def = shrineSlotDef(slot);
    const needles = [];
    if (def && def.buffHrid) needles.push(def.buffHrid);
    needles.push('/guild_buffs/' + slot, slot);
    for (const key of needles) {
      if (map[key] != null) return Math.max(0, Math.floor(Number(map[key]) || 0));
      if (map['/' + key] != null) return Math.max(0, Math.floor(Number(map['/' + key]) || 0));
    }
  }
  return 0;
}
// 生活试炼推演用：只应用「影响试炼」的神龛变体（力量=效率 +0.5%/级、节奏=动作速度 +0.5%/级）。
function applyGuildShrine(combined, person) {
  const out = { speedBonus:0, efficiencyBonus:0, successBonus:0, gatheringBonus:0, skillLevelBonus:0, damageBonus:0 };
  for (const s of shrineSlotsList()) {
    if (!s.affectsTrial) continue;
    const lv = Math.max(0, Math.min(GUILD_SHRINE_MAX_LEVEL, memberShrineLevel(person, s.slot)));
    if (lv <= 0) continue;
    for (const b of (s.buffs || [])) addBonusByType(out, b.type, lv * (Number(b.perLevel) || 0), null);
  }
  combined.speedBonus = (combined.speedBonus||0) + out.speedBonus;
  combined.efficiencyBonus = (combined.efficiencyBonus||0) + out.efficiencyBonus;
  combined.successBonus = (combined.successBonus||0) + out.successBonus;
  combined.gatheringBonus = (combined.gatheringBonus||0) + out.gatheringBonus;
  combined.skillLevelBonus = (combined.skillLevelBonus||0) + out.skillLevelBonus;
  return out;
}
// 战斗向加成聚合（战斗试炼暂未模拟）：把「战斗神龛 + 战斗房屋房间 + 战斗类公会建筑 + 精英成就」的
// 伤害/攻速/施法速度/生命·法力上限等先算出来，供后续战斗试炼直接取用。
function computeCombatBonuses(person) {
  const out = { damageBonus:0, attackSpeedBonus:0, castSpeedBonus:0, maxHpBonus:0, maxMpBonus:0, rareFindBonus:0, skillLevelBonus:0 };
  for (const s of shrineSlotsList()) {
    if (!s.affectsCombat) continue;
    const lv = Math.max(0, Math.min(GUILD_SHRINE_MAX_LEVEL, memberShrineLevel(person, s.slot)));
    if (lv <= 0) continue;
    for (const b of (s.buffs || [])) addBonusByType(out, b.type, lv * (Number(b.perLevel) || 0), null);
  }
  for (const d of houseRoomDefsList()) {
    if (!d.affectsCombat) continue;
    const lv = houseRoomLevel(person, d.key);
    if (lv <= 0) continue;
    for (const b of (d.actionBuffs || [])) addBonusByType(out, b.type, lv * (Number(b.perLevel) || 0), null);
  }
  for (const tier of achievementTiersList()) {
    if (!tier.affectsCombat || !memberAchievementDone(person, tier.key)) continue;
    for (const b of (tier.buffs || [])) addBonusByType(out, b.type, Number(b.perLevel) || 0, null);
  }
  const buildings = state.guildBuildings || {};
  const combatKeys = (typeof GUILD_BUILDING_COMBAT_KEYS !== 'undefined') ? GUILD_BUILDING_COMBAT_KEYS : [];
  for (const k of combatKeys) {
    const lv = Math.max(0, Math.min(GUILD_BUILDING_MAX_LEVEL, Math.floor(Number(buildings[k]) || 0)));
    if (lv > 0) out.skillLevelBonus += lv * GUILD_BUILDING_SKILL_PER_LEVEL;
  }
  return out;
}

// 把 state.globalBuffs 的等级换算成加成，叠到 combined 上。仅对相应技能分类生效。
function addGlobalBuffsToCombined(combined, skillId) {
  const gb = state.globalBuffs || {};
  if (GATHERING_SKILL_IDS.has(skillId)) {
    combined.gatheringBonus += globalBuffPct(gb.gathering) / 100;
  }
  if (PRODUCTION_SKILL_IDS.has(skillId)) {
    combined.efficiencyBonus += globalBuffPct(gb.production) / 100;
  }
  if (skillId === 'enhancing') {
    combined.speedBonus += globalBuffPct(gb.enhancingSpeed) / 100;
  }
}

function successRate(personLv, targetLv, successBonus) {
  const delta = personLv - targetLv;
  const adj = delta >= 0 ? SUCCESS_ABOVE*delta : SUCCESS_BELOW*delta;
  const rate = SUCCESS_BASE * (1 + adj + (successBonus||0));
  return Math.max(SUCCESS_MIN, Math.min(1, rate));
}

function computePersonSkillMetrics(person, skillIdx) {
  const skillId = SKILL_KEYS[skillIdx];
  const baseLevel = Number(person.levels[skillIdx]||0);
  // 装备：生活装备「拥有制」槽位（上衣/下装/披风）按本技能自动择优，其余配装槽按登记的单件
  const b = computeBonusForSkill(person, skillId, baseLevel);
  // 手动输入的全局 buff：按技能分类叠加相应比例
  addGlobalBuffsToCombined(b, skillId);
  // 逐人加成：成就档 buff、房屋房间 buff（依赖导入 profile 中的对应字段）
  const achB = extractAchievementBonuses(person, skillId);
  b.speedBonus += achB.speedBonus; b.efficiencyBonus += achB.efficiencyBonus; b.successBonus += achB.successBonus; b.gatheringBonus += achB.gatheringBonus; b.skillLevelBonus += achB.skillLevelBonus;
  const houseB = extractHouseBuffBonuses(person, skillId);
  b.speedBonus += houseB.speedBonus; b.efficiencyBonus += houseB.efficiencyBonus; b.successBonus += houseB.successBonus; b.gatheringBonus += houseB.gatheringBonus; b.skillLevelBonus += houseB.skillLevelBonus;
  // 公会建筑（有效等级）/ 公会神龛（效率/速度），本地输入项
  applyGuildBuilding(b, skillId);
  applyGuildShrine(b, person);
  const effLevel = Math.max(0, baseLevel + (b.skillLevelBonus||0));
  const actionSeconds = BASE_ACTION_SEC / Math.max(0.05, 1+(b.speedBonus||0));
  const workP = Math.max(0, Math.floor(effLevel * (1+(b.efficiencyBonus||0))));
  let dblP = Math.max(0, Math.min(1, b.gatheringBonus||0));
  const baseRatePerSecond = actionSeconds > 0 ? (workP*(1+dblP))/actionSeconds : 0;
  return {baseLevel,effLevel,actionSeconds,workP,dblP,baseRatePerSecond,successBonus:b.successBonus||0};
}

function expectedRate(m, T) {
  if (m.baseRatePerSecond <= 0) return 0;
  return m.baseRatePerSecond * successRate(m.effLevel, T, m.successBonus);
}

function computePasses(metricsList) {
  const N = metricsList.length; if (N===0) return 0;
  const countMult = 1 + COUNT_INFLATION*N;
  let T = START_LV, passes = 0, carry = 0, timeLeft = TRIAL_DURATION;
  while (timeLeft > 0 && passes < MAX_PASS_GUARD) {
    let rate = 0;
    for (const m of metricsList) rate += expectedRate(m, T);
    if (rate <= 1e-9) break;
    const required = (BASE_TOTAL_PT + PT_GROWTH*passes) * countMult;
    const diff = required - carry;
    if (diff <= 0) { carry -= required; passes++; T += LV_PER_PASS; continue; }
    const tNeeded = diff / rate;
    if (tNeeded > timeLeft + 1e-9) break;
    timeLeft -= tNeeded; carry = carry + tNeeded*rate - required; passes++; T += LV_PER_PASS;
  }
  return passes;
}

function finalLv(metricsList) { return START_LV + LV_PER_PASS * computePasses(metricsList); }

class MinCostFlow {
  constructor(n) { this.n=n; this.adj=Array.from({length:n},()=>[]); this.to=[]; this.cap=[]; this.cost=[]; }
  addEdge(u,v,cap,cost) { this.adj[u].push(this.to.length); this.to.push(v); this.cap.push(cap); this.cost.push(cost); this.adj[v].push(this.to.length); this.to.push(u); this.cap.push(0); this.cost.push(-cost); }
  capOf(e) { return this.cap[e]; }
  get edgeCount() { return this.to.length; }
  run(s,t) {
    const INF=Infinity, n=this.n; const dist=new Array(n), prevE=new Array(n), inQ=new Array(n);
    const spfa=()=>{ for(let i=0;i<n;i++){dist[i]=INF;prevE[i]=-1;inQ[i]=false;} dist[s]=0; const q=[s]; inQ[s]=true; while(q.length){ const u=q.shift(); inQ[u]=false; for(const e of this.adj[u]){ if(this.cap[e]<=0)continue; const v=this.to[e]; const nd=dist[u]+this.cost[e]; if(nd<dist[v]){dist[v]=nd;prevE[v]=e;if(!inQ[v]){q.push(v);inQ[v]=true;}}}} return dist[t]<INF; };
    while(spfa() && dist[t]<0){ let bn=Infinity; for(let v=t;v!==s;){const e=prevE[v];if(this.cap[e]<bn)bn=this.cap[e];v=this.to[e^1];} for(let v=t;v!==s;){const e=prevE[v];this.cap[e]-=bn;this.cap[e^1]+=bn;v=this.to[e^1];} }
  }
}

function buildPersonMetricsMap(people) {
  return people.map(p => SKILL_KEYS.map((_,s) => computePersonSkillMetrics(p, s)));
}

function initialAssignment(people, cfgs, mm) {
  const P=people.length, src=0, sink=P+5; const flow=new MinCostFlow(P+6);
  for(let p=0;p<P;p++) flow.addEdge(src,1+p,1,0);
  const pjEdge=Array.from({length:P},()=>new Array(NUM_TRIALS).fill(-1));
  for(let p=0;p<P;p++){ for(let j=0;j<NUM_TRIALS;j++){ const m=mm[p][cfgs[j].skill]; if(m.baseLevel<=0||m.baseRatePerSecond<=0)continue; const cost=-Math.max(1,Math.round(expectedRate(m,START_LV)*100)); pjEdge[p][j]=flow.edgeCount; flow.addEdge(1+p,1+P+j,1,cost); } }
  for(let j=0;j<NUM_TRIALS;j++) flow.addEdge(1+P+j,sink,cfgs[j].max,0);
  flow.run(src,sink);
  const a=new Array(P).fill(-1);
  for(let p=0;p<P;p++){ for(let j=0;j<NUM_TRIALS;j++){ const e=pjEdge[p][j]; if(e>=0 && flow.capOf(e)===0){ a[p]=j; break; } } }
  return a;
}

function localSearch(assignment, people, cfgs, mm) {
  const P=people.length; const lists=Array.from({length:NUM_TRIALS},()=>[]);
  for(let p=0;p<P;p++){ const j=assignment[p]; if(j>=0) lists[j].push(mm[p][cfgs[j].skill]); }
  const tLv=new Array(NUM_TRIALS); for(let j=0;j<NUM_TRIALS;j++) tLv[j]=finalLv(lists[j]);
  const without=(l,m)=>{const o=[];let r=false;for(const x of l){if(!r&&x===m){r=true;continue;}o.push(x);}return o;};
  const withAdd=(l,m)=>l.concat([m]);
  let improved=true, guard=0;
  while(improved && guard++<500) {
    improved=false;
    for(let p=0;p<P;p++){
      const curT=assignment[p]; const curM=curT>=0?mm[p][cfgs[curT].skill]:null;
      let bestNew=curT, bestGain=0, bestFromLv=curT>=0?tLv[curT]:0, bestNewToLv=0;
      const curFromLv=curT>=0?tLv[curT]:0;
      for(let newT=-1;newT<NUM_TRIALS;newT++){
        if(newT===curT)continue; let newM=null;
        if(newT>=0){ newM=mm[p][cfgs[newT].skill]; if(newM.baseLevel<=0)continue; if(lists[newT].length>=cfgs[newT].max)continue; }
        const newFromLv=curT>=0?finalLv(without(lists[curT],curM)):0;
        const oldToLv=newT>=0?tLv[newT]:0; const newToLv=newT>=0?finalLv(withAdd(lists[newT],newM)):0;
        const gain=(newFromLv-curFromLv)+(newToLv-oldToLv);
        if(gain>bestGain){bestGain=gain;bestNew=newT;bestFromLv=newFromLv;bestNewToLv=newToLv;}
      }
      if(bestGain>0){ if(curT>=0){const l=lists[curT];const i=l.indexOf(curM);if(i>=0)l.splice(i,1);tLv[curT]=bestFromLv;} if(bestNew>=0){lists[bestNew].push(mm[p][cfgs[bestNew].skill]);tLv[bestNew]=bestNewToLv;} assignment[p]=bestNew; improved=true; }
    }
    for(let p=0;p<P;p++){ const tP=assignment[p];if(tP<0)continue; const mPinP=mm[p][cfgs[tP].skill];
      for(let q=p+1;q<P;q++){ const tQ=assignment[q];if(tQ<0||tQ===tP)continue; const mQinQ=mm[q][cfgs[tQ].skill]; const mPinQ=mm[p][cfgs[tQ].skill]; const mQinP=mm[q][cfgs[tP].skill];
        if(mPinQ.baseLevel<=0||mQinP.baseLevel<=0)continue;
        const newLvP=finalLv(without(lists[tP],mPinP).concat([mQinP])); const newLvQ=finalLv(without(lists[tQ],mQinQ).concat([mPinQ]));
        const gain=(newLvP+newLvQ)-(tLv[tP]+tLv[tQ]);
        if(gain>0){const lp=lists[tP],lq=lists[tQ];lp.splice(lp.indexOf(mPinP),1);lp.push(mQinP);lq.splice(lq.indexOf(mQinQ),1);lq.push(mPinQ);tLv[tP]=newLvP;tLv[tQ]=newLvQ;assignment[p]=tQ;assignment[q]=tP;improved=true;}
      }
    }
  }
}

function runAssignment(people, cfgs) {
  const mm=buildPersonMetricsMap(people);
  const assignment=initialAssignment(people,cfgs,mm);
  localSearch(assignment,people,cfgs,mm);
  const P=people.length; const assigned=Array.from({length:NUM_TRIALS},()=>[]);
  for(let p=0;p<P;p++){const j=assignment[p];if(j>=0)assigned[j].push({person:people[p],metrics:mm[p][cfgs[j].skill]});}
  let grandFinal=0,grandPasses=0,grandCount=0; const cache=new Array(NUM_TRIALS);
  for(let j=0;j<NUM_TRIALS;j++){
    const list=assigned[j]; list.sort((a,b)=>a.person.name.localeCompare(b.name,'zh-Hans-CN'));
    const passes=computePasses(list.map(e=>e.metrics));
    const fLv=START_LV+LV_PER_PASS*passes;
    grandFinal+=fLv; grandPasses+=passes; grandCount+=list.length;
    const countMult = 1 + COUNT_INFLATION * list.length;
    const reqNext = Math.ceil((BASE_TOTAL_PT + PT_GROWTH * passes) * countMult);
    let sumWork = 0; for (const e of list) sumWork += e.metrics.workP;
    const finalT = START_LV + LV_PER_PASS * passes;
    let rateAtFinal = 0; for (const e of list) rateAtFinal += expectedRate(e.metrics, finalT);
    let sum=0; for(const e of list) sum+=e.person.levels[cfgs[j].skill];
    cache[j]={list,sum,passes,finalLv:fLv,reqNext,sumWork,rateAtFinal,max:cfgs[j].max,skill:cfgs[j].skill};
  }
  const assignedIds=new Set(); for(const l of assigned) for(const e of l) assignedIds.add(e.person.id);
  const unassigned=people.filter(p=>!assignedIds.has(p.id)).sort((a,b)=>a.name.localeCompare(b.name,'zh-Hans-CN'));
  return {cache,unassigned,grandCount,grandFinal,grandPasses,assignment};
}

// === SVG Helper ===
function svgIcon(id, w, h) {
  return '<svg viewBox="0 0 50 50" style="width:'+w+'px;height:'+h+'px"><use xlink:href="#'+id+'"></use></svg>';
}

// 统一的 buff 类型 → 加成字段映射（神龛 / 成就 / 房屋共用）。
// 生活试炼推演只用 speed/efficiency/success/gathering/skillLevel；
// damage / attackSpeed / castSpeed / maxHp / maxMp 等战斗向字段先算好，供后续战斗试炼直接取用。
function addBonusByType(out, type, amt, skillId) {
  if (!type || !amt) return;
  switch (type) {
    case 'efficiency':         out.efficiencyBonus = (out.efficiencyBonus||0) + amt; break;
    case 'action_speed': case 'speed': out.speedBonus = (out.speedBonus||0) + amt; break;
    case 'success_rate': case 'enhancing_success': out.successBonus = (out.successBonus||0) + amt; break;
    case 'gathering':          out.gatheringBonus = (out.gatheringBonus||0) + amt; break;
    case 'damage':             out.damageBonus = (out.damageBonus||0) + amt; break;
    case 'attack_speed':       out.attackSpeedBonus = (out.attackSpeedBonus||0) + amt; break;
    case 'cast_speed':         out.castSpeedBonus = (out.castSpeedBonus||0) + amt; break;
    case 'max_hitpoints':      out.maxHpBonus = (out.maxHpBonus||0) + amt; break;
    case 'max_manapoints':     out.maxMpBonus = (out.maxMpBonus||0) + amt; break;
    case 'rare_find':          out.rareFindBonus = (out.rareFindBonus||0) + amt; break;
    case 'essence_find':       out.essenceFindBonus = (out.essenceFindBonus||0) + amt; break;
    case 'wisdom':             out.wisdomBonus = (out.wisdomBonus||0) + amt; break;
    default:
      // <attr>_level：只有与当前技能一致（或未指定技能）时才计入有效等级；
      // 战斗属性等级（attack/defense/... ）不影响生活试炼。
      if (type.slice(-6) === '_level') {
        const attr = type.slice(0, -6);
        if (!skillId || attr === skillId) out.skillLevelBonus = (out.skillLevelBonus||0) + amt;
      }
  }
}

// === Rendering ===
function renderTableHeader() {
  const thead = document.getElementById('member-thead');
  let html = '<tr>';
  html += '<th class="assign-col">'+t('assignCol')+'</th>';
  html += '<th class="name-col">'+t('nameCol')+'</th>';
  // 专业等级(10) / 装备(22) / 房屋(17) / 神龛(10) / 成就(6) 全部个人数据已移入「详情」弹窗（见 openMemberDetail）
  html += '<th class="detail-col">'+t('detailBtn')+'</th>';
  html += '<th></th>';
  html += '</tr>';
  thead.innerHTML = html;
}
function renderAll() {
  document.title = t('title');
  applyTrialCaps();
  renderTableHeader();
  renderTrialCards();
  renderGuildInputs();
  renderMemberTable();
  renderSummary();
  updateStaticText();
  renderMemberDetailIfOpen();
}

function updateStaticText() {
  document.getElementById('h1-title').textContent = t('title');
  document.getElementById('h2-trial').textContent = t('trialConfig');
  document.getElementById('h2-member').firstChild.textContent = t('memberData') + ' ';
  { const mHint = document.getElementById('member-hint'); if (mHint) mHint.title = t('memberDetailTip'); }
  document.getElementById('btn-add-member').textContent = '+ '+t('addMember');
  document.getElementById('btn-share').textContent = t('share');
  document.getElementById('btn-import-json').textContent = t('importData');
  document.getElementById('btn-export-json').textContent = t('exportData');
  document.getElementById('export-script-link').title = t('exportScriptTitle');
  document.getElementById('btn-calculate').textContent = t('calculate');
  document.getElementById('btn-lang').textContent = t('language');
  document.getElementById('btn-theme').textContent = t('theme');
  const connEl = document.getElementById('conn-status');
  if (!state.isShared) connEl.textContent = t('offlineMode');
  else connEl.textContent = t('connected')+': '+state.guild;
  // 全局 buff 文案 + 提示 + 回填输入
  const gbTitle = document.getElementById('h3-global-buff');
  if (gbTitle) gbTitle.firstChild.textContent = t('globalBuffs') + ' ';
  const gbHint = document.getElementById('global-buff-hint');
  if (gbHint) gbHint.title = t('globalBuffsTip');
  const gbMap = [
    ['gathering',       'buffGathering',      'buffGatheringTip'],
    ['production',      'buffProduction',     'buffProductionTip'],
    ['enhancingSpeed',  'buffEnhancingSpeed', 'buffEnhancingSpeedTip'],
  ];
  for (const [k, lblKey, tipKey] of gbMap) {
    const l = document.getElementById('gb-lbl-'+k); if (l) l.textContent = t(lblKey);
    const u = document.getElementById('gb-unit-'+k); if (u) u.textContent = t('levelUnit');
    const inp = document.getElementById('gb-input-'+k);
    const item = inp && inp.parentElement;
    if (item) item.title = t(tipKey);
  }
  syncGlobalBuffInputs();
  // 公会建筑 文案 + 提示 + 回填输入
  const gbBTitle = document.getElementById('h3-guild-buildings');
  if (gbBTitle) gbBTitle.firstChild.textContent = t('guildBuildings') + ' ';
  const gbBHint = document.getElementById('guild-buildings-hint');
  if (gbBHint) gbBHint.title = t('guildBuildingsTip');
  // 顶部建筑栏副标题（“公会全局 · 随共享上传”）
  const gbShared = document.getElementById('guild-buildings-shared');
  if (gbShared) gbShared.textContent = t('guildBuildingsShared');
  syncGuildInputs();
}

function renderTrialCards() {
  const container = document.getElementById('trial-cards');
  applyTrialCaps();   // 人数上限始终由生活营地等级派生，保证显示与算法一致
  const campLv = Math.max(0, Math.min(GUILD_BUILDING_MAX_LEVEL, Math.floor(Number((state.guildBuildings||{}).skilling_encampment) || 0)));
  const capHtml = t('trialSlotsFromCamp')
    .replace('{level}', campLv)
    .replace('{base}', GUILD_BUILDING_SKILLING_BASE_CAP)
    .replace('{per}', GUILD_BUILDING_SKILLING_SLOTS_PER_LEVEL)
    .replace('{cap}', skillingTrialCap());
  container.innerHTML = state.trials.map((cfg, j) => {
    let memberListHtml = '';
    let resultHtml = '';
    if (state.result && state.result.cache[j]) {
      const c = state.result.cache[j];
      memberListHtml = c.list.map(e => {
        const lv = e.person.levels[cfg.skill];
        return '<div class="trial-member-item"><span class="ml">'+escHtml(e.person.name)+'</span><span class="mr">Lv'+lv+'</span></div>';
      }).join('');
      const rateStr = c.rateAtFinal.toFixed(1);
      resultHtml = '<div class="trial-result">Lv'+c.finalLv+' &middot; '+c.passes+t('passes')+' &middot; '+c.list.length+'/'+c.max+t('people')+'<br>'+t('teamWork')+' '+c.sumWork+' &middot; ~'+rateStr+t('perSec')+' @ Lv'+c.finalLv+'<br>'+t('nextClearNeeds')+' '+c.reqNext+' '+t('pts')+'</div>';
    }
    return '<div class="trial-card">'+
      '<div class="trial-card-header">'+
        '<div class="trial-skill-icon" onclick="openSkillPicker('+j+',this)">'+svgIcon(SKILL_KEYS[cfg.skill],36,36)+'</div>'+
        '<div class="trial-card-info"><div class="trial-card-title">'+t('trial')+' '+(j+1)+'</div><div class="trial-skill-name">'+skillLabel(cfg.skill)+'</div></div>'+
      '</div>'+
      '<div class="trial-max-row"><label>'+t('maxMembers')+':</label><span class="trial-max-value">'+cfg.max+'</span>'+
        '<span class="trial-max-hint" title="'+escHtml(capHtml)+'">'+t('trialSlotsAuto')+'</span></div>'+
      '<div class="trial-member-list" data-empty="'+t('noAssign')+'">'+memberListHtml+'</div>'+
      resultHtml+
    '</div>';
  }).join('');
}

function shrineDefsList() {
  if (typeof GUILD_SHRINE_DEFS !== 'undefined' && GUILD_SHRINE_DEFS.length) return GUILD_SHRINE_DEFS;
  const buffs = (typeof GUILD_SHRINE_SKILL_BUFFS !== 'undefined') ? GUILD_SHRINE_SKILL_BUFFS : {};
  return GUILD_SHRINE_KEYS.map(k => ({ key:k, zh:k, en:k, icon:'guild_shrine_'+k,
    type:(buffs[k]||{}).type, flatPerLevel:(buffs[k]||{}).flatPerLevel, affectsTrial:(k==='force'||k==='tempo') }));
}
// 注：角色名后不再显示神龛等级（神龛改在成员详情弹窗编辑），原 memberShrineBadgeText / personalShrineBadge 已移除

// 成就档位（成员级「个人持久化数据」，逐成员可编辑并随共享上传）。
// 只有 Beginner/Adept 两档会影响试炼指标，实际加成数值仍由 EMBEDDED_CLIENT_DATA.achievementTierDetailMap 决定。
function achievementTiersList() {
  return (typeof ACHIEVEMENT_TIERS !== 'undefined' && ACHIEVEMENT_TIERS.length) ? ACHIEVEMENT_TIERS : [];
}
// 成员勾选的档位 → 游戏 hrid 布尔表（applyAchievementTierBuffs 的入参格式）
function memberAchievementValue(p) {
  if (!p || !p.achievements) return null;
  const val = {};
  for (const d of achievementTiersList()) if (p.achievements[d.key]) val[d.hrid] = true;
  return val;
}
function memberAchievementDone(p, key) {
  return !!(p && p.achievements && p.achievements[key]);
}
// 导入 profile 的成就信息 → 成员可编辑的档位勾选（个人持久化数据）
function materializeMemberAchievements(profile) {
  const out = {};
  for (const d of achievementTiersList()) out[d.key] = false;
  if (!profile) return out;
  let value = null;
  if (profile.achievementsValue && typeof profile.achievementsValue === 'object' && !Array.isArray(profile.achievementsValue)) {
    value = profile.achievementsValue;
  } else {
    // 共享资料里成就常见为数组 characterAchievements（也可能叫 achievements）
    const rawMap = normalizeAchievementsMap(profile.achievements || profile.characterAchievements);
    if (rawMap && typeof computeAchievementsValue === 'function') value = computeAchievementsValue(rawMap);
  }
  if (value && typeof value === 'object') {
    for (const d of achievementTiersList()) if (value[d.hrid] === true) out[d.key] = true;
  }
  return out;
}

function renderMemberTable() {
  const tbody = document.getElementById('member-tbody');
  // 装备数据归一化（旧「一槽一件」的身体/腿部/背部 → 生活装备「拥有制」集合；幂等）
  for (const p of state.members) normalizeMemberEquip(p);
  if (state.members.length === 0) {
    tbody.innerHTML = '<tr><td colspan="4" style="color:var(--text-faint);padding:20px">'+t('noMembers')+'</td></tr>';
    return;
  }
  tbody.innerHTML = state.members.map(p => {
    const assign = state.assignment ? state.assignment[p.id] : -1;
    const assignClass = assign >= 0 ? 'assign-T'+(assign+1) : 'assign-none';
    let assignContent;
    if (assign >= 0) {
      const skillIdx = state.trials[assign].skill;
      assignContent = svgIcon(SKILL_KEYS[skillIdx], 22, 22);
    } else {
      assignContent = '-';
    }
    // 专业 / 装备 / 房屋 / 神龛 / 成就 全部个人数据都在「详情」弹窗里编辑（见 openMemberDetail）
    return '<tr>'+
      '<td class="assign-cell '+assignClass+'">'+assignContent+'</td>'+
      '<td class="name-cell"><input type="text" value="'+escHtml(p.name)+'" onchange="updateMemberName('+p.id+',this.value)"></td>'+
      '<td class="detail-cell"><button class="btn btn-sm" onclick="openMemberDetail('+p.id+')">'+t('detailBtn')+'</button></td>'+
      '<td><button class="btn btn-sm btn-danger" onclick="removeMember('+p.id+')">'+t('deleteBtn')+'</button></td>'+
    '</tr>';
  }).join('');
}

// === 成员详情弹窗：专业 / 装备 / 房屋 / 神龛 / 成就 等个人数据集中编辑 ===
// memberDetailId 记录当前打开的成员（null = 未打开）；渲染前用它判断是否需要刷新弹窗。
let memberDetailId = null;
function openMemberDetail(id) {
  const p = state.members.find(x => x.id === id);
  if (!p) return;
  memberDetailId = id;
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'member-detail-overlay';
  overlay.onclick = (e) => { if (e.target === overlay) closeMemberDetail(); };
  overlay.innerHTML = '<div class="modal-dialog" style="max-width:920px">'
    + '<div class="modal-title"><span id="member-detail-title"></span><button class="modal-close" onclick="closeMemberDetail()">&times;</button></div>'
    + '<div class="detail-body" id="member-detail-body"></div>'
    + '<div class="modal-actions"><button class="btn btn-primary" onclick="closeMemberDetail()">'+t('confirm')+'</button></div>'
    + '</div>';
  document.body.appendChild(overlay);
  renderMemberDetail(id);
}
function closeMemberDetail() {
  memberDetailId = null;
  const o = document.getElementById('member-detail-overlay');
  if (o) o.remove();
}
// 弹窗打开时，成员数据变化后刷新其内容（未打开则什么都不做）
function renderMemberDetailIfOpen(id) {
  if (memberDetailId === null) return;
  if (id !== undefined && id !== memberDetailId) {
    // 该成员已被删除 → 关掉弹窗
    if (!state.members.some(x => x.id === memberDetailId)) { closeMemberDetail(); }
    return;
  }
  renderMemberDetail(memberDetailId);
}
function renderMemberDetail(id) {
  const p = state.members.find(x => x.id === id);
  if (!p) { closeMemberDetail(); return; }
  normalizeMemberEquip(p);
  const en = (state.lang === 'en');
  const titleEl = document.getElementById('member-detail-title');
  if (titleEl) titleEl.textContent = (p.name || '') + ' · ' + t('memberDetail');
  const body = document.getElementById('member-detail-body');
  if (!body) return;
  // 1) 专业等级：10 项（挤奶…强化），逐人可编辑，随共享数据上传
  let skillHtml = '';
  for (let s = 0; s < 10; s++) {
    skillHtml += '<label class="detail-item" title="'+escHtml(skillLabel(s))+'">'
      + svgIcon(SKILL_KEYS[s], 20, 20)
      + '<span class="di-label">'+escHtml(skillLabel(s))+'</span>'
      + '<input type="number" value="'+(p.levels[s]||0)+'" min="0" max="999" onchange="updateSkillLevel('+p.id+','+s+',this.value)"></label>';
  }
  // 2) 装备三区：① 生活装备（勾选制）② 生活·战斗两用（整槽勾选）③ 战斗装备（配装单选）+ 生活工具
  const singleEquipCell = (slot) => {
    const lbl = equipLabel(EQUIP_TYPES.indexOf(slot));
    const eq = p.equipment && p.equipment[slot];
    return '<div class="detail-item equip-item" title="'+escHtml(lbl)+'">'
      + '<span class="di-label">'+escHtml(lbl)+'</span>'
      + (eq && eq.iconId
          ? '<div class="equip-cell" onclick="openEquipPicker('+p.id+',\''+slot+'\')">'+svgIcon(eq.iconId,24,24)+'<span class="enhance-badge">+'+(eq.enhance||0)+'</span></div>'
          : '<div class="equip-cell empty" onclick="openEquipPicker('+p.id+',\''+slot+'\')"></div>')
      + '</div>';
  };
  // 一个装备家族 = 一个方格（与工具 / 战斗装备的 equip-cell 同款，只有图标，物品名放悬停提示）。
  // 点格子 = 打开强化小面板；未拥有 → 虚线框 + 图标灰度；已拥有 → 实线高亮 + 左上角标「★ +N」（★ 在强化等级左边）。
  const familyChip = (slot, fam) => {
    const st = ownedEntry(p, slot, fam.id) || { enh: 0, refined: false };
    const on = ownedEntry(p, slot, fam.id) != null;
    const nm = familyName(fam.id, fam.name);
    const ttl = nm + ' · ' + equipLabel(EQUIP_TYPES.indexOf(slot)) + (fam.refined ? ' · ' + t('refineToggle') : '');
    const iconId = fam.refined && st.refined ? fam.id + '_refined' : fam.id;
    return '<div class="equip-cell own-cell' + (on ? ' is-owned' : ' is-off') + '" title="'+escHtml(ttl)+'"'
      + ' onclick="openEquipEnhPanel('+p.id+',\''+slot+'\',\''+fam.id+'\',this)">'
      + svgIcon(iconId, 26, 26)
      + (on ? '<span class="own-badges">'
          + (st.refined ? '<span class="refine-star">\u2605</span>' : '')
          + '<span class="enhance-badge">+'+st.enh+'</span>'
          + '</span>' : '')
      + '</div>';
  };
  const familyRow = (slot, label) => {
    const fams = equipFamilies(slot);
    if (!fams.length) return '';
    return '<div class="own-row"><span class="own-row-label">'+escHtml(label)+'</span>'
      + '<span class="own-chips">'+fams.map(f => familyChip(slot, f)).join('')+'</span></div>';
  };
  // ① 生活装备（只加生活技能加成）：上衣/下装/披风 可多件（同槽位择优）；头部/手部/脚部/副手 各 1 件
  let lifeRows = '';
  for (const slot of ['身体','腿部','背部']) lifeRows += familyRow(slot, lifeSlotLabel(slot));
  const singleLife = ['头部','手部','脚部','副手'].map(s => equipFamilies(s).map(f => familyChip(s, f)).join('')).join('');
  if (singleLife) lifeRows += '<div class="own-row"><span class="own-row-label">'+escHtml(t('lifeSingleRow'))+'</span><span class="own-chips">'+singleLife+'</span></div>';
  // ② 生活 · 战斗两用（项链/耳环/戒指/袋子）：一槽一件（生活件与战斗件互替）→ 与生活工具同款「配装选择器」
  let hybridHtml = '';
  for (const slot of HYBRID_SLOTS) hybridHtml += singleEquipCell(slot);
  // 生活工具（唯一一件）：10 个单选槽
  let toolHtml = '';
  for (const slot of TOOL_SLOTS) toolHtml += singleEquipCell(slot);
  // ③ 战斗装备（配装制：一槽一件）
  let combatHtml = '';
  for (const slot of COMBAT_EQUIP_SLOTS) combatHtml += singleEquipCell(slot);
  // 3) 房屋：17 房间（10 生活 + 7 战斗），战斗房间置灰
  let houseHtml = '';
  for (const d of houseRoomDefsList()) {
    const cls = 'detail-item' + (d.affectsTrial ? '' : ' is-inactive');
    const scope = d.affectsTrial ? t('shrineAffectsTrial') : t('shrineCombatOnly');
    houseHtml += '<label class="'+cls+'" title="'+escHtml((en?d.en:d.zh)+' · '+(en?d.effectEn:d.effectZh)+' · '+scope)+'">'
      + svgIcon(d.icon || ('house_'+d.key), 20, 20)
      + '<span class="di-label">'+escHtml(en?d.en:d.zh)+'</span>'
      + '<input type="number" value="'+houseRoomLevel(p, d.key)+'" min="0" max="'+HOUSE_ROOM_MAX_LEVEL+'" onchange="updateMemberHouseRoom('+p.id+',\''+d.key+'\',this.value)"></label>';
  }
  // 4) 神龛：10 槽位（5 座 × 生活/战斗），分两行 —— 上行生活类、下行战斗类；不影响试炼推演的置灰
  const shrineItem = (s) => {
    const cls = 'detail-item' + (s.affectsTrial ? '' : ' is-inactive');
    const scope = s.affectsTrial ? t('shrineAffectsTrial') : (s.affectsCombat ? t('shrineCombatOnly') : t('shrineNotAffectsTrial'));
    const full = (en ? s.en : s.zh);
    // 标签只保留神龛本名（去掉「神龛」二字与「（生活）/（战斗）」后缀）—— 变体由分行的「生活类 / 战斗类」标签表达
    const short = full.replace(/神龛/g, '').replace(/ Shrine/g, '')
      .replace(/\s*[（(](生活|战斗|Skilling|Combat)[）)]/g, '').trim() || full;
    return '<label class="'+cls+'" title="'+escHtml(full+': '+(en?s.effectEn:s.effectZh)+' · '+scope)+'">'
      + svgIcon(s.icon || ('guild_shrine_'+s.shrine), 20, 20)
      + '<span class="di-label">'+escHtml(short)+'</span>'
      + '<input type="number" value="'+memberShrineLevel(p, s.slot)+'" min="0" max="'+GUILD_SHRINE_MAX_LEVEL+'" onchange="updateMemberShrine('+p.id+',\''+s.slot+'\',this.value)"></label>';
  };
  const skillingSlotList = shrineSlotsList().filter(s => s.kind !== 'combat');
  const combatSlotList = shrineSlotsList().filter(s => s.kind === 'combat');
  const shrineHtml = (skillingSlotList.length || combatSlotList.length)
    ? '<div class="detail-rows">'
      + '<div class="detail-row"><span class="detail-row-label">'+escHtml(t('detailShrineSkillingRow'))+'</span><div class="detail-grid cols-5">'+skillingSlotList.map(shrineItem).join('')+'</div></div>'
      + '<div class="detail-row"><span class="detail-row-label">'+escHtml(t('detailShrineCombatRow'))+'</span><div class="detail-grid cols-5">'+combatSlotList.map(shrineItem).join('')+'</div></div>'
      + '</div>'
    : '';
  // 5) 成就完成：6 档勾选（不影响试炼推演的置灰 —— 新手/老手/精英）
  let achHtml = '';
  for (const d of achievementTiersList()) {
    const cls = 'detail-item' + (d.affectsTrial ? '' : ' is-inactive');
    const req = d.total ? (' · '+(en ? 'needs all '+d.total : '需该档全部 '+d.total+' 项')) : '';
    achHtml += '<label class="'+cls+'" title="'+escHtml((en?d.en:d.zh)+' · '+(en?d.effectEn:d.effectZh)+req)+'">'
      + '<input type="checkbox"'+(memberAchievementDone(p, d.key) ? ' checked' : '')
      + ' onchange="updateMemberAchievement('+p.id+',\''+d.key+'\',this.checked)">'
      + '<span class="di-label">'+escHtml(en?d.en:d.zh)+'<span class="di-sub">'+escHtml(en?d.effectEn:d.effectZh)+'</span></span></label>';
  }
  // 区块顺序：专业 → 装备 → 房屋 → 神龛 → 成就完成
  body.innerHTML =
    '<div class="detail-section"><div class="detail-section-title" title="'+escHtml(t('detailSkillTip'))+'">'+escHtml(t('detailSkillSec'))+'</div><div class="detail-grid">'+skillHtml+'</div></div>'
    + '<div class="detail-section"><div class="detail-section-title" title="'+escHtml(t('detailEquipTip'))+'">'+escHtml(t('detailEquipSec'))+'</div>'
      + '<div class="detail-subtitle" title="'+escHtml(t('lifeEquipTip'))+'">'+escHtml(t('lifeEquipSec'))+'</div>'
      + '<div class="own-rows">'+lifeRows+'</div>'
      + '<div class="detail-subtitle" title="'+escHtml(t('hybridEquipTip'))+'">'+escHtml(t('hybridEquipSec'))+'</div>'
      + '<div class="detail-grid">'+hybridHtml+'</div>'
      + '<div class="detail-subtitle" title="'+escHtml(t('lifeToolsTip'))+'">'+escHtml(t('lifeToolsSec'))+'</div>'
      + '<div class="detail-grid">'+toolHtml+'</div>'
      + '<div class="detail-subtitle" title="'+escHtml(t('combatEquipTip'))+'">'+escHtml(t('combatEquipSec'))+'</div>'
      + '<div class="detail-grid">'+combatHtml+'</div>'
      + '</div>'
    + '<div class="detail-section"><div class="detail-section-title" title="'+escHtml(t('houseRoomsTip'))+'">'+escHtml(t('detailHouseSec'))+'</div><div class="detail-grid">'+houseHtml+'</div></div>'
    + '<div class="detail-section"><div class="detail-section-title" title="'+escHtml(t('guildShrinePerMemberTip'))+'">'+escHtml(t('detailShrineSec'))+'</div>'+shrineHtml+'</div>'
    + '<div class="detail-section"><div class="detail-section-title" title="'+escHtml(t('achievementsTip'))+'">'+escHtml(t('detailAchSec'))+'</div><div class="detail-grid">'+achHtml+'</div></div>';
}

function renderSummary() {
  const bar = document.getElementById('summary-bar');
  if (!state.result) {
    bar.innerHTML = state.members.length+' '+t('people');
    return;
  }
  const r = state.result;
  bar.innerHTML = t('totalFinalLv')+': <span class="summary-num">'+r.grandFinal+'</span> | '+t('totalPasses')+': <span class="summary-num">'+r.grandPasses+'</span> | '+t('assigned')+': <span class="summary-num">'+r.grandCount+'/'+state.members.length+'</span>'+(r.unassigned.length>0 ? ' | '+t('unassigned')+': <span style="color:var(--danger)">'+r.unassigned.length+'</span>' : '');
}

function renderAssignmentResults() {
  renderTrialCards();
  renderMemberTable();
  renderSummary();
}

function escHtml(s) {
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// 注：角色名后不再显示神龛等级（神龛改在成员详情弹窗编辑），原 personalShrineBadge 已移除

// === Theme & Language ===
function toggleTheme() {
  state.theme = state.theme === 'light' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', state.theme);
  try { localStorage.setItem('mwi_theme', state.theme); } catch(e) {}
  document.getElementById('btn-theme').textContent = t('theme');
}
function toggleLang() {
  state.lang = state.lang === 'zh' ? 'en' : 'zh';
  try { localStorage.setItem('mwi_lang', state.lang); } catch(e) {}
  renderAll();
}
function updateGlobalBuff(key, val) {
  if (!state.globalBuffs) state.globalBuffs = { gathering:0, production:0, enhancingSpeed:0 };
  const n = Math.max(0, Math.floor(Number(val) || 0));
  state.globalBuffs[key] = n;
  try { localStorage.setItem('mwi_global_buffs', JSON.stringify(state.globalBuffs)); } catch(e) {}
  // 已经有过一次分配 → 用新加成重算；没有分配也刷新一下成员表以便未来渲染时能反映
  if (state.members && state.members.length > 0 && state.result) {
    calculate();
  } else {
    renderMemberTable();
    renderSummary();
  }
  syncGlobalBuffInputs();
}
function syncGlobalBuffInputs() {
  const gb = state.globalBuffs || { gathering:0, production:0, enhancingSpeed:0 };
  const map = { gathering:'gb-input-gathering', production:'gb-input-production', enhancingSpeed:'gb-input-enhancingSpeed' };
  for (const k in map) {
    const el = document.getElementById(map[k]);
    if (el && el !== document.activeElement) el.value = Number(gb[k] || 0);
  }
}
// 公会建筑（23 座：6 功能 + 17 试炼）/ 神龛（5）：本地输入项，渲染 + 同步 + 持久化
function guildBuildingAllKeys() {
  return (typeof GUILD_BUILDING_ALL_KEYS !== 'undefined') ? GUILD_BUILDING_ALL_KEYS : GUILD_BUILDING_KEYS;
}
function renderGuildInputs() {
  const en = (state.lang === 'en');
  const nm = (zh, e) => en ? (e || zh || '') : (zh || e || '');
  const iconRef = (id) => '<svg class="global-buff-icon" viewBox="0 0 40 40"><use xlink:href="#'+id+'"></use></svg>';
  const lvlInput = (id, cb) => '<input type="number" min="0" max="'+GUILD_BUILDING_MAX_LEVEL+'" step="1" id="'+id+'" onchange="'+cb+'">';
  const item = (iconId, label, tip, key, extraCls) =>
    '<label class="global-buff-item'+(extraCls||'')+'" title="'+escHtml(tip)+'">'
      + iconRef(iconId) + '<span class="global-buff-label">'+escHtml(label)+'</span>'
      + lvlInput('gb-building-input-'+key, "updateGuildBuilding('"+key+"', this.value)")
      + '<span class="global-buff-unit">'+t('levelUnit')+'</span></label>';

  const bb = document.getElementById('guild-buildings-bar');
  if (bb) {
    const util = (typeof GUILD_BUILDING_UTILITY !== 'undefined') ? GUILD_BUILDING_UTILITY : [];
    const trial = (typeof GUILD_BUILDING_TRIAL !== 'undefined') ? GUILD_BUILDING_TRIAL : [];
    const lifeKeys = (typeof GUILD_BUILDING_LIFE_KEYS !== 'undefined') ? GUILD_BUILDING_LIFE_KEYS : [];
    const combatKeys = (typeof GUILD_BUILDING_COMBAT_KEYS !== 'undefined') ? GUILD_BUILDING_COMBAT_KEYS : [];
    const parts = [];
    // 每块 = 一组标题 + 一个「每行最多 5 个」的等宽网格（列宽一致 → 字数不同的建筑名自动对齐）
    const row = (labelKey, items) => {
      if (!items.length) return;
      parts.push('<div class="global-buff-row">'
        + '<span class="global-buff-group-label">'+escHtml(t(labelKey))+'</span>'
        + '<div class="global-buff-grid">'+items.join('')+'</div></div>');
    };
    // 第一行：功能建筑（6 座，公会全局效果，不影响试炼层数）
    row('guildBuildingsUtility', util.map(u => {
      const iconId = (GUILD_BUILDING_ICONS && GUILD_BUILDING_ICONS[u.key]) || u.icon;
      const tip = nm(u.zh,u.en) + ' · ' + nm(u.effectZh,u.effectEn) + ' — ' + t('guildBuildingsTip');
      return item(iconId, nm(u.zh,u.en), tip, u.key, ' is-utility');
    }));
    // 第二行：生活类建筑（10 座，对应生活技能，影响生活试炼）
    row('guildBuildingsLife', trial.filter(td => lifeKeys.indexOf(td.skill) >= 0).map(td => {
      const iconId = (GUILD_BUILDING_ICONS && GUILD_BUILDING_ICONS[td.skill]) || td.icon;
      const tip = nm(td.zh,td.en) + ' · ' + nm(td.skillZh,td.skillEn) + ' +' + GUILD_BUILDING_SKILL_PER_LEVEL + ' — ' + t('guildBuildingsTip');
      return item(iconId, nm(td.zh,td.en), tip, td.skill, ' is-life');
    }));
    // 第三行：战斗类建筑（7 座，对应战斗属性；暂未模拟战斗试炼）
    row('guildBuildingsCombat', trial.filter(td => combatKeys.indexOf(td.skill) >= 0).map(td => {
      const iconId = (GUILD_BUILDING_ICONS && GUILD_BUILDING_ICONS[td.skill]) || td.icon;
      const tip = nm(td.zh,td.en) + ' · ' + nm(td.skillZh,td.skillEn) + ' +' + GUILD_BUILDING_SKILL_PER_LEVEL + ' — ' + t('guildBuildingsTip');
      return item(iconId, nm(td.zh,td.en), tip, td.skill, ' is-combat');
    }));
    bb.innerHTML = parts.join('');
  }
}
function syncGuildInputs() {
  const gb = state.guildBuildings || {};
  for (const k of guildBuildingAllKeys()) {
    const el = document.getElementById('gb-building-input-'+k);
    if (el && el !== document.activeElement) el.value = Number(gb[k] || 0);
  }
}
function updateGuildBuilding(key, val) {
  if (!state.guildBuildings) state.guildBuildings = guildBuildingAllKeys().reduce((o,k)=>(o[k]=0,o),{});
  state.guildBuildings[key] = Math.max(0, Math.min(GUILD_BUILDING_MAX_LEVEL, Math.floor(Number(val) || 0)));
  state.guildBuildingsTs = Date.now();
  // 建筑等级是公会全局，随共享数据一起上传
  saveData();
  applyTrialCaps();
  if (state.members && state.members.length > 0 && state.result) calculate(); else { renderTrialCards(); renderMemberTable(); renderSummary(); }
  syncGuildInputs();
}

function loadPrefs() {
  try {
    const lang = localStorage.getItem('mwi_lang');
    if (lang === 'en' || lang === 'zh') state.lang = lang;
    const theme = localStorage.getItem('mwi_theme');
    if (theme === 'dark' || theme === 'light') state.theme = theme;
    const rawGB = localStorage.getItem('mwi_global_buffs');
    if (rawGB) {
      try {
        const obj = JSON.parse(rawGB);
        if (obj && typeof obj === 'object') {
          state.globalBuffs = {
            gathering:      Math.max(0, Number(obj.gathering)      || 0),
            production:     Math.max(0, Number(obj.production)     || 0),
            enhancingSpeed: Math.max(0, Number(obj.enhancingSpeed) || 0),
          };
        }
      } catch(e) {}
    }
  } catch(e) {}
  // 兼容：旧版本曾把公会建筑/神龛存在 localStorage（mwi_guild_buildings / mwi_guild_shrines）。
  // 现在建筑等级随共享数据（bin / 本地 state）一起保存，神龛等级属于成员个人，故只做一次性迁移。
  try {
    const rawGBuild = localStorage.getItem('mwi_guild_buildings');
    if (rawGBuild && (!state.guildBuildingsTs || state.guildBuildingsTs === 0)) {
      const obj = JSON.parse(rawGBuild);
      if (obj && typeof obj === 'object') {
        const keys = guildBuildingAllKeys();
        if (keys.some(k => Number(obj[k]) > 0)) {
          state.guildBuildings = keys.reduce((o,k)=>(o[k]=Math.max(0,Math.floor(Number(obj[k])||0)),o),{});
          state.guildBuildingsTs = Date.now();
        }
      }
    }
    localStorage.removeItem('mwi_guild_shrines');
  } catch(e) {}
  document.documentElement.setAttribute('data-theme', state.theme);
}

// === Skill Picker ===
function openSkillPicker(trialIdx, elem) {
  closeSkillPicker();
  const popup = document.createElement('div');
  popup.className = 'skill-picker-popup';
  popup.id = 'skill-picker-popup';
  const rect = elem.getBoundingClientRect();
  popup.style.left = rect.left + 'px';
  popup.style.top = (rect.bottom + 4) + 'px';
  popup.innerHTML = SKILL_KEYS.map((sk, s) => {
    const sel = state.trials[trialIdx].skill === s ? ' selected' : '';
    return '<div class="skill-option'+sel+'" onclick="selectTrialSkill('+trialIdx+','+s+')" title="'+skillLabel(s)+'">'+svgIcon(sk,32,32)+'</div>';
  }).join('');
  document.body.appendChild(popup);
  setTimeout(() => { document.addEventListener('click', closeSkillPickerOnOutside); }, 0);
}
function closeSkillPicker() {
  const p = document.getElementById('skill-picker-popup');
  if (p) p.remove();
  document.removeEventListener('click', closeSkillPickerOnOutside);
}
function closeSkillPickerOnOutside(e) {
  const p = document.getElementById('skill-picker-popup');
  if (p && !p.contains(e.target)) closeSkillPicker();
}
function selectTrialSkill(trialIdx, skillIdx) {
  state.trials[trialIdx].skill = skillIdx;
  state.trials[trialIdx]._ts = Date.now();
  closeSkillPicker();
  renderTrialCards();
  saveData();
}

// === Equipment Picker ===
function openEquipPicker(memberId, slot) {
  pickerState = { memberId, slot, iconId:null, enhance:0 };
  const person = state.members.find(p => p.id === memberId);
  if (!person) return;
  const existing = person.equipment && person.equipment[slot];
  if (existing) { pickerState.iconId = existing.iconId; pickerState.enhance = existing.enhance || 0; }
  const allIcons = EQUIP_ICONS[slot] || [];
  // 生活装备（上衣/下装/披风/单件生活件）不从这个选择器录入 —— 它们属于「生活装备 · 勾选制」区。
  // 两用槽（项链/耳环/戒指/袋子）走本选择器、且**不排除**任何物品（生活件与战斗件都能选，一槽一件）；
  // 战斗装备 / 生活工具同样走本选择器，但会排除已在生活装备区勾选的同槽位物品，避免重复录入。
  const icons = allIcons.filter(id => !isOwnedFamily(slot, id));
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'equip-picker-overlay';
  overlay.onclick = (e) => { if (e.target === overlay) closeEquipPicker(); };
  let iconGridHtml = icons.map(iconId => {
    const sel = pickerState.iconId === iconId ? ' selected' : '';
    return '<div class="equip-icon-option'+sel+'" data-icon-id="'+iconId+'" onclick="selectEquipIcon(\''+iconId+'\')">'+svgIcon(iconId,32,32)+'<span class="icon-name">'+iconId.replace(/_/g,' ')+'</span></div>';
  }).join('');
  let enhanceBtns = '';
  for (let i = 0; i <= 20; i++) {
    const sel = pickerState.enhance === i ? ' selected' : '';
    enhanceBtns += '<button class="enhance-btn'+sel+'" data-level="'+i+'" onclick="selectEnhanceLevel('+i+')">+'+i+'</button>';
  }
  overlay.innerHTML = '<div class="modal-dialog">'+
    '<div class="modal-title"><span>'+t('selectEquip')+': '+escHtml(equipLabel(EQUIP_TYPES.indexOf(slot)))+'</span><button class="modal-close" onclick="closeEquipPicker()">&times;</button></div>'+
    '<input class="equip-search" type="text" placeholder="'+t('searchEquip')+'" oninput="filterEquipIcons(this.value)">'+
    '<div class="equip-icon-grid" id="equip-icon-grid">'+iconGridHtml+'</div>'+
    '<div><div class="equip-preview-label" style="margin-bottom:4px">'+t('enhanceLevel')+':</div><div class="enhance-selector">'+enhanceBtns+'</div></div>'+
    '<div class="equip-preview" id="equip-preview"></div>'+
    '<div class="modal-actions">'+
      '<button class="btn btn-danger" onclick="clearEquip()">'+t('clear')+'</button>'+
      '<button class="btn" onclick="closeEquipPicker()">'+t('cancel')+'</button>'+
      '<button class="btn btn-primary" onclick="confirmEquip()">'+t('confirm')+'</button>'+
    '</div>'+
  '</div>';
  document.body.appendChild(overlay);
  updateEquipPreview();
}
function closeEquipPicker() {
  const o = document.getElementById('equip-picker-overlay');
  if (o) o.remove();
}
function selectEquipIcon(iconId) {
  pickerState.iconId = iconId;
  document.querySelectorAll('#equip-icon-grid .equip-icon-option').forEach(el => {
    el.classList.toggle('selected', el.dataset.iconId === iconId);
  });
  updateEquipPreview();
}
function selectEnhanceLevel(level) {
  pickerState.enhance = level;
  document.querySelectorAll('.enhance-btn').forEach(el => {
    el.classList.toggle('selected', parseInt(el.dataset.level) === level);
  });
  updateEquipPreview();
}
function updateEquipPreview() {
  const pv = document.getElementById('equip-preview');
  if (!pv) return;
  if (pickerState.iconId) {
    pv.innerHTML = '<div class="equip-cell">'+svgIcon(pickerState.iconId,30,30)+'<span class="enhance-badge">+'+pickerState.enhance+'</span></div><span>'+pickerState.iconId.replace(/_/g,' ')+'</span>';
  } else {
    pv.innerHTML = '<span style="color:var(--text-faint);font-size:12px">'+t('noEquip')+'</span>';
  }
}
function filterEquipIcons(query) {
  const q = query.toLowerCase().trim();
  document.querySelectorAll('#equip-icon-grid .equip-icon-option').forEach(el => {
    const name = el.dataset.iconId.replace(/_/g, ' ');
    const label = el.dataset.name || '';
    const hit = !q || name.toLowerCase().includes(q) || label.toLowerCase().includes(q);
    el.style.display = hit ? '' : 'none';
  });
}
function confirmEquip() {
  if (!pickerState.iconId) { closeEquipPicker(); return; }
  const person = state.members.find(p => p.id === pickerState.memberId);
  if (!person) return;
  if (!person.equipment) person.equipment = {};
  person.equipment[pickerState.slot] = { iconId: pickerState.iconId, enhance: pickerState.enhance };
  person._ts = Date.now();
  closeEquipPicker();
  saveData();
  refreshMemberViews(pickerState.memberId);
}
function clearEquip() {
  const person = state.members.find(p => p.id === pickerState.memberId);
  if (person && person.equipment) { delete person.equipment[pickerState.slot]; person._ts = Date.now(); }
  closeEquipPicker();
  saveData();
  refreshMemberViews(pickerState.memberId);
}

// === 装备「拥有制」：点方格 = 打开强化等级 / 精炼（★）小面板 ===
// 未拥有的方格点一下即以 +0 拥有并打开面板；面板里可设强化等级（+0~+20）、切 ★ 精炼，或「取消拥有」。
// 面板挂在 body 上（position:fixed），不会被弹窗的滚动容器裁掉。
let enhPanelState = null;   // { memberId, slot, base }

function setOwnedEnhValue(memberId, slot, baseId, value) {
  const person = state.members.find(x => x.id === memberId);
  if (!person) return;
  const cur = ownedEntry(person, slot, baseId);
  if (!cur) return;
  setOwnedEntry(person, slot, baseId, clampEnhance(value), cur.refined);
  saveData();
  refreshMemberViews(memberId);
}
function stepOwnedEnh(delta) {
  const st = enhPanelState;
  if (!st) return;
  const person = state.members.find(x => x.id === st.memberId);
  if (!person) return;
  const cur = ownedEntry(person, st.slot, st.base);
  if (!cur) return;
  const next = clampEnhance(cur.enh + delta);
  setOwnedEntry(person, st.slot, st.base, next, cur.refined);
  saveData();
  const inp = document.getElementById('enh-pop-input');
  if (inp) inp.value = String(next);
  refreshMemberViews(st.memberId);
}
function setOwnedRefined(flag) {
  const st = enhPanelState;
  if (!st) return;
  const person = state.members.find(x => x.id === st.memberId);
  if (!person) return;
  const cur = ownedEntry(person, st.slot, st.base);
  if (!cur) return;
  setOwnedEntry(person, st.slot, st.base, cur.enh, !!flag);
  saveData();
  refreshMemberViews(st.memberId);
}
function dropOwnedFromPanel() {
  const st = enhPanelState;
  if (!st) return;
  const person = state.members.find(x => x.id === st.memberId);
  if (person) { clearOwnedEntry(person, st.slot, st.base); saveData(); refreshMemberViews(st.memberId); }
  closeEquipEnhPanel();
}
function openEquipEnhPanel(memberId, slot, baseId, anchor) {
  closeEquipEnhPanel(true);
  const person = state.members.find(x => x.id === memberId);
  if (!person) return;
  normalizeMemberEquip(person);
  const fam = familyOf(slot, baseId);
  if (!fam) return;
  // 锚点位置必须在任何重绘之前取：下面「顺手拥有」会触发 refreshMemberViews，
  // 重绘后传进来的 anchor 已经脱树，getBoundingClientRect() 会全归零（面板会跑到左上角）。
  const anchorRect = (anchor && anchor.getBoundingClientRect) ? anchor.getBoundingClientRect() : null;
  if (ownedEntry(person, slot, baseId) == null) {   // 点正文 = 顺手拥有它，再进面板调数值
    setOwnedEntry(person, slot, baseId, 0, false);
    saveData();
    refreshMemberViews(memberId);
  }
  enhPanelState = { memberId: memberId, slot: slot, base: baseId };
  const cur = ownedEntry(person, slot, baseId) || { enh: 0, refined: false };
  const pop = document.createElement('div');
  pop.className = 'enh-pop';
  pop.id = 'enh-pop';
  pop.onclick = (e) => e.stopPropagation();
  pop.innerHTML =
    '<div class="enh-pop-title">'+escHtml(familyName(baseId, fam.name))
      + ' <span class="enh-pop-slot">'+escHtml(equipLabel(EQUIP_TYPES.indexOf(slot)))+'</span></div>'
    + '<div class="enh-pop-row"><button class="enh-pop-step" onclick="stepOwnedEnh(-1)">&minus;</button>'
    + '<input class="enh-pop-input" id="enh-pop-input" type="number" min="0" max="'+EQUIP_MAX_ENHANCE+'" value="'+cur.enh
      + '" onchange="setOwnedEnhValue('+memberId+',\''+slot+'\',\''+baseId+'\',this.value)">'
    + '<button class="enh-pop-step" onclick="stepOwnedEnh(1)">+</button>'
    + '<span class="enh-pop-unit">+0 ~ +'+EQUIP_MAX_ENHANCE+'</span></div>'
    + (fam.refined
        ? '<label class="enh-pop-star"><input type="checkbox"'+(cur.refined ? ' checked' : '')
          + ' onchange="setOwnedRefined(this.checked)"><span>\u2605 '+escHtml(t('refineToggle'))+'</span></label>'
        : '')
    + '<div class="enh-pop-actions">'
    + '<button class="btn btn-sm btn-danger" onclick="dropOwnedFromPanel()">'+escHtml(t('unownBtn'))+'</button>'
    + '<button class="btn btn-sm btn-primary" onclick="closeEquipEnhPanel()">'+escHtml(t('enhDone'))+'</button>'
    + '</div>';
  document.body.appendChild(pop);
  // 定位：优先贴 chip 下方；越界时回收，尽量不出屏
  const r = (anchorRect && (anchorRect.width || anchorRect.height))
    ? anchorRect : { left: 8, top: 8, bottom: 8, right: 8 };
  const pw = pop.offsetWidth || 214, ph = pop.offsetHeight || 128;
  const vw = window.innerWidth || 1200, vh = window.innerHeight || 800;
  const left = Math.max(8, Math.min(r.left, vw - pw - 8));
  let top = r.bottom + 6;
  if (top + ph > vh - 8) top = Math.max(8, r.top - ph - 6);
  pop.style.left = left + 'px';
  pop.style.top = top + 'px';
  // 「点外部关闭」要延后一帧再挂：触发本次打开的那次 click 还在冒泡，
  // 立刻挂监听会在同一轮事件里就把它关掉（面板闪一下即消失，看起来像「点了没反应」）。
  setTimeout(function(){ document.addEventListener('click', closeEnhPanelOnOutside); }, 0);
}
function closeEnhPanelOnOutside(e) {
  const pop = document.getElementById('enh-pop');
  if (pop && pop.contains && !pop.contains(e.target)) closeEquipEnhPanel();
}
function closeEquipEnhPanel(silent) {
  const pop = document.getElementById('enh-pop');
  if (pop && pop.remove) pop.remove();
  document.removeEventListener('click', closeEnhPanelOnOutside);
  enhPanelState = null;
}

// === Member Management ===
function addMember() {
  const id = state.members.length > 0 ? Math.max(...state.members.map(p=>p.id)) + 1 : 0;
  state.members.push({ id, name: t('addMember'), levels: [0,0,0,0,0,0,0,0,0,0], equipment: {}, _ts: Date.now() });
  renderMemberTable();
  renderSummary();
  saveData();
}
function removeMember(id) {
  state.members = state.members.filter(p => p.id !== id);
  if (!state.deletedIds.includes(id)) state.deletedIds.push(id);
  renderMemberTable();
  renderSummary();
  renderMemberDetailIfOpen(id);
  saveData();
}
function updateMemberName(id, value) {
  const p = state.members.find(p => p.id === id);
  if (p) { p.name = value; p._ts = Date.now(); saveData(); renderMemberDetailIfOpen(id); }
}
function updateSkillLevel(id, skillIdx, value) {
  const p = state.members.find(p => p.id === id);
  if (!p) return;
  p.levels[skillIdx] = Math.max(0, parseInt(value)||0);
  p._ts = Date.now();
  saveData();
  renderMemberDetailIfOpen(id);
}// 成员个人数据（神龛 / 成就 / 房屋）改动后：有分配结果就重算，否则重绘主表；再同步刷新已打开的详情弹窗
function refreshMemberViews(id) {
  if (state.result) calculate(); else { renderMemberTable(); renderSummary(); }
  renderMemberDetailIfOpen(id);
}
// 个人神龛等级（槽位 = <shrine>_skilling / <shrine>_combat，5 座 × 2 = 10 项），逐人可编辑，随共享数据上传
function updateMemberShrine(id, slot, value) {
  const p = state.members.find(p => p.id === id);
  if (!p) return;
  if (!p.shrines) p.shrines = {};
  p.shrines[slot] = Math.max(0, Math.min(GUILD_SHRINE_MAX_LEVEL, Math.floor(Number(value) || 0)));
  p._ts = Date.now();
  saveData();
  refreshMemberViews(id);
}
// 房屋房间等级（17 个房间），逐人可编辑，随共享数据上传
function updateMemberHouseRoom(id, key, value) {
  const p = state.members.find(p => p.id === id);
  if (!p) return;
  if (!p.houseRooms) p.houseRooms = {};
  const cap = (typeof HOUSE_ROOM_MAX_LEVEL !== 'undefined') ? HOUSE_ROOM_MAX_LEVEL : 20;
  p.houseRooms[key] = Math.max(0, Math.min(cap, Math.floor(Number(value) || 0)));
  p._ts = Date.now();
  saveData();
  refreshMemberViews(id);
}
// 成就档位（成员级「个人持久化数据」）：勾选/取消，随共享数据上传
function updateMemberAchievement(id, key, checked) {
  const p = state.members.find(p => p.id === id);
  if (!p) return;
  if (!p.achievements) p.achievements = {};
  p.achievements[key] = !!checked;
  p._ts = Date.now();
  saveData();
  refreshMemberViews(id);
}

// === Calculate ===
function calculate() {
  if (state.members.length === 0) { alert(t('addMembersFirst')); return; }
  const t0 = performance.now();
  applyTrialCaps();   // 试炼人数上限由生活营地等级派生
  state.result = runAssignment(state.members, state.trials);
  state.assignment = state.result.assignment;
  const t1 = performance.now();
  renderAssignmentResults();
  const bar = document.getElementById('summary-bar');
  bar.innerHTML += ' <span style="color:var(--text-faint);font-size:11px">('+(t1-t0).toFixed(0)+'ms)</span>';
}

// === Import ===
function parseMemberFromProfile(profile) {
  if (!profile) return null;
  const name = (profile.sharableCharacter && profile.sharableCharacter.name) || '';
  if (!name) return null;
  // 提取技能等级
  const skillMap = {};
  for (const s of (profile.characterSkills || [])) {
    if (s.skillHrid) {
      const key = s.skillHrid.replace('/skills/', '');
      skillMap[key] = Number(s.level || 0);
    }
  }
  const levels = SKILL_KEYS.map(k => skillMap[k] || 0);
  // 提取装备
  const equipment = {};
  const wearableMap = profile.wearableItemMap || {};
  for (const [loc, item] of Object.entries(wearableMap)) {
    const slot = ITEM_LOCATION_TO_SLOT[loc];
    if (!slot) continue; // 跳过不支持的槽位 (charm, trinket 等)
    const iconId = item.itemHrid ? item.itemHrid.replace('/items/', '') : '';
    const enhance = Number(item.enhancementLevel || 0);
    if (iconId) {
      // 如果该槽位已有装备且当前是 two_hand, 不覆盖 main_hand
      if (slot === '主手' && equipment[slot] && loc === '/item_locations/two_hand') continue;
      equipment[slot] = { iconId, enhance };
    }
  }
  const out = { name, levels, equipment, ownedEquip: {} };
  // 装备「拥有制」：把当前穿戴中、且属于可勾选家族的装备作为「拥有集合」的初值
  // （游戏 profile_shared 只含穿戴中的装备，没有背包，其余拥有项需手工补勾）
  for (const slot of OWNED_SLOTS) {
    out.ownedEquip[slot] = {};
    const eq = equipment[slot];
    if (eq && eq.iconId && isOwnedFamily(slot, eq.iconId)) {
      out.ownedEquip[slot][eq.iconId] = clampEnhance(eq.enhance);
      delete equipment[slot];
    }
  }
  // 逐人加成数据：公会成员导出的是完整 profile，可能携带这些字段（成就/房屋 buff 依赖它们）
  if (profile.achievementsValue) out.achievementsValue = profile.achievementsValue;
  if (profile.achievementActionTypeBuffsDict) out.achievementActionTypeBuffsDict = profile.achievementActionTypeBuffsDict;
  // 成就档位：物化成成员级可编辑的「个人持久化数据」（随共享上传，勾选后为权威值）。
  // 共享资料里成就常见为数组 characterAchievements（[{achievementHrid,isCompleted}]），由 materialize 统一归一化；
  // 原始全表不保留（80 人 × 上百条会显著撑大共享载荷），只留影响试炼的 Beginner/Adept 两档。
  out.achievements = materializeMemberAchievements(profile);
  if (profile.houseActionTypeBuffsDict) out.houseActionTypeBuffsDict = profile.houseActionTypeBuffsDict;
  if (profile.houseRoomLevels) out.houseRoomLevels = profile.houseRoomLevels;
  if (profile.characterHouseRoomMap) out.characterHouseRoomMap = profile.characterHouseRoomMap;
  // 房屋房间等级：物化成成员级可编辑的 houseRooms（个人持久化数据，随共享上传）
  out.houseRooms = materializeMemberHouseRooms(profile);
  // 个人神龛增益等级：共享资料里带 guildBuffLevelMap（键 /guild_buffs/<shrine>_skilling 或 _combat）。
  // 每座神龛拆成 生活/战斗 两个槽位，直接物化成可编辑的 shrines 字段（同时保留原始 map 以便对照）。
  out.shrines = {};
  const gmap = profile.guildBuffLevelMap;
  if (gmap) out.guildBuffLevels = gmap;
  for (const s of shrineSlotsList()) {
    let lv = 0;
    if (gmap) {
      const key = s.buffHrid || ('/guild_buffs/' + s.slot);
      if (gmap[key] != null) lv = Math.floor(Number(gmap[key]) || 0);
    }
    out.shrines[s.slot] = Math.max(0, Math.min(GUILD_SHRINE_MAX_LEVEL, lv));
  }
  // 公会建筑等级（公会全局）：导出脚本可能把 guild_updated 里的 guildBuildingLevelMap 挂在成员对象上
  if (profile._guildBuildingLevelMap) out._guildBuildingLevelMap = profile._guildBuildingLevelMap;
  if (profile.guildBuildingLevelMap) out._guildBuildingLevelMap = profile.guildBuildingLevelMap;
  return out;
}
// === Import / Export ===
// 本计算器自己的备份格式标记：导入时据此区分「计算器备份」与「游戏成员 profile 数组」。
const EXPORT_FORMAT = 'mwi-trial-calculator';
const EXPORT_FORMAT_VERSION = 1;

function downloadJSON(filename, data) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(function(){ document.body.removeChild(a); URL.revokeObjectURL(url); }, 200);
}

// 组装导出用的完整备份对象（纯函数：便于测试与复用）。
function buildExportDump() {
  return Object.assign({
    _format: EXPORT_FORMAT,
    _version: EXPORT_FORMAT_VERSION,
    exportedAt: new Date().toISOString(),
  }, sharedPayload());
}

// 导出当前全部数据（成员 / 试炼 / 公会建筑 / 公会名）为 JSON —— 可直接用「导入」按钮还原。
function exportJson() {
  const members = Array.isArray(state.members) ? state.members : [];
  if (!members.length) { alert(t('exportEmpty')); return; }
  const safeGuild = String(state.guild || 'guild').replace(/[\\/:*?"<>|]/g, '_');
  const dateStr = new Date().toISOString().slice(0, 10);
  downloadJSON('MWI试炼_' + safeGuild + '_' + members.length + '人_' + dateStr + '.json', buildExportDump());
}

// 判断一份已解析的 JSON 是不是「本计算器的备份」。
// 认两种写法：① 带 _format 标记；② 直接形如 sharedPayload（含 members 数组）——
// 方便把共享 bin 里的裸载荷直接拷出来导入。
function isCalculatorDump(obj) {
  return !!obj && !Array.isArray(obj) && (obj._format === EXPORT_FORMAT || Array.isArray(obj.members));
}

// 还原单个成员：备份里的成员已是计算器结构，这里只补齐字段 / 夹取取值范围（幂等）。
function restoreMemberDump(m) {
  if (!m || typeof m !== 'object') m = {};
  const out = Object.assign({}, m);
  out.name = String(m.name || '');
  const lv = Array.isArray(m.levels) ? m.levels : [];
  out.levels = SKILL_KEYS.map(function(_, i){ return Math.max(0, Math.floor(Number(lv[i]) || 0)); });
  out.equipment = (m.equipment && typeof m.equipment === 'object') ? m.equipment : {};
  out.ownedEquip = (m.ownedEquip && typeof m.ownedEquip === 'object') ? m.ownedEquip : {};
  if (!out.shrines || typeof out.shrines !== 'object') out.shrines = {};
  if (!out.houseRooms || typeof out.houseRooms !== 'object') out.houseRooms = {};
  if (!out.achievements || typeof out.achievements !== 'object') out.achievements = {};
  out._ts = Date.now();
  return out;
}

// 用「计算器备份」整体还原状态。返回 null 表示这份数据不是备份。
function importCalculatorDump(dump) {
  const src = (dump && dump.payload && typeof dump.payload === 'object') ? dump.payload : dump;
  const rawMembers = (src && Array.isArray(src.members)) ? src.members : null;
  if (!rawMembers) return null;
  // 公会名只在本地还没有时采用 —— 避免导入别人的备份时把当前共享空间的公会名改掉
  if (src.guild && !state.guild) state.guild = String(src.guild);
  state.members = rawMembers.map(restoreMemberDump);
  state.members.forEach(function(m, i){ m.id = i; });
  if (Array.isArray(src.trials) && src.trials.length) {
    state.trials = src.trials.map(function(x){ return Object.assign({}, x); });
  }
  state.deletedIds = Array.isArray(src.deletedIds) ? src.deletedIds.slice() : [];
  if (src.guildBuildings && typeof src.guildBuildings === 'object') {
    const next = guildBuildingAllKeys().reduce(function(o,k){ o[k]=0; return o; }, {});
    for (const k of Object.keys(next)) {
      if (src.guildBuildings[k] != null) {
        next[k] = Math.max(0, Math.min(GUILD_BUILDING_MAX_LEVEL, Math.floor(Number(src.guildBuildings[k]) || 0)));
      }
    }
    state.guildBuildings = next;
    state.guildBuildingsTs = Number(src.guildBuildingsTs) || Date.now();
  }
  applyTrialCaps();
  state.members.forEach(normalizeMemberEquip);
  return { count: state.members.length };
}

// 导入后落盘：共享模式下立即全量覆盖 bin（不走合并，防止被旧数据覆盖），否则只写本地。
async function persistAfterImport() {
  const data = JSON.stringify(sharedPayload());
  try { localStorage.setItem(getStorageKey(), data); } catch(e) {}
  if (state.isShared && state.binId && state.encKey) {
    await forcePushToBin(data);
  } else {
    saveData();
  }
}

// === 合并导入（游戏成员 profile 数组）===
// 旧行为是「整体替换 state.members」，会把成员手动补的数据一把冲掉 —— 尤其是游戏导出
// 根本不包含的「装备拥有集合」（profile_shared 只有当前穿戴的 24 件，没有背包）。
// 现在按角色名合并：
//   · 同名成员 → 游戏权威字段（等级 / 配装槽 / 神龛 / 房屋 / 成就 / 原始 dict）用采集值更新；
//                装备拥有集合取并集 —— 手动勾的保留，采集到的新穿戴装备补进来。
//   · 采集里没有的名字 → 作为新成员追加。
//   · 本地有、采集里没有的成员（手动加的人 / 已退会的人）→ 原样保留，一个都不删。

// 拥有集合并集：本地已有同家族的（普通款与 ★ 精炼款在游戏里互斥，只认一个）一律保留本地；
// 其余用采集值补进来并夹取强化范围。
function mergeOwnedEquip(local, remote) {
  const out = {};
  for (const slot of Object.keys(local || {})) out[slot] = Object.assign({}, local[slot]);
  for (const slot of Object.keys(remote || {})) {
    if (!out[slot]) out[slot] = {};
    const fams = {};
    for (const k of Object.keys(out[slot])) fams[iconBaseId(k)] = true;
    const src = remote[slot] || {};
    for (const k of Object.keys(src)) {
      const base = iconBaseId(k);
      if (fams[base]) continue;          // 同家族本地已有 → 保留本地的（不覆盖、不并存）
      out[slot][k] = clampEnhance(src[k]);
      fams[base] = true;
    }
  }
  return out;
}

// 用一条新采集的 profile 更新已有成员（就地修改并返回 old）
function mergeMemberFresh(old, fresh) {
  const owned = mergeOwnedEquip(old.ownedEquip, fresh.ownedEquip);
  Object.assign(old, fresh);   // 游戏权威字段整体覆盖（fresh 里没有 id / _ts，不受影响）
  old.ownedEquip = owned;      // 拥有集合 = 并集（手动补的不能丢）
  old._ts = Date.now();
  return old;
}

// 把采集到的 profile 数组合并进当前名单，返回统计 { updated, added, kept }；无有效成员时返回 null。
function mergeMembersFromProfiles(profiles) {
  if (!Array.isArray(profiles)) profiles = [profiles];
  const byName = {};
  for (const m of state.members) {
    const k = String(m.name || '').trim();
    if (k && byName[k] === undefined) byName[k] = m;
  }
  const usedIds = {};
  const seen = {};
  const added = [];
  let updated = 0;
  let nextId = 0;
  for (const m of state.members) nextId = Math.max(nextId, (Number(m.id) || 0) + 1);
  for (const profile of profiles) {
    const fresh = parseMemberFromProfile(profile);
    if (!fresh) continue;
    const k = String(fresh.name || '').trim();
    if (seen[k]) continue;               // 采集数据里同一个人出现多次 → 只取第一条
    seen[k] = true;
    const old = k ? byName[k] : undefined;
    if (old && !usedIds[old.id]) {
      mergeMemberFresh(old, fresh);      // 已存在 → 更新（并保留手动补的拥有集合）
      usedIds[old.id] = true;
      updated++;
    } else {
      fresh.id = nextId++;
      fresh._ts = Date.now();
      added.push(fresh);                 // 新成员 → 追加
    }
  }
  if (!updated && !added.length) return null;
  const kept = state.members.filter(function(m){ return !usedIds[m.id]; }).length;
  state.members = state.members.concat(added);
  return { updated: updated, added: added.length, kept: kept };
}

function importJson() {
  const input = document.createElement('input');
  input.type = 'file'; input.accept = '.json';
  input.onchange = () => {
    const file = input.files[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      let parsed;
      try { parsed = JSON.parse(reader.result); }
      catch(e) { alert('JSON parse error: ' + e.message); return; }

      // ① 本计算器导出的完整备份 → 整体还原（成员 / 试炼 / 公会建筑 / 公会名）
      if (isCalculatorDump(parsed)) {
        const res = importCalculatorDump(parsed);
        if (!res) { alert(t('importFailed')); return; }
        await persistAfterImport();
        renderAll();
        if (state.members.length > 0) calculate();
        alert(t('importSuccess')+': '+res.count);
        return;
      }

      // ② 游戏导出的成员 profile 数组 → 按角色名「合并」进现有名单（不再整体替换）
      if (!Array.isArray(parsed)) { alert(t('importFormatUnknown')); return; }
      const stat = mergeMembersFromProfiles(parsed);
      if (!stat) { alert(t('importFailed')); return; }
      state.deletedIds = [];                      // 本端名单只增不减，历史删除标记已无意义
      applyImportedGuildBuildings(parsed);        // 若导出数据带公会建筑等级（guild_updated），自动预填
      applyTrialCaps();
      await persistAfterImport();
      renderAll();
      if (state.members.length > 0) calculate();
      alert(tplFill(t('importMergeReport'), { upd: stat.updated, add: stat.added, keep: stat.kept }));
    };
    reader.readAsText(file, 'UTF-8');
  };
  input.click();
}

// 导出数据里若带公会建筑等级（/guild_buildings/* 键 = 建筑 hrid），自动预填到 state.guildBuildings
function applyImportedGuildBuildings(profiles) {
  if (!Array.isArray(profiles)) profiles = [profiles];
  const keys = guildBuildingAllKeys();
  const hmap = (typeof GUILD_BUILDING_HRID_TO_KEY !== 'undefined') ? GUILD_BUILDING_HRID_TO_KEY : {};
  for (const prof of profiles) {
    const map = prof && (prof._guildBuildingLevelMap || prof.guildBuildingLevelMap || prof.guildBuildingLevelDict);
    if (!map || typeof map !== 'object') continue;
    const next = keys.reduce((o,k)=>(o[k]=0,o),{});
    let any = false;
    for (const [hrid, lv] of Object.entries(map)) {
      const base = String(hrid).replace('/guild_buildings/', '').replace('guild_', '');
      const key = hmap[base] || (next[base] !== undefined ? base : null);
      if (!key || next[key] === undefined) continue;
      const v = Math.max(0, Math.min(GUILD_BUILDING_MAX_LEVEL, Math.floor(Number(lv) || 0)));
      next[key] = v;
      if (v > 0) any = true;
    }
    if (any) { state.guildBuildings = next; state.guildBuildingsTs = Date.now(); return true; }
  }
  return false;
}


// === Data Persistence ===
function getStorageKey() { return 'mwi_trial_'+(state.guild||'default'); }
// 共享/持久化的统一载荷：成员（含个人神龛）+ 试炼槽 + 公会建筑（公会全局）等
function sharedPayload() {
  return {
    guild: state.guild,
    members: state.members,
    trials: state.trials,
    deletedIds: state.deletedIds,
    guildBuildings: state.guildBuildings || {},
    guildBuildingsTs: state.guildBuildingsTs || 0
  };
}
function saveData() {
  const data = JSON.stringify(sharedPayload());
  try { localStorage.setItem(getStorageKey(), data); } catch(e) {}
  if (state.isShared && state.binId && state.encKey) saveToBin(data);
}
function loadData() {
  try {
    const raw = localStorage.getItem(getStorageKey());
    if (raw) {
      Object.assign(state, JSON.parse(raw));
      if (!Array.isArray(state.deletedIds)) state.deletedIds = [];
      if (!state.guildBuildings) state.guildBuildings = guildBuildingAllKeys().reduce((o,k)=>(o[k]=0,o),{});
      if (!state.guildBuildingsTs) state.guildBuildingsTs = 0;
      return true;
    }
  } catch(e) {}
  return false;
}

// === jsonbin.io ===
const BIN_BASE = 'https://api.jsonbin.io/v3/b';
// 固定的分享加密密码：历史 bin 均用此密码加密，保留以保证兼容现有数据，且不写入分享 URL
const SHARE_PASSWORD = 'layu';
let saveTimer = null;
let isSaving = false;
function saveToBin(data) {
  clearTimeout(saveTimer);
  saveTimer = setTimeout(async () => {
    if (isSaving) { saveTimer = setTimeout(()=>saveToBin(data), 3000); return; }
    isSaving = true;
    try {
      const localData = JSON.parse(data);
      const mk = localStorage.getItem('mwi_master_key') || '';
      // Fetch latest from bin for merge
      let merged = localData;
      try {
        const rHeaders = mk ? {'X-Master-Key':mk} : {};
        const resp = await fetch(BIN_BASE+'/'+state.binId+'/latest', { headers:rHeaders });
        if (resp.ok) {
          const json = await resp.json();
          if (json.record && json.record.d) {
            const dec = await decryptRecord(json.record, state.encKey);
            const remote = JSON.parse(dec);
            merged = mergeState(localData, remote);
          }
        }
      } catch(e) { console.warn('Merge fetch failed, saving without merge:', e); }
      // Encrypt and PUT merged data
      const dataToSave = JSON.stringify(merged);
      const rec = await encryptRecord(dataToSave, state.encKey);
      const pHeaders = {'Content-Type':'application/json'};
      if (mk) pHeaders['X-Master-Key'] = mk;
      await fetch(BIN_BASE+'/'+state.binId, {
        method:'PUT', headers:pHeaders,
        body: JSON.stringify(rec)
      });
      // Sync merged result back to local state (picks up others' changes)
      state.members = merged.members;
      state.trials = merged.trials;
      state.deletedIds = merged.deletedIds || [];
      if (merged.guildBuildings) state.guildBuildings = merged.guildBuildings;
      state.guildBuildingsTs = merged.guildBuildingsTs || state.guildBuildingsTs || 0;
    } catch(e) { console.error('Save failed:', e); }
    isSaving = false;
  }, 2000);
}
// 导入等场景：立即全量覆盖 bin，不做合并，确保本地数据成为权威版本，避免被旧数据覆盖
async function forcePushToBin(data) {
  try {
    clearTimeout(saveTimer);
    const mk = localStorage.getItem('mwi_master_key') || '';
    const rec = await encryptRecord(data, state.encKey);
    const pHeaders = { 'Content-Type':'application/json' };
    if (mk) pHeaders['X-Master-Key'] = mk;
    await fetch(BIN_BASE+'/'+state.binId, { method:'PUT', headers:pHeaders, body: JSON.stringify(rec) });
    const parsed = JSON.parse(data);
    state.members = parsed.members;
    state.trials = parsed.trials;
    state.deletedIds = parsed.deletedIds || [];
    if (parsed.guildBuildings) state.guildBuildings = parsed.guildBuildings;
    state.guildBuildingsTs = parsed.guildBuildingsTs || state.guildBuildingsTs || 0;
  } catch(e) { console.error('Force push failed:', e); }
}

function mergeState(local, remote) {
  if (!remote || !remote.members) return local;
  // 合并删除标记（墓碑），确保某端删除的成员不会在合并时被远端重新加回
  const del = new Set([...(local.deletedIds||[]), ...(remote.deletedIds||[])]);
  const localMembers = local.members.filter(p => !del.has(p.id));
  // Build remote member map (排除已删除)
  const rMap = {};
  remote.members.forEach(p => { if (!del.has(p.id)) rMap[p.id] = p; });
  // Merge: for each local member, if remote has newer _ts, take remote
  const mergedMembers = localMembers.map(p => {
    const r = rMap[p.id];
    if (r && r._ts && (!p._ts || r._ts > p._ts)) return r;
    return p;
  });
  // Add remote members not present locally (added by others)，且非已删除
  const localIds = new Set(localMembers.map(p => p.id));
  remote.members.forEach(p => { if (!localIds.has(p.id) && !del.has(p.id)) mergedMembers.push(p); });
  // Merge trials by _ts
  const mergedTrials = local.trials.map((trial, i) => {
    const r = remote.trials && remote.trials[i];
    if (r && r._ts && (!trial._ts || r._ts > trial._ts)) return r;
    return trial;
  });
  // 公会建筑是「公会全局」，按时间戳取新（谁最后改的以谁为准）
  const lTs = local.guildBuildingsTs || 0, rTs = remote.guildBuildingsTs || 0;
  const mergedGB = (rTs > lTs && remote.guildBuildings) ? remote.guildBuildings : (local.guildBuildings || remote.guildBuildings || {});
  const mergedGBTs = Math.max(lTs, rTs);
  return { guild: local.guild || remote.guild, members: mergedMembers, trials: mergedTrials, deletedIds: [...del],
           guildBuildings: mergedGB, guildBuildingsTs: mergedGBTs };
}
async function loadFromBin() {
  try {
    const mk = localStorage.getItem('mwi_master_key') || '';
    const headers = mk ? {'X-Master-Key':mk} : {};
    const resp = await fetch(BIN_BASE+'/'+state.binId+'/latest', { headers });
    if (!resp.ok) {
      console.error('Load HTTP', resp.status);
      return false;
    }
    const json = await resp.json();
    if (json.record && json.record.d) {
      const dec = await decryptRecord(json.record, state.encKey);
      const data = JSON.parse(dec);
      Object.assign(state, data);
      if (!Array.isArray(state.deletedIds)) state.deletedIds = [];
      if (!state.guildBuildings) state.guildBuildings = {};
      if (!state.guildBuildingsTs) state.guildBuildingsTs = 0;
      return true;
    }
  } catch(e) { console.error('Load failed:', e); }
  return false;
}
async function createBin(guild, password, masterKey) {
  const encKey = await deriveKey(password, guild);
  const data = JSON.stringify(Object.assign(sharedPayload(), { guild }));
  const rec = await encryptRecord(data, encKey);
  const resp = await fetch(BIN_BASE, {
    method:'POST',
    headers:{'Content-Type':'application/json','X-Master-Key':masterKey,'X-Bin-Name':'MWI_'+guild,'X-Bin-Private':'false'},
    body: JSON.stringify(rec)
  });
  const json = await resp.json();
  if (!resp.ok) throw new Error('jsonbin '+resp.status+': '+(json && json.message ? json.message : resp.statusText));
  return json.metadata ? json.metadata.id : null;
}

// === Compression (gzip) ===
// Returns gzipped bytes, or the input unchanged if CompressionStream is unavailable (older browsers).
async function gzipBytes(bytes) {
  if (typeof CompressionStream === 'undefined') return bytes;
  const cs = new CompressionStream('gzip');
  const writer = cs.writable.getWriter();
  writer.write(bytes); writer.close();
  const ab = await new Response(cs.readable).arrayBuffer();
  return new Uint8Array(ab);
}
async function gunzipBytes(bytes) {
  if (typeof DecompressionStream === 'undefined') return bytes;
  const ds = new DecompressionStream('gzip');
  const writer = ds.writable.getWriter();
  writer.write(bytes); writer.close();
  const ab = await new Response(ds.readable).arrayBuffer();
  return new Uint8Array(ab);
}

// === Crypto ===
async function deriveKey(password, salt) {
  const enc = new TextEncoder();
  const keyMaterial = await crypto.subtle.importKey('raw', enc.encode(password), 'PBKDF2', false, ['deriveKey']);
  return crypto.subtle.deriveKey({name:'PBKDF2',salt:enc.encode(salt),iterations:100000,hash:'SHA-256'}, keyMaterial, {name:'AES-GCM',length:256}, false, ['encrypt','decrypt']);
}
// Chunked base64 to avoid call-stack overflow on large payloads
function bytesToBase64(bytes) {
  let bin = '';
  const chunk = 0x8000;
  for (let i = 0; i < bytes.length; i += chunk) {
    bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
  }
  return btoa(bin);
}
function base64ToBytes(b64) {
  const bin = atob(b64);
  const bytes = new Uint8Array(bin.length);
  for (let i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
  return bytes;
}
async function encryptBytes(bytes, key) {
  const iv = crypto.getRandomValues(new Uint8Array(12));
  const ct = await crypto.subtle.encrypt({name:'AES-GCM',iv}, key, bytes);
  const combined = new Uint8Array(iv.length + ct.byteLength);
  combined.set(iv); combined.set(new Uint8Array(ct), iv.length);
  return bytesToBase64(combined);
}
async function decryptBytes(b64, key) {
  const combined = base64ToBytes(b64);
  const iv = combined.slice(0, 12); const ct = combined.slice(12);
  return new Uint8Array(await crypto.subtle.decrypt({name:'AES-GCM',iv}, key, ct));
}
// gzip + encrypt. Always compressed. Returns { d }.
async function encryptRecord(text, key) {
  const bytes = new TextEncoder().encode(text);
  const gz = await gzipBytes(bytes);
  const d = await encryptBytes(gz, key);
  return { d };
}
// Decrypt + gunzip. Returns the original JSON string.
async function decryptRecord(rec, key) {
  const bytes = await decryptBytes(rec.d, key);
  const gz = await gunzipBytes(bytes);
  return new TextDecoder().decode(gz);
}

// === Share Dialog ===
function openShareDialog() {
  const overlay = document.createElement('div');
  overlay.className = 'modal-overlay';
  overlay.id = 'share-overlay';
  overlay.onclick = (e) => { if (e.target === overlay) closeShareDialog(); };
  const storedKey = localStorage.getItem('mwi_master_key') || '';
  overlay.innerHTML = '<div class="modal-dialog" style="max-width:440px">'+
    '<div class="modal-title"><span>'+t('share')+'</span><button class="modal-close" onclick="closeShareDialog()">&times;</button></div>'+
    '<div class="share-field"><label>'+t('guildName')+'</label><input type="text" id="share-guild" value="'+escHtml(state.guild)+'" placeholder="MWI"></div>'+
    '<div class="share-field"><label>'+t('masterKey')+'</label><input type="text" id="share-masterkey" value="'+escHtml(storedKey)+'" placeholder="jsonbin.io"></div>'+
    '<div style="font-size:11px;color:var(--text-muted);margin:8px 0">'+t('shareHint')+'</div>'+
    (state.binId ? '<div class="share-field"><label>'+t('currentUrl')+'</label><div class="share-url" onclick="copyShareUrl()">'+escHtml(getShareUrl())+'</div></div>' : '')+
    '<div class="modal-actions">'+
      '<button class="btn" onclick="closeShareDialog()">'+t('closeBtn')+'</button>'+
      (state.binId ? '' : '<button class="btn btn-primary" onclick="createShare()">'+t('createShare')+'</button>')+
    '</div>'+
  '</div>';
  document.body.appendChild(overlay);
}
function closeShareDialog() { const o = document.getElementById('share-overlay'); if (o) o.remove(); }
function getShareUrl() {
  const url = new URL(window.location.href);
  url.searchParams.set('guild', state.guild);
  url.searchParams.set('bin', state.binId);
  // 密码已固定为常量 SHARE_PASSWORD，不写入 URL（现有 bin 兼容）
  // if (mk) url.searchParams.set('mk', mk);
  return url.toString();
}
function copyShareUrl() {
  navigator.clipboard.writeText(getShareUrl()).then(() => alert(t('linkCopied')));
}
async function createShare() {
  const guild = document.getElementById('share-guild').value.trim();
  const masterKey = document.getElementById('share-masterkey').value.trim();
  if (!guild || !masterKey) { alert(t('fillAll')); return; }
  try {
    localStorage.setItem('mwi_master_key', masterKey);
    state.guild = guild;
    const binId = await createBin(guild, SHARE_PASSWORD, masterKey);
    if (!binId) { alert(t('createFailed')); return; }
    state.binId = binId;
    state.encKey = await deriveKey(SHARE_PASSWORD, guild);
    state.isShared = true;
    saveData();
    closeShareDialog();
    openShareDialog();
    updateConnectionStatus();
    alert(t('shareCreated'));
  } catch(e) { alert(t('createFailed')+': '+e.message); }
}
function updateConnectionStatus() {
  const el = document.getElementById('conn-status');
  const refreshBtn = document.getElementById('btn-refresh');
  if (state.isShared) {
    el.textContent = t('connected')+': '+state.guild;
    if (refreshBtn) refreshBtn.style.display = '';
  } else {
    el.textContent = t('offlineMode');
    if (refreshBtn) refreshBtn.style.display = 'none';
  }
}

async function refreshFromServer() {
  if (!state.isShared || !state.binId) return;
  clearTimeout(saveTimer);
  const ok = await loadFromBin();
  if (ok) {
    renderAll();
    if (state.members.length > 0) calculate();
  }
}

// === Init ===
async function init() {
  loadPrefs();
  renderGuildInputs();
  const params = new URLSearchParams(window.location.search);
  const guild = params.get('guild');
  const bin = params.get('bin');
  const mk = params.get('mk');
  if (mk) localStorage.setItem('mwi_master_key', mk);
  if (guild && bin) {
    state.guild = guild; state.binId = bin; state.isShared = true;
    state.encKey = await deriveKey(SHARE_PASSWORD, guild);
    let loadedFromShare = await loadFromBin();
    updateConnectionStatus();
    if (!state.trials) state.trials = [{skill:0,max:20},{skill:1,max:20},{skill:2,max:20},{skill:3,max:20}];
    applyTrialCaps();
    renderAll();
    if (loadedFromShare && state.members.length > 0) calculate();
  } else {
    loadData();
    if (!state.trials) state.trials = [{skill:0,max:20},{skill:1,max:20},{skill:2,max:20},{skill:3,max:20}];
    applyTrialCaps();
    renderAll();
  }
}
init();
'''

# ============================================================
# HTML Template
# ============================================================

HTML = r'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>MWI 试炼计算器</title>
<style>
__CSS__
</style>
</head>
<body>
__SVG_SYMBOLS__

<div class="header">
  <div class="header-left">
    <h1 id="h1-title">MWI 试炼计算器</h1>
    <span class="connection-status" id="conn-status">离线模式</span>
  </div>
  <div class="header-right">
    <button class="btn btn-icon" id="btn-lang" onclick="toggleLang()">中/EN</button>
    <button class="btn btn-icon" id="btn-theme" onclick="toggleTheme()">🌙</button>
    <button class="btn" id="btn-refresh" onclick="refreshFromServer()" style="display:none">🔄</button>
    <button class="btn" id="btn-share" onclick="openShareDialog()">共享设置</button>
    <button class="btn" id="btn-import-json" onclick="importJson()">导入</button>
    <button class="btn" id="btn-export-json" onclick="exportJson()">导出</button>
    <a href="mwi_data_export.user.js" download class="btn btn-sm" id="export-script-link" style="font-size:12px;padding:4px 8px;opacity:.6" title="">📦</a>
    <button class="btn btn-primary" id="btn-calculate" onclick="calculate()">计算最优分配</button>
  </div>
</div>

<div class="global-buff-section">
  <h3 id="h3-global-buff">全局加成 <span class="global-buff-hint" id="global-buff-hint" title=""></span></h3>
  <div class="global-buff-bar">
    <label class="global-buff-item" title="">
      <svg class="global-buff-icon" viewBox="0 0 40 40"><use xlink:href="#gathering"></use></svg>
      <span class="global-buff-label" id="gb-lbl-gathering">采集数量</span>
      <input type="number" min="0" max="20" step="1" id="gb-input-gathering" onchange="updateGlobalBuff('gathering', this.value)">
      <span class="global-buff-unit" id="gb-unit-gathering">级</span>
    </label>
    <label class="global-buff-item" title="">
      <svg class="global-buff-icon" viewBox="0 0 40 40"><use xlink:href="#efficiency"></use></svg>
      <span class="global-buff-label" id="gb-lbl-production">生产效率</span>
      <input type="number" min="0" max="20" step="1" id="gb-input-production" onchange="updateGlobalBuff('production', this.value)">
      <span class="global-buff-unit" id="gb-unit-production">级</span>
    </label>
    <label class="global-buff-item" title="">
      <svg class="global-buff-icon" viewBox="0 0 40 40"><use xlink:href="#action_speed"></use></svg>
      <span class="global-buff-label" id="gb-lbl-enhancingSpeed">强化速度</span>
      <input type="number" min="0" max="20" step="1" id="gb-input-enhancingSpeed" onchange="updateGlobalBuff('enhancingSpeed', this.value)">
      <span class="global-buff-unit" id="gb-unit-enhancingSpeed">级</span>
    </label>
  </div>
  <h3 id="h3-guild-buildings">公会建筑 <span class="global-buff-hint" id="guild-buildings-hint" title=""></span> <span class="global-buff-subhint" id="guild-buildings-shared"></span></h3>
  <div class="global-buff-bar is-stacked" id="guild-buildings-bar"></div>
</div>

<div class="trial-section">
  <h2 id="h2-trial">试炼配置</h2>
  <div class="trial-cards" id="trial-cards"></div>
</div>

<div class="member-section">
  <h2 id="h2-member">成员数据 <span class="global-buff-hint" id="member-hint" title=""></span> <button class="btn btn-sm" id="btn-add-member" onclick="addMember()">+ 添加成员</button></h2>
  <div class="table-wrap">
    <table class="member-table">
      <thead id="member-thead"></thead>
      <tbody id="member-tbody"></tbody>
    </table>
  </div>
</div>

<div class="summary-bar" id="summary-bar"></div>

<script>
__JS__
</script>
</body>
</html>'''

# ============================================================
# Main
# ============================================================

def main():
    # Read items.svg
    with open(os.path.join(BASE_DIR, 'items.svg'), 'r', encoding='utf-8') as f:
        svg_content = f.read()

    all_ids = re.findall(r'<symbol[^>]*id="([^"]+)"', svg_content)
    print(f'Total symbols in items.svg: {len(all_ids)}')

    # Categorize equipment using equip.json (authoritative) + ITEM_NAME_MAP
    equip_json_path = os.path.join(BASE_DIR, 'equip.json')
    with open(equip_json_path, 'r', encoding='utf-8') as f:
        equip_data = json.load(f)
    categorized = {}
    for slot, names in equip_data.items():
        # 双手武器合并到主手 (双手武器占主手槽, 装备时不能装副手)
        target_slot = '主手' if slot == '双手' else slot
        icon_ids = categorized.setdefault(target_slot, [])
        for name in names:
            if name.endswith(' ★'):
                base = name[:-2]
                base_icon = ITEM_NAME_MAP.get(base)
                if base_icon:
                    icon_ids.append(base_icon + '_refined')
                else:
                    print(f'  WARNING: no base mapping for "{name}" (base: "{base}")')
            else:
                icon_id = ITEM_NAME_MAP.get(name)
                if icon_id:
                    icon_ids.append(icon_id)
                else:
                    print(f'  WARNING: no mapping for "{name}"')

    # Read skills_sprite.svg for pure skill icons
    skills_sprite_path = os.path.join(BASE_DIR, 'skills_sprite.svg')
    skill_symbols = []
    if os.path.exists(skills_sprite_path):
        with open(skills_sprite_path, 'r', encoding='utf-8') as f:
            sprite_content = f.read()
        skill_ids = re.findall(r'<symbol[^>]*id="([^"]+)"', sprite_content)
        print(f'Skill icons in skills_sprite.svg: {len(skill_ids)} -> {skill_ids}')
        for sid in skill_ids:
            sym = extract_symbol(sprite_content, sid)
            if sym:
                skill_symbols.append(sym)
    else:
        print('WARNING: skills_sprite.svg not found, using _essence icons from items.svg as fallback')
        for k in SKILL_KEYS:
            sym = extract_symbol(svg_content, k + '_essence')
            if sym:
                # Rename to remove _essence suffix
                sym = sym.replace('id="' + k + '_essence"', 'id="' + k + '"')
                skill_symbols.append(sym)

    # Collect all equipment IDs to extract from items.svg
    all_extract = set()
    for cat, sids in categorized.items():
        all_extract.update(sids)

    # Extract equipment symbols from items.svg
    equip_symbols = []
    for sid in sorted(all_extract):
        sym = extract_symbol(svg_content, sid)
        if sym:
            equip_symbols.append(sym)
        else:
            print(f'  WARNING: could not extract symbol for {sid}')

    # Read buffs_sprite.svg for global buff icons (gathering / efficiency / action_speed)
    buffs_sprite_path = os.path.join(BASE_DIR, 'buffs_sprite.svg')
    buff_symbols = []
    if os.path.exists(buffs_sprite_path):
        with open(buffs_sprite_path, 'r', encoding='utf-8') as f:
            buff_content = f.read()
        for bid in ['gathering', 'efficiency', 'action_speed']:
            sym = extract_symbol(buff_content, bid)
            if sym:
                buff_symbols.append(sym)
            else:
                print(f'  WARNING: buff symbol not found: {bid}')
    else:
        print('WARNING: buffs_sprite.svg not found, global buff icons will be missing')

    # Read guild_sprite.svg for guild building / shrine icons
    guild_sprite_path = os.path.join(BASE_DIR, 'guild_sprite.svg')
    guild_symbols = []
    _gb = GAME_DATA.get('guildBuilding', {}) or {}
    _gs = GAME_DATA.get('guildShrine', {}) or {}
    # 全部 23 建筑（6 功能 + 17 试炼）+ 5 神龛的图标（顺序：功能建筑 → 试炼建筑 → 神龛）
    _guild_ids = ([u.get('icon') for u in _gb.get('utility', [])]
                  + [td.get('icon') for td in _gb.get('trial', [])]
                  + [d.get('icon') for d in _gs.get('defs', [])])
    if not _guild_ids:
        _guild_ids = list((_gb.get('icons', {}) or {}).values()) + list((_gs.get('icons', {}) or {}).values())
    _guild_ids = [x for x in _guild_ids if x]
    guild_icon_ids = set(_guild_ids)
    if os.path.exists(guild_sprite_path):
        with open(guild_sprite_path, 'r', encoding='utf-8') as f:
            guild_content = f.read()
        for gid in _guild_ids:
            sym = extract_symbol(guild_content, gid)
            if sym:
                guild_symbols.append(sym)
            else:
                print(f'  WARNING: guild symbol not found: {gid}')
        print(f'Guild icons: {len(guild_symbols)} (buildings+shrines)')
    else:
        print('WARNING: guild_sprite.svg not found, guild building/shrine icons will be missing')

    # Read house_sprite.svg for the 17 house-room icons
    house_sprite_path = os.path.join(BASE_DIR, 'house_sprite.svg')
    house_symbols = []
    _hr = GAME_DATA.get('houseRoom', {}) or {}
    _house_ids = [d.get('icon') for d in _hr.get('defs', [])]
    _house_ids = [x for x in _house_ids if x]
    if os.path.exists(house_sprite_path):
        with open(house_sprite_path, 'r', encoding='utf-8') as f:
            house_content = f.read()
        for hid in _house_ids:
            sym = extract_symbol(house_content, hid)
            if sym:
                house_symbols.append(sym)
            else:
                print(f'  WARNING: house symbol not found: {hid}')
        print(f'House icons: {len(house_symbols)} (rooms)')
    else:
        print('WARNING: house_sprite.svg not found, house room icons will be missing')

    # Combine: skill icons, equipment icons, buff icons, guild icons, house icons
    all_symbols = skill_symbols + equip_symbols + buff_symbols + guild_symbols + house_symbols
    svg_block = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="display:none">\n' + '\n'.join(all_symbols) + '\n</svg>'

    # Build EQUIP_ICONS JS
    equip_icons_lines = ['const EQUIP_ICONS = {']
    for et in EQUIP_TYPES:
        items = categorized.get(et, [])
        item_strs = [f'"{sid}"' for sid in items]
        equip_icons_lines.append(f'  "{et}":[{",".join(item_strs)}],')
    equip_icons_lines.append('};')
    equip_icons_js = '\n'.join(equip_icons_lines)

    # Build game data JS from mwi_data.json (装备/工具/房屋/公会加成等)
    gd = GAME_DATA
    game_data_lines = []
    if gd:
        game_data_lines.append('const EQUIPMENT_BASE_BONUSES = %s;' % json.dumps(gd.get('equipmentBaseBonuses', {}), ensure_ascii=False))
        game_data_lines.append('const ENH_BONUS_PERCENT_TABLE = %s;' % json.dumps(gd.get('enhancementBonusTable', [])))
        game_data_lines.append('const ACCESSORY_ENH_SLOTS = new Set(%s);' % json.dumps(gd.get('accessoryEnhSlots', []), ensure_ascii=False))
        game_data_lines.append('const TOOL_PREFIX_BONUS = %s;' % json.dumps(gd.get('toolPrefixBonus', {}), ensure_ascii=False))
        game_data_lines.append('const ENHANCER_PREFIX_BONUS = %s;' % json.dumps(gd.get('enhancerPrefixBonus', {}), ensure_ascii=False))
        game_data_lines.append('const TOOL_SUFFIX_SKILL = %s;' % json.dumps(gd.get('toolSuffixSkill', {}), ensure_ascii=False))
        game_data_lines.append('const HOUSE_ROOM_SKILL_MAP = %s;' % json.dumps(gd.get('houseRoomSkillMap', {}), ensure_ascii=False))
        game_data_lines.append('const HOUSE_BONUS_PER_LEVEL = %s;' % json.dumps(gd.get('houseBonusPerLevel', {})))
        gbd = gd.get('guildBuilding', {})
        _util = gbd.get('utility', [])
        _trial = gbd.get('trial', [])
        _util_keys = [u.get('key') for u in _util]
        _trial_keys = [td.get('skill') for td in _trial]
        _icons = {}
        for _u in _util: _icons[_u.get('key')] = _u.get('icon')
        for _td in _trial: _icons[_td.get('skill')] = _td.get('icon')
        game_data_lines.append('const GUILD_BUILDING_KEYS = %s;' % json.dumps(gbd.get('keys', _trial_keys), ensure_ascii=False))
        game_data_lines.append('const GUILD_BUILDING_LIFE_KEYS = %s;' % json.dumps(gbd.get('lifeKeys', []), ensure_ascii=False))
        game_data_lines.append('const GUILD_BUILDING_COMBAT_KEYS = %s;' % json.dumps(gbd.get('combatKeys', []), ensure_ascii=False))
        game_data_lines.append('const GUILD_BUILDING_MAX_LEVEL = %s;' % json.dumps(gbd.get('maxLevel', 20)))
        game_data_lines.append('const GUILD_BUILDING_SKILL_PER_LEVEL = %s;' % json.dumps(gbd.get('skillLevelPerLevel', 2)))
        # 试炼人数上限（游戏客户端 partyCapForKind）：cap = 基准 + min(营地等级, 上限) × 每级人数
        game_data_lines.append('const GUILD_BUILDING_SKILLING_SLOTS_PER_LEVEL = %s;' % json.dumps(gbd.get('skillingTrialSlotsPerLevel', 2)))
        game_data_lines.append('const GUILD_BUILDING_COMBAT_SLOTS_PER_LEVEL = %s;' % json.dumps(gbd.get('combatTrialSlotsPerLevel', 2)))
        game_data_lines.append('const GUILD_BUILDING_SKILLING_BASE_CAP = %s;' % json.dumps(gbd.get('skillingTrialBaseCap', 20)))
        game_data_lines.append('const GUILD_BUILDING_COMBAT_BASE_CAP = %s;' % json.dumps(gbd.get('combatTrialBaseCap', 40)))
        game_data_lines.append('const GUILD_BUILDING_UTILITY = %s;' % json.dumps(_util, ensure_ascii=False))
        game_data_lines.append('const GUILD_BUILDING_TRIAL = %s;' % json.dumps(_trial, ensure_ascii=False))
        game_data_lines.append('const GUILD_BUILDING_UTILITY_KEYS = %s;' % json.dumps(gbd.get('utilityKeys', _util_keys), ensure_ascii=False))
        game_data_lines.append('const GUILD_BUILDING_ALL_KEYS = %s;' % json.dumps(_util_keys + _trial_keys, ensure_ascii=False))
        game_data_lines.append('const GUILD_BUILDING_ICONS = %s;' % json.dumps(_icons, ensure_ascii=False))
        # 游戏 guildBuildingLevelMap 用建筑 hrid 做键，这里映射成我们内部的 key
        game_data_lines.append('const GUILD_BUILDING_HRID_TO_KEY = %s;' % json.dumps(gbd.get('hridToKey', {}), ensure_ascii=False))
        gsd = gd.get('guildShrine', {})
        game_data_lines.append('const GUILD_SHRINE_KEYS = %s;' % json.dumps(gsd.get('keys', []), ensure_ascii=False))
        game_data_lines.append('const GUILD_SHRINE_MAX_LEVEL = %s;' % json.dumps(gsd.get('maxLevel', 20)))
        game_data_lines.append('const GUILD_SHRINE_ICONS = %s;' % json.dumps(gsd.get('icons', {}), ensure_ascii=False))
        game_data_lines.append('const GUILD_SHRINE_SKILL_BUFFS = %s;' % json.dumps(gsd.get('skillingBuffs', {}), ensure_ascii=False))
        game_data_lines.append('const GUILD_SHRINE_DEFS = %s;' % json.dumps(gsd.get('defs', []), ensure_ascii=False))
        # 个人神龛增益键：/guild_buffs/<shrine>_skilling（成员数据里的 guildBuffLevelMap 用的就是这个键）
        game_data_lines.append('const GUILD_SHRINE_BUFF_HRIDS = %s;' % json.dumps(
            {s.get('key'): s.get('buffHrid') for s in gsd.get('defs', [])}, ensure_ascii=False))
        # 成就档位（成员级个人数据，逐成员可编辑，随共享数据上传）
        game_data_lines.append('const ACHIEVEMENT_TIERS = %s;' % json.dumps(gd.get('achievementTiers', []), ensure_ascii=False))
        # 个人神龛槽位（5 座 × 生活/战斗 = 10，扁平化后供 JS 直接遍历）
        _shrines = gsd.get('defs', [])
        _slots = []
        for _sd in _shrines:
            for _v in _sd.get('variants', []):
                _slot = dict(_v)
                _slot['shrine'] = _sd.get('key')
                _slot['icon'] = _sd.get('icon')
                _slots.append(_slot)
        game_data_lines.append('const GUILD_SHRINE_SLOTS = %s;' % json.dumps(_slots, ensure_ascii=False))
        # 房屋房间（成员级个人持久化数据，17 个：10 生活 + 7 战斗）
        _hrd = gd.get('houseRoom', {}) or {}
        game_data_lines.append('const HOUSE_ROOM_MAX_LEVEL = %s;' % json.dumps(_hrd.get('maxLevel', 20)))
        game_data_lines.append('const HOUSE_ROOM_KEYS = %s;' % json.dumps(_hrd.get('keys', []), ensure_ascii=False))
        game_data_lines.append('const HOUSE_ROOM_SKILLING_KEYS = %s;' % json.dumps(_hrd.get('skillingKeys', []), ensure_ascii=False))
        game_data_lines.append('const HOUSE_ROOM_COMBAT_KEYS = %s;' % json.dumps(_hrd.get('combatKeys', []), ensure_ascii=False))
        game_data_lines.append('const HOUSE_ROOM_ICONS = %s;' % json.dumps(_hrd.get('icons', {}), ensure_ascii=False))
        game_data_lines.append('const HOUSE_ROOM_DEFS = %s;' % json.dumps(_hrd.get('defs', []), ensure_ascii=False))
        game_data_lines.append('const EMBEDDED_CLIENT_DATA = %s;' % json.dumps(gd.get('embeddedClientData', {}), ensure_ascii=False))
    game_data_js = '\n'.join(game_data_lines)

    # 装备「家族」表（生活装备『勾选制』区域用）：
    #   - 命中「装备基础加成表」= 生活件（只有生活技能加成、没有战斗加成）
    #   - 同一基础款若存在「★」条目（如 采集者披风 / 采集者披风 ★）→ 折叠成一个家族，refined=true
    #     （游戏里普通款与精炼款互斥，只能穿一件 → 界面上是一个勾选 + 一个 ★ 开关）
    #   - 勾选制槽位：上衣(身体)/下装(腿部)/披风(背部)/头部/手部/脚部/副手（只列生活件）。
    #     这些槽位里的物品互不替代（挤奶工 vs 伐木工…），所以按「拥有一批、推演时择优」录入。
    #   - 两用槽位 项链/耳环/戒指/袋子（同一槽位既有生活件也有战斗件）**不在此列**：
    #     它们与生活工具一样是「一槽一件」的上下位替代 → 走配装选择器（openEquipPicker）录入。
    _eb_keys = set((gd.get('equipmentBaseBonuses') or {}).keys()) if gd else set()

    def _is_life_icon(bid):
        return ('/items/' + bid) in _eb_keys

    _owned_slots = ['身体', '腿部', '背部', '头部', '手部', '脚部', '副手']
    _hybrid_slots = ['项链', '耳环', '戒指', '袋子']

    # 先按槽位建立「基础款 iconId → 家族」表（★ 条目折叠到基础款）
    _fam_all = {}
    for _raw_slot, _names in equip_data.items():
        _slot = '主手' if _raw_slot == '双手' else _raw_slot
        _lst = _fam_all.setdefault(_slot, [])
        _by_id = {_f['id']: _f for _f in _lst}
        for _nm in _names:
            _refined = _nm.endswith(' ★')
            _base_name = _nm[:-2] if _refined else _nm
            _bid = ITEM_NAME_MAP.get(_base_name)
            if not _bid:
                continue
            _f = _by_id.get(_bid)
            if _f is None:
                _f = {'id': _bid, 'name': _base_name, 'refined': _refined, 'life': _is_life_icon(_bid)}
                _lst.append(_f)
                _by_id[_bid] = _f
            elif _refined:
                _f['refined'] = True

    _equip_families = {}
    for _slot in _owned_slots:
        _all = _fam_all.get(_slot, [])
        _sel = [_f for _f in _all if _f['life']]
        _equip_families[_slot] = _sel
        print('Equip families [%s]: %d (life=%d)'
              % (_slot, len(_sel), len([_f for _f in _sel if _f['life']])))

    life_equip_lines = [
        'const EQUIP_FAMILIES = %s;' % json.dumps(_equip_families, ensure_ascii=False),
        'const OWNED_SLOTS = %s;' % json.dumps(_owned_slots, ensure_ascii=False),
        'const HYBRID_SLOTS = %s;' % json.dumps(_hybrid_slots, ensure_ascii=False),
    ]
    life_equip_js = '\n'.join(life_equip_lines)

    # Replace placeholders
    js_filled = JS.replace('// __EQUIP_ICONS_PLACEHOLDER__', equip_icons_js)
    js_filled = js_filled.replace('// __LIFE_EQUIP_PLACEHOLDER__', life_equip_js)
    js_filled = js_filled.replace('// __GAME_DATA_PLACEHOLDER__', game_data_js)
    html_filled = HTML.replace('__CSS__', CSS).replace('__SVG_SYMBOLS__', svg_block).replace('__JS__', js_filled)

    # Write output
    out_path = os.path.join(BASE_DIR, 'mwi_trial_calculator.html')
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write(html_filled)

    print(f'\nGenerated: {out_path}')
    print(f'File size: {len(html_filled):,} bytes')
    print(f'Skill icons: {len(skill_symbols)}')
    print(f'Equipment icons: {len(equip_symbols)}')
    print(f'Total symbols: {len(all_symbols)}')
    print(f'\nEquipment categories:')
    for et in EQUIP_TYPES:
        count = len(categorized.get(et, []))
        print(f'  {et}: {count}')

if __name__ == '__main__':
    main()
