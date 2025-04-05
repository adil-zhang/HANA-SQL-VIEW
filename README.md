# SQL转HANA属性视图转换器

这是一个用于将SQL查询转换为HANA属性视图的Web应用程序。它可以将简单的SQL查询转换为符合HANA标准的XML格式视图定义。

## 功能特点

- 简洁的Web界面
- 实时SQL转换
- 支持基本的SQL查询转换
- 自动识别schema和表名
- 生成标准的HANA属性视图XML
- 支持下载生成的XML文件

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
# 或
.\venv\Scripts\activate  # Windows
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

1. 在文本框中输入SQL查询（例如：`SELECT * FROM _SYS_BIC.TABLE_NAME`）
2. 点击"转换"按钮
3. 查看生成的XML内容
4. 点击"下载XML文件"按钮保存结果

## 支持的SQL语法

- 基本的SELECT语句
- 支持schema.table_name格式的表名
- 支持多列选择

## 注意事项

- 目前支持基本的SQL查询转换
- 复杂的SQL查询可能需要手动调整生成的HANA属性视图
- 建议在使用前先测试简单的SQL查询
- 确保输入的SQL语法正确

## 许可证

MIT License 