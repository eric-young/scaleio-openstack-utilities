#!/usr/bin/env python
#
# list openstack volumes and their corresponding ScaleIO volumes
#
# requires two pip modules to be installed via pip:
#     openstacksdk
#     siolib
#

import argparse
import base64
import binascii
from openstack import connection
from siolib import ScaleIO
import six


class VolumeLister:
    """A simple example class"""
    format_string = '%-40s%-30s%-10s'
    args = None
    openstack = None
    scaleio = None

    def __init__(self, args):
        self.args = args

    @staticmethod
    def setup_arguments():
        parser = argparse.ArgumentParser(
            description='List OpenStack volumes and corresponding ScaleIO volumes')

        # openstack configuration
        parser.add_argument('--os_auth_url', dest='OS_AUTH_URL', action='store', required=True,
                            help='OpenStack Authorization URL')
        parser.add_argument('--os_tenant', dest='OS_TENANT', action='store', required=True,
                            help='OpenStack Tenant Name')
        parser.add_argument('--os_user', dest='OS_USER', action='store', required=True,
                            help='OpenStack User')
        parser.add_argument('--os_pass', dest='OS_PASS', action='store', required=True,
                            help='OpenStack Password')

        # scaleio configuration
        parser.add_argument('--sio_gateway', dest='SIO_GATEWAY', action='store', required=True,
                            help='ScaleIO Gateway')
        parser.add_argument('--sio_port', dest='SIO_PORT', action='store', required=False,
                            default='443', help='ScaleIO Gateway Port')
        parser.add_argument('--sio_user', dest='SIO_USER', action='store', required=True,
                            help='ScaleIO User')
        parser.add_argument('--sio_pass', dest='SIO_PASS', action='store', required=True,
                            help='ScaleIO Password')

        # return the parser object
        return parser

    @staticmethod
    def _convert_os_to_sio(id):
        # Base64 encode the id to get a volume name less than 32 characters due
        # to ScaleIO limitation.
        name = six.text_type(id).replace("-", "")
        try:
            name = base64.b16decode(name.upper())
        except (TypeError, binascii.Error):
            pass
        encoded_name = name
        if isinstance(encoded_name, six.text_type):
            encoded_name = encoded_name.encode('utf-8')
        encoded_name = base64.b64encode(encoded_name)
        if six.PY3:
            encoded_name = encoded_name.decode('ascii')
        return encoded_name

    def connect(self):
        self.openstack = connection.Connection(auth_url=self.args.OS_AUTH_URL,
                                               project_name=self.args.OS_TENANT,
                                               username=self.args.OS_USER,
                                               password=self.args.OS_PASS)

        self.scaleio = ScaleIO(rest_server_ip=self.args.SIO_GATEWAY,
                               rest_server_port=self.args.SIO_PORT,
                               rest_server_username=self.args.SIO_USER,
                               rest_server_password=self.args.SIO_PASS)

    def list_volumes(self):
        print(self.format_string % ("OpenStack Volume", "ScaleIO Volume", "Attached"))
        for os_volume in self.openstack.block_store.volumes(details=True, all_tenants=True):
            sio_volume = self._convert_os_to_sio(os_volume.id)
            try:
                self.scaleio._volume(sio_volume)
                attached = 'True'
                if not os_volume.attachments:
                    attached = 'False'
                print(self.format_string % (os_volume.id, sio_volume, attached))
            except:
                # if we got here, there is no SIO volume for the openstack volume
                pass

    def process(self):
        self.connect()
        self.list_volumes()


if __name__ == "__main__":
    parser = VolumeLister.setup_arguments()
    args = parser.parse_args()

    lister = VolumeLister(args)
    lister.process()
