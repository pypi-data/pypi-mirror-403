import re
from typing import List, Set, Optional
from .utils import load_rules
from .engines import AdRulesEngine

# 檢查 lxml 是否可用
try:
    from lxml import html
    HAS_LXML = True
except ImportError:
    HAS_LXML = False

class Renovator:
    def __init__(
        self, 
        rules_list: List[str], 
        dom_parser: str = "lxml",
        **kwargs # 允許接收不使用的參數以保持兼容性
    ):
        """
        :param rules_list: 規則 URL 或檔案路徑列表
        :param dom_parser: 'lxml' (推薦) 或 'bs4'
        """
        self.dom_parser = dom_parser
        self.raw_rules = load_rules(rules_list)
        
        # 始終使用純 Python 引擎
        self.engine = AdRulesEngine()
        self.engine.load_rules(self.raw_rules)

    def clean(self, html_content: str, url: str) -> str:
        """
        清理 HTML 中的廣告元素
        """
        if not html_content: return ""

        # 1. 獲取理論上適用於該 URL 的所有規則 (可能包含數萬條通用規則)
        selectors = self.engine.get_hidden_selectors(url)
        
        if not selectors: return html_content

        # 2. 根據解析器選擇路徑
        if HAS_LXML and self.dom_parser == "lxml":
            return self._clean_lxml(html_content, selectors)
        else:
            if self.dom_parser == "lxml":
                print("[Renovation-Ad] Warning: lxml not installed, falling back to bs4.")
            return self._clean_bs4(html_content, selectors)

    def _clean_lxml(self, html_content: str, selectors: Set[str]) -> str:
        """
        LXML 極速模式，包含 'DOM 內容感知過濾' (Bloom Filter Strategy)
        """
        try:
            # lxml 解析速度極快
            doc = html.fromstring(html_content)
        except Exception:
            # 解析失敗通常是因為編碼或空內容，原樣返回
            return html_content

        # === 優化核心: DOM 內容感知 ===
        # 提取文檔中實際存在的 ID 和 Class
        doc_ids = set(doc.xpath('//@id'))
        
        doc_classes = set()
        # class 屬性可能包含多個值 (例如 "ad visible")，需要拆分
        for c in doc.xpath('//@class'):
            doc_classes.update(c.split())

        # 過濾掉那些 HTML 裡根本不存在的 ID/Class 的規則
        relevant_selectors = self._filter_selectors_by_content(selectors, doc_ids, doc_classes)
        
        # 如果過濾後沒有規則了，直接返回
        if not relevant_selectors:
            return html.tostring(doc, encoding='unicode')

        # === 批次執行刪除 ===
        # 鎖定 Body 減少遍歷範圍
        body = doc.find("body")
        target_root = body if body is not None else doc
        
        removed_count = 0
        # 經過過濾後規則通常很少且精準，批次可以很大
        BATCH_SIZE = 500 
        
        sel_list = list(relevant_selectors)

        for i in range(0, len(sel_list), BATCH_SIZE):
            batch = sel_list[i : i + BATCH_SIZE]
            combined = ", ".join(batch)
            
            try:
                # cssselect 將 CSS 轉為 XPath 執行
                elements = target_root.cssselect(combined)
                for el in elements:
                    parent = el.getparent()
                    if parent is not None:
                        parent.remove(el)
                        removed_count += 1
            except Exception:
                # 若批次中有語法錯誤導致失敗，降級為逐個執行
                for s in batch:
                    try:
                        for el in target_root.cssselect(s):
                            if el.getparent() is not None:
                                el.getparent().remove(el)
                                removed_count += 1
                    except: pass

        return html.tostring(doc, encoding='unicode')

    def _filter_selectors_by_content(self, selectors: Set[str], doc_ids: Set[str], doc_classes: Set[str]) -> Set[str]:
        """
        啟發式過濾：如果選擇器依賴某個 ID (#id) 或 Class (.class)，
        但該 ID/Class 不在 doc_ids/doc_classes 中，則丟棄。
        """
        valid = set()
        
        for sel in selectors:
            # 排除不支援的複雜語法，避免 cssselect 報錯或效能低落
            # 例如 :-abp-has, :xpath, [-abp-properties]
            if any(x in sel for x in [":-abp", ":xpath", ":has", "[-abp", "[style"]):
                continue

            # 檢查 ID 依賴
            if '#' in sel:
                # 匹配 #word 
                match = re.search(r'#([\w-]+)', sel)
                if match:
                    req_id = match.group(1)
                    if req_id not in doc_ids:
                        continue 

            # 檢查 Class 依賴
            if '.' in sel:
                # 匹配 .word
                match = re.search(r'\.([\w-]+)', sel)
                if match:
                    req_class = match.group(1)
                    if req_class not in doc_classes:
                        continue 
            
            valid.add(sel)
            
        return valid

    def _clean_bs4(self, html_content, selectors):
        """BeautifulSoup 相容模式 (無內容感知優化，較慢)"""
        from bs4 import BeautifulSoup
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
        except: return html_content

        # 簡單過濾不支援的語法
        safe_selectors = [s for s in selectors if ":-abp" not in s]
        
        # 限制處理數量，避免 BS4 卡死
        limit = 2000 
        if len(safe_selectors) > limit:
            safe_selectors = safe_selectors[:limit]

        # 小批次處理
        for i in range(0, len(safe_selectors), 30):
            try:
                combined = ", ".join(safe_selectors[i:i+30])
                for el in soup.select(combined):
                    el.decompose()
            except: pass
        
        return str(soup)

def clean_html(html_content: str, url: str, rules_list: List[str], dom_parser: str = "lxml") -> str:
    """快速調用接口"""
    renovator = Renovator(rules_list, dom_parser=dom_parser)
    return renovator.clean(html_content, url)