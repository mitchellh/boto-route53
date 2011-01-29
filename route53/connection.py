"""
Represents a connection to the Route53 service.
"""
import uuid
import xml.sax
import boto
from boto import handler
from boto.connection import AWSAuthConnection
from boto.exception import BotoServerError
from boto.resultset import ResultSet

from change_info import ChangeInfo
from hosted_zone import HostedZone
from record import Record

class AWSRestConnection(AWSAuthConnection):
    ResponseError = BotoServerError

    def __init__(self, host, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, path='/', provider='aws'):
        AWSAuthConnection.__init__(self, host, aws_access_key_id, aws_secret_access_key,
                                   is_secure, port, proxy, proxy_port, proxy_user, proxy_pass,
                                   debug, https_connection_factory, path)

    def make_request(self, endpoint, params=None, data='', verb='GET'):
        if isinstance(endpoint, list):
            endpoint = "/".join(endpoint)

        http_request = self.build_base_http_request(verb, endpoint, None, params, data=data)
        http_request = self.fill_in_auth(http_request)
        return self._send_http_request(http_request)

    def get_list(self, endpoint, markers, params=None, data='', verb='GET', expected_status=200):
        response = self.make_request(endpoint, params, data, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == expected_status:
            rs = ResultSet(markers)
            h = handler.XmlHandler(rs, self)
            xml.sax.parseString(body, h)
            return rs
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error(body)
            raise self.ResponseError(response.status, response.reason, body)

    def get_object(self, endpoint, cls, params=None, data='', verb='GET', expected_status=200):
        response = self.make_request(endpoint, params, data, verb)
        body = response.read()
        boto.log.debug(body)
        if response.status == expected_status:
            obj = cls(self)
            h = handler.XmlHandler(obj, self)
            xml.sax.parseString(body, h)
            return obj
        else:
            boto.log.error('%s %s' % (response.status, response.reason))
            boto.log.error(body)
            raise self.ResponseError(response.status, response.reason, body)

class Route53Connection(AWSRestConnection):
    DefaultHost = 'route53.amazonaws.com'
    Version = '2010-10-01'
    XMLNameSpace = 'https://route53.amazonaws.com/doc/2010-10-01/'

    CreateHostedZoneRequestXML = """<?xml version="1.0" encoding="UTF-8"?>
        <CreateHostedZoneRequest xmlns="%(xmlns)s">
            <Name>%(name)s</Name>
            <CallerReference>%(caller_ref)s</CallerReference>
            <HostedZoneConfig>
                <Comment>%(comment)s</Comment>
            </HostedZoneConfig>
        </CreateHostedZoneRequest>"""

    def __init__(self, aws_access_key_id=None, aws_secret_access_key=None,
                 is_secure=True, host=None, port=None, proxy=None, proxy_port=None,
                 proxy_user=None, proxy_pass=None, debug=0,
                 https_connection_factory=None, path='/'):
        AWSRestConnection.__init__(self, self.DefaultHost, aws_access_key_id,
                                   aws_secret_access_key,
                                   is_secure, port, proxy, proxy_port,
                                   proxy_user, proxy_pass, debug,
                                   https_connection_factory, path)

    def _required_auth_capability(self):
        return ['route53']

    # We override make_request to add the version to the endpoint
    def make_request(self, endpoint, params=None, data='', verb='GET'):
        true_endpoint = [self.Version]

        if isinstance(endpoint, list):
            true_endpoint.extend(endpoint)
        else:
            true_endpoint.append(endpoint)

        return super(self.__class__, self).make_request(true_endpoint, params, data, verb)

    def get_all_hosted_zones(self):
        """
        Returns a HostedZone object for each zone defined for this AWS
        account.

        :rtype: list
        :return: A list of :class:`boto.route53.hostedzone.HostedZone`
        """
        return self.get_list('hostedzone', [('HostedZone', HostedZone)])

    def get_hosted_zone(self, hosted_zone_id):
        """
        Get detailed information about a particular Hosted Zone.

        :type hosted_zone_id: str
        :param hosted_zone_id: The unique identifier for the Hosted Zone

        :rtype: :class:`boto.route53.hostedzone.HostedZone`
        :return: The HostedZone object.
        """
        return self.get_object(['hostedzone', hosted_zone_id], HostedZone)

    def create_hosted_zone(self, domain_name, caller_ref=None, comment=''):
        """
        Create a new Hosted Zone. Returns the new zone object created.

        :type domain_name: str
        :param domain_name: The name of the domain. This should be a
                            fully-specified domain, and should end with
                            a final period as the last label indication.
                            If you omit the final period, Amazon Route 53
                            assumes the domain is relative to the root.
                            This is the name you have registered with your
                            DNS registrar. It is also the name you will
                            delegate from your registrar to the Amazon
                            Route 53 delegation servers returned in
                            response to this request.A list of strings
                            with the image IDs wanted

        :type caller_ref: str
        :param caller_ref: A unique string that identifies the request
                           and that allows failed CreateHostedZone requests
                           to be retried without the risk of executing the
                           operation twice.
                           If you don't provide a value for this, boto will
                           generate a Type 4 UUID and use that.

        :type comment: str
        :param comment: Any comments you want to include about the hosted
                        zone.

        :rtype: :class:`boto.route53.hostedzone.HostedZone`
        :returns: The newly created HostedZone.
        """
        if caller_ref is None:
            caller_ref = str(uuid.uuid4())
        params = {'name' : domain_name,
                  'caller_ref' : caller_ref,
                  'comment' : comment,
                  'xmlns' : self.XMLNameSpace
                  }
        xml = self.CreateHostedZoneRequestXML % params

        return self.get_object('hostedzone', HostedZone, data=xml, verb='POST', expected_status=201)

    def delete_hosted_zone(self, hosted_zone_id):
        """
        Delete a hosted zone with the given ID.

        :rtype: :class:`boto.route53.change_info.ChangeInfo`
        :return: The ChangeInfo result of the operation.
        """
        return self.get_object(['hostedzone', hosted_zone_id], ChangeInfo, verb='DELETE')

    def get_all_rrsets(self, hosted_zone_id, type=None,
                       name=None, maxitems=None):
        """
        Retrieve the Resource Record Sets defined for this Hosted Zone.
        Returns an array of Record objects.

        :type hosted_zone_id: str
        :param hosted_zone_id: The unique identifier for the Hosted Zone

        :type type: str
        :param type: The type of resource record set to begin the record
                     listing from.  Valid choices are:

                     * A
                     * AAAA
                     * CNAME
                     * MX
                     * NS
                     * PTR
                     * SOA
                     * SPF
                     * SRV
                     * TXT

        :type name: str
        :param name: The first name in the lexicographic ordering of domain
                     names to be retrieved

        :type maxitems: int
        :param maxitems: The maximum number of records
        """
        params = {'type': type, 'name': name, 'maxitems': maxitems}
        return self.get_list(['hostedzone', hosted_zone_id, 'rrset'],
                             [('ResourceRecordSet', Record)],
                             params)

    def get_change(self, change_id):
        """
        Get information about a proposed set of changes, as submitted
        by the change_rrsets method.

        :type change_id: str
        :param change_id: The unique identifier for the set of changes.
                          This ID is returned in the response to the
                          change_rrsets method.

        :rtype: :class:`boto.route53.change_info.ChangeInfo`
        :return: The ChangeInfo object for the ID requested.
        """
        return self.get_object(['change', change_id], ChangeInfo)
