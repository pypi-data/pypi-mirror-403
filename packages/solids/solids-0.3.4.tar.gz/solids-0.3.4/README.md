# SolidASE_0.0
Crystal Structure Prediction for web-based frameworks

This code is intended to explore the energy landscape of crystalline structures using Python and its libraries such as ASE, PyXtal, Dscribe, and Aegon.

Solids relies in two separated schemes: The Stochastich Algorithm and the Evolutive Algorithm.

The Stochastich Algorithm builts and relaxes a set of Point-Group-Based structues in order to preliminarily explore the energy landscape of cystalline structures. The advantage of this process is that is based on stages where the level of theory can be refined after each stage.

The Evolutive Algorithm improves on the Stochastic one by transmiting the already-available good structural traits to new generations using Crossover and Mutation operators. Each set of crossovers and mutants are relaxed and, in turn, pass on their characteristics to new candidates, untill halting criteria is met. 

In version 1.0 Solids is interfaced with ESM optimization by ASE, GULP and VASP.

#Usage
To install in UNIX-based systems, use pip install solids.

Once installed, used ./run_solids.py input_emt to create the inputEMT file.

Then, execute the code by typping ./run_solids.py inputEMT.


