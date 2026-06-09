"""
TAICA 期末專案修正版
題目：AI 讀心術：結合語意分析與 MBTI 理論的次世代性格檢測工具
說明：本系統為課程展示與人格傾向探索用途，非正式心理診斷工具。
"""

import json
import random
import re
from typing import Any, Dict, List, Tuple

import plotly.graph_objects as go
import streamlit as st
from groq import Groq


# ============================================================
# 1. 基本設定與題庫
# ============================================================
APP_TITLE = "AI 讀心術：結合語意分析與 MBTI 理論的次世代性格檢測工具"
APP_SUBTITLE = "以選項輔助、開放式回答、語意分析與 MBTI 四向度架構進行人格傾向探索"
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


def build_download_text(result: Dict[str, Any]) -> str:
    """整理可下載的純文字報告。"""
    score_lines = "\n".join([f"- {dim}：{score}" for dim, score in result["scores"].items()])
    return f"""{APP_TITLE}

專屬類型：{result['type']}

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
    lines = [
        f"### 🌸 TAICA 專屬人格解析 - {nickname} 🌸",
        "",
        "#### 一、整體人格傾向",
        f"依據本次 16 題作答紀錄，系統推估你的人格傾向為 **{mbti_type}**。此類型代表四向度的綜合結果，但若某些分數接近 50，表示該向度並非強烈偏向單一端點，而是會依情境調整。",
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
        "#### 五、提醒",
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
請用 2 到 3 句說明鎖定類型 {locked_type} 與主要特質。不得出現其他 MBTI 類型。

#### 二、四向度分析
請分別說明 E-I、S-N、T-F、J-P。每一項都必須包含：分數、正確術語、語意線索。

#### 三、你的閃光點 ✨
請列出 2 到 3 點優勢，並連結使用者回答。

#### 四、小煩惱與建議 💡
請列出 2 到 3 點可能盲點與具體建議。

#### 五、提醒
請補上一句：本結果僅供自我探索與課程展示使用，不代表正式心理診斷。
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
    並由生成式 AI 依據 MBTI 四向度架構進行人格傾向分析。結果僅供自我探索與課程展示，
    不作為正式心理診斷或臨床判定依據。
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
            f"### 🎉 你的專屬類型：<span style='color:#FF7EB3;'>{result['type']}</span>",
            unsafe_allow_html=True,
        )
        st.markdown("#### 四向度分數")
        for dim, score in result["scores"].items():
            st.write(f"**{dim}（{DIMENSION_RULES[dim]['label']}）**：{score} / 100")

        st.download_button(
            label="📄 下載分析報告 TXT",
            data=build_download_text(result),
            file_name=f"TAICA_MBTI_Report_{st.session_state.nickname}.txt",
            mime="text/plain",
        )

        if st.button("🔁 重新生成 AI 分析"):
            st.session_state.analysis_result = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("查看本次作答紀錄與資料結構"):
        st.json(st.session_state.history)
