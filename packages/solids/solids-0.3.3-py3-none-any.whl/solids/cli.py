def main():
    import sys
    from textwrap import dedent
    if len(sys.argv) != 2:
        print("Please note that the correct usage is ./run_solids.py desiredInput (modify desiredInput.txt to your liking and then w)")
        sys.exit(1)
    inst = sys.argv[1]
    if inst == "input_emt":
        input_text = dedent("""
        ---COMPOSITION---
        Al 10
        ---COMPOSITION---
        formula_units        1          #The number of atoms in composition are multiplied by this number
        dimension            3          #Solids can handle 2- and 3-dimensional crystals
        volume_factor        1.0        #The volume factor of the unit cell
        tol_atomic_overlap   0.97       #The minimum distance between atoms is 95% the sum of their radii

        #ALGORITHM PARAMETERS:
        algorithm            evolutive  #Stochastic -> Stochastic algorithm, evolutive-> Evolutive Algorithm
        nof_initpop          10         #Size of the initial population of crystals

        #Evolutive:
        nof_matings          20         #Number of matings
        nof_strains          6         #Number of strains
        nof_xchange          0          #Number of atom exchanges

        #NICHING PARAMETERS:
        tol_similarity       0.97       #Tol for similarity
        cutoff_energy        5.0        #Energy Cut-off
        cutoff_population    10         #Number of final candidates

        #HALT CRITERION:
        #Stochastic:
        nof_stages            2       #Number of Optimization Stages in the Stochastich algorithm

        #STOP CRITERION:
        nof_generations         20   #Max generations
        nof_repeats             5    #Number of repeated polymorphs
        nof_stagnant            7    #Max stagnant cycles

        #THEORY LEVEL:
        calculator            EMT     #Available calculators: EMT, VASP, GULP
        nof_processes         10      #Number of parallel local opts"""
        ).strip()
        inputfile = 'inputEMT'
        with open(inputfile, "w") as f: 
            f.write(input_text)
    elif inst == "input_vasp":
        input_text = dedent("""
        ---COMPOSITION---
        C  2
        ---COMPOSITION---
        formula_units           4
        dimension               3
        volume_factor           1.0
        tol_atomic_overlap      0.95
        algorithm               evolutive

        #EVOLUTIVE PARAMETERS:
        nof_initpop             15    #Initial Population
        nof_matings             12     #Number of matings
        nof_strains             3
        nof_xchange             0

        #NICHING PARAMETERS:
        tol_similarity          0.95  #Tol for similarity
        cutoff_energy           2.0   #Energy Cut-off
        cutoff_population       8     #Max population size

        #HALT CRITERION:
        nof_generations         10    #Max generations
        nof_repeats             5     #Max repeated isomers
        nof_stagnant            5     #Max stagnant cycles

        #THEORY LEVEL:
        nof_processes           6    #Number of parallel local opts
        calculator              VASP
        nof_parcalcs            7

        ---VASP---
        ---VASP---""").strip()
        inputfile = 'inputVASP'
        with open(inputfile, "w") as f: 
            f.write(input_text)
    elif inst == "input_gulp":
        input_text = dedent("""
        ---COMPOSITION---
        Ti   1
        O    2
        ---COMPOSITION---
        formula_units           4
        dimension               3
        volume_factor           1.0
        tol_atomic_overlap      0.98

        #ALGORITHM PARAMETERS:
        algorithm               evolutive
        nof_initpop             10    #Initial Population

        #Evolutive
        nof_matings             20    #No. of matings
        nof_strains             6     #No. of strains
        nof_xchange             6     #No. of atom exchanges

        #NICHING PARAMETERS:
        tol_similarity          0.98  #Tol for similarity
        cutoff_energy           5.0   #Energy Cut-off
        cutoff_population       10    #Number of final candidates

        #HALT CRITERION:
        #Stochastic:
        nof_stages              2     #Number of Optimization Stages when using the Stochastich algorithm

        #Evolutive:
        nof_repeats             3     #Breaks the process if the same structures are repeated 5 times
        nof_stagnant            2     #If the best 3 solutions are iteratively located, the process stops
        nof_generations         20     #Number of generations

        #THEORY LEVEL:
        calculator              GULP
        nof_processes           10    #Number of parallel local opts
        path_exe                /home/installdir/bin/gulp

        ---GULP---
        opti conj conp
        switch_minimiser bfgs gnorm 0.01
        vectors
        LATTICEVECTORS
        frac
        COORDINATES
        lib /home/GULP/Libraries/matsui-akaogi.lib
        ---GULP---

        # Parameters for local optimizations with different potentials
        #TiO2
        #---GULP---
        #opti conj conp
        #switch_minimiser bfgs gnorm 0.01
        #vectors
        #LATTICEVECTORS
        #frac
        #COORDINATES
        #lib /home/GULP/Libraries/matsui-akaogi.lib
        #---GULP---

        ##SiO2
        #---GULP---
        #opti conj conp
        #switch_minimiser bfgs gnorm 0.01
        #vectors
        #LATTICEVECTORS
        #frac
        #COORDINATES
        #lib /home/GULP/Libraries/tsuneyuki.lib
        #---GULP---

        # MgAl2O4 100GPa
        # ---GULP---
        # opti conjugate nosymmetry conp
        # switch_minimiser bfgs gnorm 0.01
        # pressure 100 GPa
        # vectors
        # LATTICEVECTORS
        # frac
        # COORDINATES
        # space
        # 1
        # species
        # Mg  2.0
        # Al  3.0
        # O  -2.0
        # lennard 12 6
        # Mg O   1.50 0.00 0.00 6.0
        # Al O   1.50 0.00 0.00 6.0
        # O O    1.50 0.00 0.00 6.0
        # Mg Mg  1.50 0.00 0.00 6.0
        # Mg Al  1.50 0.00 0.00 6.0
        # Al Al  1.50 0.00 0.00 6.0
        # buck
        # Mg O 1428.5 0.2945 0.0 0.0 7.0
        # Al O 1114.9 0.3118 0.0 0.0 7.0
        # O O  2023.8 0.2674 0.0 0.0 7.0
        # maxcyc 850
        # switch rfo 0.010
        # ---GULP---

        #MgSiO3
        # ---GULP---
        # opti conjugate nosymmetry conv
        # switch_minimiser bfgs gnorm 0.01
        # vectors
        # LATTICEVECTORS
        # frac
        # COORDINATES
        # space
        # 1
        # species
        # Mg 1.8
        # Si 2.4
        # O -1.4
        # lennard 12 6
        # Mg O  2.5 0.0 0.0 6.0
        # Mg Si 1.5 0.0 0.0 6.0
        # Si O  1.5 0.0 0.0 6.0
        # Mg Mg 1.5 0.0 0.0 6.0
        # Si O  1.5 0.0 0.0 6.0
        # O  O  2.5 0.0 0.0 6.0
        # buck
        # Mg O   806.915 0.291 2.346 0.0 10.0
        # Si O  1122.392 0.256 0.000 0.0 10.0
        # O O    792.329 0.362 31.58 0.0 10.0
        # Mg Mg  900.343 0.220 0.174 0.0 10.0
        # Mg Si 1536.282 0.185 0.000 0.0 10.0
        # Si Si 3516.558 0.150 0.000 0.0 10.0
        # maxcyc
        # 800
        # switch rfo cycle 350
        # ---GULP---"""
        ).strip()
        inputfile = 'inputGULP'
        with open(inputfile, "w") as f: 
            f.write(input_text)
    else: 
        inputfile = sys.argv[1]
        from solids.heuristic  import mainAlgorithm
        xopt_sort=mainAlgorithm(inputfile)
