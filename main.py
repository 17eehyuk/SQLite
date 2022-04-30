from flask import Flask, request ,redirect
import sqlite3
import numpy as np

#DB파일에연결
conn = sqlite3.connect('./database.db', check_same_thread=False)
#print('DB연결 성공')

#커서생성   #커서에 명령을 해서 처리 수행
sqlite_cusor = conn.cursor()
#print('커서생성 성공')

app = Flask(__name__)

def html(body, script=None):
    if script is None:
        script=''
    return f'''
    <!DOCTYPE html> 
    <html>
        <head>
            <meta charset="utf-8">
            <title>SQLite</title>
            <scrpit>
                {script}
            </script>
        </head>
        <body>
            <h1><a href="/">SQLite</a></h1>
            {body}
        </body>
    </html>  
    '''

#Read
def select_all_table(sql_table_name):
    sqlite_cusor.execute(
    f'''
    SELECT * FROM {sql_table_name}
    '''
    )
    sql_tables = sqlite_cusor.fetchall()
    return sql_tables

def return_col_name_arr(sql_table_name):
    table_cols = sqlite_cusor.execute(f'''
        SELECT name FROM PRAGMA_TABLE_INFO('{sql_table_name}');
    ''')
    return_arr = []

    for table_col in table_cols:
        return_arr.append(table_col)
    return return_arr


#Update
def insert_row_NULL(sql_table_name):

    len_col = len(return_col_name_arr(sql_table_name))

    i = 0
    Nulls = '('

    while i<int(len_col):
        Nulls = Nulls + 'NULL,'
        i = i + 1

    Nulls = Nulls[:-1] +')'

    sqlite_cusor.execute(
    f'''
        INSERT INTO {sql_table_name} VALUES {Nulls};
    '''
    )
    conn.commit()       #저장
    return  print('행 추가 성공')

def rename_table_name(sql_table_name, new_talbe_name):
    sqlite_cusor.execute(f'''
        ALTER TABLE {sql_table_name} RENAME TO {new_talbe_name};
    ''')
    conn.commit()       #저장



def insert_col(sql_table_name, new_col_name):
    sqlite_cusor.execute(
    f'''
        ALTER TABLE {sql_table_name} ADD COLUMN {new_col_name} TEXT;
    '''
    )
    conn.commit()       #저장
    return  print(f'열 "{new_col_name}" 추가 성공')



def rename_col(sql_table_name, old_name, new_name):
    sqlite_cusor.execute(f'''
        ALTER TABLE {sql_table_name} RENAME COLUMN {old_name} TO {new_name};
    ''')
    conn.commit()       #저장
    


#Delete
def clear_table(sql_table_name):
    sqlite_cusor.execute(f'''
        DELETE FROM {sql_table_name};
    ''')
    conn.commit()       #저장

def del_col(sql_table_name, del_col_name):
    sqlite_cusor.execute(
    f'''
        ALTER TABLE {sql_table_name} DROP COLUMN {del_col_name};
    '''
    )
    conn.commit()       #저장
    return  print(f'열 "{del_col_name}" 삭제 성공')



#sql 데이터를 html 표로 만들어줌
def sql_to_html_table(sql_table_name, update_mode=None):
    sql_data = select_all_table(sql_table_name)
    col_names = return_col_name_arr(sql_table_name)

    if update_mode is None:
        #빈테이블 오류 방지
        if sql_data == []:
            sql_data = ['']

        table_name = ''
        for col_name in col_names:
            table_name = table_name + f'<th>{col_name[0]}</th>\n'

        table_data = ''
        for row in sql_data:
            table_data = table_data + '\t<tr>\n'
            for data in row:
                table_data = table_data + f'\t\t<td>{data}</td>\n'
            table_data = table_data + '\t</tr>\n'
        
            html_table = f'''
        <table border="1px">
            <tr>
                {table_name}
            </tr>
            {table_data}
        </table>
        '''
    elif update_mode is True:
        if sql_data == []:
            html_table = f'''
            <form action="/read/{sql_table_name}">
                <input type="submit" value="이전으로">
            </form>
            '''
        
        else:
            i = 0
            table_name = ''
            for col_name in col_names:
                table_name = table_name + f'<th><input type="text" name="col_name[{i}]" value="{col_name[0]}"></th>\n'      #나중에 열 수정도 가능
                i = i + 1
                #table_name = table_name + f'<th>{col_name[0]}</th>\n'

            table_data = ''
            
            #첫번째 for문에서 0이 되게 하기 위해 -1
            i = -1
            j = -1

            for row in sql_data:
                i = i+1
                table_data = table_data + '\t<tr>\n'
                for data in row:
                    j = j+1
                    table_data = table_data + f'\t\t<td><input type="text" value="{data}" name="row_data[{i}][{j}]"></td>\n'
                table_data = table_data + f'\t\t<td><input type="radio" name="row_delete[{i}]" value="1" class="checkbox">삭제</label></td>\n'
                table_data = table_data + f'\t\t<td><input type="radio" name="row_delete[{i}]" value="0" class="checkbox" checked>취소</label></td>\n'
                table_data = table_data + '\t</tr>\n'
                j=0
            html_table = f'''
            <form method="POST">
                <input type="hidden" name="sql_table_name" value="{sql_table_name}">
                <table border="1px">
                    <tr>
                        {table_name}
                        <th colspan="2">삭제하기</th>
                    </tr>
                    {table_data}
                </table>            
                <input type="submit" value="수정완료" formaction="/update_table_process/">
            </form>
            '''    
    return html_table
    


##################################################################################

@app.route('/')
def index():
    tables = sqlite_cusor.execute('''
        SELECT tbl_name FROM sqlite_master;
    ''')
    table_list = ''

    for table in tables:
        table_list = table_list + f'<option>{table[0]}</option>\n'

    body = f'''
        <form method="POST">
            <select name="selected_table">
                {table_list}
            </select>   
            <input type="submit" value="테이블보기" formaction="/read/">
            <input type="submit" value="테이블생성" formaction="/create/">
        </form>
    
    '''
    return html(body)

##################################################################################

#Create
@app.route('/create/', methods=["POST"])
def create():

    # 더미코드(form 양식을 테이블보기와 같이 사용하기 때문에 없으면 오류 발생 그냥 무시하기)
    try:
        request.form['selected_table']
    except:
        print('무시')

    body =f'''
    <form method="post" action="/create_process/">
        <input type="text" placeholder="테이블 이름은?" name="table_name">
        <input type="submit" value="테이블생성">
    </form>
    '''
    return html(body)

@app.route('/create_process/', methods=["POST"])
def create_process():
    table_name = request.form['table_name']
    sqlite_cusor.execute(
    f'''
    CREATE TABLE {table_name}(새로운테이블 text);
    '''
    )
    print(f'테이블 {table_name} 생성 성공')
    return redirect(f'/read/{table_name}')

##################################################################################

#Read   
@app.route('/read/', methods=["POST"])
def read_post():
    try:
        selected_table = request.form['selected_table']
        return redirect(f'/read/{selected_table}')
    except:
        return redirect('/')
    
    

@app.route('/read/<selected_table>', methods=["GET"])
def read_get(selected_table):
    #sql_data = select_all_table(selected_table)    
    # hidden text는 form을 보내주기 위해서 만듬
    body = f'''
    <h2>{selected_table}</h2>
    <form method="POST">
        <input type="text" name="selected_table" value="{selected_table}" hidden>
        <input type="submit" value="행추가" formaction="/append_row/">
        <input type="submit" value="데이터수정(행열)" formaction="/update_table/">
        <input type="submit" value="열추가" formaction="/append_col/">
        <input type="submit" value="열삭제" formaction="/delete_col/">        
        <input type="submit" value="테이블명변경" formaction="/rename_table/">
        <input type="submit" value="테이블삭제" formaction="/delete/">
    </form>
    <br>
    {sql_to_html_table(selected_table)}    
    '''
    
    return html(body)

##################################################################################

#Update

@app.route('/append_row/', methods=["POST"])
def append_row():
    selected_table = request.form['selected_table']   
    insert_row_NULL(selected_table)
    return redirect(f'/read/{selected_table}')

@app.route('/rename_table/', methods=["POST"])
def rename_table():
    selected_table = request.form['selected_table']
    body =f'''
    <h3>현재이름 : {selected_table}</h3>
    <form method="post" action="/rename_table_process/">
        <input type="text" name="selected_table" value="{selected_table}" hidden>
        <input type="text" placeholder="새 테이블 이름은?" name="new_table_name">
        <input type="submit" value="이름변경">
    </form>
    '''
    return html(body)

@app.route('/rename_table_process/', methods=["POST"])
def rename_table_process():
    selected_table = request.form['selected_table']
    new_col_name = request.form['new_table_name']  
    rename_table_name(selected_table, new_col_name)
    return redirect(f'/read/{new_col_name}')

@app.route('/append_col/', methods=["POST"])
def append_col():
    selected_table = request.form['selected_table']
    body =f'''
    <form method="post" action="/append_col_process/">
        <input type="text" name="selected_table" value="{selected_table}" hidden>
        <input type="text" placeholder="열 이름은?" name="new_col_name">
        <input type="submit" value="열추가">
    </form>
    '''
    return html(body)



@app.route('/append_col_process/', methods=["POST"])
def append_col_process():
    selected_table = request.form['selected_table']
    new_col_name = request.form['new_col_name']  
    insert_col(selected_table, new_col_name)
    return redirect(f'/read/{selected_table}')



@app.route('/update_table/', methods=["POST"])
def update_table():

    selected_table = request.form['selected_table']
    body = f'''
    <h2>{selected_table}</h2>
    {sql_to_html_table(selected_table,True)}
    '''
    return html(body)

@app.route('/update_table_process/', methods=["POST"])
def update_table_process():
    return_list = list(dict(request.form).values())
    table_name = return_list[:1][0]     #테이블명 출력 [0]이 있어야 배열이 아닌 데이터가 나옴
    talbe_values_list = return_list[1:]
    len_col = len(return_col_name_arr(table_name))

    # 열 이름 변경
    old_names = return_col_name_arr(table_name)
    print(old_names)
    new_names = talbe_values_list[:len_col]
    print(new_names)

    i = 0
    while i< len_col:
        if old_names[i][0] != new_names[i]:
            rename_col(table_name, old_names[i][0], new_names[i])               # old_names는 [('이름',), ('수명',)] 으로 출력되기 때문에
        i = i + 1        
        



    talbe_values_list = talbe_values_list[len_col:]
    print(talbe_values_list)
    
    col_count = len(return_col_name_arr(table_name)) + 1       # 삭제하기 열도 있기 때문에 +1
    row_count = int(len(talbe_values_list)/col_count)       
    #print(col_count)
    #print(row_count)

    new_arrays = np.array(talbe_values_list).reshape(row_count,col_count)
    #print(new_arrays)

    clear_table(table_name)

    update_sql_table = []

    for new_array in new_arrays:
        tmp_list = list(new_array)
        #print(tmp_list)
        delete_judge = tmp_list[col_count-1]
        #print(delete_judge)
        if int(delete_judge) == 1:
            continue
        #return_sql_table.append(tuple(tmp_list.pop()))         # 삭제열 제외하고 추가
        tmp_list.pop()
        update_sql_table.append(tuple(tmp_list))                # 이값을 sql로 넣기



    len_col = len(return_col_name_arr(table_name))
    i = 0
    ques_marks = '('
    while i<int(len_col):
        ques_marks = ques_marks + '?,'
        i = i + 1
    ques_marks = ques_marks[:-1] +')'



    sqlite_cusor.executemany(
        f'''
        INSERT INTO {table_name} VALUES {ques_marks};
        ''', update_sql_table
    )
    conn.commit()
    return redirect(f'/read/{table_name}')




##################################################################################

#Delete
@app.route('/delete/', methods=["POST"])
def delete():
    selected_table = request.form['selected_table']
    #print(selected_table)
    body = f'''
    <h2>테이블 "{selected_table}" 을(를) 정말로 삭제할 것입니까?</h2>
    <form method="post">
        <input hidden name="table_name" value="{selected_table}">
        <input type="radio" name="delete_sure" value="1">네</label>
        <input type="radio" name="delete_sure" value="0" checked>아니요</label>
        <br>
        <input type="submit" formaction="/delete_process/">
    </form>
    
    '''

    return html(body)


@app.route('/delete_process/', methods=["POST"])
def delete_process(): 

    
    delete_sure = request.form['delete_sure']

    if delete_sure == '1':
        table_name = request.form['table_name']
        sqlite_cusor.execute(
        f'''
        DROP TABLE {table_name}
        '''
        )
        return redirect('/')
    else:
        return redirect('/')


@app.route('/delete_col/', methods=["POST"])
def delete_col():
    selected_table = request.form['selected_table']
    col_names = return_col_name_arr(selected_table)
    col_name_list = '<ul>\n'

    for col_name in col_names:
        col_name_list = col_name_list + f'''<li>{col_name[0]}</li>\n'''
    col_name_list = col_name_list + '</ul>'

    body =f'''
    {col_name_list}
    <form method="post" action="/delete_col_process/">
        <input type="text" name="selected_table" value="{selected_table}" hidden>
        <input type="text" placeholder="삭제할 열 이름은?" name="del_col_name">
        <input type="submit" value="삭제">
    </form>
    '''
    return html(body)


@app.route('/delete_col_process/', methods=["POST"])
def delete_col_process():
    selected_table = request.form['selected_table']
    del_col_name = request.form['del_col_name']
    print(selected_table)
    print(del_col_name)
    del_col(selected_table, del_col_name)
    return redirect(f'/read/{selected_table}')
    #return('gd')
  
        

app.run(port=3000, debug=True, host='0.0.0.0')      #포트변경가능   #debug=True : 코드바꾸면 자동으로 서버가 껏다켜짐       #host='0.0.0.0' 모든 ip접속가능     #끝에 있어야됨