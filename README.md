# Boto Route53 Library

This is a nicer interface to the Amazon Route 53 service built on
top of boto. Work is underway to merge this work back upstream to
boto, but until then it will live in this separate library.

## Installation

Since my goal is to get this merged back into boto, the only
installation method is from the source itself. Download the source
and do a typical `setup.py` call:

    python setup.py install

## Usage

The usage style very much follows the standards set by boto itself,
so if you've used boto, you should feel right at home. An example
is shown below:

    import time
    from route53.connection import Route53Connection

    # Create a connection (AWS credentials from environmental variables)
    # and list all zones.
    conn = Route53Connection()
    for zone in conn.get_all_hosted_zones():
        print "Zone: %s" % zone.name

    # Create a zone and wait for it to complete
    change = conn.create_hosted_zone("mydomain.com.")
    while change.status == "PENDING":
        time.sleep(2)
        change.update()

    print "New zone created!"

Every module and class is documented so based on the small example
shown above, it should be easy to see how to use the rest of the library.
