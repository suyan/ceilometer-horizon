Ceilometer plugin for Horizon
==================

This is a ceilometer plugin that enables ceilometer in Horizon.

Installation
------------
Just type in the directory:

    python setup.py install


Setup the Horizon dashboard
-------------------

Modify the `local_settings.py` file in Horizon to add the following lines:

    import sys
        admin_dashboard = sys.modules['openstack-dashboard.admin']
        admin_dashboard.INSTALLED_APPS += ('ceilometer-horizon.admin_panel',)

        project_dashboard = sys.modules['openstack-dashboard.project']
        project_dashboard.INSTALLED_APPS += ('ceilometer-horizon.project_panel',)


You may need to restart the apache server to enable the plugin:
    
    `service apache2 restart`
