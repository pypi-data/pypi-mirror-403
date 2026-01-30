============================
Tencent Cloud DLC Connector
============================

Tencent Cloud DLC Connector is a python SDK connecting to DLC elastic engines, compatible with DPAPI2.0

The SDK works on Python versions:

   * 3.9

Quick Start
-----------
First, install the library:

.. code-block:: sh

    $ pip install tencentcloud-dlc-connector

or download source code from github and install:

.. code-block:: python

    import tdlc_connector
    import datatime
    from tdlc_connector import constants
 
    conn = tdlc_connector.connect(region="<REGION>",
        secret_id="<SECRET_ID>",
        secret_key="<SECRET_KEY>",
        engine="<ENGINE>",
        engine_type=constants.EngineType.SPARK,
        result_style=constants.ResultStyles.LIST,
        download=False,
        mode=constants.Mode.LASY)
    
    cursor = conn.cursor()
    count = cursor.execute("SELECT 1")
    cursor.fetchone()
