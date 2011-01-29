"""
Represents a connection to the Route53 service.
"""
import xml.sax
import boto
from boto import handler
from boto.connection import AWSAuthConnection
from boto.exception import BotoServerError
from boto.resultset import ResultSet

from hosted_zone import HostedZone

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
