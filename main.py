def main():
    import sekitoba_data_manage as dm
    #from simulation import buy_simulation
    #from simulation import test
    from analyze import kernel
    from simulation import wide_simulation
    rank_model = dm.pickle_load( "rank_model.pickle" )
    data = dm.pickle_load( "rank_simu_data.pickle" )

    kernel_data = kernel.main( rank_model, data )
    #test.main( rank_model, data, kernel_data )
    #buy_simulation.main()
    wide_simulation.main( rank_model, data, kernel_data )

if __name__ == "__main__":
    main()
