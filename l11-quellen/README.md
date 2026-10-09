# L11 取证源（Nie zu alt fürs Internet!）

本目录只放**文本类**取证源（体积小、可复算），扫描件图片留在工作区 `skyflyld/l11-quellen/`（12 张 JPG，约 12MB）。

- `ocr/` — 12 张教材照片的逐页 OCR（p01=S.313 … p12=S.326），DS-V4 视觉模型，`--task de`
- `vok/` — 词表页（S.317 / S.318 / S.326）双栏「德文 | 中文」定向 OCR
- `lektion11-ppt-text.txt` — 教师课件 59 页文本（`officecli view <pptx> text` 导出），本单元的**答案源**
- `check_verbatim_l11.py` — 逐字门：`l11-data.json` 里每条德文必须能在上述源中逐字找到
  （教材带填空横线的句子按空位分段校验；句首大小写差异单列放行）

```bash
python3 l11-quellen/check_verbatim_l11.py        # 退出码 0 = 全部命中
```
