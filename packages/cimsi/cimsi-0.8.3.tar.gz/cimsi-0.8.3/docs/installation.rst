Installation
=============

IMSI and its dependencies can be installed from git or PyPI into a Python 3 virtual environment.

.. note::
    ECCC users on U2 can access the group environment by referencing the CanESM docs.

Creating a virtual environment
-----------------------------------------------


You can create a virtual environment using `UV <https://docs.astral.sh/uv/>`_ (recommended):

.. code-block:: bash

    >> uv venv imsi-venv --python=3.12   # Python 3.12+ is supported
    >> source activate imsi-venv


Or, to create a virtual environment with standard python tooling (use `venv <https://docs.python.org/3/library/venv.html>`_):

.. code-block:: bash

    >> python3 -m venv imsi-venv
    >> source imsi-venv/bin/activate


Installing imsi into your environment from PyPI
----------------------------------------------------------------


.. code-block:: bash

    # install IMSI directly from PyPI
    >> uv pip install cimsi


Or you can use standard python tooling with pip:

.. code-block:: bash

    >> pip install cimsi


Local installation
-----------------------------------------------


IMSI can be installed locally by cloning the source repository. You can use the ``-e`` flag to install in editable/development mode.

.. code-block:: bash
    
    >> git clone git@gitlab.science.gc.ca:CanESM/imsi.git
    >> cd imsi
    >> uv pip install -e .
    # or pip install -e . for standard python tooling


Testing the installation
--------------------------

After installation, verify IMSI is available by running:

.. code-block:: bash

    >> imsi --version


This should print the current IMSI version.

Tab Completion
-----------------
.. tip::

    If you are using bash v >= 4.4 and Python click v >= 8.x, you can enable
    tab-completion for imsi CLI commands. These are not required and are
    simply for convenience.

    **Steps:**

    1. Activate an imsi environment

    .. code-block:: bash

       >> source /path/to/imsi/bin/activate

    You can confirm that the environment is active by entering ``which imsi`` on your command line.

    2. Generate the shell functions required, and save them to a file in a location accessible to you.

    .. code-block::

       >> _IMSI_COMPLETE=bash_source imsi > ~/.imsi-complete.bash

    In the example above, the file ``.imsi-complete.bash`` is saved to the user's home directory.

    3. Source the file. You can do this on the command line or from within your profile.

    .. code-block:: bash

        # .profile
        >> source ~/.imsi-complete.bash

    **Result:**

    You should now be able to use tabs to trigger suggested functions and options
    for imsi commands. These tab-completions are triggered using **two** tabs.

    .. code-block:: bash

       >> imsi <TAB><TAB>
       build          config         list           save-restarts  status
       chunk-manager  ensemble       log-state      set            submit
       clean          iss            reload         setup
       >> imsi setup -<TAB><TAB>
       --runid         --ver           --model         --seq           --flow          -h
       --repo          --exp           --fetch_method  --machine       --postproc      --help

    The generalized instructions can also be found in the
    `click documentation on Shell Completion <https://click.palletsprojects.com/en/stable/shell-completion/>`_
