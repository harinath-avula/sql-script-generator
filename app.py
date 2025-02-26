from flask import Flask, request, render_template, send_file
import re
import os

def parse_insert_query(query):
    match = re.match(r"INSERT INTO (\w+) \((.*?)\) VALUES \((.*?)\)", query, re.IGNORECASE)
    if not match:
        return None
    
    table_name = match.group(1)
    columns = [col.strip() for col in match.group(2).split(',')]
    values = [val.strip() for val in match.group(3).split(',')]
    
    return table_name, columns, values

def generate_exec_statement(table_name, columns, values, user, cfg_item, updt_type):
    param_assignments = ",\n".join([f"@ICol_{col} = {val}" for col, val in zip(columns, values)])
    additional_params = (
        f"@IParam_G_USER = '{user}',\n"
        f"@IParam_N_CFG_ITEM = '{cfg_item}',\n"
        f"@IParam_N_UPDT_TYP = '{updt_type}'"
    )
    
    exec_statement = f"""
    EXEC usp_{table_name}
    {param_assignments},
    {additional_params}
    """.strip()
    
    return exec_statement

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files['sql_file']
        if file:
            file_path = os.path.join(UPLOAD_FOLDER, file.filename)
            file.save(file_path)
            
            with open(file_path, 'r') as f:
                queries = f.readlines()
            
            stored_procedures = []
            for query in queries:
                parsed = parse_insert_query(query.strip())
                if parsed:
                    table_name, columns, values = parsed
                    exec_script = generate_exec_statement(table_name, columns, values, 'afs.user', '', 'I')
                    stored_procedures.append(exec_script)
            
            output_file = os.path.join(UPLOAD_FOLDER, 'output.sql')
            with open(output_file, 'w') as f:
                f.write('\n\n'.join(stored_procedures))
            
            return send_file(output_file, as_attachment=True)
    
    return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
