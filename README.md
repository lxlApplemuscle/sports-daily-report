# Sports Daily Report

从懂球帝抓取近期赛事数据，依据赛事重要性规则库筛选内容，并生成中文赛事日报 PDF、单页 PNG 与高分辨率拼接长图。

## 使用方法

```bash
python -u crawlerScore_DoubleSaveVersion.py
```

运行后会生成：

- `output/data/FootballGames.xls`：赛事数据；
- `output/pdf/football_daily_report.pdf`：赛事日报；
- `output/png/football_daily_report_combined.png`：600 DPI 拼接长图。

## 主要文件

- `crawlerScore_DoubleSaveVersion.py`：抓取、筛选、生成与导出流程；
- `赛事重要性规则库.md`：赛事展示等级和重点排序规则；
- `football_daily_report_typography.tex`：日报排版模板；
- `myModel.cls`：LaTeX 视觉样式；
- `FootballGames.xls`：示例赛事数据。

## 依赖

- Python 3；
- XeLaTeX（TeX Live 或 MiKTeX）；
- Poppler（提供 `pdftoppm`）；
- Python 包：`pandas`、`xlwt`、`Pillow`。
