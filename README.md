# Shining Force III Scenario 1 繁體中文補丁

這是 **Shining Force III Scenario 1** 的繁體中文補丁專案。公開內容以補丁、中文翻譯資料、建置工具與文件為限；不提供遊戲映像、BIOS、模擬器或英文原始文字。

## 狀態

目前標記為 **B30-R2**。這是仍在驗證中的版本，並非已完整驗證的三部曲翻譯。已知限制與工作狀態見[狀態頁](docs/STATUS.md)。

## 使用方式

需要 Python 3.10 以上版本；工具僅使用 Python 標準函式庫。請自行取得合法可用的遊戲來源映像及音訊資料。來源映像必須是英文 v24，工具會依 SHA-256 檢查，不符合時不能套用。此專案不提供來源映像，也不表示第三方已授權其散布。

```sh
python tools/sf3_patch.py verify
python tools/sf3_patch.py apply --source PATH --audio PATH --out dist/scenario1
```

`build` 使用相同參數，可產生可重現的 R2 建置輸出：

```sh
python tools/sf3_patch.py build --source PATH --audio PATH --out dist/scenario1
```

若要建立本機翻譯編輯上下文（會含本機來源文字），請使用：

```sh
python tools/sf3_patch.py context --source PATH --out build/context.json
```

`--source` 指原始英文 v24 的 MODE1/2352 Track 1 BIN；`--audio` 指同一版的原始 Track 2 BIN。路徑含空格時請加雙引號。輸出資料夾必須尚未存在；省略音軌時只產生 Track 1，不建立雙軌 CUE。提供音軌後，完成的 CUE 可交給 Saturn 模擬器開啟。

本機上下文只可輸出至已排除的 `build/`；不得提交。工具不修改來源映像、模擬器設定或存檔。

## 專案內容

- `patches/`：補丁檔
- `data/scenario1.json`：版本、雜湊與限制資訊
- `translations/`：繁體中文翻譯資料
- `assets/fonts/`：字型資產與授權資訊
- `tools/`：建置與檢查工具

翻譯資料保留文字鍵、中文內容、位置及 `preserve` 控制欄位；英文原文由使用者在本機產生上下文，不隨翻譯資料散布。

詳見[貢獻指南](docs/CONTRIBUTING.md)、[發布紀錄](docs/RELEASES.md)、[儲存庫結構](docs/REPOSITORY.md)及[注意事項](NOTICE.md)。

## 本機檢查

```sh
python -m unittest discover -s tests -v
python tools/check_public_tree.py
```

後者檢查 Git 暫存／追蹤檔案的實際內容；新增檔案後先 `git add` 再執行。GitHub Actions 使用合成資料測試工具與公開檔案，不使用或上傳遊戲映像。

原有 `SS/`、`research/`、`report/`、`milestone1/` 與本機建置輸出保留於工作目錄，但由 `.gitignore` 排除，不會出現在 clone 中。工具及原創文件的 MIT 授權範圍、字型與第三方內容聲明見 [NOTICE.md](NOTICE.md)。
