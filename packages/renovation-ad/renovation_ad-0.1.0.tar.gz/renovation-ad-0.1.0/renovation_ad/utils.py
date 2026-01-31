import os
import requests
from typing import List

def load_rules(rules_list: List[str]) -> List[str]:
    """
    從 URL、檔案路徑或字串列表中載入規則
    """
    consolidated_rules = []
    
    for item in rules_list:
        item = item.strip()
        if not item:
            continue
            
        # 1. 處理 URL
        if item.startswith("http://") or item.startswith("https://"):
            try:
                print(f"正在下載規則: {item} ...")
                response = requests.get(item, timeout=15)
                response.raise_for_status()
                consolidated_rules.extend(response.text.splitlines())
            except Exception as e:
                print(f"[Renovation-Ad] 警告: 無法下載規則 {item}: {e}")
        
        # 2. 處理本地檔案
        elif os.path.exists(item):
            try:
                with open(item, 'r', encoding='utf-8') as f:
                    consolidated_rules.extend(f.read().splitlines())
            except Exception as e:
                print(f"[Renovation-Ad] 警告: 無法讀取檔案 {item}: {e}")
        
        # 3. 視為原始規則字串
        else:
            consolidated_rules.append(item)
            
    return consolidated_rules