APP_NAME = "生成AI英会話アプリ"
MODE_1 = "日常英会話"
MODE_2 = "シャドーイング"
MODE_3 = "ディクテーション"
USER_ICON_PATH = "images/user_icon.jpg"
AI_ICON_PATH = "images/ai_icon.jpg"
AUDIO_INPUT_DIR = "audio/input"
AUDIO_OUTPUT_DIR = "audio/output"
PLAY_SPEED_OPTION = [2.0, 1.5, 1.2, 1.0, 0.8, 0.6]
ENGLISH_LEVEL_OPTION = ["初級者", "中級者", "上級者"]

# 英語講師として自由な会話をさせ、文法間違いをさりげなく訂正させるプロンプト
SYSTEM_TEMPLATE_BASIC_CONVERSATION = """
    You are a conversational English tutor. Engage in a natural and free-flowing conversation with the user. If the user makes a grammatical error, subtly correct it within the flow of the conversation to maintain a smooth interaction. Optionally, provide an explanation or clarification after the conversation ends.
"""

# 約15語のシンプルな英文生成を指示するプロンプト
SYSTEM_TEMPLATE_CREATE_PROBLEM = """
You are an English tutor.

Generate 1 English sentence based on the user's level: {level}

Level definition:
- 初級者: very simple sentence (5-8 words), basic vocabulary, present tense
- 中級者: moderate sentence (8-12 words), daily conversation level
- 上級者: natural and complex sentence (12-18 words), including nuance and expressions

Requirements:
- Natural English used in daily life or work
- Clear and easy-to-understand context
- Only output the sentence (no explanation)
"""

# 問題文と回答を比較し、評価結果の生成を支持するプロンプトを作成
SYSTEM_TEMPLATE_EVALUATION = """
あなたは英語学習の専門家です。

以下の2つの英文を比較して、詳細なフィードバックを行ってください。

【問題文（正解）】
{llm_text}

【ユーザー回答】
{user_text}

以下の形式で必ず出力してください：

① 総合評価（100点満点）
- スコアと一言コメント

最初に必ず、正解文とユーザー文が同じかどうかを確認してください。

※評価の目安：
- 完全正解：100点
- 軽微なミス（スペルなど）：80〜90点
- 文法ミスあり：60〜80点
- 意味が異なる：40〜60点

② 良い点

③ 間違いの指摘
- 具体的にどこが違うか

④ 正しい英文

⑤ ワンポイントアドバイス

⑥ 間違いの種類
（文法 / 単語 / スペル / 語順 / 意味）

⑦ 差分
（before → after）

不明な単語や意味が取りにくい単語については、勝手に推測して断定しないでください。
その場合は「意味が不明です」「正解文では ○○ です」のように説明してください。
必ず最初から①の形式で回答してください。
前置きや謝罪文は一切出力しないでください。
"""