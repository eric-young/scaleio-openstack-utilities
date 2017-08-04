# list-sio-volumes

Utility to list the mappings between OpenStack and ScaleIO volumes

## Usage

Invoking the script with no arguments, or -h, whill show usage:
```
usage: list-sio-volumes.py [-h] --os_auth_url OS_AUTH_URL
                           --os_tenant OS_TENANT
                           --os_user OS_USER
                           --os_pass OS_PASS
                           [--os_all_tenants]
                           --sio_gateway SIO_GATEWAY
                           [--sio_port SIO_PORT]
                           --sio_user SIO_USER
                           --sio_pass SIO_PASS

List OpenStack volumes and corresponding ScaleIO volumes

optional arguments:
  -h, --help                  show this help message and exit
  --os_auth_url OS_AUTH_URL   OpenStack Authorization URL
  --os_tenant OS_TENANT       OpenStack Tenant Name
  --os_user OS_USER           OpenStack User
  --os_pass OS_PASS           OpenStack Password
  --os_all_tenants            Show volumes from all tenants
  --sio_gateway SIO_GATEWAY   ScaleIO Gateway
  --sio_port SIO_PORT         ScaleIO Gateway Port
  --sio_user SIO_USER         ScaleIO User
  --sio_pass SIO_PASS         ScaleIO Password

```

## Notes:

For Newton and Ocata, the OS_AUTH_URL should be the v2.0 URL:
http://<ipaddress>:5000/v2.0

For Pike, the OS_AUTH_URL should be in the form of:
http://<ipaddress>/identity

## Requirements

Requires a few python modules which can be installed via pip
```
pip install -r requirements.txt
```

 
