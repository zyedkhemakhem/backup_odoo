import os
import subprocess
import sys
from os.path import expanduser

def get_argument_value(argument):
    try:
        index = sys.argv.index(argument) + 1
        return sys.argv[index]
    except (ValueError, IndexError):
        return None

odoo_container = get_argument_value('--odoo_container')
database_container = get_argument_value('--database_container')
base_name = get_argument_value('--newdatabase')  # database_name_jdida
restore_name = get_argument_value('--olddatabase')  # data_base_name_9dima
masterpassword = get_argument_value('--masterpassword')
#exemple de script pour lancement d'une commande ::    python3 test.py --odoo_container docker-compose_odoo_summer2024_1 --database_container psql_summer2024 --newdatabase ous  --olddatabase tayara_2024-07-17_08-25-33.zip --masterpassword Welcome@summer2024
if odoo_container and database_container and base_name and restore_name and masterpassword:
    output = subprocess.check_output(
        f"docker exec {odoo_container} bash -c 'PGPASSWORD=odoo psql -h {database_container} -U odoo -d postgres -t -A -c \"SELECT datname FROM pg_database WHERE datname NOT IN ('\\'postgres\\'', '\\'template0\\'', '\\'template1\\'');\"'",
        shell=True,
        text=True
    )
    database_list = output.strip().split()
    print(database_list)
    
    if base_name in database_list:
        print("Database already exists.")
    else:
        if '.dump' in restore_name:
            subprocess.run(
                f"docker exec -it {database_container} bash -c \"PGPASSWORD='odoo' createdb {base_name} -U odoo -E UTF8 --host {database_container}\"",
                shell=True, check=True)
            subprocess.run(
                f"docker exec -it {database_container} bash -c \"cd /mnt/backup && PGPASSWORD='odoo' pg_restore --host {database_container} --username odoo --dbname {base_name} --role odoo --verbose {restore_name}\"",
                shell=True, check=True)
        elif '.zip' in restore_name:
            home = expanduser("~")        
            os.chdir(home)  
            subprocess.run(
                f'curl -F "master_pwd={masterpassword}" -F "name={base_name}" -F "backup_file=@{restore_name}" -F "copy=true" http://localhost:8069/web/database/restore',
                shell=True, check=True)

        sql_commands = [
            "UPDATE ir_config_parameter SET value=md5(random()::text) WHERE key='database.uuid';",
            "DELETE FROM ir_mail_server;",
            "DELETE FROM fetchmail_server;",
            "UPDATE ir_cron SET active = False;",
            "UPDATE res_users SET login = 'admin' WHERE id=2;",
            "UPDATE res_users SET password = 'admin' WHERE id=2;"
        ]
        
        for command in sql_commands:
            os.system(
                f"docker exec -i {odoo_container} bash -c \"PGPASSWORD=odoo psql -h {database_container} -U odoo -d {base_name} -c \\\"{command}\\\"\"")
else:
    print("missing arguments you must include all of them :  --odoo_container --database_container --newdatabase --olddatabase --masterpassword")

