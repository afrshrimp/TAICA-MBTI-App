import streamlit as st
import json
import re
import plotly.graph_objects as go
import random
from groq import Groq
import pandas as pd

# --- 1. 頁面配置與進階視覺美化 ---
st.set_page_config(page_title="TAICA MBTI V14 🌸 (Master Edition)", page_icon="👑", layout="wide")

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

# --- 2. 全域暫存資料庫 (資料持久化與全班統計) ---
@st.cache_resource
def get_global_leaderboard():
    return [] 

global_board = get_global_leaderboard()

# --- 3. 核心 AI 引擎 (解耦架構設計) ---
class TAICAMasterCloud:
    def __init__(self):
        try:
            self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        except Exception as e:
            st.error("⚠️ 系統初始化異常：未偵測到環境變數 GROQ_API_KEY。")
            
        # 鎖定高可用性、低延遲的 Llama 3.1 8B 瞬態模型
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
                temperature=0.3, # 極低溫度，鎖定幻覺與格式穩定性
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            return f"API 呼叫失敗：{e}"

    def draw_radar(self, scores, mbti_type):
        categories = ['E-I(外向/內向)', 'S-N(實感/直覺)', 'T-F(思考/情感)', 'J-P(判斷/感知)']
        
        def safe_val(v):
            try:
                return max(0, min(100, float(v))) 
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
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#5D4037"),
            margin=dict(l=20, r=20, t=20, b=20)
        )
        return fig

# --- 4. 狀態管理與路由 ---
st.markdown('<h1 class="main-title">✨ 懂你的 16 型人格小助手 ✨</h1>', unsafe_allow_html=True)

if 'v14_init' not in st.session_state:
    master_temp = TAICAMasterCloud()
    all_qs = [{"dim": dim, "q": q} for dim, qs in master_temp.q_bank.items() for q in qs]
    random.shuffle(all_qs)
    
    st.session_state.update({
        'v14_init': False, 'step': 1, 'history': [], 'nickname': '', 'gender': '',
        'questions': all_qs, 'saved_to_board': False
    })

master = TAICAMasterCloud()

# --- 側邊欄：動態數據可視化儀表板 ---
with st.sidebar:
    st.markdown("### 🎀 測驗小檔案")
    if st.session_state.v14_init:
        st.write(f"🧸 暱稱: **{st.session_state.nickname}**")
        st.write(f"✨ 性別: **{st.session_state.gender}**")
        st.progress(min(st.session_state.step / 16, 1.0))
        st.write(f"進度: {min(st.session_state.step, 16)} / 16")
    
    st.markdown("---")
    st.markdown("### 🏆 班級 MBTI 統計牆")
    if len(global_board) > 0:
        df = pd.DataFrame(global_board)
        st.dataframe(df.tail(5).iloc[::-1], hide_index=True, use_container_width=True)
        st.write("**類型分佈排行：**")
        type_counts = df['MBTI類型'].value_counts()
        st.bar_chart(type_counts, color="#FF7EB3")
    else:
        st.info("目前還沒有人完成測驗喔，趕快搶頭香！")
        
    st.markdown("---")
    if st.button("🔄 重新開始測驗", use_container_width=True):
        for k in st.session_state.keys(): del st.session_state[k]
        st.rerun()

# --- 5. 測驗主流程控制 ---
# 階段 A: 身分認證登錄
if not st.session_state.v14_init:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("👋 哈囉！先讓我認識你吧")
    c1, c2 = st.columns(2)
    with c1: nick = st.text_input("怎麼稱呼你呢？", placeholder="輸入暱稱")
    with c2: gend = st.radio("你的性別是？", ["女孩", "男孩"], horizontal=True)
    if st.button("🌸 開始輕鬆測驗 🌸"):
        if nick:
            st.session_state.nickname, st.session_state.gender, st.session_state.v14_init = nick, gend, True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 階段 B: 零延遲快速測驗
elif st.session_state.step <= 16:
    current_q_text = st.session_state.questions[st.session_state.step - 1]['q']
    
    st.markdown(f'<div class="question-box"><h4>題 {st.session_state.step} / 16</h4><p style="font-size:1.3rem; font-weight:bold;">{current_q_text}</p></div>', unsafe_allow_html=True)
    
    with st.form(key=f"v14_form_{st.session_state.step}"):
        ans = st.text_input("你的直覺是什麼呢？", placeholder="簡單寫下你的想法...", key=f"input_{st.session_state.step}")
        if st.form_submit_button("送出 💌"):
            if ans:
                st.session_state.history.append({"q": current_q_text, "a": ans})
                st.session_state.step += 1
                st.rerun()

# 階段 C: 最終 AI 深度報告 (搭載 Prompt 邏輯鎖與 Few-Shot 範本)
else:
    with st.spinner("✨ 測驗完成！AI 正在雲端為你整理專屬分析報告..."):
        
        # 嚴密的提示工程：確保 JSON 穩定性與語意對齊
        analysis_p = f"""
        受試者：{st.session_state.nickname} ({st.session_state.gender})。
        請根據問答紀錄分析其 MBTI 人格。

        【超級重要：格式規範】
        你必須完全模仿下方的【完美範例】格式來輸出，絕對不要增加額外的標題或廢話。

        【🔥 絕對指令：邏輯一致性約束】
        你的報告內文必須與你算出的 MBTI 類型「嚴格吻合」，絕不可前後矛盾！
        - 如果算出 I (內向)，必須強調其「內在能量、深思熟慮」，絕不可寫「充滿廣泛社交能力」。
        - 如果算出 E (外向)，必須強調其「從人群中獲得能量與活潑」。
        請確保敘述完全合理化該 MBTI 類型的標準特質。

        【完美範例開始】
        ```json
        {{"scores": {{"E-I": 80, "S-N": 30, "T-F": 65, "J-P": 45}}, "type": "ENFP"}}
        ```
        
        ### 🌸 TAICA 專屬人格解析 - (受試者暱稱) 🌸
        
        【你的閃光點✨】
        * (列出第一點溫柔的稱讚與分析，必須符合其 MBTI 特質)
        * (列出第二點)
        
        【小煩惱與建議💡】
        * (列出第一點貼心的建議)
        * (列出第二點)
        【完美範例結束】
        """
        raw_res = master.call_ai(analysis_p, str(st.session_state.history))
        
        default_scores = {"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50}
        mbti_type = "未定義"
        report = raw_res
        
        try:
            # 容錯 JSON 解析引擎 (已修復引號語法錯誤)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_res, re.DOTALL | re.IGNORECASE)
            if not json_match:
                json_match = re.search(r'\{[^{}]*"scores".*?\}', raw_res, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    if json_str.count('{') > json_str.count('}'): json_str += '}'
                    data = json.loads(json_str)
                    report = raw_res.replace(json_match.group(), "").strip()
            else:
                data = json.loads(json_match.group(1))
                report = raw_res.replace(json_match.group(0), "").strip()
                
            mbti_type = data.get("type", mbti_type)
            default_scores = data.get("scores", default_scores)
        except:
            pass 
        
        # 寫入全域儀表板
        if not st.session_state.saved_to_board and mbti_type != "未定義":
            global_board.append({"受試者": st.session_state.nickname, "MBTI類型": mbti_type})
            st.session_state.saved_to_board = True
        
        st.balloons()
        
        # 渲染最終報告區塊
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        col_l, col_r = st.columns([3, 2])
        with col_l:
            st.markdown(report)
            
            # 一鍵匯出功能
            download_content = f"【TAICA 專屬人格解析 - {st.session_state.nickname}】\n\n專屬類型：{mbti_type}\n\n{report.replace('#', '')}"
            st.download_button(
                label="💌 一鍵下載專屬報告",
                data=download_content,
                file_name=f"TAICA_MBTI_{st.session_state.nickname}.txt",
                mime="text/plain"
            )
            
        with col_r:
            st.plotly_chart(master.draw_radar(default_scores, mbti_type), use_container_width=True)
            st.markdown(f"<h3 style='text-align: center;'>🎉 你的專屬類型：<span style='color:#FF7EB3;'>{mbti_type}</span></h3>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
