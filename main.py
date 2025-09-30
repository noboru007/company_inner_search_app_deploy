"""
このファイルは、Webアプリのメイン処理が記述されたファイルです。
"""

############################################################
# 1. ライブラリの読み込み
############################################################
# 環境変数の設定（HTTPリクエストの識別用）
import os
if not os.environ.get('USER_AGENT'):
    os.environ['USER_AGENT'] = 'CompanyInnerSearchApp/1.0'
# 「.env」ファイルから環境変数を読み込むための関数
# from dotenv import load_dotenv
# ログ出力を行うためのモジュール
import logging
# streamlitアプリの表示を担当するモジュール
import streamlit as st
# （自作）画面表示以外の様々な関数が定義されているモジュール
import utils
# （自作）アプリ起動時に実行される初期化処理が記述された関数
from initialize import initialize
# （自作）画面表示系の関数が定義されているモジュール
import components as cn
# （自作）変数（定数）がまとめて定義・管理されているモジュール
import constants as ct


############################################################
# 2. 設定関連
############################################################
# ブラウザタブの表示文言を設定
st.set_page_config(
    page_title=ct.APP_NAME
)

# ログ出力を行うためのロガーの設定
logger = logging.getLogger(ct.LOGGER_NAME)


############################################################
# 3. 初期化処理
############################################################
try:
    # 初期化処理（「initialize.py」の「initialize」関数を実行）
    # 初期化処理として、大きく以下3つの処理が実行されます。
    # 1 ログ出力の設定
    # 2 初期化データの用意
    # 3 Retriever（ベクターストアからの検索を担当するオブジェクト」の作成
    initialize()
except Exception as e:
    # エラーログの出力
    logger.error(f"{ct.INITIALIZE_ERROR_MESSAGE}\n{e}")
    # エラーメッセージの画面表示
    st.error(utils.build_error_message(ct.INITIALIZE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    # 後続の処理を中断
    st.stop()

# アプリ起動時のログファイルへの出力
if not "initialized" in st.session_state:
    st.session_state.initialized = True
    logger.info(ct.APP_BOOT_MESSAGE)



############################################################
# 4. サイドバー表示 必須課題 【問題3】サイドバー表示
############################################################
# サイドバー（利用目的選択と入力例）
cn.display_sidebar()

############################################################
# 5. メインコンテンツ表示
############################################################
# タイトル表示
cn.display_app_title()

# AIメッセージの初期表示
cn.display_initial_ai_message()


############################################################
# 6. 会話ログの表示
############################################################
try:
    # 会話ログの表示
    cn.display_conversation_log()
except Exception as e:
    # エラーログの出力
    logger.error(f"{ct.CONVERSATION_LOG_ERROR_MESSAGE}\n{e}")
    # エラーメッセージの画面表示
    st.error(utils.build_error_message(ct.CONVERSATION_LOG_ERROR_MESSAGE), icon=ct.ERROR_ICON)
    # 後続の処理を中断
    st.stop()


############################################################
# 7. チャット入力の受け付け
############################################################
chat_message = st.chat_input(ct.CHAT_INPUT_HELPER_TEXT)


############################################################
# 8. チャット送信時の処理
############################################################
# チャット欄から送信を行うと「chat_message」に入力値が格納されるため、if文の条件式がTrueとなります。このif文の中では、チャット送信後の処理が記述されています。
# 
# LLMアプリでログとして記録を取りたい情報の一つが、LLMに渡されたユーザーメッセージです。チャットが送信された後、辞書型でユーザーメッセージと利用目的（「社内文書検索」or「社内問い合わせ」）の情報をログファイルに出力しています。

if chat_message:
    # ==========================================
    # 7-1. ユーザーメッセージの表示
    # ==========================================
    # ユーザーメッセージのログ出力
    logger.info({"message": chat_message, "application_mode": st.session_state.mode})

    # ユーザーメッセージを表示
    with st.chat_message("user"):
        st.markdown(chat_message)

    # ==========================================
    # 7-2. LLMからの回答取得
    # ==========================================
    # 「st.spinner」でグルグル回っている間、表示の不具合が発生しないよう空のエリアを表示
    # またwith文の前に「st.empty()」というコードを実行していますが、これはStreamlitで空のエリアを表示するために用意しているものです。スピナーのwith文の前に空のエリアを表示しておかないと、表示の不具合が発生することがあるため、スピナーのwith文と一緒に空のエリアを表示する必要があることを覚えておきましょう。
    res_box = st.empty()
    # LLMによる回答生成（回答生成が完了するまでグルグル回す）
    # スピナーは、「with st.spinner()」で表示できます。このwith文の中のコード実行が完了するまで、スピナーが表示されます。引数として渡したテキストは、スピナーと一緒に表示されます。
    with st.spinner(ct.SPINNER_TEXT):
        try:
            # 画面読み込み時に作成したRetrieverを使い、Chainを実行
            # utils.pyモジュールの「get_llm_response()」関数にユーザーメッセージを渡して実行することで、LLMからの回答が生成され、変数「llm_response」に格納されます。
            llm_response = utils.get_llm_response(chat_message)
        except Exception as e:
            # エラーログの出力
            logger.error(f"{ct.GET_LLM_RESPONSE_ERROR_MESSAGE}\n{e}")
            # エラーメッセージの画面表示
            st.error(utils.build_error_message(ct.GET_LLM_RESPONSE_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            # 後続の処理を中断
            st.stop()
    
    # ==========================================
    # 7-3. LLMからの回答表示
    # ==========================================
    with st.chat_message("assistant"):
        try:
            # ==========================================
            # モードが「社内文書検索」の場合
            # ==========================================
            if st.session_state.mode == ct.ANSWER_MODE_1:
                # 入力内容と関連性が高い社内文書のありかを表示
                content = cn.display_search_llm_response(llm_response)

            # ==========================================
            # モードが「社内問い合わせ」の場合
            # ==========================================
            elif st.session_state.mode == ct.ANSWER_MODE_2:
                # 入力に対しての回答と、参照した文書のありかを表示
                content = cn.display_contact_llm_response(llm_response)
            
            # AIメッセージのログ出力
            logger.info({"message": content, "application_mode": st.session_state.mode})
        except Exception as e:
            # エラーログの出力
            logger.error(f"{ct.DISP_ANSWER_ERROR_MESSAGE}\n{e}")
            # エラーメッセージの画面表示
            st.error(utils.build_error_message(ct.DISP_ANSWER_ERROR_MESSAGE), icon=ct.ERROR_ICON)
            # 後続の処理を中断
            st.stop()

    # ==========================================
    # 7-4. 会話ログへの追加
    # ==========================================
    # 表示用の会話ログにユーザーメッセージを追加
    # 「st.session_state」で、会話ログを追加するためのリスト「messages」にユーザーメッセージとAIメッセージをそれぞれ追加しています。会話ログを表示する際にユーザーメッセージ用とAIメッセージ用で処理を分岐するため、「role」も一緒に渡しています。
    st.session_state.messages.append({"role": "user", "content": chat_message})
    # 表示用の会話ログにAIメッセージを追加
    st.session_state.messages.append({"role": "assistant", "content": content})
