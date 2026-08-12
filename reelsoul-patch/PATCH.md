# Reelsoul 增補：繪本插畫動畫（SVG 分層）

這一包是要**併進你本機的 `~/.claude/skills/reelsoul/`**，不是獨立 skill。

來源：2026-08-09 實作《樹牆》60 秒 12 鏡故事片的整條產線（含實際踩到的坑）。

---

## 一、直接放進去的檔案

| 這一包裡的位置 | 放到 reelsoul 的哪裡 | 是什麼 |
|---|---|---|
| `references/繪本插畫動畫.md` | `references/` | 新的工藝文件（主要內容） |
| `scripts/contact.py` | `scripts/` | 接觸表工具（抽格拼成一張圖檢查） |
| `scripts/make_bgm_storybook.py` | `scripts/` | 鋼琴＋弦樂墊配樂（chiptune 之外的第二種） |
| `examples/範例_繪本分層動畫.html` | `references/範例/` | 12 鏡 60 秒故事片，可直接改 |
| `examples/範例_繪本單場景.html` | `references/範例/` | 單場景 20 秒版，比較好上手 |
| `examples/grain.png` | `references/範例/` | ★ 顆粒貼圖，**必須跟兩支 HTML 放同一層**，否則紙紋不會出現 |

兩支範例都是自足的：`python3 scripts/contact.py references/範例/範例_繪本分層動畫.html 2.5,32.5,57.5`
就能直接看到畫面，不需要任何素材或金鑰。

`contact.py` 吃環境變數 `CHROMIUM`（指定 chromium 執行檔）、`CANVAS_W` / `CANVAS_H`。

`make_bgm_storybook.py` 和既有的 `make_chiptune_bgm.py` 是同一套思路
（純標準庫 `wave` 寫取樣點、零版權），只是音色換成柔和鋼琴＋弦樂墊，配插畫風。

---

## 二、要改的既有檔案

### 1. `SKILL.md` — 開場第 4 題，五種改六種

原文：
```
4️⃣ 要不要插播動畫？要的話哪種風格：
   資訊圖解（黑板）／動畫字卡／8-bit 像素／火柴人手繪／水彩插畫
```
改成：
```
4️⃣ 要不要插播動畫？要的話哪種風格：
   資訊圖解（黑板）／動畫字卡／8-bit 像素／火柴人手繪／水彩插畫／繪本插畫（分層）
```

### 2. `SKILL.md` — Step 5 插播動畫段落

原文：
```
**動畫**：詳見 `references/插播動畫.md`。五種風格（開場第 4 題問過使用者要哪種）：
資訊圖解（黑板／黑底）／動畫字卡轉場／8-bit 像素／火柴人手繪／水彩插畫。
```
改成：
```
**動畫**：詳見 `references/插播動畫.md`。六種風格（開場第 4 題問過使用者要哪種）：
資訊圖解（黑板／黑底）／動畫字卡轉場／8-bit 像素／火柴人手繪／水彩插畫／繪本插畫（分層）。
繪本插畫另見 `references/繪本插畫動畫.md`——它和水彩插畫的差別是「整個場景用 SVG 畫、
每層獨立動」，做得出真正的視差，也是唯一適合拿來做「多鏡頭故事片」的一種。
```

### 3. `SKILL.md` — 檔案地圖，工法區加一行

在 `references/火柴人動畫工藝.md` 那行下面插入：
```
- `references/繪本插畫動畫.md` — ★繪本／樸素派分層動畫：純函式 seek(t)、深度視差表、
  只動一點點、場景切換、12 鏡故事片結構、平行渲染、兩段式響度（做繪本風前必讀）
```

### 4. `SKILL.md` — 引擎表，`html_render.py` 那列補一句

原文：
```
| `html_render.py` | HTML `seek(t)` 逐格算圖 → mp4（像素／火柴人／水彩／字卡共用） |
```
改成：
```
| `html_render.py` | HTML `seek(t)` 逐格算圖 → mp4（像素／火柴人／水彩／繪本／字卡共用）。**長片開多 process 平行跑**：照 frame index 寫檔互不干擾，核心數 -1 個 worker，1440 格從 26 分鐘降到 9 分鐘 |
```

### 5. `references/常見錯誤.md` — 併入這幾列

繪本／分層動畫專屬的症狀，`繪本插畫動畫.md` 末尾有完整表，這裡挑跨風格通用的四則：

| 症狀 | 原因 | 修法 |
|---|---|---|
| 分段渲染的接縫處畫面跳掉 | 場景生成用了 `Math.random()`，每次重載都不一樣 | 換固定種子 PRNG（`mulberry32`）；`seek(t)` 必須是純函式 |
| 畫面出現不該有的水平硬線 | 霧／漸層區塊用了純色 `<rect>` | 換 `linearGradient` 往下淡出 |
| 瀏覽器起不來、叫你跑 `playwright install`（跑了也沒用） | pip 版 playwright 與系統 chromium 版號不合 | `launch(executable_path="<chromium 路徑>")` |
| 合成後聲音很小，推大就爆 | 只看 LUFS 沒看真實峰值餘裕 | 先量 json；餘裕不夠就走兩段式 loudnorm（見下） |

### 6. `references/剪輯工藝.md` — 音訊段落補「兩段式 loudnorm」

現有做法（平推增益）在 LRA 小的時候沒問題，但**峰值餘裕不夠時會爆**。補這段判斷：

```
量：ffmpeg -i in.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json -f null -

目標增益 = -14 − input_i
若 input_tp + 目標增益 < -1.5  → 平推 volume=XdB（最乾淨，不動動態）
否則                          → 兩段式：把 measured_I / measured_TP / measured_LRA /
                                measured_thresh / offset 五個值餵回第二段
```

順便補編碼那段：**平塗／插畫類畫面 crf 用 23 就好**，crf 18 只是在編碼顆粒雜訊，
並排放大比對看不出差別，檔案卻是兩倍大。

---

## 三、順手記一筆：token 成本

這次全程 5,800 萬 tokens，其中 94% 是快取讀取（每輪重讀整段對話）。
真正的輸出只有 37.5 萬。**渲染完全不花 token**——1440 格截圖、ffmpeg、
配樂合成全是 CPU。

最花 token 的是「看圖改稿」：每張讀進來的截圖，之後每一輪都要重讀一次。
所以 `繪本插畫動畫.md` 裡把**接觸表**列為 QC 的標準做法，
一顆一顆單獨截圖看是最貴的做法。
