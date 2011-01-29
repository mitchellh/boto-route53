"""
Represents Route 53 change status for an operation.
"""

class ChangeInfo(object):
    def __init__(self, connection=None):
        self.connection = connection

    def __repr__(self):
        return 'ChangeInfo:%s' % self.id

    def startElement(self, name, attrs, connection):
        pass

    def endElement(self, name, value, connection):
        if name == 'Id':
            self.id = value.replace("/change/", "")
        elif name == 'Status':
            self.status = value
        elif name == 'SubmittedAt':
            self.submitted_at = value

    def update(self):
        """
        Update the change info's state information by making a call
        to fetch the current attributes from the service.

        :rtype: string
        :returns: The current status of the change.
        """
        self.__dict__.update(self.connection.get_change(self.id).__dict__)
        return self.status
