import streamlit as st
import pandas as pd
import requests
import os
import glob
import base64
import random
import altair as alt
import math
from datetime import datetime, timedelta

# --- 1. 基础路径配置 ---
# 获取当前代码文件所在的文件夹路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

# 假设你的图片放在代码同级目录下的 'images' 文件夹中
IMAGE_DIR_PATH = os.path.join(CURRENT_DIR, "esimages") 

# 数据文件夹放在代码同级目录下的 'es_data' 文件夹中
DATA_DIR_PATH = os.path.join(CURRENT_DIR, "es_data")

# 移除了 page_icon 中的 emoji
st.set_page_config(page_title="ES Deluxe Tracker", layout="wide")

# --- 2. 全局筛选标准 ---
UNIVERSE_KEYWORDS = [
    "eternal sunshine", "intro (end of the world)", "bye", "don't wanna break up again",
    "saturn returns interlude", "supernatural", "true story", "the boy is mine",
    "yes, and?", "we can't be friends", "i wish i hated you", "imperfect for you",
    "ordinary things", "twilight zone", "warm", "dandelion", "past life", "hampstead"
]

def is_relevant_track(name):
    n = name.lower()
    if "we can" in n and "friends" in n and "live" in n: return True
    if "don" in n and "wanna" in n and "live" in n: return True
    return any(k in n for k in UNIVERSE_KEYWORDS)

# --- 3. 工具函数 ---
def get_img_base64(file_name):
    possible_exts = ['.jpg', '.png', '.webp', '.jpeg']
    file_path = None
    direct_path = os.path.join(IMAGE_DIR_PATH, file_name)
    if os.path.exists(direct_path):
        file_path = direct_path
    else:
        base_name = os.path.splitext(file_name)[0]
        for ext in possible_exts:
            temp_path = os.path.join(IMAGE_DIR_PATH, base_name + ext)
            if os.path.exists(temp_path):
                file_path = temp_path
                break
    if not file_path: return ""
    with open(file_path, "rb") as f: data = f.read()
    encoded = base64.b64encode(data).decode()
    if file_path.endswith('.png'): mime = 'image/png'
    elif file_path.endswith('.webp'): mime = 'image/webp'
    else: mime = 'image/jpeg'
    return f"data:{mime};base64,{encoded}"

def clean_number(x):
    try: return int(str(x).replace(',', '').replace('+', '').split('.')[0])
    except: return 0

def fix_encoding(s):
    if not isinstance(s, str): return s
    s = s.replace("â€™", "'").replace("â\x80\x99", "'").replace("’", "'")
    s = s.replace("â€“", "-").replace("â\x80\x93", "-").replace("–", "-")
    return s

# --- 4. 随机背景 ---
search_pattern = os.path.join(IMAGE_DIR_PATH, "imgi_*.jpg")
bg_candidates = glob.glob(search_pattern)
if not bg_candidates: 
    bg_candidates = glob.glob(os.path.join(IMAGE_DIR_PATH, "*.jpg"))

specific_bgs = [
    "ab67616d0000b2738e7e2c150cdfe189f7584fc4.jpg",
    "ab67616d00001e0296094d0c80f0f321da705f88.jpg",
    "c05ac5704cafd9d1242c0225e5c2ce67.1000x1000x1.png",
    "c96f76385524a89fea9f1fa731113c6a.1000x1000x1.png",
    "c1646624c824a8fadb6640002a43afe4.1000x1000x1.png",
    "d2e07aab978bc9c5270a3113587205fe.1000x1000x1.png",
    "e2da24f179bcc16641dac283bd5ad4e1.1000x1000x1.png",
    "ab67616d00001e0207894829ab71aac2e995f425.jpg"
]

for bg_file in specific_bgs:
    full_path = os.path.join(IMAGE_DIR_PATH, bg_file)
    if os.path.exists(full_path):
        bg_candidates.append(full_path)

if bg_candidates:
    if 'random_bg_path' not in st.session_state:
        st.session_state.random_bg_path = random.choice(bg_candidates)
    bg_base64 = get_img_base64(os.path.basename(st.session_state.random_bg_path))
else: bg_base64 = ""

# --- 5. 样式 (CSS) ---
PRIMARY_COLOR = "#8B0000"
SECONDARY_COLOR = "#FF6347"
POSITIVE_COLOR = "#2E8B57"
NEGATIVE_COLOR = "#B22222"

css_styles = f"""
<style>
html, body, [class*="css"], .stApp, .stApp *, div, span, p, h1, h2, h3, h4, h5, h6, table, td, th {{
    font-family: 'Times New Roman', Times, serif !important;
}}
.stApp {{
    background-image: linear-gradient(rgba(255, 255, 255, 0.25), rgba(255, 255, 255, 0.25)), url("{bg_base64}");
    background-repeat: repeat; 
    background-size: 33.333% auto; 
    background-position: top left;
    background-attachment: fixed;
}}
.block-container {{ max-width: 1600px; padding-top: 1rem; padding-bottom: 5rem; margin: 0 auto; }}

/* --- Hero Card --- */
.hero-card {{
    background: linear-gradient(135deg, rgba(255, 250, 250, 0.98), rgba(255, 240, 240, 0.98));
    border: 2px solid {PRIMARY_COLOR};
    border-radius: 20px;
    padding: 25px;
    box-shadow: 0 8px 20px rgba(139, 0, 0, 0.15);
    margin-bottom: 30px;
}}
.hero-title {{
    font-size: 42px;
    font-weight: 800;
    color: {PRIMARY_COLOR};
    margin-bottom: 5px; /* Reduced for timestamp */
    text-transform: uppercase;
    letter-spacing: 2px;
    text-align: center;
    text-shadow: 1px 1px 0px rgba(255,255,255,0.8);
}}
.hero-timestamp {{
    font-size: 16px;
    color: #666;
    text-align: center;
    margin-bottom: 25px;
    border-bottom: 1px solid rgba(139,0,0,0.1);
    padding-bottom: 15px;
    font-style: italic;
}}
.hero-flex-container {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 20px;
}}
.hero-side {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 20px;
    min-width: 450px;
}}
.hero-data {{ text-align: center; flex: 1; }}
.hero-img {{
    width: 180px; height: 180px;
    border-radius: 0;
    box-shadow: none;
    object-fit: cover;
}}
.hero-divider {{
    width: 2px; height: 120px;
    background-color: {SECONDARY_COLOR}; 
    opacity: 0.3; margin: 0 10px;
}}
.hero-label {{ font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: 1px; margin-top: 5px; }}
.hero-val-big {{ font-size: 36px; font-weight: 700; color: {PRIMARY_COLOR}; margin: 2px 0; line-height: 1.1; }}
.hero-val-daily {{ font-size: 24px; font-weight: 700; color: {POSITIVE_COLOR}; }}
.hero-sub-title {{ font-size: 22px; font-weight: 700; color: #333; margin-bottom: 10px; }}

/* --- Sub Cards --- */
.sub-card-flex {{
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid {PRIMARY_COLOR};
    border-radius: 15px;
    padding: 20px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 20px;
    box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    height: 100%;
}}
.sub-card-img {{
    width: 220px; height: 220px;
    border-radius: 0;
    box-shadow: none;
    object-fit: cover;
    flex-shrink: 0;
}}
.sub-card-data {{ flex: 1; text-align: center; }}

/* --- Metrics & Badges --- */
.metric-title {{ font-size: 20px; font-weight: bold; color: {PRIMARY_COLOR}; margin-bottom: 12px; }}
.metric-label {{ font-size: 15px; color: #666; text-transform: uppercase; letter-spacing: 1px; }}
.flex-metric-row {{ display: flex; justify-content: center; align-items: baseline; flex-wrap: nowrap; gap: 10px; width: 100%; }}
.metric-value-small {{ font-size: 32px; font-weight: 700; color: {PRIMARY_COLOR}; margin: 0; }}
.sub-metric {{ font-size: 14px; color: #888; margin-top: 8px; }}
.comp-badge {{ font-size: 16px; font-weight: bold; vertical-align: middle; white-space: nowrap; margin-left: 5px; }}
.comp-up {{ color: {POSITIVE_COLOR}; }}
.comp-down {{ color: {NEGATIVE_COLOR}; }}

/* --- Highlight Strip --- */
.highlight-strip {{
    background: rgba(255, 255, 255, 0.95);
    border: 1px solid #ddd;
    border-radius: 12px;
    padding: 0;
    display: flex;
    overflow: hidden;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    margin-bottom: 20px;
    flex-wrap: wrap;
}}
.highlight-left {{
    flex: 1.3;
    min-width: 450px;
    padding: 20px;
    border-right: 1px solid #eee;
    background: linear-gradient(to right, #fffaf0, #fff);
}}
.highlight-right {{
    flex: 1;
    min-width: 350px;
    padding: 20px;
    background: #fff;
}}
.hl-header {{
    font-size: 16px; font-weight: bold; color: {PRIMARY_COLOR};
    margin-bottom: 15px; text-transform: uppercase; letter-spacing: 1px;
    border-bottom: 2px solid #f0f0f0; padding-bottom: 5px;
}}
.mover-col {{ flex: 1; }}
.mover-row {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; font-size: 15px; border-bottom: 1px dashed #f0f0f0; padding-bottom: 4px; }}
.mover-song-name {{ white-space: normal; word-break: break-word; margin-right: 10px; flex: 1; }}
.gainer-pct {{ color: {POSITIVE_COLOR}; font-weight: bold; white-space: nowrap; }}
.faller-pct {{ color: {NEGATIVE_COLOR}; font-weight: bold; white-space: nowrap; }}

.stats-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }}
.stat-box {{ background: #fdfdfd; padding: 12px; border-radius: 8px; text-align: center; border: 1px solid #eee; box-shadow: 0 2px 5px rgba(0,0,0,0.03); }}
.stat-label {{ font-size: 13px; color: #666; margin-bottom: 5px; font-weight: 600; }}
.stat-val {{ font-size: 20px; font-weight: bold; color: {PRIMARY_COLOR}; }}

/* --- Milestone Section --- */
.milestone-box {{
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 20px; text-align: center; gap: 10px;
}}
.milestone-title {{
    font-size: 26px; font-weight: 800; color: {PRIMARY_COLOR}; text-transform: uppercase;
}}
.milestone-data {{
    font-size: 18px; color: #333; margin: 10px 0;
}}
.spotify-btn {{
    display: inline-block;
    background-color: #1DB954;
    color: white;
    padding: 12px 24px;
    border-radius: 25px;
    text-decoration: none;
    font-weight: bold;
    font-size: 16px;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: background-color 0.3s;
    margin-top: 10px;
}}
.spotify-btn:hover {{ background-color: #1ed760; color: white; text-decoration: none; }}

/* --- General --- */
.section-gap {{ height: 40px; width: 100%; clear: both; }}
.content-block {{
    background-color: rgba(255, 255, 255, 0.95);
    border-radius: 15px; padding: 20px; border: 1px solid #ddd;
    box-shadow: 0 4px 10px rgba(0,0,0,0.05); height: 100%;
}}
.table-scroll {{ max-height: 900px; overflow-y: auto; }}
table.custom-table {{ width: 100%; border-collapse: collapse; font-size: 16px; }}
table.custom-table th {{ position: sticky; top: 0; background-color: #f9f9f9; color: {PRIMARY_COLOR}; border-bottom: 2px solid {PRIMARY_COLOR}; padding: 15px; text-align: left; font-weight: bold; z-index: 1; white-space: nowrap !important; }}
table.custom-table td {{ padding: 12px 15px; border-bottom: 1px solid #eee; color: #333; vertical-align: middle; white-space: nowrap !important; }}
table.custom-table tr:hover {{ background-color: #fff5f5; }}
table.custom-table td:nth-child(2) {{ font-weight: bold; }}
.card-internal-header {{
    color: {PRIMARY_COLOR}; font-size: 28px; font-weight: 700;
    margin-bottom: 20px; text-align: center;
    text-shadow: 2px 0 0 white, -2px 0 0 white, 0 2px 0 white, 0 -2px 0 white, 1px 1px 0 white, -1px -1px 0 white;
}}
.footer {{ margin-top: 60px; text-align: center; color: #333; font-size: 14px; background-color: rgba(255,255,255,0.85); padding: 20px; border-radius: 15px; }}
</style>
"""
st.markdown(css_styles, unsafe_allow_html=True)

# --- 6. 数据处理 ---
HEADERS = {"User-Agent": "Mozilla/5.0"}
if not os.path.exists(DATA_DIR_PATH): os.makedirs(DATA_DIR_PATH)

@st.cache_data(ttl=3600)
def get_kworb_data():
    try:
        r = requests.get("https://kworb.net/spotify/artist/66CXWjxzNUsdJxJ2JdwvnR_songs.html", headers=HEADERS, timeout=15)
        r.encoding = 'utf-8'
        dfs = pd.read_html(r.text)
        for table in dfs:
            if 'Song Title' in table.columns: return table
    except: pass
    return None

def process_data_with_history():
    raw_df = get_kworb_data()
    if raw_df is None: return None

    today_df = raw_df.rename(columns={'Song Title': 'Song'}).copy()
    today_df['Song'] = today_df['Song'].apply(fix_encoding)
    today_df['Streams_Num'] = today_df['Streams'].apply(clean_number)
    today_df['Daily_Raw'] = today_df['Daily'].apply(clean_number)
    today_df = today_df.groupby('Song', as_index=False).agg({'Streams_Num': 'max', 'Daily_Raw': 'max'})

    today_str = datetime.now().strftime("%Y-%m-%d")
    today_file = os.path.join(DATA_DIR_PATH, f"{today_str}.csv")
    today_df.to_csv(today_file, index=False)

    all_files = sorted(glob.glob(os.path.join(DATA_DIR_PATH, "*.csv")))
    history_files = [f for f in all_files if os.path.basename(f) != f"{today_str}.csv"]
    prev_file = history_files[-1] if len(history_files) >= 1 else None
    
    merged = today_df.copy()
    merged['Daily_Num'] = merged['Daily_Raw'] 
    merged['Daily_Prev_Day'] = 0 
    merged['Streams_Num_Prev'] = 0 
    merged['Daily_Percent_Change'] = 0.0

    if prev_file:
        try:
            prev_df = pd.read_csv(prev_file)
            prev_df['Song'] = prev_df['Song'].apply(fix_encoding)
            
            if 'Daily_Raw' in prev_df.columns:
                daily_prev_map = prev_df.set_index('Song')['Daily_Raw']
                merged['Daily_Prev_Day'] = merged['Song'].map(daily_prev_map).fillna(0)
            
            prev_stream_map = prev_df.set_index('Song')['Streams_Num']
            merged['Streams_Num_Prev'] = merged['Song'].map(prev_stream_map).fillna(0)
            
            merged['Daily_Calc'] = merged['Streams_Num'] - merged['Streams_Num_Prev']
            
            is_new = merged['Streams_Num_Prev'] == 0
            merged['Daily_Num'] = merged['Daily_Calc']
            merged.loc[is_new, 'Daily_Num'] = merged.loc[is_new, 'Daily_Raw']
            
            mask_fallback = (merged['Daily_Num'] <= 0) & (merged['Daily_Raw'] > 0)
            merged.loc[mask_fallback, 'Daily_Num'] = merged.loc[mask_fallback, 'Daily_Raw']
            
            merged['Daily_Diff'] = merged['Daily_Num'] - merged['Daily_Prev_Day']
            
            valid_prev_daily = merged['Daily_Prev_Day'] > 0
            merged.loc[valid_prev_daily, 'Daily_Percent_Change'] = (
                merged['Daily_Diff'] / merged['Daily_Prev_Day'] * 100
            )

        except Exception as e:
            st.error(f"Error reading history: {e}")

    return merged

# --- 7. 分类定义 ---
STANDARD_EDITION_SET = {
    "intro (end of the world)", "bye", "don't wanna break up again", "saturn returns interlude",
    "eternal sunshine", "supernatural", "true story", "the boy is mine", "yes, and?",
    "we can't be friends (wait for your love)", "i wish i hated you", "imperfect for you",
    "ordinary things (feat. nonna)"
}
STREAMING_DELUXE_ADDITIONS = {
    "intro (end of the world) - extended", "twilight zone", "warm", "dandelion", "past life", "hampstead"
}
STREAMING_DELUXE_SET = STANDARD_EDITION_SET.union(STREAMING_DELUXE_ADDITIONS)

REMIXES_ON_CD = {
    "yes, and? (with mariah carey) - remix", "supernatural (with troye sivan) - remix",
    "the boy is mine (with brandy, monica) - remix"
}
OFFICIAL_DELUXE_CD_SET = STREAMING_DELUXE_SET.union(REMIXES_ON_CD)

# 移除了 emoji
def get_track_category(song_name):
    s = song_name.lower().strip()
    if s in OFFICIAL_DELUXE_CD_SET: return "Deluxe CD"
    if "live" in s or "snl" in s: return "Live"
    if "a cappella" in s: return "A Cappella"
    if "instrumental" in s: return "Instrumental"
    return "Other"

def filter_and_categorize(df):
    df_filtered = df[df['Song'].apply(is_relevant_track)].copy()
    df_filtered['Category'] = df_filtered['Song'].apply(get_track_category)
    df_filtered = df_filtered.drop_duplicates(subset=['Song'])

    cat_order = {"Deluxe CD": 0, "Live": 1, "Other": 2, "A Cappella": 3, "Instrumental": 4}
    df_filtered['Cat_Rank'] = df_filtered['Category'].map(cat_order).fillna(99)
    df_filtered = df_filtered.sort_values(['Cat_Rank', 'Daily_Num'], ascending=[True, False]).reset_index(drop=True)
    return df_filtered

def calculate_set_stats_with_diff(df, target_set):
    subset = df[df['Song'].str.lower().isin(target_set)]
    streams = subset['Streams_Num'].sum()
    daily = subset['Daily_Num'].sum()
    daily_diff = subset['Daily_Diff'].sum()
    count = len(subset)
    return streams, daily, daily_diff, count

# --- 8. 历史趋势数据生成 ---
def get_historical_charts_data():
    all_files = sorted(glob.glob(os.path.join(DATA_DIR_PATH, "*.csv")))
    records_total = []
    records_daily = []
    song_history_list = []

    for f in all_files:
        date_str = os.path.basename(f).replace(".csv", "")
        try:
            df = pd.read_csv(f)
            df['Song'] = df['Song'].apply(fix_encoding)
            df['Song_Lower'] = df['Song'].str.lower().str.strip()
            if 'Daily_Raw' in df.columns:
                 df['Daily_Raw'] = df['Daily_Raw'].fillna(0).astype(int)
            else:
                 df['Daily_Raw'] = 0
            if 'Streams_Num' not in df.columns:
                 df['Streams_Num'] = df['Streams'].apply(clean_number)

            df['is_valid'] = df['Song'].apply(is_relevant_track)
            valid_tracks = df[df['is_valid']]
            
            for _, row in valid_tracks.iterrows():
                song_history_list.append({
                    "Date": date_str,
                    "Song": row['Song'],
                    "Streams": row['Streams_Num'],
                    "Daily": row['Daily_Raw']
                })

            univ = valid_tracks
            dlx = df[df['Song_Lower'].isin(OFFICIAL_DELUXE_CD_SET)]
            std = df[df['Song_Lower'].isin(STANDARD_EDITION_SET)]
            stm = df[df['Song_Lower'].isin(STREAMING_DELUXE_SET)]

            records_total.append({
                "Date": date_str,
                "Official Deluxe CD": dlx['Streams_Num'].sum(),
                "Standard Edition": std['Streams_Num'].sum(),
                "Standard Deluxe Edition": stm['Streams_Num'].sum(), 
                "Full Universe": univ['Streams_Num'].sum()
            })

            records_daily.append({
                "Date": date_str,
                "Official Deluxe CD": dlx['Daily_Raw'].sum(),
                "Standard Edition": std['Daily_Raw'].sum(),
                "Standard Deluxe Edition": stm['Daily_Raw'].sum(),
                "Full Universe": univ['Daily_Raw'].sum()
            })

        except: pass

    if not records_total: return None, None, None, None
    
    hist_total_df = pd.DataFrame(records_total)
    hist_daily_df = pd.DataFrame(records_daily)
    hist_songs_df = pd.DataFrame(song_history_list)
    
    # 7-Day Split Calculation
    seven_day_stats = {}
    cols = ["Official Deluxe CD", "Standard Edition", "Standard Deluxe Edition", "Full Universe"]
    
    if len(hist_total_df) >= 7:
        row_now = hist_total_df.iloc[-1]
        row_7d_ago = hist_total_df.iloc[-7]
        for c in cols:
            seven_day_stats[c] = row_now[c] - row_7d_ago[c]
    elif len(hist_total_df) > 0:
        row_now = hist_total_df.iloc[-1]
        row_first = hist_total_df.iloc[0]
        for c in cols:
            seven_day_stats[c] = row_now[c] - row_first[c]
    else:
        for c in cols: seven_day_stats[c] = 0
        
    return hist_total_df, hist_daily_df, hist_songs_df, seven_day_stats

# --- 9. 高级绘图函数 (Altair) ---
def make_macro_chart(data, title, is_total=False):
    melted = data.melt('Date', var_name='Version', value_name='Streams')
    # 更新了 domain 以匹配无 emoji 的名称
    domain_color = ['Official Deluxe CD', 'Standard Edition', 'Standard Deluxe Edition', 'Full Universe']
    range_color = [PRIMARY_COLOR, SECONDARY_COLOR, POSITIVE_COLOR, '#000000']

    y_scale = alt.Scale(zero=False, padding=0, nice=False)
    y_axis = alt.Axis(title=None, format='.4s', labelExpr="replace(datum.label, 'G', 'B')")

    if is_total:
        y_scale = alt.Scale(zero=False, nice=False, padding=0.02)
    
    chart = alt.Chart(melted).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X('Date:T', axis=alt.Axis(format='%m-%d', title=None)),
        y=alt.Y('Streams:Q', scale=y_scale, axis=y_axis),
        color=alt.Color('Version:N', scale=alt.Scale(domain=domain_color, range=range_color), legend=alt.Legend(title=None, orient='top')),
        tooltip=[alt.Tooltip('Date:T', format='%Y-%m-%d'), alt.Tooltip('Version:N'), alt.Tooltip('Streams:Q', format=',')]
    ).properties(height=350, title=title).interactive()

    return chart

def make_single_song_chart(data, song_name):
    base = alt.Chart(data).encode(x=alt.X('Date:T', axis=alt.Axis(format='%m-%d', title=None)))
    min_t = data['Streams'].min()
    max_t = data['Streams'].max()
    scale_total = alt.Scale(zero=False, nice=False, padding=0.05)
    axis_total = alt.Axis(title='Total Streams', titleColor=PRIMARY_COLOR, labelExpr="replace(format(datum.value, '.2s'), 'G', 'B')")
    
    line_total = base.mark_line(color=PRIMARY_COLOR, strokeWidth=3).encode(
        y=alt.Y('Streams:Q', scale=scale_total, axis=axis_total),
        tooltip=[alt.Tooltip('Date:T'), alt.Tooltip('Streams:Q', format=',', title='Total')]
    )
    
    scale_daily = alt.Scale(zero=False, nice=False, padding=0.05)
    
    line_daily = base.mark_line(color=POSITIVE_COLOR, strokeWidth=2, strokeDash=[5,5]).encode(
        y=alt.Y('Daily:Q', scale=scale_daily, axis=alt.Axis(title='Daily Increase', titleColor=POSITIVE_COLOR, format=',.0f')),
        tooltip=[alt.Tooltip('Date:T'), alt.Tooltip('Daily:Q', format=',', title='Daily')]
    )
    
    chart = alt.layer(line_total, line_daily).resolve_scale(y='independent').properties(height=350, title=f"Trend: {song_name}").interactive()
    return chart

# --- 10. 主程序 UI ---
with st.spinner("Processing Data..."):
    full_df = process_data_with_history()
    hist_total, hist_daily, hist_songs, seven_day_stats = get_historical_charts_data()

if full_df is not None:
    final_df = filter_and_categorize(full_df)
    
    daily_active = final_df[final_df['Daily_Prev_Day'] > 0].copy()
    
    dlx_s, dlx_d, dlx_diff, dlx_c = calculate_set_stats_with_diff(final_df, OFFICIAL_DELUXE_CD_SET)
    tot_s = final_df['Streams_Num'].sum()
    tot_d = final_df['Daily_Num'].sum()
    tot_diff = final_df['Daily_Diff'].sum()
    tot_c = len(final_df)
    std_s, std_d, std_diff, std_c = calculate_set_stats_with_diff(final_df, STANDARD_EDITION_SET)
    stm_s, stm_d, stm_diff, stm_c = calculate_set_stats_with_diff(final_df, STREAMING_DELUXE_SET)
    
    # 图像资源
    img_hero_L = get_img_base64("ETERNALSUNSHINE.webp")
    img_hero_R = get_img_base64("ETERNALSUNSHINEDELUXE.png")
    img_sub_std = get_img_base64("d6718530158d6e809732743ecfd37adf_1000x.webp") 
    img_sub_dlx = get_img_base64("lsjglsdD2C9_11.webp")

    def get_diff_html(diff_val, current_daily):
        yesterday_daily = current_daily - diff_val
        pct_str = ""
        if yesterday_daily > 0:
            pct = (diff_val / yesterday_daily) * 100
            pct_str = f"({pct:+.1f}%)"
        elif yesterday_daily == 0 and diff_val != 0: pct_str = "(N/A)"
        
        # 移除了 emoji，仅保留文本符号
        if diff_val > 0: return f'<span class="comp-badge comp-up">▲ {diff_val:,.0f} <span style="font-size:0.8em">{pct_str}</span></span>'
        if diff_val < 0: return f'<span class="comp-badge comp-down">▼ {abs(diff_val):,.0f} <span style="font-size:0.8em">{pct_str}</span></span>'
        return '<span class="comp-badge" style="color:#999">-</span>'

    diff_html_dlx = get_diff_html(dlx_diff, dlx_d)
    diff_html_tot = get_diff_html(tot_diff, tot_d)

    # --- Hero Card ---
    # 添加了 Timestamp
    current_time_str = datetime.now().strftime("%B %d, %Y | %H:%M")
    st.markdown(f'''<div class="hero-card">
<div class="hero-title">Eternal Sunshine Tracker</div>
<div class="hero-timestamp">{current_time_str}</div>
<div class="hero-flex-container">
<div class="hero-side">
<img src="{img_hero_L}" class="hero-img">
<div class="hero-data">
<div class="hero-sub-title">Official Deluxe CD</div>
<div class="hero-label">Total Streams</div>
<div class="hero-val-big">{dlx_s:,.0f}</div>
<div class="hero-label">Daily Increase</div>
<div class="flex-metric-row">
<div class="hero-val-daily">+{dlx_d:,.0f}</div>
<div>{diff_html_dlx}</div>
</div>
<div class="sub-metric">Tracks: {dlx_c} / 22</div>
</div>
</div>
<div class="hero-divider"></div>
<div class="hero-side">
<div class="hero-data">
<div class="hero-sub-title">Full Universe (All Versions)</div>
<div class="hero-label">Total Streams</div>
<div class="hero-val-big">{tot_s:,.0f}</div>
<div class="hero-label">Daily Increase</div>
<div class="flex-metric-row">
<div class="hero-val-daily">+{tot_d:,.0f}</div>
<div>{diff_html_tot}</div>
</div>
<div class="sub-metric">Total Tracks: {tot_c}</div>
</div>
<img src="{img_hero_R}" class="hero-img">
</div>
</div>
</div>''', unsafe_allow_html=True)

    # --- Sub Cards ---
    c1, c2 = st.columns(2)
    with c1:
        diff_html_std = get_diff_html(std_diff, std_d)
        st.markdown(f'''<div class="sub-card-flex">
<img src="{img_sub_std}" class="sub-card-img">
<div class="sub-card-data">
<div class="metric-title">Standard Edition</div>
<div class="metric-label">Total Streams</div>
<div class="metric-value-small">{std_s:,.0f}</div>
<div class="metric-label" style="margin-top:5px;">Daily</div>
<div class="flex-metric-row">
<div class="metric-value-small" style="font-size: 20px; color: #2E8B57;">+{std_d:,.0f}</div>
<div>{diff_html_std}</div>
</div>
<div class="sub-metric">Tracks: {std_c} / 13</div>
</div>
</div>''', unsafe_allow_html=True)
    with c2:
        diff_html_stm = get_diff_html(stm_diff, stm_d)
        st.markdown(f'''<div class="sub-card-flex">
<div class="sub-card-data">
<div class="metric-title">Standard Deluxe Edition</div>
<div class="metric-label">Total Streams</div>
<div class="metric-value-small">{stm_s:,.0f}</div>
<div class="metric-label" style="margin-top:5px;">Daily</div>
<div class="flex-metric-row">
<div class="metric-value-small" style="font-size: 20px; color: #2E8B57;">+{stm_d:,.0f}</div>
<div>{diff_html_stm}</div>
</div>
<div class="sub-metric">Tracks: {stm_c} / 19</div>
</div>
<img src="{img_sub_dlx}" class="sub-card-img">
</div>''', unsafe_allow_html=True)

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    # --- Highlight Strip (No Emojis) ---
    gain_html = ""
    if not daily_active.empty:
        top_3_gain = daily_active.nlargest(3, 'Daily_Percent_Change')
        for idx, row in top_3_gain.iterrows():
            song_name = row['Song']
            daily_inc = row['Daily_Num']
            gain_html += f'<div class="mover-row"><span class="mover-song-name">{song_name}</span><span style="white-space:nowrap"><span style="color:#666; margin-right:5px;">+{daily_inc:,.0f}</span><span class="gainer-pct">(+{row["Daily_Percent_Change"]:.1f}%)</span></span></div>'
    else: gain_html = "<div class='mover-row'>No Data</div>"

    fall_html = ""
    if not daily_active.empty:
        top_3_fall = daily_active.nsmallest(3, 'Daily_Percent_Change')
        for idx, row in top_3_fall.iterrows():
            song_name = row['Song']
            val = row['Daily_Percent_Change']
            daily_inc = row['Daily_Num']
            val_str = f"{daily_inc:,.0f}"
            if daily_inc > 0: val_str = f"+{val_str}"
            color_cls = "faller-pct" if val < 0 else "gainer-pct"
            sign = "+" if val > 0 else ""
            fall_html += f'<div class="mover-row"><span class="mover-song-name">{song_name}</span><span style="white-space:nowrap"><span style="color:#666; margin-right:5px;">{val_str}</span><span class="{color_cls}">({sign}{val:.1f}%)</span></span></div>'
    else: fall_html = "<div class='mover-row'>No Data</div>"

    if seven_day_stats:
        s7_uni = seven_day_stats.get("Full Universe", 0)
        s7_dlx = seven_day_stats.get("Official Deluxe CD", 0)
        s7_std = seven_day_stats.get("Standard Edition", 0)
        s7_stm = seven_day_stats.get("Standard Deluxe Edition", 0)
        
        stats_html = f'''
<div class="stat-box"><div class="stat-label">Full Universe</div><div class="stat-val">+{s7_uni:,.0f}</div></div>
<div class="stat-box"><div class="stat-label">Official Deluxe</div><div class="stat-val">+{s7_dlx:,.0f}</div></div>
<div class="stat-box"><div class="stat-label">Standard Ed.</div><div class="stat-val">+{s7_std:,.0f}</div></div>
<div class="stat-box"><div class="stat-label">Std. Deluxe</div><div class="stat-val">+{s7_stm:,.0f}</div></div>
'''
    else: stats_html = "<div>Not enough history</div>"

    # 移除了标题中的 emoji
    st.markdown(f'''<div class="highlight-strip">
<div class="highlight-left">
<div style="display:flex; gap:30px; flex-wrap:wrap;">
<div class="mover-col">
<div class="hl-header">Top 3 Gainers</div>
{gain_html}
</div>
<div style="width:1px; background:#eee;"></div>
<div class="mover-col">
<div class="hl-header">Top 3 Fallers</div>
{fall_html}
</div>
</div>
</div>
<div class="highlight-right">
<div class="hl-header">Past 7 Days Increase</div>
<div class="stats-grid">
{stats_html}
</div>
</div>
</div>''', unsafe_allow_html=True)

    # --- Milestone Tracker (Replaced Tier List) ---
    # 逻辑: 如果现在是 65亿，目标是 70亿。如果已经 71亿，目标是 80亿。
    # 基础目标 70亿
    target_billion = 7
    while tot_s >= target_billion * 1_000_000_000:
        target_billion += 1
    
    target_streams = target_billion * 1_000_000_000
    remaining_streams = target_streams - tot_s
    
    # 预测日期
    seven_day_uni_gain = seven_day_stats.get("Full Universe", 0)
    avg_daily_gain = seven_day_uni_gain / 7 if seven_day_uni_gain > 0 else 0
    
    if avg_daily_gain > 0:
        days_to_go = remaining_streams / avg_daily_gain
        estimated_date = datetime.now() + timedelta(days=days_to_go)
        date_display = estimated_date.strftime("%B %d, %Y")
    else:
        date_display = "Indefinite (Need more data)"

    st.markdown(f'''<div class="content-block" style="margin-bottom: 20px;">
<div class="milestone-box">
<div class="milestone-title">Road to {target_billion} Billion Streams</div>
<div class="milestone-data">
    Remaining: <strong>{remaining_streams:,.0f}</strong>
    <span style="margin: 0 10px; color: #ccc;">|</span>
    Estimated Completion: <strong>{date_display}</strong>
</div>
<a href="https://open.spotify.com/album/6cbwstHlsAIIWurIIXXBPd，写上" target="_blank" class="spotify-btn">KEEP STREAMING!!</a>
</div>
</div>''', unsafe_allow_html=True)


    # --- List ---
    if tot_d > 0:
        final_df['Share'] = (final_df['Daily_Num'] / tot_d * 100).round(2).astype(str) + '%'
    else: final_df['Share'] = "0%"

    display_df = final_df[['Song', 'Category', 'Daily_Num', 'Daily_Diff', 'Daily_Prev_Day', 'Streams_Num', 'Share']].copy()
    display_df.insert(0, '#', range(1, len(display_df) + 1))

    def format_diff_col_with_pct(row):
        val = row['Daily_Diff']
        prev = row['Daily_Prev_Day']
        pct_str = ""
        if prev > 0: pct_str = f"({(val / prev) * 100:+.1f}%)"
        elif prev == 0 and val != 0: pct_str = "(N/A)"
        
        # 移除了 emoji，仅保留文本符号
        if val > 0: return f"▲ {val:,.0f} {pct_str}"
        if val < 0: return f"▼ {abs(val):,.0f} {pct_str}"
        return "-"

    display_df['Daily_Num'] = display_df['Daily_Num'].apply(lambda x: f"+{x:,}")
    display_df['Vs Yesterday'] = display_df.apply(format_diff_col_with_pct, axis=1)
    display_df['Streams_Num'] = display_df['Streams_Num'].apply(lambda x: f"{x:,}")
    display_df = display_df[['#', 'Song', 'Category', 'Daily_Num', 'Vs Yesterday', 'Streams_Num', 'Share']]

    table_html = display_df.to_html(classes='custom-table', index=False, escape=True)
    table_html = table_html.replace("▲", f"<span style='color:{POSITIVE_COLOR}; font-weight:bold'>▲").replace("▼", f"<span style='color:{NEGATIVE_COLOR}; font-weight:bold'>▼")
    
    st.markdown(f'''<div class="content-block"><div class="card-internal-header">Detailed Track List</div><div class="table-scroll">{table_html}</div></div>''', unsafe_allow_html=True)

    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    # --- Charts ---
    if hist_total is not None and not hist_total.empty:
        st.markdown(f'''<div class="content-block" style="padding-bottom: 0px; border-bottom: none; border-bottom-left-radius: 0; border-bottom-right-radius: 0;">
<div class="card-internal-header">Historical Trends</div>
</div>''', unsafe_allow_html=True)
        
        with st.container():
             st.markdown("""<style>
div[data-testid="stVerticalBlock"] > div:has(div[class*="content-block"]) + div {
    background-color: rgba(255, 255, 255, 0.95);
    border: 1px solid #ddd; border-top: none;
    border-bottom-left-radius: 15px; border-bottom-right-radius: 15px;
    padding: 30px; margin-top: -30px; box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
</style>""", unsafe_allow_html=True)
             
             col_L, col_R = st.columns([3, 2], gap="large")
             
             with col_L:
                 st.markdown("##### Album Versions Overview") # Removed Emoji
                 tab1, tab2 = st.tabs(["Total Streams", "Daily Increase"])
                 with tab1:
                    c_total = make_macro_chart(hist_total, "", is_total=True)
                    st.altair_chart(c_total, use_container_width=True)
                 with tab2:
                    c_daily = make_macro_chart(hist_daily, "", is_total=False)
                    st.altair_chart(c_daily, use_container_width=True)
            
             with col_R:
                 st.markdown("##### Single Track Analyzer") # Removed Emoji
                 if hist_songs is not None and not hist_songs.empty:
                     song_list = sorted(hist_songs['Song'].unique())
                     default_idx = 0
                     for i, s in enumerate(song_list):
                         if "we can't be friends" in s.lower(): 
                             default_idx = i
                             break
                     selected_song = st.selectbox("Select a song to track:", song_list, index=default_idx)
                     song_data = hist_songs[hist_songs['Song'] == selected_song].copy()
                     if not song_data.empty:
                         c_song = make_single_song_chart(song_data, selected_song)
                         st.altair_chart(c_song, use_container_width=True)
                 else:
                     st.write("No song data available.")
    else:
        st.info("Not enough historical data to display charts yet.")

    # 更新了署名
    st.markdown('<div class="footer">唐可可的小炸弹 with gemini/ ig:sampoohh/ email: sheepYeoh@outlook.com</div>', unsafe_allow_html=True)
else:

    st.error("Connection failed. Unable to reach Kworb.")
