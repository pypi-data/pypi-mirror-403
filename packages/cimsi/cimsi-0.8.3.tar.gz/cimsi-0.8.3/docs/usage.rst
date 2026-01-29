=====
Usage
=====

Setting up a run
--------------------------------------

With ``imsi setup``
++++++++++++++++++++

Use ``imsi setup`` to create a run directory, obtain the model source code,
and extract all required model configuration files. The setup will result
in an imsi configured directory, from which futher interaction with the run
is conducted.

The output of ``imsi setup -h``:

.. program-output:: imsi setup -h

``imsi setup`` creates some subdirectories for the run, including ``bin`` (for executables),
and ``config``. The ``config`` directory contains various run configuration files, including
cpp directives and namelists, that have been extracted and modified according to the choice
of model and experiment.

Example

.. code-block:: bash

    >> imsi setup --repo=https://gitlab.science.gc.ca:CanESM/CanESM5 --ver=develop_canesm --exp=cmip6-piControl --model=canesm51_p1 --runid=<unique-runid>

The setup also creates a log file in the run directory (``.imsi-setup.log``), and a readable/writable **resolved** ``yaml`` state file containing the
full details of the configuration options (``imsi_configuration_<runid>.yaml``). Additionally, it will extract
the ``save_restart_files.sh``, ``imsi-tmp-compile.sh``, and ``tapeload_rs.sh`` scripts from the ``imsi-config`` directory within the
housing model repo.

.. warning::

   Changes to the above ``imsi_configuration_<runid>.yaml`` file are
   **not automatically applied to your run**. If you want changes to take affect,
   you need to run ``imsi config`` after making updates to this local ``yaml``
   file.

Once you make the desired changes, if any (see :ref:`here <Modifying basic run parameters>` for details
on making simple changes to a configuration), you then
need to step through the following steps:

.. code-block:: bash

    >> imsi build         # run the compilation tool to build your model's execs
    >> imsi save-restarts # save your model's restarts
    >> imsi submit        # submit your jobs!

to launch your experiment!

Interactively with ``imsi setup-menu``
++++++++++++++++++++++++++++++++++++++++++++

``imsi setup-menu`` provides an interactive menu-driven interface that assembles a complete ``imsi setup`` command.
Repos that appear in the ``setup-menu`` are listed based on `.rc` files. You can read more about these files under ``imsi list``.

.. image:: _static/setup-menu.gif
   :alt: imsi setup-menu interactive demo
   :align: center
   :width: 700px
   :target: _static/setup-menu.gif



Querying available configurations
----------------------------------

The output of imsi list -h:

.. program-output:: imsi list -h


With ``imsi list``
+++++++++++++++++++++++

Use imsi list to query the supported models, and experiments known to IMSI.

If you are already in an imsi-configured repository, the results will be based on that repository's ``imsi-config`` directory. If you are not in an imsi-configured repository, you can:
1. Point directly to a single repository using ``--repo-path <path>``

2. Point to a directory containing multiple repositories (each with an imsi-config) using ``--repo-path <directory>``

3. Using ``IMSI_DEFAULT_CONFIG_REPOS``. Users can set this value in two ways (each definition is treated additively):

    i. In ``$HOME/imsi.user.rc``

    ii. In a bash session as an environment variable, under ``imsi.user.rc``.

Default fall-back values are packaged with imsi under the ``imsi/imsi.site.rc`` file and are site-specific.

You can further narrow the results with:

``--filter-model <name>`` -- show only configurations for a given model name

``--filter-experiment <name>`` -- show only configurations for a given experiment name

Example commands:

.. code-block:: bash

    # List configurations from the current repository
    imsi list

    # List configurations from a specific repo path
    imsi list --repo-path /path/to/model-repo

    # List configurations from multiple repos in a directory
    imsi list --repo-path /path/to/repos-dir

    # Filter by model and experiment
    imsi list --filter-model canesm53_b1_p1 --filter-experiment cmip6-historical


Modifying basic run parameters
------------------------------

There are three general methods in imsi that can be used to modify run parameters,
based on the three commands: ``imsi config``, ``imsi reload``, and ``imsi set``.
These commands can be used in conjunction with each other and invoked repeatedly
in a single run directory. Choosing which command to use the command depends
on the workflow.


1\. Modify the Resolved Configuration File and run ``imsi config``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

  +------------------+------------------------------------------------------------------+
  | **Command**      | .. code-block:: bash                                             |
  |                  |                                                                  |
  |                  |     >> imsi config                                               |
  |                  |                                                                  |
  +------------------+------------------------------------------------------------------+
  | **Steps**        | 1. modify the contents of ``imsi_configuration_<runid>.yaml``    |
  |                  | 2. run ``imsi config``                                           |
  +------------------+------------------------------------------------------------------+
  | **Purpose**      | Apply simple one-off changes to a run. This can be useful for    |
  |                  | development and testing purposes, such as testing the effects    |
  |                  | of simple parameter switches and running shorter simulations by  |
  |                  | changing the date settings.                                      |
  +------------------+------------------------------------------------------------------+
  | **Caveats**      | \- Modifications apply to (downstream) contents, not (upstream)  |
  |                  | imsi Configuration Files.                                        |
  |                  | Modifications to imsi configuration ``yaml`` files are not       |
  |                  | version controlled in this workflow.                             |
  |                  |                                                                  |
  |                  | \- Running ``imsi config`` will modify (overwrite) contents under|
  |                  | the ``/config`` and ``/sequencer`` folder. For some sequencers,  |
  |                  | the contents related to a run-in-progress will be preserved      |
  |                  | unless ``-f`` is used.                                           |
  +------------------+------------------------------------------------------------------+

  **What does** ``imsi config`` **do?**

  ``imsi config`` propagates the current (saved) contents of the Resolved
  Configuration File to the run's downstream directories, ``/config`` and
  ``/sequencer``.

  In other words, if you modify the contents of the Resolved Configuration File,
  you must then invoke ``imsi config`` to apply the changes to the run.

2\. Modify the upstream imsi Configuration Files and run ``imsi reload``
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   +------------------+------------------------------------------------------------------+
   | **Command**      | .. code-block:: bash                                             |
   |                  |                                                                  |
   |                  |     >> imsi reload                                               |
   |                  |                                                                  |
   +------------------+------------------------------------------------------------------+
   | **Steps**        | 1. modify the contents of ``/src/imsi-config``                   |
   |                  | 2. run ``imsi reload``                                           |
   +------------------+------------------------------------------------------------------+
   | **Purpose**      | This is the best way to create reproducible and sharable         |
   |                  | modifications to specific configurations. This is the best       |
   |                  | method for developing official modifications to models/          |
   |                  | experiments (or other configuration), or for developers who      |
   |                  | are adding new models/experiments under the current source       |
   |                  | repository (to be used in conjunction with ``imsi set -s``).     |
   +------------------+------------------------------------------------------------------+
   | **Caveats**      | \- In most cases, users should set up runs with                  |
   |                  | ``--fetch_method`` as ``clone*|copy``, as a linked source may be |
   |                  | write-restricted or unintentionally modify other linked runs.    |
   |                  |                                                                  |
   |                  | \- Calling ``imsi reload`` will overwrite (manual) modifications |
   |                  | to the Resolved Configuration File and downstream configuration  |
   |                  | folders.                                                         |
   +------------------+------------------------------------------------------------------+

   **What does** ``imsi reload`` **do?**

   ``imsi reload`` literally re-resolves and re-extracts the upstream imsi
   Configuration Files from ``/src/imsi-config`` and updates (overwrites) the
   Resolved Configuration File and contents in the downstream configuration
   folders (``/config`` and ``/sequencer``).

   Changes applied to the run folder before invoking ``imsi reload`` will be
   overwritten. If changes are not made to the imsi Configuration Files,
   ``imsi reload`` can be used to "reset" the run folder to the configuration
   state resolved by the initial setup command.

.. tip::

   When developing new configuration components under the imsi Configuration Files
   directory, use ``imsi validate`` before ``imsi reload`` to apply validation.


3\. Swap setup parameters using ``imsi set --selections``
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
   +------------------+------------------------------------------------------------------+
   | **Command**      | .. code-block:: bash                                             |
   |                  |                                                                  |
   |                  |     >> imsi set --selections <setup_param>=<value>               |
   |                  |                                                                  |
   +------------------+------------------------------------------------------------------+
   | **Steps**        | Run the command above. ``setup_param`` is any of the parameters  |
   |                  | in ``imsi setup`` that affect the configuration itself, and      |
   |                  | ``value`` is any corresponding key of the configuration in the   |
   |                  | imsi Configuration Files.                                        |
   +------------------+------------------------------------------------------------------+
   | **Purpose**      | Swap or "reload" parts of resolved configuration. Setting a new  |
   |                  | value to one part of configuration may also cause a re-resolving |
   |                  | to other parts (e.g., setting to a different ``machine`` could   |
   |                  | also change the compiler configuration). This is most useful for |
   |                  | developing new configurations under the imsi Configuration Files.|
   |                  | See conceptual example below.                                    |
   +------------------+------------------------------------------------------------------+
   | **Caveats**      | \- Similar to ``imsi reload``, invoking this command will        |
   |                  | overwrite modifications to the Resolved Configuration File and   |
   |                  | downstream configuration folders.                                |
   |                  |                                                                  |
   |                  | \- If a user entered an undesired parameter upon initial setup   |
   |                  | of a run folder, this command does work to "switch" the          |
   |                  | configuration for that parameter. However, it is advisable that  |
   |                  | a new setup is run instead, to keep the development steps        |
   |                  | traceable and easily repeatable.                                 |
   +------------------+------------------------------------------------------------------+

   **What does** ``imsi set -s`` **do?**

   Similiar to ``imsi reload``, ``imsi set -s`` re-resolves and re-extracts the
   the upstream imsi Configuration Files from ``/src/imsi-config`` and updates
   (overwrites) the Resolved Configuration File and contents in the downstream
   configuration folders (``/config`` and ``/sequencer``).

   The best use of ``imsi set -s`` is to apply changes while developing new
   configuration locally. See :ref:`using-imsi-set` for an illustration of this
   workflow.

   Multiple selections can also be combined together, as in:

   .. code-block::

      >> imsi set -s model=model-x -s exp=exp-y


4\. Apply blocks of pre-defined modifications using ``imsi override --option``
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++


   +------------------+------------------------------------------------------------------+
   | **Command**      | .. code-block:: bash                                             |
   |                  |                                                                  |
   |                  |     >> imsi override --option <option_block>/<option_file>       |
   |                  |                                                                  |
   +------------------+------------------------------------------------------------------+
   | **Steps**        | Run the command above. The options are defined in the imsi       |
   |                  | Configuration Files for the source, nominally in YAML files      |
   |                  | under ``imsi-config/options/<option_block>/<option_file>``.      |
   +------------------+------------------------------------------------------------------+
   | **Purpose**      | Apply pre-defined sets of modifications to the run               |
   |                  | configuration. The directory ``<option_block>`` and its contents |
   |                  | can be generally thought of as common modifications to           |
   |                  | configuration that are not otherwise captured in the structured  |
   |                  | configuration system.                                            |
   +------------------+------------------------------------------------------------------+

   **What does** ``imsi override --option`` **do?**

   In simple terms, ``imsi override --option`` is analogous to manually modifying the Resolved
   Configuration File and running ``imsi config``.

.. warning::

   **Avoid editing the contents of the Run Configuration Folder directly**

      The contents of ``/config`` are ultimately what are intended to be used by
      the model. Users should **not** edit the contents of these files directly, since
      these **these modifications can be overwritten** by subsequent imsi commands.
      Some of these contents may also be used by the model at run time.

      Users should use the methods described above to also ensure that their
      modifications are repeatable and sharable.


.. _using-imsi-set:

Using ``imsi set``
++++++++++++++++++

``imsi set`` is most appropriate for making more complex, compound modifications
to configuration.

``imsi set --selections`` is most useful for developing new sets of configurations.

For example, suppose a user sets up a run using

.. code-block:: bash

   >> imsi setup --model=model-A --exp=exp-A ...

The configuration for the model and experiment are contained in the imsi
Configuration Files for the source repository.

After initial setup, the user wants to develop a new experiment for the model,
``exp-B``. They add a new file in their local run setup folder:

.. code-block:: text

   src/imsi-config
   ├── experiments
   │   ├── imsi-exp-config_exp-A.yaml
   |   └── imsi-exp-config_exp-B.yaml        <-- new
   ├── models
   │   ├── imsi-model-config_model-A.yaml

which contains:

.. code-block:: yaml

   experiments:
     exp-B:
        supported_models:
          - model-A
        inherits_from: exp-A
        # ... more configuration for exp-B ...

To then use ``exp-B`` in their local run setup, they should then run

.. code-block:: bash

   >> imsi set -s exp=exp-B

Any further modifications to the upstream Configuration File for ``exp-B``
can be applied by using ``imsi reload`` for simplicity thereafter.


Validating imsi configuration files with ``imsi validate``
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The user can run ``imsi validate`` during development to ensure that the contents
of their configurations are valid. This command checks for schema compliance and YAML syntax. While it does **not** check for logical consistency of configuration contents, it can help catch common errors early in the development process.

The output of ``imsi validate -h``:

.. program-output:: imsi validate -h



Building run executables
------------------------

With ``imsi build``
++++++++++++++++++++

.. code-block::

   >> imsi build

It is worth noting that all this does is call the extracted ``imsi-tmp-compile.sh`` script. Additionally,
if `any` arguments/flags are provided after ``imsi build``, it will send the arguments to extracted script.

For example:

.. code-block::

   >> imsi build -f -a

would send the ``-f -a`` flags to ``imsi-tmp-compile.sh``.


Saving restarts
------------------

With ``imsi save-restarts``
++++++++++++++++++++++++++++++

.. code-block:: bash

    >> imsi save-restarts

Note that likewise to ``imsi build``, ``imsi save-restarts`` just calls the extracted ``save_restart_files.sh``
script `and` any arguments and/or flags given to to the call are sent to the underlying script.

If the restart files you need are on tape storage, you'll need to run the following instead:

.. code-block:: bash

    >> imsi tapeload-rs

which is effectively a wrapper for the script ``tapeload_rs.sh``.

Submitting the run
-------------------

With ``imsi submit``
++++++++++++++++++++++

.. code-block:: bash

    >> imsi submit

This will interact with the sequencer in use and intelligently execute a sequencer/machine specific submission
command.

Monitoring a run
----------------

While many HPC users will be accustomed to monitoring simulations/jobs via sequencer specific tools (``xflow``
for ``maestro`` users) or job-scheduler commands like ``qstat`` or ``squeue``. Provided the sequencer being used
support this, ``imsi`` also provides a method for monitoring the status of a simulation (or ensemble of simulations):


For maestro sequencers with ``imsi status``
++++++++++++++++++++++++++++++++++++++++++

This CLI command ultimately interfaces with the sequencer caps, so **the behaviour of this command is sequencer specific**. To run the status command, do:

.. code-block:: bash

   >> imsi status


For ``maestro``, will result in:

.. image:: _static/maestro_status.png
   :alt: Maestro ``imsi status`` output
   :align: center

.. raw:: html

   <div style="height:10px"></div>


which will tell you all the ``maestro`` experiments running, and within each experiment, it will show you
which jobs are currently queued, running, failed, completed, or in ``maestro``'s "catchup" status.

iss
+++++++

This feature has not yet been implemented for ``iss`` - if you execute this command while using ``iss``, you will
see a ``NotImplementedError`` raised.
