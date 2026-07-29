def main():
    #from argparse import ArgumentParser
    #import matplotlib.pyplot as plt
    #import numpy as np
    #from mpi4py import MPI
    #from tqdm import tqdm

    #import SekitobaDataManage as dm
    import SekitobaLibrary as lib
    #from simulation import buy_simulation
    #from simulation import recovery_simulation
    from simulation import simulation_test
    from simulation import one_simulation
    from simulation import ex_simulation
    from simulation import triplet_simulation

    lib.name.set_name( "time_index" )
    lib.log.set_write( False )
    #simulation_test.main()
    one_simulation.main()
    #ex_simulation.main()
    #triplet_simulation.main()

if __name__ == "__main__":
    main()
