# 繪本風動畫 Reel（風格 C 延伸版）

小紅書「里大猫」那種樸素派繪本動畫的做法，用 `8bit-video-maker` skill 的流程做出來：
**寫一個 HTML → Playwright 逐格截圖 → ffmpeg 合成 MP4**。

輸出：`storybook_reel.mp4`（1080×1920，20 秒，24fps，含配樂）

---

## 和 skill 內建風格 C 的差別

skill 的 `watercolor_reel_template.html` 假設素材是 **AI 生圖 + PIL 去背**：
一張背景圖做 Ken Burns、一張角色圖疊上去搖擺。

這一版把場景改成 **純 SVG 平塗畫出來**，原因有兩個：

1. 樸素派／繪本風本來就是平面色塊，SVG 畫得出來，而且不用等生圖模型。
2. 更重要：**每一層都能獨立動**。單張背景圖只能整張一起縮放，
   分層之後天空、遠樹、近樹、草地、角色可以用不同倍率推進，**視差**才出得來。
   這是讓畫面「活起來」而不是「一張圖在放大」的關鍵。

想改回 AI 生圖版也可以：把 `<svg>` 換成 `<img>`，保留下面的 `seek()` 邏輯即可。

---

## 檔案

| 檔案 | 說明 |
|---|---|
| `storybook_reel.html` | 動畫本體。定義 `window.seek(t)`，給秒數畫出那一格 |
| `grain.png` | 紙質顆粒貼圖（Pillow 產生，300×300 雜訊） |
| `make_storybook_bgm.py` | 配樂合成（純 Python 標準庫，零版權） |
| `render_chunk.py` | 逐格截圖（改自 skill，加上 `executable_path`） |
| `preview.py` | 只截幾個時間點出來檢查，改稿時用這個，別每次都全渲染 |

---

## 重現步驟

```bash
# 0. 環境（本機通常只缺 ffmpeg）
pip install playwright pillow && playwright install chromium
# Ubuntu: apt-get install -y ffmpeg fonts-noto-cjk

# 1. 顆粒貼圖
python3 -c "
from PIL import Image; import random
random.seed(7); S=300
img=Image.new('RGBA',(S,S)); px=img.load()
for y in range(S):
    for x in range(S):
        v=random.randint(0,255); px[x,y]=(v,v,v,255)
img.save('grain.png')"

# 2. 改稿時先看單格（快）
python3 preview.py storybook_reel.html 2,10,19

# 3. 逐格渲染（540×960 @2x → 1080×1920），分段跑
for s in 0 120 240 360; do
  python3 render_chunk.py storybook_reel.html /tmp/frames 540 960 2 $s $((s+120))
done

# 4. 配樂 + 合成
python3 make_storybook_bgm.py bgm.wav 20
ffmpeg -y -framerate 24 -i /tmp/frames/f%04d.png -i bgm.wav \
  -vf "scale=1080:1920:flags=lanczos" -c:v libx264 -pix_fmt yuv420p -crf 18 \
  -c:a aac -b:a 160k -shortest -movflags +faststart storybook_reel.mp4
```

---

## 這支片好看在哪（可以直接套到別的題材）

### 1. 風格先定死
低彩度大地色、平塗無漸層、大色塊、紙紋顆粒。色票寫在檔頭，全片只用這幾個顏色。
不確定就少用顏色，不要多用。

### 2. 分層（最關鍵）
```
天空 → 雲 → 鳥 → 遠丘 → 後排樹 → 空氣霧 → 中排樹
     → 草坡 → 樹腳暗帶 → 前排樹 → 前景草地 → 草筆觸 → 人物 → 前景草葉
```
每層有一個「深度值」，鏡頭推進時 `k = 1 + (s-1) × 深度`。
天空 0.15、人物 1.22、最前景草葉 1.55 —— 差距就是視差。

### 3. 空氣遠近感
遠處疊一層淡色漸層（`hazeG`），越遠越白越淡。
**一定要用漸層不要用純色矩形**，否則畫面會出現一條硬邊。

### 4. 只動一點點
全片的動作只有：風吹樹叢、草擺、雲飄、鳥飛過、大衣輕晃、兔子抽耳朵（＋一次小跳）、浮塵。
沒有任何角色走路、轉身、揮手。**克制才高級**，而且不會崩。

風的寫法是兩個不同頻率的 sin 相加，避免規律得像節拍器：
```js
var w = Math.sin(t*0.55)*0.55 + Math.sin(t*1.02+2.4)*0.26;
```

### 5. 鏡頭慢推
20 秒只推進 9.5%，用 easeInOut。看得出來在動，但不會暈。

### 6. 後期統一
顆粒兩層（overlay 提亮 + multiply 壓暗）、暖光 soft-light、暗角。
這三層蓋下去，所有色塊會被「黏」成同一張紙上的畫。

---

## 踩過的坑

| 症狀 | 原因 | 修法 |
|---|---|---|
| 樹頂長出奇怪的鉤狀邊 | 用「偏移的錐形」當受光面，頂端曲線會互切 | 陰影／受光改用橢圓，clip 在樹形內 |
| 草的筆觸浮在樹叢上 | 草地元素的 y 範圍蓋到樹的區間 | 限制在樹腳線以下（y ≥ 636） |
| 畫面出現水平硬線 | 霧用了純色 `<rect>` | 換成 `linearGradient` 淡出 |
| 樹叢像聖誕樹 | 圓錐控制點太靠內、高寬比太大 | 控制點拉到 0.78w、高寬比降到約 3.7 |
| 分段渲染接不起來 | 場景用了 `Math.random()`，每次重載都不一樣 | 換成固定種子的 `mulberry32` |
| 找不到瀏覽器 | pip 版 playwright 與系統 chromium 版號不合 | `launch(executable_path="/opt/pw-browsers/chromium")` |

> 最後一點特別重要：**`seek(t)` 必須是純函式**。
> 分段渲染 = 頁面重新載入好幾次，任何隨機或累加狀態都會讓接縫處跳一下。
