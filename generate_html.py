#!/usr/bin/env python3
"""Generate MWI Trial Calculator HTML v4 - i18n, themes, correct skill icons, reqNext."""

import re, json, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')

# Load Chinese item name -> icon ID mapping (generated from game localization)
ITEM_NAME_MAP_PATH = os.path.join(ASSETS_DIR, 'item_name_map.json')
ITEM_NAME_MAP = {}
if os.path.exists(ITEM_NAME_MAP_PATH):
    with open(ITEM_NAME_MAP_PATH, 'r', encoding='utf-8') as f:
        ITEM_NAME_MAP = json.load(f)

# 游戏数据（装备/工具/房屋/公会加成 + 游戏 client 定义），与生成逻辑分离，单独维护。
GAME_DATA_PATH = os.path.join(ASSETS_DIR, 'mwi_data.json')
GAME_DATA = {}
if os.path.exists(GAME_DATA_PATH):
    with open(GAME_DATA_PATH, 'r', encoding='utf-8') as f:
        GAME_DATA = json.load(f)
else:
    print('WARNING: mwi_data.json not found, game data will be missing')

# 游戏物品等级（itemLevel，取自 init_client_data 的 itemDetailMap）。
# 导入配装时按装备等级覆盖：高级装备可覆盖低级装备。
EQUIP_LEVELS_PATH = os.path.join(ASSETS_DIR, 'equip_levels.json')
EQUIP_LEVELS = {}
if os.path.exists(EQUIP_LEVELS_PATH):
    with open(EQUIP_LEVELS_PATH, 'r', encoding='utf-8') as f:
        EQUIP_LEVELS = json.load(f)
else:
    print('WARNING: equip_levels.json not found, equipment-level comparison will fall back')

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
# 前端源码（src/）：CSS / JS / HTML 独立维护，构建时读入并内联
# ============================================================

SRC_DIR = os.path.join(BASE_DIR, 'src')


def read_src(name):
    """读取 src/ 下的前端源码，去掉首尾空行（内联时按位置补换行）。"""
    with open(os.path.join(SRC_DIR, name), 'r', encoding='utf-8') as f:
        return f.read().strip('\n')


# ============================================================
# Main
# ============================================================

def main():
    # CSS / JS 内联在 <style> / <script> 中间，首尾各留一个换行；HTML 模板本身首尾无空行
    css_src = '\n' + read_src('styles.css') + '\n'
    js_src = '\n' + read_src('app.js') + '\n'
    html_src = read_src('index.html')

    # Read items.svg
    with open(os.path.join(ASSETS_DIR, 'items.svg'), 'r', encoding='utf-8') as f:
        svg_content = f.read()

    all_ids = re.findall(r'<symbol[^>]*id="([^"]+)"', svg_content)
    print(f'Total symbols in items.svg: {len(all_ids)}')

    # Categorize equipment using equip.json (authoritative) + ITEM_NAME_MAP
    equip_json_path = os.path.join(ASSETS_DIR, 'equip.json')
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
    skills_sprite_path = os.path.join(ASSETS_DIR, 'skills_sprite.svg')
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
    buffs_sprite_path = os.path.join(ASSETS_DIR, 'buffs_sprite.svg')
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
    guild_sprite_path = os.path.join(ASSETS_DIR, 'guild_sprite.svg')
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
    house_sprite_path = os.path.join(ASSETS_DIR, 'house_sprite.svg')
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
        game_data_lines.append('const EQUIP_LEVELS = %s;' % json.dumps(EQUIP_LEVELS, ensure_ascii=False, separators=(',', ':')))
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
    js_filled = js_src.replace('// __EQUIP_ICONS_PLACEHOLDER__', equip_icons_js)
    js_filled = js_filled.replace('// __LIFE_EQUIP_PLACEHOLDER__', life_equip_js)
    js_filled = js_filled.replace('// __GAME_DATA_PLACEHOLDER__', game_data_js)
    html_filled = html_src.replace('__CSS__', css_src).replace('__SVG_SYMBOLS__', svg_block).replace('__JS__', js_filled)

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
