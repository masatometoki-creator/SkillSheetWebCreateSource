import streamlit as st
import sqlite3
import pandas as pd
import os
import hashlib

# データベースパス
DB_PATH = os.path.join(os.path.dirname(__file__), "skillsheet_data.db")

# --- 権限チェック: 管理者以外はアクセス禁止 ---
if st.session_state.get('role') != "管理者":
    st.error("ユーザー管理ページへのアクセス権限がありません。ホームに戻ります。")
    st.session_state.current_page = "🏠 ホーム"
    st.rerun()

st.title("👥 ユーザー管理")

# ページ内ナビゲーション
nav_cols = st.columns([1, 1, 8])
with nav_cols[0]:
    if st.button("🏠 ホームへ戻る", key="go_home_from_usermgmt"):
        st.session_state.current_page = "🏠 ホーム"
        st.rerun()

st.markdown("---")

# カスタムCSS
st.markdown(
    """
    <style>
    .card-section {
        background: linear-gradient(120deg, #e3f2fd 80%, #bbdefb 100%);
        border-radius: 1.2rem;
        box-shadow: 0 4px 16px rgba(25, 118, 210, 0.10);
        padding: 1.5rem 1.5rem 1.2rem 1.5rem;
        margin-bottom: 1.5rem;
        border: 1.5px solid #1976d2;
    }
    .card-title {
        color: #1976d2;
        font-weight: bold;
        font-size: 1.2rem;
        margin-bottom: 0.7rem;
        letter-spacing: 0.04em;
    }
    </style>
    """,
    unsafe_allow_html=True
)

def hash_password(password):
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def get_all_users():
    """全ユーザーを取得"""
    conn = sqlite3.connect(DB_PATH)
    try:
        df = pd.read_sql_query(
            "SELECT id, login_id, password_hash, username, role, created_at FROM users ORDER BY created_at DESC",
            conn
        )
        return df
    except Exception as e:
        st.error(f"ユーザー一覧の取得に失敗しました: {str(e)}")
        return pd.DataFrame()
    finally:
        conn.close()

def create_user(login_id, password, username, role):
    """新規ユーザーを作成"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # 重複チェック
        cursor.execute("SELECT id FROM users WHERE login_id = ?", (login_id,))
        if cursor.fetchone():
            return False, "このIDは既に使用されています。"
        
        password_hash = hash_password(password)
        cursor.execute(
            "INSERT INTO users (login_id, password_hash, username, role) VALUES (?, ?, ?, ?)",
            (login_id, password_hash, username, role)
        )
        conn.commit()
        return True, "ユーザーを作成しました。"
    except Exception as e:
        conn.rollback()
        return False, f"ユーザー作成エラー: {str(e)}"
    finally:
        conn.close()

def update_user(user_id, login_id, password, username, role):
    """ユーザー情報を更新"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # 重複チェック（自分以外）
        cursor.execute("SELECT id FROM users WHERE login_id = ? AND id != ?", (login_id, user_id))
        if cursor.fetchone():
            return False, "このIDは既に使用されています。"
        
        if password:
            # パスワードが入力されている場合は更新
            password_hash = hash_password(password)
            cursor.execute(
                "UPDATE users SET login_id = ?, password_hash = ?, username = ?, role = ? WHERE id = ?",
                (login_id, password_hash, username, role, user_id)
            )
        else:
            # パスワードが空の場合はパスワードを更新しない
            cursor.execute(
                "UPDATE users SET login_id = ?, username = ?, role = ? WHERE id = ?",
                (login_id, username, role, user_id)
            )
        conn.commit()
        return True, "ユーザー情報を更新しました。"
    except Exception as e:
        conn.rollback()
        return False, f"ユーザー更新エラー: {str(e)}"
    finally:
        conn.close()

def delete_user(user_id):
    """ユーザーを削除"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # 現在ログイン中のユーザーは削除できない
        current_user_id = st.session_state.get('user_id')
        if user_id == current_user_id:
            return False, "現在ログイン中のユーザーは削除できません。"
        
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        conn.commit()
        return True, "ユーザーを削除しました。"
    except Exception as e:
        conn.rollback()
        return False, f"ユーザー削除エラー: {str(e)}"
    finally:
        conn.close()

# タブで機能を分ける
tab1, tab2, tab3 = st.tabs(["📋 ユーザー一覧", "➕ 新規登録", "✏️ 編集・削除"])

# タブ1: ユーザー一覧
with tab1:
    st.markdown(
        "<div class='card-section'><div class='card-title'>登録ユーザー一覧</div>",
        unsafe_allow_html=True
    )
    users_df = get_all_users()
    
    if users_df.empty:
        st.info("登録されているユーザーがありません。")
    else:
        # パスワードハッシュは非表示にして、ユーザー名と権限のみ表示
        display_df = users_df[['id', 'login_id', 'username', 'role', 'created_at']].copy()
        display_df.columns = ['ID', 'ログインID', 'ユーザー名', '権限', '作成日時']
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

# タブ2: 新規登録
with tab2:
    st.markdown(
        "<div class='card-section'><div class='card-title'>新規ユーザー登録</div>",
        unsafe_allow_html=True
    )
    
    with st.form("new_user_form"):
        new_login_id = st.text_input("ログインID *", key="new_login_id", help="ログイン時に使用するID")
        new_password = st.text_input("パスワード *", type="password", key="new_password", help="ログイン時に使用するパスワード")
        new_username = st.text_input("ユーザー名 *", key="new_username", help="表示名として使用されるユーザー名")
        new_role = st.selectbox("権限 *", ["一般", "管理者"], key="new_role", help="ユーザーの権限を選択してください")
        
        submitted = st.form_submit_button("ユーザーを登録", type="primary", use_container_width=True)
        
        if submitted:
            if not new_login_id or not new_password or not new_username:
                st.error("すべての項目を入力してください。")
            elif len(new_password) < 4:
                st.error("パスワードは4文字以上で入力してください。")
            else:
                success, message = create_user(new_login_id, new_password, new_username, new_role)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
    st.markdown("</div>", unsafe_allow_html=True)

# タブ3: 編集・削除
with tab3:
    users_df = get_all_users()
    
    if users_df.empty:
        st.info("編集・削除できるユーザーがありません。")
    else:
        st.markdown(
            "<div class='card-section'><div class='card-title'>ユーザー情報の編集・削除</div>",
            unsafe_allow_html=True
        )
        
        # ユーザー選択
        user_options = []
        for _, row in users_df.iterrows():
            username = row.get('username', '')
            display_name = f"ID: {row['id']} - {row['login_id']} ({username if username else 'ユーザー名なし'}) [{row['role']}]"
            user_options.append((display_name, row['id']))
        
        selected_user_id = st.selectbox(
            "編集・削除するユーザーを選択:",
            options=[opt[1] for opt in user_options],
            format_func=lambda x: next(opt[0] for opt in user_options if opt[1] == x),
            key="edit_user_select"
        )
        
        if selected_user_id:
            # 選択されたユーザーの情報を取得
            selected_user = users_df[users_df['id'] == selected_user_id].iloc[0]
            current_user_id = st.session_state.get('user_id')
            is_current_user = selected_user_id == current_user_id
            
            st.markdown("---")
            
            # 編集フォーム
            with st.form("edit_user_form"):
                st.markdown("**ユーザー情報の編集**")
                edit_login_id = st.text_input("ログインID *", value=selected_user['login_id'], key="edit_login_id")
                edit_password = st.text_input("パスワード（変更する場合のみ入力）", type="password", key="edit_password", 
                                            help="パスワードを変更しない場合は空欄のままにしてください")
                edit_username = st.text_input("ユーザー名 *", value=selected_user.get('username', ''), key="edit_username")
                edit_role = st.selectbox("権限 *", ["一般", "管理者"], 
                                       index=0 if selected_user['role'] == "一般" else 1,
                                       key="edit_role", help="ユーザーの権限を選択してください")
                
                col1, col2 = st.columns(2)
                with col1:
                    update_submitted = st.form_submit_button("情報を更新", type="primary", use_container_width=True)
                with col2:
                    delete_submitted = st.form_submit_button("ユーザーを削除", type="secondary", use_container_width=True)
                
                if update_submitted:
                    if not edit_login_id or not edit_username:
                        st.error("ログインIDとユーザー名は必須です。")
                    else:
                        success, message = update_user(selected_user_id, edit_login_id, edit_password, edit_username, edit_role)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                if delete_submitted:
                    if is_current_user:
                        st.error("現在ログイン中のユーザーは削除できません。")
                    else:
                        success, message = delete_user(selected_user_id)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        
        st.markdown("</div>", unsafe_allow_html=True)

