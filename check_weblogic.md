# Nagios Weblogic Cluster check script

checking weblogic cluster script

### requirement
1. python 3.6
2. weblogic Server 12.1.1

### check model
1. server<br>
check servers (admin and managed servers) status
http://host:port/management/tenant-monitoring/servers
2. ear<br>
check application status
http://host:port/management/tenant-monitoring/applications/application_name
3. datasource<br>
check datasource status
http://host:port/management/tenant-monitoring/datasources/datasource_name

### install
On the Weblogic server admin console, enable the RESTful management service in domain generic advance setting
install Python3.6
```
yum install -y https://centos7.iuscommunity.org/ius-release.rpm
yum install -y python36u python36u-pip
pip3.6 install requests
```
call this script as folowing
```
check_weblogic.py -m datasource --host=192.15.3.4 --port=7001 --url=management/tenant-monitoring/servers --user=userName --password=yourPASSWORD
```
