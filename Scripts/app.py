import streamlit as st
import traceback  # 追加
import pandas as pd  # 追加
import os  # ← ここを追加
import openpyxl  # ← ここに追加
from io import BytesIO
import hashlib
import sqlite3

# ページ設定
st.set_page_config(
    page_title="ホーム",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': None
    }
)

# ネットワークアクセスを有効化
import os
if 'STREAMLIT_SERVER_ADDRESS' not in os.environ:
    os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
if 'STREAMLIT_SERVER_PORT' not in os.environ:
    os.environ['STREAMLIT_SERVER_PORT'] = '8501'

# --- ログイン認証機能 ---
DB_PATH = os.path.join(os.path.dirname(__file__), "skillsheet_data.db")

def hash_password(password):
    """パスワードをハッシュ化"""
    return hashlib.sha256(password.encode()).hexdigest()

def init_users_table():
    """ユーザー管理テーブルを初期化"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                login_id TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                username TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        # デフォルトユーザーが存在しない場合は作成
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute('''
                INSERT INTO users (login_id, password_hash, username)
                VALUES (?, ?, ?)
            ''', ('admin', hash_password('admin123'), '管理者'))
        conn.commit()
    except Exception as e:
        conn.rollback()
        st.error(f"ユーザーテーブルの初期化エラー: {str(e)}")
    finally:
        conn.close()

def authenticate_user(login_id, password):
    """ユーザー認証"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        cursor.execute('''
            SELECT id, login_id, password_hash, username FROM users WHERE login_id = ?
        ''', (login_id,))
        user = cursor.fetchone()
        if user and hash_password(password) == user[2]:
            return {'id': user[0], 'login_id': user[1], 'username': user[3]}
        return None
    except Exception as e:
        st.error(f"認証エラー: {str(e)}")
        return None
    finally:
        conn.close()

# ユーザーテーブルを初期化
init_users_table()

# セッション状態の初期化
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'login_error' not in st.session_state:
    st.session_state.login_error = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None

# ログイン画面
def show_login_page():
    """ログイン画面を表示"""
    st.markdown(
        """
        <style>
        .login-container {
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 80vh;
        }
        .login-box {
            background: linear-gradient(120deg, #e3f2fd 80%, #bbdefb 100%);
            border-radius: 1.5rem;
            box-shadow: 0 4px 20px rgba(25, 118, 210, 0.15);
            padding: 3rem 4rem;
            border: 2px solid #1976d2;
            max-width: 450px;
            width: 100%;
        }
        .login-title {
            color: #1976d2;
            font-weight: bold;
            font-size: 2rem;
            text-align: center;
            margin-bottom: 2rem;
            letter-spacing: 0.05em;
        }
        .login-input {
            margin-bottom: 1.5rem;
        }
        .login-button {
            width: 100%;
            margin-top: 1rem;
        }
        .error-message {
            color: #e53935;
            background-color: #ffebee;
            padding: 0.8rem;
            border-radius: 0.5rem;
            margin-bottom: 1rem;
            border: 1px solid #e53935;
            text-align: center;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    st.markdown('<div class="login-box">', unsafe_allow_html=True)
    st.markdown('<div class="login-title">🔐 ログイン</div>', unsafe_allow_html=True)
    
    if st.session_state.login_error:
        st.markdown(
            '<div class="error-message">IDまたはパスワードが正しくありません。</div>',
            unsafe_allow_html=True
        )
    
    with st.form("login_form"):
        login_id = st.text_input("ID", key="login_id_input", help="ログインIDを入力してください")
        login_password = st.text_input("パスワード", type="password", key="login_password_input", help="パスワードを入力してください")
        submitted = st.form_submit_button("ログイン", type="primary", use_container_width=True)
        
        if submitted:
            # 認証チェック
            user = authenticate_user(login_id, login_password)
            if user:
                st.session_state.authenticated = True
                st.session_state.login_error = False
                st.session_state.user_id = user['id']
                st.session_state.username = user['username']
                st.rerun()
            else:
                st.session_state.login_error = True
                st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ログアウト機能
def logout():
    """ログアウト処理"""
    st.session_state.authenticated = False
    st.session_state.login_error = False
    st.session_state.user_id = None
    st.session_state.username = None
    if 'current_page' in st.session_state:
        del st.session_state.current_page
    st.rerun()

# 認証チェック：ログインしていない場合はログイン画面を表示
if not st.session_state.authenticated:
    show_login_page()
    st.stop()  # 以降のコードを実行しない

# --- サイドバーの背景色やラジオボタンの視認性向上のためのカスタムCSS ---
st.markdown(
    """
    <style>
    /* サイドバーの背景色を青に */
    section[data-testid="stSidebar"] {
        background-color: #1976d2 !important; /* 濃い青 */
    }
    /* サイドバー内のテキスト色を白に */
    section[data-testid="stSidebar"] .css-1v0mbdj, /* Streamlit 1.32以降 */
    section[data-testid="stSidebar"] .css-1c7y2kd, /* Streamlit 1.25-1.31 */
    section[data-testid="stSidebar"] .css-1d391kg { /* 旧バージョン */
        color: white !important;
    }
    /* サイドバーのラジオボタンのラベルも白に */
    section[data-testid="stSidebar"] label {
        color: white !important;
    }
    /* サイドバーのラジオボタンの選択肢背景を白にし、黒い枠線と影を追加して浮かせる */
    section[data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"] {
        background-color: #fff !important;
        color: #222 !important;
        border-radius: 0.5rem;
        padding: 0.2rem 0.8rem;
        border: 2px solid #222 !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
        margin-bottom: 0.5rem;
        transition: box-shadow 0.2s, background 0.2s;
        position: relative;
        z-index: 1;
    }
    /* 選択中のラジオボタンはより強調 */
    section[data-testid="stSidebar"] .stRadio > div > label[data-baseweb="radio"][aria-checked="true"] {
        background-color: #e3f2fd !important;
        border: 2px solid #1565c0 !important;
        color: #1565c0 !important;
        box-shadow: 0 4px 12px rgba(21,101,192,0.15);
    }
    /* ラジオボタンのinput自体も前面に */
    section[data-testid="stSidebar"] .stRadio input[type="radio"] {
        z-index: 2;
        position: relative;
    }
    /* チェックボックスやセレクトボックスにも黒い枠線と白背景 */
    section[data-testid="stSidebar"] .stCheckbox,
    section[data-testid="stSidebar"] .stSelectbox,
    section[data-testid="stSidebar"] .stMultiSelect {
        border: 2px solid #222 !important;
        border-radius: 0.3rem !important;
        background-color: #fff !important;
        color: #222 !important;
        padding: 0.2rem 0.5rem !important;
        margin-bottom: 0.3rem !important;
        box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    }
    /* 入力欄にも黒い枠線と白背景 */
    section[data-testid="stSidebar"] input,
    section[data-testid="stSidebar"] textarea {
        border: 2px solid #222 !important;
        border-radius: 0.3rem !important;
        background-color: #fff !important;
        color: #222 !important;
    }
    /* フォーカス時の枠線を強調 */
    section[data-testid="stSidebar"] input:focus,
    section[data-testid="stSidebar"] textarea:focus {
        border: 2px solid #1565c0 !important;
        outline: none !important;
    }
    /* サイドバーのラジオボタンの選択肢間に余白 */
    section[data-testid="stSidebar"] .stRadio > div {
        gap: 0.5rem !important;
        display: flex;
        flex-direction: column;
    }
    /* サイドバーのタイトルに影をつけて浮かせる＋視認性向上 */
    section[data-testid="stSidebar"] h1, section[data-testid="stSidebar"] h2, section[data-testid="stSidebar"] h3 {
        text-shadow: 0 2px 8px rgba(0,0,0,0.18);
        color: #fff !important;
        background: linear-gradient(90deg, #1565c0 60%, #1976d2 100%);
        padding: 0.4em 0.8em 0.4em 0.8em;
        border-radius: 0.5em;
        margin-bottom: 0.7em;
        letter-spacing: 0.05em;
        font-weight: bold;
        font-size: 1.5em;
        box-shadow: 0 2px 8px rgba(0,0,0,0.10);
        border-left: 6px solid #fff;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- サイドバーのナビゲーション ---
with st.sidebar:
    # ユーザー名表示
    if st.session_state.get('username'):
        st.markdown(
            f"""
            <div style="
                color: #fff;
                font-size: 1.1em;
                font-weight: bold;
                text-align: center;
                background: linear-gradient(90deg, #1565c0 60%, #1976d2 100%);
                padding: 0.5em 0.8em;
                border-radius: 0.5em;
                margin-bottom: 0.7em;
                border-left: 4px solid #fff;
                ">
                👤 {st.session_state.username}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # "メニュー" の視認性を上げるためにHTMLで太字・大きめ・影付き・余白付きで表示
    st.markdown(
        """
        <div style="
            color: #fff;
            font-size: 1.7em;
            font-weight: bold;
            text-shadow: 0 2px 8px rgba(0,0,0,0.18);
            background: linear-gradient(90deg, #1565c0 60%, #1976d2 100%);
            padding: 0.4em 0.8em 0.4em 0.8em;
            border-radius: 0.5em;
            margin-bottom: 0.7em;
            letter-spacing: 0.05em;
            border-left: 6px solid #fff;
            ">
            メニュー
        </div>
        """,
        unsafe_allow_html=True
    )
    nav_options = [
        "🏠 ホーム",
        "📝 スキルシート作成",
        "📊 データ参照・管理",
        "✏️ スキルシート更新"
    ]
    # セッションの現在ページに応じてラジオの選択位置を同期
    current_index = nav_options.index(st.session_state.get("current_page", "🏠 ホーム")) if st.session_state.get("current_page", "🏠 ホーム") in nav_options else 0
    # ラジオボタンのラベルが背景につぶれないようhelp引数で余白を追加
    page = st.radio(
        "ページを選択してください",
        nav_options,
        index=current_index,
        key="sidebar_nav",
        help="ページを選択してください"
    )
    
    # ログアウトボタン
    st.markdown("---")
    st.markdown(
        """
        <style>
        .logout-button {
            width: 100%;
            margin-top: 1rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    if st.button("🚪 ログアウト", key="logout_button", use_container_width=True):
        logout()

# セッション状態でページを管理
if 'current_page' not in st.session_state:
    st.session_state.current_page = "🏠 ホーム"

# ページ選択に基づいてセッション状態を更新
if page != st.session_state.current_page:
    st.session_state.current_page = page
    st.rerun()

# --- メイン画面レイアウト工夫 ---
if st.session_state.current_page == "🏠 ホーム":
    # タイトルと説明を横並びで配置
    st.markdown(
        """
        <style>
        .main-home-header {
            display: flex;
            align-items: center;
            gap: 2.5rem;
            margin-bottom: 0.5rem;
        }
        .main-home-header .icon {
            font-size: 3.2rem;
            margin-right: 0.5rem;
        }
        .main-home-header .title {
            font-size: 2.2rem;
            font-weight: bold;
            color: #1976d2;
            letter-spacing: 0.04em;
            text-shadow: 0 2px 8px rgba(25,118,210,0.10);
        }
        .main-home-header .desc {
            font-size: 1.1rem;
            color: #444;
            margin-top: 0.2rem;
        }
        .main-home-section {
            background: #f5f7fa;
            border-radius: 1.2rem;
            box-shadow: 0 2px 12px rgba(25,118,210,0.07);
            padding: 2.2rem 2.5rem 1.5rem 2.5rem;
            margin-bottom: 2.2rem;
        }
        .main-home-btn {
            width: 100%;
            font-size: 1.15rem !important;
            padding: 0.7rem 0 !important;
            margin-top: 0.7rem !important;
            margin-bottom: 0.2rem !important;
        }
        .main-home-section h3 {
            margin-bottom: 0.5rem;
            color: #1976d2;
            font-weight: bold;
        }
        .main-home-section .section-desc {
            color: #555;
            margin-bottom: 0.7rem;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    st.markdown(
        """
        <div class="main-home-header">
            <div class="icon">🏠</div>
            <div>
                <div class="title">スキルシート管理システム</div>
                <div class="desc">エンジニアのスキルシートを作成・管理・更新できるWebアプリです。</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")

    # 3つの機能を横並びのカード風に配置
    col1, col2, col3 = st.columns([1,1,1])

    with col1:
        st.markdown(
            """
            <div class="main-home-section">
                <h3>📝 スキルシート作成</h3>
                <div class="section-desc">新しいスキルシートを作成します</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("作成画面へ", key="create_btn", help="新規スキルシート作成", use_container_width=True):
            st.session_state.current_page = "📝 スキルシート作成"
            st.rerun()

    with col2:
        st.markdown(
            """
            <div class="main-home-section">
                <h3>📊 データ参照・管理</h3>
                <div class="section-desc">保存されたデータを表示・管理します</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("参照ページへ", key="view_btn", help="データ参照・管理", use_container_width=True):
            st.session_state.current_page = "📊 データ参照・管理"
            st.rerun()

    with col3:
        st.markdown(
            """
            <div class="main-home-section">
                <h3>✏️ スキルシート更新</h3>
                <div class="section-desc">既存のスキルシートに案件情報を追加・更新します</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        if st.button("更新ページへ", key="update_btn", help="スキルシート更新", use_container_width=True):
            st.session_state.current_page = "✏️ スキルシート更新"
            st.rerun()

    # ボタンの色を赤色に統一するためのカスタムCSS
    st.markdown(
        """
        <style>
        div.stButton > button {
            background-color: #e53935 !important;
            color: white !important;
            border: none !important;
            border-radius: 0.7rem !important;
            font-weight: bold !important;
            transition: background 0.2s;
            box-shadow: 0 2px 8px rgba(229,57,53,0.10);
        }
        div.stButton > button:hover {
            background-color: #b71c1c !important;
            color: white !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

elif st.session_state.current_page == "📝 スキルシート作成":
    # スキルシート作成ページの内容を直接実行
    skill_sheet_path = os.path.join(os.path.dirname(__file__), "SkillSheetWebCreate.py")
    exec(open(skill_sheet_path, encoding="utf-8").read())
elif st.session_state.current_page == "📊 データ参照・管理":
    # データ参照ページの内容を直接実行
    data_view_path = os.path.join(os.path.dirname(__file__), "DataViewPage.py")
    exec(open(data_view_path, encoding="utf-8").read())
elif st.session_state.current_page == "✏️ スキルシート更新":
    # スキルシート更新ページの内容を直接実行
    update_path = os.path.join(os.path.dirname(__file__), "UpdatePageEnhanced.py")
    exec(open(update_path, encoding="utf-8").read())



   