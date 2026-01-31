<div align="center">

<img src="docs/assets/logo-bilibili-rater.png" width="500px" alt="logo">

# bilibili-rater

[![PyPI - License](https://img.shields.io/pypi/l/bilibili-rater)](https://github.com/NearlyHeadlessJack/bilibili-rater/blob/main/LICENSE)
[![PyPI - Version](https://img.shields.io/pypi/v/bilibili-rater?color=blue)](https://pypi.org/project/bilibili-rater/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bilibili-rater)](https://pypi.org/project/bilibili-rater/)
[![Test](https://github.com/NearlyHeadlessJack/bilibili-rater/actions/workflows/Publish.yml/badge.svg?branch=dev)](https://github.com/NearlyHeadlessJack/bilibili-rater/actions/workflows/Publish.yml)
[![GitHub Tag](https://img.shields.io/github/v/tag/NearlyHeadlessJack/bilibili-rater)](https://github.com/NearlyHeadlessJack/bilibili-rater/tags)

**⚠️使用注意: 请勿使用本项目用于违反法律或违反社区规则的行为, 例如刷屏、辱骂、广告推广等。**  

**本项目基于[bilibili-api](https://github.com/Nemo2011/bilibili-api)开发, ⚠️⚠️务必注意B站官方的反爬虫系统, 设置合理的请求间隙。**

**本项目使用[GPLv3](https://gnu.ac.cn/licenses/gpl-3.0.html#license-text)许可证, 仅供个人学习使用, 请勿用于商业用途。**  

</div>

仓库地址: https://github.com/NearlyHeadlessJack/bilibili-rater  
Python>=3.10  
安装最新稳定版    
```commandline
pip install bilibili-rater

// 使用阿里云镜像加速
pip install -i https://mirrors.aliyun.com/pypi/simple bilibili-rater
```
安装开发版本  
[![PyPI - Version](https://img.shields.io/pypi/v/bilibili-rater?pypiBaseUrl=https%3A%2F%2Ftest.pypi.org&label=TestPyPI)](https://test.pypi.org/project/bilibili-rater/)

```shell
pip install --index-url https://test.pypi.org/simple/ bilibili-rater==0.x.x.dev13
```

---

## 简介
bilibili-rater 适用于在B站搬运的美剧、动画等视频下, 按预置规则获取对应imdb信息, 并自动评论**季**、**集**、**标题**和**评分**等信息。

设置自动化后, 可24h监控指定up主的最新视频并提供评分信息, 供其他观众参考。

<img src="docs/assets/example_1.png" width="300px" alt="示例">

## Feature
- 自定义“季-集”信息的爬取方式, 可通过视频简介的固定模式来获取。
- 可以获取当期节目在整季中的评分排名。
- 可以获取本季平均分和评分中位数。
- 可以获取本集的首播时间。
- 基于[bilibili-api](https://github.com/Nemo2011/bilibili-api)开发, 对B站的访问高可靠性。
- 提供多种imdb数据获取方式, 支持使用[imdbinfo](https://github.com/tveronesi/imdbinfo)直接从imdb网站进行抓取, 也支持
使用[omdbapi](http://www.omdbapi.com/)从第三方数据库获取imdb评分信息。

## 适合用户
- 影视搬运类up主本人。
- 热心观众, 但需要与up主沟通好“季-集”信息获取模式。

## FAQ

+ 本项目可以直接识别某个视频是哪个节目, 以及具体某一季、某一集吗？
    + 不可以, 是哪个节目需要在脚本中设定`resource_id`。“季-集”信息需要视频上传者提供获取模式, 本项目只提供从视频简介中抓取对应“季-集”数据的接口
`handler`及其抽象类`class SeasonEpisodeHandler(ABC)`。
用户可以设置自定义的模式匹配方法。  
+ imdb信息是自动获取的吗？ 
    + 是的, 首先从b站视频获取到“季-集”信息后, 会使用脚本中提供的抓取器(`fetcher`), 自动获取imdb信息。
+ 可以使用豆瓣评分吗？
    + 不可以, 因为豆瓣没有单集评分功能。
+ omdbapi和直接获取imdb的信息有什么区别？
    + omdbapi胜在稳定，不受制于imdb可能出现的反爬虫策略更新。但是omdbapi方式无法获取排名、平均分和中位数信息，且评分数据并不是最新的。
# 使用教程与示例
## 1. 确定你要抓取的up主与节目信息
up主通过B站数字`uid`确定, 节目信息通过imdb编号确定。  
例如要抓取up主[龙三条](https://space.bilibili.com/5024187), `uid`为`5024187`。  
我要抓取的节目为[《恶搞之家》](https://www.imdb.com/title/tt0182576/), imdb编号为`tt0182576`。   
> imdb影视节目的编码一般为`tt`开头。可通过[imdb网站](https://www.imdb.com)对应页面的URL看到。   

> [!NOTE]
> 连载节目请获取**根节目**的imdb代码, 不要使用季或集的imdb代码, 他们是独立的。

> 连载节目的根imdb代码可通过[imdb网站](https://www.imdb.com)搜索节目名, 进入根节目的页面, 通过URL看到。例如《恶搞之家》https://www.imdb.com/title/tt0182576/ 的根imdb编号为`tt0182576`。  

## 2. 获取用于发表评论账号的credentials

获取用于评论的账号credentials, 具体方法请直接参考[bilibili-api使用文档](https://nemo2011.github.io/bilibili-api/#/get-credential)。

这里一共需要五个值：`sessdata`, `bili_jct`, `buvid3`, `buvid4`, `dedeuserid`。

## 3. 创建imdb信息获取器`fetcher`
程序运行时需要`fetcher`才能获取imdb信息, 当前版本内置两个`fetcher`, 分别为`DirectFetcher`, `OmdbFetcher`。

| `fetcher`       | 原理                     | 适用情形        |
|-----------------|------------------------|-------------|
| `DirectFetcher` | 直接构造请求从imdb官网获取最新信息    | 适用于大多数情况    |
| `OmdbFetcher`   | 通过第三方数据库omdb提供的api获取信息 | imdb无法进行爬虫时 |

> [!IMPORTANT]
> `OmdbFetcher`需要提前申请api key。

- [omdb网站](http://omdbapi.com/apikey.aspx)提供了免费、快速的api, 可以获得imdb的数据。
- 输入邮箱并提交后, 邮件会收到api key。**请点击邮件中的激活链接, 否则api key无法使用**


## 4. 创建Python脚本
创建一个Python文件, 并添加以下内容：
```python
import bilibili_rater
from bilibili_api import Credential
import asyncio

credential = Credential(
    sessdata="",
    bili_jct="",
    buvid3="",
    buvid4="",
    dedeuserid="",
)


fetcher_omdb = bilibili_rater.OmdbFetcher(api_key="xxxx",
                                          is_show_title=True)
fetcher_direct = bilibili_rater.DirectFetcher(is_show_ranking=True,
                                              is_show_title=True,
                                              is_show_release_date=True,
                                              is_show_average=True,
                                              is_show_median=True)


job = bilibili_rater.BilibiliRater(
    uploader_uid=591331248,  # up主 uid
    credential=credential,  
    handler=bilibili_rater.OnlyNumberHandler.handle,  # “季-集”信息的解包方式
    resource_id="tt0397306",  # 根节目的imdb编号
    resource_cn_name="美国老爹",  #  最终显示在评论中的节目中文名
    imdb_fetchers=[fetcher_direct, fetcher_omdb],  # 使用的imdb信息获取器
)

asyncio.run(job.run())
```
其中, `handler`的设置详情请见[自定义handler](#自定义handler)。

`imdb_fetchers`接收一个`fetcher`列表。程序会依次使用列表中的`fetcher`来获取imdb信息。    
若前一个`fetcher`获取失败, 程序会自动尝试使用下一个`fetcher`。  
因此建议将`OmdbFetcher`放在最后, 作为最后的获取方式运行。


## 5. 运行脚本或设置自动化
可以直接运行脚本  
```commandline
python script.py
```
如果一切正常, 会提示评论发送成功。

但是这样, 脚本只会运行一次。

### 自动化

#### 使用`cron`
- 1. 创建一个运行脚本`run-bilibili-rater-1.sh`
```shell
#!/bin/bash
python /path/to/script.py
```
- 2. 添加定时任务
```shell
crontab -e

// 在新页面里面添加一行
*/10 0 * * * /path/to/run-bilibili-rater-1.sh
```
这样脚本会每10分钟运行一次。  
关于`cron`语法, 请参见[教程](https://www.runoob.com/linux/linux-comm-crontab.html), 
或直接使用[生成器](https://cron.ciding.cc/)。

### 多任务运行
有些时候我们并不会只关注一个up主的某个节目, 而是关注多个up主或者多个节目。这样需要分别编写Python脚本与对应的运行脚本。  
对于同一个up主的不同节目, 请不要使用相同的handler。否则会被解析为同一个节目。  
例如《辛普森一家》使用简介第一行用"S03E05"形式来标注“季-集”信息, 《恶搞之家》使用简介第一行用"10-4"来标注“季-集”信息。  

使用不同的handler可以区分两者, 不至于误将一个节目解析为另一个节目。

此外, 在使用`cron`来调度脚本时, **⚠️请勿设置多个脚本在同一时刻运行**, 会极大增加被系统检测的风险, 可能导致账号封禁。

可以这样设置：
```shell
1,31 * * * * /path/to/run-bilibili-rater-1.sh
16,46 * * * * /path/to/run-bilibili-rater-2.sh
```  
这样两个脚本岔开运行, 减少了被封禁的风险。

# 自定义`handler`
bilibili-rater通过`handler`来抓取视频对应的“季-集”信息。  

`handler`本质是一个字符串解析器, 将字符串中包含的“季-集”信息解析出来。

`handler`属于抽象类`SeasonEpisodeHandler`, 其原型为：
```python
from abc import ABC
class SeasonEpisodeHandler(ABC):
    @staticmethod
    def handle(desc: str) -> tuple[int, int]:
        pass
```
其中      
`desc`为经过处理视频简介, 只包含简介第一行的信息。 
`handler`返回一个元组, 元组的第一个元素为“季”信息, 第二个元素为“集”信息。  

bilibili-rater已实现三种handler, 可以直接使用:  

| handler                       | 说明                     | 适用情形                      |
|-------------------------------|------------------------|---------------------------|
| `OnlyNumberHandler.handler`   | 简介第一行, 只使用数字来标注“季-集”信息 | 简介第一行为"3-2","10-5","6-14" |
| `NormalLetterHandler.handler` | 简介第一行, 使用"S"和"E"字母来标注  | "S08E12","S1E09","S13E15" |
| `DotHandler.handler`          | 简介第一行, 使用"."来分割"季-集"信息 | "1.2","8.5","14.3"        |  


## 自己实现的`handler`
注意, 在解析失败情况下也需要返回元组`(0,0)`, 程序会略过本次更新, 否则会崩溃。

```python
import bilibili_rater
from bilibili_api import Credential
import asyncio

# 继承SeasonEpisodeHandler
class MyCustomHandler(bilibili_rater.SeasonEpisodeHandler): 
    # 实现自定义的handle方法
    @staticmethod
    def handle(desc: str) -> tuple[int, int]:
      # 处理逻辑
      #
      #
      if True:
          # 成功返回结果 季号, 集号
          return 3,6
      else:
          # 失败返回0,0
          return 0,0

        
credential = Credential(
    sessdata="",
    bili_jct="",
    buvid3="",
    buvid4="",
    dedeuserid="",
)

fetcher_omdb = bilibili_rater.OmdbFetcher(api_key="xxxx",
                                          is_show_title=True)
fetcher_direct = bilibili_rater.DirectFetcher(is_show_ranking=True,
                                              is_show_title=True,
                                              is_show_release_date=True,
                                              is_show_average=True,
                                              is_show_median=True)

job = bilibili_rater.BilibiliRater(
    uploader_uid=591331248,  # up主uid
    credential=credential,  
    handler=MyCustomHandler.handle,  # “季-集”信息的解包方式
    resource_id="tt0397306",  # 根节目的imdb编号
    resource_cn_name="美国老爹",  #  最终显示在评论中的节目中文名
    imdb_fetchers=[fetcher_direct, fetcher_omdb],  
)

asyncio.run(job.run())
```

## 形参说明
- `desc: str`, 类型为字符串, 仅包含简介第一行内容。

# 开发文档（完善中）
## 类
### `BilibiliRater`
`BilibiliRater`类是主类, 运行程序时, 需要实例化该类。`BilibiliRater.run()`则开始一次运行。先获取视频信息，
如果视频BV号在缓存里则跳过本次搜刮。否则会获取简介中的“季-集”信息，然后使用获取器得到imdb信息并生成评论文本。然后再发送评论。

构建`BilibiliRater`需要以下参数
- `uploader_uid: int`
  - up主uid
- `credential: bilibili_api.Credential`
  - bilibili_api中的`Credential`类，用于存储Cookie
- `handler: SeasonEpisodeHandler.handle`
  - 简介信息解析器
- `resource_id: str`
  - 根节目的imdb编号
- `resource_cn_name: str`
  - 节目的中文名
- `imdb_fetchers: list[ImdbFetcher]`
  - 列表，里面是imdb信息获取器