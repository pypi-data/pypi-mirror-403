import abc
from urllib.parse import urlparse
from typing import List, Set, Dict

class AdRulesEngine:
    """
    純 Python 實現的規則解析器。
    專注於解析 EasyList 格式的 Cosmetic Rules (##.classname)。
    """
    def __init__(self):
        # 結構: List of dict
        self.cosmetic_rules: List[Dict] = []

    def load_rules(self, rules: List[str]):
        """
        解析規則列表，提取 CSS 隱藏規則。
        """
        for rule in rules:
            rule = rule.strip()
            # 快速過濾無效行
            if len(rule) < 3 or "##" not in rule or rule.startswith("!"):
                continue
            
            parts = rule.split("##", 1)
            # 排除 script:inject 或其他過於複雜的非 CSS 語法
            if len(parts) != 2: 
                continue

            domain_part = parts[0]
            selector = parts[1]

            include_domains = set()
            exclude_domains = set()

            if domain_part:
                for d in domain_part.split(','):
                    d = d.strip()
                    if not d: continue
                    if d.startswith('~'):
                        exclude_domains.add(d[1:])
                    else:
                        include_domains.add(d)
            
            self.cosmetic_rules.append({
                'include': include_domains,
                'exclude': exclude_domains,
                'selector': selector
            })
        
        # 雖然 Python 解析快，但如果規則有數萬條，可以考慮在此處去重 (Optional)

    def get_hidden_selectors(self, url: str) -> Set[str]:
        """
        根據 URL 返回該頁面適用的所有 CSS 選擇器。
        """
        if not url:
            return set()
            
        parsed = urlparse(url)
        hostname = parsed.netloc.lower()
        # 移除端口號
        if ":" in hostname: 
            hostname = hostname.split(":")[0]

        active_selectors = set()
        
        for rule in self.cosmetic_rules:
            # 1. 排除檢查 (Domain Exclusion)
            if rule['exclude']:
                if any(ed in hostname for ed in rule['exclude']):
                    continue
            
            # 2. 包含檢查 (Domain Inclusion)
            if not rule['include']:
                # 通用規則
                active_selectors.add(rule['selector'])
            else:
                # 特定域名規則 (檢查是否為子域名或完全匹配)
                if any(id in hostname for id in rule['include']):
                    active_selectors.add(rule['selector'])

        return active_selectors