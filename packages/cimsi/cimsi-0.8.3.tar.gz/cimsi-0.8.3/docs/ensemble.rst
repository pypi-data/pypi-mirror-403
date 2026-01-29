=============
Ensemble Tool
=============

.. contents:: Table of Contents
  :depth: 2
  :local:

Overview
------------

The ensemble tool enables the extension of IMSI to many runs. 
It implements IMSI commands as subcommands of the ensemble tool, so 
existing commands are replicated in the tool but are applied across 
multiple ensemble members. Users can refer to the main implementation details of the available commands to view behaviour. 

See ``imsi ensemble --help`` for a list of available commands.

.. program-output:: imsi ensemble -h


Configuration Files
----------------------------------------------
The ensemble tool can be used in several ways, including from a single high-level config, 
to external tables defining ensemble members as ``.yaml`` or ``.csv`` files,
or combinations of both tables and the high-level config. However, regardless of how a user decides to use the ensamble tool,
its critical to understand what the underlying tool is doing:

   1. The ensemble tool composes a set of changes for each ensemble member.
   2. These changes are mapped directly onto the Resolved Configuration with the defined hierarchy for each ensemble member (users are responsible for setting the hierarchy correctly!)
   3. The ensemble tool then loops through the ``imsi (ensemble) <command>`` **for each ensemble member** with the modified Resolved Configuration 

After setting up their first ensemble, users are encouraged to look at the Resolved Configuration files for each ensemble member, 
which are stored in each ensemble member's setup directory as ``imsi_configuration_{runid}.yaml``, and verify that their modifications
have been correctly applied at the correct hierarchical levels.


The entry config (required)
------------------------------------

Defining the entry configuration file
+++++++++++++++++++++++++++++++++++++++++++++++
The entry config is a ``.yaml`` file that must be defined at every invocation of the ensemble tool defined with ``--config-path ...``. 
For convenience, the default file is ``$(pwd)/config.yaml``, but ``--config-path`` can point to any valid ``.yaml`` file on disk.

The ensemble tool reads the high-level config and sets up the ensemble members accordingly, e.g.:

.. code-block:: bash

   imsi ensemble --config-path=config.yaml <command>


Contents of the entry config file
+++++++++++++++++++++++++++++++++++++++++
Inside of the entry config are sets of required parameters: the ``ensemble-level`` and ``member-level`` parameters.

``ensemble_level`` parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These are global parameters for ensemble runs that are logically defined **once per ensemble run**. They do not specify **any information about individual members**.

.. list-table:: ``ensemble_level`` parameters
   :widths: 20 80
   :header-rows: 1

   * - Required Parameters
     - Description
   * - ``user``
     - Defaults to ``$USER``. The user running the ensemble.
   * - ``run_directory``
     - Defaults to ``$pwd``. Directory where ensemble setup/run directories are created.
   * - ``share_repo``
     - Defaults to ``False``. If True, the first ensemble member's setup ``src`` repository is symlinked to subsequent setup directories.
   * - **Optional Parameters**
     - **Description**  
   * - ``config_table``
     - Path to the configuration table. See details on configuration tables below.
   * - ``aliases``
     - ``alias: parameter`` pairs to help keep table headers short.

An example ``ensemble_level`` configuration could look like the following:

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}  # required, recommended example automatically sets omegaconf interpolation to $USER
     run_directory: /output/path/to/ensemble/setup_dirs/  # optional, defaults to pwd
     config_table: table.csv  # optional table, see details below
     share_repo: true  # optional, defaults to false
.. warning::
  The ensemble tool is configured to overwrite any existing setup directories defined under ``run_directory``.
  Where the main IMSI tools may prompt users for confirmation before taking action, the ensemble tool does not. 
  Users should take caution of the location of their working directories and be aware of the 
  underlying action the ensemble tool is taking.

``member_level`` parameters
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^


These parameters are defined **once per ensemble member** and represent **any** parameter from
the Resolved Configuration File including the full hierarchy in the cast of nested parameters.


.. tip::

  In a configuration file, the full hierarchy to a parameter is referred to as its **key-path**. For example, the hierarchical configuration

  .. code-block:: yaml

    components:
      CanAM:
        namelists:
          canam_settings:
            phys_parm:
              pp_rdm_num_pert: <value>

  has the key-path ``components -> CanAM -> namelists -> canam_settings -> phys_parm -> pp_rdm_num_pert``. This concept can be used to construct aliases for long key-paths.

Creating ensembles via the entry config
+++++++++++++++++++++++++++++++++++++++++++++++

**Any** ``member_level`` variable may be defined as either a single value or a list of values.
If a list is provided, the ensemble tool will generate a separate run for each value in that list.
When multiple ``member_level`` variables are defined as lists, their list indices are aligned: values with the same index across different variables correspond to the same ensemble member.

For example, the following ``member_level`` configuration

.. code-block:: yaml

  member_level:
    this:
      is:
        a:
          parameter: [value-a, value-b]
    another:
      parameter: [value-01, value-02]


constructs two ensemble members with the following key-paths defined:

  - Ensemble Member 1:
  - ``this -> is -> a -> parameter``: ``value-a``
  - ``another -> parameter``: ``value-01``
  - Ensemble Member 2:
  - ``this -> is -> a -> parameter``: ``value-b``
  - ``another -> parameter``: ``value-02``

.. tip::
  In order to determine the correct key path or hierarchy for member level parameters, 
  users should refer to a reference Resolved Configuration File on disk 
  (i.e. ``imsi_configuration_{runid}.yaml``). Running ``imsi setup ...`` 
  might be necessary to generate this file for reference.


Aliases
------------------------

.. tip:: 
  Key paths can quickly become long and ugly. To help shorten this and make tables more readable,
  you can specify an alias for long key-paths in the ``ensemble_level: aliases`` section. This alias then becomes
  global and can be used in configuration tables (see below) or in the ``member_level`` section of the entry config file.

  .. code-block:: yaml
      
    ensemble_level:
      user: ${oc.env:USER}
      ...
      aliases:
        # the alias key can be any dictionary compatible string
        pp_rdm_num_pert: components:CanAM:namelists:canam_settings:phys_parm:pp_rdm_num_pert

  ``pp_rdm_num_pert`` can then be used in place of the full key-path in configuration tables or the ``member_level`` section.

Setup parameters
-----------------------------
Setup parameters include any argument that could be provided to ``imsi setup``. All setup parameters must be defined under the subkey ``setup`` to be
correctly recognized and used by imsi. For example:

.. code-block:: yaml

  member_level:
    setup:
      runid: [run-01, run-02]
      model: [canesm51_p1, canam51_p1]
      exp: [cmip6-piControl, cmip6-amip]

.. warning:: 
  Failure to place setup keys under ``setup`` will prevent imsi from
  recognizing setup parameters and will either fail or resort to defaults leading to unexpected behaviour.


Configuration tables via the ``config_table`` parameter (optional)
---------------------------------------------------------------------
While the entry config file is required for all ensembles, IMSI's ensemble tool also supports the definition of **external** 
configuration tables at the ``ensemble_level`` to define ensemble members in a bulk format. 
Configuration tables allow for easier (and sometimes more flexible and explicit) modification of ensemble member parameters, especially for large ensembles. 
Configuration tables store discrete ensemble member runs and their associated parameter modifications. 
IMSI's ensemble tool supports ``.yaml`` and ``.csv`` formats. Legacy ``.txt`` support is still available but deprecated, with a ``DeprecationWarning`` 
issued when used.

.. note:: We recommend that users use the ``.yaml`` format for external tables due to its explicit representation of key hierarchies

When using external configuration tables, users have the option of defining **all** ensemble member parameters in the table itself,
or defining a subset of parameters in the table and using the entry config to define common parameters. When defining all parameters in the table,
the entry config's ``member_level`` section can be left empty (i.e. ``member_level: {}``).


Supported Configuration Formats for ``ensemble_level: config_table``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To illustrate the use of configuration tables, consider the following entry config file:

.. code-block:: yaml

   # entry config file
   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     config_table: config/example.(yaml|csv)  # path to config table
     share_repo: true

   member_level: {}

``.yaml`` table format
^^^^^^^^^^^^^^^^^^^^^^^^^^
To have an equivalent ensemble to previous examples, the ``config/example.yaml`` would then contain:

.. code-block:: yaml

  # example.yaml
   - setup:
       runid: run-01
       model: canesm51_p1
       exp: cmip6-piControl

   - setup:
       runid: run-02
       model: canam51_p1
       exp: cmip6-amip

.. note:: The external ``.yaml`` config table is a list where each hyphen ``-`` denotes a new list item, with each item in the list representing an ensemble member.

CSV table format
^^^^^^^^^^^^^^^^^^^

For a ``.csv`` config table, the same content ``config_table: config/example.csv`` would look like:

.. code-block:: text

   # example.csv
   setup:runid,  setup:model, setup:exp
   run-01,       canesm51_p1, cmip6-piControl
   run-02,       canam51_p1,  cmip6-amip

.. note:: 
  In ``.csv`` config tables, the header row must contain the full key-paths for each parameter, 
  with nested keys separated by colons ``:``. Each subsequent row represents an ensemble member.


Advanced Configuration Techniques
----------------------------------------------
.. tip:: 
  Users can always refer to the Resolved Configuration File for each ensemble member to understand how
  their configurations are being applied and to verify settings are being applied as expected.

Mixing `member_level` parameters and tables via broadcasting
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The ensemble tool resolves configurations from multiple sources as follows:

1. If a key exists in both ``member_level`` and a ``config_table.(yaml|csv)``, the table value overrides and issues a warning.
2. If a key exists only in ``member_level``:

  - Single values are **broadcasted** to all ensemble members.
  - Lists must match the number of ensemble members defined in the table.
  - Any overlapping keys (even lists) are overridden by the ``config_table`` values. If they don't exist in the ``config_table``, they are broadcasted to all ensemble members.


.. note:: Broadcasting in this context means that singular values are copied and applied to each ensemble member. Lists are broadcasted to each ensemble member in the order they are defined.

Omitting parameters in configuration tables
++++++++++++++++++++++++++++++++++++++++++++++

For tables, the ensemble tool supports configurations where users can omit parameters from ensemble runs that are present 
in other members. This makes the tool flexible to arbitrary configuration structures, and allows the ability to create diverse ensembles.

For example, the following config tables are valid:

**CSV**:

.. code-block:: text

   setup:runid, setup:model, some:imsi:parameter
   run-01-csv,  canesm51_p1,
   run-02-csv,  canam51_p1,  123

**YAML**:

.. code-block:: yaml

   - setup:
       runid: run-01-yaml-table
       model: canesm51_p1

   - setup:
       runid: run-02-yaml-table
       model: canam51_p1
       some: # note how this level is only defined for this member
         imsi:
           parameter: 123

.. warning::
  This technique only available for table configurations due to the structure of ensemble 
  member definitions in a ``member_level`` section.


Modifying lower level configuration parameters
----------------------------------------------
The ensemble tool allows for the modification of any non-setup parameter in the resolved ``yaml`` file (i.e. ``imsi_configuration_{runid}.yaml``). 
Below are some examples for how to modify the parameter ``pp_rdm_num_pert``.

.. important:: 
  As mentioned many times now, the parameter that is being modified must contain the entire 
  heriarchy of the Resolved Configuration file (i.e. ``imsi_configuration_{runid}.yaml``). The ensemble tool 
  modifies the resolved ``.yaml`` file in place and runs ``imsi config`` on the modified file. 
  If a new key is added to the resolved``.yaml`` by the ensemble tool, it will warn users.

Low level parameter modification in a ``.yaml`` table (recommended method):
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: yaml
    
    - setup:
        runid: run-01
        model: canesm51_p1
        exp: cmip6-piControl
      components:
        CanAM:
          namelists:
            canam_settings: 
              phys_parm:
                pp_rdm_num_pert: 0

    - setup:
        runid: run-02
        model: canam51_p1
        exp: cmip6-amip
      components:
        CanAM:
          namelists:
            canam_settings: 
              phys_parm:
                pp_rdm_num_pert: 2



Low level parameter modification in the entry config file
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     ...
   member_level:
    setup:
      runid: [run-01, run-02]
    components:
      CanAM:
        namelists:
          canam_settings: 
            phys_parm:
              pp_rdm_num_pert: [0, 2]


Low level parameter modification in a ``.csv`` config table
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: text
    
   runid,  model,       exp,             components:CanAM:namelists:canam_settings:phys_parm:pp_rdm_num_pert
   run-01, canesm51_p1, cmip6-piControl, 0
   run-02, canam51_p1,  cmip6-amip,      2

As mentioned above, you can specify an **alias** for that very long key-path in your entry config:

.. code-block:: yaml
    
   ensemble_level:
     user: ${oc.env:USER}
     ...
     aliases:
       # the alias key can be any dictionary compatible string
       pp_rdm_num_pert: components:CanAM:namelists:canam_settings:phys_parm:pp_rdm_num_pert
   member_level: {}


And then in your ``.csv`` config table:

.. code-block:: text

   setup:runid,  setup:model, setup:exp,       pp_rdm_num_pert
   run-01,       canesm51_p1, cmip6-piControl, 0
   run-02,       canam51_p1,  cmip6-amip,      2


Simple examples from CanESM
------------------------------------

To help get users started in the ``canesm`` world, we provide some simple ensemble config files here.

Simple ensemble with varying adjustable params:
++++++++++++++++++++++++++++++++++++++++++++++++++

A very common use case of an ensemble is to use it to assess the affects of adjusting parameters. Say we
are working with ``CanESM6`` and want to assess affect of varying ``ap_uicefac`` and ``ap_facacc``, where we
we `also` want:

* to share the source repo and executables
* make the simulations go until year ``3000``


Example 1: the entry config
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For simple experiments is possible to set all the configuration in a single file. For example, we
can create a single ``config.yaml`` with:

.. code-block:: yaml

    # config.yaml
    ensemble_level:
        user: ${oc.env:USER}
        share_repo: true
        aliases:
            uicefac: components:CanAM:namelists:model_settings.nml:adjustable_parm:ap_uicefac
            facacc: components:CanAM:namelists:model_settings.nml:adjustable_parm:ap_facacc

    member_level:
        setup:
            model: canesm6_p1
            exp: dev-repeated-cycle-phy53
            ver: v6.0-imsi-integration
            runid: [myrun01, myrun02, myrun03]
        uicefac: [ 4078.0351998582, 4084.30063527445, 3935.17992548678 ]
        facacc: [ 9.15046755786538, 14.0613122621687, 11.5656114129704 ]
        sequencing:
            run_dates:
                run_segment_stop_time: 3000



Example 2: ``.yaml`` format config table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``.yaml`` format lets you organize your run information explicitly and cleanly, and also makes it `easier` to
only define the modifications you want applied to that single run - i.e. say you only want to modify
the default value for one run.

.. code-block:: yaml

    # config.yaml
    ensemble_level:
        user: ${oc.env:USER}
        config_table: table.yaml
        share_repo: true
        aliases:
            uicefac: components:CanAM:namelists:model_settings.nml:adjustable_parm:ap_uicefac
            facacc: components:CanAM:namelists:model_settings.nml:adjustable_parm:ap_facacc

    member_level:
        setup:
            model: canesm6_p1
            exp: dev-repeated-cycle-phy53
            ver: v6.0-imsi-integration
        sequencing:
            run_dates:
                run_segment_stop_time: 3000

.. code-block:: yaml

    # table.yaml
    - setup:
        runid: myrun07
      uicefac: 4078.0351998582
      facacc: 9.15046755786538

    - setup:
        runid: myrun08
      uicefac: 4084.30063527445
      facacc: 14.0613122621687

    - setup:
        runid: myrun09
      uicefac: 3935.17992548678
      facacc: 11.5656114129704


Example 3: ``.csv`` format config table
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The ``.csv`` format offers a tabular format that uses explicit delimiters
and is able to leverage aliases to limit the column length of the tables.

.. code-block:: yaml

    # config.yaml
    ensemble_level:
        user: ${oc.env:USER}
        config_table: table.csv
        share_repo: true
        aliases:
            uicefac: components:CanAM:namelists:model_settings.nml:adjustable_parm:ap_uicefac
            facacc: components:CanAM:namelists:model_settings.nml:adjustable_parm:ap_facacc

    member_level:
        setup:
            model: canesm6_p1
            exp: dev-repeated-cycle-phy53
            ver: v6.0-imsi-integration
        sequencing:
            run_dates:
                run_segment_stop_time: 3000

.. code-block:: text

    # table.csv
    setup:runid, uicefac, facacc
    myrun01, 4078.0351998582, 9.15046755786538
    myrun02, 4084.30063527445, 14.0613122621687
    myrun03, 3935.17992548678, 11.5656114129704


Simple ensemble for testing experiments:
++++++++++++++++++++++++++++++++++++++++++

To help launch production/test ensembles, users may wish to launch an ensemble of multiple canned experiments. For example,
for ``CanESM6``, we might want to test 2 years of the AMIP, ESM, and OMIP models in the same ensemble. This can easily be done with
the following config file

.. code-block:: yaml

    # define a runid prefix to refer to runs in the ensemble
    prefix: v6-sys

    ensemble_level:
        user: ${oc.env:USER} # pick up the user from the account running `imsi ensemble ...`
        share_repo: true     # share execs and repo

    member_level:
        setup:
            repo: git@gitlab.science.gc.ca:CanESM/CanESM5.git
            ver: v6.0-imsi-integration
            runid: [
                "${oc.select:prefix}-amip53",
                "${oc.select:prefix}-omip",
                "${oc.select:prefix}-esm53"
            ]
            exp: [
                "dev-amip-v6-phy53",
                "dev-omip1-v6",
                "dev-repeated-cycle-phy53"
            ]
            model: [
                "canam6_p1",
                "cannemo6_p1",
                "canesm6_p1"
            ]
        sequencing:
            run_dates:
                run_segment_start_time: [
                    "2003",
                    "0001",
                    "1001"
                ]
                run_segment_stop_time: [
                    "2004",
                    "0002",
                    "1002"
                ]


Conceptual examples of broadcasting
-------------------------------------

Broadcasting techniques in the entry config file.
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
  - Running an ensemble with a single model and multiple experiments.
  - Running an ensemble with multiple models and a single experiment.
  - Running an ensemble with multiple models and multiple experiments.

Example 1: Single model, multiple experiments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true

   member_level:
     setup: 
       runid: [run-01, run-02]
       model: canesm51_p1 # this is broadcasted to all ensemble members and is equivalent to [canesm51_p1, canesm51_p1]
       exp: [cmip6-piControl, cmip6-amip]

Example 2: Multiple models, single experiment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true

   member_level:
     setup:
       runid: [run-01, run-02]
       model: [canesm51_p1, canam51_p1]
       exp: cmip6-piControl # this is broadcasted to all ensemble members and is equivalent to [cmip6-piControl, cmip6-piControl]

Example 3: Multiple models, multiple experiments (no broadcasting)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true

   member_level:
     setup:
       runid: [run-01, run-02, run-03, run-04]
       model: [canesm51_p1, canam51_p1, canesm51_p2, canam51_p2]
       exp: [cmip6-piControl, cmip6-amip, cmip6-historical, cmip6-ssp585]



Examples mixing the entry config with config tables:
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Example 1: Single model and version; multiple experiments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following entry config:

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true
     config_table: config/example.yaml

   member_level:
     setup:
       ver: imsi-integration
       model: canesm51_p1


In ``config/config.yaml``, the commented keys show the equivalent structure in a table

.. code-block:: yaml

   - setup:
       runid: run-01
     # model: canesm51_p1
       exp: cmip6-piControl
     # ver: imsi-integration
   - setup:
        runid: run-02
      # model: canesm51_p1
        exp: cmip6-historical
      # ver: imsi-integration

Example 2: Multiple models; single experiment and version
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following entry config:

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true
     config_table: config/example.yaml

   member_level:
     setup:
       ver: imsi-integration
       exp: cmip6-piControl


In ``config/config.yaml``, the commented keys show the equivalent structure in a table

.. code-block:: yaml

   - setup:
       runid: run-01
       model: canesm51_p1
       # ver: imsi-integration
       # exp: cmip6-piControl
   - setup:
        runid: run-02
        model: canam51_p1
      # ver: imsi-integration
      # exp: cmip6-piControl



Example 3: Multiple models, multiple experiments
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Consider the following entry config:

.. code-block:: yaml

   ensemble_level:
     user: ${oc.env:USER}
     run_directory: /output/path/to/ensemble/setup_dirs/
     share_repo: true
     config_table: config/example.yaml

   member_level:
     setup:
       model: [model_A, model_B]
       ver: imsi-integration

In ``config/config.yaml``, the commented keys show the equivalent structure in a table

.. code-block:: yaml

   - setup:
       runid: run-01
       # model: model_A
       exp: cmip6-piControl
      # ver: imsi-integration
   - setup:
        runid: run-02
        # model: model_B
        exp: cmip6-amip
      # ver: imsi-integration

