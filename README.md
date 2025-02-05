# HistCite工具的Python实现

[![PyPI](https://img.shields.io/pypi/v/histcite-python)](https://pypi.org/project/histcite-python)
[![Supported Versions](https://img.shields.io/pypi/pyversions/histcite-python.svg)](https://pypi.org/project/histcite-python)
[![Codecov](https://codecov.io/gh/doublessay/histcite-python/graph/badge.svg?token=99V9E2CI1H)](https://codecov.io/gh/doublessay/histcite-python)
[![License](https://img.shields.io/pypi/l/histcite-python.svg)](https://github.com/doublessay/histcite-python/blob/main/LICENSE)

由于原引文分析工具 [HistCite](https://support.clarivate.com/ScientificandAcademicResearch/s/article/HistCite-No-longer-in-active-development-or-officially-supported) 已停止维护，目前国内使用较多的为中科大某同学 (知乎昵称[Tsing](https://www.zhihu.com/people/wq123)) 在源程序基础上修复的版本 [HistCite Pro](https://zhuanlan.zhihu.com/p/20902898)，仅适用于 `Windows` 平台，存在较大限制。借助 [pandas 2.0](https://pandas.pydata.org/docs/dev/index.html) 和可视化工具 [Graphviz](https://graphviz.org)，本工具实现了 `HistCite` 的核心功能，可以跨平台使用，同时拓展了对 [其他数据源](#数据准备) 的支持。

核心功能：
- 生成引文网络图；
- 生成统计数据，包括文献、作者、机构、文献来源、作者关键词等分析对象；
- 发现不在本地文献集中、但被本地文献集引用较多的文献，即本次文献获取过程忽略的重要文献；

工具对比：
|对比项|histcite-python|histcite pro|
|:----|:----|:----|
|是否开源|是|否|
|是否跨平台|是|否，仅限 Windows|
|是否支持其他数据源|是|否，仅限 Web of Science|
|是否提供前端界面|否|是|
|引文网络图|矢量图，比较清晰|位图，比较模糊|

## 快速开始
```console
pip install histcite-python
```

## 数据准备
|数据来源|下载说明|默认文件名|
|:----|:----|:----|
|Web of Science|`核心合集`，格式选择 `Tab delimited file/制表符分隔文件`，导出内容选择 `Full Record and Cited References/全记录与引用的参考文献` 或者是 `Custom selection/自定义选择项`，全选字段。|`savedrecs*.txt`|
|CSSCI|从 `CSSCI数据库` 正常导出即可。|`LY_*.txt`|
|Scopus|格式选择 `CSV` 文件，导出字段需要额外勾选 `Author keywords` 和 `Include references`，或者直接全选字段。|`scopus*.csv`|

> [!WARNING]
> 文件下载后不要重命名(会根据文件名识别有效的题录数据文件)，把下载的所有文件放在一个单独的文件夹内。

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
$ histcite /Users/.../Downloads/dataset wos --top 100 --disable_timeline
```

> [!NOTE]
> 生成的结果保存在 `folder_path` 下的 `result` 文件夹内，包含
> - 描述统计表 descriptive_statistics.xlsx
> - 引文网络图节点信息表 graph_node_info.xlsx
> - 引文网络图的数据文件 graph.dot
>     - 借助 [Graphviz在线编辑器](http://magjac.com/graphviz-visual-editor/) 或下载到本地的 [Graphviz工具](https://graphviz.org/) 生成引文网络图。

引文网络图示例：

![](https://raw.githubusercontent.com/doublessay/histcite-python/main/examples/graph.svg)

对应的节点信息如下(以CSSCI数据源为例，不同文献数据库的节点信息字段存在差异)：
| |AU|TI|PY|SO|LCS|
|:----|:----|:----|:----|:----|:----|
|55|张坤; 查先进|我国智慧图书馆的发展沿革及构建策略研究|2021|国家图书馆学刊|6|
|60|石婷婷; 徐建华; 张雨浓|数字孪生技术驱动下的智慧图书馆应用场景与体系架构设计|2021|情报理论与实践|7|
|63|卢小宾; 宋姬芳; 蒋玲; 洪先锋; 刘静; 张薷|智慧图书馆建设标准探析|2021|中国图书馆学报|9|
|81|程焕文; 钟远薪|智慧图书馆的三维解析|2021|图书馆论坛|10|
|86|段美珍; 初景利; 张冬荣; 解贺嘉|智慧图书馆的内涵特点及其认知模型研究|2021|图书情报工作|7|
|...| | | | | |

2. 使用 Jupyter，比命令行更加灵活，可以自定义更多参数，查看 [demo.ipynb](demo.ipynb)

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
|`AU`|Authors or Inventors|
|`TI`|Article Title|
|`SO`|Source Title|
|`DT`|Document Type|
|`FU`|Funding Orgs|
|`CR`|Cited References|
|`DE`|Author Keywords|
|`C3`|Author Affiliations|
|`NR`|Cited Reference Count|
|`TC`|Times Cited Count|
|`J9`|Journal Abbreviation|
|`PY`|Publication Year|
|`VL`|Volume|
|`IS`|Issue|
|`BP`|Start Page|
|`EP`|End Page|
|`DI`|DOI|
|...|[Please refer to Web of Science fields.](https://webofscience.help.clarivate.com/en-us/Content/export-records.htm)|

## FAQ
1. 为什么生成的引文网络图时间线会错乱？
- Graphviz 会自动调整节点位置，节点数量过少时容易出现这一问题。可以通过设置参数来关闭时间线。

2. 为什么有些学科领域的参考文献解析的错误率较高？
- 不同学科领域的主要引用来源不同，期刊引用格式要求不同，导致不同数据库、不同学科领域的引文格式与解析方式差异较大。您可以查看解析后的参考文献表 (refs_df)，如果错误率较高，或者发现具有某种特征的参考文献均出现了解析错误，欢迎提交 [Feature Request](https://github.com/doublessay/histcite-python/issues)，我们会尽快修复。

3. 想要分析其他数据源的文献元数据？
- 该数据源能够导出文献的参考文献或引文数据。如果满足这一条件的话，欢迎提交 [Feature Request](https://github.com/doublessay/histcite-python/issues)，我们会尽快支持。

4. 是否存在其他类似的工具？
- [CiteSpace](https://citespace.podia.com/)
- [CitNetExplorer](https://www.citnetexplorer.nl/)
- [Connected Papers](https://www.connectedpapers.com/)
- [Litmaps](https://app.litmaps.com/)
