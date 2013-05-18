Ceilometer plugin for Horizon
==================

This is a ceilometer plugin that enables ceilometer in Horizon.

Installation
------------
Must have install these packages

    python-ceilometerclient
    svglib
    reportlab
    keystone

Just type in the directory:

    python setup.py install


Add Ceilometer panel to the Horizon dashboard
-------------------

Add following lines to the `local_settings.py` file in Horizon:

    import sys
    settings = sys.modules['openstack_dashboard.settings']
    settings.INSTALLED_APPS += ('ceilometer_horizon.admin',)
    from openstack_dashboard.dashboards.admin import dashboard
    dashboard.SystemPanels.panels += ('ceilometer',)


You may need to restart the apache server to enable the plugin:
    
    `service apache2 restart`
