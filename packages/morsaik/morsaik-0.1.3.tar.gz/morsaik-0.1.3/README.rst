README
======

Welcome to the Motif Reactor Simulation, Analysis and Inference Kit (``morsaik``) repository.

Introduction
------------

In order to investigate RNA reactors as candidates for the origins of life,
efficient simulations are needed
because the space of possible RNA sequences increases exponentially with the length of the strands,
as well as the number of reactions between two strands.
In addition, simulations have to be compared to experimental data for validation and parameter calibration.
Here, we present the ``morsaik`` python package for sqeuence motif (or k-mer) reactor simulation, analysis and inference.
It enables users to simulate RNA sequence motif dynamics in the mean field approximation
as well as to infer the reaction parameters from data
with Bayesian methods and to analyze results by computing observables and plotting.
``morsaik`` simulates an RNA reactor by following the reactions and the concentrations of all strands inside up to a certain length (of four nucleotides by default).
Longer strands are followed indirectly, by tracking the concentrations of their containing sequence motifs of that maximum length.

For a more detailed introduction,
please go to the demos_.

.. _demos: https://github.com/joharkit/morsaik/tree/main/demos

For an overview of the package and its aim,
please refer to the paper_ or the documentation_.

.. _paper: https://github.com/joharkit/morsaik/tree/main/paper
.. _documentation: https://joharkit.github.io/morsaik

Installation
------------

You can install ``morsaik`` from PyPI

.. code-block:: shell

    pip install morsaik

Alternatively, clone the repository from source, go into the directory and install it via ``pip``:

.. code-block:: shell

    git clone https://github.com/joharkit/morsaik.git
    cd morsaik
    pip install .

Contribution
------------

You are very welcome to contribute to this package.
Please open an issue and send a PR with your changes.
Please remember to upgrade the docs and the manual if needed
and adjust the test pipeline, adding new tests eventually.
In case of any questions, please contact me.

Tests
-----

All important functions are tested with tests in the `test` directory.
The `.gitlab-ci.yml` performs all tests automatically.

If you want to run the tests locally, please make sure, everything is installed
and just run

.. code-block:: shell

   pytest

or, if you use ``poetry`` run

.. code-block:: shell

   poetry run pytest

This will start all tests.
Since those are quite a lot, please ensure, you have enough computational
resources.
Else, just specify the test you want to run
as an argument directly after the ``pytest`` command.
