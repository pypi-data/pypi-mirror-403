import os
import re
import sys
import json
import duckdb
import sqlite3
import inspect
from typing import Callable
from pydantic import BaseModel

DBENGINE = 'SQLite'
ADMINDB = 'db/admin.db'
DUCKDBENGINE = 'DUCK'
ADMINDUCKDB = 'db/dadmin.db'

ADMINDBNAME = 'admin'
ADMINZONENAME = 'ADMIN'
ADMINUSERNAME = 'admin'
ADMINZONE = 0
ADMINUSER = 1
DEFPASSWORD = '123456'
ENCODING = 'ISO-8859-1'
ENCODINGSIG = 'utf-8-sig'
PLACEHOLDER = r'\:\w+\b'
COLUUID = 'uuid'
ARRAY = 'array'

JOURPRAGMA = 'PRAGMA journal_mode=WAL'
FKEYPRAGMA = 'PRAGMA foreign_keys=1'
TEMPPRAGMA = 'PRAGMA temp_store=2'

## GLOBAL CONST

ERROR = 'error'
ACTION = 'action'
RESULT = 'result'

UNKNOWN = 'Unknown'
DBERROR = 'DatabaseError'
UNERROR = 'UnexpectedError'

BADZONEID = 'Zone ID not allowed'
ERRORINPUT = 'Invalid function parameters'
NOROWCOUNT = 'Input not verified, no updates were made'

NOENTRIES = 'A financial transaction must be recorded with at least 2 entries'
NOBALANCE = 'The total value of debits must equal the total value of credits'

## GLOBAL COLUMN

COL_ACCOUNT = 'account'
COL_ACTIVE = 'active'
COL_CODE = 'code'
COL_CREATED = 'created'
COL_CREATOR = 'creator'
COL_CREDIT = 'credit'
COL_DATED = 'dated'
COL_DEBIT = 'debit'
COL_GROUP = 'grup'
COL_ID = 'id'
COL_INFO = 'info'
COL_ITEM = 'item'
COL_MODIFIED = 'modified'
COL_MODIFIER = 'modifier'
COL_NAME = 'name'
COL_NOTE = 'note'
COL_REF = 'ref'
COL_ROLE = 'role'
COL_ROOT = 'root'
COL_SPEC = 'spec'
COL_SUB = 'sub'
COL_TX = 'tx'
COL_USER = 'user'
COL_UUID = 'uuid'
COL_WORKBEGIN = 'workbegin'
COL_WORKEND = 'workend'
COL_ZADM = 'zadmin'
COL_ZONE = 'zone'

COL_ZONEID = 'zoneid'
COL_ZONEIDN = 'zoneidn'
COL_CONUSER = 'conuser'
COL_USERIDN = 'useridn'

COL_PASS = 'hpwd'
COL_OPWD = 'oldpass'
COL_NPWD = 'newpass'

COL_ACCOUNTCODE = 'accountcode'
COL_WORKTIME = 'worktime'

COL_OFFSET = 'offset'
COL_LIMIT = 'limit'

QUERY_ZONEID = 'SELECT id FROM zones WHERE CAST(id AS VARCHAR)=TRIM(:zoneidn) OR name=UPPER(TRIM(:zoneidn)) LIMIT 1'

class Execute (BaseModel):
  func: Callable=None
  data: dict={'query':'','values':{},'retquery':None,'retvalues':{},'db_path':None,'many':False,'script':False,'aid':UNKNOWN,'engine':None,'connect':None,'pandas':False}
  check: dict={'err_stat':None,'err_func':None,'err_message':''}

def set_engine (engine):
  return setattr(sys.modules[__name__], 'sys_engine', engine)

def set_connect (connect):
  return setattr(sys.modules[__name__], 'sys_connect', connect)

def say_engine ():
  return print(sys_engine)

def say_connect ():
  return print(sys_connect)

def is_select (query, check='select'):
  return str(query).strip().lower().startswith(check)

def admindb (engine):
  return ADMINDB if engine in [sqlite3, None] else (ADMINDUCKDB if engine in [duckdb] else None)

def dbprefix (engine, defval='x'):
  return '' if engine in [sqlite3, None] else ('d' if engine in [duckdb] else defval)

def get_zonedb (zoneidn, engine):
  return f"{dbprefix(engine)}{ADMINDBNAME if (zoneid:=get_zoneid(zoneidn, engine=engine))==ADMINZONE else (str(zoneid) if zoneid is not None else '')}"

def get_zoneid (zoneidn, engine=None):
  return ADMINZONE if str(zoneidn).upper() in [ADMINZONENAME, str(ADMINZONE)] else check_admin(QUERY_ZONEID, {COL_ZONEIDN: str(zoneidn)}, engine=(engine or sys_engine))

def get_aid (layer=4):
  return callup(layer)

def callup (layer=2):
  return inspect.stack()[layer][3]

def kwarg (**kw):
  return kw

def dict_item (modifier, active, cancel, id, uuid):
  return locals()

def dicts_items (it):
  return [dict_item(it.modifier, it.active, it.cancel, x, None) for x in it.ids] if it.ids else [dict_item(it.modifier, it.active, it.cancel, None, x) for x in it.uuids]

def select_value (query, vals={}, index=0, engine=None):
  return check_admin(query, vals, index, engine=(engine or sys_engine))

def first_row (resultset, defrow=None):
  return resultset_first_row(resultset) if not resultset_is_empty(resultset) else defrow

def reform_model (model):
  return model if type(model) in [dict, list, tuple, str, int, float] else model.model_dump()

def regexp (pattern, text):
  return 1 if re.search(pattern, text) else 0

## SQLITE vs DUCKDB

def sql_replace (text, pat, rep):
  return re.sub(re.escape(pat), rep, text, flags=re.IGNORECASE)

def sql_date_replace (text):
  return re.sub(r'DATE\((.*?)\)', r'CAST(\1 AS DATE)', text, flags=re.IGNORECASE)

def sql_uni_replace (text: str, replaces: dict={}) -> str:
  for key, val in replaces.items(): text = sql_replace(text, key, val)
  return text

def sql_duck_replace (text: str, replaces: dict={}) -> str:
  return sql_date_replace(sql_uni_replace(text, replaces))

def check_valid_naming (column='name'):
  return f"({column} NOT REGEXP '^[0-9]+$')"

def check_valid_naming2 (column='name'):
  return f"(NOT REGEXP_MATCHES({column}, '^[0-9]+$'))"

def duck_replaces ():
  return {
    check_valid_naming(): check_valid_naming2(),
    "DATETIME('now')": 'now()',
    "DATE('now')": 'CAST(now() AS DATE)',
    'AUTOINCREMENT': ''
  }

## STORED FUNCTIONS

def json_extract (json_str, path):
  try:
    json_data = json.loads(json_str)
    path = path.split('$.')[-1]
    path_components = path.split('.')
    value = json_data
    for component in path_components:
      value = value.get(component)
    return value
  except (json.JSONDecodeError, AttributeError, TypeError):
    return None

def update_placeholders (query: str, engine=None, holdermark: str=':', holder: str=PLACEHOLDER) -> str:
  engine = engine or sys_engine
  if type(query) not in [str]: return None
  if engine in [sqlite3, None]: return query
  if engine in [duckdb]: query = sql_duck_replace(query, duck_replaces())
  newmark = '$' if engine in [duckdb] else holdermark
  subs = re.findall(holder, query)
  items = iter(str(e) for e in subs)
  newquery = re.sub(holder, lambda lm: f'{newmark}{next(items)[1:]}', query)
  return newquery

def update_values (query: str, values: dict, engine=None, holder: str=PLACEHOLDER) -> dict:
  engine = engine or sys_engine
  if type(query) not in [str]: return None
  if engine in [sqlite3, None]: return values
  if type(values) not in [dict, list, tuple]: return values
  def update(object):
    if type(object) not in [dict]: return object
    subs = list(set(re.findall(holder, query)))
    subs = [sub[1:] for sub in subs]
    return {key: value for key, value in object.items() if key in subs}
  if type(values) in [list, tuple]:
    newvalues = [update(value) for value in list(values)]
  else:
    newvalues = update(values)
  return newvalues

def get_rowcount (cursor, engine=None):
  engine = engine or sys_engine
  try:
    if engine in [duckdb]:
      (rowcount,) = cursor.fetchone()
    else:
      rowcount = cursor.rowcount
  except:
    rowcount = cursor.rowcount
  return rowcount

def attach (cursor, engine=None):
  try:
    cursor.execute(f"ATTACH DATABASE '{admindb(engine or sys_engine)}' AS admin")
  except:
    pass

def connect_duckdb (db_path: str):
  conn = duckdb.connect(db_path)
  return conn

def connect_sqlite (db_path: str):
  return connect_db(db_path)

def connect_db (db_path: str):
  conn = sqlite3.connect(db_path)
  conn.create_function('json_extract', 2, json_extract)
  conn.create_function('regexp_matches', 2, regexp)
  conn.create_function('regexp', 2, regexp)
  conn.execute(JOURPRAGMA)
  conn.execute(TEMPPRAGMA)
  conn.execute(FKEYPRAGMA)
  return conn

set_engine(sqlite3)

set_connect(connect_sqlite)

def zonedb (zoneid: any, engine=None) -> str:
  engine = engine or sys_engine
  zoneid = get_zonedb(zoneid, engine=engine)
  return None if zoneid is None else f'db/{zoneid}.db'

def getdb (zoneid: any, engine=None) -> str:
  engine = engine or sys_engine
  db = zonedb(zoneid, engine=engine)
  if not db: raise(ValueError(f'DataError: no such database: {zoneid}'))
  return db

def import_zone_database (zoneid: any, table: str, csvdata: any, engine=None) -> dict:
  import io
  import csv
  conn = None
  res = dict_result(aid=callup(1))
  engine = engine or sys_engine
  try:
    if type(csvdata) is str:
      with open(csvdata, 'r', encoding=ENCODINGSIG) as file:
        reader = csv.reader(file)
        headers = next(reader)
        rows = [tuple(row) for row in reader]
    elif type(csvdata) is dict:
      reader = csv.reader(io.StringIO(csvdata.get('data')))
      headers = next(reader)
      rows = [tuple(row) for row in reader]
    else:
      res[ERROR] = f'ReadError: no valid data loaded'
      return res
    placeholders = ','.join(['?' for _ in headers])
    query = f"INSERT INTO {table} ({','.join(headers)}) VALUES ({placeholders})"
    conn = engine.connect(getdb(zoneid, engine=engine))
    cursor = conn.cursor()
    cursor.executemany(query, list(filter(None, rows)))
  except Exception as e:
    res[ERROR] = f'ActionError: {e}'
  finally:
    if conn:
      conn.commit()
      conn.close()
  return res

def export_zone_database (zoneid: any, table: str, csv_path: str=None, idr: list=[], engine=None) -> dict:
  import io
  import csv
  conn = None
  res = dict_result(aid=callup(1))
  where = '' if not idr else f'WHERE id BETWEEN ? AND ?'
  query = f'SELECT * FROM {table} {where}'
  engine = engine or sys_engine
  try:
    conn = engine.connect(getdb(zoneid, engine=engine))
    cursor = conn.cursor()
    cursor.execute(query, idr if where else [])
    rows = cursor.fetchall()
    headers = [description[0] for description in cursor.description]
    def csvwrite(output, headers, rows):
      writer = csv.writer(output)
      writer.writerow(headers)
      writer.writerows(rows)
    if csv_path:
      with open(csv_path, 'w', newline='', encoding=ENCODINGSIG) as output:
        csvwrite(output, headers, rows)
      res[RESULT] = [{'file': csv_path}]
    else:
      output = io.StringIO()
      csvwrite(output, headers, rows)
      res[RESULT] = [{'data': output.getvalue()}]
  except Exception as e:
    res[ERROR] = f'ActionError: {e}'
  finally:
    if conn:
      conn.close()
  return res

def export_database_tables (zoneid: any, engine=None) -> dict:
  conn = None
  res = dict_result(aid=callup(1))
  engine = engine or sys_engine
  if engine in [duckdb]:
    query = "SELECT table_name FROM duckdb_tables"
  elif engine in [sqlite3, None]:
    query = "SELECT name FROM sqlite_master WHERE type='table'"
  else:
    query = ""
  try:
    conn = engine.connect(getdb(zoneid, engine=engine))
    cursor = conn.cursor()
    cursor.execute(query)
    tables = cursor.fetchall()
    tables = [table[0] for table in tables]
    res[RESULT] = tables
  except Exception as e:
    res[ERROR] = f'ActionError: {e}'
  finally:
    if conn:
      conn.close()
  return res

def check_admin (query: str, values: dict={}, index=0, engine=None) -> dict:
  engine = engine or sys_engine
  conn = None
  try:
    conn = engine.connect(getdb(ADMINDBNAME, engine=engine))
    cursor = conn.cursor()
    cursor.execute(update_placeholders(query, engine), update_values(query, values, engine))
    rows = cursor.fetchone()
    return None if not rows else rows[index]
  except Exception as e:
    return None
  finally:
    if conn:
      conn.close()

def out_pandas (conn, query: str, values: dict={}, simplelist: bool=False, dataindex: int=0):
  import pandas as pd
  df = pd.read_sql_query(query, conn, params=values)
  if simplelist: return df.iloc[:,dataindex]
  return df

## CORE FUNCTIONS

def execute_table_create_insert_update (db_path: str, query: str, values: dict={}, retquery: str=None, retvalues: dict={}, many: bool=False, script: bool=False, aid: str=UNKNOWN, engine=None, connect=None, pandas: bool=False) -> dict:
  engine = engine or sys_engine
  connect = connect or sys_connect
  conn = None
  try:
    conn = connect(db_path)
    cursor = conn.cursor()
    attach(cursor, engine=engine)
    if script and engine in [sqlite3, None]:
      cursor.executescript(query)
    else:
      newquery = update_placeholders(query, engine)
      newvalues = update_values(query, values, engine)
      if many:
        cursor.executemany(newquery, newvalues)
      else:
        cursor.execute(newquery, newvalues)
    rowcount = get_rowcount(cursor, engine)
    conn.commit()
    if rowcount==0:
      return error_database(NOROWCOUNT)
    if retquery is None:
      return dict_result(aid=aid)
    elif not is_select(retquery):
      return dict_result(err=ERRORINPUT, aid=aid)
    else:
      if pandas:
        return dict_result(out_pandas(conn, update_placeholders(retquery, engine), update_values(retquery, retvalues, engine)), aid=aid)
      else:
        return fetch_table_as_list_of_dict(db_path, retquery, retvalues, aid=aid, engine=engine, connect=connect)
  except engine.Error as e:
    conn.rollback()
    return error_database(e)
  except Exception as e:
    return error_unexpect(e)
  finally:
    if conn:
      conn.close()

def fetch_table_as_list_of_dict (db_path: str, query: str, values: dict={}, retquery=None, retvalues=None, many: bool=False, script: bool=False, aid: str=UNKNOWN, engine=None, connect=None, pandas: bool=False) -> dict:
  engine = engine or sys_engine
  connect = connect or sys_connect
  conn = None
  try:
    conn = connect(db_path)
    cursor = conn.cursor()
    attach(cursor, engine=engine)
    newquery = update_placeholders(query, engine)
    newvalues = update_values(query, values, engine)
    if pandas:
      return dict_result(out_pandas(conn, newquery, newvalues), aid=aid)
    cursor.execute(newquery, newvalues)
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    list_of_dicts = [dict(zip(columns, row)) for row in rows]
    return dict_result(result=list_of_dicts, aid=aid)
  except engine.Error as e:
    return error_database(e)
  except Exception as e:
    return error_unexpect(e)
  finally:
    if conn:
      conn.close()

def fetch_table_as_simple_list (db_path: str, query: str, values: dict={}, retquery=None, retvalues=None, many: bool=False, script: bool=False, aid: str=UNKNOWN, engine=None, connect=None, pandas: bool=False) -> dict:
  engine = engine or sys_engine
  connect = connect or sys_connect
  conn = None
  try:
    conn = connect(db_path)
    cursor = conn.cursor()
    attach(cursor, engine=engine)
    newquery = update_placeholders(query, engine)
    newvalues = update_values(query, values, engine)
    if pandas:
      return dict_result(out_pandas(conn, newquery, newvalues, simplelist=True), aid=aid)
    cursor.execute(newquery, newvalues)
    rows = cursor.fetchall()
    rows = [row[0] for row in rows]
    return dict_result(result=rows, aid=aid)
  except engine.Error as e:
    return error_database(e)
  except Exception as e:
    return error_unexpect(e)
  finally:
    if conn:
      conn.close()

def resultset_first_row (result: dict) -> dict:
  try:
    row = result[RESULT][0]
    if type(row) is dict: return row
    return {}
  except:
    return {}

def resultset_is_empty (result: dict) -> bool:
  try:
    return (result.get(ERROR) is not None) or (not result.get(RESULT))
  except:
    return True

def dict_result (result: list=[], err: str=None, scope: str=UNKNOWN, aid: str=UNKNOWN) -> dict:
  if err is None:
    return {ACTION: aid, ERROR: None, RESULT: result}
  else:
    return {ACTION: aid, ERROR: f"{scope}: {err}", RESULT: []}

def error_database (err: str, aid: str=UNKNOWN) -> dict:
  return dict_result([], err, DBERROR, aid=aid)

def error_unexpect (err: str, aid: str=UNKNOWN) -> dict:
  return dict_result([], err, UNERROR, aid=aid)

def db_exist (db_path: str, engine=None) -> bool:
  engine = engine or sys_engine
  try:
    if os.path.isfile(db_path):
      if os.path.getsize(db_path)>100:
        with open(db_path,'r', encoding=ENCODING) as f:
          header = f.read(100)
          if engine in [sqlite3, None]: return header.startswith(DBENGINE)
          if engine in [duckdb]: return header[8:].startswith(DUCKDBENGINE)
    return False
  except:
    return False

def setquery (model: Execute, query: str, aid: str=UNKNOWN):
  model.data['query'] = query
  model.data['aid'] = aid

def setretquery (model: Execute, query: str):
  model.data['retquery'] = query

def setvals (model: Execute, vals: dict={}):
  model.data['values'] = vals

def setretvals (model: Execute, vals: dict={}):
  model.data['retvalues'] = vals

def setmany (model: Execute, val: bool=False):
  model.data['many'] = val

def setscript (model: Execute, val: bool=False):
  model.data['script'] = val

def setpandas (model: Execute, val: bool=False):
  model.data['pandas'] = val

def setengine (model: Execute, val=None):
  model.data['engine'] = val or sys_engine

def setconnect (model: Execute, val=None):
  model.data['connect'] = val or sys_connect

def setdbpath (model: Execute, val: str):
  model.data['db_path'] = val

def db_execute (db_caller: Execute) -> dict:
  if db_caller.check['err_stat']: return db_caller.check['err_func'](db_caller.check['err_message'])
  return db_caller.func(**db_caller.data)

def batch (queries: list, db_path: str=None, engine=None, connect=None) -> dict:
  engine = engine or sys_engine
  connect = connect or sys_connect
  if not db_path: db_path = admindb(engine)
  caller = Execute(func=execute_table_create_insert_update)
  setquery(caller, ';'.join(queries))
  setscript(caller, True)
  setengine(caller, engine)
  setconnect(caller, connect)
  setdbpath(caller, db_path)
  return db_execute(caller)

db_insert = execute_table_create_insert_update

db_select = fetch_table_as_list_of_dict

db_list = fetch_table_as_simple_list

def select_dict (query: str, model: BaseModel, db_path: str=None, func=db_select, layer=4, engine=None, connect=None, pandas: bool=False, **kw) -> dict:
  engine = engine or sys_engine
  connect = connect or sys_connect
  if not db_path: db_path = admindb(engine)
  caller = Execute(func=func)
  setquery(caller, query, aid=get_aid(layer))
  setvals(caller, reform_model(model))
  setengine(caller, engine)
  setconnect(caller, connect)
  setdbpath(caller, db_path)
  setpandas(caller, pandas)
  return db_execute(caller)

def select_list (query: str, model: BaseModel, db_path: str=None, engine=None, connect=None, pandas: bool=False, **kw) -> dict:
  engine = engine or sys_engine
  connect = connect or sys_connect
  return select_dict(func=db_list, query=query, model=model, db_path=db_path, engine=engine, connect=connect, pandas=pandas)

def insert_one (query: str, model: BaseModel, retquery: str='', db_path: str=None, layer=4, engine=None, connect=None, pandas: bool=False, **kw) -> dict:
  engine = engine or sys_engine
  connect = connect or sys_connect
  if not db_path: db_path = admindb(engine)
  caller = Execute(func=db_insert)
  setquery(caller, query, aid=get_aid(layer))
  setretquery(caller, retquery)
  data = reform_model(model)
  if type(data) is dict:
    if data.get(ARRAY):
      data[COL_LIMIT] = len(model.array)
      setvals(caller, model.array)
      setmany(caller, True)
    else:
      setvals(caller, data)
    setretvals(caller, data) ##limit
  else:
    setvals(caller, data)
    setretvals(caller, kw.get('retvalues'))
  setengine(caller, engine)
  setconnect(caller, connect)
  setdbpath(caller, db_path)
  setpandas(caller, pandas)
  return db_execute(caller)

create_one = insert_one

update_one = insert_one

delete_one = insert_one

insert_many = insert_one

create_many = insert_many

update_many = insert_many

delete_many = insert_many
