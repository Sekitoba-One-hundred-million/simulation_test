import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import sekitoba_library as lib
import sekitoba_data_manage as dm

def main():
    recovery_rate = 0
    test_result = { "count": 0, "bet_count": 0, "one_money": 0, "one_win": 0 }
    check = {}
    t = 1

    rank_model = dm.pickle_load( "rank_model.pickle" )
    data = dm.pickle_load( "rank_simu_data.pickle" )
    #rank_dist_model = dm.pickle_load( "rank_dist_model.pickle" )
    #rank_dist_data = dm.pickle_load( "rank_dist_simu_data.pickle" )
    baren_odds_data = dm.pickle_load( "baren_odds_data.pickle" )
    
    for race_id in tqdm( data.keys() ):
        year = race_id[0:4]
        number = race_id[-2:]
        
        if not year in lib.test_years:
            continue
        
        horce_list = []
        score_list = []
        
        for horce_id in data[race_id].keys():
            scores = {}
            ex_value = {}
            
            p_data = rank_model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )
                
            ex_value["score"] = p_data[0]
            ex_value["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_value["odds"] = data[race_id][horce_id]["answer"]["odds"]
            ex_value["popular"] = data[race_id][horce_id]["answer"]["popular"]
            ex_value["horce_num"] = data[race_id][horce_id]["answer"]["horce_num"]
            ex_value["horce_id"] = horce_id
            horce_list.append( ex_value )
            score_list.append( p_data[0] )

        if len( horce_list ) < 3:
            continue

        sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )
        use_horce_num = []

        def baren_odds_get( horce_num_1, horce_num_2 ):
            min_horce_num = int( min( horce_num_1, horce_num_2 ) )
            max_horce_num = int( max( horce_num_1, horce_num_2 ) )

            try:
                return baren_odds_data[race_id][min_horce_num][max_horce_num]
            except:
                return -1

        bc = 1
        t = 3
        buy = False
        
        horce_num_1 = sort_result[0]["horce_num"]
        rank_1 = sort_result[0]["rank"]
        score_1 = sort_result[0]["score"]

        for r in range( 1, 4 ):
            horce_num_2 = sort_result[r]["horce_num"]
            rank_2 = sort_result[r]["rank"]
            score_2 = sort_result[r]["score"]
            baren_odds = baren_odds_get( horce_num_1, horce_num_2 )

            if baren_odds == -1:
                continue

            if score_1 < 0 or score_2 < 0:
                continue

            bc = int( baren_odds * score_2 * score_1 )
            buy = True
            test_result["bet_count"] += bc
            
            if rank_1 <= 2 and rank_2 <= 2:
                test_result["one_win"] += 1
                test_result["one_money"] += baren_odds * bc

                if 50 < baren_odds:
                    print( baren_odds, bc )

        if buy:
            test_result["count"] += 1            
                    
    one_recovery_rate = ( test_result["one_money"] / test_result["bet_count"] ) * 100 
    one_win_rate = ( test_result["one_win"] / test_result["count"] ) * 100
    
    print( "" )
    print( "馬連 回収率{}%".format( one_recovery_rate ) )
    print( "馬連 勝率{}%".format( one_win_rate ) )
    print( "賭けた回数{}回".format( test_result["bet_count"] ) )

    #for k in check.keys():
    #    count = check[k]["count"]
    #    recovery = check[k]["recovery"] / count
    #    recovery *= 100

    #    if recovery > 90:
    #        print( k, count, recovery )
