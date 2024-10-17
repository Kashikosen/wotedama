//
//  LogMessage.swift
//  wotedama_alpha
//
//  Created by 大川　明日香 on 2024/10/17.
//

import Foundation

func logMessage(logContents: String) {
    // ログメッセージの外部ファイル保存
    // ログ用日時
    let logTimeFormatter = DateFormatter()
    logTimeFormatter.timeStyle = .medium
    logTimeFormatter.dateStyle = .medium
    logTimeFormatter.locale = Locale(identifier: "ja_JP")
    let now = Date()
    
    // ログ用メッセージ
    let logMessage = "\(logTimeFormatter.string(from: now)): \(logContents)\n"
    
    if let dir = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first {
        let fileURL = dir.appendingPathComponent("wotedamaLog.txt")
        
        if FileManager.default.fileExists(atPath: fileURL.path) {
            // 既存のファイルがある場合は追記モードで開く
            do {
                let fileHandle = try FileHandle(forWritingTo: fileURL)
                fileHandle.seekToEndOfFile()
                if let data = logMessage.data(using: .utf8) {
                    fileHandle.write(data)
                }
                fileHandle.closeFile()
            } catch {
                NSLog("ログファイルへの追記に失敗しました: \(error)")
            }
        } else {
            // ファイルが存在しない場合は新規作成
            do {
                try logMessage.write(to: fileURL, atomically: true, encoding: .utf8)
            } catch {
                NSLog("ログファイルの作成に失敗しました: \(error)")
            }
        }
    }
}

