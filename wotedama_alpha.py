# -*- coding: utf-8 -*-
# kill -9 $(lsof -t -i:12345)
# ベクトル化処理

import MeCab
from transformers import AutoTokenizer, AutoModelForMaskedLM
import torch
import socket
import PySimpleGUI as sg
import threading
import statistics
import re

# GPUの使用
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

# モデルとトークナイザーの読み込み
model_name = "cl-tohoku/bert-base-japanese-whole-word-masking"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForMaskedLM.from_pretrained(model_name)

# MeCabのセットアップ
mecab = MeCab.Tagger("-Owakati")
tagger = MeCab.Tagger()

# 文字種判別
kanji = re.compile('[\u2E80-\u2FDF\u3005-\u3007\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\U00020000-\U0002EBEF]+')

# ソケット通信
M_SIZE = 1024
host = '127.0.0.1'
port = 12345

# ソケットを作成
sock = socket.socket(socket.AF_INET, type=socket.SOCK_STREAM)
print('create socket')

sock.bind((host, port))


class Context:

    def __init__(self):
        self.options = []
        self.sentences = ''
        self.sentences_mask = ''
        threading.Thread(target=self.receive_messages_and_predict_conversions, daemon=True).start()

    ### 文字入力GUI ###
    def create_text_gui(self):
        # レイアウト
        layout = [
            [sg.Multiline(default_text='', size=(150, 50),
                          border_width=2, key='text1',
                          text_color='#000000', background_color='#ffffff')],
            [sg.Button('read', key='bt_read'), sg.Button('clear', key='bt_clear'), sg.Button('Quit', key='bt_quit')]]

        # ウィンドウ作成
        window = sg.Window('jpIMTest06.py', layout, return_keyboard_events=True)

        # イベントループ
        while True:
            event, values = window.read()  # イベントの読み取り（イベント待ち）
            if event is None or event == 'bt_quit' or event == 'q' and ('Meta_L' or 'Meta_R'):
                break
            elif event == 'bt_read' or event == 'r' and ('Meta_L' or 'Meta_R') or event.startswith('Return'):
                print(values['text1'])
                self.sentences = values['text1']
            elif event == 'bt_clear' or event == 'c' and ('Meta_L' or 'Meta_R'):
                window['text1'].update('')
                self.sentences = ''

        # 終了表示
        window.close()

    ###

    ### メッセージの受信と変換候補の予測
    def receive_messages_and_predict_conversions(self):

        # 接続待機
        sock.listen(1)
        print('Waiting for connection')

        # 接続
        conn, cli_addr = sock.accept()
        print(f"Connection established with {cli_addr}")

        # バッファーのリセット
        buffer = ""

        while True:
            try:
                print('Waiting message')

                # メッセージ受信
                message = conn.recv(M_SIZE)
                if not message:
                    print('Connection closed by the client.')
                    break

                buffer += message.decode(encoding='utf-8')

                # メッセージを行毎に処理
                while '\n' in buffer:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    print(f'Received message is [{line}]')

                    # メッセージ判定(入力文or変換候補)
                    if line.startswith("sentences"):
                        print("メッセージ判定sentences")
                        self.sentences_mask = [self.sentences + '[MASK]']
                        print(f"入力文: {self.sentences_mask}")

                    elif line.startswith("candidates"):
                        line = line[11:]
                        line = line.split(',')
                        self.options = line
                        print(f"変換候補: {self.options}")

                        # 予測処理呼び出し
                        print("予測処理を呼び出します")
                        self.predict_masked_word(conn)

            except Exception as error:
                print(f'Error occurred: {error}')
                break

            except KeyboardInterrupt:
                print('\nClosing connection')
                conn.close()
                break

    # 予測
    def predict_masked_word(self, conn):
        print("予測開始")
        # トークナイズ
        inputs = tokenizer(self.sentences_mask, return_tensors="pt")

        # 'token_type_ids' を含むキーを削除
        inputs.pop("token_type_ids", None)

        mask_token_index = torch.where(inputs["input_ids"] == tokenizer.mask_token_id)[1]
        if len(mask_token_index) == 0:
            print("マスクトークンが見つかりませんでした")
            return
        print(f"トークナイズされたデータ: {inputs['input_ids']}")

        # マスクされたトークンの予測
        with torch.no_grad():
            outputs = model(**inputs)

            logits = outputs.logits
            mask_token_logits = logits[0, mask_token_index, :]
            print(f"mask_token_logits: {mask_token_logits.size()}")

        # スコア算出を呼び出し
        scores = self.calculate_scores(mask_token_logits, conn)
        return scores

    # スコア算出
    def calculate_scores(self, mask_token_logits, conn):
        print("スコア算出")
        scores = {}
        for option in self.options:
            # トークナイズしてIDを取得
            option_id = tokenizer.convert_tokens_to_ids(tokenizer.tokenize(option))[0]
            if option_id >= mask_token_logits.size(1):
                print(f"無効なoption_id: {option_id}")
                continue
            # スコアを取得
            scores[option] = mask_token_logits[0, option_id].item()
        print(f"スコア: {scores}")

        # スコアが高い順に並び替える
        sorted_options = sorted(self.options, key=lambda opt: scores.get(opt, -float('inf')), reverse=True)
        print(f"ソート後: {sorted_options}")

        # スコアが最も高い選択肢を選ぶ
        best_option = max(scores, key=scores.get)
        print(f"最適な選択肢: {best_option}")

        # スコアの平均値と標準偏差を算出
        mean_scores = statistics.mean(scores.values())
        sd_scores = statistics.pstdev(scores.values())
        print(f"スコアの平均値: {mean_scores}")
        print(f"スコアの標準偏差: {sd_scores}")

        for option, score in scores.items():
            if score == max(scores.values()):
                scores[option] = score - (sd_scores * 3)
                print(f"スコア修正1: {option}    {score} → {scores[option]}")
        
        for option, score in scores.items():
            if len(option) >= 2:
                if kanji.search(option):
                    scores[option] = score + (len(option)*2)
                    print(f"スコア修正2: {option}    {score} → {scores[option]}")
            else:
                scores[option] = score - 3
                print(f"スコア修正3: {option}    {score} → {scores[option]}")
        
        new_sorted_options = sorted(self.options, key=lambda opt: scores.get(opt, -float('inf')), reverse=True)
        print(f"スコア修正後ソート: {new_sorted_options}")



        # 解析結果を送信
        #conn, cli_addr = sock.accept()
        self.send_candidates_message(conn, new_sorted_options)

    # 解析結果を送信
    def send_candidates_message(self, conn, new_sorted_options):
        print('Send response to Client')
        sorted_options_str = str(new_sorted_options)
        conn.send(sorted_options_str.encode(encoding='utf-8'))
        print(f'Send message is [{sorted_options_str}]')
        print("-" * 50)


###

context = Context()
context.create_text_gui()
