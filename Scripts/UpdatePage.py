import streamlit as st
import sqlite3
import pandas as pd
import os
from datetime import datetime, timedelta
import re

# データベースパス
DB_PATH = os.path.join(os.path.dirname(__file__), "skillsheet_data.db")

st.title("📝 スキルシート更新")

# ページ内ナビゲーション
nav_cols = st.columns([1, 1, 8])
with nav_cols[0]:
    if st.button("🏠 ホームへ戻る", key="go_home_from_update"):
        st.session_state.current_page = "🏠 ホーム"
        st.rerun()

st.markdown("---")

# 編集モードの選択
edit_mode = st.radio(
    "編集モードを選択してください:",
    ["基本情報の編集", "案件情報の編集", "スキル情報の編集", "新しい案件情報の追加"],
    key="edit_mode"
)

st.markdown("---")

# データベースからユーザー一覧を取得
def get_user_list():
    """ユーザー一覧を取得"""
    conn = sqlite3.connect(DB_PATH)
    try:
        # 新しいスキーマを優先
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_info'")
        if cursor.fetchone():
            # 新しいスキーマ
            query = """
                SELECT id, name, name_kana, created_at
                FROM user_info
                ORDER BY created_at DESC
            """
        else:
            # 古いスキーマ
            query = """
                SELECT id, name, name_kana, created_at
                FROM basic_info
                ORDER BY created_at DESC
            """
        
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"ユーザー一覧の取得に失敗しました: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

# ユーザー選択
st.subheader("更新するユーザーを選択してください")
user_df = get_user_list()

if user_df.empty:
    st.warning("データベースにユーザー情報がありません。")
else:
    # ユーザー選択用のセレクトボックス
    user_options = []
    for _, row in user_df.iterrows():
        display_name = f"{row['name']} ({row['name_kana']}) - {row['created_at']}"
        user_options.append((display_name, row['id']))
    
    selected_user = st.selectbox(
        "ユーザーを選択:",
        options=[opt[1] for opt in user_options],
        format_func=lambda x: next(opt[0] for opt in user_options if opt[1] == x),
        key="selected_user"
    )
    
    if selected_user:
        # 選択されたユーザーの詳細情報を取得
        def get_user_details(user_id):
            """ユーザーの詳細情報を取得"""
            conn = sqlite3.connect(DB_PATH)
            try:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_info'")
                if cursor.fetchone():
                    # 新しいスキーマ
                    user_query = "SELECT * FROM user_info WHERE id = ?"
                    skills_query = "SELECT * FROM skills WHERE user_info_id = ?"
                    projects_query = "SELECT * FROM projects WHERE user_info_id = ?"
                else:
                    # 古いスキーマ
                    user_query = "SELECT * FROM basic_info WHERE id = ?"
                    skills_query = None
                    projects_query = "SELECT * FROM projects WHERE basic_info_id = ?"
                
                user_data = pd.read_sql_query(user_query, conn, params=(user_id,))
                
                skills_data = pd.DataFrame()
                if skills_query:
                    skills_data = pd.read_sql_query(skills_query, conn, params=(user_id,))
                
                projects_data = pd.read_sql_query(projects_query, conn, params=(user_id,))
                
                return user_data, skills_data, projects_data
            except Exception as e:
                st.error(f"ユーザー詳細の取得に失敗しました: {str(e)}")
                return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            finally:
                conn.close()
        
        user_data, skills_data, projects_data = get_user_details(selected_user)
        
        if not user_data.empty:
            # 基本情報の表示と編集
            if edit_mode == "基本情報の編集":
                st.subheader("基本情報の編集")
                
                with st.form("edit_basic_info_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        name = st.text_input("氏名", value=user_data.iloc[0]['name'], key="edit_name")
                        name_kana = st.text_input("カナ", value=user_data.iloc[0]['name_kana'], key="edit_name_kana")
                        gender = st.selectbox("性別", ["男", "女"], index=0 if user_data.iloc[0]['gender'] == "男" else 1, key="edit_gender")
                        birth_date = st.date_input("生年月日", value=datetime.strptime(user_data.iloc[0]['birth_date'], '%Y-%m-%d').date() if user_data.iloc[0]['birth_date'] else None, key="edit_birth_date")
                        final_education = st.text_input("最終学歴", value=user_data.iloc[0]['final_education'], key="edit_final_education")
                    
                    with col2:
                        transportation = st.text_input("電車", value=user_data.iloc[0]['transportation'], key="edit_transportation")
                        nearest_station = st.text_input("最寄り駅", value=user_data.iloc[0]['nearest_station'], key="edit_nearest_station")
                        access_method = st.selectbox("駅からの交通手段", ["徒歩", "自転車", "バス", "車"], 
                                                   index=["徒歩", "自転車", "バス", "車"].index(user_data.iloc[0]['access_method']) if user_data.iloc[0]['access_method'] in ["徒歩", "自転車", "バス", "車"] else 0, 
                                                   key="edit_access_method")
                        access_time = st.text_input("所要時間(分)", value=user_data.iloc[0]['access_time'], key="edit_access_time")
                        graduation_date = st.text_input("卒業年月", value=user_data.iloc[0]['graduation_date'], key="edit_graduation_date")
                    
                    self_pr = st.text_area("自己PR", value=user_data.iloc[0]['self_pr'], key="edit_self_pr")
                    qualifications = st.text_area("資格", value=user_data.iloc[0]['qualifications'], key="edit_qualifications")
                    
                    submitted = st.form_submit_button("基本情報を更新", type="primary")
                    
                    if submitted:
                        def update_basic_info(user_id, updated_data):
                            """基本情報を更新"""
                            conn = sqlite3.connect(DB_PATH)
                            try:
                                cursor = conn.cursor()
                                
                                # 新しいスキーマかどうか確認
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_info'")
                                use_new_schema = cursor.fetchone() is not None
                                
                                if use_new_schema:
                                    cursor.execute("""
                                        UPDATE user_info SET 
                                        name = ?, name_kana = ?, transportation = ?, nearest_station = ?,
                                        access_method = ?, access_time = ?, gender = ?, birth_date = ?,
                                        final_education = ?, graduation_date = ?, self_pr = ?, qualifications = ?
                                        WHERE id = ?
                                    """, (
                                        updated_data['name'], updated_data['name_kana'], updated_data['transportation'],
                                        updated_data['nearest_station'], updated_data['access_method'], updated_data['access_time'],
                                        updated_data['gender'], updated_data['birth_date'], updated_data['final_education'],
                                        updated_data['graduation_date'], updated_data['self_pr'], updated_data['qualifications'],
                                        user_id
                                    ))
                                else:
                                    cursor.execute("""
                                        UPDATE basic_info SET 
                                        name = ?, name_kana = ?, transportation = ?, nearest_station = ?,
                                        access_method = ?, access_time = ?, gender = ?, birth_date = ?,
                                        final_education = ?, graduation_date = ?, self_pr = ?
                                        WHERE id = ?
                                    """, (
                                        updated_data['name'], updated_data['name_kana'], updated_data['transportation'],
                                        updated_data['nearest_station'], updated_data['access_method'], updated_data['access_time'],
                                        updated_data['gender'], updated_data['birth_date'], updated_data['final_education'],
                                        updated_data['graduation_date'], updated_data['self_pr'], user_id
                                    ))
                                
                                conn.commit()
                                return True
                            except Exception as e:
                                conn.rollback()
                                st.error(f"基本情報の更新に失敗しました: {str(e)}")
                                return False
                            finally:
                                conn.close()
                        
                        # データを準備
                        updated_data = {
                            'name': name,
                            'name_kana': name_kana,
                            'transportation': transportation,
                            'nearest_station': nearest_station,
                            'access_method': access_method,
                            'access_time': access_time,
                            'gender': gender,
                            'birth_date': birth_date.strftime('%Y-%m-%d') if birth_date else None,
                            'final_education': final_education,
                            'graduation_date': graduation_date,
                            'self_pr': self_pr,
                            'qualifications': qualifications
                        }
                        
                        if update_basic_info(selected_user, updated_data):
                            st.success("基本情報を更新しました！")
                            st.rerun()
                        else:
                            st.error("基本情報の更新に失敗しました。")
            else:
                # 基本情報の表示のみ
                st.subheader("基本情報")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**氏名:** {user_data.iloc[0]['name']}")
                    st.write(f"**カナ:** {user_data.iloc[0]['name_kana']}")
                    st.write(f"**性別:** {user_data.iloc[0]['gender']}")
                with col2:
                    st.write(f"**最寄り駅:** {user_data.iloc[0]['nearest_station']}")
                    st.write(f"**交通手段:** {user_data.iloc[0]['access_method']}")
                    st.write(f"**所要時間:** {user_data.iloc[0]['access_time']}分")
            
            st.markdown("---")
            
            # 案件情報の更新フォーム
            st.subheader("案件情報の更新")
            
            if not projects_data.empty:
                st.write("**現在の案件情報:**")
                for idx, project in projects_data.iterrows():
                    with st.expander(f"案件 {idx + 1}: {project.get('system_name', 'N/A')}"):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.write(f"**期間:** {project.get('period_start', 'N/A')} ～ {project.get('period_end', 'N/A')}")
                            st.write(f"**役割:** {project.get('role', 'N/A')}")
                            st.write(f"**業種:** {project.get('industry', 'N/A')}")
                        with col2:
                            st.write(f"**工程:** {project.get('phases', 'N/A')}")
                            st.write(f"**人数:** {project.get('headcount', 'N/A')}")
                            st.write(f"**作業内容:** {project.get('work_content', 'N/A')}")
                        
                        st.write("**環境情報:**")
                        env_cols = st.columns(4)
                        with env_cols[0]:
                            st.write(f"**言語:** {project.get('env_langs', 'N/A')}")
                        with env_cols[1]:
                            st.write(f"**ツール:** {project.get('env_tools', 'N/A')}")
                        with env_cols[2]:
                            st.write(f"**DB:** {project.get('env_dbs', 'N/A')}")
                        with env_cols[3]:
                            st.write(f"**OS/マシン:** {project.get('env_oss', 'N/A')}")
                
                st.markdown("---")
                
                # 新しい案件情報の追加
                st.subheader("新しい案件情報の追加")
                
                with st.form("new_project_form"):
                    col1, col2 = st.columns(2)
                    with col1:
                        period_start = st.date_input("開始日", key="new_period_start")
                        period_end = st.date_input("終了日", key="new_period_end")
                        system_name = st.text_input("システム名・作業内容", key="new_system_name")
                        role = st.selectbox("役割", [
                            "CNSL(コンサルタント)", "PMO(プロジェクトマネジメントオフィス)", 
                            "PM(プロジェクトマネージャー)", "PL(プロジェクトリーダー)",
                            "SL(サブリーダー)", "SE(システムエンジニア)", "PG(プログラマ)", "M（メンバー）"
                        ], key="new_role")
                    with col2:
                        industry = st.selectbox("業種", [
                            "農林業", "鉱業", "建設業", "製造業", "情報通信", "運輸業", 
                            "卸売・小売", "金融・保険", "不動産業", "飲食・宿泊所", 
                            "医療・福祉", "教育・学習", "複合サービス事業", "サービス業", "公務", "その他"
                        ], key="new_industry")
                        headcount = st.text_input("人数", key="new_headcount")
                        work_content = st.text_area("作業内容詳細", key="new_work_content")
                    
                    # 工程選択
                    st.write("**工程:**")
                    phase_cols = st.columns(5)
                    phases = []
                    phase_options = ["環境構築", "要件", "基本", "詳細", "製造", "単体", "結合", "総合", "保守運用", "他"]
                    for i, phase in enumerate(phase_options):
                        with phase_cols[i % 5]:
                            if st.checkbox(phase, key=f"new_phase_{i}"):
                                phases.append(phase)
                    
                    # 環境情報
                    st.write("**環境情報:**")
                    env_cols = st.columns(4)
                    with env_cols[0]:
                        env_langs = st.text_area("言語", key="new_env_langs", help="複数ある場合は改行で区切って入力")
                    with env_cols[1]:
                        env_tools = st.text_area("ツール/FW/Lib", key="new_env_tools", help="複数ある場合は改行で区切って入力")
                    with env_cols[2]:
                        env_dbs = st.text_area("DB", key="new_env_dbs", help="複数ある場合は改行で区切って入力")
                    with env_cols[3]:
                        env_oss = st.text_area("OS/マシン", key="new_env_oss", help="複数ある場合は改行で区切って入力")
                    
                    submitted = st.form_submit_button("案件情報を追加", type="primary")
                    
                    if submitted:
                        # 案件情報をデータベースに保存
                        def save_new_project(user_id, project_data):
                            """新しい案件情報を保存"""
                            conn = sqlite3.connect(DB_PATH)
                            try:
                                cursor = conn.cursor()
                                
                                # 新しいスキーマかどうか確認
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_info'")
                                use_new_schema = cursor.fetchone() is not None
                                
                                if use_new_schema:
                                    cursor.execute("""
                                        INSERT INTO projects (user_info_id, period_start, period_end, system_name,
                                                           role, industry, work_content, phases, headcount,
                                                           env_langs, env_tools, env_dbs, env_oss)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        user_id, project_data['period_start'], project_data['period_end'],
                                        project_data['system_name'], project_data['role'], project_data['industry'],
                                        project_data['work_content'], str(phases), project_data['headcount'],
                                        project_data['env_langs'], project_data['env_tools'],
                                        project_data['env_dbs'], project_data['env_oss']
                                    ))
                                else:
                                    cursor.execute("""
                                        INSERT INTO projects (basic_info_id, period_start, period_end, system_name,
                                                           role, industry, work_content, phases, headcount,
                                                           env_langs, env_tools, env_dbs, env_oss)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (
                                        user_id, project_data['period_start'], project_data['period_end'],
                                        project_data['system_name'], project_data['role'], project_data['industry'],
                                        project_data['work_content'], str(phases), project_data['headcount'],
                                        project_data['env_langs'], project_data['env_tools'],
                                        project_data['env_dbs'], project_data['env_oss']
                                    ))
                                
                                conn.commit()
                                return True
                            except Exception as e:
                                conn.rollback()
                                st.error(f"案件情報の保存に失敗しました: {str(e)}")
                                return False
                            finally:
                                conn.close()
                        
                        # スキル情報の自動追加
                        def update_skills_from_project(user_id, project_data):
                            """案件情報からスキル情報を自動更新"""
                            conn = sqlite3.connect(DB_PATH)
                            try:
                                cursor = conn.cursor()
                                
                                # 新しいスキーマかどうか確認
                                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_info'")
                                use_new_schema = cursor.fetchone() is not None
                                
                                if not use_new_schema:
                                    return  # 古いスキーマの場合はスキップ
                                
                                # 期間から経験年数を計算
                                def calculate_years(start_date, end_date):
                                    if not start_date or not end_date:
                                        return 0
                                    try:
                                        start = datetime.strptime(str(start_date), "%Y-%m-%d")
                                        end = datetime.strptime(str(end_date), "%Y-%m-%d")
                                        delta = end - start
                                        return round(delta.days / 365.25, 1)
                                    except:
                                        return 0
                                
                                experience_years = calculate_years(project_data['period_start'], project_data['period_end'])
                                
                                # 言語スキルの追加
                                if project_data['env_langs']:
                                    languages = [lang.strip() for lang in str(project_data['env_langs']).split('\n') if lang.strip()]
                                    for lang in languages:
                                        # 既存のスキルを確認
                                        cursor.execute("""
                                            SELECT experience_years FROM skills 
                                            WHERE user_info_id = ? AND skill_type = 'language' AND skill_name = ?
                                        """, (user_id, lang))
                                        existing = cursor.fetchone()
                                        
                                        if existing:
                                            # 既存の経験年数に追加
                                            new_years = float(existing[0]) + experience_years
                                            cursor.execute("""
                                                UPDATE skills SET experience_years = ? 
                                                WHERE user_info_id = ? AND skill_type = 'language' AND skill_name = ?
                                            """, (new_years, user_id, lang))
                                        else:
                                            # 新しいスキルを追加
                                            cursor.execute("""
                                                INSERT INTO skills (user_info_id, skill_type, skill_name, experience_years)
                                                VALUES (?, 'language', ?, ?)
                                            """, (user_id, lang, experience_years))
                                
                                # ツールスキルの追加
                                if project_data['env_tools']:
                                    tools = [tool.strip() for tool in str(project_data['env_tools']).split('\n') if tool.strip()]
                                    for tool in tools:
                                        cursor.execute("""
                                            SELECT experience_years FROM skills 
                                            WHERE user_info_id = ? AND skill_type = 'tool' AND skill_name = ?
                                        """, (user_id, tool))
                                        existing = cursor.fetchone()
                                        
                                        if existing:
                                            new_years = float(existing[0]) + experience_years
                                            cursor.execute("""
                                                UPDATE skills SET experience_years = ? 
                                                WHERE user_info_id = ? AND skill_type = 'tool' AND skill_name = ?
                                            """, (new_years, user_id, tool))
                                        else:
                                            cursor.execute("""
                                                INSERT INTO skills (user_info_id, skill_type, skill_name, experience_years)
                                                VALUES (?, 'tool', ?, ?)
                                            """, (user_id, tool, experience_years))
                                
                                # DBスキルの追加
                                if project_data['env_dbs']:
                                    dbs = [db.strip() for db in str(project_data['env_dbs']).split('\n') if db.strip()]
                                    for db in dbs:
                                        cursor.execute("""
                                            SELECT experience_years FROM skills 
                                            WHERE user_info_id = ? AND skill_type = 'db' AND skill_name = ?
                                        """, (user_id, db))
                                        existing = cursor.fetchone()
                                        
                                        if existing:
                                            new_years = float(existing[0]) + experience_years
                                            cursor.execute("""
                                                UPDATE skills SET experience_years = ? 
                                                WHERE user_info_id = ? AND skill_type = 'db' AND skill_name = ?
                                            """, (new_years, user_id, db))
                                        else:
                                            cursor.execute("""
                                                INSERT INTO skills (user_info_id, skill_type, skill_name, experience_years)
                                                VALUES (?, 'db', ?, ?)
                                            """, (user_id, db, experience_years))
                                
                                # マシンスキルの追加
                                if project_data['env_oss']:
                                    machines = [machine.strip() for machine in str(project_data['env_oss']).split('\n') if machine.strip()]
                                    for machine in machines:
                                        cursor.execute("""
                                            SELECT experience_years FROM skills 
                                            WHERE user_info_id = ? AND skill_type = 'machine' AND skill_name = ?
                                        """, (user_id, machine))
                                        existing = cursor.fetchone()
                                        
                                        if existing:
                                            new_years = float(existing[0]) + experience_years
                                            cursor.execute("""
                                                UPDATE skills SET experience_years = ? 
                                                WHERE user_info_id = ? AND skill_type = 'machine' AND skill_name = ?
                                            """, (new_years, user_id, machine))
                                        else:
                                            cursor.execute("""
                                                INSERT INTO skills (user_info_id, skill_type, skill_name, experience_years)
                                                VALUES (?, 'machine', ?, ?)
                                            """, (user_id, machine, experience_years))
                                
                                conn.commit()
                                return True
                            except Exception as e:
                                conn.rollback()
                                st.error(f"スキル情報の更新に失敗しました: {str(e)}")
                                return False
                            finally:
                                conn.close()
                        
                        # データを準備
                        project_data = {
                            'period_start': period_start.strftime('%Y-%m-%d') if period_start else '',
                            'period_end': period_end.strftime('%Y-%m-%d') if period_end else '',
                            'system_name': system_name,
                            'role': role,
                            'industry': industry,
                            'work_content': work_content,
                            'headcount': headcount,
                            'env_langs': env_langs,
                            'env_tools': env_tools,
                            'env_dbs': env_dbs,
                            'env_oss': env_oss
                        }
                        
                        # 案件情報を保存
                        if save_new_project(selected_user, project_data):
                            st.success("案件情報を追加しました！")
                            
                            # スキル情報を自動更新
                            if update_skills_from_project(selected_user, project_data):
                                st.success("スキル情報を自動更新しました！")
                            
                            st.rerun()
                        else:
                            st.error("案件情報の保存に失敗しました。")
            else:
                st.info("このユーザーには案件情報がありません。")
        else:
            st.error("ユーザー情報の取得に失敗しました。")

# 一時ファイルを削除
if os.path.exists("check_db_structure.py"):
    os.remove("check_db_structure.py")
