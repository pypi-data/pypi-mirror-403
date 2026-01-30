def full_year (column, yyyy):
  return f"(CAST(STRFTIME('%Y', {column}) AS INT) = CAST({yyyy} AS INT))"

def year_month (column, yyyy, mm):
  return f"(CAST(STRFTIME('%Y', {column}) AS INT) = CAST({yyyy} AS INT) AND CAST(STRFTIME('%m', {column}) AS INT) = CAST({mm} AS INT))"

def date_between (column, dd1, dd2):
  return f'(DATE({column}) BETWEEN DATE({dd1}) AND DATE({dd2}))'

def moderators_of_system ():
  return f'(SELECT id FROM users WHERE zone=0)'

def admins_of_system ():
  return f'(SELECT id FROM users WHERE zone=0 AND zadmin=1)'

def items_of_sub (sub_placeholder):
  return f'(SELECT id FROM items WHERE sub={sub_placeholder})'

def subs_of_account (account_placeholder):
  return f'(SELECT id FROM subs WHERE account={account_placeholder})'

def column_setting (column, cplaceholder, placeholder):
  return f"{column} = CASE WHEN {cplaceholder} != '' THEN {placeholder} ELSE {column} END"

def close_items_listing (limit, offset):
  return f'ORDER BY CAST(subs.account AS VARCHAR), subs.code, items.head LIMIT {limit} OFFSET {offset}'

def close_subs_listing (limit, offset):
  return f'ORDER BY CAST(subs.account AS VARCHAR), subs.code LIMIT {limit} OFFSET {offset}'

def accounts_of_code_like (code_placeholder):
  return f"(SELECT id FROM accounts WHERE code LIKE '%'||{code_placeholder}||'%')"

def check_sub_identify (id_placeholder, account_placeholder, code_placeholder):
  return f'(id={id_placeholder} OR (account={account_placeholder} AND code=UPPER(TRIM({code_placeholder}))))'

def check_sub_acc_like (placeholder):
  return f"CAST(subs.account AS VARCHAR) LIKE '%'||{placeholder}||'%'"

def check_uid_identify (id_placeholder, uuid_placeholder):
  return f'(id={id_placeholder} OR uuid={uuid_placeholder})'

def check_uid_identifies (ids_placeholder, uuids_placeholder):
  return f'(id IN ({ids_placeholder}) OR uuid IN ({uuids_placeholder}))'

def check_item_uid_identify (id_placeholder, uuid_placeholder):
  return f'(items.id={id_placeholder} OR items.uuid={uuid_placeholder})'

def check_item_uid_identifies (ids_placeholder, uuids_placeholder):
  return f'(items.id IN ({ids_placeholder}) OR items.uuid IN ({uuids_placeholder}))'

def role_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM roles WHERE id={id_placeholder})'

def specrole_exists (spec_placeholder, role_placeholder):
  return f'EXISTS (SELECT 1 FROM specroles WHERE spec={spec_placeholder} AND role={role_placeholder})'

def userrole_exists (user_placeholder, role_placeholder):
  return f'EXISTS (SELECT 1 FROM userroles WHERE user={user_placeholder} AND role={role_placeholder})'

def spec_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM specs WHERE id={id_placeholder})'

def userspec_exists (user_placeholder, spec_placeholder):
  return f'EXISTS (SELECT 1 FROM userspecs WHERE user={user_placeholder} AND spec={spec_placeholder})'

def group_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM groups WHERE id={id_placeholder})'

group_id_exists = group_exists

def root_exists (id_placeholder, code_placeholder):
  return f'EXISTS (SELECT 1 FROM roots WHERE id={id_placeholder} OR code=UPPER(TRIM({code_placeholder})))'

def root_id_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM roots WHERE id={id_placeholder})'

def account_exists (id_placeholder, code_placeholder):
  return f'EXISTS (SELECT 1 FROM accounts WHERE id={id_placeholder} OR code=UPPER(TRIM({code_placeholder})))'

def account_id_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM accounts WHERE id={id_placeholder})'

def sub_exists (code_placeholder, account_placeholder):
  return f'EXISTS (SELECT 1 FROM subs, accounts WHERE subs.code=UPPER(TRIM({code_placeholder})) AND subs.account={account_placeholder} AND subs.account=accounts.id)'

def sub_id_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM subs WHERE id={id_placeholder})'

def zone_exists (id_placeholder, name_placeholder):
  return f'EXISTS (SELECT 1 FROM zones WHERE id={id_placeholder} OR name=UPPER(TRIM({name_placeholder})))'

def zone_id_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM zones WHERE id={id_placeholder})'

def attach_user_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM admin.users WHERE id={id_placeholder})'

def attach_user_check (idname_placeholder):
  return f'(SELECT id FROM admin.users WHERE {check_idname(idname_placeholder)})'

def user_name_exists (name_placeholder):
  return f'EXISTS (SELECT 1 FROM users WHERE name=LOWER(TRIM({name_placeholder})))'

def user_id_exists (id_placeholder):
  return f'EXISTS (SELECT 1 FROM users WHERE id={id_placeholder})'

def check_obj_active (active_placeholder):
  return f'(obj.active = (CASE WHEN {active_placeholder} IN (0,1) THEN {active_placeholder} ELSE obj.active END))'

def check_obj_zone_name (name_placeholder):
  return f'(obj.zone = (SELECT id FROM zones WHERE name=UPPER(TRIM({name_placeholder})) LIMIT 1))'

def check_obj_zoneidn (id_placeholder, name_placeholder):
  return f'(obj.zone = (SELECT id FROM zones WHERE {check_zone_id_or_name(id_placeholder, name_placeholder)} LIMIT 1))'

def check_user_id_or_name (id_placeholder, name_placeholder):
  return f'(id={id_placeholder} OR name=LOWER(TRIM({name_placeholder})))'

def check_strict_user_id_or_name (id_placeholder, name_placeholder):
  return f'(users.id={id_placeholder} OR users.name=LOWER(TRIM({name_placeholder})))'

def check_strict_user_worktime (worktime_placeholder):
  return f"(users.workend IS NULL OR DATE({worktime_placeholder}) BETWEEN IFNULL(DATE(users.workbegin), DATE('1900-01-01')) AND DATE(users.workend))"

def check_strict_user_working (worktime_placeholder):
  return f'({check_strict_user_active()} AND {check_strict_user_worktime(worktime_placeholder)})'

def check_strict_user_active ():
  return f'(users.active=1 AND users.zone IN (SELECT id FROM zones WHERE active=1))'

def check_zone_id_or_name (id_placeholder, name_placeholder):
  return f'(id={id_placeholder} OR name=UPPER(TRIM({name_placeholder})))'

def set_user_note (cnote_placeholder, note_placeholder, modifier_placeholder):
  return f"note = CASE WHEN {cnote_placeholder} != '' THEN (IFNULL(note,'') || '\n' || {note_placeholder} || ' [uid.' || IFNULL({modifier_placeholder},'N/A') || '] ' || DATETIME('now')) ELSE note END"

def set_user_modify (modifier_placeholder):
  return f"modified=(DATETIME('now')), modifier={modifier_placeholder}"

set_modifier_value = set_user_modify

def check_user_id (id_placeholder, name_placeholder):
  return f'((user={id_placeholder} OR users.name=LOWER(TRIM({name_placeholder}))) AND user=users.id)'

def check_user_in_specs (user_placeholder, name_placeholder):
  return f'({check_user_id(user_placeholder, name_placeholder)} AND spec=specs.id)'

def check_user_in_roles (user_placeholder, name_placeholder):
  return f'({check_user_id(user_placeholder, name_placeholder)} AND role=roles.id)'

def check_user_spec (user_placeholder, name_placeholder, spec_placeholder):
  return f'({check_user_id(user_placeholder, name_placeholder)} AND spec={spec_placeholder})'

def check_user_role (user_placeholder, name_placeholder, role_placeholder):
  return f'({check_user_id(user_placeholder, name_placeholder)} AND role={role_placeholder})'

def check_user_spec_in_specs (user_placeholder, name_placeholder, spec_placeholder):
  return f'({check_user_id(user_placeholder, name_placeholder)} AND spec={spec_placeholder} AND spec=specs.id)'

def check_user_role_in_roles (user_placeholder, name_placeholder, role_placeholder):
  return f'({check_user_id(user_placeholder, name_placeholder)} AND role={role_placeholder} AND role=roles.id)'

check_id_or_uuid = check_uid_identify

def check_id_or_name (id_placeholder, name_placeholder):
  return f'(id={id_placeholder} OR LOWER(TRIM(name))=LOWER(TRIM({name_placeholder})))'

def check_iduuid (placeholder):
  return f'(TRIM(CAST(id AS VARCHAR))=TRIM({placeholder}) OR LOWER(TRIM(uuid))=LOWER(TRIM({placeholder})))'

def check_idname (placeholder):
  return f'(TRIM(CAST(id AS VARCHAR))=TRIM({placeholder}) OR LOWER(TRIM(name))=LOWER(TRIM({placeholder})))'

def check_strict_idname (placeholder):
  return f'(TRIM(CAST(users.id AS VARCHAR))=TRIM({placeholder}) OR LOWER(TRIM(users.name))=LOWER(TRIM({placeholder})))'

def check_ones_admin (zone_placeholder, user_placeholder):
  return f'(zadmin=1 AND zone IN ({zone_of_zoneuser(zone_placeholder,user_placeholder)}))'

def check_ones_admin_or_moderator (zone_placeholder, user_placeholder):
  return f'(zone=0 OR {check_ones_admin(zone_placeholder,user_placeholder)})'

check_admin_or_moderator_of = check_ones_admin_or_moderator

check_admin_of = check_ones_admin

def zone_of_user (user_placeholder):
  return f'(SELECT zone FROM users WHERE {check_idname(user_placeholder)})'

def zone_by_user (user_placeholder):
  return f'(SELECT id FROM zones WHERE id IN {zone_of_user(user_placeholder)})'

def zone_by_idname (idn_placeholder):
  return f'(SELECT id FROM zones WHERE id={idn_placeholder} OR name=UPPER(TRIM({idn_placeholder})) LIMIT 1)'

def zone_of_zoneuser (zone_placeholder, user_placeholder):
  return f'(SELECT id FROM zones WHERE {check_idname(zone_placeholder)} OR id IN {zone_of_user(user_placeholder)})'

def zone_case_idname (zone_placeholder):
  return f"(CASE WHEN {zone_placeholder} != '' THEN (SELECT id FROM zones WHERE {check_idname(zone_placeholder)}) ELSE zone END)"

def get_zoneidn_by_useridn (zone_placeholder, user_placeholder):
  return f"(CASE WHEN {user_placeholder} != '' THEN {zone_by_user(user_placeholder)} ELSE {zone_case_idname(zone_placeholder)} END)"

def zone_case_system (zone_placeholder, zone='zone'):
  return f"(CASE WHEN TRIM({zone_placeholder})='0' OR UPPER(TRIM({zone_placeholder}))='ADMIN' THEN {zone} ELSE (SELECT id FROM zones WHERE {check_idname(zone_placeholder)} LIMIT 1) END)"

def increase_id (table):
  return f'(SELECT IFNULL(MAX(id),0)+1 FROM {table})'

def search_idname (table, placeholder, fields='*'):
  return f"SELECT {fields} FROM {table} WHERE (CAST(id AS VARCHAR) LIKE '%'||{placeholder}||'%' OR name LIKE '%'||{placeholder}||'%')"

def limit_offset (limnum, setnum):
  return f'{limit(limnum)} {offset(setnum)}'

def offset (num):
  return f'\n OFFSET {num}'

def limit (num):
  return f'\n LIMIT {num}'

def multi_holders (query, lst):
  return query.replace('??', ','.join(['(?)' for x in lst]))

def uuid_value ():
  return "lower(hex(randomblob(4)))||'-'||lower(hex(randomblob(2)))||'-4'||substr(lower(hex(randomblob(2))),2)||'-'||substr('89ab',abs(random())%4+1,1)||substr(lower(hex(randomblob(2))),2)||'-'||lower(hex(randomblob(6)))"

def empty_json ():
  return '{}'
