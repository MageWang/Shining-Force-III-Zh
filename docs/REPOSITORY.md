# 公開儲存庫與本機資料

公開儲存庫以單一 Scenario 1 B30-R2 BPS 補丁為基準；目前沒有第二、三部補丁。

```text
README.md                使用方式
LICENSE / NOTICE.md      工具及第三方授權範圍
patches/scenario1/       只有 BPS，不含成品光碟
translations/scenario1/  34 份有效譯文，去除重複覆寫及英文原文
data/                   版本清單、名詞字典、固定姓名字碼
assets/fonts/           兩套必要 BDF 與完整隨附授權
tools/                  獨立套用、重建及公開內容檢查工具
tests/                  不依賴遊戲的合成測試
.github/workflows/      不需遊戲映像的 CI
docs/                   狀態、貢獻與發布文件
```

## 已完成的小任務（2026-10-30）

- [x] 盤點並分離公開內容；舊目錄不刪除、不加入版本控制。
- [x] 匯出 5,535 筆去重有效項目，其中 210 筆以 `preserve: true` 從本機來源保留原文。
- [x] 攜帶必要字型及 Ark Pixel、Fusion Pixel、Cubic 11、Galmuri 授權聲明。
- [x] 將建置程式從研究工具拆出，只使用 Python 標準函式庫及公開資料。
- [x] 獨立重建 82 個文字庫、映像與 BPS，與固定 R2 雜湊逐一相符。
- [x] 實際套用 BPS，確認輸出與重建結果相同，保留來源不變。
- [x] 加入 Git 暫存內容檢查，避免只檢查工作目錄而漏掉已暫存的舊資料。
- [x] 由暫存檔案匯出乾淨目錄，獨立重建的映像與補丁完全相同，資料／上下文與合成測試通過。
- [ ] 遠端儲存庫網址確認後，推送至指定公開儲存庫。

## 本機保留項目

`SS/` 內的遊戲、BIOS、模擬器，`research/` 的研究工具、歷次整合映像、啟動器與存檔，`report/` 的截圖，以及舊 `milestone1/` 均由根目錄白名單排除。`build/`、`dist/`、IDE 暫存及根目錄草稿也不納入。未移動現有遊戲或使用者存檔。

新的開發資料應放在公開目錄；私有測試輸入／輸出請放 `build/`。新增根目錄項目時，須同時檢查 `.gitignore` 與 `tools/check_public_tree.py` 的白名單。即使 `git add -f` 強制加入常見遊戲檔或存檔，檢查器也會拒絕。

## 發布流程

1. 執行 README 所列測試及雜湊檢查。
2. 於本機使用指定英文 v24 Track 1／2 重建，確認來源保持不變。
3. 完成該版本的遊玩驗證並更新已知問題、版本清單與發布紀錄。
4. `git add` 後執行 `python tools/check_public_tree.py`，檢查 `git diff --cached`。
5. 提交原始碼及 BPS，再推送至指定遠端；Release 附件只提供 BPS 與必要說明／授權，不附建置出的 BIN／CUE、存檔或 BIOS。

本機重建的成功不等於已完成全遊戲測試。驗證缺口仍須保留於[狀態頁](STATUS.md)。
