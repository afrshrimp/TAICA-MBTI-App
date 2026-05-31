import streamlit as st
import json
import re
import plotly.graph_objects as go
import random
from groq import Groq

# --- 1. 頁面配置：可愛風格 ---
st.set_page_config(page_title="TAICA MBTI V12 🌸 (Cloud Edition)", page_icon="☁️", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FFF5F7; color: #5D4037; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .main-title { color: #FF7EB3; text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 20px; text-shadow: 1px 1px 2px #FFD1DC; }
    .question-box { background: #FFFFFF; border: 2px solid #FFD1DC; padding: 25px; border-radius: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(255, 126, 179, 0.1); }
    .report-card { background: #FFFFFF; border: 2px dashed #FF9A9E; padding: 30px; border-radius: 25px; color: #5D4037; line-height: 1.8; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); }
    .stButton>button { background: linear-gradient(90deg, #FF9A9E 0%, #FECFEF 100%); color: #5D4037; font-weight: bold; border-radius: 30px; width: 100%; border: none; height: 3em; box-shadow: 0 4px 10px rgba(255, 154, 158, 0.3); transition: 0.3s;}
    .stButton>button:hover { transform: scale(1.02); }
    </style>
    """, unsafe_allow_html=True)

class TAICAMasterCloud:
    def __init__(self):
        # 讀取 Streamlit 雲端設定的隱私金鑰
        try:
            self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        except Exception as e:
            st.error("⚠️ 尚未設定 API Key，請在 Streamlit Cloud 的 Secrets 中設定 GROQ_API_KEY。")
            
        # 使用 Groq 上的 Llama 3 8B 模型
        # self.model = "llama3-8b-8192" 已退役
        # 更新為 Llama 3.1 8B 瞬態模型
        self.model = "llama-3.1-8b-instant"
        
        self.q_bank = {
            'E-I': ["放假喜歡一個人宅著，還是跟朋友出門去玩？", "到陌生的聚會，你會主動跟人搭話嗎？", "心情不好時，喜歡找人傾訴還是自己消化？", "在人群中，你通常是說話的人還是聽別人說？"],
            'S-N': ["買東西是看實用性，還是憑感覺和設計？", "你喜歡按部就班，還是充滿驚喜的生活？", "你比較常想著『現在該做什麼』還是『未來會怎樣』？", "看電影時，你注意畫面細節還是整體的意境？"],
            'T-F': ["朋友遇到困難，你先幫他想辦法還是先安慰他？", "做決定時，你更相信客觀邏輯還是內心直覺？", "看比賽時，你在乎誰贏，還是過程精不精彩？", "你覺得『講道理』比較重要，還是『顧及感受』？"],
            'J-P': ["出門旅行會排好行程，還是走到哪玩到哪？", "你的桌面通常是乾淨整齊的，還是亂中有序？", "喜歡提前把作業做完，還是最後一刻才趕工？", "買東西會先列好清單，還是看到喜歡就買？"]
        }

    def call_ai(self, system_prompt, user_prompt):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model=self.model,
                temperature=0.6,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            return f"API 呼叫失敗：{e}"

    def draw_radar(self, scores, mbti_type):
        categories = ['E-I(外向/內向)', 'S-N(實感/直覺)', 'T-F(思考/情感)', 'J-P(判斷/感知)']
        
        def safe_val(v):
            try:
                val = float(v)
                return max(0, min(100, val)) 
            except:
                return 50

        values = [safe_val(scores.get('E-I', 50)), safe_val(scores.get('S-N', 50)), 
                  safe_val(scores.get('T-F', 50)), safe_val(scores.get('J-P', 50))]
                  
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values, theta=categories, fill='toself',
            fillcolor='rgba(255, 154, 158, 0.4)', line=dict(color='#FF7EB3', width=3),
            marker=dict(color='#FF7EB3', size=8), name=f"類型: {mbti_type}"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#FFE4E1"),
                       angularaxis=dict(gridcolor="#FFE4E1", color="#5D4037")),
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#5D4037")
        )
        return fig

# --- 3. 狀態管理 ---
st.markdown('<h1 class="main-title">✨ 懂你的 16 型人格小助手 ✨</h1>', unsafe_allow_html=True)

if 'v12_init' not in st.session_state:
    master_temp = TAICAMasterCloud()
    all_qs = [{"dim": dim, "q": q} for dim, qs in master_temp.q_bank.items() for q in qs]
    random.shuffle(all_qs)
    
    st.session_state.update({
        'v12_init': False, 'step': 1, 'history': [], 'nickname': '', 'gender': '',
        'questions': all_qs
    })

master = TAICAMasterCloud()

# 側邊欄
with st.sidebar:
    st.markdown("### 🎀 測驗小檔案")
    if st.session_state.v12_init:
        st.write(f"🧸 暱稱: **{st.session_state.nickname}**")
        st.write(f"✨ 性別: **{st.session_state.gender}**")
        st.progress(min(st.session_state.step / 16, 1.0))
        st.write(f"進度: {min(st.session_state.step, 16)} / 16")
    if st.button("🔄 重新開始測驗"):
        for k in st.session_state.keys(): del st.session_state[k]
        st.rerun()

# 階段 A: 登錄
if not st.session_state.v12_init:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("👋 哈囉！先讓我認識你吧")
    c1, c2 = st.columns(2)
    with c1: nick = st.text_input("怎麼稱呼你呢？", placeholder="輸入暱稱")
    with c2: gend = st.radio("你的性別是？", ["女孩", "男孩"], horizontal=True)
    if st.button("🌸 開始輕鬆測驗 🌸"):
        if nick:
            st.session_state.nickname, st.session_state.gender, st.session_state.v12_init = nick, gend, True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 階段 B: 16 題快速測驗
elif st.session_state.step <= 16:
    current_q_text = st.session_state.questions[st.session_state.step - 1]['q']
    
    st.markdown(f'<div class="question-box"><h4>題 {st.session_state.step} / 16</h4><p style="font-size:1.3rem; font-weight:bold;">{current_q_text}</p></div>', unsafe_allow_html=True)
    
    with st.form(key=f"v12_form_{st.session_state.step}"):
        ans = st.text_input("你的直覺是什麼呢？", placeholder="簡單寫下你的想法...", key=f"input_{st.session_state.step}")
        if st.form_submit_button("送出 💌"):
            if ans:
                st.session_state.history.append({"q": current_q_text, "a": ans})
                st.session_state.step += 1
                st.rerun()

# 階段 C: 最終 AI 深度報告
else:
    with st.spinner("✨ 測驗完成！AI 正在雲端為你整理專屬分析報告..."):
        analysis_p = f"""
        受試者：{st.session_state.nickname} ({st.session_state.gender})。
        請根據問答紀錄分析其 MBTI 人格。

        【超級重要：格式規範】
        你必須先輸出一個 JSON 區塊，用 ```json 和 ``` 包起來。數值必須是 0 到 100 的「正整數」。
        範例格式：
        ```json
        {{"scores": {{"E-I": 80, "S-N": 30, "T-F": 65, "J-P": 45}}, "type": "ENFP"}}
        ```
        
        輸出完 JSON 區塊後，請開始寫報告內文：
        ### 🌸 TAICA 專屬人格解析 - {st.session_state.nickname} 🌸
        【你的閃光點✨】
        【小煩惱與建議💡】
        """
        raw_res = master.call_ai(analysis_p, str(st.session_state.history))
        
        default_scores = {"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50}
        mbti_type = "未定義 (AI 解析微調中)"
        report = raw_res
        
        try:
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_res, re.DOTALL | re.IGNORECASE)
            if not json_match:
                json_match = re.search(r'\{[^{}]*"scores".*?\}', raw_res, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    if json_str.count('{') > json_str.count('}'):
                        json_str += '}'
                    data = json.loads(json_str)
                    report = raw_res.replace(json_match.group(), "").strip()
            else:
                data = json.loads(json_match.group(1))
                report = raw_res.replace(json_match.group(0), "").strip()
                
            mbti_type = data.get("type", mbti_type)
            default_scores = data.get("scores", default_scores)
        except:
            st.warning("⚠️ 喔喔！AI 在計算分數時稍微發散了，但大師已經幫你還原了報告！")
        
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        col_l, col_r = st.columns([3, 2])
        with col_l:
            st.markdown(report)
        with col_r:
            st.plotly_chart(master.draw_radar(default_scores, mbti_type), use_container_width=True)
            st.markdown(f"### 🎉 你的專屬類型：<span style='color:#FF7EB3;'>{mbti_type}</span>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
