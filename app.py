import streamlit as st
import json
import re
import plotly.graph_objects as go
import random
from groq import Groq
import pandas as pd
import time

# --- 1. 頁面配置與進階毛玻璃 (Glassmorphism) 視覺美化 ---
st.set_page_config(page_title="TAICA MBTI V17.0 🌸 (Glassmorphism)", page_icon="👑", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&family=JetBrains+Mono&display=swap');
    
    /* 漸層背景與全域字體 */
    .stApp { 
        background: linear-gradient(135deg, #FFF0F5 0%, #FFE4E1 100%); 
        font-family: 'Noto Sans TC', sans-serif; 
        color: #5D4037;
    }
    
    /* 漸層動態標題 */
    .main-title { 
        background: linear-gradient(45deg, #FF7EB3, #FF9A9E, #FF7EB3);
        background-size: 200% auto;
        -webkit-background-clip: text; 
        -webkit-text-fill-color: transparent; 
        text-align: center; font-size: 3rem; font-weight: 900; 
        margin-bottom: 10px; 
        animation: shine 3s linear infinite, fadeInDown 0.8s ease-out;
    }
    .subtitle { text-align: center; color: #d87093; font-size: 1.1rem; margin-bottom: 40px; font-weight: 700; }
    
    /* 毛玻璃題目卡片 (Glassmorphism) */
    .question-box { 
        background: rgba(255, 255, 255, 0.6); 
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.8); 
        padding: 35px; border-radius: 25px; margin: 20px 0; 
        box-shadow: 0 8px 32px rgba(255, 126, 179, 0.15); 
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* 最終報告精緻卡片 */
    .report-card { 
        background: #FFFFFF; border: none; padding: 40px; border-radius: 30px; 
        color: #5D4037; line-height: 1.8; 
        box-shadow: 0 10px 40px rgba(255, 154, 158, 0.2); 
        animation: fadeIn 1s ease-in;
    }
    
    /* 漸層按鈕 hover 放縮特效 */
    .stButton>button { 
        background: linear-gradient(90deg, #FF9A9E 0%, #FECFEF 100%); 
        color: #5D4037; font-weight: 900; border-radius: 30px; width: 100%; border: none; 
        height: 3.5em; box-shadow: 0 4px 15px rgba(255, 154, 158, 0.4); 
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); font-size: 1.15rem;
    }
    .stButton>button:hover { 
        transform: translateY(-3px) scale(1.02); 
        box-shadow: 0 8px 25px rgba(255, 154, 158, 0.6); 
    }
    
    /* 靈魂神獸專屬呼吸燈特效 */
    .pet-title { 
        font-size: 2.2rem; color: #FF7EB3; text-align: center; font-weight: 900; 
        margin-bottom: 25px; text-shadow: 0 0 15px rgba(255,126,179,0.3);
        animation: pulse 2.5s infinite ease-in-out;
    }
    
    /* 輸入框美化 */
    .stTextArea>div>div>textarea { border-radius: 15px; border: 2px solid #FFE4E1; background: rgba(255,255,255,0.9); }
    .stTextArea>div>div>textarea:focus { border-color: #FF9A9E; box-shadow: 0 0 10px rgba(255, 154, 158, 0.3); }
    .stTextInput>div>div>input { border-radius: 15px; border: 2px solid #FFE4E1; }
    
    /* 定義關鍵影格動畫 */
    @keyframes shine { to { background-position: 200% center; } }
    @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
    @keyframes fadeInUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes fadeInDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.03); } 100% { transform: scale(1); } }
    </style>
    """, unsafe_allow_html=True)

# --- 🔥 MBTI 官方 16 型人格稱號字典 ---
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
            fillcolor='rgba(255, 154, 158, 0.45)', line=dict(color='#FF7EB3', width=3),
            marker=dict(color='#FF7EB3', size=10, symbol='diamond'), name=f"類型: {mbti_type}"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255, 154, 158, 0.3)"),
                       angularaxis=dict(gridcolor="rgba(255, 154, 158, 0.3)", color="#5D4037", font=dict(size=13, weight="bold"))),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", font=dict(color="#5D4037"),
            margin=dict(l=40, r=40, t=40, b=40)
        )
        return fig

# --- 4. 狀態管理與路由 ---
st.markdown('<h1 class="main-title">✨ TAICA 靈魂神獸測驗 ✨</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI 驅動・深度探索你的 16 型隱藏人格</div>', unsafe_allow_html=True)

if 'v17_init' not in st.session_state:
    master_temp = TAICAMasterCloud()
    all_qs = [{"dim": dim, "q": q} for dim, qs in master_temp.q_bank.items() for q in qs]
    random.shuffle(all_qs)
    
    st.session_state.update({
        'v17_init': False, 'step': 1, 'history': [], 'nickname': '', 'gender': '',
        'questions': all_qs, 'saved_to_board': False
    })

master = TAICAMasterCloud()

# --- 側邊欄：進階儀表板 ---
with st.sidebar:
    st.markdown("### 🎀 專屬探索檔案")
    if st.session_state.v17_init:
        st.write(f"🧸 探險家: **{st.session_state.nickname}**")
        st.write(f"✨ 特質: **{st.session_state.gender}**")
        st.progress(min(st.session_state.step / 16, 1.0))
        st.write(f"🔮 探索進度: {min(st.session_state.step, 16)} / 16 題")
    
    st.markdown("---")
    st.markdown("### 🏆 班級神獸圖鑑 (Live)")
    if len(global_board) > 0:
        df = pd.DataFrame(global_board)
        st.dataframe(df.tail(5).iloc[::-1], hide_index=True, use_container_width=True)
        type_counts = df['MBTI類型'].value_counts()
        st.bar_chart(type_counts, color="#FF7EB3")
    else:
        st.info("圖鑑空空如也，快成為全班第一隻登錄的神獸！")
        
    st.markdown("---")
    if st.button("🔄 重新展開旅程", use_container_width=True):
        for k in st.session_state.keys(): del st.session_state[k]
        st.rerun()

# --- 5. 測驗主流程 ---
# 為了讓畫面在寬螢幕下更集中、更好看，使用 columns 進行版面置中控制
main_c1, main_c2, main_c3 = st.columns([1, 4, 1])

with main_c2:
    if not st.session_state.v17_init:
        st.markdown('<div class="question-box">', unsafe_allow_html=True)
        st.subheader("👋 哈囉！準備好遇見你的靈魂神獸了嗎？")
        c1, c2 = st.columns(2)
        with c1: nick = st.text_input("怎麼稱呼你呢？", placeholder="輸入你的專屬暱稱")
        with c2: gend = st.radio("你的角色設定是？", ["女孩 🌸", "男孩 🍃"], horizontal=True)
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("✨ 點擊開始探索 ✨"):
            if nick:
                st.session_state.nickname, st.session_state.gender, st.session_state.v17_init = nick, gend, True
                st.toast(f"歡迎來到 TAICA，{nick}！旅程開始囉 🚀")
                time.sleep(0.5)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.step <= 16:
        current_q_text = st.session_state.questions[st.session_state.step - 1]['q']
        
        # 進度條美化
        st.progress(st.session_state.step / 16.0)
        
        st.markdown(f'<div class="question-box"><h4 style="color: #FF9A9E; margin-bottom: 5px;">第 {st.session_state.step} 題 / 共 16 題</h4><p style="font-size:1.5rem; font-weight:900; color: #5D4037; line-height: 1.5;">{current_q_text}</p></div>', unsafe_allow_html=True)
        
        with st.form(key=f"v17_form_{st.session_state.step}"):
            ans = st.text_area("你的直覺是什麼呢？(越詳細 AI 算得越準喔！)", placeholder="靜下心來，隨心所欲地寫下想法...", key=f"input_{st.session_state.step}", height=120)
            submit = st.form_submit_button("送出心聲 💌")
            
            if submit and ans:
                st.session_state.history.append({"q": current_q_text, "a": ans})
                st.session_state.step += 1
                st.rerun()

# 滿版顯示分析報告 (跳出 main_c2 的限制)
if st.session_state.get('v17_init') and st.session_state.step > 16:
    if 'final_report' not in st.session_state or 'final_pet' not in st.session_state:
        with st.spinner("✨ 測驗完成！大師正在進行 Fuzzy 模糊邏輯運算，並為你召喚專屬守護神獸..."):
            
            # --- 以下為完整保留的後台 AI 核心邏輯 ---
            analysis_p = f"""
            受試者：{st.session_state.nickname} ({st.session_state.gender})。你現在是結合『模糊邏輯學(Fuzzy Logic)』與『社群遊戲化』的權威 AI。

            【⚖️ 核心技術：Fuzzy 模糊邏輯計分】
            人類的性格不是非黑即白。請在思考時，對每個回答進行「模糊程度」評分 (0~100)。
            - 0~49 代表偏向 E/S/T/J；50~100 代表偏向 I/N/F/P。
            最後綜合 16 題的模糊權重，給出最終分數。

            【🐾 社群分享：召喚印象寵物】
            請根據受試者的 MBTI 與回答特質，為他設計一隻專屬的「印象寵物 (Spirit Animal)」。
            格式必須為：形容詞 + 動物名稱 + Emoji。

            【🧠 思考鏈 (CoT)】
            步驟 1：開啟 <thought_process> 標籤，進行模糊邏輯運算。
            步驟 2：關閉 </thought_process> 標籤。
            步驟 3：嚴格輸出下方的 ```json 區塊 (必須包含 pet 欄位)。
            步驟 4：撰寫溫柔的診斷報告。

            【完美輸出格式範本】
            <thought_process>
            ...模糊運算過程...
            </thought_process>

            ```json
            {{"scores": {{"E-I": 25, "S-N": 35, "T-F": 80, "J-P": 15}}, "type": "ESFJ", "pet": "熱情溫暖的黃金獵犬 🦮"}}
            ```
            
            ### 🌸 TAICA 專屬人格解析 - {st.session_state.nickname} 🌸
            
            【🐾 你的專屬印象寵物】
            你是**(填入寵物名稱)**！(用兩句話溫柔解釋為什麼性格像這隻動物)
            
            【✨ 專屬你的閃光點】
            * (撰寫符合其 MBTI 的優點)
            
            【💡 小煩惱與成長建議】
            * (撰寫貼心建議)
            
            【報告結束】
            """
            raw_res = master.call_ai(analysis_p, str(st.session_state.history))
            
            default_scores = {"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50}
            mbti_type, pet_name = "未定義", "神祕可愛的小精靈 🧚"
            report = raw_res
            
            try:
                json_match = re.search(r"```json\s*(\{.*?\})\s*```", raw_res, re.DOTALL | re.IGNORECASE)
                if not json_match:
                    json_match = re.search(r'\{[^{}]*"scores".*?\}', raw_res, re.DOTALL)
                    if json_match:
                        json_str = json_match.group()
                        if json_str.count('{') > json_str.count('}'): json_str += '}'
                        data = json.loads(json_str)
                else:
                    data = json.loads(json_match.group(1))
                    
                mbti_type = data.get("type", mbti_type)
                default_scores = data.get("scores", default_scores)
                pet_name = data.get("pet", pet_name)
                
                # 🔥 擷取後台思考過程並印出 (完美保留開發者日誌)
                thought_match = re.search(r'<thought_process>(.*?)</thought_process>', raw_res, re.DOTALL | re.IGNORECASE)
                backend_log = thought_match.group(1).strip() if thought_match else "無思考過程紀錄"
                print(f"\n=== [後台監控] {st.session_state.nickname} 的 MBTI 運算日誌 ===")
                print(backend_log)
                print("=====================================================\n")

                # 🔥 頭尾雙殺防禦法 (清理前端報告)
                if "### 🌸 TAICA" in raw_res:
                    report = "### 🌸 TAICA" + raw_res.split("### 🌸 TAICA")[1]
                else:
                    report = re.sub(r'<thought_process>.*?</thought_process>', '', raw_res, flags=re.DOTALL | re.IGNORECASE).strip()
                
                if "【報告結束】" in report:
                    report = report.split("【報告結束】")[0].strip()
                    
                report = re.sub(r'```json.*?```', '', report, flags=re.DOTALL | re.IGNORECASE).strip()
                report = re.sub(r'```[a-zA-Z]*', '', report).strip()
                
            except Exception as e:
                print(f"解析發生錯誤: {e}")
                report = "系統正在進行深度腦力激盪，請稍後再試！"
            
            st.session_state.final_report = report
            st.session_state.final_mbti_type = mbti_type
            st.session_state.final_scores = default_scores
            st.session_state.final_pet = pet_name
            
            if not st.session_state.saved_to_board and mbti_type != "未定義":
                global_board.append({"受試者": st.session_state.nickname, "MBTI類型": mbti_type})
                st.session_state.saved_to_board = True
            
            st.balloons()
            st.toast("🎉 你的專屬神獸已降臨！")

    # --- 渲染超美終極報告 ---
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    
    st.markdown(f'<div class="pet-title">你的靈魂神獸是...<br>✨ {st.session_state.final_pet} ✨</div>', unsafe_allow_html=True)
    
    col_l, col_r = st.columns([1.2, 1])
    with col_l:
        st.markdown(st.session_state.final_report)
        
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.markdown("#### 💌 匯出你的專屬報告 (與朋友分享)")
        
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
        st.markdown(f"<h3 style='text-align: center; color: #5D4037; animation: fadeIn 2s ease-in;'>🎉 專屬類型：<br><span style='color:#FF7EB3; font-size: 2.5rem; font-weight: 900;'>{st.session_state.final_mbti_type}</span><br>({current_title})</h3>", unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
