from distutils.core import setup


setup(name="ceilometer-horizon",
      version="0.1",
      description="A ceilometer module that can be plugged into horizon.",
      author="Brooklyn Chen",
      author_email="brooklyn.chen@canonical.com",
      packages=["ceilometer-horizon"],
      package_data={"ceilometer-horizon": []},
      )

