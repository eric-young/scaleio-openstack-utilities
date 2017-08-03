# list-sio-volumes

Utility to list the mappings between OpenStack and ScaleIO volumes

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
```

Requires a few python modules which can be installed via pip
```
pip install -r requirements.txt
```

 
