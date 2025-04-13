# HANA SQL 视图生成器

这是一个基于Flask的Web应用，用于将SQL查询转换为HANA计算视图的XML格式。

## 功能特点

- 支持单表查询和JOIN查询
- 自动处理表别名
- 支持/BIC/格式的表名
- 自动生成Projection视图和Join视图
- 支持多行SQL查询
- 自动处理JOIN条件中的字段

## 技术栈

- Python 3.7+
- Flask
- SQLAlchemy
- python-dotenv
- Werkzeug

## 项目结构

```
project/
├── app.py                  # 主应用文件
├── requirements.txt        # 项目依赖
├── templates/
│   ├── index.html         # 前端页面
│   └── xml_templates/     # XML模板文件
│       ├── base_config.xml
│       ├── description_metadata.xml
│       ├── local_variables.xml
│       ├── data_sources.xml
│       ├── calculation_views.xml
│       ├── logical_model.xml
│       └── layout.xml
```

## 安装步骤

1. 克隆项目到本地
```bash
git clone [repository-url]
cd [project-directory]
```

2. 创建并激活虚拟环境
```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
```

## 运行应用

1. 确保虚拟环境已激活
2. 运行应用：
```bash
python app.py
```
3. 打开浏览器访问：http://localhost:5000

## 使用方法

1. 启动应用：
```bash
python app.py
```

2. 访问Web界面：
```
http://localhost:5000
```

3. 输入SQL查询并点击"生成视图"按钮

## SQL查询格式

### 单表查询
```sql
SELECT COL1, COL2 FROM TABLE1
```

### JOIN查询
```sql
SELECT T1.COL1, T1.COL2, T2.COL3 
FROM TABLE1 AS T1 
LEFT JOIN TABLE2 AS T2 ON T1.ID = T2.ID
```

### 多行SQL查询
```sql
SELECT 
    T1.COL1, 
    T1.COL2, 
    T2.COL3 
FROM 
    TABLE1 AS T1 
LEFT JOIN 
    TABLE2 AS T2 
ON 
    T1.ID = T2.ID
```

## 注意事项

1. 表名支持以下格式：
   - 简单表名：`TABLE1`
   - 带schema的表名：`SCHEMA.TABLE1`
   - /BIC/格式的表名：`ABAP./BIC/TABLE1`

2. JOIN查询支持：
   - LEFT JOIN
   - RIGHT JOIN
   - INNER JOIN

3. 表别名是可选的，但建议使用以提高可读性

4. JOIN条件支持多个条件，使用AND连接

## 输出说明

生成的XML包含以下主要部分：

1. 数据源（DataSources）：定义所有使用的表或视图
2. Projection视图：为每个数据源创建一个Projection视图
3. Join视图（如果有JOIN）：连接所有Projection视图
4. 逻辑模型：定义最终输出的字段和映射关系

## 许可证

本项目采用 Apache License 2.0。详情请参阅 [LICENSE](LICENSE) 文件。

Apache License 2.0 的主要特点：
- 允许商业使用
- 允许修改
- 允许分发
- 允许专利使用
- 允许私人使用
- 包含责任限制
- 包含专利授权
- 包含商标使用限制

## 贡献指南

欢迎提交 Issue 和 Pull Request 来帮助改进这个项目。

## 联系方式

如有任何问题或建议，请通过以下方式联系：
- 提交 Issue
- 发送邮件至 [adil_zhang@163.com]

## 更新日志

### v1.0.0
- 初始版本发布
- 支持基本的SQL到HANA属性视图的转换
- 支持/BIC/格式表名的处理 