# 第 13 組｜AI 讀心術：結合語意分析與 MBTI 理論的次世代性格檢測工具

## 1. 專案簡介

本專案為 TAICA 期末專案第 13 組作品，題目為：

**AI 讀心術：結合語意分析與 MBTI 理論的次世代性格檢測工具**

本系統以 Streamlit 建立互動式網頁介面，結合 Groq API 之生成式 AI 模型與 MBTI 四向度架構，讓使用者透過 16 題測驗完成個人化人格傾向分析。系統除了輸出 MBTI 類型，也提供中文類型稱呼、四向度分數、12 項延伸特質、職涯點子、工作特質、關係模式、能量驅動因素，以及多格式報告下載功能。

本系統定位為**課程展示與人格傾向探索工具**，並非正式心理診斷或臨床評估工具。

---

## 2. 組別與組員

| 組別 | 第 13 組 |
|---|---|

| 姓名 | 學校 |系別 | Email | 分工 |
|---|---|---|---|---|
| 胡佳鈺 | 龍華科技大學 |電機系碩一｜ G1142161011@gm.lhu.edu.tw | 專案主題規劃、系統架構設計、Streamlit 介面開發、Groq API 串接、MBTI 四向度計分邏輯、進階報告與匯出功能整合、報告與影片內容統整 |
| 胡佳媺 | 龍華科技大學 |電機系二技四年級｜ D1132161001@gm.lhu.edu.tw | 測驗題目與選項檢查、使用者操作流程測試、介面文字檢視 |
| 顏祐成 | 龍華科技大學 |電機系碩一｜ G1142161004@gm.lhu.edu.tw | 系統功能測試、結果頁面檢查、圖表呈現與報告下載流程測試 |
| 劉權慶 | 龍華科技大學 |電子系二年級｜ D1134172033@gm.lhu.edu.tw | 程式執行環境、套件安裝、部署流程測試與問題回饋 |

---

## 3. 專案特色

1. **混合式作答設計**  
   使用者可直接選擇參考選項，也可在「以上皆非」時輸入自由文字，兼顧低操作門檻與個人化表達。

2. **程式端穩定計分**  
   MBTI 四向度分數與最終類型由程式端計算，避免生成式 AI 每次自行判斷造成結果不一致。

3. **生成式 AI 報告生成**  
   系統將鎖定後的分數與類型交由 Groq API 生成繁體中文人格分析報告。

4. **中文化 MBTI 結果**  
   不只顯示 ISTJ、ENFP 等英文縮寫，也提供本專案自訂中文稱呼，例如「ISTJ｜穩健執行者」。

5. **12 項延伸特質分數**  
   系統根據四向度結果延伸推估社交互動能量、獨處恢復能量、現實細節敏銳度、邏輯決策強度、壓力調節彈性等 12 項輔助指標。

6. **視覺化圖表**  
   提供 MBTI 四向度雷達圖與 12 項延伸特質長條圖，讓使用者更直觀理解結果。

7. **多格式報告匯出**  
   支援 PDF、PNG、HTML、TXT 與 ZIP 報告包下載。手機使用者可優先使用單一檔案下載，降低操作困難。

---

## 4. 系統架構

本系統主要流程如下：

```text
使用者輸入基本資料
        ↓
16 題 MBTI 四向度測驗
        ↓
儲存結構化作答紀錄
        ↓
程式端計算四向度分數
        ↓
推導 MBTI 類型與中文稱呼
        ↓
Groq API 生成文字分析報告
        ↓
產生雷達圖、長條圖與完整報告
        ↓
提供 PDF / PNG / HTML / TXT / ZIP 下載
```

---

## 5. 使用技術

| 類別 | 技術 |
|---|---|
| 前端介面 | Streamlit |
| AI 模型 API | Groq API |
| 生成模型 | llama-3.1-8b-instant |
| 圖表視覺化 | Plotly、Matplotlib、Pillow |
| PDF 報告生成 | ReportLab、Pillow |
| 程式語言 | Python |
| 部署平台 | Streamlit Community Cloud |

---

## 6. 專案檔案說明

專案目錄如下：

```text
taica-ai-mbti-report/
│
├── app.py
├── requirements.txt
├── packages.txt
├── README.md
└── .gitignore
```

| 檔案 | 說明 |
|---|---|
| `app.py` | Streamlit 主程式，包含測驗流程、計分邏輯、AI 報告生成與報告匯出 |
| `requirements.txt` | Python 套件需求 |
| `packages.txt` | Streamlit Cloud 系統套件需求，用於安裝中文字型 |
| `README.md` | 專案說明文件 |
| `.gitignore` | 避免上傳 API Key、快取檔與環境檔案 |

---

## 7. 安裝方式

### 7.1 下載專案

```bash
git clone https://github.com/afrshrimp/TAICA-MBTI-App.git
cd taica-ai-mbti-report
```

### 7.2 安裝 Python 套件

```bash
pip install -r requirements.txt
```

`requirements.txt` 內容：

```txt
streamlit
plotly
groq
reportlab
pillow
kaleido
```

---

## 8. Groq API Key 設定

本系統需要 Groq API Key 才能產生 AI 文字報告。

### 8.1 本機執行設定

請在專案根目錄建立資料夾：

```bash
mkdir .streamlit
```

接著建立檔案：

```text
.streamlit/secrets.toml
```

內容如下：

```toml
GROQ_API_KEY = "請填入你的 Groq API Key"
GROQ_MODEL = "llama-3.1-8b-instant"
```

### 8.2 注意事項

請勿將以下檔案上傳至 GitHub：

```text
.streamlit/secrets.toml
```

因為此檔案包含 API Key，若公開上傳可能造成金鑰外洩。

`.gitignore` 內容：

```gitignore
.streamlit/secrets.toml
__pycache__/
*.pyc
.env
```

---

## 9. 本機執行方式

在 PowerShell 或終端機輸入：

```bash
streamlit run app.py
```

執行後瀏覽器會自動開啟系統頁面。若沒有自動開啟，可手動進入：

```text
http://localhost:8501
```

---

## 10. Streamlit Cloud 部署說明

若要讓使用者透過網址直接測驗，可部署至 Streamlit Community Cloud。

### 10.1 GitHub 準備

請將以下檔案上傳至 GitHub repository：

```text
app.py
requirements.txt
packages.txt
README.md
.gitignore
```

請勿上傳：

```text
.streamlit/secrets.toml
```

### 10.2 packages.txt

為避免 PDF 中文變成方塊，Streamlit Cloud 需加入系統中文字型套件。

`packages.txt` 內容：

```txt
fonts-noto-cjk
```

### 10.3 Streamlit Cloud Secrets

在 Streamlit Cloud 的 App 設定中加入 Secrets：

```toml
GROQ_API_KEY = "請填入你的 Groq API Key"
GROQ_MODEL = "llama-3.1-8b-instant"
```

### 10.4 部署完成

部署完成後會產生類似以下網址：

```text
https://你的專案名稱.streamlit.app
```

---

## 11. 操作流程

1. 使用者進入系統首頁。
2. 輸入暱稱與稱謂偏好。
3. 依序回答 16 題測驗。
4. 每題可選擇參考選項，或選擇「以上皆非，我想自己回答」輸入自由文字。
5. 系統根據作答紀錄計算 MBTI 四向度分數。
6. 系統推導 MBTI 類型與中文稱呼。
7. Groq API 生成繁體中文人格分析報告。
8. 系統顯示雷達圖、長條圖與完整文字報告。
9. 使用者可下載 PDF、PNG、HTML、TXT 或 ZIP 報告包。

---

## 12. 測驗與報告內容

系統輸出的報告包含：

- MBTI 類型
- 中文稱呼
- 類型摘要
- E-I、S-N、T-F、J-P 四向度分數
- 四向度雷達圖
- 12 項延伸特質長條圖
- 完整人格分析報告
- 職涯點子
- 工作特質
- 關係模式
- 能量驅動因素
- 免責聲明

---

## 13. 重要限制與聲明

1. 本系統僅供課程展示與人格傾向探索使用。
2. 本系統不是正式心理診斷工具。
3. MBTI 結果僅代表本次作答下的傾向，不應作為職涯、醫療或心理決策的唯一依據。
4. 12 項延伸特質為本專案依 MBTI 四向度設計之輔助分析指標，並非標準化心理量表。
5. 若多人同時使用，可能受到 API 速率限制或網路環境影響。

---

## 14. 開發過程中遇到的問題與修正

| 問題 | 原因 | 修正方式 |
|---|---|---|
| Groq 舊模型停用 | 原使用模型已被官方停用 | 改用 `llama-3.1-8b-instant` |
| AI 報告與分數不一致 | 早期版本讓 AI 同時計分與寫報告 | 改由程式端鎖定分數與類型，AI 僅負責文字化報告 |
| S-N、T-F 術語混用 | 生成式 AI 容易混淆 MBTI 術語 | Prompt 中加入嚴格術語定義與限制 |
| 手機 PDF 文字變方塊 | PDF 中文字型未正確顯示 | 改用圖片化 PDF 與 Noto CJK 字型 |
| ZIP 對手機不友善 | 手機使用者需額外解壓縮 | 單一檔案下載優先，ZIP 改為進階選項 |

---

## 15. 未來改進方向

1. 增加題目數量，提高分數判斷穩定性。
2. 引入向量語意相似度或更完整的語意標註方法。
3. 加入使用者歷史紀錄與多次測驗比較功能。
4. 加入更多圖表互動與個人化解釋。
5. 增加管理者後台，供研究或課堂展示統計使用。

---

## 16. 授權與使用範圍

本專案為 TAICA 課程期末專案成果，主要用於課程展示、學習紀錄與非商業用途。若後續延伸使用，應注意 Groq API 使用規範、模型服務限制與使用者資料隱私保護。

---

## 17. 聯絡方式

主要開發與專案整合：

胡佳鈺  
龍華科技大學  
G1142161011@gm.lhu.edu.tw
