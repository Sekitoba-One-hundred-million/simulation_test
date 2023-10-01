import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import sekitoba_library as lib
import sekitoba_data_manage as dm

def main():
    move_money_list = []
    recovery_data = {}
    test_result = { "count": 0, "bet_count": 0, "money": 0, "win": 0 }
    rank_model = dm.pickle_load( "rank_model.pickle" )
    data = dm.pickle_load( "rank_simu_data.pickle" )
    popular_kind_win_rate_data = dm.pickle_load( "popular_kind_win_rate_data.pickle" )
    wide_odds_data = dm.pickle_load( "wide_odds_data.pickle" )
    odds_data = dm.pickle_load( "odds_data.pickle" )
    users_score_data = dm.pickle_load( "users_score_data.pickle" )

    def wide_odds_get( horce_num_1, horce_num_2 ):
        min_horce_num = int( min( horce_num_1, horce_num_2 ) )
        max_horce_num = int( max( horce_num_1, horce_num_2 ) )

        try:
            return wide_odds_data[race_id][min_horce_num][max_horce_num]
        except:
            return {}

    race_id_list = list( data.keys() )
    random.shuffle( race_id_list )
    
    for race_id in tqdm( race_id_list ):
        year = race_id[0:4]
        number = race_id[-2:]

        if not year == "2022":
            continue

        if not race_id in users_score_data:
            continue

        horce_list = []
        all_score = 0
        min_users_score = 100
        min_rank_score = 100
        all_horce_num = len( data[race_id] )
        
        for horce_id in data[race_id].keys():
            if not horce_id in users_score_data[race_id]:
                continue
            
            scores = {}
            ex_dict = {}
            p_data = rank_model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )
            score = p_data[0]
            all_score += score
            ex_dict["score"] = score
            ex_dict["users_score"] = 0
            ex_dict["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_dict["odds"] = data[race_id][horce_id]["answer"]["odds"]
            ex_dict["popular"] = data[race_id][horce_id]["answer"]["popular"]
            ex_dict["horce_num"] = data[race_id][horce_id]["answer"]["horce_num"]
            ex_dict["horce_id"] = horce_id
            ex_dict["ex_score"] = 0

            for k in users_score_data[race_id][horce_id]:
                ex_dict["users_score"] += users_score_data[race_id][horce_id][k]

            min_users_score = min( min_users_score, ex_dict["users_score"] )
            min_rank_score = min( min_rank_score, ex_dict["score"] )
            horce_list.append( ex_dict )

        if len( horce_list ) < 6: #or all_horce_num > 8:
            continue

        score_rate = 1
        popular_rate = 0.1

        if all_score == 0:
            continue

        all_score -= len( horce_list ) * min_rank_score

        for horce_data in horce_list:
            horce_data["score"] -= min_rank_score
            horce_data["score"] /= all_score

        buy = False
        bet_count = 1#int( max_have_money / check_money ) * 10
        #if all_horce_num < 9:
        #    bet_count *= 2

        bet_candidate = []
        users_sort_result = sorted( horce_list, key=lambda x:x["users_score"], reverse = True )
        rank_sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )
        base_horce_num_list = [ rank_sort_result[0]["horce_num"] ]
        check_formation_count = [ len( rank_sort_result ) ]
        
        for i in range( 0, len( rank_sort_result ) ):
            rank_1 = rank_sort_result[i]["rank"]
            horce_num_1 = rank_sort_result[i]["horce_num"]
            ex_score_1 = rank_sort_result[i]["score"]

            for r in range( i + 1, len( rank_sort_result ) ):
                rank_2 = rank_sort_result[r]["rank"]
                horce_num_2 = rank_sort_result[r]["horce_num"]

                #users_score = users_sort_result[r]["users_score"]
                ex_score_2 = rank_sort_result[r]["score"]
                wide_odds = wide_odds_get( horce_num_1, horce_num_2 )

                if len( wide_odds ) == 0:
                    continue

                bet_candidate.append( { "horce_num": [ horce_num_1, horce_num_2 ], \
                                       "rank": [ rank_1, rank_2 ], \
                                       "wide_odds": wide_odds["min"], \
                                       "bet_count": bet_count,
                                       "score": ex_score_1 + ex_score_2 } )
        
        if len( bet_candidate ) < 0:
            continue

        rk = int( all_horce_num )
        
        for bc in bet_candidate:
            rank_1 = bc["rank"][0]
            rank_2 = bc["rank"][1]
            horce_num_1 = bc["horce_num"][0]
            horce_num_2 = bc["horce_num"][1]
                
            buy = True

            test_result["bet_count"] += bc["bet_count"]
            lib.dic_append( recovery_data, rk, { "recovery": 0, "count": 0 } )
            recovery_data[rk]["count"] += bc["bet_count"] 
            
            if rank_1 <= 3 and rank_2 <= 3:
                try:
                    wide_odds = odds_data[race_id]["ワイド"][int(rank_1+rank_2-3)] / 100
                except:
                    continue

                test_result["win"] += 1
                test_result["money"] += wide_odds * bc["bet_count"]
                recovery_data[rk]["recovery"] += wide_odds
            
        if buy:
            test_result["count"] += 1

    recovery_rate = ( test_result["money"] / test_result["bet_count"] ) * 100
    win_rate = ( test_result["win"] / test_result["count"] ) * 100

    key_list = sorted( list( recovery_data.keys() ) )
    print( "" )

    for k in key_list:
        recovery = recovery_data[k]["recovery"] / recovery_data[k]["count"]
        print( k, recovery, recovery_data[k]["count"] )

if __name__ == "__main__":
    main()
