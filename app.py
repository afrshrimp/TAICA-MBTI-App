"""
TAICA 期末專案修正版
題目：AI 讀心術：結合語意分析與 MBTI 理論的次世代性格檢測工具
說明：本系統為課程展示與人格傾向探索用途，非正式心理診斷工具。
"""

import base64
import html
import io
import json
import random
import re
import textwrap
from datetime import datetime
from pathlib import Path
import zipfile
from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go
import streamlit as st
from groq import Groq

try:
    from PIL import Image as PILImage, ImageDraw, ImageFont
except Exception:
    PILImage = None
    ImageDraw = None
    ImageFont = None

try:
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.platypus import Image as RLImage
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
except Exception:
    colors = None
    TA_CENTER = None
    TA_LEFT = None
    A4 = None
    ParagraphStyle = None
    getSampleStyleSheet = None
    cm = None
    pdfmetrics = None
    TTFont = None
    UnicodeCIDFont = None
    RLImage = None
    PageBreak = None
    Paragraph = None
    SimpleDocTemplate = None
    Spacer = None
    Table = None
    TableStyle = None


# ============================================================
# 1. 基本設定與題庫
# ============================================================
APP_TITLE = "AI 讀心術：結合語意分析與 MBTI 理論的次世代性格檢測工具"
APP_SUBTITLE = "以選項輔助、開放式回答、語意分析與 MBTI 四向度架構，免費產生中文類型與進階人格報告"
TOTAL_QUESTIONS = 16
DEFAULT_MODEL = "llama-3.1-8b-instant"

# 分數定義：分數越高越偏左側字母，越低越偏右側字母。
DIMENSION_RULES = {
    "E-I": {"high": "E", "low": "I", "label": "外向 E / 內向 I"},
    "S-N": {"high": "S", "low": "N", "label": "實感 S / 直覺 N"},
    "T-F": {"high": "T", "low": "F", "label": "思考 T / 情感 F"},
    "J-P": {"high": "J", "low": "P", "label": "判斷 J / 感知 P"},
}

Q_BANK = {
    "E-I": [
        "放假喜歡一個人宅著，還是跟朋友出門去玩？",
        "到陌生的聚會，你會主動跟人搭話嗎？",
        "心情不好時，喜歡找人傾訴還是自己消化？",
        "在人群中，你通常是說話的人還是聽別人說？",
    ],
    "S-N": [
        "買東西是看實用性，還是憑感覺和設計？",
        "你喜歡按部就班，還是充滿驚喜的生活？",
        "你比較常想著『現在該做什麼』還是『未來會怎樣』？",
        "看電影時，你注意畫面細節還是整體的意境？",
    ],
    "T-F": [
        "朋友遇到困難，你先幫他想辦法還是先安慰他？",
        "做決定時，你更相信客觀邏輯還是內心直覺？",
        "看比賽時，你在乎誰贏，還是過程精不精彩？",
        "你覺得『講道理』比較重要，還是『顧及感受』？",
    ],
    "J-P": [
        "出門旅行會排好行程，還是走到哪玩到哪？",
        "你的桌面通常是乾淨整齊的，還是亂中有序？",
        "喜歡提前把作業做完，還是最後一刻才趕工？",
        "買東西會先列好清單，還是看到喜歡就買？",
    ],
}


# 每題提供參考選項，降低使用者必須自行打字的負擔。
# 選項僅作為作答輔助；若使用者選擇「以上皆非」，仍可輸入個人化回答。
OPTION_BANK = {
    "放假喜歡一個人宅著，還是跟朋友出門去玩？": [
        "我比較喜歡一個人休息，讓自己恢復能量。",
        "我喜歡找朋友出門，聊天或活動會讓我更有精神。",
        "看當天狀態，有時想獨處，有時想跟朋友出去。",
        "我通常會先安排好想做的事，再決定要不要約人。",
    ],
    "到陌生的聚會，你會主動跟人搭話嗎？": [
        "我會主動開話題，認識新朋友對我來說不困難。",
        "我通常會先觀察環境，等別人來找我比較自在。",
        "如果氣氛自然或有人介紹，我才會比較願意聊天。",
        "我會選擇跟少數人深聊，而不是到處交際。",
    ],
    "心情不好時，喜歡找人傾訴還是自己消化？": [
        "我會找信任的人說出來，講完會比較舒服。",
        "我比較習慣自己整理情緒，不太想立刻說。",
        "我會先自己想一想，真的受不了才找人聊。",
        "我會用做事、運動或娛樂轉移注意力。",
    ],
    "在人群中，你通常是說話的人還是聽別人說？": [
        "我常常是帶動話題或分享想法的人。",
        "我比較常聽別人說，必要時才表達意見。",
        "熟人面前比較會說話，陌生人面前會安靜。",
        "我會看場合，有需要時才主動發言。",
    ],
    "買東西是看實用性，還是憑感覺和設計？": [
        "我會先看功能、價格與實用性。",
        "我很在意設計、氛圍和第一眼感覺。",
        "我會在實用與喜歡之間取得平衡。",
        "如果很喜歡，即使不是最實用也可能會買。",
    ],
    "你喜歡按部就班，還是充滿驚喜的生活？": [
        "我喜歡穩定、有規律、可預期的生活。",
        "我喜歡變化和新鮮感，不想每天都一樣。",
        "大方向穩定就好，小地方可以有驚喜。",
        "我會依照目標與當下心情調整生活方式。",
    ],
    "你比較常想著『現在該做什麼』還是『未來會怎樣』？": [
        "我比較重視現在要完成的事情。",
        "我常常思考未來可能性和長遠發展。",
        "我會先處理眼前問題，但也會想未來方向。",
        "我容易想到很多可能情境，再回頭安排現在。",
    ],
    "看電影時，你注意畫面細節還是整體的意境？": [
        "我會注意畫面、道具、台詞和具體細節。",
        "我比較在意整體氛圍、象徵意義和情緒感受。",
        "劇情合理性和整體感覺我都會注意。",
        "我通常會思考導演想表達的深層概念。",
    ],
    "朋友遇到困難，你先幫他想辦法還是先安慰他？": [
        "我會先幫他分析問題，找出可行解法。",
        "我會先安慰他，讓他覺得有人理解。",
        "我會先聽他說，再判斷要安慰還是給建議。",
        "我會陪他整理情緒，之後再一起想辦法。",
    ],
    "做決定時，你更相信客觀邏輯還是內心直覺？": [
        "我比較相信資料、邏輯和利弊分析。",
        "我比較相信內心感受與直覺判斷。",
        "我會先分析，再確認自己的感覺能不能接受。",
        "我會考慮這個決定對人際關係的影響。",
    ],
    "看比賽時，你在乎誰贏，還是過程精不精彩？": [
        "我比較在乎結果，輸贏很重要。",
        "我比較在乎過程是否精彩、有沒有感動。",
        "結果和過程我都會在意。",
        "我會看參賽者的努力與故事，而不只看分數。",
    ],
    "你覺得『講道理』比較重要，還是『顧及感受』？": [
        "我覺得講清楚道理與原則比較重要。",
        "我覺得顧及對方感受比較重要。",
        "我希望道理要講，但語氣也不能傷人。",
        "我會依照對象和情境調整表達方式。",
    ],
    "出門旅行會排好行程，還是走到哪玩到哪？": [
        "我會先安排好行程、交通與時間。",
        "我喜歡自由探索，走到哪玩到哪。",
        "我會排大方向，但保留彈性時間。",
        "我會先列想去的地方，到現場再調整順序。",
    ],
    "你的桌面通常是乾淨整齊的，還是亂中有序？": [
        "我喜歡桌面整齊，東西要放在固定位置。",
        "我的桌面可能看起來亂，但我知道東西在哪裡。",
        "忙的時候會亂，事情結束後會整理。",
        "我只整理必要區域，不一定追求完全整齊。",
    ],
    "喜歡提前把作業做完，還是最後一刻才趕工？": [
        "我喜歡提前完成，避免最後壓力太大。",
        "我常常到最後一刻才比較有動力完成。",
        "重要的會提早做，普通的可能拖到後面。",
        "我會先想架構，真正完成可能接近截止前。",
    ],
    "買東西會先列好清單，還是看到喜歡就買？": [
        "我會先列清單，照需求購買。",
        "我看到喜歡的東西就可能直接買。",
        "我會有清單，但也會保留臨時購買的彈性。",
        "我會先比價或查資料，再決定要不要買。",
    ],
}

CUSTOM_OPTION = "以上皆非，我想自己回答"


# ============================================================
# 2. 頁面配置與 CSS
# ============================================================
st.set_page_config(
    page_title="TAICA MBTI AI 讀心術",
    page_icon="🧠",
    layout="wide",
)

st.markdown(
    """
    <style>
    .stApp {
        background-color: #FFF5F7;
        color: #5D4037;
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    }
    .main-title {
        color: #FF7EB3;
        text-align: center;
        font-size: 2.45rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        text-shadow: 1px 1px 2px #FFD1DC;
    }
    .subtitle {
        color: #6D4C41;
        text-align: center;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .question-box {
        background: #FFFFFF;
        border: 2px solid #FFD1DC;
        padding: 25px;
        border-radius: 20px;
        margin: 20px 0;
        box-shadow: 0 4px 10px rgba(255, 126, 179, 0.1);
    }
    .report-card {
        background: #FFFFFF;
        border: 2px dashed #FF9A9E;
        padding: 30px;
        border-radius: 25px;
        color: #5D4037;
        line-height: 1.8;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
    }
    .method-card {
        background: #FFFFFF;
        border-left: 6px solid #FF9A9E;
        padding: 18px 22px;
        border-radius: 14px;
        margin: 12px 0 20px 0;
        line-height: 1.7;
    }
    .stButton>button {
        background: linear-gradient(90deg, #FF9A9E 0%, #FECFEF 100%);
        color: #5D4037;
        font-weight: bold;
        border-radius: 30px;
        width: 100%;
        border: none;
        height: 3em;
        box-shadow: 0 4px 10px rgba(255, 154, 158, 0.3);
        transition: 0.3s;
    }
    .stButton>button:hover {
        transform: scale(1.02);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 3. 工具函式：狀態、分數驗證、JSON 解析、圖表
# ============================================================
def make_questions() -> List[Dict[str, str]]:
    """將四個 MBTI 向度題庫展開，並隨機排序。"""
    questions = [{"dim": dim, "q": q} for dim, qs in Q_BANK.items() for q in qs]
    random.shuffle(questions)
    return questions


def init_session_state() -> None:
    """初始化 Streamlit session state。"""
    if "app_initialized" not in st.session_state:
        st.session_state.update(
            {
                "app_initialized": True,
                "test_started": False,
                "step": 1,
                "history": [],
                "nickname": "",
                "profile_note": "不透露",
                "questions": make_questions(),
                "analysis_result": None,
            }
        )


def reset_test() -> None:
    """重置測驗。刪除時必須先轉成 list，避免迭代中修改 session_state。"""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


def safe_score(value: Any, default: int = 50) -> int:
    """將模型輸出的分數轉成 0 到 100 的整數。"""
    try:
        score = int(round(float(value)))
        return max(0, min(100, score))
    except (TypeError, ValueError):
        return default


def validate_scores(raw_scores: Dict[str, Any]) -> Dict[str, int]:
    """確保四個向度皆有合理分數。"""
    return {dim: safe_score(raw_scores.get(dim, 50)) for dim in DIMENSION_RULES.keys()}


def infer_mbti_type(scores: Dict[str, int]) -> str:
    """
    依照分數推導 MBTI 類型。
    分數越高越偏左側字母，越低越偏右側字母。
    50 分以上採左側字母，低於 50 採右側字母。
    注意：若分數落在 45 到 55，報告文字應描述為「接近中間」，但類型仍需為了顯示結果而擇一。
    """
    mbti = []
    for dim, rule in DIMENSION_RULES.items():
        mbti.append(rule["high"] if scores.get(dim, 50) >= 50 else rule["low"])
    return "".join(mbti)


def extract_json_from_text(text: str) -> Tuple[Dict[str, Any], str]:
    """
    從 LLM 回覆中擷取 JSON。
    優先讀取 ```json ... ``` 區塊；若失敗，再嘗試從全文逐段解析 JSON 物件。
    """
    if not text:
        return {}, ""

    fenced_match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    if fenced_match:
        json_text = fenced_match.group(1).strip()
        data = json.loads(json_text)
        report_text = text.replace(fenced_match.group(0), "").strip()
        return data, report_text

    decoder = json.JSONDecoder()
    for match in re.finditer(r"\{", text):
        try:
            data, end_idx = decoder.raw_decode(text[match.start() :])
            if isinstance(data, dict) and "scores" in data:
                report_text = (text[: match.start()] + text[match.start() + end_idx :]).strip()
                return data, report_text
        except json.JSONDecodeError:
            continue

    return {}, text.strip()


def parse_ai_response(raw_text: str) -> Dict[str, Any]:
    """解析模型回覆，並提供失敗時的安全預設值。"""
    default_scores = {dim: 50 for dim in DIMENSION_RULES.keys()}
    default_type = infer_mbti_type(default_scores)

    try:
        data, report = extract_json_from_text(raw_text)
        scores = validate_scores(data.get("scores", default_scores))
        # 為避免 LLM 文字與分數不一致，最終類型一律由程式端依分數推導。
        # 例如 S-N 分數偏 S，報告就不應輸出 N；T-F 也不可被誤寫成直覺。
        mbti_type = infer_mbti_type(scores)

        if not report:
            report = "AI 已完成分數判定，但未產生完整文字報告。建議重新生成一次分析。"

        return {
            "ok": True,
            "scores": scores,
            "type": mbti_type,
            "report": report,
            "raw": raw_text,
        }
    except Exception as exc:
        return {
            "ok": False,
            "scores": default_scores,
            "type": default_type,
            "report": f"AI 回覆格式解析失敗，系統已暫以中性分數顯示。錯誤原因：{exc}",
            "raw": raw_text,
        }


def draw_radar(scores: Dict[str, int], mbti_type: str) -> go.Figure:
    """繪製 MBTI 四向度雷達圖。"""
    categories = [
        "E-I\n外向/內向",
        "S-N\n實感/直覺",
        "T-F\n思考/情感",
        "J-P\n判斷/感知",
    ]
    values = [scores.get("E-I", 50), scores.get("S-N", 50), scores.get("T-F", 50), scores.get("J-P", 50)]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            fillcolor="rgba(255, 154, 158, 0.4)",
            line=dict(color="#FF7EB3", width=3),
            marker=dict(color="#FF7EB3", size=8),
            name=f"類型：{mbti_type}",
        )
    )
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 100], gridcolor="#FFE4E1"),
            angularaxis=dict(gridcolor="#FFE4E1", color="#5D4037"),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#5D4037"),
        margin=dict(l=40, r=40, t=50, b=40),
    )
    return fig


def draw_extended_traits_bar_chart(traits: Dict[str, int]) -> go.Figure:
    """繪製 12 項延伸特質分組長條圖，利於教師與使用者快速比較高低分布。"""
    trait_category = {
        "社交互動能量": ("社交能量", "#FF9A9E"),
        "獨處恢復能量": ("社交能量", "#FF9A9E"),
        "現實細節敏銳度": ("感知風格", "#F8BBD0"),
        "抽象想像延展力": ("感知風格", "#F8BBD0"),
        "邏輯決策強度": ("決策風格", "#CE93D8"),
        "同理協調強度": ("決策風格", "#CE93D8"),
        "規劃執行穩定度": ("執行節奏", "#90CAF9"),
        "彈性應變開放度": ("執行節奏", "#90CAF9"),
        "自我節奏掌控力": ("適配能力", "#A5D6A7"),
        "團隊溝通適配度": ("適配能力", "#A5D6A7"),
        "職涯探索適配度": ("適配能力", "#A5D6A7"),
        "壓力調節彈性": ("適配能力", "#A5D6A7"),
    }
    category_order = ["社交能量", "感知風格", "決策風格", "執行節奏", "適配能力"]
    ordered_items = sorted(
        traits.items(),
        key=lambda item: (category_order.index(trait_category[item[0]][0]), -item[1]),
    )

    labels = [f"{trait_category[name][0]}｜{name}" for name, _ in ordered_items]
    values = [value for _, value in ordered_items]
    colors = [trait_category[name][1] for name, _ in ordered_items]
    category_for_hover = [trait_category[name][0] for name, _ in ordered_items]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            text=[f"{v} / 100" for v in values],
            textposition="outside",
            marker=dict(color=colors, line=dict(color="#6D4C41", width=0.8)),
            customdata=category_for_hover,
            hovertemplate="類別：%{customdata}<br>%{y}<br>分數：%{x} / 100<extra></extra>",
        )
    )
    fig.add_vline(
        x=50,
        line_width=2,
        line_dash="dash",
        line_color="#8D6E63",
        annotation_text="50：中性參考線",
        annotation_position="top",
    )
    fig.update_layout(
        title="12 項延伸特質分組長條圖",
        xaxis=dict(range=[0, 100], title="分數", gridcolor="#FFE4E1"),
        yaxis=dict(title="特質類別｜特質項目", automargin=True),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#5D4037"),
        margin=dict(l=20, r=80, t=60, b=40),
        height=620,
    )
    fig.update_yaxes(autorange="reversed")
    return fig


def summarize_extended_traits(traits: Dict[str, int]) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """回傳前三高與前三低特質，作為結果頁的快速摘要。"""
    sorted_items = sorted(traits.items(), key=lambda item: item[1], reverse=True)
    return sorted_items[:3], sorted_items[-3:]


def find_cjk_font_path() -> Optional[str]:
    """尋找可支援繁體中文的字型，供圖片輸出使用。

    注意：不要使用 DejaVuSans 當後備字型，因為它不支援完整繁體中文，
    會造成手機 PDF 或 PNG 文字變成方塊。
    """
    candidates = [
        # Streamlit Cloud / Ubuntu after installing fonts-noto-cjk
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJKtc-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansTC-Regular.ttf",
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        # Windows
        r"C:/Windows/Fonts/msjh.ttc",
        r"C:/Windows/Fonts/msjh.ttf",
        r"C:/Windows/Fonts/mingliu.ttc",
        r"C:/Windows/Fonts/kaiu.ttf",
        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return path
    return None


def get_required_cjk_font_path() -> str:
    """取得 CJK 字型；若環境缺字型，直接提示修正方式。"""
    font_path = find_cjk_font_path()
    if not font_path:
        raise RuntimeError(
            "找不到可支援繁體中文的字型。若部署在 Streamlit Cloud，"
            "請新增 packages.txt 並寫入 fonts-noto-cjk；若在本機，請確認系統有微軟正黑體、明體、PingFang 或 Noto CJK。"
        )
    return font_path



def load_cjk_font(size: int):
    """載入真正可顯示繁體中文的字型。

    若字型檔是 .ttc，Pillow 預設可能載入 JP 索引；
    這裡優先使用 TC 索引，避免繁中輸出被替換成方塊。
    """
    font_path = get_required_cjk_font_path()
    suffix = Path(font_path).suffix.lower()
    if suffix == ".ttc":
        # NotoSansCJK-Regular.ttc 常見索引：0 JP、1 KR、2 SC、3 TC、4 HK
        preferred_indices = [3, 4, 2, 0, 1]
        last_error = None
        for idx in preferred_indices:
            try:
                font = ImageFont.truetype(font_path, size, index=idx)
                name = " ".join(font.getname())
                if any(token in name for token in ["TC", "HK", "CJK", "Microsoft", "PingFang", "Ming"]):
                    return font
            except Exception as exc:
                last_error = exc
        try:
            return ImageFont.truetype(font_path, size)
        except Exception as exc:
            raise RuntimeError(f"中文字型載入失敗：{font_path}；{exc or last_error}")
    return ImageFont.truetype(font_path, size)

def markdown_to_plain_text(markdown_text: str) -> str:
    """將報告中的 Markdown 簡化為純文字，方便輸出 PDF 與圖片。"""
    text = re.sub(r"```.*?```", "", markdown_text or "", flags=re.DOTALL)
    text = re.sub(r"#{1,6}\s*", "", text)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"^\s*[-*]\s+", "- ", text, flags=re.MULTILINE)
    return text.strip()


def markdown_to_simple_html(markdown_text: str) -> str:
    """將報告 Markdown 轉成簡易 HTML，不依賴額外套件。"""
    html_lines = []
    for raw_line in (markdown_text or "").splitlines():
        line = raw_line.strip()
        if not line:
            html_lines.append("<br>")
            continue
        clean = html.escape(line)
        clean = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", clean)
        if line.startswith("### "):
            html_lines.append(f"<h2>{clean[4:]}</h2>")
        elif line.startswith("#### "):
            html_lines.append(f"<h3>{clean[5:]}</h3>")
        elif line.startswith("##### "):
            html_lines.append(f"<h4>{clean[6:]}</h4>")
        elif re.match(r"^\d+[.、]", line):
            html_lines.append(f"<p class='item'>{clean}</p>")
        elif line.startswith("- "):
            html_lines.append(f"<p class='item'>{clean}</p>")
        else:
            html_lines.append(f"<p>{clean}</p>")
    return "\n".join(html_lines)


def fig_to_png_bytes(fig: go.Figure, scale: int = 2) -> Optional[bytes]:
    """將 Plotly 圖表匯出為 PNG。需要安裝 kaleido。"""
    try:
        return fig.to_image(format="png", scale=scale)
    except Exception:
        return None


def build_report_html(result: Dict[str, Any]) -> str:
    """建立可下載、可用瀏覽器列印為 PDF 的完整 HTML 報告。"""
    mbti_type = result["type"]
    type_info = get_type_info(mbti_type)
    traits = compute_extended_traits(result["scores"])
    top_traits, low_traits = summarize_extended_traits(traits)
    score_rows = "".join(
        f"<tr><td>{html.escape(dim)}</td><td>{html.escape(DIMENSION_RULES[dim]['label'])}</td><td>{score} / 100</td></tr>"
        for dim, score in result["scores"].items()
    )
    trait_rows = "".join(
        f"<tr><td>{html.escape(name)}</td><td>{value} / 100</td></tr>"
        for name, value in traits.items()
    )
    top_text = "、".join([f"{name} {value}" for name, value in top_traits])
    low_text = "、".join([f"{name} {value}" for name, value in low_traits])
    report_html = markdown_to_simple_html(result["report"])
    try:
        summary_b64 = base64.b64encode(build_report_summary_image(result)).decode("ascii")
        summary_image_html = f"<img src='data:image/png;base64,{summary_b64}' style='max-width:100%; border:1px solid #FFD1DC; border-radius:18px;' alt='報告摘要圖片'>"
    except Exception:
        summary_image_html = "<p>摘要圖片無法產生。</p>"
    try:
        traits_b64 = base64.b64encode(build_traits_chart_image(result)).decode("ascii")
        traits_image_html = f"<img src='data:image/png;base64,{traits_b64}' style='max-width:100%; border:1px solid #FFD1DC; border-radius:18px;' alt='12 項延伸特質長條圖'>"
    except Exception:
        traits_image_html = "<p>長條圖圖片無法產生。</p>"
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>{html.escape(APP_TITLE)} - {html.escape(type_display(mbti_type))}</title>
<style>
@page {{ size: A4; margin: 1.6cm; }}
body {{ font-family: 'Microsoft JhengHei', 'Noto Sans CJK TC', Arial, sans-serif; background: #FFF5F7; color: #5D4037; line-height: 1.75; }}
.report {{ max-width: 900px; margin: 0 auto; background: white; border: 2px solid #FFD1DC; border-radius: 24px; padding: 34px; box-shadow: 0 8px 28px rgba(255, 126, 179, 0.16); }}
h1 {{ color: #FF7EB3; text-align: center; margin-bottom: 8px; }}
.subtitle {{ text-align: center; color: #6D4C41; margin-bottom: 24px; }}
.badge {{ display: inline-block; padding: 8px 14px; border-radius: 999px; background: #FCE4EC; color: #AD1457; font-weight: 700; }}
.summary {{ border-left: 6px solid #FF9A9E; background: #FFF8FA; padding: 16px 18px; border-radius: 14px; margin: 18px 0; }}
table {{ width: 100%; border-collapse: collapse; margin: 12px 0 22px; }}
th, td {{ border-bottom: 1px solid #F8BBD0; padding: 9px 10px; text-align: left; }}
th {{ background: #FFF0F3; color: #6D4C41; }}
h2, h3 {{ color: #AD1457; }}
h4 {{ color: #6D4C41; }}
.item {{ margin-left: 12px; }}
.footer {{ margin-top: 28px; font-size: 0.9rem; color: #795548; border-top: 1px dashed #F8BBD0; padding-top: 12px; }}
@media print {{ body {{ background: white; }} .report {{ box-shadow: none; border: none; }} }}
</style>
</head>
<body>
<div class="report">
<h1>{html.escape(APP_TITLE)}</h1>
<div class="subtitle">生成時間：{generated_at}</div>
<div class="summary">
<div class="badge">專屬類型：{html.escape(type_display(mbti_type))}</div>
<p><strong>中文稱呼：</strong>{html.escape(type_info['zh'])}</p>
<p><strong>類型摘要：</strong>{html.escape(type_info['brief'])}</p>
<p><strong>最高 3 項特質：</strong>{html.escape(top_text)}</p>
<p><strong>較低 3 項特質：</strong>{html.escape(low_text)}</p>
</div>
<h2>報告摘要圖片</h2>
<p>下方圖片已嵌入 HTML，離線開啟時仍可顯示。</p>
{summary_image_html}
<h2>12 項延伸特質長條圖</h2>
{traits_image_html}
<h2>四向度分數</h2>
<table><tr><th>向度</th><th>定義</th><th>分數</th></tr>{score_rows}</table>
<h2>12 項延伸特質分數</h2>
<table><tr><th>特質</th><th>分數</th></tr>{trait_rows}</table>
<h2>完整分析報告</h2>
{report_html}
<div class="footer">本結果僅供課程展示與人格傾向探索使用，不作為正式心理診斷依據。可使用瀏覽器列印功能另存為 PDF。</div>
</div>
</body>
</html>"""


def build_pdf_report(result: Dict[str, Any]) -> bytes:
    """建立手機相容 PDF。

    本函式改用 Pillow 將整份報告繪製成多頁圖片，再輸出為 PDF。
    優點是中文不依賴手機 PDF 閱讀器的字型支援，可避免文字變方塊。
    缺點是 PDF 文字不可選取；因此頁面仍保留 HTML/TXT 下載作為可複製文字版本。
    """
    if PILImage is None or ImageDraw is None or ImageFont is None:
        raise RuntimeError("尚未安裝 pillow，請在 requirements.txt 加入 pillow。")

    font_path = get_required_cjk_font_path()
    page_w, page_h = 1240, 1754  # A4 at approximately 150 dpi
    margin_x, margin_y = 86, 78
    content_w = page_w - margin_x * 2

    title_font = load_cjk_font(42)
    h_font = load_cjk_font(32)
    body_font = load_cjk_font(25)
    small_font = load_cjk_font(21)

    def new_page() -> PILImage.Image:
        return PILImage.new("RGB", (page_w, page_h), "white")

    def line_height(font, extra=12):
        bbox = font.getbbox("測試Ag")
        return (bbox[3] - bbox[1]) + extra

    def wrap_text_by_width(text: str, font, max_width: int) -> List[str]:
        text = str(text).replace("	", " ").strip()
        if not text:
            return [""]
        lines = []
        for raw in text.split("\n"):
            raw = raw.strip()
            if not raw:
                lines.append("")
                continue
            current = ""
            for ch in raw:
                trial = current + ch
                if font.getlength(trial) <= max_width:
                    current = trial
                else:
                    if current:
                        lines.append(current)
                    current = ch
            if current:
                lines.append(current)
        return lines

    def draw_wrapped(draw, text: str, x: int, y: int, font, fill="#5D4037", max_width: int = content_w, gap: int = 10) -> int:
        for line in wrap_text_by_width(text, font, max_width):
            draw.text((x, y), line, font=font, fill=fill)
            y += line_height(font, gap)
        return y

    def paste_scaled(page: PILImage.Image, png_bytes: bytes, x: int, y: int, max_w: int, max_h: int) -> int:
        img = PILImage.open(io.BytesIO(png_bytes)).convert("RGB")
        ratio = min(max_w / img.width, max_h / img.height)
        new_size = (max(1, int(img.width * ratio)), max(1, int(img.height * ratio)))
        img = img.resize(new_size)
        page.paste(img, (x, y))
        return y + img.height + 28

    pages: List[PILImage.Image] = []
    mbti_type = result["type"]
    type_info = get_type_info(mbti_type)
    traits = compute_extended_traits(result["scores"])
    top_traits, low_traits = summarize_extended_traits(traits)

    # Page 1: title, type, scores, summary card
    page = new_page()
    draw = ImageDraw.Draw(page)
    y = margin_y
    y = draw_wrapped(draw, APP_TITLE, margin_x, y, title_font, fill="#AD1457", max_width=content_w, gap=14) + 8
    draw.text((margin_x, y), f"專屬類型：{type_display(mbti_type)}", font=h_font, fill="#AD1457")
    y += line_height(h_font, 18)
    y = draw_wrapped(draw, f"類型摘要：{type_info['brief']}", margin_x, y, body_font, max_width=content_w)
    y = draw_wrapped(draw, f"生成時間：{datetime.now().strftime('%Y-%m-%d %H:%M')}", margin_x, y + 10, small_font, fill="#795548") + 14

    draw.text((margin_x, y), "四向度分數", font=h_font, fill="#AD1457")
    y += line_height(h_font, 10)
    for dim, score in result["scores"].items():
        label = DIMENSION_RULES[dim]["label"]
        draw.text((margin_x + 18, y), f"{dim} | {label}：{score} / 100", font=body_font, fill="#5D4037")
        y += line_height(body_font, 8)
    y += 10

    draw.text((margin_x, y), "最高 3 項特質", font=h_font, fill="#AD1457")
    y += line_height(h_font, 8)
    for name, value in top_traits:
        draw.text((margin_x + 18, y), f"- {name}：{value} / 100", font=body_font, fill="#5D4037")
        y += line_height(body_font, 7)
    y += 8
    draw.text((margin_x, y), "較低 3 項特質", font=h_font, fill="#AD1457")
    y += line_height(h_font, 8)
    for name, value in low_traits:
        draw.text((margin_x + 18, y), f"- {name}：{value} / 100", font=body_font, fill="#5D4037")
        y += line_height(body_font, 7)
    footer = "本結果僅供課程展示與人格傾向探索使用，不作為正式心理診斷依據。"
    y = draw_wrapped(draw, footer, margin_x, y + 24, small_font, fill="#795548", max_width=content_w)
    pages.append(page)

    # Page 2: visual charts as images
    page = new_page()
    draw = ImageDraw.Draw(page)
    y = margin_y
    draw.text((margin_x, y), "圖表視覺化", font=title_font, fill="#AD1457")
    y += line_height(title_font, 18)

    radar_png = fig_to_png_bytes(draw_radar(result["scores"], mbti_type), scale=2)
    if radar_png:
        draw.text((margin_x, y), "MBTI 四向度雷達圖", font=h_font, fill="#AD1457")
        y += line_height(h_font, 10)
        y = paste_scaled(page, radar_png, margin_x + 150, y, content_w - 300, 520)

    draw.text((margin_x, y), "12 項延伸特質長條圖", font=h_font, fill="#AD1457")
    y += line_height(h_font, 10)
    bar_png = build_traits_chart_image(result)
    y = paste_scaled(page, bar_png, margin_x, y, content_w, 780)
    pages.append(page)

    # Page 3: trait table
    page = new_page()
    draw = ImageDraw.Draw(page)
    y = margin_y
    draw.text((margin_x, y), "12 項延伸特質分數", font=title_font, fill="#AD1457")
    y += line_height(title_font, 18)
    for idx, (name, value) in enumerate(traits.items(), 1):
        draw.text((margin_x + 18, y), f"{idx}. {name}：{value} / 100", font=body_font, fill="#5D4037")
        y += line_height(body_font, 8)
    y += 18
    y = draw_wrapped(draw, "最高 3 項特質：" + "、".join([f"{name} {value}" for name, value in top_traits]), margin_x, y, body_font, max_width=content_w)
    y = draw_wrapped(draw, "較低 3 項特質：" + "、".join([f"{name} {value}" for name, value in low_traits]), margin_x, y + 8, body_font, max_width=content_w)
    pages.append(page)

    # Remaining pages: full analysis report text
    report_lines = []
    for block in markdown_to_plain_text(result["report"]).split("\n"):
        block = block.strip()
        if block:
            report_lines.extend(wrap_text_by_width(block, body_font, content_w))
        report_lines.append("")

    page = new_page()
    draw = ImageDraw.Draw(page)
    y = margin_y
    draw.text((margin_x, y), "完整分析報告", font=title_font, fill="#AD1457")
    y += line_height(title_font, 18)
    for line in report_lines:
        if y > page_h - margin_y - line_height(body_font):
            pages.append(page)
            page = new_page()
            draw = ImageDraw.Draw(page)
            y = margin_y
        if line:
            draw.text((margin_x, y), line, font=body_font, fill="#5D4037")
            y += line_height(body_font, 8)
        else:
            y += int(line_height(body_font, 8) * 0.45)
    y += 12
    if y < page_h - margin_y - 80:
        draw_wrapped(draw, "註：本結果僅供課程展示與人格傾向探索使用，不作為正式心理診斷依據。", margin_x, y, small_font, fill="#795548", max_width=content_w)
    pages.append(page)

    # Save all pages as one PDF. Since each page is an image, mobile PDF readers will not show CJK squares.
    buffer = io.BytesIO()
    first, rest = pages[0], pages[1:]
    first.save(buffer, format="PDF", save_all=True, append_images=rest, resolution=150.0)
    buffer.seek(0)
    return buffer.getvalue()


def build_text_pdf_report_deprecated(result: Dict[str, Any]) -> bytes:
    """保留舊版文字 PDF 寫法作為備用；手機端不建議使用。"""
    if SimpleDocTemplate is None:
        raise RuntimeError("尚未安裝 reportlab，請在 requirements.txt 加入 reportlab。")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.55 * cm,
        leftMargin=1.55 * cm,
        topMargin=1.45 * cm,
        bottomMargin=1.45 * cm,
    )

    font_name = "MSung-Light"
    try:
        pdfmetrics.registerFont(UnicodeCIDFont(font_name))
    except Exception:
        font_name = "Helvetica"

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("TitleCJK", parent=styles["Title"], fontName=font_name, fontSize=18, leading=24, alignment=TA_CENTER, textColor=colors.HexColor("#AD1457"))
    h_style = ParagraphStyle("HeadingCJK", parent=styles["Heading2"], fontName=font_name, fontSize=13, leading=18, textColor=colors.HexColor("#AD1457"), spaceBefore=10, spaceAfter=6)
    body_style = ParagraphStyle("BodyCJK", parent=styles["BodyText"], fontName=font_name, fontSize=10.5, leading=16, alignment=TA_LEFT)
    small_style = ParagraphStyle("SmallCJK", parent=body_style, fontSize=9, leading=13, textColor=colors.HexColor("#6D4C41"))

    mbti_type = result["type"]
    type_info = get_type_info(mbti_type)
    story = [Paragraph(html.escape(APP_TITLE), title_style), Spacer(1, 0.25 * cm)]
    story.append(Paragraph(html.escape(f"專屬類型：{type_display(mbti_type)}"), h_style))
    story.append(Paragraph(html.escape(f"類型摘要：{type_info['brief']}"), body_style))
    story.append(Paragraph(html.escape("本結果僅供課程展示與人格傾向探索使用，不作為正式心理診斷依據。"), small_style))
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

def build_report_summary_image(result: Dict[str, Any]) -> bytes:
    """建立一張摘要圖片 PNG，適合社群分享或放入簡報。需要 pillow。"""
    if PILImage is None:
        raise RuntimeError("尚未安裝 pillow，請在 requirements.txt 加入 pillow。")

    font_path = find_cjk_font_path()
    if not font_path:
        raise RuntimeError("找不到可支援中文的系統字型，無法輸出中文圖片。")

    W, H = 1200, 1600
    img = PILImage.new("RGB", (W, H), "#FFF5F7")
    draw = ImageDraw.Draw(img)
    font_title = load_cjk_font(42)
    font_h = load_cjk_font(30)
    font_body = load_cjk_font(24)
    font_small = load_cjk_font(20)

    def draw_text_wrapped(text: str, x: int, y: int, font, fill="#5D4037", width_chars=34, line_gap=10):
        lines = []
        for para in str(text).split("\n"):
            lines.extend(textwrap.wrap(para, width=width_chars) or [""])
        for line in lines:
            draw.text((x, y), line, font=font, fill=fill)
            y += font.size + line_gap
        return y

    # Card background
    draw.rounded_rectangle((60, 55, W - 60, H - 55), radius=38, fill="#FFFFFF", outline="#FFD1DC", width=4)
    y = 105
    y = draw_text_wrapped(APP_TITLE, 105, y, font_title, fill="#AD1457", width_chars=24, line_gap=12)
    y += 12
    mbti_type = result["type"]
    info = get_type_info(mbti_type)
    draw.rounded_rectangle((105, y, 1095, y + 92), radius=28, fill="#FCE4EC")
    draw.text((135, y + 24), f"專屬類型：{type_display(mbti_type)}", font=font_h, fill="#AD1457")
    y += 120
    y = draw_text_wrapped(f"類型摘要：{info['brief']}", 105, y, font_body, width_chars=34)
    y += 14

    draw.text((105, y), "四向度分數", font=font_h, fill="#AD1457")
    y += 48
    for dim, score in result["scores"].items():
        label = DIMENSION_RULES[dim]["label"]
        bar_x, bar_y = 105, y + 34
        draw.text((105, y), f"{dim}｜{label}：{score} / 100", font=font_body, fill="#5D4037")
        draw.rounded_rectangle((bar_x, bar_y, 1095, bar_y + 22), radius=11, fill="#FFE4E1")
        draw.rounded_rectangle((bar_x, bar_y, bar_x + int(990 * score / 100), bar_y + 22), radius=11, fill="#FF9A9E")
        y += 82

    traits = compute_extended_traits(result["scores"])
    top_traits, low_traits = summarize_extended_traits(traits)
    y += 12
    draw.text((105, y), "最高 3 項特質", font=font_h, fill="#AD1457")
    y += 46
    for name, value in top_traits:
        draw.text((125, y), f"- {name}：{value} / 100", font=font_body, fill="#5D4037")
        y += 38
    y += 18
    draw.text((105, y), "較低 3 項特質", font=font_h, fill="#AD1457")
    y += 46
    for name, value in low_traits:
        draw.text((125, y), f"- {name}：{value} / 100", font=font_body, fill="#5D4037")
        y += 38

    y += 22
    footer = "本結果僅供課程展示與人格傾向探索使用，不作為正式心理診斷依據。"
    draw_text_wrapped(footer, 105, y, font_small, fill="#795548", width_chars=42)
    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def build_traits_chart_image(result: Dict[str, Any]) -> bytes:
    """以 Pillow 繪製可下載的 12 項延伸特質長條圖 PNG；不依賴 kaleido，較適合 Streamlit Cloud 分享給同學下載。"""
    if PILImage is None:
        raise RuntimeError("尚未安裝 pillow，請在 requirements.txt 加入 pillow。")

    font_path = find_cjk_font_path()
    if not font_path:
        raise RuntimeError("找不到可支援中文的系統字型，無法輸出中文圖片。")

    traits = compute_extended_traits(result["scores"])
    groups = [
        ("社交能量", ["社交互動能量", "獨處恢復能量"]),
        ("感知風格", ["現實細節敏銳度", "抽象想像延展力"]),
        ("決策風格", ["邏輯決策強度", "同理協調強度"]),
        ("執行節奏", ["規劃執行穩定度", "彈性應變開放度"]),
        ("適配能力", ["自我節奏掌控力", "團隊溝通適配度", "職涯探索適配度", "壓力調節彈性"]),
    ]
    palette = {
        "社交能量": "#FF9A9E",
        "感知風格": "#F8BBD0",
        "決策風格": "#CE93D8",
        "執行節奏": "#90CAF9",
        "適配能力": "#A5D6A7",
    }

    font_title = load_cjk_font(40)
    font_h = load_cjk_font(28)
    font_body = load_cjk_font(23)
    font_small = ImageFont.truetype(font_path, 19)

    W, H = 1500, 1350
    img = PILImage.new("RGB", (W, H), "#FFF5F7")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((45, 45, W - 45, H - 45), radius=34, fill="#FFFFFF", outline="#FFD1DC", width=4)
    y = 90
    draw.text((85, y), "12 項延伸特質分組長條圖", font=font_title, fill="#AD1457")
    y += 58
    draw.text((85, y), f"專屬類型：{type_display(result['type'])}｜50 分為中性參考線", font=font_small, fill="#6D4C41")
    y += 58

    left_label_x = 105
    bar_x = 500
    bar_w = 800
    bar_h = 30
    row_gap = 44
    axis_top = y
    axis_bottom = H - 115

    # 50 分參考線
    x50 = bar_x + int(bar_w * 0.5)
    draw.line((x50, axis_top, x50, axis_bottom), fill="#8D6E63", width=3)
    draw.text((x50 + 8, axis_top - 28), "50 中性線", font=font_small, fill="#8D6E63")

    for group_name, names in groups:
        ordered = sorted([(name, traits[name]) for name in names], key=lambda x: x[1], reverse=True)
        draw.text((left_label_x, y), group_name, font=font_h, fill="#AD1457")
        y += 42
        for name, value in ordered:
            draw.text((left_label_x + 22, y + 2), name, font=font_body, fill="#5D4037")
            draw.rounded_rectangle((bar_x, y, bar_x + bar_w, y + bar_h), radius=15, fill="#FFE4E1")
            fill_w = int(bar_w * value / 100)
            draw.rounded_rectangle((bar_x, y, bar_x + fill_w, y + bar_h), radius=15, fill=palette[group_name])
            draw.text((bar_x + bar_w + 25, y - 1), f"{value} / 100", font=font_body, fill="#5D4037")
            y += row_gap
        y += 22

    # x 軸標籤
    axis_y = H - 82
    draw.line((bar_x, axis_y, bar_x + bar_w, axis_y), fill="#D7CCC8", width=2)
    for tick in [0, 25, 50, 75, 100]:
        tx = bar_x + int(bar_w * tick / 100)
        draw.line((tx, axis_y - 8, tx, axis_y + 8), fill="#8D6E63", width=2)
        draw.text((tx - 18, axis_y + 14), str(tick), font=font_small, fill="#6D4C41")

    out = io.BytesIO()
    img.save(out, format="PNG")
    return out.getvalue()


def safe_export_filename(name: str) -> str:
    """清理下載檔名，避免暱稱含有檔案系統不適合字元。"""
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", str(name).strip())
    return cleaned or "user"


def build_export_zip(result: Dict[str, Any]) -> bytes:
    """建立一鍵下載 ZIP：包含 TXT、HTML、PDF、摘要 PNG、長條圖 PNG，讓同學不需逐一下載。"""
    nickname = safe_export_filename(st.session_state.get("nickname", "user"))
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(f"TAICA_MBTI_Report_{nickname}.txt", build_download_text(result))
        zf.writestr(f"TAICA_MBTI_Report_{nickname}.html", build_report_html(result).encode("utf-8"))

        try:
            zf.writestr(f"TAICA_MBTI_Report_{nickname}.pdf", build_pdf_report(result))
        except Exception as exc:
            zf.writestr("PDF_Export_Error.txt", f"PDF 產生失敗：{exc}")

        try:
            zf.writestr(f"TAICA_MBTI_Summary_{nickname}.png", build_report_summary_image(result))
        except Exception as exc:
            zf.writestr("Summary_Image_Error.txt", f"摘要圖片產生失敗：{exc}")

        try:
            # 優先使用純 Pillow 版本，部署到雲端時比 kaleido 更不容易失敗。
            zf.writestr(f"TAICA_MBTI_Traits_Bar_{nickname}.png", build_traits_chart_image(result))
        except Exception as exc:
            bar_png = fig_to_png_bytes(draw_extended_traits_bar_chart(compute_extended_traits(result["scores"])), scale=2)
            if bar_png:
                zf.writestr(f"TAICA_MBTI_Traits_Bar_{nickname}.png", bar_png)
            else:
                zf.writestr("Traits_Bar_Image_Error.txt", f"長條圖圖片產生失敗：{exc}")
    buffer.seek(0)
    return buffer.getvalue()

def build_download_text(result: Dict[str, Any]) -> str:
    """整理可下載的純文字報告。"""
    score_lines = "\n".join([f"- {dim}：{score}" for dim, score in result["scores"].items()])
    mbti_type = result["type"]
    return f"""{APP_TITLE}

專屬類型：{type_display(mbti_type)}
中文稱呼：{get_type_info(mbti_type)['zh']}
類型摘要：{get_type_info(mbti_type)['brief']}

四向度分數：
{score_lines}

分析報告：
{result['report']}

註：本結果僅供課程展示與人格傾向探索使用，不作為正式心理診斷依據。
"""



# ============================================================
# 3-1. 教師版穩定計分：分數由程式端計算，AI 只負責文字化報告
# ============================================================
# 分數定義：分數越高越偏該向度左側字母；越低越偏右側字母。
# 例如 E-I 高分偏 E，低分偏 I；S-N 高分偏 S，低分偏 N。
OPTION_SCORE_TABLE = {
    "放假喜歡一個人宅著，還是跟朋友出門去玩？": [20, 80, 50, 45],
    "到陌生的聚會，你會主動跟人搭話嗎？": [85, 25, 45, 35],
    "心情不好時，喜歡找人傾訴還是自己消化？": [75, 25, 40, 35],
    "在人群中，你通常是說話的人還是聽別人說？": [85, 25, 45, 50],
    "買東西是看實用性，還是憑感覺和設計？": [85, 25, 60, 35],
    "你喜歡按部就班，還是充滿驚喜的生活？": [85, 25, 60, 50],
    "你比較常想著『現在該做什麼』還是『未來會怎樣』？": [85, 25, 55, 35],
    "看電影時，你注意畫面細節還是整體的意境？": [85, 25, 55, 25],
    "朋友遇到困難，你先幫他想辦法還是先安慰他？": [85, 25, 55, 40],
    "做決定時，你更相信客觀邏輯還是內心直覺？": [85, 25, 60, 40],
    "看比賽時，你在乎誰贏，還是過程精不精彩？": [75, 35, 55, 40],
    "你覺得『講道理』比較重要，還是『顧及感受』？": [85, 25, 60, 45],
    "出門旅行會排好行程，還是走到哪玩到哪？": [85, 25, 45, 55],
    "你的桌面通常是乾淨整齊的，還是亂中有序？": [85, 25, 55, 60],
    "喜歡提前把作業做完，還是最後一刻才趕工？": [85, 25, 60, 45],
    "買東西會先列好清單，還是看到喜歡就買？": [85, 25, 45, 70],
}

MBTI_TYPES = {
    "ISTJ", "ISFJ", "INFJ", "INTJ", "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP", "ESTJ", "ESFJ", "ENFJ", "ENTJ"
}

# 中文稱呼採本專案自訂命名，避免使用商業測驗網站的專有包裝。
# 用途是讓一般使用者看懂 MBTI 簡稱背後的性格輪廓。
MBTI_TYPE_INFO = {
    "ISTJ": {"zh": "穩健執行者", "brief": "重視責任、秩序、細節與可靠執行。"},
    "ISFJ": {"zh": "溫暖守護者", "brief": "細心、負責、重視安全感與實際照顧。"},
    "INFJ": {"zh": "洞察引導者", "brief": "重視意義、同理與長遠方向，善於理解他人。"},
    "INTJ": {"zh": "策略規劃者", "brief": "重視系統、遠見、效率與長期規劃。"},
    "ISTP": {"zh": "冷靜實作者", "brief": "擅長分析現況、拆解問題與即時處理。"},
    "ISFP": {"zh": "感性創作者", "brief": "重視感受、審美、自由與個人價值。"},
    "INFP": {"zh": "理想調和者", "brief": "重視真誠、價值感、想像力與內在一致。"},
    "INTP": {"zh": "邏輯探索者", "brief": "喜歡推理、探索原理與建立自己的理解系統。"},
    "ESTP": {"zh": "行動挑戰者", "brief": "反應快、重視實作、喜歡即時挑戰與現場感。"},
    "ESFP": {"zh": "活力表現者", "brief": "外放、親和、享受體驗並善於帶動氣氛。"},
    "ENFP": {"zh": "靈感倡議者", "brief": "充滿想法、重視可能性、人際連結與自我實現。"},
    "ENTP": {"zh": "創新辯論者", "brief": "喜歡發想、挑戰框架、討論觀點與快速試錯。"},
    "ESTJ": {"zh": "高效管理者", "brief": "重視規則、效率、責任分工與明確成果。"},
    "ESFJ": {"zh": "關懷協調者", "brief": "重視人際和諧、照顧需求與團體秩序。"},
    "ENFJ": {"zh": "鼓舞領導者", "brief": "善於支持他人、凝聚方向與帶動團隊成長。"},
    "ENTJ": {"zh": "果斷指揮者", "brief": "目標導向、重視策略、組織效率與決策力。"},
}


def get_type_info(mbti_type: str) -> Dict[str, str]:
    return MBTI_TYPE_INFO.get(mbti_type, {"zh": "人格傾向未定義", "brief": "此類型需要更多作答資料輔助判讀。"})


def type_display(mbti_type: str) -> str:
    info = get_type_info(mbti_type)
    return f"{mbti_type}｜{info['zh']}"


def clamp_score(value: float) -> int:
    return max(0, min(100, int(round(value))))


def compute_extended_traits(scores: Dict[str, int]) -> Dict[str, int]:
    """
    由四向度分數延伸出的 12 項輔助特質分數。
    注意：這些不是正式心理量表，而是本課程專案依 MBTI 四向度設計的可解釋指標。
    """
    ei = scores.get("E-I", 50)
    sn = scores.get("S-N", 50)
    tf = scores.get("T-F", 50)
    jp = scores.get("J-P", 50)
    balance = lambda x: 100 - abs(x - 50) * 2
    return {
        "社交互動能量": clamp_score(ei),
        "獨處恢復能量": clamp_score(100 - ei),
        "現實細節敏銳度": clamp_score(sn),
        "抽象想像延展力": clamp_score(100 - sn),
        "邏輯決策強度": clamp_score(tf),
        "同理協調強度": clamp_score(100 - tf),
        "規劃執行穩定度": clamp_score(jp),
        "彈性應變開放度": clamp_score(100 - jp),
        "自我節奏掌控力": clamp_score((100 - ei) * 0.35 + jp * 0.35 + sn * 0.30),
        "團隊溝通適配度": clamp_score(ei * 0.30 + (100 - tf) * 0.35 + jp * 0.15 + balance(sn) * 0.20),
        "職涯探索適配度": clamp_score(tf * 0.25 + sn * 0.20 + (100 - sn) * 0.20 + jp * 0.15 + balance(ei) * 0.20),
        "壓力調節彈性": clamp_score((100 - jp) * 0.35 + balance(tf) * 0.30 + (100 - ei) * 0.20 + balance(sn) * 0.15),
    }


def extended_trait_lines(scores: Dict[str, int]) -> List[str]:
    traits = compute_extended_traits(scores)
    return [f"- {name}：{value} / 100" for name, value in traits.items()]


def extended_sections(mbti_type: str, scores: Dict[str, int]) -> List[str]:
    """產生免費進階報告段落：12 項額外特質、職涯、工作、關係與能量驅動。"""
    info = get_type_info(mbti_type)
    traits = compute_extended_traits(scores)
    ei, sn, tf, jp = scores["E-I"], scores["S-N"], scores["T-F"], scores["J-P"]

    career_by_type = {
        "ISTJ": ["資料整理／行政管理", "品管與流程管理", "財務、稽核或專案控管"],
        "ISFJ": ["教育輔導", "照護服務", "行政支援與客戶成功"],
        "INFJ": ["心理／教育相關助人工作", "品牌內容與研究企劃", "非營利與社會影響專案"],
        "INTJ": ["系統分析", "策略規劃", "研究開發與資料分析"],
        "ISTP": ["工程維修與技術實作", "產品測試", "現場問題排除"],
        "ISFP": ["設計、影像與美感創作", "手作與體驗設計", "人文服務型工作"],
        "INFP": ["文字創作", "諮詢輔導", "內容策展與社群議題"],
        "INTP": ["研究分析", "程式與系統設計", "資料科學與理論建模"],
        "ESTP": ["業務開發", "活動執行", "創業與現場營運"],
        "ESFP": ["行銷活動", "表演與內容創作", "顧客服務與體驗設計"],
        "ENFP": ["創意企劃", "教育推廣", "社群經營與跨域專案"],
        "ENTP": ["產品企劃", "創新提案", "顧問、辯論與策略發想"],
        "ESTJ": ["管理職", "營運流程設計", "專案管理與制度建置"],
        "ESFJ": ["人資與訓練", "公關活動", "顧客關係與團隊協調"],
        "ENFJ": ["教育培訓", "組織發展", "品牌溝通與團隊領導"],
        "ENTJ": ["企業策略", "高階專案管理", "創業、商業開發與組織領導"],
    }
    career = career_by_type.get(mbti_type, ["跨域企劃", "資料分析", "專案協作"])

    work_style = []
    work_style.append("適合有明確目標與可追蹤成果的任務。" if jp >= 50 else "適合保留彈性、允許探索與快速調整的任務。")
    work_style.append("偏好具體資訊、規則與實際案例。" if sn >= 50 else "偏好概念發想、可能性推演與整體方向。")
    work_style.append("決策時較重視邏輯、效率與原則。" if tf >= 50 else "決策時較重視人際影響、價值感與感受。")

    relationship = []
    relationship.append("在人際關係中較需要安靜空間與熟悉感，深度關係通常比大量社交更重要。" if ei < 50 else "在人際關係中較容易透過互動獲得能量，也較願意主動建立連結。")
    relationship.append("溝通上適合把事實、需求與期待說清楚。" if tf >= 50 else "溝通上適合先確認情緒與感受，再討論問題本身。")

    drivers = []
    drivers.append("完成明確任務與看見具體成果" if sn >= 50 else "探索新想法與看見未來可能")
    drivers.append("獨處整理後重新取得掌控感" if ei < 50 else "透過互動、討論與外部回饋獲得動力")
    drivers.append("建立秩序與穩定節奏" if jp >= 50 else "保留自由度與臨場調整空間")

    return [
        "#### 六、12 項額外特質分數｜本系統免費提供",
        "以下分數由四向度結果延伸推估，屬於課程專案的輔助分析指標，目的在於提供比簡稱更具體的自我理解。",
        *extended_trait_lines(scores),
        "",
        "#### 七、職涯點子",
        f"依據 **{type_display(mbti_type)}** 的傾向，可優先探索：" + "、".join(career) + "。",
        "",
        "#### 八、工作特質",
        *[f"- {item}" for item in work_style],
        "",
        "#### 九、關係模式",
        *[f"- {item}" for item in relationship],
        "",
        "#### 十、能量驅動因素",
        *[f"- {item}" for item in drivers],
        "",
        "#### 十一、免費進階報告說明",
        "本專案將 MBTI 簡稱、中文稱呼、12 項延伸特質、職涯點子、工作特質、關係模式與能量驅動因素整合在同一份報告中，讓使用者不需付費也能取得更完整的自我探索回饋。",
    ]


def score_preset_answer(question: str, answer: str) -> int:
    """依照題目與預設選項位置回傳穩定分數。"""
    options = OPTION_BANK.get(question, [])
    scores = OPTION_SCORE_TABLE.get(question, [])
    if answer in options and len(scores) == len(options):
        return scores[options.index(answer)]
    return 50


def score_custom_answer(dim: str, answer: str) -> int:
    """對自由輸入做保守關鍵字判斷；無明確線索時回傳中性 50。"""
    text = answer.strip().lower()
    if not text:
        return 50

    # 使用者表明不參與該情境，例如「我不看比賽」「我不看電影」，不應強行推論人格。
    neutral_patterns = ["不看", "沒有", "不去", "沒興趣", "不一定", "看情況", "看狀況"]
    if any(p in text for p in neutral_patterns):
        # 但 E-I 的「我都不說話」是明確內向線索，不視為中性。
        if dim == "E-I" and any(p in text for p in ["不說話", "安靜", "沉默"]):
            return 15
        return 50

    if dim == "E-I":
        if any(p in text for p in ["不說話", "安靜", "沉默", "獨處", "一個人", "自己", "不主動", "聽", "宅"]):
            return 20
        if any(p in text for p in ["主動", "聊天", "朋友", "聚會", "出門", "說話", "分享"]):
            return 80
    elif dim == "S-N":
        if any(p in text for p in ["實用", "功能", "價格", "細節", "現在", "具體", "按部就班", "穩定"]):
            return 80
        if any(p in text for p in ["未來", "可能", "想像", "意境", "感覺", "設計", "抽象", "驚喜", "概念"]):
            return 25
    elif dim == "T-F":
        if any(p in text for p in ["邏輯", "道理", "分析", "原則", "客觀", "解決", "辦法", "利弊"]):
            return 80
        if any(p in text for p in ["感受", "安慰", "情緒", "同理", "關係", "支持", "陪", "心情"]):
            return 25
    elif dim == "J-P":
        if any(p in text for p in ["計畫", "規劃", "清單", "提前", "整理", "安排", "固定", "完成"]):
            return 80
        if any(p in text for p in ["彈性", "隨機", "臨時", "自由", "拖", "最後", "走到哪", "看心情"]):
            return 25
    return 50


def compute_scores_from_history(history: List[Dict[str, str]]) -> Dict[str, int]:
    """以程式端穩定規則計算四向度分數，避免 LLM 每次自行打分造成結果矛盾。"""
    grouped = {dim: [] for dim in DIMENSION_RULES.keys()}
    for item in history:
        dim = item.get("dim", "")
        question = item.get("question", "")
        answer = item.get("answer", "")
        source = item.get("answer_source", "")
        if dim not in grouped:
            continue
        if source == "preset_option":
            grouped[dim].append(score_preset_answer(question, answer))
        else:
            grouped[dim].append(score_custom_answer(dim, answer))

    scores = {}
    for dim, vals in grouped.items():
        scores[dim] = int(round(sum(vals) / len(vals))) if vals else 50
    return validate_scores(scores)


def dim_tendency(dim: str, score: int) -> str:
    """產生單一向度的文字傾向描述。"""
    if dim == "E-I":
        if 45 <= score <= 55:
            return "外向與內向傾向接近中間，會依場合切換互動方式"
        return "偏外向 E，較容易從互動中獲得能量" if score > 55 else "偏內向 I，較重視獨處、觀察與自我整理"
    if dim == "S-N":
        if 45 <= score <= 55:
            return "實感與直覺傾向接近中間，能同時考慮現實資訊與未來可能"
        return "偏實感 S，較重視具體資訊、實用性與現實細節" if score > 55 else "偏直覺 N，較重視未來可能、整體意義與抽象連結"
    if dim == "T-F":
        if 45 <= score <= 55:
            return "思考與情感傾向接近中間，會在邏輯分析與感受考量間取得平衡"
        return "偏思考 T，較重視邏輯、原則與問題解法" if score > 55 else "偏情感 F，較重視感受、人際影響與同理支持"
    if dim == "J-P":
        if 45 <= score <= 55:
            return "判斷與感知傾向接近中間，既需要基本規劃，也保留彈性調整"
        return "偏判斷 J，較重視規劃、結構與提前完成" if score > 55 else "偏感知 P，較重視彈性、探索與臨場調整"
    return "傾向接近中間"


def evidence_text(history: List[Dict[str, str]], dim: str, max_items: int = 2) -> str:
    """從作答紀錄摘取該向度的語意線索。"""
    answers = [item.get("answer", "") for item in history if item.get("dim") == dim]
    answers = [a for a in answers if a]
    if not answers:
        return "本向度缺少明確回答線索。"
    selected = answers[:max_items]
    return "；".join([f"「{a}」" for a in selected])


def report_has_conflicting_type(report: str, expected_type: str) -> bool:
    """檢查 AI 報告是否出現與程式端類型不同的 MBTI 類型。"""
    found = set(re.findall(r"\b[IE][SN][TF][JP]\b", report or ""))
    return bool(found - {expected_type})


def render_fallback_report(nickname: str, scores: Dict[str, int], mbti_type: str, history: List[Dict[str, str]]) -> str:
    """當 AI 報告矛盾或 API 無法使用時，以程式端產生穩定且術語正確的報告。"""
    info = get_type_info(mbti_type)
    lines = [
        f"### 🌸 TAICA 專屬人格解析 - {nickname} 🌸",
        "",
        "#### 一、整體人格傾向",
        f"依據本次 16 題作答紀錄，系統推估你的人格傾向為 **{type_display(mbti_type)}**。{info['brief']} 此類型代表四向度的綜合結果；若某些分數接近 50，表示該向度並非強烈偏向單一端點，而是會依情境調整。",
        "",
        "#### 二、四向度分析",
    ]
    for dim in DIMENSION_RULES.keys():
        lines.extend([
            f"##### {dim}：{DIMENSION_RULES[dim]['label']}",
            f"分數：**{scores[dim]} / 100**。{dim_tendency(dim, scores[dim])}。",
            f"語意線索：{evidence_text(history, dim)}。",
            "",
        ])
    lines.extend([
        "#### 三、你的閃光點 ✨",
        "1. 你的回答顯示你能在不同情境中調整行為，不是單一固定模式。",
        "2. 你在作答中多次呈現『保留彈性』或『先判斷情境』的傾向，代表你具備情境判斷能力。",
        "3. 若某些向度分數接近中間，表示你可能能在兩種取向之間切換，這在團隊合作與問題處理上有彈性。",
        "",
        "#### 四、小煩惱與建議 💡",
        "1. 若遇到陌生或壓力較高的情境，可先用低負擔方式表達想法，例如簡短回應或事前準備重點。",
        "2. 若偏好彈性安排，建議仍保留最低限度的時間表與優先順序，避免臨近截止時壓力過高。",
        "3. 做決策時可同時列出『客觀理由』與『個人感受』，讓判斷更完整。",
        "",
    ])
    lines.extend(extended_sections(mbti_type, scores))
    lines.extend([
        "",
        "#### 十二、提醒",
        "本結果僅供自我探索與課程展示使用，不代表正式心理診斷。",
    ])
    return "\n".join(lines)

# ============================================================
# 4. AI 分析器
# ============================================================
class TAICAAIAnalyzer:
    def __init__(self) -> None:
        self.client = None
        self.model = st.secrets.get("GROQ_MODEL", DEFAULT_MODEL)

        api_key = st.secrets.get("GROQ_API_KEY", None)
        if api_key:
            self.client = Groq(api_key=api_key)

    def is_ready(self) -> bool:
        return self.client is not None

    def build_prompt(self, locked_scores: Dict[str, int], locked_type: str) -> str:
        return f"""
你是一位協助 TAICA 期末專案展示的 AI 語意分析助教。你的任務是根據使用者 16 題回答撰寫繁體中文人格傾向報告。

【最重要限制：分數與類型已由程式端完成計算，你不得重新計算、不得改寫、不得輸出其他 MBTI 類型】
- 鎖定四向度分數：{json.dumps(locked_scores, ensure_ascii=False)}
- 鎖定 MBTI 類型：{locked_type}
- 鎖定中文稱呼：{get_type_info(locked_type)['zh']}
- 鎖定類型摘要：{get_type_info(locked_type)['brief']}
- 報告中只能出現這一個 MBTI 類型：{locked_type}
- 不得出現其他 MBTI 類型，例如 ISTP、ENTP、ISFP 等，除非它正好等於鎖定類型。

【MBTI 四向度定義，必須嚴格遵守】
E-I：外向 Extraversion / 內向 Introversion。
- 分數高於 55 代表偏外向 E。
- 分數低於 45 代表偏內向 I。
- 45 到 55 代表外向與內向接近中間。

S-N：實感 Sensing / 直覺 Intuition。
- 分數高於 55 代表偏實感 S，重視具體資訊、現實經驗、細節與實用性。
- 分數低於 45 代表偏直覺 N，重視抽象概念、未來可能、象徵意義與整體意境。
- 45 到 55 代表實感與直覺接近中間。

T-F：思考 Thinking / 情感 Feeling。
- 分數高於 55 代表偏思考 T，重視邏輯、原則、客觀分析與問題解法。
- 分數低於 45 代表偏情感 F，重視感受、人際影響、價值判斷與同理支持。
- 45 到 55 代表思考與情感接近中間。

J-P：判斷 Judging / 感知 Perceiving。
- 分數高於 55 代表偏判斷 J，重視規劃、結構、提前安排與完成感。
- 分數低於 45 代表偏感知 P，重視彈性、探索、臨場調整與開放選擇。
- 45 到 55 代表判斷與感知接近中間。

【嚴禁混用術語】
1. S-N 只能解釋為「實感／直覺」，不可寫成「感性」。
2. T-F 只能解釋為「思考／情感」，不可寫成「直覺」。
3. J-P 的「感知 P」不可與 S-N 的「實感 S」混淆。
4. 若分數介於 45 到 55，必須描述為「接近中間」或「較平衡」，不可硬說明顯偏某端。

【分析依據要求】
1. 請根據每筆資料的 dim 與 answer 撰寫語意依據。
2. 每一向度至少概述 1 個回答線索。
3. 使用溫和、具體、非診斷式語氣。
4. profile_note 僅能用於稱謂或語氣，不可作為人格判定依據。

【輸出格式】
請不要輸出 JSON。請直接輸出以下繁體中文報告：

### 🌸 TAICA 專屬人格解析 - {st.session_state.nickname} 🌸

#### 一、整體人格傾向
請用 2 到 3 句說明鎖定類型 {locked_type}，並同時顯示中文稱呼「{get_type_info(locked_type)['zh']}」。不得出現其他 MBTI 類型。

#### 二、四向度分析
請分別說明 E-I、S-N、T-F、J-P。每一項都必須包含：分數、正確術語、語意線索。

#### 三、你的閃光點 ✨
請列出 2 到 3 點優勢，並連結使用者回答。

#### 四、小煩惱與建議 💡
請列出 2 到 3 點可能盲點與具體建議。

#### 五、提醒
請補上一句：本結果僅供自我探索與課程展示使用，不代表正式心理診斷。

#### 六、12 項額外特質分數｜本系統免費提供
請依據以下資料逐項列出 12 項延伸特質分數，不可更改數字：
{json.dumps(compute_extended_traits(locked_scores), ensure_ascii=False)}

#### 七、職涯點子
請提供 3 個適合探索的職涯或任務方向，語氣需保守，不可寫成絕對推薦。

#### 八、工作特質
請說明此類型在工作或學習任務中的偏好、優勢與注意事項。

#### 九、關係模式
請說明此類型在人際互動、親密關係或團隊關係中的常見模式。

#### 十、能量驅動因素
請說明此類型通常從哪些情境獲得動力，又可能在哪些情境消耗能量。

#### 十一、免費進階報告說明
請說明本專案將 MBTI 簡稱、中文稱呼、12 項延伸特質、職涯點子、工作特質、關係模式與能量驅動因素整合於同一份報告，提供使用者免費取得完整自我探索回饋。
"""

    def analyze(self, history: List[Dict[str, str]], nickname: str, profile_note: str) -> Dict[str, Any]:
        # 教師修正版：分數與 MBTI 類型一律由程式端計算，避免 LLM 自行打分造成畫面與報告矛盾。
        locked_scores = compute_scores_from_history(history)
        locked_type = infer_mbti_type(locked_scores)
        fallback_report = render_fallback_report(nickname, locked_scores, locked_type, history)

        if not self.is_ready():
            return {
                "ok": False,
                "scores": locked_scores,
                "type": locked_type,
                "report": "尚未設定 GROQ_API_KEY，因此無法呼叫 Groq API 產生 AI 文字報告。以下為系統依照穩定計分規則產生的安全報告。\n\n" + fallback_report,
                "raw": "",
            }

        user_payload = {
            "nickname": nickname,
            "profile_note": profile_note,
            "locked_scores": locked_scores,
            "locked_type": locked_type,
            "answers": history,
        }

        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": self.build_prompt(locked_scores, locked_type)},
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False, indent=2)},
                ],
            )
            report = completion.choices[0].message.content.strip()
            if report_has_conflicting_type(report, locked_type):
                report = "AI 報告出現與程式端分數不一致的 MBTI 類型，因此系統已改用穩定校正版報告。\n\n" + fallback_report
                ok = False
            else:
                ok = True
            return {
                "ok": ok,
                "scores": locked_scores,
                "type": locked_type,
                "report": report,
                "raw": report,
            }
        except Exception as exc:
            return {
                "ok": False,
                "scores": locked_scores,
                "type": locked_type,
                "report": f"API 呼叫失敗：{exc}\n\n以下為系統依照穩定計分規則產生的安全報告。\n\n" + fallback_report,
                "raw": "",
            }


# ============================================================
# 5. Streamlit 主程式
# ============================================================
init_session_state()
analyzer = TAICAAIAnalyzer()

st.markdown(f'<h1 class="main-title">🧠 {APP_TITLE}</h1>', unsafe_allow_html=True)
st.markdown(f'<div class="subtitle">{APP_SUBTITLE}</div>', unsafe_allow_html=True)

st.markdown(
    """
    <div class="method-card">
    <b>專案定位：</b>本系統透過 16 題選項輔助與開放式問答蒐集使用者語意資料，
    並由生成式 AI 依據 MBTI 四向度架構進行人格傾向分析。除了 MBTI 簡稱外，
    也提供中文稱呼、12 項延伸特質分數、職涯點子、工作特質、關係模式與能量驅動因素。
    結果僅供自我探索與課程展示，不作為正式心理診斷或臨床判定依據。
    </div>
    """,
    unsafe_allow_html=True,
)

# 側邊欄
with st.sidebar:
    st.markdown("### 🎀 測驗小檔案")
    if st.session_state.test_started:
        st.write(f"🧸 暱稱：**{st.session_state.nickname}**")
        st.write(f"✨ 個人化稱謂：**{st.session_state.profile_note}**")
        progress_value = min(len(st.session_state.history) / TOTAL_QUESTIONS, 1.0)
        st.progress(progress_value)
        st.write(f"進度：{len(st.session_state.history)} / {TOTAL_QUESTIONS}")
    else:
        st.write("尚未開始測驗。")

    st.divider()
    st.caption("API 狀態")
    if analyzer.is_ready():
        st.success("Groq API 已設定")
    else:
        st.warning("尚未設定 GROQ_API_KEY")

    if st.button("🔄 重新開始測驗"):
        reset_test()

# 階段 A：基本資料
if not st.session_state.test_started:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("👋 開始前，先建立測驗小檔案")

    c1, c2 = st.columns(2)
    with c1:
        nickname = st.text_input("怎麼稱呼你呢？", placeholder="例如：小花、Amy、佳佳")
    with c2:
        profile_note = st.radio("報告稱謂偏好", ["女孩", "男孩", "不透露", "其他"], horizontal=True)

    st.caption("稱謂資料僅用於報告語氣呈現，不會作為 MBTI 類型判定依據。")

    if st.button("🌸 開始輕鬆測驗 🌸"):
        if nickname.strip():
            st.session_state.nickname = nickname.strip()
            st.session_state.profile_note = profile_note
            st.session_state.test_started = True
            st.rerun()
        else:
            st.warning("請先輸入暱稱，再開始測驗。")

    st.markdown("</div>", unsafe_allow_html=True)

# 階段 B：逐題作答
elif st.session_state.step <= TOTAL_QUESTIONS:
    current_q = st.session_state.questions[st.session_state.step - 1]
    current_q_text = current_q["q"]
    current_dim = current_q["dim"]

    st.markdown(
        f"""
        <div class="question-box">
            <h4>題 {st.session_state.step} / {TOTAL_QUESTIONS}</h4>
            <p style="font-size:1.3rem; font-weight:bold;">{current_q_text}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    options = OPTION_BANK.get(current_q_text, []) + [CUSTOM_OPTION]

    # 注意：不要把 radio 放在 st.form 裡。
    # Streamlit 的 form 只有按下 submit 後才會更新內部 widget 狀態，
    # 因此若希望選到「以上皆非」時立即彈出輸入框，radio 與 text_area 必須放在 form 外。
    selected_option = st.radio(
        "不想打字也沒關係，可以先選一個最接近你的答案：",
        options,
        key=f"option_{st.session_state.step}",
    )

    custom_answer = ""
    if selected_option == CUSTOM_OPTION:
        st.info("你選擇了『以上皆非』，請在下方輸入更符合自己的回答。")
        custom_answer = st.text_area(
            "請寫下你的想法：",
            placeholder="例如：我覺得要看當天狀態，或補充更符合自己的描述。",
            key=f"custom_answer_{st.session_state.step}",
            height=120,
        )
    else:
        st.caption("若選項大致符合你的想法，可直接送出；AI 會依據此選項進行語意分析。")

    submitted = st.button("送出 💌", key=f"submit_{st.session_state.step}")

    if submitted:
        if selected_option == CUSTOM_OPTION:
            cleaned_answer = custom_answer.strip()
            answer_source = "custom_text"
        else:
            cleaned_answer = selected_option.strip()
            answer_source = "preset_option"

        if cleaned_answer:
            st.session_state.history.append(
                {
                    "question_no": st.session_state.step,
                    "dim": current_dim,
                    "question": current_q_text,
                    "answer": cleaned_answer,
                    "answer_source": answer_source,
                }
            )
            st.session_state.step += 1
            st.session_state.analysis_result = None
            st.rerun()
        else:
            st.warning("若選擇『以上皆非』，請先輸入自己的回答後再送出。")

# 階段 C：AI 分析與結果呈現
else:
    if st.session_state.analysis_result is None:
        with st.spinner("✨ 測驗完成！AI 正在依據你的回答整理人格傾向分析..."):
            st.session_state.analysis_result = analyzer.analyze(
                history=st.session_state.history,
                nickname=st.session_state.nickname,
                profile_note=st.session_state.profile_note,
            )

    result = st.session_state.analysis_result

    if not result["ok"]:
        st.warning("AI 分析流程未完全成功，以下為系統安全回傳結果。")

    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    col_l, col_r = st.columns([3, 2])

    with col_l:
        st.markdown(result["report"])

    with col_r:
        st.plotly_chart(draw_radar(result["scores"], result["type"]), use_container_width=True)
        st.markdown(
            f"### 🎉 你的專屬類型：<span style='color:#FF7EB3;'>{type_display(result['type'])}</span>",
            unsafe_allow_html=True,
        )
        st.caption(get_type_info(result["type"])["brief"])

        st.markdown("#### 四向度分數")
        for dim, score in result["scores"].items():
            st.write(f"**{dim}（{DIMENSION_RULES[dim]['label']}）**：{score} / 100")

        with st.expander("免費查看 12 項額外特質分數", expanded=True):
            traits = compute_extended_traits(result["scores"])
            top_traits, low_traits = summarize_extended_traits(traits)
            st.caption("以下長條圖依類別分組，並在同類別中由高到低排序；虛線 50 分為中性參考線。")
            st.plotly_chart(draw_extended_traits_bar_chart(traits), use_container_width=True)

            c_high, c_low = st.columns(2)
            with c_high:
                st.markdown("#### 最高的 3 項特質")
                for trait_name, trait_score in top_traits:
                    st.write(f"**{trait_name}**：{trait_score} / 100")
            with c_low:
                st.markdown("#### 較低的 3 項特質")
                for trait_name, trait_score in low_traits:
                    st.write(f"**{trait_name}**：{trait_score} / 100")

            st.markdown("#### 12 項特質數值一覽")
            for trait_name, trait_score in traits.items():
                st.write(f"**{trait_name}**：{trait_score} / 100")

        st.markdown("#### 匯出報告版面")
        st.caption("手機使用者建議直接下載 PDF 或 PNG；ZIP 會放在下方進階選項，避免手機還要解壓縮。")

        export_name = safe_export_filename(st.session_state.nickname)
        html_report = build_report_html(result)
        txt_report = build_download_text(result)

        try:
            pdf_report = build_pdf_report(result)
            st.download_button(
                label="📕 手機優先：下載完整報告 PDF",
                data=pdf_report,
                file_name=f"TAICA_MBTI_Report_{export_name}.pdf",
                mime="application/pdf",
                use_container_width=True,
            )
        except Exception as exc:
            st.info(f"PDF 尚無法產生：{exc}")

        try:
            summary_png = build_report_summary_image(result)
            st.download_button(
                label="🖼️ 手機優先：下載報告摘要圖片 PNG",
                data=summary_png,
                file_name=f"TAICA_MBTI_Summary_{export_name}.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception as exc:
            st.info(f"摘要圖片尚無法產生：{exc}")

        try:
            traits_png = build_traits_chart_image(result)
            st.download_button(
                label="📊 下載 12 項特質長條圖 PNG",
                data=traits_png,
                file_name=f"TAICA_MBTI_Traits_Bar_{export_name}.png",
                mime="image/png",
                use_container_width=True,
            )
        except Exception as exc:
            st.info(f"長條圖圖片尚無法產生：{exc}")

        st.download_button(
            label="🌐 下載完整報告 HTML",
            data=html_report.encode("utf-8"),
            file_name=f"TAICA_MBTI_Report_{export_name}.html",
            mime="text/html",
            use_container_width=True,
        )

        st.download_button(
            label="📄 下載純文字報告 TXT",
            data=txt_report,
            file_name=f"TAICA_MBTI_Report_{export_name}.txt",
            mime="text/plain",
            use_container_width=True,
        )

        with st.expander("電腦使用者進階下載：完整報告包 ZIP", expanded=False):
            st.caption("ZIP 適合電腦一次保存所有檔案；手機使用者建議下載上方 PDF 或 PNG。")
            st.download_button(
                label="📦 一鍵下載完整報告包 ZIP",
                data=build_export_zip(result),
                file_name=f"TAICA_MBTI_Export_{export_name}.zip",
                mime="application/zip",
                use_container_width=True,
            )

        if st.button("🔁 重新生成 AI 分析"):
            st.session_state.analysis_result = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("查看本次作答紀錄與資料結構"):
        st.json(st.session_state.history)
