import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv

# .env を読み込む
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


# --- ゲームモード選択 ---
mode = st.selectbox("ゲームモードを選択", ["論破度判定"])

# --- 論破度モードのときだけキャラクター選択 ---
character = None
if mode == "論破度判定":
    character = st.selectbox("場面を選択", ["魔王軍入団面接"])

# --- セッション状態の初期化 ---
if "turn" not in st.session_state:
    st.session_state.turn = 0
if "history" not in st.session_state:
    st.session_state.history = []
if "finished" not in st.session_state:
    st.session_state.finished = False
if "intro_shown" not in st.session_state:
    st.session_state.intro_shown = False

# --- チャット履歴の表示（魔王は画像つき） ---
for msg in st.session_state.history:
    if msg["role"] == "assistant":
        with st.chat_message("assistant"):
            st.image("maou.jpeg", width=80)
            st.write(msg["content"])
    else:
        with st.chat_message("user"):
            st.write(msg["content"])

# --- 魔王軍入団面接の最初のメッセージ ---
if (
    mode == "論破度判定"
    and character == "魔王軍入団面接"
    and not st.session_state.intro_shown
):
    intro = "🔥 **魔王軍 入団面接を開始する…**\n魔王：『まずは名を名乗れ。貴様は何者だ？』"
    st.session_state.history.append({"role": "assistant", "content": intro})
    st.session_state.intro_shown = True
    st.session_state.turn = 1
    st.rerun()

# --- ユーザー入力 ---
user_input = st.chat_input("メッセージを入力")

if user_input and not st.session_state.finished:

    # ユーザー発言を履歴に追加
    st.session_state.history.append({"role": "user", "content": user_input})
    st.session_state.turn += 1

    # --- 質問フェーズ（最大10ターン） ---
    if st.session_state.turn <= 10 and not st.session_state.finished:

        system_prompt = f"""
あなたは魔王として振る舞う。
ユーザーは魔王軍に入りたい志願者である。
あなたは面接官として、ユーザーに質問を投げかける。
質問は短く鋭く、魔王らしい威圧感を持たせる。
返答は「質問のみ」にする。

現在のターン: {st.session_state.turn}

もし次の質問が最後の質問（ターン10）であれば、
必ず質問文の冒頭に「これが最後の質問だ…」と付け加える。
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                *st.session_state.history
            ]
        )

        ai_reply = response.choices[0].message.content
        st.session_state.history.append({"role": "assistant", "content": ai_reply})

    # --- 評価フェーズ（最低3ターン以降、AIが判断） ---
    if st.session_state.turn >= 3 and not st.session_state.finished:

        eval_prompt = """
あなたは魔王として、志願者の回答を100点満点で評価する。

評価基準（各25点満点）：
1. 魔王軍にふさわしい野心（0〜25）
2. 忠誠心（0〜25）
3. 戦闘力のアピール（0〜25）
4. 論理性と説得力（0〜25）

あなたは以下を判断する：
1. 志願者の回答が評価に十分な情報を含んでいるか？
2. もし十分なら即座に評価を行う。
3. もし不十分なら「False」とだけ返す。

返答形式（評価可能な場合）：

野心：◯◯点  
忠誠心：◯◯点  
戦闘力：◯◯点  
論理性：◯◯点  
――――――  
合計：◯◯点  
評価コメント：◯◯◯  
判定：合格 or 不合格

評価不可能 → 「False」
"""

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": eval_prompt},
                *st.session_state.history
            ]
        )

        result = response.choices[0].message.content.strip()

        if result != "False":
            st.session_state.history.append({"role": "assistant", "content": result})
            st.session_state.finished = True

        elif st.session_state.turn >= 10:
            final_eval_prompt = """
あなたは魔王として、志願者の回答を100点満点で評価する。

評価基準（各25点満点）：
1. 魔王軍にふさわしい野心（0〜25）
2. 忠誠心（0〜25）
3. 戦闘力のアピール（0〜25）
4. 論理性と説得力（0〜25）

返答形式：

野心：◯◯点  
忠誠心：◯◯点  
戦闘力：◯◯点  
論理性：◯◯点  
――――――  
合計：◯◯点  
評価コメント：◯◯◯  
判定：合格 or 不合格
"""

            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": final_eval_prompt},
                    *st.session_state.history
                ]
            )

            final_result = response.choices[0].message.content
            st.session_state.history.append({"role": "assistant", "content": final_result})
            st.session_state.finished = True

    st.rerun()

# --- ゲーム終了後の案内 ---
if st.session_state.finished:
    st.info("面接は終了しました。もう一度プレイするには下のボタンを押してください。")

    if st.button("もう一度プレイする"):
        st.session_state.turn = 0
        st.session_state.history = []
        st.session_state.finished = False
        st.session_state.intro_shown = False
        st.rerun()
