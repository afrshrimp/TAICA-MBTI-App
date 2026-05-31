import streamlit as st
import json
import re
import plotly.graph_objects as go
import random
from groq import Groq
import pandas as pd

# --- 1. 頁面配置與櫻花馬卡龍系視覺美化 ---
st.set_page_config(page_title="TAICA MBTI V16.2 🌸 (Title Edition)", page_icon="👑", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #FFF5F7; color: #5D4037; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .main-title { color: #FF7EB3; text-align: center; font-size: 2.5rem; font-weight: 900; margin-bottom: 20px; text-shadow: 2px 2px 4px #FFD1DC; }
    .question-box { background: #FFFFFF; border: 2px solid #FFD1DC; padding: 25px; border-radius: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(255, 126, 179, 0.1); }
    .report-card { background: #FFFFFF; border: 2px dashed #FF9A9E; padding: 30px; border-radius: 25px; color: #5D4037; line-height: 1.8; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); }
    .stButton>button { background: linear-gradient(90deg, #FF9A9E 0%, #FECFEF 100%); color: #5D4037; font-weight: bold; border-radius: 30px; width: 100%; border: none; height: 3.5em; box-shadow: 0 4px 10px rgba(255, 154, 158, 0.3); transition: 0.3s; font-size: 1.1rem;}
    .stButton>button:hover { transform: scale(1.03); box-shadow: 0 6px 15px rgba(255, 154, 158, 0.4); }
    .stTextInput>div>div>input { border-radius: 15px; border: 1px solid #FFD1DC; }
    .pet-title { font-size: 2rem; color: #FF7EB3; text-align: center; font-weight: bold; margin-bottom: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 🔥 新增：MBTI 官方 16 型人格稱號字典 (零幻覺防禦機制) ---
MBTI_TITLES = {
    "INTJ": "建築師", "INTP": "邏輯學家", "ENTJ": "指揮官", "ENTP": "辯論家",
    "INFJ": "提倡者", "INFP": "調停者", "ENFJ": "主人公", "ENFP": "競選者",
    "ISTJ": "物流師", "ISFJ": "守衛者", "ESTJ": "總經理", "ESFJ": "執政官",
    "ISTP": "鑑賞家", "ISFP": "探險家", "ESTP": "企業家", "ESFP": "表演者"
}

# --- 2. 全域暫存資料庫 ---
@st.cache_resource
def get_global_leaderboard():
    return [] 

global_board = get_global_leaderboard()

# --- 3. 核心 AI 引擎 ---
class TAICAMasterCloud:
    def __init__(self):
        try:
            self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        except Exception:
            st.error("⚠️ 系統初始化異常：未偵測到雲端環境變數 GROQ_API_KEY。")
            
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
                temperature=0.4, 
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            return f"API 連線失敗：{e}"

    def draw_radar(self, scores, mbti_type):
        categories = ['E-I(外向/內向)', 'S-N(實感/直覺)', 'T-F(思考/情感)', 'J-P(判斷/感知)']
        
        def safe_val(v):
            try: return max(0, min(100, float(v))) 
            except: return 50 

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
            margin=dict(l=30, r=30, t=30, b=30)
        )
        return fig

# --- 4. 狀態管理與路由 ---
st.markdown('<h1 class="main-title">✨ 懂你的 16 型人格小助手 ✨</h1>', unsafe_allow_html=True)

if 'v16_init' not in st.session_state:
    master_temp = TAICAMasterCloud()
    all_qs = [{"dim": dim, "q": q} for dim, qs in master_temp.q_bank.items() for q in qs]
    random.shuffle(all_qs)
    
    st.session_state.update({
        'v16_init': False, 'step': 1, 'history': [], 'nickname': '', 'gender': '',
        'questions': all_qs, 'saved_to_board': False
    })

master = TAICAMasterCloud()

# --- 側邊欄 ---
with st.sidebar:
    st.markdown("### 🎀 測驗小檔案")
    if st.session_state.v16_init:
        st.write(f"🧸 暱稱: **{st.session_state.nickname}**")
        st.write(f"✨ 性別: **{st.session_state.gender}**")
        st.progress(min(st.session_state.step / 16, 1.0))
        st.write(f"解析進度: {min(st.session_state.step, 16)} / 16 題")
    
    st.markdown("---")
    st.markdown("### 🏆 班級 MBTI 統計牆")
    if len(global_board) > 0:
        df = pd.DataFrame(global_board)
        st.dataframe(df.tail(5).iloc[::-1], hide_index=True, use_container_width=True)
        type_counts = df['MBTI類型'].value_counts()
        st.bar_chart(type_counts, color="#FF7EB3")
    else:
        st.info("快成為全班第一個測出神獸的人！")
        
    st.markdown("---")
    if st.button("🔄 重新開始測驗", use_container_width=True):
        for k in st.session_state.keys(): del st.session_state[k]
        st.rerun()

# --- 5. 測驗主流程 ---
if not st.session_state.v16_init:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("👋 哈囉！先讓我認識你吧")
    c1, c2 = st.columns(2)
    with c1: nick = st.text_input("怎麼稱呼你呢？", placeholder="輸入暱稱")
    with c2: gend = st.radio("你的性別是？", ["女孩", "男孩"], horizontal=True)
    if st.button("🌸 開始探索專屬神獸 🌸"):
        if nick:
            st.session_state.nickname, st.session_state.gender, st.session_state.v16_init = nick, gend, True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step <= 16:
    current_q_text = st.session_state.questions[st.session_state.step - 1]['q']
    
    st.markdown(f'<div class="question-box"><h4>題 {st.session_state.step} / 16</h4><p style="font-size:1.3rem; font-weight:bold; color: #5D4037;">{current_q_text}</p></div>', unsafe_allow_html=True)
    
    with st.form(key=f"v16_form_{st.session_state.step}"):
        ans = st.text_input("你的直覺是什麼呢？", placeholder="隨心所欲地寫下想法...", key=f"input_{st.session_state.step}")
        submit = st.form_submit_button("送出答案 💌")
        
        if submit and ans:
            st.session_state.history.append({"q": current_q_text, "a": ans})
            st.session_state.step += 1
            st.rerun()

else:
    if 'final_report' not in st.session_state or 'final_pet' not in st.session_state:
        with st.spinner("✨ 測驗完成！大師正在進行 Fuzzy 模糊邏輯運算，並為你召喚專屬守護神獸..."):
            
           # 🔥 V16.3 提示詞修復：防抄襲機制與變數佔位符
            analysis_p = f"""
            受試者：{st.session_state.nickname} ({st.session_state.gender})。你現在是結合『模糊邏輯學(Fuzzy Logic)』與『社群遊戲化』的權威 AI。

            【⚖️ 核心技術：Fuzzy 模糊邏輯計分】
            人類的性格不是非黑即白。請在思考時，對每個回答進行「模糊程度」評分 (0~100)。
            - 0~49 代表偏向 E/S/T/J；50~100 代表偏向 I/N/F/P。
            最後綜合 16 題的模糊權重，給出最終分數。

            【🐾 社群分享：召喚印象寵物】
            請根據受試者的 MBTI 與回答特質，為他設計一隻專屬的「印象寵物 (Spirit Animal)」。
            格式必須為：形容詞 + 動物名稱 + Emoji。

            【🧠 思考鏈 (CoT) 與輸出規範】
            步驟 1：開啟 <thought_process> 標籤，進行模糊邏輯運算。
            步驟 2：關閉 </thought_process> 標籤。
            步驟 3：嚴格輸出下方的 ```json 區塊。
            步驟 4：撰寫溫柔的診斷報告。

            【⚠️ 絕對警告：禁止抄襲】
            下方的 JSON 範本只是「格式參考」，你絕對不可以輸出 "XXXX" 或 "形容詞+動物+Emoji"，你必須填入你親自計算出來的真實分數、4個大寫字母與設計出的寵物！

            【完美輸出格式範本】
            <thought_process>
            ...模糊運算過程...
            </thought_process>

            ```json
            {{"scores": {{"E-I": 85, "S-N": 30, "T-F": 70, "J-P": 20}}, "type": "XXXX", "pet": "形容詞+動物+Emoji"}}
            ```
            
            ### 🌸 TAICA 專屬人格解析 - {st.session_state.nickname} 🌸
            
            【🐾 你的專屬印象寵物】
            你是**(填入你生成的專屬寵物)**！(用兩句話溫柔解釋為什麼性格像這隻動物)
            
            【✨ 專屬你的閃光點】
            * (撰寫符合其 MBTI 的優點)
            
            【💡 小煩惱與成長建議】
            * (撰寫貼心建議)
            
            【報告結束】
            """
            raw_res = master.call_ai(analysis_p, str(st.session_state.history))
            
            default_scores = {"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50}
            mbti_type = "未定義"
            pet_name = "神祕可愛的小精靈 🧚"
            report = raw_res
            
            try:
                json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_res, re.DOTALL | re.IGNORECASE)
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
                pet_name = data.get("pet", pet_name)
                
                # 🔥 頭尾雙殺防禦法
                if "### 🌸 TAICA" in report:
                    report = "### 🌸 TAICA" + report.split("### 🌸 TAICA")[1]
                else:
                    report = re.sub(r'<thought_process>.*?</thought_process>', '', report, flags=re.DOTALL | re.IGNORECASE).strip()
                
                if "【報告結束】" in report:
                    report = report.split("【報告結束】")[0].strip()
                    
                report = re.sub(r'```[a-zA-Z]*', '', report).strip()
                
            except:
                pass
            
            st.session_state.final_report = report
            st.session_state.final_mbti_type = mbti_type
            st.session_state.final_scores = default_scores
            st.session_state.final_pet = pet_name
            
            if not st.session_state.saved_to_board and mbti_type != "未定義":
                global_board.append({"受試者": st.session_state.nickname, "MBTI類型": mbti_type})
                st.session_state.saved_to_board = True
            
            st.balloons()

    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    
    st.markdown(f'<div class="pet-title">你的靈魂神獸：{st.session_state.final_pet}</div>', unsafe_allow_html=True)
    
    col_l, col_r = st.columns([3, 2])
    with col_l:
        st.markdown(st.session_state.final_report)
        
        st.markdown("---")
        st.markdown("#### 💌 匯出你的專屬報告 (與朋友分享)")
        
        # 🔥 動態抓取官方稱號，若無則顯示「神祕類型」
        current_title = MBTI_TITLES.get(st.session_state.final_mbti_type, "神祕類型")
        
        export_txt = f"【TAICA 專屬人格解析 - {st.session_state.nickname}】\n\n專屬類型：{st.session_state.final_mbti_type} ({current_title})\n靈魂神獸：{st.session_state.final_pet}\n\n{st.session_state.final_report.replace('#', '')}"
        
        export_md = f"# TAICA 專屬人格解析 - {st.session_state.nickname}\n\n**專屬類型**：{st.session_state.final_mbti_type} ({current_title})\n**靈魂神獸**：{st.session_state.final_pet}\n\n{st.session_state.final_report}\n\n*(提示：使用瀏覽器打開此 Markdown 檔案，按下 Ctrl+P 即可列印成精美的 PDF 報告！)*"
        
        dl_c1, dl_c2 = st.columns(2)
        with dl_c1:
            st.download_button("📝 下載純文字版 (.txt)", data=export_txt, file_name=f"TAICA_MBTI_{st.session_state.nickname}.txt", mime="text/plain", use_container_width=True)
        with dl_c2:
            st.download_button("🖨️ 下載排版列印版 (.md)", data=export_md, file_name=f"TAICA_MBTI_{st.session_state.nickname}.md", mime="text/markdown", use_container_width=True)
            
    with col_r:
        st.plotly_chart(master.draw_radar(st.session_state.final_scores, st.session_state.final_mbti_type), use_container_width=True)
        
        # 🔥 網頁 UI 也同步顯示稱號！
        st.markdown(f"<h3 style='text-align: center; color: #5D4037;'>🎉 專屬類型：<span style='color:#FF7EB3;'>{st.session_state.final_mbti_type} ({current_title})</span></h3>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
