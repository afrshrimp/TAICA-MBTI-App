import streamlit as st
import json
import re
import plotly.graph_objects as go
import random
from groq import Groq
import pandas as pd

# --- 1. 頁面配置與櫻花馬卡龍系視覺美化 ---
st.set_page_config(page_title="TAICA MBTI V15 🌸 (CoT Edition)", page_icon="👑", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
    .stApp { background-color: #FFF5F7; color: #5D4037; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .main-title { color: #FF7EB3; text-align: center; font-size: 2.5rem; font-weight: 800; margin-bottom: 20px; text-shadow: 1px 1px 2px #FFD1DC; }
    .question-box { background: #FFFFFF; border: 2px solid #FFD1DC; padding: 25px; border-radius: 20px; margin: 20px 0; box-shadow: 0 4px 10px rgba(255, 126, 179, 0.1); }
    .report-card { background: #FFFFFF; border: 2px dashed #FF9A9E; padding: 30px; border-radius: 25px; color: #5D4037; line-height: 1.8; box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05); }
    .stButton>button { background: linear-gradient(90deg, #FF9A9E 0%, #FECFEF 100%); color: #5D4037; font-weight: bold; border-radius: 30px; width: 100%; border: none; height: 3em; box-shadow: 0 4px 10px rgba(255, 154, 158, 0.3); transition: 0.3s; font-size: 1.1rem;}
    .stButton>button:hover { transform: scale(1.03); box-shadow: 0 6px 15px rgba(255, 154, 158, 0.4); }
    .stTextInput>div>div>input { border-radius: 15px; border: 1px solid #FFD1DC; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. 全域暫存資料庫 (Demo 現場互動核心) ---
@st.cache_resource
def get_global_leaderboard():
    # 利用 Streamlit 快取機制建立零配置的臨時資料庫
    return [] 

global_board = get_global_leaderboard()

# --- 3. 核心 AI 引擎 (搭載 Groq 雲端大腦) ---
class TAICAMasterCloud:
    def __init__(self):
        try:
            self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        except Exception as e:
            st.error("⚠️ 系統初始化異常：未偵測到雲端環境變數 GROQ_API_KEY。")
            
        # 鎖定高可用性、極速推論的 Llama 3.1 8B 瞬態模型
        self.model = "llama-3.1-8b-instant" 
        
        # 經過 UX 優化的極簡生活化題庫 (20字以內)
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
                temperature=0.3, # 低溫度，鎖定幻覺，確保 Chain-of-Thought 的邏輯穩定
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            return f"API 連線失敗：{e}"

    def draw_radar(self, scores, mbti_type):
        categories = ['E-I(外向/內向)', 'S-N(實感/直覺)', 'T-F(思考/情感)', 'J-P(判斷/感知)']
        
        # 確保雷達圖數值在 0-100 之間，防止 AI 計算失誤噴出負數
        def safe_val(v):
            try:
                return max(0, min(100, float(v))) 
            except:
                return 50 # 預設中間值

        values = [safe_val(scores.get('E-I', 50)), safe_val(scores.get('S-N', 50)), 
                  safe_val(scores.get('T-F', 50)), safe_val(scores.get('J-P', 50))]
                  
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values, theta=categories, fill='toself',
            fillcolor='rgba(255, 154, 158, 0.3)', line=dict(color='#FF7EB3', width=3),
            marker=dict(color='#FF7EB3', size=8), name=f"類型: {mbti_type}"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100], gridcolor="#FFE4E1"),
                       angularaxis=dict(gridcolor="#FFE4E1", color="#5D4037")),
            paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#5D4037"),
            margin=dict(l=30, r=30, t=30, b=30)
        )
        return fig

# --- 4. 狀態管理與路由設計 ---
st.markdown('<h1 class="main-title">✨ 懂你的 16 型人格小助手 ✨</h1>', unsafe_allow_html=True)

if 'v15_init' not in st.session_state:
    master_temp = TAICAMasterCloud()
    # 預先隨機化題庫並排好序列
    all_qs = [{"dim": dim, "q": q} for dim, qs in master_temp.q_bank.items() for q in qs]
    random.shuffle(all_qs)
    
    st.session_state.update({
        'v15_init': False, 'step': 1, 'history': [], 'nickname': '', 'gender': '',
        'questions': all_qs, 'saved_to_board': False
    })

master = TAICAMasterCloud()

# --- 側邊欄：即時數據可視化儀表板 (作品集亮點) ---
with st.sidebar:
    st.markdown("### 🎀 測驗小檔案")
    if st.session_state.v15_init:
        st.write(f"🧸 暱稱: **{st.session_state.nickname}**")
        st.write(f"✨ 性別: **{st.session_state.gender}**")
        st.progress(min(st.session_state.step / 16, 1.0))
        st.write(f"解析進度: {min(st.session_state.step, 16)} / 16 題")
    
    st.markdown("---")
    st.markdown("### 🏆 班級 MBTI 統計牆 (Demo 互動用)")
    if len(global_board) > 0:
        df = pd.DataFrame(global_board)
        # 顯示最新測驗的 5 個人 (倒序顯示)
        st.dataframe(df.tail(5).iloc[::-1], hide_index=True, use_container_width=True)
        # 顯示直觀的條形統計圖
        st.write("**類型分佈排行：**")
        type_counts = df['MBTI類型'].value_counts()
        st.bar_chart(type_counts, color="#FF7EB3")
    else:
        st.info("目前還沒有人完成測驗喔，在 Demo 現場趕快搶頭香！")
        
    st.markdown("---")
    if st.button("🔄 重新開始測驗", use_container_width=True):
        for k in st.session_state.keys(): del st.session_state[k]
        st.rerun()

# --- 5. 測驗主流程控制 ---
# 階段 A: 身分認證登錄
if not st.session_state.v11_init:
    st.markdown('<div class="report-card">', unsafe_allow_html=True)
    st.subheader("👋 哈囉！先讓我認識你吧")
    c1, c2 = st.columns(2)
    with c1: nick = st.text_input("怎麼稱呼你呢？", placeholder="輸入暱稱")
    with c2: gend = st.radio("你的性別是？", ["女孩", "男孩"], horizontal=True)
    if st.button("🌸 開始輕鬆測驗 🌸"):
        if nick:
            # 兼容 V11 的 session 初始化邏輯
            st.session_state.nickname, st.session_state.gender, st.session_state.v11_init = nick, gend, True
            st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# 階段 B: 快速測驗 (Python 內建題庫，不耗 Token 不延遲)
elif st.session_state.step <= 16:
    current_q_text = st.session_state.questions[st.session_state.step - 1]['q']
    
    st.markdown(f'<div class="question-box"><h4>題 {st.session_state.step} / 16</h4><p style="font-size:1.3rem; font-weight:bold; color: #5D4037;">{current_q_text}</p></div>', unsafe_allow_html=True)
    
    # 使用 st.form 確保輸入完畢再送出，節省 Streamlit 的重新渲染開銷
    with st.form(key=f"v15_form_{st.session_state.step}"):
        ans = st.text_input("你的直覺是什麼呢？", placeholder="簡單寫下你的想法...", key=f"input_{st.session_state.step}")
        submit = st.form_submit_button("送出答案 💌")
        
        if submit and ans:
            # 儲存對話歷史供最後分析
            st.session_state.history.append({"q": current_q_text, "a": ans})
            st.session_state.step += 1
            st.rerun()

# 階段 C: 最終 AI 深度報告 (搭載 V15 最高級 Chain-of-Thought 思考鏈)
else:
    with st.spinner("✨ 測驗完成！大師正在雲端利用 Chain-of-Thought 思考鏈精算數據，並為你撰寫報告..."):
        
        # 🔥 V15 終極提示工程：引入隱藏思考區與邏輯一致性契約
        analysis_p = f"""
        受試者：{st.session_state.nickname}。你現在是權威 AI 心理計量學家。請依據使用者的 16 題回答，嚴謹計算其 MBTI。

        【學術要求：測驗準確性協議】
        為確保診斷的絕對準確，你必須嚴格遵循以下「思考鏈 (Chain-of-Thought)」步驟進行：

        步驟 1：在輸出任何正式內容前，你必須先開啟一個 <thought_process> 標籤。
        步驟 2：在 <thought_process> 內，逐題分析使用者的回答對應到哪個心理維度倾向。
        步驟 3：在 <thought_process> 內，手算四個維度的統計分數，並確定最終 MBTI 類型。
        步驟 4：關閉 </thought_process> 標籤。
        步驟 5：根據你在思考區得出的結論，輸出嚴格標準的 ```json 區塊。
        步驟 6：撰寫與算出的 JSON 數據百分之百對齊、絕不矛盾的溫柔繁體中文診斷報告。報告標題請填入：### 🌸 TAICA 專屬人格解析 - (填入受試者暱稱) 🌸

        【🔥 絕對指令：邏輯一致性契約】
        你的報告敘述必須完全合理化該 MBTI 類型的標準特質，絕不可前後矛盾！
        - 如果是 I (內向)，報告重點應放在其「內在能量來源、深思熟慮」，絕不可寫「充滿廣泛的社交溝通與主動搭話特質」。
        - 如果是 Fe (ISFJ/INFJ) 表現出的主動社交，必須合理解釋其基於同理心的初衷，而非 E 人的能量來源。

        【完美輸出範例範本】
        <thought_process>
        - 分析題1：選擇宅在家，I維度傾向 +10。
        - 分析題5：雖然會社交但提到需要獨處充電，判定為 I 維度。
        - ...逐題分析完畢。
        - 分數統計加總: E-I: 20, S-N: 60, T-F: 45, J-P: 75。最終判定類型為 ISFJ。
        </thought_process>

        ```json
        {{"scores": {{"E-I": 20, "S-N": 60, "T-F": 45, "J-P": 75}}, "type": "ISFJ"}}
        ```
        
        ### 🌸 TAICA 專屬人格解析 - (暱稱) 🌸
        
        【專屬你的閃光點✨】
        * (符合 ISFJ 的閃光點...)
        
        【小煩惱與成長建議💡】
        * (符合 ISFJ 的建議...)
        """
        raw_res = master.call_ai(analysis_p, str(st.session_state.history))
        
        # 初始化預設值，防止 AI 幻覺導致崩潰
        default_scores = {"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50}
        mbti_type = "未定義"
        report = raw_res
        
        try:
            # V15 容錯型 JSON 解析引擎 (已修復 Markdown 格式與引號問題)
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_res, re.DOTALL | re.IGNORECASE)
            if not json_match:
                # 退而求其次，尋找包含 "scores" 的大括號區塊
                json_match = re.search(r'\{[^{}]*"scores".*?\}', raw_res, re.DOTALL)
                if json_match:
                    json_str = json_match.group()
                    # 暴力修復 AI 偶爾忘記關大括號的 Bug
                    if json_str.count('{') > json_str.count('}'): json_str += '}'
                    data = json.loads(json_str)
                    # 移除原文字中的 JSON 區塊
                    report = raw_res.replace(json_match.group(), "").strip()
            else:
                # 正常抓取到 Markdown 區塊
                data = json.loads(json_match.group(1))
                # 將 JSON 區塊（含 Markdown 標籤）從原文字中剔除
                report = raw_res.replace(json_match.group(0), "").strip()
                
            mbti_type = data.get("type", mbti_type)
            default_scores = data.get("scores", default_scores)
            
            # 【關鍵優化】剔除 AI 思考鏈區塊 (`<thought_process>...</thought_process>`)，只保留報告本身
            report = re.sub(r'<thought_process>.*?</thought_process>', '', report, flags=re.DOTALL | re.IGNORECASE).strip()
            
        except:
            # 解析失敗時，雖然無法畫圖，但至少呈現完整的 AI 原始回應（含報告）
            st.warning("⚠️ 喔喔！AI 大腦在計算多維度分數時稍微發散了，但大師已經還原了報告內容！")
        
        # 寫入全域統計牆 (確保網站不休眠前數據持久化)
        if not st.session_state.saved_to_board and mbti_type != "未定義":
            global_board.append({"受試者": st.session_state.nickname, "MBTI類型": mbti_type})
            st.session_state.saved_to_board = True
        
        # 成功完成測驗，觸發氣球特效
        st.balloons()
        
        # 渲染最終診斷報告與雷達圖區塊
        st.markdown('<div class="report-card">', unsafe_allow_html=True)
        col_l, col_r = st.columns([3, 2])
        with col_l:
            # 顯示純淨版診斷報告 (已濾除 JSON 與思考鏈)
            st.markdown(report)
            
            # 增加期末專題亮點功能：一鍵匯出報告 txt
            download_content = f"【TAICA 專屬人格解析 - {st.session_state.nickname}】\n\n專屬類型：{mbti_type}\n\n{report.replace('#', '')}"
            st.download_button(
                label="💌 一鍵下載我的專屬報告",
                data=download_content,
                file_name=f"TAICA_MBTI_{st.session_state.nickname}.txt",
                mime="text/plain",
                use_container_width=True
            )
            
        with col_r:
            st.plotly_chart(master.draw_radar(default_scores, mbti_type), use_container_width=True)
            st.markdown(f"<h3 style='text-align: center; color: #5D4037;'>🎉 你的專屬類型：<span style='color:#FF7EB3;'>{mbti_type}</span></h3>", unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
