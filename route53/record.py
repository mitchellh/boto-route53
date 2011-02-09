"""
Individual record and record sets.
"""

class RecordSet(object):
    ChangeResourceRecordSetsBody = """<?xml version="1.0" encoding="UTF-8"?>
    <ChangeResourceRecordSetsRequest xmlns="https://route53.amazonaws.com/doc/2010-10-01/">
            <ChangeBatch>
                <Comment>%(comment)s</Comment>
                <Changes>%(changes)s</Changes>
            </ChangeBatch>
        </ChangeResourceRecordSetsRequest>"""

    ChangeXML = """<Change>
        <Action>%(action)s</Action>
        %(record)s
    </Change>"""


    def __init__(self, connection=None, hosted_zone_id=None, comment=None):
        self.connection = connection
        self.hosted_zone_id = hosted_zone_id
        self.comment = comment
        self.changes = []

    def __repr__(self):
        return '<ResourceRecordSets: %s>' % self.hosted_zone_id

    def add_change(self, action, name, type, ttl=600):
        """
        Add a change request. If you want to add values to the change
        request, then modify the returned Record.
        """
        change = Record(self.connection, name, type, ttl)
        self.changes.append((action, change))
        return change

    def to_xml(self):
        """Convert this ResourceRecordSet into XML
        to be saved via the ChangeResourceRecordSetsRequest"""
        changesXML = ""
        for change in self.changes:
            changeParams = {"action": change[0], "record": change[1].to_xml()}
            changesXML += self.ChangeXML % changeParams
        params = {"comment": self.comment, "changes": changesXML}
        return self.ChangeResourceRecordSetsBody % params

    def commit(self):
        """Commit this change"""
        if not self.connection:
            from route53.connection import Route53Connection
            self.connection = Route53Connection()
        return self.connection.change_rrsets(self.hosted_zone_id, self.to_xml())

class Record(object):
    XMLBody = """<ResourceRecordSet>
        <Name>%(name)s</Name>
        <Type>%(type)s</Type>
        <TTL>%(ttl)s</TTL>
        <ResourceRecords>
            %(records)s
        </ResourceRecords>
    </ResourceRecordSet>"""

    ResourceRecordBody = "<ResourceRecord><Value>%s</Value></ResourceRecord>"

    def __init__(self, connection=None, name=None, type=None, ttl=600):
        """
        Init method to create a new Record for Route 53.

        :type connection: :class:`boto.route53.Route53Connection`
        :param connection: Optional connection object. If this isn't given and
                           you attempt to delete or modify the record, then
                           a connection will attempt to be obtained.

        :type name: string
        :param name: The name you wish to perform the action on.

        :type type: string
        :param type: The type of record.

        :type ttl: int
        :param ttl: Optional TTL for the record.
        """
        self.connection = connection
        self.name = name
        self.type = type
        self.ttl = ttl
        self.values = []

    def __repr__(self):
        return "%s %s %s" % (self.name, self.type, self.values)

    def startElement(self, name, attrs, connection):
        if name == 'ResourceRecords':
            self.values = []

        return None

    def endElement(self, name, value, connection):
        if name == 'Name':
            self.name = value
        elif name == 'Type':
            self.type = value
        elif name == 'TTL':
            self.ttl = value
        elif name == 'Value':
            self.values.append(value)
        else:
            setattr(self, name, value)

    def to_xml(self):
        """
        Returns the XML representation for this record.

        :rtype: string
        :returns: The XML representation for this record.
        """
        records_xml = ""
        for value in self.values:
            records_xml += self.ResourceRecordBody % value
        params = {
            "name": self.name,
            "type": self.type,
            "ttl": self.ttl,
            "records": records_xml
        }
        return self.XMLBody % params
