import streamlit as st
import os
import time
from pathlib import Path
import wave
import pyaudio
from pydub import AudioSegment
from audiorecorder import audiorecorder
import numpy as np
from scipy.io.wavfile import write
from langchain.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    MessagesPlaceholder,
)
from langchain.schema import SystemMessage
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from langchain.chains import ConversationChain
import constants as ct

import subprocess
import tempfile
import shutil

def record_audio(audio_input_file_path):
    """
    音声入力を受け取って音声ファイルを作成
    """

    audio = audiorecorder(
        start_prompt="発話開始",
        pause_prompt="やり直す",
        stop_prompt="発話終了",
        start_style={"color":"white", "background-color":"black"},
        pause_style={"color":"gray", "background-color":"white"},
        stop_style={"color":"white", "background-color":"black"}
    )

    if len(audio) > 0:
        audio.export(audio_input_file_path, format="wav")
    else:
        st.stop()

def transcribe_audio(audio_input_file_path):
    """
    音声入力ファイルから文字起こしテキストを取得
    Args:
        audio_input_file_path: 音声入力ファイルのパス
    """

    with open(audio_input_file_path, 'rb') as audio_input_file:
        transcript = st.session_state.openai_obj.audio.transcriptions.create(
            model="whisper-1",
            file=audio_input_file,
            language="en"
        )
    
    # 音声入力ファイルを削除
    os.remove(audio_input_file_path)

    return transcript

def save_to_wav(llm_response_audio, audio_output_file_path):
    """
    一旦mp3形式で音声ファイル作成後、wav形式に変換
    Args:
        llm_response_audio: LLMからの回答の音声データ
        audio_output_file_path: 出力先のファイルパス
    """

    temp_audio_output_filename = f"{ct.AUDIO_OUTPUT_DIR}/temp_audio_output_{int(time.time())}.mp3"
    with open(temp_audio_output_filename, "wb") as temp_audio_output_file:
        temp_audio_output_file.write(llm_response_audio)
    
    audio_mp3 = AudioSegment.from_file(temp_audio_output_filename, format="mp3")
    audio_mp3.export(audio_output_file_path, format="wav")

    # 音声出力用に一時的に作ったmp3ファイルを削除
    os.remove(temp_audio_output_filename)

def change_wav_speed_preserve_pitch(input_wav_path: str, speed: float) -> str:
    """
    ffmpeg の atempo を使って、音程を維持したまま再生速度だけ変更した wav を作成する
    戻り値は変換後 wav のパス
    """
    if speed == 1.0:
        return input_wav_path

    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg が見つかりません。brew install ffmpeg を実行してください。")

    temp_output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    temp_output_path = temp_output_file.name
    temp_output_file.close()

    # atempo は 0.5〜2.0 を1段で扱える
    # 0.6, 0.8, 1.2, 1.5, 2.0 は今回の選択肢ならそのまま使える
    command = [
        "ffmpeg",
        "-y",
        "-i", input_wav_path,
        "-filter:a", f"atempo={speed}",
        temp_output_path
    ]

    result = subprocess.run(command, capture_output=True, text=True)

    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg 音声速度変換エラー: {result.stderr}")

    return temp_output_path    

def play_wav(audio_output_file_path: str, speed: float = 1.0):
    """
    wav ファイルを再生する
    speed を変えても音程が極端に変わらないように ffmpeg の atempo を使う
    """
    converted_file_path = None

    try:
        target_file_path = audio_output_file_path

        if speed != 1.0:
            converted_file_path = change_wav_speed_preserve_pitch(
                input_wav_path=audio_output_file_path,
                speed=speed
            )
            target_file_path = converted_file_path

        wav_file = wave.open(target_file_path, "rb")
        audio_player = pyaudio.PyAudio()

        stream = audio_player.open(
            format=audio_player.get_format_from_width(wav_file.getsampwidth()),
            channels=wav_file.getnchannels(),
            rate=wav_file.getframerate(),
            output=True
        )

        chunk_size = 1024
        data = wav_file.readframes(chunk_size)

        while data:
            stream.write(data)
            data = wav_file.readframes(chunk_size)

        stream.stop_stream()
        stream.close()
        audio_player.terminate()
        wav_file.close()

    finally:
        if converted_file_path and os.path.exists(converted_file_path):
            os.remove(converted_file_path)

        if os.path.exists(audio_output_file_path):
            os.remove(audio_output_file_path)

def create_chain(system_template):
    """
    LLMによる回答生成用のChain作成
    """

    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_template),
        MessagesPlaceholder(variable_name="history"),
        HumanMessagePromptTemplate.from_template("{input}")
    ])
    chain = ConversationChain(
        llm=st.session_state.llm,
        memory=st.session_state.memory,
        prompt=prompt
    )

    return chain

def create_problem_and_play_audio():
    """
    問題生成と音声ファイルの再生
    Args:
        chain: 問題文生成用のChain
        speed: 再生速度（1.0が通常速度、0.5で半分の速さ、2.0で倍速など）
        openai_obj: OpenAIのオブジェクト
    """

    # 問題文を生成するChainを実行し、問題文を取得
    problem = st.session_state.chain_create_problem.predict(input="")

    # LLMからの回答を音声データに変換
    llm_response_audio = st.session_state.openai_obj.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=problem
    )

    # 音声ファイルの作成
    audio_output_file_path = f"{ct.AUDIO_OUTPUT_DIR}/audio_output_{int(time.time())}.wav"
    save_to_wav(llm_response_audio.content, audio_output_file_path)

    # 音声ファイルの読み上げ
    play_wav(audio_output_file_path, st.session_state.speed)

    return problem, llm_response_audio

def create_evaluation():
    """
    ユーザー入力値の評価生成
    """

    llm_response_evaluation = st.session_state.chain_evaluation.predict(input="")

    return llm_response_evaluation