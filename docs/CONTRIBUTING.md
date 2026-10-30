# 貢獻指南

感謝協助改善繁體中文補丁。請將變更限於可公開的工具、中文翻譯資料、文件及必要的授權資產。

## 翻譯資料

翻譯資料只應保存文字鍵、繁體中文翻譯、位置資訊，以及必要的控制欄位（例如 `preserve: true`）。不要將英文原始文字複製進翻譯檔或提交本機產生的上下文檔；英文文字應由使用者本機來源建立。

保留鍵名與位置資訊，避免改動無關記錄。若某一欄位必須原樣保留，使用既有 `preserve` 慣例，並說明原因。

## 建置與驗證

使用 Python 3.10 以上版本及標準函式庫：

```sh
python tools/sf3_patch.py verify
python tools/sf3_patch.py apply --source PATH --audio PATH --out dist/scenario1
python tools/sf3_patch.py build --source PATH --audio PATH --out dist/scenario1
python tools/sf3_patch.py context --source PATH --out build/context.json
```

`build` 用於嚴格可重現的 R2 建置。`context` 產生含本機英文來源的編輯上下文；輸出只供本機使用，不可提交。請以個人路徑取代 `PATH`，不可加入硬編碼的使用者電腦路徑。

目前 `build` 會逐庫及逐映像對照固定 R2 雜湊。修改譯文後若產物不同，工具會拒絕當作 R2 發布；新版本需經覆核並更新版本清單、補丁及雜湊。`data/terminology.json` 用於人工校對與統一名詞，現有公開譯文已套用 R2 字典結果，建置不會暗中改寫譯文或姓名字碼表。

提交前執行 `python -m unittest discover -s tests -v`、`python tools/sf3_patch.py verify`，再於 `git add` 後執行 `python tools/check_public_tree.py`。僅有合成資料的測試可交由公開 CI 執行；實際映像重建與遊玩結果記錄於本機後，在文件中彙整結論。

在提交前檢視差異，確認沒有遊戲來源、BIOS、模擬器檔案、存檔、模擬器狀態、日誌、截圖、英文原文或本機建置輸出。勿將個人測試結果表述為完整三部曲驗證。

## 授權與來源

保留第三方字型的授權與來源檔案，並維持其與字型資產的對應。不得以專案文件暗示遊戲或英文腳本的散布已獲授權；本專案不提供此類授權判斷。
