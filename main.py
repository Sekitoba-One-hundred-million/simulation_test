def main():
    import sekitoba_data_manage as dm
    from simulation import buy_simulation
    from simulation import baren_simulation
    from simulation import test
    
    #simu_data = dm.pickle_load( "rank_simu_data.pickle" )
    #model = dm.pickle_load( "rank_model.pickle" )
    buy_simulation.main()
    #baren_simulation.main()
    #test.main()

if __name__ == "__main__":
    main()
