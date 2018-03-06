# Nagios Oracle RAC Database check script

checking oracle rac and db status script

### requirement
1. python 3.6
2. oracle rac 11.2.0.4

### check model
1. rac_crs<br>
check rac crs daemon using crsctl
2. rac_srv<br>
check rac using srvctl
3. rac_asm<br>
check rac asm disk group using asmcmd
4. rac_listener<br>
check rac listener using lsnrctl
5. db_status<br>
check db status
6. db_tablespace<br>
check db free tablespace size
7. db_rmanfullbackup<br>
check db rman full backup
8. db_dataguard<br>
check db dataguard status

### install
On the oracle server, install oracle instanceclient
```
unzip instantclient-basic-linux.x64-11.2.0.4.0.zip -d /opt/oracle
unzip  instantclient-sqlplus-linux.x64-11.2.0.4.0.zip -d /opt/oracle
cd /opt/oracle/instantclient_11_2
ln -s libclntsh.so.11.1 libclntsh.so
ln -s libocci.so.12.1 libocci.so
```
install nrpe services
```
yum install -y nrpe
systemctl enable nrpe
systemctl start nrpe
```
install Python3.6
```
yum install -y https://centos7.iuscommunity.org/ius-release.rpm
yum install -y python36u python36u-pip
```
install cx_Oracle
```
usermod -s /bin/bash nrpe
su - nrpe
echo "LD_LIBRARY_PATH=/opt/oracle/instantclient_11_2:$LD_LIBRARY_PATH" >> .bash_profile
echo "PATH=$PATH:/opt/oracle/instantclient_11_2" >> .bash_profile
echo "export LD_LIBRARY_PATH PATH" >> .bash_profile
source .bash_profile
mkdir -p .local/lib/python3.6/site-packages
pip3.6 install --target=.local/lib/python3.6/site-packages cx_Oracle
```
modify sudoers
```
#visudo -f /etc/sudoers, allow enviorment variable
Defaults    env_keep += "ORACLE_SID ORACLE_HOME"

#visudo -f /etc/sudoers.d/nrpe
nrpe ALL=(grid) NOPASSWD:/u01/app/11.2.0/grid/bin/asmcmd
```
add nrpe to oinstall group, this make nrpe user can execute oracle bin files
```
usermod -a -G oinstall nrpe
```
when check model is rac_xxxx, you should pass oh,sid,user
```
check_oracle.py -m rac_crs --oh=/u01/app/11.2.0/grid
check_oracle.py -m rac_asm --oh=/u01/app/11.2.0/grid --user=grid --sid=+ASM1
```
when check model is db_xxxxx, you should add a query user in oracle
```
CREATE USER nrpe IDENTIFIED BY yourPASSWORD;
GRANT CREATE SESSION TO nrpe;
GRANT SELECT ON V_$RMAN_BACKUP_JOB_DETAILS TO nrpe;
GRANT SELECT ON dba_tablespaces TO nrpe;
GRANT SELECT ON dba_data_files TO nrpe;
```
and call this script as folowing
```
check_oracle.py -m db_status --host=192.15.3.4 --port=1521 --user=nrpe --password=yourPASSWORD
check_oracle.py -m db_tablespace --host=192.15.3.4 --port=1521 --user=nrpe --password=yourPASSWORD
```
when check model is db_dataguard, this script should execute at the dataguard server with sysdba role
```
when execute via nrpe, you should pass LD_LIBRARY_PATH to this script
/usr/bin/env LD_LIBRARY_PATH=/path/to/instantclient_12_2 /path/to/check_oracle.py
check_oracle.py -m db_dataguard --host=localhost --port=1521 --user=sys --password=yourpassword --sid=yoursid
```
