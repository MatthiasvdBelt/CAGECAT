#!/bin/bash
# Author: Matthias van den Belt

fp="/backups/$(date +"%Y%m%d")_backup"
todays_backup="$(date +"%Y%m%d")_backup"

echo "Creating directory: $fp"
mkdir $fp

echo "Copying jobs folder to $fp/jobs"
cp -r /repo/cagecat/jobs "$fp"

echo "Copying SQL database  to $fp/database.db"
cp /repo/cagecat/database.db "$fp"

echo "Copying config.py to $fp/config.py (CAGECAT's version number)"
cp /repo/config_files/config.py "$fp"

echo "Writing cblaster version to $fp/cblaster_version.txt"
/miniconda3/bin/cblaster --version > "$fp/cblaster_version.txt"

echo "Listing HMM databases to $fp/hmm_databases.txt"
ls -lR /hmm_databases/ > "$fp/hmm_databases.txt"

echo "Copying logs folder to $fp/process_logs"
cp -r /process_logs "$fp"

pckgs_linux="$fp/linux_packages.txt"
echo "Writing installed Linux packages to $pckgs_linux"
apt list --installed > "$pckgs_linux"

libs_python="$fp/python_libs.txt"
echo "Writing installed Python libraries to $libs_python"
/miniconda3/bin/pip freeze > "$libs_python"

crontab_fn="$fp/cron_commands.txt"
echo "Writing crontab to $crontab_fn"
crontab -l > "$crontab_fn"

echo "Compressing in to $fp.tar.gz"
cd "/backups" || exit
tar cvf - $todays_backup --remove-files | gzip -9 - > $fp.tar.gz

echo "Finished. Backup available at $fp.tar.gz"
