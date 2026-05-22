import os
import json
from pathlib  import Path

BASE = Path(__file__).parent.parent
RAW_DATA = BASE/"raw_data"/"dialogues"
OUT_JSON = BASE/"raw_data"/"raw_dialogues.json"
ALL_DATA = []
for subdir in ["A_first_time","B_family"]:
    folder = RAW_DATA/subdir
    for file in folder.glob("*.json"):
        with open(file,"r",encoding="utf-8") as f:
            data = json.load(f)
            ALL_DATA.append(data)
            
with open(OUT_JSON,"w",encoding="utf-8") as f:    
    json.dump(ALL_DATA,f,ensure_ascii = False,indent = 2)   
    
print(f"合并完成，合并了{len(ALL_DATA)}行，输出文件：{OUT_JSON}") 
            
            
