import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import sekitoba_library as lib
import sekitoba_data_manage as dm

def best_index_get( partern_list, bet_candidate ):
    score = -10000000
    index = -1

    for i in range( 0, len( bet_candidate ) ):
        rate = 0
        score_list = { "+": [], "-": [] }
        bet_candidate[i]["bet_count"] += 1

        for partern in partern_list:
            current_score = 0
            
            for bc in bet_candidate:                
                wide_odds = bc["wide_odds"]
                rate_score = partern["score"]
                #print( bc )

                if bc["horce_num"][0] in partern["horce_num"] and \
                  bc["horce_num"][1] in partern["horce_num"]:
                    current_score += bc["bet_count"] * rate_score * wide_odds
                else:
                    current_score -= math.pow( bc["bet_count"], 1.5 ) * rate_score

            if current_score == 0:
                continue
            elif current_score < 0:
                score_list["-"].append( current_score )
            else:
                score_list["+"].append( current_score )
            
        sum_len = len( score_list["+"] ) + len( score_list["-"] )
        plus_rate = math.pow( len( score_list["+"] ) / sum_len, 2 )
        minus_rate = math.pow( len( score_list["-"] ) / sum_len, 2 )
        instance_score = sum( score_list["+"] ) * plus_rate + sum( score_list["-"] ) * minus_rate
        #print( i, instance_score )

        if score < instance_score:
            index = i
            score = instance_score

        bet_candidate[i]["bet_count"] -= 1

    #print( "" )
    return index, score

def bet_best_get( partern_list, bet_candidate ):
    all_score = 0
    
    for i in range( 0, len( bet_candidate ) ):
        current_score = 0
        horce_num_1 = bet_candidate[i]["horce_num"][0]
        horce_num_2 = bet_candidate[i]["horce_num"][1]
        wide_odds = bet_candidate[i]["wide_odds"]
        
        for partern in partern_list:
            rate_score = partern["score"]

            if horce_num_1 in partern["horce_num"] and \
              horce_num_2 in partern["horce_num"]:
                current_score += rate_score * wide_odds
            else:
                current_score -= rate_score

        bet_candidate[i]["ex_score"] = math.exp( current_score )
        all_score += math.exp( current_score )

    if all_score == 0:
        return None, None
    
    bet_candidate = sorted( bet_candidate, key = lambda x:x["ex_score"], reverse = True )
    
    bt = 30
    score = 0
    
    for i in range( 0, len( bet_candidate ) ):
        bet_candidate[i]["ex_score"] /= all_score
        bet_candidate[i]["bet_count"] = int( bt * bet_candidate[i]["ex_score"] )
        score += bet_candidate[i]["ex_score"] * bet_candidate[i]["wide_odds"]

    return bet_candidate, score

def main( rank_model, data, kernel_data ):
    have_money = 3000
    move_money_list = []
    test_result = { "count": 0, "bet_count": 0, "money": 0, "win": 0 }

    wide_odds_data = dm.pickle_load( "wide_odds_data.pickle" )
    odds_data = dm.pickle_load( "odds_data.pickle" )

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
        
        if not year in lib.test_years:
            continue
        
        horce_list = []
        
        for horce_id in data[race_id].keys():
            scores = {}
            ex_value = {}
            
            p_data = rank_model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )
            ex_value["score"] = math.exp( kernel_data["model"].score_samples( np.array( [ [ p_data[0] - kernel_data["max_score"] ] ] ) )[0] )
            ex_value["base_score"] = p_data[0]
            ex_value["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_value["odds"] = data[race_id][horce_id]["answer"]["odds"]
            ex_value["popular"] = data[race_id][horce_id]["answer"]["popular"]
            ex_value["horce_num"] = data[race_id][horce_id]["answer"]["horce_num"]
            ex_value["horce_id"] = horce_id
            horce_list.append( ex_value )

        if len( horce_list ) < 3 or len( horce_list ) > 14:
            continue

        all_score = 0
        sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )

        for i in range( 0, len( sort_result ) ):
            sort_result[i]["score"] /= ( 1 + ( i * 0.3 ) )
            all_score += sort_result[i]["score"]

        for i in range( 0, len( sort_result ) ):
            sort_result[i]["score"] /= all_score
            
        buy = False
        bc = 1

        if len( sort_result ) < 5:
            continue

        all_score = 0
        partern_list = []

        for i in range( 0, len( sort_result ) ):
            score_1 = sort_result[i]["score"]
            rank_1 = sort_result[i]["rank"]
            horce_num_1 = sort_result[i]["horce_num"]

            for r in range( i + 1, len( sort_result ) ):
                score_2 = sort_result[r]["score"]
                rank_2 = sort_result[r]["rank"]
                horce_num_2 = sort_result[r]["horce_num"]

                for t in range( r + 1, len( sort_result ) ):
                    score_3 = sort_result[t]["score"]
                    score_3 = math.exp( kernel_data["model"].score_samples( np.array( [ [ score_3 ] ] ) )[0] )
                    horce_num_3 = sort_result[t]["horce_num"]
                    partern_list.append( { "horce_num": [ horce_num_1, horce_num_2, horce_num_3 ], \
                                        "score": score_1 * score_2 * score_3 } )                    
                    all_score += score_1 * score_2 * score_3
                    instance_score = 1                    

        for i in range( 0, len( partern_list ) ):
            partern_list[i]["score"] /= all_score

        bet_candidate = []
        sum_odds = 0
        
        for i in range( 0, 3 ):
            rank_1 = sort_result[i]["rank"]
            horce_num_1 = sort_result[i]["horce_num"]

            for r in range( i + 1, 4 ):
                rank_2 = sort_result[r]["rank"]
                horce_num_2 = sort_result[r]["horce_num"]
                wide_odds = wide_odds_get( horce_num_1, horce_num_2 )

                if len( wide_odds ) == 0:
                    continue

                sum_odds += wide_odds["min"]
                bet_candidate.append( { "horce_num": [ horce_num_1, horce_num_2 ], \
                                       "rank": [ rank_1, rank_2 ], \
                                       "wide_odds": wide_odds["min"], \
                                       "bet_count": 0 } )

        for bc in bet_candidate:
            bc["rate"] = 0
            
            for partern in partern_list:
                if bc["horce_num"][0] in partern["horce_num"] and \
                  bc["horce_num"][1] in partern["horce_num"]:
                    bc["rate"] += partern["score"]

            
        #c = int( have_money / 50 )
        c = 50
        
        for i in range( 0, c ):
            index, score = best_index_get( partern_list, bet_candidate )
            bet_candidate[index]["bet_count"] += 1

        if sum_odds > 30:
            continue

        for bc in bet_candidate:
            rank_1 = bc["rank"][0]
            rank_2 = bc["rank"][1]
            horce_num_1 = bc["horce_num"][0]
            horce_num_2 = bc["horce_num"][1]
                
            buy = True
            test_result["bet_count"] += bc["bet_count"]
            have_money -= bc["bet_count"]
            
            if rank_1 <= 3 and rank_2 <= 3:
                try:
                    wide_odds = odds_data[race_id]["ワイド"][int(rank_1+rank_2-3)] / 100
                except:
                    continue
                    
                test_result["win"] += 1
                test_result["money"] += wide_odds * bc["bet_count"]
                have_money += wide_odds * bc["bet_count"]

        if buy:
            test_result["count"] += 1
            move_money_list.append( have_money )

    recovery_rate = ( test_result["money"] / test_result["bet_count"] ) * 100
    win_rate = ( test_result["win"] / test_result["count"] ) * 100
    
    print( "" )
    print( "ワイド 回収率{}%".format( recovery_rate ) )
    print( "ワイド 勝率{}%".format( win_rate ) )
    print( "賭けた回数{}回".format( test_result["bet_count"] ) )
    print( "賭けたレース数{}回".format( test_result["count"] ) )

    plt.plot( list( range( 0, len( move_money_list ) ) ), move_money_list )
    plt.savefig( "/Volumes/Gilgamesh/move_money.png" )
