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
.global-buff-item { display:inline-flex; align-items:center; gap:6px; padding:4px 10px; border:1px solid var(--border); border-radius:4px; background:var(--conn-bg); font-size:12px; color:var(--text); cursor:pointer; }
.global-buff-item .global-buff-icon { width:18px; height:18px; flex:0 0 auto; vertical-align:middle; }
.global-buff-item input { width:48px; padding:2px 6px; border:1px solid var(--border); border-radius:3px; background:var(--input-bg); color:var(--text); font-size:12px; text-align:center; }
.global-buff-item input:focus { outline:none; border-color:var(--accent); }
.global-buff-item .global-buff-unit { color:var(--text-faint); font-size:11px; }

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
table.member-table th.skill-col { min-width:52px; }
table.member-table th.skill-col svg { width:20px; height:20px; vertical-align:middle; }
table.member-table th.equip-col { min-width:48px; font-size:10px; padding:4px 2px; white-space:nowrap; }
table.member-table th.assign-col { min-width:44px; }
table.member-table th.name-col { min-width:90px; text-align:left; }
table.member-table td.name-cell { text-align:left; }
table.member-table td input { width:100%; border:1px solid transparent; background:transparent; font-size:13px; padding:2px 4px; border-radius:3px; color:var(--text); }
table.member-table td input:focus { border-color:var(--accent); background:var(--input-bg); outline:none; }
table.member-table td.skill-input input { width:52px; text-align:center; }
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
    addMember:'添加成员', share:'共享设置', importData:'导入',
    exportScriptTitle:'下载油猴脚本，自动采集公会成员数据导出为 JSON',
    calculate:'计算最优分配', assignCol:'分配', nameCol:'角色名', maxMembers:'人数上限',
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
    teamWork:'团队工作能力', nextClearNeeds:'下1次还需', pts:'点', perSec:'点/秒',
    trial:'试炼', language:'中/EN', theme:'🌙',
    globalBuffs:'全局加成',
    globalBuffsTip:'手动输入你所在服务器/账号的社区大厅全局 buff 等级：0 = 无 buff，1~20 级启用。加成 = 19.5 + 等级×0.5（%），仅本地保存，每个玩家按自己实际情况填。',
    buffGathering:'采集数量', buffGatheringTip:'仅对采集类技能（挤奶/采摘/伐木）的双倍产出概率生效；0=无，1~20 级，加成 = 19.5 + 等级×0.5（%）。',
    buffProduction:'生产效率', buffProductionTip:'仅对生产类技能（奶酪锻造/制作/缝纫/烹饪/冲泡/炼金）的效率生效；0=无，1~20 级，加成 = 19.5 + 等级×0.5（%）。',
    buffEnhancingSpeed:'强化速度', buffEnhancingSpeedTip:'仅对强化技能的动作速度生效；0=无，1~20 级，加成 = 19.5 + 等级×0.5（%）。',
    levelUnit:'级',
    skillLabels:['挤奶','采摘','伐木','奶酪锻造','制作','缝纫','烹饪','冲泡','炼金','强化'],
    equipLabels:['主手','副手','头部','身体','手部','腿部','脚部','项链','耳环','戒指','袋子','背部','挤奶工具','采摘工具','伐木工具','奶酪锻造工具','制作工具','缝纫工具','烹饪工具','冲泡工具','炼金工具','强化工具'],
    equipShort:['主手','副手','头部','身体','手部','腿部','脚部','项链','耳环','戒指','袋子','背部','挤奶','采摘','伐木','奶酪','制作','缝纫','烹饪','冲泡','炼金','强化'],
  },
  en: {
    title:'MWI Trial Calculator', trialConfig:'Trial Config', memberData:'Member Data',
    addMember:'Add Member', share:'Share', importData:'Import',
    exportScriptTitle:'Download userscript to auto-collect guild member data as JSON',
    calculate:'Calculate', assignCol:'Assign', nameCol:'Name', maxMembers:'Max',
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
    teamWork:'Team Work', nextClearNeeds:'Next clear needs', pts:'pts', perSec:'pts/s',
    trial:'Trial', language:'中/EN', theme:'☀️',
    globalBuffs:'Global Buffs',
    globalBuffsTip:'Enter your server/account community-hall global buff level: 0 = none, 1~20 = active. Bonus = 19.5 + level×0.5 (%), stored locally only.',
    buffGathering:'Gathering Qty', buffGatheringTip:'Applies only to gathering skills (Milking/Foraging/Woodcutting) as double-drop chance. 0=none, 1~20, bonus = 19.5 + level×0.5 (%).',
    buffProduction:'Production Eff', buffProductionTip:'Applies only to production skills (Cheesesmithing/Crafting/Tailoring/Cooking/Brewing/Alchemy) as efficiency. 0=none, 1~20, bonus = 19.5 + level×0.5 (%).',
    buffEnhancingSpeed:'Enhancing Spd', buffEnhancingSpeedTip:'Applies only to the Enhancing skill as action speed. 0=none, 1~20, bonus = 19.5 + level×0.5 (%).',
    levelUnit:'lv',
    skillLabels:['Milking','Foraging','Woodcutting','Cheesesmithing','Crafting','Tailoring','Cooking','Brewing','Alchemy','Enhancing'],
    equipLabels:['Main Hand','Off Hand','Head','Body','Hands','Legs','Feet','Necklace','Earring','Ring','Pouch','Back','Milking Tool','Foraging Tool','Woodcutting Tool','Cheesesmithing Tool','Crafting Tool','Tailoring Tool','Cooking Tool','Brewing Tool','Alchemy Tool','Enhancing Tool'],
    equipShort:['MH','OH','Head','Body','Hands','Legs','Feet','Neck','Ear','Ring','Bag','Back','Milk','Forage','Wood','Cheese','Craft','Tailor','Cook','Brew','Alch','Enh'],
  }
};
function t(key) { return (I18N[state.lang] && I18N[state.lang][key]) || key; }
function skillLabel(idx) { return I18N[state.lang].skillLabels[idx]; }
function equipLabel(idx) { return I18N[state.lang].equipLabels[idx]; }
function equipShortLabel(idx) { return I18N[state.lang].equipShort[idx]; }

// === Constants ===
const SKILL_KEYS = ['milking','foraging','woodcutting','cheesesmithing','crafting','tailoring','cooking','brewing','alchemy','enhancing'];
const EQUIP_TYPES = ['主手','副手','头部','身体','手部','腿部','脚部','项链','耳环','戒指','袋子','背部','挤奶工具','采摘工具','伐木工具','奶酪锻造工具','制作工具','缝纫工具','烹饪工具','冲泡工具','炼金工具','强化工具'];
const TOOL_SKILL_MAP = {'挤奶工具':'milking','采摘工具':'foraging','伐木工具':'woodcutting','奶酪锻造工具':'cheesesmithing','制作工具':'crafting','缝纫工具':'tailoring','烹饪工具':'cooking','冲泡工具':'brewing','炼金工具':'alchemy','强化工具':'enhancing'};
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
const TRIAL_DURATION = 3600, START_LV = 100, LV_PER_PASS = 10, COUNT_INFLATION = 0.01;
const BASE_ACTION_SEC = 10, SUCCESS_BASE = 0.80, SUCCESS_BELOW = 0.01, SUCCESS_ABOVE = 0.005, SUCCESS_MIN = 0.05;
const BASE_TOTAL_PT = 40000, PT_GROWTH = 4000, MAX_PASS_GUARD = 10000, NUM_TRIALS = 4;

// __EQUIP_ICONS_PLACEHOLDER__

// === State ===
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
  globalBuffs: { gathering: 0, production: 0, enhancingSpeed: 0 }
};
let pickerState = { memberId:null, slot:null, iconId:null, enhance:0 };

// === Algorithm ===
function computeMemberBonuses(equipment) {
  const b = {};
  for (const k of SKILL_KEYS) b[k] = {speedBonus:0,efficiencyBonus:0,successBonus:0,gatheringBonus:0,skillLevelBonus:0};
  if (!equipment) return b;
  for (const [slot, eq] of Object.entries(equipment)) {
    if (!eq || (!eq.iconId && !(eq.enhance > 0))) continue;
    const L = eq.enhance || 0;
    const skill = TOOL_SKILL_MAP[slot];
    if (skill) {
      b[skill].speedBonus += L*0.025;
      b[skill].efficiencyBonus += L*0.015;
      b[skill].successBonus += L*0.005;
      b[skill].gatheringBonus += L*0.01;
      b[skill].skillLevelBonus += L*0.5;
    } else {
      for (const s of SKILL_KEYS) {
        b[s].speedBonus += L*0.002; b[s].efficiencyBonus += L*0.001; b[s].skillLevelBonus += L*0.1;
      }
    }
  }
  return b;
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
  const bonuses = computeMemberBonuses(person.equipment);
  const skillId = SKILL_KEYS[skillIdx];
  const b = bonuses[skillId];
  // 手动输入的全局 buff：按技能分类叠加相应比例
  addGlobalBuffsToCombined(b, skillId);
  const baseLevel = Number(person.levels[skillIdx]||0);
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

// === Rendering ===
function renderTableHeader() {
  const thead = document.getElementById('member-thead');
  let html = '<tr>';
  html += '<th class="assign-col">'+t('assignCol')+'</th>';
  html += '<th class="name-col">'+t('nameCol')+'</th>';
  for (let s = 0; s < 10; s++) {
    html += '<th class="skill-col" title="'+skillLabel(s)+'">'+svgIcon(SKILL_KEYS[s],20,20)+'</th>';
  }
  for (let i = 0; i < EQUIP_TYPES.length; i++) {
    html += '<th class="equip-col">'+equipShortLabel(i)+'</th>';
  }
  html += '<th></th>';
  html += '</tr>';
  thead.innerHTML = html;
}
function renderAll() {
  document.title = t('title');
  renderTableHeader();
  renderTrialCards();
  renderMemberTable();
  renderSummary();
  updateStaticText();
}

function updateStaticText() {
  document.getElementById('h1-title').textContent = t('title');
  document.getElementById('h2-trial').textContent = t('trialConfig');
  document.getElementById('h2-member').firstChild.textContent = t('memberData') + ' ';
  document.getElementById('btn-add-member').textContent = '+ '+t('addMember');
  document.getElementById('btn-share').textContent = t('share');
  document.getElementById('btn-import-json').textContent = t('importData');
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
}

function renderTrialCards() {
  const container = document.getElementById('trial-cards');
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
      '<div class="trial-max-row"><label>'+t('maxMembers')+':</label><input type="number" value="'+cfg.max+'" min="1" max="80" onchange="updateTrialMax('+j+',this.value)"></div>'+
      '<div class="trial-member-list" data-empty="'+t('noAssign')+'">'+memberListHtml+'</div>'+
      resultHtml+
    '</div>';
  }).join('');
}

function renderMemberTable() {
  const tbody = document.getElementById('member-tbody');
  if (state.members.length === 0) {
    tbody.innerHTML = '<tr><td colspan="36" style="color:var(--text-faint);padding:20px">'+t('noMembers')+'</td></tr>';
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
    let skillCells = '';
    for (let s = 0; s < 10; s++) {
      skillCells += '<td class="skill-input"><input type="number" value="'+(p.levels[s]||0)+'" min="0" max="999" onchange="updateSkillLevel('+p.id+','+s+',this.value)"></td>';
    }
    let equipCells = '';
    for (let i = 0; i < EQUIP_TYPES.length; i++) {
      const slot = EQUIP_TYPES[i];
      const eq = p.equipment && p.equipment[slot];
      if (eq && eq.iconId) {
        equipCells += '<td><div class="equip-cell" onclick="openEquipPicker('+p.id+',\''+slot+'\')">'+svgIcon(eq.iconId,30,30)+'<span class="enhance-badge">+'+(eq.enhance||0)+'</span></div></td>';
      } else {
        equipCells += '<td><div class="equip-cell empty" onclick="openEquipPicker('+p.id+',\''+slot+'\')"></div></td>';
      }
    }
    return '<tr>'+
      '<td class="assign-cell '+assignClass+'">'+assignContent+'</td>'+
      '<td class="name-cell"><input type="text" value="'+escHtml(p.name)+'" onchange="updateMemberName('+p.id+',this.value)"></td>'+
      skillCells + equipCells +
      '<td><button class="btn btn-sm btn-danger" onclick="removeMember('+p.id+')">'+t('deleteBtn')+'</button></td>'+
    '</tr>';
  }).join('');
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
  const icons = EQUIP_ICONS[slot] || [];
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
    el.style.display = (!q || name.toLowerCase().includes(q)) ? '' : 'none';
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
  renderMemberTable();
  saveData();
}
function clearEquip() {
  const person = state.members.find(p => p.id === pickerState.memberId);
  if (person && person.equipment) { delete person.equipment[pickerState.slot]; person._ts = Date.now(); }
  closeEquipPicker();
  renderMemberTable();
  saveData();
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
  saveData();
}
function updateMemberName(id, value) {
  const p = state.members.find(p => p.id === id);
  if (p) { p.name = value; p._ts = Date.now(); saveData(); }
}
function updateSkillLevel(id, skillIdx, value) {
  const p = state.members.find(p => p.id === id);
  if (p) { p.levels[skillIdx] = Math.max(0, parseInt(value)||0); p._ts = Date.now(); saveData(); }
}
function updateTrialMax(trialIdx, value) {
  state.trials[trialIdx].max = Math.max(1, parseInt(value)||20);
  state.trials[trialIdx]._ts = Date.now();
  saveData();
}

// === Calculate ===
function calculate() {
  if (state.members.length === 0) { alert(t('addMembersFirst')); return; }
  const t0 = performance.now();
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
  return { name, levels, equipment };
}
function importJson() {
  const input = document.createElement('input');
  input.type = 'file'; input.accept = '.json';
  input.onchange = () => {
    const file = input.files[0]; if (!file) return;
    const reader = new FileReader();
    reader.onload = async () => {
      let membersData;
      try {
        membersData = JSON.parse(reader.result);
        if (!Array.isArray(membersData)) throw new Error('JSON must be an array');
      } catch(e) {
        alert('JSON parse error: ' + e.message);
        return;
      }
      const newMembers = [];
      for (const profile of membersData) {
        const m = parseMemberFromProfile(profile);
        if (m) {
          m.id = newMembers.length > 0 ? newMembers[newMembers.length-1].id + 1 : 0;
          m._ts = Date.now();   // 标记为最新，避免被旧共享 bin 数据在合并时覆盖
          newMembers.push(m);
        }
      }
      if (newMembers.length > 0) {
        state.members = newMembers;
        state.deletedIds = [];
        const data = JSON.stringify({ guild: state.guild, members: state.members, trials: state.trials, deletedIds: state.deletedIds });
        try { localStorage.setItem(getStorageKey(), data); } catch(e) {}
        if (state.isShared && state.binId && state.encKey) {
          await forcePushToBin(data);   // 立即全量覆盖 bin，不走合并，防止被旧数据覆盖
        } else {
          saveData();
        }
        renderAll();
        if (state.members.length > 0) calculate();
        alert(t('importSuccess')+': '+newMembers.length);
      } else {
        alert(t('importFailed'));
      }
    };
    reader.readAsText(file, 'UTF-8');
  };
  input.click();
}


// === Data Persistence ===
function getStorageKey() { return 'mwi_trial_'+(state.guild||'default'); }
function saveData() {
  const data = JSON.stringify({ guild:state.guild, members:state.members, trials:state.trials, deletedIds:state.deletedIds });
  try { localStorage.setItem(getStorageKey(), data); } catch(e) {}
  if (state.isShared && state.binId && state.encKey) saveToBin(data);
}
function loadData() {
  try {
    const raw = localStorage.getItem(getStorageKey());
    if (raw) { Object.assign(state, JSON.parse(raw)); if (!Array.isArray(state.deletedIds)) state.deletedIds = []; return true; }
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
  return { guild: local.guild || remote.guild, members: mergedMembers, trials: mergedTrials, deletedIds: [...del] };
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
      return true;
    }
  } catch(e) { console.error('Load failed:', e); }
  return false;
}
async function createBin(guild, password, masterKey) {
  const encKey = await deriveKey(password, guild);
  const data = JSON.stringify({ guild, members: state.members, trials: state.trials, deletedIds: state.deletedIds });
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
    renderAll();
    if (loadedFromShare && state.members.length > 0) calculate();
  } else {
    loadData();
    if (!state.trials) state.trials = [{skill:0,max:20},{skill:1,max:20},{skill:2,max:20},{skill:3,max:20}];
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
</div>

<div class="trial-section">
  <h2 id="h2-trial">试炼配置</h2>
  <div class="trial-cards" id="trial-cards"></div>
</div>

<div class="member-section">
  <h2 id="h2-member">成员数据 <button class="btn btn-sm" id="btn-add-member" onclick="addMember()">+ 添加成员</button></h2>
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

    # Combine: skill icons, equipment icons, then buff icons
    all_symbols = skill_symbols + equip_symbols + buff_symbols
    svg_block = '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" style="display:none">\n' + '\n'.join(all_symbols) + '\n</svg>'

    # Build EQUIP_ICONS JS
    equip_icons_lines = ['const EQUIP_ICONS = {']
    for et in EQUIP_TYPES:
        items = categorized.get(et, [])
        item_strs = [f'"{sid}"' for sid in items]
        equip_icons_lines.append(f'  "{et}":[{",".join(item_strs)}],')
    equip_icons_lines.append('};')
    equip_icons_js = '\n'.join(equip_icons_lines)

    # Replace placeholders
    js_filled = JS.replace('// __EQUIP_ICONS_PLACEHOLDER__', equip_icons_js)
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
