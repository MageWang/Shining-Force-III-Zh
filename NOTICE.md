# 注意事項與第三方資產

本儲存庫提供 Shining Force III Scenario 1 的補丁與相關工具，不包含遊戲光碟映像、BIOS、模擬器或英文遊戲腳本。使用者須自行準備英文 v24 來源；`data/scenario1.json` 記錄來源雜湊：

`e41ce410d792064cda2421d16a96a613a885f814a169cc5515eb0aff4cbed147`

此雜湊用於辨識建置基底。原遊戲由 SEGA／Camelot 製作；英文基底來自 [Shining Force III Translation Project](https://sf3trans.shiningforcecentral.com/)。本專案與上述權利人及英文團隊無隸屬關係，未將其素材視為本專案可授權的內容。

## 授權範圍

`LICENSE` 的 MIT 授權適用於本專案原創工具、測試及文件。遊戲內容、衍生翻譯、補丁中的遊戲差分資料與商標不在此 MIT 授權範圍；字型另依隨附 OFL 授權。公開 Git 儲存庫不會改變第三方素材的權利歸屬。

## 字型

- Ark Pixel：`assets/fonts/ArkPixel/ark-pixel-12px-monospaced-zh_tw.bdf`。上游為 [TakWolf/ark-pixel-font](https://github.com/TakWolf/ark-pixel-font)，版權標示為 Copyright (c) 2021, TakWolf。隨附 SIL Open Font License 1.1，見 `assets/fonts/ArkPixel/OFL.txt`。
- Fusion Pixel：`assets/fonts/FusionPixel/fusion-pixel-12px-monospaced-zh_tw.bdf`。本地來源記錄指向 [2026.10.25 發行頁](https://github.com/TakWolf/fusion-pixel-font/releases/tag/2026.10.25)，原始資產為 [BDF ZIP](https://github.com/TakWolf/fusion-pixel-font/releases/download/2026.10.25/fusion-pixel-font-12px-monospaced-bdf-v2026.10.25.zip)。隨附 SIL Open Font License 1.1、來源記錄及上游授權文件，見 `assets/fonts/FusionPixel/`。

字型檔應與對應授權及來源聲明一同散布；請保留 Fusion Pixel 內附的 Ark Pixel、Cubic 11 及 Galmuri 授權文件。

## 專案狀態

B30-R2 尚非完整驗證的三部曲版本。已知驗證缺口見 [docs/STATUS.md](docs/STATUS.md)。
