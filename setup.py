from setuptools import setup

import route53

setup(name = "route53",
      version = route53.__version__,
      description = "Route53 API built on top of boto.",
      long_description = "Route53 API built on top of boto until the Route53 API in boto is improved.",
      author = "Mitchell Hashimoto",
      author_email = "mitchell.hashimoto@gmail.com",
      install_requires = "boto==2.0b3"
      )
