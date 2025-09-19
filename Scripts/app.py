import streamlit as st
import traceback  # 追加
import pandas as pd  # 追加

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
    import os
    skill_sheet_path = os.path.join(os.path.dirname(__file__), "SkillSheetWebCreate.py")
    exec(open(skill_sheet_path, encoding="utf-8").read())
elif st.session_state.current_page == "📊 データ参照・管理":
    # データ参照ページの内容を直接実行
    import os
    data_view_path = os.path.join(os.path.dirname(__file__), "DataViewPage.py")
    exec(open(data_view_path, encoding="utf-8").read())
elif st.session_state.current_page == "✏️ スキルシート更新":
    # スキルシート更新ページの内容を直接実行
    import os
    update_path = os.path.join(os.path.dirname(__file__), "UpdatePageEnhanced.py")
    exec(open(update_path, encoding="utf-8").read())
    # 4番（PythonのScriptsフォルダにパスを通す）を試したところ、以下のエラーが表示されました:
    #
    # PS C:\Users\MetokiMasato> C:\Users\MetokiMasato\AppData\Local\Programs\Python\PythonXX\Scripts
    # C:\Users\MetokiMasato\AppData\Local\Programs\Python\PythonXX\Scripts : 用語 'C:\Users\MetokiMasato\AppData\Local\Programs\Python\PythonXX\Scripts' は、コマンドレット、関数、スクリプト ファイル、または操作可能なプログラムの名前として認識されません。名前が正しく記述されていることを確認し、パスが含まれている場合はそのパスが正しいことを確認してから、再試行してください。
    # 発生場所 行:1 文字:1
    # + C:\Users\MetokiMasato\AppData\Local\Programs\Python\PythonXX\Scripts
    # + ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    #     + CategoryInfo          : ObjectNotFound: (C:\Users\Metoki...ythonXX\Scripts:String) [], CommandNotFoundException
    #     + FullyQualifiedErrorId : CommandNotFoundException
    #
    # → このエラーは、「パスをコマンドとして実行」してしまったため発生しています。
    #   パスを通すには、環境変数「Path」にScriptsフォルダのパスを追加してください。
    #   追加後、新しいコマンドプロンプトやPowerShellを開き直してから「streamlit run app.py」などのコマンドを実行してください。



