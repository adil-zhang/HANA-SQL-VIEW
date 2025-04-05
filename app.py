from flask import Flask, render_template, request, jsonify
import re
from datetime import datetime
import os

app = Flask(__name__)

def load_template(template_name):
    template_path = os.path.join('templates', 'xml_templates', template_name)
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def sql_to_hana_attribute_view(sql_query):
    try:
        # 将SQL查询转换为大写
        sql_query = sql_query.upper()
        
        # 提取schema和表名
        table_match = re.search(r'FROM\s+(\w+\.\/BIC\/\w+)', sql_query)
        if table_match:
            schema, table_name = table_match.group(1).split('.')
            # 处理/BIC/格式的表名
            if schema == 'ABAP' and table_name.startswith('/BIC/'):
                # 提取不带/BIC/的表名部分
                table_name_without_bic = table_name[5:]
                # 生成数据源ID（去掉最后一位数字）
                data_source_id = re.sub(r'\d$', '', table_name_without_bic)
                # 保持原始表名不变
                table_name = table_name
            else:
                data_source_id = table_name
        else:
            table_match = re.search(r'FROM\s+(\w+)', sql_query)
            schema = ''
            table_name = table_match.group(1) if table_match else 'UNKNOWN_TABLE'
            data_source_id = table_name
        
        # 根据schema设置数据源类型
        source_type = 'CALCULATION_VIEW' if schema == '_SYS_BIC' else 'DATA_BASE_TABLE'
        
        # 提取列名
        columns_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query)
        columns = [col.strip() for col in columns_match.group(1).split(',')] if columns_match else []
        
        # 准备模板变量
        view_id = f"Z_{table_name}_VIEW"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.000")
        
        # 生成视图属性
        view_attributes = '\n'.join(f'        <viewAttribute id="{col}"/>' for col in columns)
        attribute_mappings = '\n'.join(f'        <mapping xsi:type="Calculation:AttributeMapping" target="{col}" source="{col}"/>' for col in columns)
        logical_attributes = '\n'.join(f'''      <attribute id="{col}" order="{i+1}" attributeHierarchyActive="false" displayAttribute="false">
        <descriptions defaultDescription="{col}"/>
        <keyMapping columnObjectName="Projection_1" columnName="{col}"/>
      </attribute>''' for i, col in enumerate(columns))
        
        # 加载并组合所有模板
        xml_parts = [
            load_template('base_config.xml').format(view_id=view_id),
            load_template('description_metadata.xml').format(
                view_description=f"{view_id} 计算视图",
                changed_at=current_time
            ),
            # load_template('local_variables.xml'),  # 暂时注释掉本地变量部分
            load_template('data_sources.xml').format(
                table_name=table_name,
                source_type=source_type,
                schema=schema if schema else 'ABAP',  # 如果没有指定schema，默认使用ABAP
                data_source_id=data_source_id  # 使用处理后的数据源ID
            ),
            load_template('calculation_views.xml').format(
                view_attributes=view_attributes,
                attribute_mappings=attribute_mappings,
                table_name=data_source_id  # 使用处理后的数据源ID
            ),
            load_template('logical_model.xml').format(logical_attributes=logical_attributes),
            load_template('layout.xml')
        ]
        
        return '\n'.join(xml_parts)
    except Exception as e:
        return f"转换过程中出现错误: {str(e)}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/convert', methods=['POST'])
def convert():
    sql_query = request.json.get('sql_query', '')
    if not sql_query:
        return jsonify({'error': '请提供SQL查询'}), 400
    
    hana_view = sql_to_hana_attribute_view(sql_query)
    return jsonify({'hana_view': hana_view})

if __name__ == '__main__':
    app.run(debug=True) 