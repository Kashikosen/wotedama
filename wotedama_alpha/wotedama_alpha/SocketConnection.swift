//
//  SocketConnection.swift
//  wotedama_alpha
//
//  Created by 大川　明日香 on 2024/10/17.
//

import SwiftUI
import Network
import InputMethodKit

class SocketConnection {
    let host: NWEndpoint.Host = "127.0.0.1"
    let port: NWEndpoint.Port = 12345
    var connection: NWConnection?
    var reconnectCount = 0
    
    //クラス外での受信結果（変換）を処理するためのクロージャ
    var candidateMessage: ((String) -> Void)?
    
    //初期化時のみ接続
    init() {
        connect()
    }
    
    //接続
    func connect() {
        connection = NWConnection(host: host, port: port, using: .tcp)
        connection?.stateUpdateHandler = { newState in
            switch newState {
            case .ready:
                logMessage(logContents: "接続が確立されました")
                self.receiveMessage()
            case .failed(let error):
                logMessage(logContents: "接続に失敗しました: \(error)")
                self.reconnect()
                
                //再接続回数が3回を超えたらbreak
                if self.reconnectCount > 3 {
                    break
                }
                
            default:
                break
            }
        }
        connection!.start(queue: .global())
    }
    
    //再接続
    func reconnect() {
        logMessage(logContents: "再接続")
        DispatchQueue.global().asyncAfter(deadline: .now() + 5) {
            self.reconnectCount += 1
            self.connect()
        }
    }
    
    //送信
    func sendMessage(inputMessage: String) {
        guard let payload = inputMessage.data(using: .utf8) else {
            logMessage(logContents: "文字列のエンコードに失敗しました")
            return
        }
        connection?.send(content: payload, completion: .contentProcessed({ sendError in
            if let error = sendError {
                logMessage(logContents: "送信エラー: \(error)")
            } else {
                logMessage(logContents: "メッセージ送信: \(inputMessage)")
            }
        }))
    }
    
    //受信
    func receiveMessage() {
        connection?.receive(minimumIncompleteLength: 1, maximumLength: 65535) { [weak self] (data: Data?, context: NWConnection.ContentContext?, isComlete: Bool, error: NWError?) in
            if let data = data, !data.isEmpty {
                let receivedMessage = String(data: data, encoding: .utf8) ?? "不明なメッセージ"
                logMessage(logContents: "メッセージ受信: \(receivedMessage)")
                
                //セマフォ解放
                gotCandidatesSemaphore.signal()
                
                //クロージャ呼び出し
                self?.candidateMessage?(receivedMessage)
                
                //継続して受信
                self?.receiveMessage()
                
            } else if let error = error {
                logMessage(logContents: "受信エラー: \(error.localizedDescription)")
                
                //少し待ってから再接続
                DispatchQueue.global().asyncAfter(deadline: .now() + 1.0) {
                    self?.receiveMessage()
                }
            }
        }
    }
}
