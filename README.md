# HistCite 工具的 Python 实现

[![PyPI](https://img.shields.io/pypi/v/histcite-python)](https://pypi.org/project/histcite-python)
[![Supported Versions](https://img.shields.io/pypi/pyversions/histcite-python.svg)](https://pypi.org/project/histcite-python)
[![Codecov](https://codecov.io/gh/doublessay/histcite-python/graph/badge.svg?token=99V9E2CI1H)](https://codecov.io/gh/doublessay/histcite-python)
[![License](https://img.shields.io/pypi/l/histcite-python.svg)](https://github.com/doublessay/histcite-python/blob/main/LICENSE)

由于原引文分析工具 [HistCite](https://support.clarivate.com/ScientificandAcademicResearch/s/article/HistCite-No-longer-in-active-development-or-officially-supported) 已停止维护，目前国内使用较多的为中科大某同学 (知乎昵称 [Tsing](https://www.zhihu.com/people/wq123)) 在源程序基础上修复的版本 [HistCite Pro](https://zhuanlan.zhihu.com/p/20902898)，仅适用于 `Windows` 平台，存在较大限制。借助 [pandas 2.0](https://pandas.pydata.org/docs/dev/index.html) 和可视化工具 [Graphviz](https://graphviz.org)，本工具实现了 `HistCite` 的核心功能，可以跨平台使用，同时拓展了对 [其他数据源](#数据准备) 的支持。

核心功能：
- 生成引文网络图；
- 生成统计数据，包括文献、作者、机构、文献来源、作者关键词等分析对象；

工具对比：
|对比项|histcite-python|histcite pro|
|:----|:----|:----|
|是否开源|是|否|
|是否跨平台|是|否，仅限 Windows|
|是否支持其他数据源|是|否，仅限 Web of Science|
|是否提供前端界面|否|是，可交互|
|引文网络图|矢量图，比较清晰|位图，比较模糊|

## 快速开始
```console
$ pip install histcite-python
```

## 数据准备
|数据来源|下载说明|原始文件名|
|:----|:----|:----|
|Web of Science|`核心合集`，格式选择 `Tab delimited file` 或 `Plain text file`，导出内容选择 `Full Record and Cited References` 或者是 `Custom selection`，全选字段。|`savedrecs*.txt`|
|CSSCI|从 `CSSCI数据库` 正常导出即可。|`LY_*.txt`|
|Scopus|网站语言切换到英文，格式选择 `CSV` 文件，导出字段需要额外勾选 `Author keywords` 和 `Include references`，或者直接全选字段。|`scopus*.csv`|

> [!WARNING]
> 文件下载后不要重命名(会根据文件名识别有效的数据文件)，把下载的所有文件放在一个单独的文件夹内。

## 使用方法
1. 使用命令行工具
```console
$ histcite -h
usage: histcite [-h] (--top TOP | --threshold THRESHOLD | --node NODE) [--disable_timeline] folder_path {wos,cssci,scopus}

A Python interface for histcite.

positional arguments:
  folder_path           Folder path of downloaded data.
  {wos,cssci,scopus}    Data source.

options:
  -h, --help            show this help message and exit
  --top                 Top N nodes with the highest LCS.
  --threshold           Nodes with LCS greater than threshold.
  --disable_timeline    Whether to disable timeline.
```

```console
$ histcite /Users/.../Downloads/dataset wos --top 50
```

> [!NOTE]
> 生成的结果保存在 `folder_path` 下的 `result` 文件夹内，包含
> - 引文网络图节点信息表 graph_node_info.xlsx
> - 引文网络图的数据文件 graph.dot
>     - 借助 [Graphviz 在线编辑器](http://magjac.com/graphviz-visual-editor/) 或下载到本地的 [Graphviz](https://graphviz.org/) 生成引文网络图。

引文网络图示例：

![](https://raw.githubusercontent.com/doublessay/histcite-python/main/examples/graph.svg)

对应的节点信息如下(以 CSSCI 数据源为例)：
| |AU|TI|PY|SO|LCS|
|:----|:----|:----|:----|:----|:----|
|314|王世伟|论智慧图书馆的三大特点|2012|中国图书馆学报|76|
|316|董晓霞; 龚向阳; 张若林; 严潮斌|智慧图书馆的定义、设计以及实现|2011|现代图书情报技术|37|
|317|王世伟|未来图书馆的新模式——智慧图书馆|2011|图书馆建设|59|
|...| | | | | |

2. 使用 Jupyter Notebook，可以自定义更多参数，导出描述性统计数据，请查看 [demo.ipynb](demo.ipynb)

## 字段说明
|Field Name|Description|
|:----|:----|
|`GCS`|Global Citation Score, 表示一篇文献在文献数据库中的总被引次数|
|`LCS`|Local Citation Score, 表示一篇文献在本地文献集中的被引次数|
|`GCR`|Global Cited References, 表示一篇文献的参考文献数量|
|`LCR`|Local Cited References, 表示一篇文献的参考文献在本地文献集中的数量|
|`T*` |Total score, e.g. TLCS = Total Local Citation Scores.|
|`Recs`|Count of Records|
|`FAU`|First Author|
|`CAU`|Corresponding Authors|
|`AU`|Authors|
|`CO`|Country of Authors|
|`C1`|Addresses|
|`C3`|Author Affiliations|
|`RP`|Reprint Address|
|`I2`|Institution with Subdivision|
|`TI`|Article Title|
|`SO`|Source Title|
|`DT`|Document Type|
|`DE`|Author Keywords|
|`CR`|Cited References|
|`NR`|Cited Reference Count|
|`TC`|Times Cited Count|
|`PY`|Publication Year|
|`VL`|Volume|
|`IS`|Issue|
|`BP`|Start Page|
|`EP`|End Page|
|`DI`|DOI|
|...|[Please refer to Web of Science fields.](https://webofscience.help.clarivate.com/en-us/Content/export-records.htm)|

## FAQ
1. 为什么生成的引文网络图时间线会错乱？
- 节点位置由 Graphviz 自动调整，节点数量较少时容易出现这一问题。可以通过设置参数隐藏时间线。

2. 是否存在其他类似的工具？
- [CiteSpace](https://citespace.podia.com/)
- [CitNetExplorer](https://www.citnetexplorer.nl/)
- [VOSviewer](https://www.vosviewer.com/)
- [Connected Papers](https://www.connectedpapers.com/)
- [Litmaps](https://app.litmaps.com/)
