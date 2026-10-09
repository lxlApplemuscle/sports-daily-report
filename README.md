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
- `球队队徽库.json`：球队名称、别名与队徽文件的映射；
- `football_daily_report_typography.tex`：日报排版模板；
- `myModel.cls`：LaTeX 视觉样式；
- `FootballGames.xls`：示例赛事数据。

## 依赖

- Python 3；
- XeLaTeX（TeX Live 或 MiKTeX）；
- Poppler（提供 `pdftoppm`）；
- Python 包：`pandas`、`xlwt`、`Pillow`。

## 维护队徽库

队徽不写在 Python 代码中。将图片放入 `logo/` 下的分类目录后，在 `球队队徽库.json` 对应赛事分区的 `clubs` 数组新增一项即可：

```json
{"id": "real-madrid", "logo": "la_liga/real-madrid.png", "aliases": ["皇家马德里", "皇马", "Real Madrid"]}
```

`logo` 路径相对于 `logo/`。程序会将比赛数据中的球队名称统一为 Unicode 标准形式，忽略大小写、空格与常见分隔符，并优先匹配较长别名；例如 `Manchester United`、`MAN UNITED` 和 `曼联` 都可命中同一队徽。未收录的球队保持纯文字，避免误配。