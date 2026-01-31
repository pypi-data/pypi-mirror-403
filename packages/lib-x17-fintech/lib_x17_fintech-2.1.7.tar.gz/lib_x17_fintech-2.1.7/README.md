# lib-x17-fintech

专业的金融数据处理库 - 提供统一的存储抽象、数据获取、模式管理和序列化能力。

[![Python](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-2467%20passed-brightgreen.svg)](pytest.ini)
[![Coverage](https://img.shields.io/badge/coverage-98%25-brightgreen.svg)](.coverage)

## 概述

`lib-x17-fintech` 是一个功能完整的金融数据处理库，为 X17 生态系统提供核心数据基础设施。通过模块化设计，提供从数据获取到存储的完整解决方案。

### 核心特性

- 🔌 **存储抽象** - 统一的接口支持本地文件系统和 AWS S3
- 📊 **数据获取** - 完整的 Job 系统，支持 Tushare、Baostock 等数据源
- 📐 **模式管理** - 灵活的表结构定义和验证
- 💾 **序列化** - 多格式支持（Parquet、CSV、JSON、Pickle）
- ⚡ **高性能** - 智能缓存、重试和分页机制
- 🛡️ **类型安全** - 完整的类型提示和协议接口

## 快速开始

### 安装

```bash
# 基础安装
pip install lib-x17-fintech

# 开发环境（包含测试工具）
pip install lib-x17-fintech[dev]

# 从源码安装
git clone <repository-url>
cd lib-x17-fintech
pip install -e .
```

### 基本用法

#### 1. 获取金融数据

```python
from xfintech.data.source.tushare import Session, Stock

# 创建会话
session = Session(credential="your_tushare_token")

# 获取股票列表
job = Stock(session=session)
result = job.run()

print(result.data)  # pandas DataFrame
```

#### 2. 保存数据到存储

```python
from xfintech.connect import MacOSConnect, Artifact, ConnectRef
from xfintech.serde import PandasSerialiser, DataFormat

# 创建存储连接
connect = MacOSConnect()

# 保存数据
artifact = Artifact(
    ref=ConnectRef("~/data/stocks.parquet"),
    data=result.data
)
artifact.write(connect, PandasSerialiser, DataFormat.PARQUET)
```

#### 3. 定义数据模式

```python
from xfintech.fabric import TableInfo, ColumnInfo, ColumnKind

# 定义表结构
schema = TableInfo(
    name="stock_daily",
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING),
        ColumnInfo(name="trade_date", kind=ColumnKind.DATE),
        ColumnInfo(name="open", kind=ColumnKind.FLOAT),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT),
    ]
)

# 验证数据
schema.validate(dataframe)
```

#### 4. 完整数据管道

```python
from xfintech.data.source.tushare import Session, Dayline
from xfintech.data.common import Cache, Retry
from xfintech.connect import S3Connect, Artifact, ConnectRef
from xfintech.serde import PandasSerialiser, DataFormat

# 1. 获取数据（带缓存和重试）
session = Session(credential="token")
job = Dayline(
    session=session,
    params={"ts_code": "000001.SZ", "start_date": "20260101"},
    cache=Cache(),
    retry=Retry(retry=3, wait=1.0, rate=2.0)
)
result = job.run()

# 2. 保存到 S3
connect = S3Connect(bucket="my-bucket")
artifact = Artifact(
    ref=ConnectRef("data/dayline/000001.parquet"),
    data=result.data,
    meta={"job": job.name, "duration": job.metric.duration}
)
artifact.write(connect, PandasSerialiser, DataFormat.PARQUET)

print(f"✅ 保存 {len(result.data)} 行数据，耗时 {job.metric.duration:.2f} 秒")
```

## 模块架构

```
xfintech/
├── connect/        # 存储连接抽象
│   ├── MacOSConnect    - 本地文件系统
│   ├── S3Connect       - AWS S3
│   └── Artifact        - 数据工件
│
├── data/           # 数据获取基础设施
│   ├── common/         - 通用工具（Cache, Retry, Metric）
│   ├── job/            - Job 系统和注册中心
│   ├── relay/          - 中继客户端
│   └── source/         - 数据源（Tushare, Baostock）
│
├── fabric/         # 数据模式管理
│   ├── TableInfo       - 表结构定义
│   ├── ColumnInfo      - 列信息
│   └── ColumnKind      - 数据类型枚举
│
└── serde/          # 序列化/反序列化
    ├── PythonSerialiser    - Python 对象
    ├── PandasSerialiser    - DataFrame
    └── DataFormat          - 格式枚举
```

## 模块详解

### [xfintech.connect](xfintech/connect/README.md) - 存储连接

统一的存储抽象层，支持多种后端。

**主要功能**:
- `MacOSConnect` - 本地文件系统操作
- `S3Connect` - AWS S3 对象存储
- `Artifact` - 数据工件管理
- `ConnectRef` - 路径引用

**快速示例**:
```python
from xfintech.connect import MacOSConnect, Artifact, ConnectRef

connect = MacOSConnect()
artifact = Artifact(ref=ConnectRef("~/data/file.parquet"), data=df)
artifact.write(connect, serialiser, format)
```

[📖 完整文档](xfintech/connect/README.md)

---

### [xfintech.data](xfintech/data/README.md) - 数据获取

完整的数据获取基础设施，Job 系统管理数据请求生命周期。

**主要功能**:
- `Job` - 作业基类
- `TushareJob` - Tushare 数据源
- `Cache` - 智能缓存
- `Retry` - 指数退避重试
- `Metric` - 性能监控

**快速示例**:
```python
from xfintech.data.source.tushare import Session, Stock
from xfintech.data.common import Cache, Retry

session = Session(credential="token")
job = Stock(
    session=session,
    cache=Cache(),
    retry=Retry(retry=3, wait=1.0)
)
result = job.run()
```

**支持的数据源**:
- ✅ Tushare (28+ 股票数据类)
- ✅ Baostock
- 🔄 更多数据源开发中...

[📖 完整文档](xfintech/data/README.md)

---

### [xfintech.fabric](xfintech/fabric/README.md) - 数据模式

灵活的表结构定义和验证系统。

**主要功能**:
- `TableInfo` - 表结构定义
- `ColumnInfo` - 列信息管理
- `ColumnKind` - 7 种数据类型
- 数据验证和文档生成

**快速示例**:
```python
from xfintech.fabric import TableInfo, ColumnInfo, ColumnKind

schema = TableInfo(
    name="stock_daily",
    columns=[
        ColumnInfo(name="ts_code", kind=ColumnKind.STRING),
        ColumnInfo(name="close", kind=ColumnKind.FLOAT),
    ]
)

# 验证数据
schema.validate(df)
```

[📖 完整文档](xfintech/fabric/README.md)

---

### [xfintech.serde](xfintech/serde/README.md) - 序列化

多格式序列化和反序列化支持。

**主要功能**:
- `PythonSerialiser` - Python 对象（Pickle）
- `PandasSerialiser` - DataFrame（Parquet/CSV/JSON）
- `DataFormat` - 格式枚举
- 自动类型检测

**快速示例**:
```python
from xfintech.serde import PandasSerialiser, DataFormat

# 序列化
serialised = PandasSerialiser.serialise(df, DataFormat.PARQUET)

# 反序列化
df = PandasSerialiser.deserialise(serialised, DataFormat.PARQUET)
```

**支持格式**:
| 格式 | 扩展名 | 适用场景 |
|------|--------|----------|
| Parquet | .parquet | 大数据集（推荐）|
| CSV | .csv | 文本导入/导出 |
| JSON | .json | API 交互 |
| Pickle | .pkl | Python 对象 |

[📖 完整文档](xfintech/serde/README.md)

## 使用场景

### 场景 1: 构建数据仓库

```python
from xfintech.data.source.tushare import Session, Dayline
from xfintech.connect import S3Connect, Artifact, ConnectRef
from xfintech.serde import PandasSerialiser, DataFormat
from datetime import datetime, timedelta

def build_data_warehouse():
    """构建股票日线数据仓库"""
    session = Session(credential="token")
    connect = S3Connect(bucket="datawarehouse")
    
    # 获取过去 30 天的数据
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    symbols = ["000001.SZ", "600000.SH", "000002.SZ"]
    
    for symbol in symbols:
        job = Dayline(
            session=session,
            params={
                "ts_code": symbol,
                "start_date": start_date.strftime("%Y%m%d"),
                "end_date": end_date.strftime("%Y%m%d")
            }
        )
        result = job.run()
        
        # 保存到 S3
        path = f"stocks/daily/{symbol}/{end_date.strftime('%Y%m%d')}.parquet"
        artifact = Artifact(ref=ConnectRef(path), data=result.data)
        artifact.write(connect, PandasSerialiser, DataFormat.PARQUET)
        
        print(f"✅ {symbol}: {len(result.data)} 行")
```

### 场景 2: 数据质量监控

```python
from xfintech.data.source.tushare import Session, Stock
from xfintech.fabric import TableInfo, ColumnInfo, ColumnKind

def monitor_data_quality():
    """监控数据质量"""
    # 1. 定义期望的模式
    expected_schema = TableInfo(
        name="stock_basic",
        columns=[
            ColumnInfo(name="ts_code", kind=ColumnKind.STRING),
            ColumnInfo(name="name", kind=ColumnKind.STRING),
            ColumnInfo(name="list_date", kind=ColumnKind.DATE),
        ]
    )
    
    # 2. 获取数据
    session = Session(credential="token")
    job = Stock(session=session)
    result = job.run()
    
    # 3. 验证
    try:
        expected_schema.validate(result.data)
        print("✅ 数据质量检查通过")
    except Exception as e:
        print(f"❌ 数据质量问题: {e}")
```

### 场景 3: 增量数据更新

```python
from xfintech.data.source.tushare import Session, TradeDate, Dayline
from xfintech.connect import MacOSConnect, Artifact, ConnectRef
from xfintech.serde import PandasSerialiser, DataFormat
import pandas as pd

def incremental_update():
    """增量更新每日数据"""
    session = Session(credential="token")
    connect = MacOSConnect()
    
    # 1. 获取最新交易日
    trade_date_job = TradeDate(
        session=session,
        params={"exchange": "SSE"}
    )
    trade_dates = trade_date_job.run().data
    latest_date = trade_dates['cal_date'].max()
    
    # 2. 检查是否已存在
    ref = ConnectRef(f"~/data/daily/{latest_date}.parquet")
    if connect.exists(ref):
        print(f"📌 {latest_date} 数据已存在，跳过")
        return
    
    # 3. 获取并保存新数据
    job = Dayline(
        session=session,
        params={"trade_date": latest_date}
    )
    result = job.run()
    
    artifact = Artifact(ref=ref, data=result.data)
    artifact.write(connect, PandasSerialiser, DataFormat.PARQUET)
    
    print(f"✅ 更新 {latest_date}: {len(result.data)} 行")
```

## 测试

```bash
# 运行所有测试
pytest

# 带覆盖率报告
pytest --cov=xfintech --cov-report=html

# 运行特定模块测试
pytest xfintech/connect/
pytest xfintech/data/
pytest xfintech/fabric/
pytest xfintech/serde/

# 性能基准测试
pytest --benchmark-only
```

**测试统计**:
- ✅ 2,467 测试全部通过
- 📊 98% 代码覆盖率
- ⚡ 所有测试 < 5 秒

## 开发

### 项目结构

```bash
lib-x17-fintech/
├── xfintech/              # 源代码
│   ├── connect/           # 存储模块
│   ├── data/              # 数据模块
│   ├── fabric/            # 模式模块
│   └── serde/             # 序列化模块
├── tests/                 # 测试（镜像源码结构）
├── example/               # 示例代码
├── pyproject.toml         # 项目配置
├── pytest.ini             # 测试配置
├── environment.yml        # Conda 环境
└── makefile               # 构建脚本
```

### 环境设置

```bash
# 使用 Conda
conda env create -f environment.yml
conda activate xfintech

# 或使用 pip
python -m venv venv
source venv/bin/activate  # Linux/Mac
pip install -e .[dev]
```

### 代码规范

```bash
# 格式化和 Lint
ruff check xfintech/
ruff format xfintech/

# 类型检查
mypy xfintech/
```

### 构建和发布

```bash
# 构建包
python -m build

# 发布到 PyPI
twine upload dist/*
```

## 配置

### 环境变量

```bash
# Tushare 配置
export TUSHARE_TOKEN="your_token_here"

# AWS 配置（用于 S3Connect）
export AWS_ACCESS_KEY_ID="your_key"
export AWS_SECRET_ACCESS_KEY="your_secret"
export AWS_DEFAULT_REGION="us-east-1"

# 缓存目录
export XFINTECH_CACHE_DIR="/custom/cache/path"
```

### 配置文件

创建 `~/.xfintech/config.toml`:

```toml
[tushare]
token = "your_tushare_token"

[cache]
path = "/data/cache"
ttl = 86400  # 24 hours

[s3]
bucket = "my-data-bucket"
region = "us-east-1"
```

## 最佳实践

### ✅ 推荐做法

```python
# 1. 始终使用缓存
from xfintech.data.common import Cache
job = SomeJob(session=session, cache=Cache())

# 2. 配置重试策略
from xfintech.data.common import Retry
job = SomeJob(session=session, retry=Retry(retry=3, wait=1.0, rate=2.0))

# 3. 使用上下文管理器
with connect:
    artifact.write(connect, serialiser, format)

# 4. 验证数据模式
schema.validate(dataframe)

# 5. 监控性能
result = job.run()
print(f"耗时: {job.metric.duration} 秒")
```

### ❌ 避免的做法

```python
# 1. 不使用缓存（重复 API 调用）
job = SomeJob(session=session)  # 缺少 cache

# 2. 硬编码路径
path = "/Users/john/data/file.csv"  # 使用 ConnectRef

# 3. 忽略错误
result = job.run()  # 不检查 job.metric.errors

# 4. 不验证数据
artifact.write(connect, serialiser, format)  # 先验证
```

## 常见问题

### Q: 如何选择存储后端？

**A**: 
- 本地开发/小数据集 → `MacOSConnect`
- 生产环境/大数据集/团队协作 → `S3Connect`

### Q: 哪种序列化格式最适合？

**A**:
- 性能优先（大数据）→ Parquet
- 人类可读 → CSV
- API 交互 → JSON
- Python 对象 → Pickle

### Q: 如何提高数据获取性能？

**A**:
1. 启用缓存: `Cache()`
2. 调大分页: `Paginate(pagesize=5000)`
3. 并发获取: 使用 `ThreadPoolExecutor`
4. 使用中继: `Session(mode="relay")`

### Q: 测试失败怎么办？

**A**:
```bash
# 查看详细错误
pytest -v

# 只运行失败的测试
pytest --lf

# 查看标准输出
pytest -s
```

## 贡献

欢迎贡献！请遵循以下流程：

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/amazing`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing`)
5. 创建 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 作者

**Xing Xing** - [x.xing.work@gmail.com](mailto:x.xing.work@gmail.com)

## 相关项目

- `lib-x17-cloudcdk` - AWS CDK 基础设施
- `lib-x17-cloudsdk` - 云服务 SDK
- `lib-x17-cloudmeta` - 云元数据管理

## 更新日志

### v2.0.0 (2026-01-09)
- ✨ 完整的四模块架构（connect, data, fabric, serde）
- 📚 完善的文档和示例
- ✅ 2,467 测试，98% 覆盖率
- 🚀 性能优化和缓存机制

---

**让金融数据处理变得简单、高效、可靠！** 🚀
