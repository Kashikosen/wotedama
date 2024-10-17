//
//  Untitled.swift
//  wotedama_alpha
//
//  Created by 大川　明日香 on 2024/10/17.
//

import Foundation

extension KeyMap {
    private static let h2z: [String: String] = [
        "!": "！",
        "\"": "”",
        "#": "＃",
        "%": "％",
        "&": "＆",
        "'": "’",
        "(": "（",
        ")": "）",
        "=": "＝",
        "~": "〜",
        "|": "｜",
        "`": "｀",
        "{": "『",
        "+": "＋",
        "*": "＊",
        "}": "』",
        "<": "＜",
        ">": "＞",
        "?": "？",
        "_": "＿",
        "-": "ー",
        "^": "＾",
        "\\": "＼",
        "¥": "￥",
        "@": "＠",
        "[": "「",
        ";": "；",
        ":": "：",
        "]": "」",
        ",": "、",
        ".": "。",
        "/": "・"
    ]

    static func h2zMap(_ text: String) -> String {
        h2z[text, default: text]
    }
}
