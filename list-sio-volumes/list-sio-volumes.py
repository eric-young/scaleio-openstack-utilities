#!/usr/bin/env python
#
# list openstack volumes and their corresponding ScaleIO volumes
#
# requires a few pip modules to be installed via pip:
#     openstacksdk
#     requests
#     six
#

import argparse
import base64
import binascii
from openstack import connection
import requests
import six
from urllib import quote


class SIOWrapper:
    gateway_address = None
    gateway_port = None
    sio_user = None
    sio_pass = None
    sio_token = None

    def __init__(self, gateway, port, user, password):
        self.gateway_address = gateway
        self.gateway_port = port
        self.sio_user = user
        self.sio_pass = password

    def _get(self, r_uri):
        """
        executes a REST GET of the provided URI
        :param r_uri: The endpoint to invoke, not including scheme, hostname, port
        :return: response of the query
        """

        r_uri = "https://" + self.gateway_address + ":" + self.gateway_port + r_uri
        r = requests.get(r_uri,
                         auth=(self.sio_user, self.sio_token),
                         verify=False)
        r = self._check_response(r, r_uri)
        response = r.json()

        return r, response

    def _check_response(self, response, request):
        """
        checks the response from a REST GET, re-authenticates and re-executes
        query if needed
        :param response: The response from a prior GET call
        :param request: The original request, in case it needs to be re-issued
        :return: response of the query
        """

        if (response.status_code == 401 or
            response.status_code == 403):
            login_request = ("https://" + self.gateway_address +
                             ":" + self.gateway_port + "/api/login")
            r = requests.get(login_request,
                    auth=(self.sio_user, self.sio_pass),
                    verify=False)
            token = r.json()
            self.sio_token = token
            # Repeat request with valid token.
            response = requests.get(request,
                auth=(self.sio_user, self.sio_token),
                verify=False)

        return response

    def encode_string(self, value, double=False):
        """
        Url encode a string to ASCII in order to escape any characters not
         allowed :, /, ?, #, &, =. If parameter 'double=True' perform two passes
         of encoding which may be required for some REST api endpoints. This is
         usually done to remove any additional special characters produce by the
         single encoding pass.
        :param value: Value to encode
        :param double: Double encode string
        :return: encoded string
        """

        # Replace special characters in string using the %xx escape
        encoded_str = quote(value, '')
        if double:  # double encode
            encoded_str = quote(encoded_str, '')

        return encoded_str

    def get_volumeid(self, volume_name):
        """
        Return ScaleIO volume ID given a unique string volume name
        :param volume_name: Unique 32 character string name of the volume
        :return: ScaleIO ID of volume
        """

        volume_id = None
        volume_name = self.encode_string(volume_name, double=True)

        r_uri = '/api/types/Volume/instances/getByName::' + volume_name

        req, response = self._get(r_uri)
        if req.status_code == 200:
            volume_id = req.json()
        return volume_id


class VolumeLister:
    """A simple class to show mappings of openstack to scaleio volumes"""
    format_string = '%-40s%-30s%-20s%-10s'
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
        parser.add_argument('--os_all_tenants', dest='OS_ALL_TENANTS', action='store_true',
                            default='False', help='Show volumes from all tenants')

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
        """
        converts an openstack volume id to a ScaleIO volume name
        :param id: The OpenStack volume ID
        :return: ScaleIO Volume name
        """

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
        """
        establishes connections to openstack and prepares for communication
        with ScaleIO
        :return: None
        """

        self.openstack = connection.Connection(auth_url=self.args.OS_AUTH_URL,
                                               project_name=self.args.OS_TENANT,
                                               username=self.args.OS_USER,
                                               password=self.args.OS_PASS)

        self.scaleio = SIOWrapper(self.args.SIO_GATEWAY,
                                  self.args.SIO_PORT,
                                  self.args.SIO_USER,
                                  self.args.SIO_PASS)

    def list_volumes(self):
        """
        Process all the OpenStack volumes and determines which have a corresponding
        ScaleIO Volume ID. Prints a list of all volumes that exist in both
        OpenStack and ScaleIO
        :return: None
        """

        print(self.format_string % ("OpenStack Volume", "ScaleIO Name", "ScaleIO ID", "Attached"))
        for os_volume in self.openstack.block_store.volumes(details=True,
                                                            all_tenants=self.args.OS_ALL_TENANTS):
            sio_volume = self._convert_os_to_sio(os_volume.id)
            try:
                vol_id = self.scaleio.get_volumeid(sio_volume)
                if vol_id is not None:
                    attached = 'True'
                    if not os_volume.attachments:
                        attached = 'False'
                    print(self.format_string % (os_volume.id, sio_volume, vol_id, attached))
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
