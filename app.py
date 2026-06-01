import streamlit as st
import json
import plotly.graph_objects as go
import random
from groq import Groq
import pandas as pd
import time
import base64

# --- 1. 頁面配置與視覺美化 ---
st.set_page_config(page_title="TAICA MBTI V20.0 🌸 (Ultimate Pet Edition)", page_icon="🐾", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700;900&display=swap');
    .stApp { background: linear-gradient(135deg, #FFF0F5 0%, #FFE4E1 100%); font-family: 'Noto Sans TC', sans-serif; color: #5D4037; }
    .main-title { 
        background: linear-gradient(45deg, #FF7EB3, #FF9A9E, #FF7EB3); background-size: 200% auto;
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; 
        text-align: center; font-size: 3.2rem; font-weight: 900; margin-bottom: 5px; 
    }
    .subtitle { text-align: center; color: #d87093; font-size: 1.2rem; margin-bottom: 30px; font-weight: 700; }
    .glass-card { 
        background: rgba(255, 255, 255, 0.75); backdrop-filter: blur(15px); -webkit-backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.9); padding: 35px; border-radius: 25px; margin: 20px 0; 
        box-shadow: 0 10px 40px rgba(255, 126, 179, 0.2); 
    }
    .stButton>button { 
        background: #FFFFFF; color: #FF7EB3; font-weight: 700; border-radius: 20px; 
        border: 2px solid #FFD1DC; height: auto; padding: 10px; box-shadow: 0 4px 10px rgba(255, 154, 158, 0.1); 
        transition: 0.3s; width: 100%; white-space: normal;
    }
    .stButton>button:hover { background: #FF7EB3; color: #FFFFFF; transform: translateY(-3px); border-color: #FF7EB3; box-shadow: 0 6px 15px rgba(255, 154, 158, 0.3);}
    .pet-title { font-size: 2.5rem; color: #FF7EB3; text-align: center; font-weight: 900; margin-bottom: 10px; text-shadow: 0 0 15px rgba(255,126,179,0.4); animation: pulse 2s infinite;}
    
    /* IG 限動卡片專屬 CSS */
    .ig-story-card {
        background: linear-gradient(135deg, #FF9A9E 0%, #FECFEF 100%);
        border-radius: 30px; padding: 40px 20px; text-align: center; color: white;
        aspect-ratio: 9/16; max-width: 320px; margin: 20px auto;
        box-shadow: 0 15px 35px rgba(255, 154, 158, 0.5); position: relative; overflow: hidden;
    }
    .ig-story-card h2 { color: white; font-size: 2.5rem; font-weight: 900; margin-bottom: 5px; text-shadow: 2px 2px 4px rgba(0,0,0,0.2);}
    .ig-story-card h3 { color: #FFF0F5; font-size: 1.5rem; font-weight: 700; margin-top: 0;}
    .ig-story-card .pet-emoji { font-size: 5rem; margin: 20px 0; text-shadow: 0 10px 20px rgba(0,0,0,0.15);}
    .ig-story-card .watermark { position: absolute; bottom: 20px; width: 100%; left: 0; font-size: 0.9rem; opacity: 0.8;}
    
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
    </style>
    """, unsafe_allow_html=True)

MBTI_TITLES = {
    "INTJ": "建築師", "INTP": "邏輯學家", "ENTJ": "指揮官", "ENTP": "辯論家",
    "INFJ": "提倡者", "INFP": "調停者", "ENFJ": "主人公", "ENFP": "競選者",
    "ISTJ": "物流師", "ISFJ": "守衛者", "ESTJ": "總經理", "ESFJ": "執政官",
    "ISTP": "鑑賞家", "ISFP": "探險家", "ESTP": "企業家", "ESFP": "表演者"
}

def create_download_link(data, filename, text, emoji):
    b64 = base64.b64encode(data.encode('utf-8')).decode()
    return f'<a href="data:file/txt;base64,{b64}" download="{filename}" style="background: #FFFFFF; color: #FF7EB3; font-weight: 700; border-radius: 20px; border: 2px solid #FFD1DC; padding: 10px; box-shadow: 0 4px 10px rgba(255, 154, 158, 0.1); transition: 0.3s; width: 100%; display: block; text-align: center; text-decoration: none; box-sizing: border-box; margin-top: 10px;">{emoji} {text}</a>'

@st.cache_resource
def get_global_leaderboard():
    return [] 
global_board = get_global_leaderboard()

# --- 3. 核心 AI 引擎 ---
class TAICAMasterCloud:
    def __init__(self):
        try: self.client = Groq(api_key=st.secrets["GROQ_API_KEY"])
        except: st.error("⚠️ 未偵測到 GROQ_API_KEY。")
        self.model = "llama-3.1-8b-instant" 
        self.q_bank = {
            'E-I': [
                {"q": "放假喜歡一個人宅著，還是跟朋友出門去玩？", "opts": ["🏠 絕對是宅在家", "🎉 找朋友出門嗨", "🤔 看心情跟看局"]},
                {"q": "到陌生的聚會，你會主動跟人搭話嗎？", "opts": ["💬 當然會主動聊", "👀 默默在角落觀察", "🤝 只找看起來好親近的"]},
                {"q": "心情不好時，喜歡找人傾訴還是自己消化？", "opts": ["🗣️ 找朋友大吐苦水", "🤫 自己躲起來安靜消化", "🎧 做別的事轉移注意"]},
                {"q": "在人群中，你通常是說話的人還是聽別人說？", "opts": ["📢 通常是我在說", "👂 我比較常當傾聽者", "⚖️ 說跟聽各半"]}
            ],
            'S-N': [
                {"q": "買東西是看實用性，還是憑感覺和設計？", "opts": ["🛠️ 絕對是實用至上", "✨ 顏值即正義感覺對就買", "⚖️ 實用跟好看我都要"]},
                {"q": "你喜歡按部就班，還是充滿驚喜的生活？", "opts": ["📋 喜歡一切在計畫中", "🎁 喜歡充滿變化跟驚喜", "🔄 大方向要有小細節隨意"]},
                {"q": "你比較常想著『現在該做什麼』還是『未來會怎樣』？", "opts": ["🎯 活在當下解決眼前", "🚀 常常腦洞大開想未來", "🧭 為了未來規劃現在"]},
                {"q": "看電影時，你注意畫面細節還是整體的意境？", "opts": ["🔍 注意服裝道具等細節", "🌌 感受整體氛圍與意境", "🍿 只顧著看劇情爽不爽"]}
            ],
            'T-F': [
                {"q": "朋友遇到困難，你先幫他想辦法還是先安慰他？", "opts": ["💡 馬上幫他分析解決", "🫂 先安撫情緒最重要", "🤝 邊安慰邊想辦法"]},
                {"q": "做決定時，你更相信客觀邏輯還是內心直覺？", "opts": ["📊 列優缺點理性分析", "💖 跟著直覺感覺走", "⚖️ 理智分析後交給直覺"]},
                {"q": "看比賽時，你在乎誰贏，還是過程精不精彩？", "opts": ["🏆 當然在乎輸贏", "🎢 過程刺激精彩最重要", "🌟 有喜歡的選手就好"]},
                {"q": "你覺得『講道理』比較重要，還是『顧及感受』？", "opts": ["⚖️ 道理就是道理", "❤️ 傷感情就沒意思了", "🤔 看事情的嚴重程度"]}
            ],
            'J-P': [
                {"q": "出門旅行會排好行程，還是走到哪玩到哪？", "opts": ["🗺️ 行程表排滿按表操課", "🎲 沒計畫走到哪玩到哪", "📍 只定大景點剩下隨緣"]},
                {"q": "你的桌面通常是乾淨整齊的，還是亂中有序？", "opts": ["✨ 一塵不染物歸原位", "🌪️ 別人看亂但我找得到", "🧹 一陣一陣的大掃除才乾淨"]},
                {"q": "喜歡提前把作業做完，還是最後一刻才趕工？", "opts": ["✅ 提早做完才安心", "🔥 死線前才有爆發力", "📅 會分配進度慢慢做"]},
                {"q": "買東西會先列好清單，還是看到喜歡就買？", "opts": ["📝 嚴格按照清單買", "🛒 逛一逛看到喜歡就買", "😅 有清單但還是會亂買"]}
            ]
        }

    def call_ai(self, system_prompt, user_prompt):
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}],
                model=self.model, temperature=0.5, max_tokens=2048, response_format={"type": "json_object"} 
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as e:
            return f'{{"report": "API 異常：{e}", "type": "未知", "pet": "迷路的小狗 🐶", "scores": {{"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50}}}}'

    def draw_radar(self, scores, mbti_type):
        categories = ['E-I(外向/內向)', 'S-N(實感/直覺)', 'T-F(思考/情感)', 'J-P(判斷/感知)']
        def safe_val(v):
            try: return max(0, min(100, float(v))) 
            except: return 50 
        values = [safe_val(scores.get('E-I', 50)), safe_val(scores.get('S-N', 50)), safe_val(scores.get('T-F', 50)), safe_val(scores.get('J-P', 50))]
        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=values, theta=categories, fill='toself', fillcolor='rgba(255, 154, 158, 0.45)', 
            line=dict(color='#FF7EB3', width=3), marker=dict(color='#FF7EB3', size=10), name=f"類型: {mbti_type}"
        ))
        fig.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 100], gridcolor="rgba(255, 154, 158, 0.3)"),
                angularaxis=dict(gridcolor="rgba(255, 154, 158, 0.3)", tickfont=dict(size=13, color="#5D4037"))
            ),
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)", margin=dict(l=40, r=40, t=40, b=40)
        )
        return fig

# --- 4. 狀態管理 ---
st.markdown('<h1 class="main-title">🐾 TAICA 專屬寵物測驗 🐾</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">AI 驅動・尋找潛藏在你靈魂深處的專屬萌寵</div>', unsafe_allow_html=True)

if 'v20_init' not in st.session_state:
    master_temp = TAICAMasterCloud()
    all_qs = []
    for dim, qs in master_temp.q_bank.items():
        for q_dict in qs: all_qs.append({'dim': dim, 'q': q_dict['q'], 'opts': q_dict['opts']})
    random.shuffle(all_qs)
    st.session_state.update({
        'v20_init': False, 'step': 1, 'history': [], 'nickname': '', 'gender': '',
        'questions': all_qs, 'saved_to_board': False,
        'final_report': '', 'final_mbti_type': '未定義', 
        'final_scores': {"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50}, 'final_pet': '神祕精靈'
    })

master = TAICAMasterCloud()

# --- 5. 三大核心分頁 (Tabs) ---
tab1, tab2, tab3 = st.tabs(["✨ 尋找專屬寵物", "💞 寵物羈絆合盤", "📊 數據中心 (開發者)"])

with tab1:
    main_c1, main_c2, main_c3 = st.columns([1, 4, 1])
    with main_c2:
        if not st.session_state.v20_init:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.subheader("👋 哈囉！準備好遇見你的專屬寵物了嗎？")
            c1, c2 = st.columns(2)
            with c1: nick = st.text_input("怎麼稱呼你呢？", placeholder="輸入你的專屬暱稱")
            with c2: gend = st.radio("你的角色設定是？", ["女孩 🌸", "男孩 🍃"], horizontal=True)
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""<style>div[data-testid="stButton"] button {background: linear-gradient(90deg, #FF9A9E 0%, #FECFEF 100%); color: #5D4037;}</style>""", unsafe_allow_html=True)
            if st.button("✨ 點擊開始探索 ✨"):
                if nick:
                    st.session_state.nickname, st.session_state.gender, st.session_state.v20_init = nick, gend, True
                    st.toast(f"歡迎來到 TAICA，{nick}！旅程開始囉 🚀")
                    time.sleep(0.5)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.step <= 16:
            for chat in st.session_state.history:
                with st.chat_message("ai", avatar="🐾"): st.write(chat['q'])
                with st.chat_message("human", avatar="🌸" if st.session_state.gender=="女孩 🌸" else "🍃"): st.write(chat['a'])
                    
            curr_q = st.session_state.questions[st.session_state.step - 1]
            with st.chat_message("ai", avatar="🐾"):
                st.markdown(f"**第 {st.session_state.step}/16 題：**<br><span style='font-size: 1.2rem; color:#5D4037;'>{curr_q['q']}</span>", unsafe_allow_html=True)
                st.write("") 
                opt_cols = st.columns(3)
                for i, opt in enumerate(curr_q['opts']):
                    if opt_cols[i].button(opt, key=f"btn_{st.session_state.step}_{i}"):
                        st.session_state.history.append({"q": curr_q['q'], "a": opt})
                        st.session_state.step += 1
                        st.rerun()
                        
            user_input = st.chat_input("選項不夠準？在這裡輸入你自己獨特的想法...")
            if user_input:
                st.session_state.history.append({"q": curr_q['q'], "a": user_input})
                st.session_state.step += 1
                st.rerun()

        # 測驗完成報告區
        if st.session_state.get('v20_init') and st.session_state.step > 16:
            if not st.session_state.final_report:
                with st.spinner("🐾 測驗完成！大師正在進行模糊運算，為你召喚專屬寵物..."):
                    
                    # 🔥 隱藏彩蛋 Prompt：如果很隨和就出水豚！
                    analysis_p = f"""
                    受試者：{st.session_state.nickname} ({st.session_state.gender})。你現在是結合『模糊邏輯學』的權威 AI。
                    請分析 16 題回答。對每個回答評分 (0~49偏向 E/S/T/J；50~100偏向 I/N/F/P)。
                    
                    【🎁 隱藏彩蛋機制 (極機密)】
                    如果受試者的回答展現出「極度隨和、情緒穩定、喜歡自己消化、不愛社交」等高比例的 I 與 P 特質，請務必將專屬寵物設定為超稀有的：『佛系大水豚 🦦』！
                    
                    【⚠️ 系統強制輸出規範 (JSON Mode)】
                    必須只輸出一個合法 JSON，包含：
                    1. "thought_process": 運算總結（限 50 字內）。
                    2. "scores": {{"E-I":整數, "S-N":整數, "T-F":整數, "J-P":整數}}
                    3. "type": 4 碼 MBTI。
                    4. "pet": 專屬寵物 (格式：形容詞 + 動物 + Emoji)。
                    5. "report": 給使用者的完整解析報告。排版包含「🐾 你的專屬寵物」、「✨ 專屬閃光點」、「💡 成長建議」。
                    """
                    raw_res = master.call_ai(analysis_p, str(st.session_state.history))
                    
                    try:
                        data = json.loads(raw_res)
                        mbti_type = data.get("type", "未定義")
                        default_scores = data.get("scores", {"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50})
                        pet_name = data.get("pet", "萌萌小精靈 🧚")
                        report = data.get("report", "報告生成失敗。")
                        print(f"\n=== [後台監控] {st.session_state.nickname} 運算日誌 ===\n{data.get('thought_process', '無日誌')}\n")
                    except Exception as e:
                        mbti_type, pet_name, default_scores = "未定義", "萌萌小精靈 🧚", {"E-I": 50, "S-N": 50, "T-F": 50, "J-P": 50}
                        report = f"系統解析中發生插曲！(錯誤碼: {e})"
                    
                    st.session_state.update({'final_report': report, 'final_mbti_type': mbti_type, 'final_scores': default_scores, 'final_pet': pet_name})
                    if not st.session_state.saved_to_board and mbti_type != "未定義":
                        global_board.append({"受試者": st.session_state.nickname, "MBTI類型": mbti_type, "寵物": pet_name})
                        st.session_state.saved_to_board = True
                    
                    st.balloons() # 抽卡成功特效
                    st.toast("🎉 你的專屬萌寵已降臨！")
                    st.rerun()

            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown(f'<div class="pet-title">✨ 召喚成功 ✨<br>你的專屬寵物是：{st.session_state.final_pet}</div>', unsafe_allow_html=True)
            
            # --- 📸 IG 限動分享卡產生器 ---
            current_title = MBTI_TITLES.get(st.session_state.final_mbti_type, "神祕類型")
            pet_emoji = st.session_state.final_pet.split(" ")[-1] if " " in st.session_state.final_pet else "🐾"
            ig_html = f"""
            <div class="ig-story-card">
                <h3>{st.session_state.nickname} 的專屬寵物</h3>
                <div class="pet-emoji">{pet_emoji}</div>
                <h2>{st.session_state.final_mbti_type}</h2>
                <p style="font-size:1.2rem; font-weight:bold;">{st.session_state.final_pet}</p>
                <div class="watermark">🔍 TAICA AI 人格測驗</div>
            </div>
            <p style="text-align:center; color:#FF7EB3; font-weight:bold;">📸 推薦：手機長按圖片或直接截圖發佈 IG 限動！</p>
            """
            
            col_l, col_r = st.columns([1.2, 1])
            with col_l:
                st.markdown(st.session_state.final_report)
                st.markdown("<br><hr>", unsafe_allow_html=True)
                export_txt = f"【TAICA 專屬人格解析 - {st.session_state.nickname}】\n\n類型：{st.session_state.final_mbti_type} ({current_title})\n專屬寵物：{st.session_state.final_pet}\n\n{st.session_state.final_report.replace('#', '')}"
                dl_c1, dl_c2 = st.columns(2)
                with dl_c1: st.markdown(create_download_link(export_txt, f"TAICA_{st.session_state.nickname}.txt", "下載純文字版", "📝"), unsafe_allow_html=True)
                with dl_c2: 
                    if st.button("🔄 再玩一次"): 
                        for k in st.session_state.keys(): del st.session_state[k]
                        st.rerun()
            with col_r:
                st.plotly_chart(master.draw_radar(st.session_state.final_scores, st.session_state.final_mbti_type), use_container_width=True)
                st.markdown(ig_html, unsafe_allow_html=True) # 顯示 IG 卡片
            st.markdown('</div>', unsafe_allow_html=True)

with tab2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#FF7EB3;'>💞 寵物羈絆合盤系統</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center;'>測完你的 MBTI 了嗎？輸入好友或伴侶的 MBTI，看看你們的靈魂有多契合！</p>", unsafe_allow_html=True)
    
    bond_c1, bond_c2 = st.columns(2)
    with bond_c1: my_mbti = st.selectbox("你的 MBTI", list(MBTI_TITLES.keys()), index=0)
    with bond_c2: friend_mbti = st.selectbox("朋友的 MBTI", list(MBTI_TITLES.keys()), index=15)
    
    if st.button("🔮 計算羈絆指數", use_container_width=True):
        with st.spinner("AI 正在解析兩隻寵物的相處模式..."):
            bond_prompt = f"請以輕鬆可愛的語氣，分析 {my_mbti} 與 {friend_mbti} 的相處契合度。輸出包含：1. 契合度分數(1~100) 2. 簡短相處優勢 3. 潛在小摩擦。限 150 字。"
            bond_result = master.call_ai("你是 MBTI 戀愛與人際關係大師，回答簡短精確。", bond_prompt)
            st.success("計算完成！")
            st.info(bond_result)
    st.markdown('</div>', unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<h2 style='text-align:center; color:#FF7EB3;'>📊 TAICA 數據中心</h2>", unsafe_allow_html=True)
    if len(global_board) > 0:
        df = pd.DataFrame(global_board)
        st.markdown(f"**累積探索人數：** {len(df)} 人")
        st.dataframe(df.iloc[::-1], hide_index=True, use_container_width=True)
        
        st.markdown("### 🌟 班級 MBTI 分佈")
        type_counts = df['MBTI類型'].value_counts().reset_index()
        type_counts.columns = ['MBTI類型', '人數']
        st.bar_chart(type_counts.set_index('MBTI類型'), color="#FF9A9E")
    else:
        st.info("目前系統剛啟動，還沒有數據進來喔！去測驗大廳邀請同學來玩吧！")
    st.markdown('</div>', unsafe_allow_html=True)
