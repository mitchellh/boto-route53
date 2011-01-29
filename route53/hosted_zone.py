"""
Represents a single hosted zone.
"""
from change_info import ChangeInfo

class HostedZone(object):
    def __init__(self, connection=None, id=None, name=None, owner=None,
                 version=None, caller_reference=None, comment=None):
        self.connection = connection
        self.id = id
        self.name = name
        self.owner = owner
        self.version = version
        self.caller_reference = caller_reference
        self.comment = comment
        self.name_servers = []

    def __repr__(self):
        return 'HostedZone:%s' % self.id

    def startElement(self, name, attrs, connection):
        if name == 'ChangeInfo':
            self.change_info = ChangeInfo(self.connection)
            return self.change_info
        elif name == 'NameServers':
            self.name_servers = []
            return None
        else:
            return None

    def endElement(self, name, value, connection):
        if name == 'Id':
            self.id = value.replace("/hostedzone/", "")
        elif name == 'Name':
            self.name = value
        elif name == 'Owner':
            self.owner = value
        elif name == 'Version':
            self.version = value
        elif name == 'CallerReference':
            self.caller_reference = value
        elif name == 'Comment':
            self.comment = value
        elif name == 'NameServer':
            self.name_servers.append(value)
        else:
            setattr(self, name, value)

    def records(self, type=None, name=None, maxitems=None):
        """
        Retrieve the resource record sets defined for this hosted
        zone.

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
        return self.connection.get_all_rrsets(self.id, type, name, maxitems)

    def delete(self):
        """
        Delete the hosted zone.

        :rtype: :class:`boto.route53.change_info.ChangeInfo`
        :return: The ChangeInfo result of the operation
        """
        return self.connection.delete_hosted_zone(self.id)

