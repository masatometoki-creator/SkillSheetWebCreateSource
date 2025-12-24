import streamlit as st

# --- ここでPandasを使えるようにする ---
try:
    import pandas as pd
except ImportError:
    st.error("Pandasがインストールされていません。'pip install pandas'でインストールしてください。")
    import sys
    sys.exit(1)
# -------------------------------------

import sqlite3
import os

# データベースパス
DB_PATH = os.path.join(os.path.dirname(__file__), "skillsheet_data.db")

# --- カスタムCSS: 青系で統一（ボタン以外） ---
st.markdown(
    """
    <style>
    /* 入力フォーム背景・枠線・フォーカス色を青系で強調 */
    .stNumberInput > div > input, .stTextInput > div > input, .stSelectbox > div > div {
        background-color: #e3f2fd !important;
        border: 2px solid #1976d2 !important;
        border-radius: 0.5rem !important;
        color: #0d223a !important;
        font-weight: bold !important;
        box-shadow: 0 2px 8px rgba(25, 118, 210, 0.08);
    }
    .stNumberInput > div > input:focus, .stTextInput > div > input:focus, .stSelectbox > div > div:focus {
        border: 2.5px solid #0d47a1 !important;
        background-color: #bbdefb !important;
        outline: none !important;
    }
    /* ボタンは赤系で目立たせる（元のまま） */
    div.stButton > button {
        background-color: #e53935 !important;
        color: white !important;
        border: none !important;
        border-radius: 0.7rem !important;
        font-weight: bold !important;
        transition: background 0.2s;
        box-shadow: 0 2px 8px rgba(229,57,53,0.10);
        letter-spacing: 0.05em;
    }
    div.stButton > button:hover {
        background-color: #b71c1c !important;
        color: white !important;
        transform: scale(1.04);
    }
    /* セレクトボックスのドロップダウンも青系で強調 */
    .stSelectbox [data-baseweb="select"] {
        background-color: #e3f2fd !important;
        border-radius: 0.5rem !important;
    }
    /* カード風の枠（青系グラデーション） */
    .card-section {
        background: linear-gradient(120deg, #e3f2fd 80%, #bbdefb 100%);
        border-radius: 1.2rem;
        box-shadow: 0 4px 16px rgba(25, 118, 210, 0.10);
        padding: 1.5rem 1.5rem 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        border: 1.5px solid #1976d2;
        animation: fadeIn 0.7s;
    }
    .card-title {
        color: #1976d2;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 0.7rem;
        letter-spacing: 0.04em;
    }
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px);}
        to { opacity: 1; transform: translateY(0);}
    }
    /* データフレームのヘッダー色（青系） */
    .stDataFrame thead tr th {
        background-color: #bbdefb !important;
        color: #0d47a1 !important;
        font-weight: bold !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

st.markdown(
    "<h1 style='color:#1976d2; font-weight:bold; letter-spacing:0.08em; margin-bottom:0.2em;'>📊 データ参照・管理</h1>",
    unsafe_allow_html=True
)

# --- ホームに戻るボタン ---
nav_cols = st.columns([1, 8])
with nav_cols[0]:
    if st.button("🏠 ホームへ戻る", key="go_home_from_dataview"):
        # セッション状態をクリア
        if 'selected_id' in st.session_state:
            del st.session_state.selected_id
        if 'show_data' in st.session_state:
            del st.session_state.show_data
        st.session_state.current_page = "🏠 ホーム"
        st.rerun()



# データベースからデータを取得して表示する関数
def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    try:
        conn.execute(f"SELECT 1 FROM {table} LIMIT 1")
        return True
    except Exception:
        return False

def display_saved_data():
    """保存されたデータを表示（新スキーマ優先、なければ旧スキーマ）"""
    conn = sqlite3.connect(DB_PATH)
    try:
        use_new = _table_exists(conn, "user_info")
        # ログインユーザーIDを取得
        login_user_id = st.session_state.get('user_id')

        if use_new:
            # ログインユーザーが作成したスキルシートのみ表示
            if login_user_id:
                users_df = pd.read_sql_query(
                    """
                    SELECT id, name, name_kana, gender, birth_date, final_education, created_at
                    FROM user_info
                    WHERE login_user_id = ?
                    ORDER BY created_at DESC
                    """,
                    conn,
                    params=[login_user_id]
                )
            else:
                users_df = pd.DataFrame()
        else:
            # 旧スキーマの場合は全件表示（後方互換性のため）
            users_df = pd.read_sql_query(
                """
                SELECT id, name, name_kana, gender, birth_date, final_education, created_at
                FROM basic_info
                ORDER BY created_at DESC
                """,
                conn,
            )

        if users_df.empty:
            st.info("まだデータが保存されていません。")
            return

        with st.container():
            st.markdown(
                "<div class='card-section'><div class='card-title'>登録一覧</div>",
                unsafe_allow_html=True
            )
            st.dataframe(users_df, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # セレクトボックスを枠で囲むためにst.selectboxをst.containerでラップ
        with st.container():
            st.markdown(
                "<div class='card-section'><div class='card-title'>詳細データ選択</div>",
                unsafe_allow_html=True
            )
            
            # セッション状態から現在の選択を取得、またはデフォルト値を設定
            if 'selected_id' not in st.session_state:
                st.session_state.selected_id = users_df["id"].tolist()[0] if not users_df.empty else None
            
            selected_id = st.selectbox(
                "詳細を表示するデータを選択してください:",
                options=users_df["id"].tolist(),
                index=users_df["id"].tolist().index(st.session_state.selected_id) if st.session_state.selected_id in users_df["id"].tolist() else 0,
                format_func=lambda x: f"ID: {x} - {users_df[users_df['id']==x]['name'].iloc[0]} ({users_df[users_df['id']==x]['created_at'].iloc[0]})",
                key="data_selector"
            )
            
            # 選択されたIDをセッション状態に保存（変更時のみ）
            if selected_id != st.session_state.selected_id:
                st.session_state.selected_id = selected_id
            
            st.markdown("</div>", unsafe_allow_html=True)

        if not selected_id:
            return

        # 詳細情報を2カラムでカード表示
        st.markdown(
            "<div class='card-section'><div class='card-title'>詳細情報</div>",
            unsafe_allow_html=True
        )
        col1, col2 = st.columns([1, 1])

        if use_new:
            # ログインユーザーが作成したスキルシートのみ表示
            login_user_id = st.session_state.get('user_id')
            if login_user_id:
                detail = pd.read_sql_query(
                    "SELECT * FROM user_info WHERE id = ? AND login_user_id = ?",
                    conn,
                    params=[selected_id, login_user_id],
                )
            else:
                detail = pd.DataFrame()
            if not detail.empty:
                with col1:
                    st.markdown("**基本情報**")
                    row = detail.iloc[0]
                    if pd.notna(row.get('name')):
                        st.write(f"**氏名:** {row['name']}")
                    if pd.notna(row.get('name_kana')):
                        st.write(f"**カナ:** {row['name_kana']}")
                    if pd.notna(row.get('gender')):
                        st.write(f"**性別:** {row['gender']}")
                    if pd.notna(row.get('birth_date')):
                        st.write(f"**生年月日:** {row['birth_date']}")
                    if pd.notna(row.get('final_education')):
                        st.write(f"**最終学歴:** {row['final_education']}")
                    if pd.notna(row.get('nearest_station')):
                        st.write(f"**最寄り駅:** {row['nearest_station']}")
                    if pd.notna(row.get('access_method')):
                        st.write(f"**交通手段:** {row['access_method']}")
                    if pd.notna(row.get('access_time')):
                        st.write(f"**所要時間:** {row['access_time']}分")

                # 資格はuser_info.qualificationsに保持（文字列）
                quals = detail.iloc[0]["qualifications"] if not detail.empty else ""
                if isinstance(quals, str) and quals.strip():
                    with col2:
                        st.markdown("**資格**")
                        st.write(quals)

            if not detail.empty:
                skills = pd.read_sql_query(
                    "SELECT skill_type, skill_name, experience_years FROM skills WHERE user_info_id = ?",
                    conn,
                    params=[selected_id],
                )
            else:
                skills = pd.DataFrame()
            if not skills.empty:
                st.markdown("---")
                st.markdown("**スキル**")
                st.dataframe(skills, use_container_width=True, hide_index=True)

            if not detail.empty:
                projects = pd.read_sql_query(
                    """
                    SELECT period_start, period_end, system_name, role, industry, work_content, phases, headcount,
                           env_langs, env_tools, env_dbs, env_oss
                    FROM projects WHERE user_info_id = ?
                    """,
                    conn,
                    params=[selected_id],
                )
            else:
                projects = pd.DataFrame()
            if not projects.empty:
                st.markdown("---")
                st.markdown("**職務経歴**")
                # phasesカラムを処理して表示用に変換
                PHASE_LABELS = [
                    "環境構築", "要件", "基本", "詳細", "製造", "単体", "結合", "総合", "保守運用", "他"
                ]
                projects_display = projects.copy()
                
                def parse_phases(phases_val):
                    """phasesの値を解析して辞書形式に変換"""
                    if pd.isna(phases_val) or phases_val == '':
                        return {label: False for label in PHASE_LABELS}
                    
                    try:
                        import ast
                        import json
                        # 文字列の場合、JSONまたはPythonリテラルとして解析
                        if isinstance(phases_val, str):
                            # JSON形式を試す
                            try:
                                phases_dict = json.loads(phases_val)
                            except:
                                # Pythonリテラルとして解析
                                try:
                                    phases_dict = ast.literal_eval(phases_val)
                                except:
                                    # リスト形式の場合
                                    if phases_val.startswith('[') and phases_val.endswith(']'):
                                        phases_list = ast.literal_eval(phases_val)
                                        phases_dict = {label: label in phases_list for label in PHASE_LABELS}
                                    else:
                                        return {label: False for label in PHASE_LABELS}
                        else:
                            phases_dict = phases_val
                        
                        # 辞書形式の場合
                        if isinstance(phases_dict, dict):
                            result = {}
                            for label in PHASE_LABELS:
                                # true/falseまたは1/0をチェック
                                val = phases_dict.get(label, False)
                                result[label] = val in [True, 1, 'true', 'True', '1']
                            return result
                        # リスト形式の場合（工程名のリスト）
                        elif isinstance(phases_dict, list):
                            return {label: label in phases_dict for label in PHASE_LABELS}
                        else:
                            return {label: False for label in PHASE_LABELS}
                    except Exception as e:
                        return {label: False for label in PHASE_LABELS}
                
                # phasesカラムを解析して各工程の列に展開
                if 'phases' in projects_display.columns:
                    phases_data = projects_display['phases'].apply(parse_phases)
                    # 各工程の列を追加（true→●、false→空白）
                    for label in PHASE_LABELS:
                        projects_display[label] = phases_data.apply(lambda x: '●' if x.get(label, False) else '')
                    # 元のphasesカラムを削除
                    projects_display = projects_display.drop(columns=['phases'])
                
                st.dataframe(projects_display, use_container_width=True, hide_index=True)
        else:
            # 旧スキーマ
            basic_detail = pd.read_sql_query(
                "SELECT * FROM basic_info WHERE id = ?",
                conn,
                params=[selected_id],
            )
            if not basic_detail.empty:
                with col1:
                    st.markdown("**基本情報**")
                    row = basic_detail.iloc[0]
                    if pd.notna(row.get('name')):
                        st.write(f"**氏名:** {row['name']}")
                    if pd.notna(row.get('name_kana')):
                        st.write(f"**カナ:** {row['name_kana']}")
                    if pd.notna(row.get('gender')):
                        st.write(f"**性別:** {row['gender']}")
                    if pd.notna(row.get('birth_date')):
                        st.write(f"**生年月日:** {row['birth_date']}")
                    if pd.notna(row.get('final_education')):
                        st.write(f"**最終学歴:** {row['final_education']}")
                    if pd.notna(row.get('nearest_station')):
                        st.write(f"**最寄り駅:** {row['nearest_station']}")
                    if pd.notna(row.get('access_method')):
                        st.write(f"**交通手段:** {row['access_method']}")
                    if pd.notna(row.get('access_time')):
                        st.write(f"**所要時間:** {row['access_time']}分")

            qualifications = pd.read_sql_query(
                "SELECT qualification FROM qualifications WHERE basic_info_id = ?",
                conn,
                params=[selected_id],
            )
            if not qualifications.empty:
                with col2:
                    st.markdown("**資格**")
                    st.dataframe(qualifications, use_container_width=True, hide_index=True)

            languages = pd.read_sql_query(
                "SELECT language, experience_years FROM languages WHERE basic_info_id = ?",
                conn,
                params=[selected_id],
            )
            if not languages.empty:
                st.markdown("---")
                st.markdown("**言語**")
                st.dataframe(languages, use_container_width=True, hide_index=True)

            tools = pd.read_sql_query(
                "SELECT tool, experience_years FROM tools WHERE basic_info_id = ?",
                conn,
                params=[selected_id],
            )
            if not tools.empty:
                st.markdown("---")
                st.markdown("**ツール/フレームワーク/ライブラリ**")
                st.dataframe(tools, use_container_width=True, hide_index=True)

            databases = pd.read_sql_query(
                "SELECT database, experience_years FROM databases WHERE basic_info_id = ?",
                conn,
                params=[selected_id],
            )
            if not databases.empty:
                st.markdown("---")
                st.markdown("**データベース**")
                st.dataframe(databases, use_container_width=True, hide_index=True)

            machines = pd.read_sql_query(
                "SELECT machine, experience_years FROM machines WHERE basic_info_id = ?",
                conn,
                params=[selected_id],
            )
            if not machines.empty:
                st.markdown("---")
                st.markdown("**マシン/OS**")
                st.dataframe(machines, use_container_width=True, hide_index=True)

            projects = pd.read_sql_query(
                """
                SELECT period_start, period_end, system_name, role, industry, work_content, headcount
                FROM projects WHERE basic_info_id = ?
                """,
                conn,
                params=[selected_id],
            )
            if not projects.empty:
                st.markdown("---")
                st.markdown("**職務経歴**")
                st.dataframe(projects, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
    
    except Exception as e:
        st.error(f"データ取得エラー: {str(e)}")
    finally:
        conn.close()

with st.container():
    st.markdown(
        "<div class='card-section' style='text-align:center;'><div class='card-title'>データ表示</div>",
        unsafe_allow_html=True
    )
    if st.button("保存されたデータを表示", type="primary"):
        # セッション状態を初期化してデータ表示状態に設定
        if 'selected_id' in st.session_state:
            del st.session_state.selected_id
        st.session_state.show_data = True
    st.markdown("</div>", unsafe_allow_html=True)

# データ表示状態の場合、データを表示
if st.session_state.get('show_data', False):
    display_saved_data()
# --- データ削除機能をカードで ---
st.markdown("<div class='card-section'><div class='card-title'>データ管理</div>", unsafe_allow_html=True)
with st.container():
    delete_id = st.number_input(
        "削除するデータのIDを入力:",
        min_value=1,
        step=1,
        key="delete_id_input",
        help="削除したいデータのIDを入力してください"
    )
    if st.button("データを削除", type="secondary"):
        if delete_id:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            try:
                # 新スキーマ優先で削除。なければ旧スキーマを削除
                login_user_id = st.session_state.get('user_id')
                if _table_exists(conn, "user_info"):
                    # ログインユーザーが作成したスキルシートのみ削除可能
                    if login_user_id:
                        cursor.execute("SELECT id FROM user_info WHERE id = ? AND login_user_id = ?", (delete_id, login_user_id))
                        if cursor.fetchone():
                            cursor.execute("DELETE FROM skills WHERE user_info_id = ?", (delete_id,))
                            cursor.execute("DELETE FROM projects WHERE user_info_id = ?", (delete_id,))
                            cursor.execute("DELETE FROM user_info WHERE id = ?", (delete_id,))
                            conn.commit()
                            st.success(f"ID {delete_id} のデータを削除しました。")
                        else:
                            st.error("このデータを削除する権限がありません。")
                    else:
                        st.error("ログインが必要です。")
                else:
                    cursor.execute("DELETE FROM qualifications WHERE basic_info_id = ?", (delete_id,))
                    cursor.execute("DELETE FROM languages WHERE basic_info_id = ?", (delete_id,))
                    cursor.execute("DELETE FROM tools WHERE basic_info_id = ?", (delete_id,))
                    cursor.execute("DELETE FROM databases WHERE basic_info_id = ?", (delete_id,))
                    cursor.execute("DELETE FROM machines WHERE basic_info_id = ?", (delete_id,))
                    cursor.execute("DELETE FROM projects WHERE basic_info_id = ?", (delete_id,))
                    cursor.execute("DELETE FROM basic_info WHERE id = ?", (delete_id,))
                    conn.commit()
                    st.success(f"ID {delete_id} のデータを削除しました。")
            except Exception as e:
                st.error(f"削除エラー: {str(e)}")
            finally:
                conn.close()
        else:
            st.warning("削除するデータのIDを入力してください。")
st.markdown("</div>", unsafe_allow_html=True)