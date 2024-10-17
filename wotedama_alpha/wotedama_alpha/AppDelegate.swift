//
//  AppDelegate.swift
//  wotedama_alpha
//
//  Created by 大川　明日香 on 2024/10/17.
//

import Cocoa
import InputMethodKit
import KanaKanjiConverterModuleWithDefaultDictionary
import SwiftUI
import Foundation

// Necessary to launch this app
class NSManualApplication: NSApplication {
    let appDelegate = AppDelegate()

    override init() {
        super.init()
        self.delegate = appDelegate
    }

    required init?(coder: NSCoder) {
        // No need for implementation
        fatalError("init(coder:) has not been implemented")
    }
}

@main
class AppDelegate: NSObject, NSApplicationDelegate {
    var server = IMKServer()
    var candidatesWindow = IMKCandidates()
    @MainActor var kanaKanjiConverter = KanaKanjiConverter()

    func applicationDidFinishLaunching(_ notification: Notification) {
        // Insert code here to initialize your application
        self.server = IMKServer(name: Bundle.main.infoDictionary?["InputMethodConnectionName"] as? String, bundleIdentifier: Bundle.main.bundleIdentifier)
        self.candidatesWindow = IMKCandidates(server: server, panelType: kIMKSingleColumnScrollingCandidatePanel, styleType: kIMKMain)
        NSLog("tried connection")

        logMessage(logContents: "ログテスト")
    }

    func applicationWillTerminate(_ notification: Notification) {
        // Insert code here to tear down your application
    }
}
