# -*- coding: utf-8 -*-
"""
Created on Fri Sep  6 13:20:07 2024

@author: lixianlong
"""

import json
import re
import os
import subprocess
import tempfile
import urllib.request, urllib.error
import unicodedata
from glob import glob
from collections import Counter
from PIL import Image, ImageChops
import xlwt
import pandas as pd
from   datetime import datetime, timedelta, time as datetime_time
from zoneinfo import ZoneInfo

PNG_RENDER_DPI = 600
PNG_PAGE_JOIN_GAP_MM = 4.5
PNG_PAGE_CONTENT_PADDING_PX = 8
PNG_CONTINUATION_CROP_PADDING_MM = 1.5
LOGO_REGISTRY_FILENAME = '球队队徽库.json'


todayTime = datetime.now(ZoneInfo('Asia/Shanghai')).strftime("%Y-%m-%d")
baseurl  = "https://dongqiudi.com/api/data/tab/league/new/index?start="+todayTime+"14:17:04&init=1&platform=www"  #要爬取的网页链接
findItem  = re.compile(r'{"relate_type":(.*?)}')

def askURL(url):
    head = {  # 模拟浏览器头部信息，向豆瓣服务器发送消息
        "User-Agent": "Mozilla / 5.0(Windows NT 10.0; Win64; x64) AppleWebKit / 537.36(KHTML, like Gecko) Chrome / 80.0.3987.122  Safari / 537.36"
    }
    # 用户代理，表示告诉豆瓣服务器，我们是什么类型的机器、浏览器（本质上是告诉浏览器，我们可以接收什么水平的文件内容）

    request = urllib.request.Request(url, headers=head)
    html = ""
    try:
        response = urllib.request.urlopen(request)
        html = response.read().decode("utf-8")
    except urllib.error.URLError as e:
        if hasattr(e, "code"):
            print(e.code)
        if hasattr(e, "reason"):
            print(e.reason)
    return html
    
def saveData(datalist, dataPath, fileType):
    col = ("Event", "BeijingTime", "HostTeam", "Score", "GuestTeam") 
    def get_Name1():
        book = xlwt.Workbook(encoding="utf-8",style_compression=0) #创建workbook对象
        sheet = book.add_sheet('GameTeams', cell_overwrite_ok=True) #创建工作表
        for i in range(0, len(col)):
            sheet.write(0,i,col[i])  #列名
        for i in range(0,len(datalist)):
            data = datalist[i]
            for j in range(0,len(col)):
                sheet.write(i+1,j,data[j])  #数据
        book.save(dataPath+'.'+fileType) #保存
        print('Save as Excel Files')
    def get_Name2():
        pd_Data = pd.core.frame.DataFrame(datalist)
        pd_Data.to_csv(dataPath+'.'+fileType, header=False, sep=' ', index=False)
        print('Save as TXT Files')
    fileName={
        'txt': get_Name2, 
        'xls': get_Name1}
    fileName.get(fileType)()

def latex_escape(text):
    """转义赛事、球队名称中可能出现的 LaTeX 特殊字符。"""
    text = str(text).replace('\\/', '/')
    replacements = {
        '\\': r'\textbackslash{}', '&': r'\&', '%': r'\%', '$': r'\$',
        '#': r'\#', '_': r'\_', '{': r'\{', '}': r'\}',
        '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
    }
    return ''.join(replacements.get(char, char) for char in text)
def normalized_team_name(team):
    """统一全半角、大小写与分隔符，供队徽别名匹配使用。"""
    normalized = unicodedata.normalize('NFKC', str(team)).casefold()
    return ''.join(char for char in normalized if char.isalnum())

def load_logo_registry():
    """读取可扩展的队徽库，并区分国家队及赛事徽标别名。"""
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    registry_path = os.path.join(script_dir, LOGO_REGISTRY_FILENAME)
    try:
        with open(registry_path, encoding='utf-8') as registry_file:
            registry = json.load(registry_file)
    except OSError as error:
        raise FileNotFoundError('未找到队徽库：%s' % registry_path) from error
    except json.JSONDecodeError as error:
        raise ValueError('队徽库 JSON 格式错误：%s' % error) from error

    raw_clubs = registry.get('clubs')
    if raw_clubs is None:
        competitions = registry.get('competitions')
        if not isinstance(competitions, dict):
            raise ValueError('队徽库缺少 competitions 对象。')
        clubs = []
        for competition_name, competition in competitions.items():
            if not isinstance(competition, dict) or not isinstance(competition.get('clubs'), list):
                raise ValueError('队徽库中的每个分区都必须包含 clubs 数组。')
            clubs.extend((club, competition_name == 'national_teams') for club in competition['clubs'])
    else:
        if not isinstance(raw_clubs, list):
            raise ValueError('队徽库中的 clubs 必须是数组。')
        clubs = [(club, False) for club in raw_clubs]

    aliases = []
    football_national_aliases = []
    for club, is_national_team in clubs:
        if not isinstance(club, dict) or not isinstance(club.get('logo'), str):
            raise ValueError('队徽库中的每个俱乐部都必须包含 logo。')
        for alias in club.get('aliases', ()):
            if not isinstance(alias, str) or not normalized_team_name(alias):
                raise ValueError('队徽库中的 aliases 必须是非空字符串。')
            aliases.append((normalized_team_name(alias), club['logo']))
        if is_national_team:
            for alias in club.get('football_only_aliases', ()):
                if not isinstance(alias, str) or not normalized_team_name(alias):
                    raise ValueError('国家队的 football_only_aliases 必须是非空字符串。')
                football_national_aliases.append((normalized_team_name(alias), club['logo']))

    event_logo_aliases = []
    event_logos = registry.get('event_logos', ())
    if not isinstance(event_logos, list):
        raise ValueError('队徽库中的 event_logos 必须是数组。')
    for event_logo in event_logos:
        if not isinstance(event_logo, dict) or not isinstance(event_logo.get('logo'), str):
            raise ValueError('赛事徽标必须包含 logo。')
        for keyword in event_logo.get('keywords', ()):
            if not isinstance(keyword, str) or not normalized_team_name(keyword):
                raise ValueError('赛事徽标的 keywords 必须是非空字符串。')
            event_logo_aliases.append((normalized_team_name(keyword), event_logo['logo']))

    tennis_player_aliases = []
    tennis_players = registry.get('tennis_players', ())
    if not isinstance(tennis_players, list):
        raise ValueError('队徽库中的 tennis_players 必须是数组。')
    for player in tennis_players:
        if not isinstance(player, dict) or not isinstance(player.get('portrait'), str):
            raise ValueError('网球运动员必须包含 portrait。')
        for alias in player.get('aliases', ()):
            if not isinstance(alias, str) or not normalized_team_name(alias):
                raise ValueError('网球运动员的 aliases 必须是非空字符串。')
            tennis_player_aliases.append((normalized_team_name(alias), player['portrait']))
    return (tuple(sorted(aliases, key=lambda item: len(item[0]), reverse=True)),
            tuple(sorted(football_national_aliases, key=lambda item: len(item[0]), reverse=True)),
            tuple(sorted(event_logo_aliases, key=lambda item: len(item[0]), reverse=True)),
            tuple(sorted(tennis_player_aliases, key=lambda item: len(item[0]), reverse=True)))

LOGO_ALIASES, FOOTBALL_NATIONAL_ALIASES, EVENT_LOGO_ALIASES, TENNIS_PLAYER_ALIASES = load_logo_registry()
def is_football_national_event(event):
    """仅在可明确判定为足球的国家队赛事中启用裸国家名。"""
    event = str(event).replace('\\/', '/')
    if contains_any(event, ('篮球', '男篮', '女篮')):
        return False
    return contains_any(event, ('世界杯', '世预赛', '欧洲杯', '欧国联', '美洲杯', '麒麟杯', '足球', '男足', '女足'))
def is_tennis_event(event):
    """仅在网球赛事中以运动员立绘替换队徽位置。"""
    return contains_any(event, tuple(RULES['tennis']['keywords']) + ('ATP', 'WTA'))

def latex_team_name(team, event='', compact=False):
    """为球队附加队徽；网球赛事中的已收录运动员使用对应立绘。"""
    escaped_team = latex_escape(team)
    normalized_team = normalized_team_name(team)
    if is_tennis_event(event):
        for alias, portrait_path in TENNIS_PLAYER_ALIASES:
            if alias in normalized_team:
                macro = 'CompactPlayerWithPortrait' if compact else 'PlayerWithPortrait'
                return r'\%s{logo/%s}{%s}' % (macro, portrait_path, escaped_team)
    for alias, logo_path in LOGO_ALIASES:
        if alias in normalized_team:
            return r'\ClubWithLogo{logo/%s}{%s}' % (logo_path, escaped_team)
    if is_football_national_event(event):
        for alias, logo_path in FOOTBALL_NATIONAL_ALIASES:
            if alias == normalized_team:
                return r'\ClubWithLogo{logo/%s}{%s}' % (logo_path, escaped_team)
    return escaped_team

def event_logo_path(event):
    """按赛事名返回赛事徽标路径；英文缩写使用完整词边界匹配。"""
    normalized_event = normalized_team_name(event)
    for keyword, logo_path in EVENT_LOGO_ALIASES:
        if keyword.isascii() and keyword.isalnum():
            if re.search(r'(?<![a-z0-9])%s(?![a-z0-9])' % re.escape(keyword), normalized_event):
                return logo_path
        elif keyword in normalized_event:
            return logo_path
    return ''

def latex_event_name(event, compact=False):
    """在可识别赛事标题前放置对应的实色赛事徽标。"""
    escaped_event = latex_escape(event)
    logo_path = event_logo_path(event)
    if not logo_path:
        return escaped_event
    macro = 'CompactEventTitleWithLogo' if compact else 'EventTitleWithLogo'
    return r'\%s{logo/%s}{%s}' % (macro, logo_path, escaped_event)
def match_datetime(match_time):
    try:
        return datetime.strptime(match_time, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None

def preview_display_time(event, match_time):
    """按项目规则决定预告是否展示具体开赛时间。"""
    parsed_time = match_datetime(match_time)
    tennis = RULES['tennis']
    if contains_any(event, tennis['keywords']) and not tennis.get('show_preview_time', True):
        return ''
    return parsed_time.strftime('%H:%M') if parsed_time else ''

def load_rules():
    """读取赛事重要性规则库中的唯一 JSON 配置。"""
    script_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
    rules_path = os.path.join(script_dir, '赛事重要性规则库.md')
    try:
        with open(rules_path, encoding='utf-8') as rules_file:
            content = rules_file.read()
    except OSError as error:
        raise FileNotFoundError('未找到赛事重要性规则库：%s' % rules_path) from error

    config_block = re.search(r'```json\s*([\s\S]*?)\s*```', content)
    if not config_block:
        raise ValueError('规则库缺少 JSON 配置块。')
    try:
        rules = json.loads(config_block.group(1))
    except json.JSONDecodeError as error:
        raise ValueError('规则库 JSON 格式错误：%s' % error) from error
    required_sections = ('report', 'unmatched', 'china', 'football', 'basketball', 'tennis', 'snooker',
                         'european_national_powerhouses')
    missing_sections = [name for name in required_sections if name not in rules]
    if missing_sections:
        raise ValueError('规则库缺少以下配置：' + '、'.join(missing_sections))
    return rules

RULES = load_rules()
LEVEL_VALUE = {'hidden': 0, 'base': 1, 'focus': 2}

def contains_any(text, keywords):
    return any(keyword in text for keyword in keywords)

def rule_event_keywords(rule):
    """统一读取赛事正式名称与爬虫可能使用的简称。"""
    return tuple(rule.get('keywords', ())) + tuple(rule.get('aliases', ()))

def matches_rule_event(event, rule):
    return contains_any(event, rule_event_keywords(rule))

def match_rule_teams(text, rule, level):
    return contains_any(text, rule.get(level + '_teams', ()))

def league_teams(region):
    teams = []
    for league in RULES['football']['leagues']:
        if league.get('region') == region:
            teams.extend(league.get('focus_teams', ()))
            teams.extend(league.get('base_teams', ()))
    return teams

def national_team_level(event, text):
    national = RULES['football']['national']
    for key in ('world_cup', 'european_championship'):
        rule = national[key]
        if matches_rule_event(event, rule):
            teams = RULES[rule['focus_teams_from']]
            return 'focus' if contains_any(text, teams) else rule['default']

    copa = national['copa_america']
    if matches_rule_event(event, copa):
        return 'base' if contains_any(text, copa['base_teams']) else 'hidden'

    asian = national['asian_competitions']
    if matches_rule_event(event, asian):
        if contains_any(text, asian['focus_teams']):
            return 'focus'
        return 'base' if contains_any(text, asian['base_teams']) else 'hidden'

    nations = national['nations_league']
    if matches_rule_event(event, nations):
        if nations['required_keyword'] in event:
            if contains_any(text, RULES[nations['focus_teams_from']]):
                return 'focus'
            return nations['default']
        return 'hidden'

    exhibitions = national['exhibitions']
    if matches_rule_event(event, exhibitions):
        teams = list(exhibitions['base_teams']) + list(RULES[exhibitions['base_teams_from']])
        return 'base' if contains_any(text, teams) else 'hidden'
    return None

def club_competition_level(event, text):
    continental = RULES['football']['continental_club']
    european_clubs = league_teams('欧洲')
    asian_clubs = league_teams('亚洲')
    champions = continental['champions_league']
    if matches_rule_event(event, champions):
        if contains_any(event, champions['knockout_keywords']):
            return 'focus'
        return 'focus' if champions['group'] in event and contains_any(text, european_clubs) else 'hidden'

    for key, clubs in (('europa_league', european_clubs), ('asian_champions_league', asian_clubs)):
        rule = continental[key]
        if matches_rule_event(event, rule):
            if contains_any(text, clubs) or contains_any(event, rule['focus_stages']):
                return 'focus'
            return 'base' if contains_any(event, rule['base_stages']) else 'hidden'

    libertadores = continental['copa_libertadores']
    if matches_rule_event(event, libertadores):
        if contains_any(event, libertadores['focus_stages']):
            return 'focus'
        return 'base' if contains_any(event, libertadores['base_stages']) else 'hidden'

    for league in RULES['football']['leagues']:
        if matches_rule_event(event, league):
            if match_rule_teams(text, league, 'focus'):
                return 'focus'
            if match_rule_teams(text, league, 'base'):
                return 'base'
            return league.get('default', 'hidden')
    return None

def basketball_level(event, text):
    basketball = RULES['basketball']
    if matches_rule_event(event, basketball['wcba']):
        return 'hidden'
    wnba = basketball['wnba']
    if matches_rule_event(event, wnba):
        return 'base' if match_rule_teams(text, wnba, 'base') else 'hidden'
    for key in ('nba', 'cba'):
        rule = basketball[key]
        if matches_rule_event(event, rule):
            if rule['playoff_keyword'] in event or match_rule_teams(text, rule, 'focus'):
                return 'focus'
            return 'base' if match_rule_teams(text, rule, 'base') else 'hidden'
    return None

def individual_sport_level(event, text):
    tennis = RULES['tennis']
    if contains_any(event, tennis['keywords']):
        if (contains_any(event, tennis['grand_slams']) and contains_any(event, tennis['focus_stages'])) \
                or contains_any(text, tennis['focus_players']):
            return 'focus'
        return 'base' if contains_any(text, tennis['base_players']) else 'hidden'

    snooker = RULES['snooker']
    if contains_any(event, snooker['keywords']):
        if snooker['world_championship'] in event and contains_any(text, snooker['focus_players']):
            return 'focus'
        return 'hidden'
    return None

def match_display_level(row):
    event, _, host, _, guest = row
    normalized_event = event.replace('\\/', '/')
    text = ''.join((normalized_event, host, guest))
    china = RULES['china']
    is_china = china['marker'] in text
    is_youth = bool(re.search(china['youth_pattern'], text))

    if is_china:
        if is_youth and contains_any(normalized_event, china['youth_base_keywords']):
            return 'base'
        return 'focus'
    if contains_any(text, china['star_athletes']) and contains_any(normalized_event, china['major_games']):
        return 'focus'

    level = individual_sport_level(normalized_event, text)
    if level is not None:
        return level
    level = basketball_level(normalized_event, text)
    if level is not None:
        return level
    level = national_team_level(normalized_event, text)
    if level is not None:
        return level
    if '女足' in normalized_event:
        return RULES['football']['women']['default']
    level = club_competition_level(normalized_event, text)
    return level or RULES['unmatched']

def is_non_football(row):
    event = row[0].replace('\\/', '/')
    non_football = RULES['tennis']['keywords'] + RULES['snooker']['keywords']
    for rule in RULES['basketball'].values():
        non_football += rule['keywords']
    return contains_any(event, non_football)

def is_excluded_event(row):
    return match_display_level(row) == 'hidden'

def focus_level(row):
    return LEVEL_VALUE[match_display_level(row)]

def priority_rule_matches(row, rule):
    """通用匹配规则库中的优先级条件，不在代码中写赛事名称。"""
    event, _, host, _, guest = row
    event = event.replace('\\/', '/')
    team = ''.join((host, guest))
    fields = {'event': event, 'team': team, 'text': event + team}
    for field_name, field_text in fields.items():
        required = rule.get(field_name + '_any', ())
        excluded = rule.get(field_name + '_none', ())
        if required and not contains_any(field_text, required):
            return False
        if excluded and contains_any(field_text, excluded):
            return False
    return True

def focus_priority(row):
    """按规则库中的条件与分值确定重点卡片的保留顺序。"""
    priority = RULES['report']['focus_priority']
    for rule in priority['rules']:
        if priority_rule_matches(row, rule):
            return rule['priority']
    return priority['default']

def is_focus_match(row):
    return focus_level(row) >= 2

def match_sort_key(row):
    value = match_datetime(row[1])
    return (value is None, value or datetime.max, row[0], row[2], row[4])

def partition_by_selected(matches, selected_focus):
    """把已通过展示规则筛选的比赛完整分成重点和普通两组。"""
    available = Counter(tuple(row) for row in matches)
    focus_matches = []
    for row in selected_focus:
        key = tuple(row)
        if available[key]:
            focus_matches.append(row)
            available[key] -= 1

    selected = Counter(tuple(row) for row in focus_matches)
    ordinary_matches = []
    for row in matches:
        key = tuple(row)
        if selected[key]:
            selected[key] -= 1
        else:
            ordinary_matches.append(row)
    return focus_matches, sorted(ordinary_matches, key=match_sort_key)

def split_display_matches(matches):
    """最多保留八场重点，其余已收录比赛全部归入普通组。"""
    eligible = [row for row in matches if not is_excluded_event(row)]
    focus_candidates = sorted([row for row in eligible if is_focus_match(row)],
                              key=lambda row: (-focus_priority(row), match_sort_key(row)))
    limit = RULES['report']['focus_limit_per_block']
    focus_matches, ordinary_matches = partition_by_selected(eligible, focus_candidates[:limit])
    stats = {
        'focus_candidates': len(focus_candidates),
        'focus_shown': len(focus_matches),
        'focus_downgraded': max(0, len(focus_candidates) - len(focus_matches)),
        'ordinary_original': len(eligible) - len(focus_candidates),
        'ordinary_shown': len(ordinary_matches),
        'total_shown': len(focus_matches) + len(ordinary_matches),
    }
    return focus_matches, ordinary_matches, stats

def report_time_window(now=None):
    """按规则库计算北京时间整点锚点、回顾起点和预告终点。"""
    report_config = RULES['report']
    if now is None:
        now = datetime.now(ZoneInfo(report_config['timezone']))
    elif now.tzinfo is None:
        now = now.replace(tzinfo=ZoneInfo(report_config['timezone']))
    else:
        now = now.astimezone(ZoneInfo(report_config['timezone']))
    anchor = now.replace(minute=0, second=0, microsecond=0, tzinfo=None)
    recap_start = datetime.combine((anchor - timedelta(hours=report_config['recap_start_hours_before'])).date(),
                                   datetime_time.min)
    preview_end = datetime.combine((anchor + timedelta(hours=report_config['preview_end_hours_after'])).date(),
                                   datetime_time.max)
    return anchor, recap_start, preview_end

def make_result_cards(matches):
    """昨日赛果以双栏卡片排版；焦点由卡片样式而非文字区分。"""
    cards = []
    for event, _, host, score, guest in matches:
        values = [latex_event_name(event), latex_team_name(host, event), latex_escape(score), latex_team_name(guest, event)]
        cards.append(r'\FocusResultMatch{%s}{%s}{%s}{%s}' % tuple(values))
    return make_card_grid(cards)

def make_compact_rows(matches, command):
    """非重点赛事共享一个外框，内部采用双栏紧凑行。"""
    rows = []
    for event, match_time, host, score, guest in matches:
        values = [latex_event_name(event, compact=True), latex_team_name(host, event, compact=True), latex_escape(score), latex_team_name(guest, event, compact=True)]
        if command == 'OtherResultRow':
            row = r'\OtherResultRow{%s}{%s}{%s}{%s}' % tuple(values)
        else:
            display_time = preview_display_time(event, match_time)
            row = r'\OtherScheduleRow{%s}{%s}{%s}{%s}' % (display_time, values[0], values[1], values[3])
        rows.append(row)

    lines = []
    for index in range(0, len(rows), 2):
        lines.extend((r'\begin{minipage}[t]{0.46\linewidth}', rows[index], r'\end{minipage}'))
        if index + 1 < len(rows):
            lines.extend((r'\hspace{0.08\linewidth}', r'\begin{minipage}[t]{0.46\linewidth}', rows[index + 1], r'\end{minipage}'))
        if index + 2 < len(rows):
            lines.append(r'\CompactRowSeparator')
    return '\n'.join(lines)

def make_preview_day(title, matches, selected_focus=None):
    """每个比赛日期只显示一次标题，避免跨页重复。"""
    if not matches:
        return ''
    if selected_focus is None:
        focus_matches, other_matches, _ = split_display_matches(matches)
    else:
        focus_matches, other_matches = partition_by_selected(matches, selected_focus)
    lines = [r'\PreviewDay{%s}' % latex_escape(title)]
    lines.append(make_focus_schedule_cards(focus_matches))
    if other_matches:
        if focus_matches:
            lines.append(r'\MatchGroupGap')
        lines.append(r'\OtherScheduleList{%s}' % make_compact_rows(other_matches, 'OtherScheduleRow'))
    return '\n'.join(lines)

def make_focus_schedule_cards(matches):
    cards = []
    for event, match_time, host, _, guest in matches:
        values = [latex_event_name(event), latex_team_name(host, event), latex_team_name(guest, event)]
        display_time = preview_display_time(event, match_time)
        cards.append(r'\FocusScheduleMatch{%s}{%s}{%s}{%s}' %
                     (values[0], display_time, values[1], values[2]))
    return make_card_grid(cards)

def make_card_grid(cards):
    lines = []
    for index in range(0, len(cards), 2):
        lines.extend((r'\begin{minipage}[t]{0.46\linewidth}', cards[index], r'\end{minipage}'))
        if index + 1 < len(cards):
            lines.extend((r'\hspace{0.08\linewidth}', r'\begin{minipage}[t]{0.46\linewidth}',
                          cards[index + 1], r'\end{minipage}'))
        if index + 2 < len(cards):
            lines.append(r'\vspace{1.5mm}')
    return '\n'.join(lines)

def save_latex_content(datalist, content_path, meta_path):
    """根据本次爬取结果生成固定赛报模板的内容区。"""
    anchor, recap_start, preview_end = report_time_window()

    completed_in_window = sorted(
        [row for row in datalist
         if row[3].strip().lower() != 'vs'
         and ((match_datetime(row[1]) and recap_start <= match_datetime(row[1]) <= anchor)
              or (is_non_football(row) and not match_datetime(row[1])))],
        key=match_sort_key)
    completed = [row for row in completed_in_window if not is_excluded_event(row)]
    scheduled_in_window = [row for row in datalist
                           if row[3].strip().lower() == 'vs'
                           and match_datetime(row[1])
                           and anchor < match_datetime(row[1]) <= preview_end]
    scheduled = [row for row in scheduled_in_window if not is_excluded_event(row)]
    preview_matches = {}
    for row in sorted(scheduled, key=match_sort_key):
        preview_matches.setdefault(match_datetime(row[1]).date(), []).append(row)
    inferred_china_matches = [
        (row[0], anchor.strftime('%Y-%m-%d 00:00:00'), row[2], row[3], row[4])
        for row in datalist
        if row[3].strip().lower() == 'vs'
        and not match_datetime(row[1])
        and contains_any(''.join((row[0], row[2], row[4])),
                         (RULES['china']['marker'],) + tuple(RULES['china']['star_athletes']))
    ]
    if inferred_china_matches:
        preview_matches.setdefault(anchor.date(), []).extend(inferred_china_matches)

    meta = r'''\renewcommand{\ReportDate}{%s}''' % anchor.date().strftime('%Y.%m.%d')

    focus_completed, other_completed, recap_stats = split_display_matches(completed)
    sections = []
    if completed:
        result_content = make_result_cards(focus_completed)
        if other_completed:
            if focus_completed:
                result_content += '\n' + r'\MatchGroupGap'
            result_content += '\n' + r'\OtherResultList{%s}' % make_compact_rows(other_completed, 'OtherResultRow')
        sections.append('\\section{赛果回顾}\n%s' % result_content)
    all_preview_matches = [row for date in sorted(preview_matches) for row in preview_matches[date]]
    selected_preview_focus, _, preview_stats = split_display_matches(all_preview_matches)
    preview_content = ('\n' + r'\MatchGroupGap' + '\n').join(
        make_preview_day(date.strftime('%m 月 %d 日'), preview_matches[date], selected_preview_focus)
        for date in sorted(preview_matches))
    if preview_content:
        sections.append(r'\section{未来两日赛事预告}' + '\n' + preview_content)
    content = '\n\n'.join(section for section in sections if section) or r'\noindent 暂无可展示的赛事。'

    with open(meta_path, 'w', encoding='utf-8') as output:
        output.write(meta)
    with open(content_path, 'w', encoding='utf-8') as output:
        output.write(content)
    print('Recap window: fetched=%d, excluded by rules=%d' %
          (len(completed_in_window), len(completed_in_window) - len(completed)))
    print('Recap groups: focus candidates=%d, focus shown=%d, downgraded to ordinary=%d, '
          'original ordinary=%d, total shown=%d' %
          (recap_stats['focus_candidates'], recap_stats['focus_shown'], recap_stats['focus_downgraded'],
           recap_stats['ordinary_original'], recap_stats['total_shown']))
    print('Preview window: fetched=%d, excluded by rules=%d, inferred without exact time=%d' %
          (len(scheduled_in_window), len(scheduled_in_window) - len(scheduled), len(inferred_china_matches)))
    print('Preview groups: focus candidates=%d, focus shown=%d, downgraded to ordinary=%d, '
          'original ordinary=%d, total shown=%d' %
          (preview_stats['focus_candidates'], preview_stats['focus_shown'], preview_stats['focus_downgraded'],
           preview_stats['ordinary_original'], preview_stats['total_shown']))
    print('Save LaTeX Report Content')

def compile_daily_report(project_dir):
    """用 XeLaTeX 将本次爬虫生成的内容编译为 A4 竖版 PDF。"""
    pdf_dir = os.path.join(project_dir, 'output', 'pdf')
    os.makedirs(pdf_dir, exist_ok=True)
    command = [
        'xelatex', '-jobname=football_daily_report', '-interaction=nonstopmode',
        '-halt-on-error', '-output-directory=' + pdf_dir,
        'football_daily_report_typography.tex'
    ]
    for _ in range(2):
        subprocess.run(command, cwd=project_dir, check=True)
    print('Save as PDF:', os.path.join(pdf_dir, 'football_daily_report.pdf'))

def content_crop_box(image, padding=PNG_PAGE_CONTENT_PADDING_PX):
    """计算页面内容的裁切范围，同时保留少量安全边距。"""
    rgb_image = image.convert('RGB')
    difference = ImageChops.difference(rgb_image, Image.new('RGB', rgb_image.size, 'white'))
    content_box = difference.convert('L').point(lambda value: 255 if value > 12 else 0).getbbox()
    if not content_box:
        return (0, 0, rgb_image.width, rgb_image.height)
    left, top, right, bottom = content_box
    return (max(0, left - padding), max(0, top - padding),
            min(rgb_image.width, right + padding), min(rgb_image.height, bottom + padding))

def remove_repeated_page_header(image):
    """裁掉重复页眉，并返回裁后图像及首行正文前实际保留的像素距离。"""
    rgb_image = image.convert('RGB')
    difference = ImageChops.difference(rgb_image, Image.new('RGB', rgb_image.size, 'white'))
    mask = difference.convert('L').point(lambda value: 255 if value > 12 else 0)
    header_rule_bottom = 0
    rule_threshold = max(3, round(rgb_image.width * 0.1))
    for row in range(round(rgb_image.height * 0.35)):
        red_pixels = sum(1 for red, green, blue in
                         (rgb_image.getpixel((column, row)) for column in range(rgb_image.width))
                         if red > 140 and red > green * 1.35 and red > blue * 1.35)
        if red_pixels >= rule_threshold:
            header_rule_bottom = row + 1

    if not header_rule_bottom:
        return rgb_image, 0
    start_row = header_rule_bottom + 1
    activity_threshold = max(3, rgb_image.width // 100)
    safety_padding = round(PNG_RENDER_DPI * PNG_CONTINUATION_CROP_PADDING_MM / 25.4)
    for row in range(start_row, round(rgb_image.height * 0.35)):
        activity = sum(mask.crop((0, row, rgb_image.width, min(row + 4, rgb_image.height))).histogram()[1:])
        if activity >= activity_threshold:
            crop_start = max(start_row, row - safety_padding)
            return rgb_image.crop((0, crop_start, rgb_image.width, rgb_image.height)), row - crop_start
    return rgb_image, 0
def stack_pages_vertically(pages, gap_pixels=0):
    """按阅读顺序拼接已裁边的页面，并保留统一的页间距。"""
    target_width = pages[0].width
    if any(page.width != target_width for page in pages):
        raise ValueError('拼接页面的横向裁切范围不一致。')
    total_height = sum(page.height for page in pages) + gap_pixels * (len(pages) - 1)
    combined = Image.new('RGBA', (target_width, total_height), (255, 255, 255, 255))
    offset = 0
    for page in pages:
        combined.alpha_composite(page, (0, offset))
        offset += page.height + gap_pixels
    return combined

def export_report_pngs(project_dir):
    """导出裁边后的单页 PNG，并按统一间距纵向拼接为长图。"""
    pdf_path = os.path.join(project_dir, 'output', 'pdf', 'football_daily_report.pdf')
    png_dir = os.path.join(project_dir, 'output', 'png')
    os.makedirs(png_dir, exist_ok=True)
    for old_page in glob(os.path.join(png_dir, 'football_daily_report_page_*.png')):
        os.remove(old_page)

    with tempfile.TemporaryDirectory() as render_dir:
        render_prefix = os.path.join(render_dir, 'report_page')
        subprocess.run(['pdftoppm', '-png', '-r', str(PNG_RENDER_DPI), pdf_path, render_prefix], check=True)
        rendered_pages = sorted(
            glob(render_prefix + '-*.png'),
            key=lambda path: int(re.search(r'-(\d+)\.png$', path).group(1)))
        if not rendered_pages:
            raise RuntimeError('PDF 未生成可导出的页面 PNG。')

        page_images = []
        crop_boxes = []
        for page_path in rendered_pages:
            with Image.open(page_path) as page_image:
                page_images.append(page_image.convert('RGBA'))
                crop_boxes.append(content_crop_box(page_image))

        shared_left = min(crop_box[0] for crop_box in crop_boxes)
        shared_right = max(crop_box[2] for crop_box in crop_boxes)
        cropped_pages = []
        for index, (page_image, crop_box) in enumerate(zip(page_images, crop_boxes), start=1):
            cropped_page = page_image.crop((shared_left, crop_box[1], shared_right, crop_box[3]))
            output_path = os.path.join(png_dir, 'football_daily_report_page_%d.png' % index)
            cropped_page.save(output_path)
            cropped_pages.append(cropped_page)

    combined_pages = list(cropped_pages)
    continuation_padding_pixels = 0
    if len(combined_pages) > 1:
        original_height = combined_pages[1].height
        cropped_continuation, continuation_padding_pixels = remove_repeated_page_header(combined_pages[1])
        combined_pages[1] = cropped_continuation.convert('RGBA')
        print('Removed repeated page header: %dpx -> %dpx; preserved top padding: %dpx.' %
              (original_height, combined_pages[1].height, continuation_padding_pixels))
    # 用实际保留的顶部安全距离反向补偿拼接空白，保持总视觉距离与原版一致。
    join_gap_pixels = max(0, round(PNG_RENDER_DPI * PNG_PAGE_JOIN_GAP_MM / 25.4)
                          + PNG_PAGE_CONTENT_PADDING_PX - continuation_padding_pixels)
    combined = stack_pages_vertically(combined_pages, join_gap_pixels)
    combined_path = os.path.join(png_dir, 'football_daily_report_combined.png')
    combined.save(combined_path)
    print('Save page PNGs and combined PNG:', combined_path)

    
datalist = []
html = askURL(baseurl)
for item in re.findall(findItem, html):
    item  = str(item)
    data = []
    if re.findall(r'".*?"', item)[0]=='"match"':
        event = re.findall(r'"match_title":"(.*?)",', item)[0].encode('utf-8').decode('raw_unicode_escape')
        data.append(event)
        date  = re.findall(r'"date_utc":"(.*?)",', item)[0]
        time  = re.findall(r'"time_utc":"(.*?)",', item)[0]
        start = re.findall(r'"start_play":"(.*?)",', item)[0] 
        utc_time = date+'T'+time
        utc_start= start.split(' ')[0]+'T'+start.split(' ')[1] 
        try:
            beijing_time=datetime.strptime(utc_start,"%Y-%m-%dT%H:%M:%S")+timedelta(hours=8)
            data.append(beijing_time.strftime("%Y-%m-%dT%H:%M:%S").replace('T', ' '))
        except:
            data.append("-")
        teamA = re.findall(r'"team_A_name":"(.*?)",', item)[0].encode('utf-8').decode('raw_unicode_escape')
        data.append(teamA)
        scoreA= re.findall(r'"fs_A":"(.*?)",', item)[0]
        if len(scoreA) !=0:
            scoreB= re.findall(r'"fs_B":"(.*?)",', item)[0]
            score = scoreA+"-"+scoreB
            data.append(score)
        else:
            data.append('vs')
        teamB = re.findall(r'"team_B_name":"(.*?)",', item)[0].encode('utf-8').decode('raw_unicode_escape')
        data.append(teamB)
        datalist.append(data)

# 将数据保存至项目目录，避免依赖旧的个人磁盘路径。
project_dir = os.path.dirname(os.path.abspath(__file__))
output_dir = os.path.join(project_dir, 'output', 'data')
os.makedirs(output_dir, exist_ok=True)
try:
    saveData(datalist, os.path.join(output_dir, 'FootballGames'), 'xls')
except PermissionError:
    print('Excel 文件被占用，跳过 XLS 覆盖；继续生成 LaTeX 与 PDF。')
save_latex_content(datalist, os.path.join(output_dir, 'matches_content.tex'),
                   os.path.join(output_dir, 'matches_meta.tex'))
compile_daily_report(project_dir)
export_report_pngs(project_dir)
