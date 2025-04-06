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
        # SQL预处理：替换多个空格和换行为单个空格
        sql_query = re.sub(r'\s+', ' ', sql_query).strip().upper()
        
        # 提取列名和表名
        columns_match = re.search(r'SELECT\s+(.*?)\s+FROM', sql_query, re.DOTALL)
        columns = []
        if columns_match:
            columns_raw = columns_match.group(1).strip()
            columns = [col.strip() for col in columns_raw.split(',')]
        
        # 提取表信息
        tables = []
        join_conditions = []
        
        # 提取主表
        main_table_match = re.search(r'FROM\s+([\w\.\/]+)(?:\s+AS\s+(\w+))?', sql_query)
        if main_table_match:
            full_table_name = main_table_match.group(1)
            table_alias = main_table_match.group(2)
            if '.' in full_table_name:
                schema, table_name = full_table_name.split('.')
            else:
                schema = ''
                table_name = full_table_name
            
            # 处理/BIC/格式的表名
            if schema == 'ABAP' and table_name.startswith('/BIC/'):
                table_name_without_bic = table_name[5:]
                data_source_id = re.sub(r'\d$', '', table_name_without_bic)
            else:
                data_source_id = table_name
            
            tables.append({
                'full_name': full_table_name,
                'schema': schema,
                'name': table_name,
                'alias': table_alias or table_name,
                'data_source_id': data_source_id,
                'projection_id': f"Projection_{len(tables)+1}"
            })
        
        # 检查是否有JOIN
        has_join = 'JOIN' in sql_query
        
        if has_join:
            # 提取JOIN表和条件，使用更健壮的正则表达式
            join_pattern = r'(?:LEFT|RIGHT|INNER)?\s+JOIN\s+([\w\.\/]+)(?:\s+AS\s+(\w+))?\s+ON\s+(.*?)(?=\s+(?:LEFT|RIGHT|INNER)\s+JOIN|\s+WHERE|$)'
            join_matches = re.finditer(join_pattern, sql_query, re.DOTALL)
            
            for match in join_matches:
                full_table_name = match.group(1)
                table_alias = match.group(2)
                join_condition = match.group(3).strip()
                
                if '.' in full_table_name:
                    schema, table_name = full_table_name.split('.')
                else:
                    schema = ''
                    table_name = full_table_name
                
                # 处理/BIC/格式的表名
                if schema == 'ABAP' and table_name.startswith('/BIC/'):
                    table_name_without_bic = table_name[5:]
                    data_source_id = re.sub(r'\d$', '', table_name_without_bic)
                else:
                    data_source_id = table_name
                
                tables.append({
                    'full_name': full_table_name,
                    'schema': schema,
                    'name': table_name,
                    'alias': table_alias or table_name,
                    'data_source_id': data_source_id,
                    'projection_id': f"Projection_{len(tables)+1}"
                })
                
                # 解析JOIN条件
                for condition in join_condition.split('AND'):
                    condition = condition.strip()
                    if '=' in condition:
                        left, right = condition.split('=')
                        if '.' in left and '.' in right:
                            left_table, left_col = left.strip().split('.')
                            right_table, right_col = right.strip().split('.')
                            join_conditions.append({
                                'left_table': left_table,
                                'left_col': left_col,
                                'right_table': right_table,
                                'right_col': right_col
                            })
        
        # 准备模板变量
        view_id = f"Z_{tables[0]['name']}_VIEW"
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.000")
        
        # 生成数据源XML
        data_sources_xml = []
        for table in tables:
            source_type = 'CALCULATION_VIEW' if table['schema'] == '_SYS_BIC' else 'DATA_BASE_TABLE'
            data_sources_xml.append(f'''  <DataSource id="{table['data_source_id']}" type="{source_type}">
    <viewAttributes allViewAttributes="true"/>
    <columnObject schemaName="{table['schema'] if table['schema'] else 'ABAP'}" columnObjectName="{table['name']}"/>
  </DataSource>''')
        
        # 生成Projection视图
        projection_views = []
        for table in tables:
            # 获取该表的所有列
            table_columns = []
            if has_join:
                # 从SELECT语句中收集该表的列
                table_columns = [col.split('.')[1] for col in columns if '.' in col and col.split('.')[0].strip() == table['alias']]
                
                # 从JOIN条件中收集该表的列
                join_columns = []
                for condition in join_conditions:
                    if condition['left_table'] == table['alias']:
                        join_columns.append(condition['left_col'])
                    if condition['right_table'] == table['alias']:
                        join_columns.append(condition['right_col'])
                
                # 合并列并移除重复
                table_columns = list(set(table_columns + join_columns))
            else:
                table_columns = columns
            
            if not table_columns:
                continue
                
            view_attributes = '\n'.join(f'        <viewAttribute id="{col}"/>' for col in table_columns)
            attribute_mappings = '\n'.join(f'        <mapping xsi:type="Calculation:AttributeMapping" target="{col}" source="{col}"/>' for col in table_columns)
            
            projection_views.append(f'''    <calculationView xsi:type="Calculation:ProjectionView" id="{table['projection_id']}">
      <descriptions/>
      <viewAttributes>
{view_attributes}
      </viewAttributes>
      <calculatedViewAttributes/>
      <input node="#{table['data_source_id']}">
{attribute_mappings}
      </input>
    </calculationView>''')
        
        # 生成Join视图（如果有JOIN）
        join_view = ''
        if has_join and len(tables) > 1:
            # 生成Join视图的输入
            join_inputs = []
            for table in tables:
                # 获取该表的所有列（包括SELECT和JOIN条件中的列）
                table_columns = []
                # 从SELECT语句中收集该表的列
                select_columns = [col.split('.')[1] for col in columns if '.' in col and col.split('.')[0].strip() == table['alias']]
                # 从JOIN条件中收集该表的列
                join_columns = []
                for condition in join_conditions:
                    if condition['left_table'] == table['alias']:
                        join_columns.append(condition['left_col'])
                    if condition['right_table'] == table['alias']:
                        join_columns.append(condition['right_col'])
                
                # 合并列并移除重复
                table_columns = list(set(select_columns + join_columns))
                
                if not table_columns:
                    continue
                    
                attribute_mappings = '\n'.join(f'        <mapping xsi:type="Calculation:AttributeMapping" target="{col}" source="{col}"/>' 
                                              for col in table_columns)
                
                join_inputs.append(f'''      <input node="#{table['projection_id']}">
{attribute_mappings}
      </input>''')
            
            # 生成Join属性
            join_attributes = '\n'.join(f'      <joinAttribute name="{condition["left_col"]}"/>' 
                                       for condition in join_conditions)
            
            # 生成Join视图的属性
            # 使用所有表的列作为Join视图的属性
            all_join_columns = []
            for col in columns:
                if '.' in col:
                    col_parts = col.split('.')
                    all_join_columns.append(col_parts[1])
                else:
                    all_join_columns.append(col)
                    
            join_view_attributes = '\n'.join(f'        <viewAttribute id="{col}"/>' for col in all_join_columns)
            
            join_view = f'''    <calculationView xsi:type="Calculation:JoinView" id="Join_1" joinOrder="OUTSIDE_IN" joinType="leftOuter">
      <descriptions/>
      <viewAttributes>
{join_view_attributes}
      </viewAttributes>
      <calculatedViewAttributes/>
{join_inputs[0]}
{join_inputs[1]}
{join_attributes}
    </calculationView>'''
        
        # 生成逻辑属性
        logical_attributes = []
        for i, col in enumerate(columns):
            if '.' in col:
                col_parts = col.split('.')
                col_name = col_parts[1]
                logical_attributes.append(f'''      <attribute id="{col_name}" order="{i+1}" attributeHierarchyActive="false" displayAttribute="false">
        <descriptions defaultDescription="{col_name}"/>
        <keyMapping columnObjectName="{'Join_1' if has_join else 'Projection_1'}" columnName="{col_name}"/>
      </attribute>''')
            else:
                logical_attributes.append(f'''      <attribute id="{col}" order="{i+1}" attributeHierarchyActive="false" displayAttribute="false">
        <descriptions defaultDescription="{col}"/>
        <keyMapping columnObjectName="{'Join_1' if has_join else 'Projection_1'}" columnName="{col}"/>
      </attribute>''')
        logical_attributes_str = '\n'.join(logical_attributes)
        
        # 生成布局
        shapes = []
        for i, table in enumerate(tables):
            shapes.append(f'''      <shape expanded="true" modelObjectName="{table['projection_id']}" modelObjectNameSpace="CalculationView">
        <upperLeftCorner x="{100 + i * 200}" y="261"/>
        <rectangleSize height="-1" width="-1"/>
      </shape>''')
        
        if has_join and len(tables) > 1:
            shapes.append('''      <shape expanded="true" modelObjectName="Join_1" modelObjectNameSpace="CalculationView">
        <upperLeftCorner x="99" y="165"/>
        <rectangleSize height="0" width="0"/>
      </shape>''')
        
        # 加载并组合所有模板
        xml_parts = [
            load_template('base_config.xml').format(view_id=view_id),
            load_template('description_metadata.xml').format(
                view_description=f"{view_id} 计算视图",
                changed_at=current_time
            ),
            # load_template('local_variables.xml'),  # 暂时注释掉本地变量部分
            '<dataSources>\n' + '\n'.join(data_sources_xml) + '\n  </dataSources>',
            '<calculationViews>\n' + '\n'.join(projection_views) + '\n' + join_view + '\n  </calculationViews>',
            load_template('logical_model.xml').format(
                model_id="Join_1" if has_join else "Projection_1",
                logical_attributes=logical_attributes_str
            ),
            load_template('layout.xml').format(shapes='\n'.join(shapes))
        ]
        
        return '\n'.join(xml_parts)
    except Exception as e:
        import traceback
        return f"转换过程中出现错误: {str(e)}\n{traceback.format_exc()}"

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