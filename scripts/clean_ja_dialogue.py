# -*- coding: utf-8 -*-
"""
日语对话语料清洗脚本
功能：去噪 / 统一ですます体 / 去中式日语 / 情绪标签 / 过滤不良内容
"""
import json
import re
from pathlib import Path

# ===================== 1. 配置路径 =====================
BASE_DIR = Path(__file__).parent.parent
RAW_PATH = BASE_DIR / "raw_data" /"raw_dialogues.json"
CLEAN_CSV = BASE_DIR / "cleaned_data" / "cleaned_dialogue.csv"
CLEAN_JSONL = BASE_DIR / "cleaned_data" / "cleaned_dialogue.jsonl"

# 确保输出目录存在
CLEAN_CSV.parent.mkdir(parents=True, exist_ok=True)

# ===================== 2. 规则库 =====================

# 中式日语黑名单（简单替换，实际项目中建议用更精准的方式）
CHINESE_JA_PATTERNS = {
    r"私は": "",
    r"あなたは": "",
    r"とても": "とっても",
    r"すごく": "すごく",
    r"本当に": "ほんとに",
    r"非常に": "とても",
    r"私の": "私の",
    r"あなたの": "",
    r"よく": "",
    r"ぜひ": "",
}

# 不良内容关键词
BAD_WORDS = ["暴力", "犯罪", "卑猥", "脅迫", "差別"]

# 情绪标签映射（正则匹配）
EMOTION_PATTERNS = [
    (r"(嬉しい|楽しい|好き|うれしい|大好き|楽し|素敵|いいね|よかった)", "happy"),
    (r"(悲しい|寂しい|嫌い|苦手|つらい|残念|悲し|淋しい)", "sad"),
    (r"(怒る|腹立たしい|イライラ|ムカつく|怒|ムカ)", "angry"),
    (r"(どうして|なんで|どう|何|なに|か|？|？)", "question"),
]

# ===================== 3. 清洗函数 =====================

def load_raw_data():
    """加载原始JSON，展平嵌套的utterance列表"""
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # 如果是列表（多个对话），遍历；如果是单个字典，包成列表
    if not isinstance(data, list):
        data = [data]
    
    all_utterances = []
    for dialogue in data:
        dialogue_id = dialogue.get("dialogue_id", "unknown")
        dialogue_type = dialogue.get("dialogue_type", "unknown")
        
        for utt in dialogue.get("utterances", []):
            all_utterances.append({
                "dialogue_id": dialogue_id,
                "dialogue_type": dialogue_type,
                "utterance_id": utt.get("utterance_id"),
                "speaker": utt.get("interlocutor_id"),
                "text": utt.get("text", ""),
                "mention_to": utt.get("mention_to", []),
            })
    
    print(f"原始对话数：{len(data)}，总utterance数：{len(all_utterances)}")
    return all_utterances


def remove_noise(text):
    """去噪：删除多余空格、控制字符，保留日语、中文、基本标点"""
    if not isinstance(text, str):
        text = str(text) if text is not None else ""
    
    # 删除控制字符（除了换行）
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
    
    # 统一空格：全角空格、多个半角空格 → 单个半角空格
    text = re.sub(r'[\u3000\s]+', ' ', text).strip()
    
    return text


def remove_chinese_ja(text):
    """去除中式日语（简单版）"""
    for pattern, repl in CHINESE_JA_PATTERNS.items():
        text = re.sub(pattern, repl, text)
    return text.strip()


def to_desumasu(text):
    """
    统一ですます体（简化版，处理常见结尾）
    注意：完整版需要MeCab做形态素解析，这里先用规则覆盖大部分情况
    """
    # 名词/形容动词 + だ → です
    # 注意：只替换句尾的"だ"，避免替换"まだ"等词中间的"だ"
    text = re.sub(r'(?<![まひそ])だ(?=[。！？\s]|$)', 'です', text)
    
    # 动词简体 → ます形（简化规则，仅处理常见结尾）
    # る → ます（一段动词）
    text = re.sub(r'([いきしちにひみりえけせてねへめれ])る(?=[。！？\s]|$)', r'\1ます', text)
    
    # う段结尾的五段动词 → い段 + ます（简化，可能不完全准确）
    text = re.sub(r'([わかさたなはまやらがざだばぱ])(?=[。！？\s]|$)', r'\1います', text)
    
    # った → りました（过去式）
    text = re.sub(r'([いきしちにひみり])った(?=[。！？\s]|$)', r'\1りました', text)
    
    return text


def filter_bad_content(text):
    """过滤不良内容"""
    for word in BAD_WORDS:
        if word in text:
            return ""  # 包含不良词，整句删除
    return text


def add_emotion_label(text):
    """自动打情绪标签"""
    for pattern, label in EMOTION_PATTERNS:
        if re.search(pattern, text):
            return label
    return "neutral"


# ===================== 4. 主清洗流程 =====================

def clean_dialogue():
    # 1. 加载并展平数据
    records = load_raw_data()
    
    cleaned_records = []
    
    for record in records:
        text = record["text"]
        
        # 2. 去噪
        text = remove_noise(text)
        if not text:
            continue
        
        # 3. 去除中式日语
        text = remove_chinese_ja(text)
        
        # 4. 统一ですます体
        text_clean = to_desumasu(text)
        
        # 5. 过滤不良内容
        text_clean = filter_bad_content(text_clean)
        if not text_clean:
            continue
        
        # 6. 打情绪标签
        emotion = add_emotion_label(text_clean)
        
        cleaned_records.append({
            "dialogue_id": record["dialogue_id"],
            "dialogue_type": record["dialogue_type"],
            "utterance_id": record["utterance_id"],
            "speaker": record["speaker"],
            "text_original": record["text"],      # 保留原文
            "text_clean": text_clean,              # 清洗后
            "emotion": emotion,
            "mention_to": record["mention_to"],
        })
    
    print(f"清洗后条数：{len(cleaned_records)}")
    
    # 7. 保存 CSV
    import csv
    with open(CLEAN_CSV, "w", encoding="utf-8-sig", newline="") as f:
        if cleaned_records:
            writer = csv.DictWriter(f, fieldnames=cleaned_records[0].keys())
            writer.writeheader()
            writer.writerows(cleaned_records)
    
    # 8. 保存 JSONL
    with open(CLEAN_JSONL, "w", encoding="utf-8") as f:
        for record in cleaned_records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    print(f"CSV保存路径：{CLEAN_CSV}")
    print(f"JSONL保存路径：{CLEAN_JSONL}")
    
    return cleaned_records


if __name__ == "__main__":
    clean_dialogue()