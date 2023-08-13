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

                if bc["horce_num"][0] in partern["horce_num"] and \
                  bc["horce_num"][1] in partern["horce_num"]:
                    current_score += bc["bet_count"] * rate_score * wide_odds
                else:
                    current_score -= math.pow( bc["bet_count"], 1.2 ) * rate_score

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

def candiate_create( horce_data, partern_list ):
    bet_candidate_list = []
    all_bet_patern = {}
    sum_odds = 0
    sort_result = sorted( horce_data, key = lambda x:x["horce_num"] )

    # ワイドの全てのパターン
    for i in range( 0, len( sort_result ) ):
        rank_1 = sort_result[i]["rank"]
        horce_num_1 = sort_result[i]["horce_num"]
        all_patern[horce_num_1] = {}

        for r in range( i + 1, len( sort_result ) ):
            rank_2 = sort_result[r]["rank"]
            horce_num_2 = sort_result[r]["horce_num"]
            wide_odds = wide_odds_get( horce_num_1, horce_num_2 )
            
            if len( wide_odds ) == 0:
                continue

            all_bet_patern[horce_num_1][horce_num_2] = { "horce_num": [ horce_num_1, horce_num_2 ], \
                                                        "rank": [ rank_1, rank_2 ], \
                                                        "wide_odds": wide_odds["min"], \
                                                        "bet_count": 0 }

    # 対象のワイドが起きる確率を算出
    for horce_num_1 in all_bet_patern.keys():
        for horce_num_2 in all_bet_patern[horce_num_1].keys():
            all_bet_patern[horce_num_1][horce_num_2]["rate"] = 0
                        
            for partern in partern_list:
                if horce_num_1 in partern["horce_num"] and \
                  horce_num_2 in partern["horce_num"]:
                    all_bet_patern[horce_num_1][horce_num_2]["rate"] += partern["score"]
                

def main( rank_model, data, kernel_data ):
    have_money = 3000
    move_money_list = []
    recovery_data = {}
    test_result = { "count": 0, "bet_count": 0, "money": 0, "win": 0 }
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
        
        if not year in lib.test_years:
            continue

        if not race_id in users_score_data:
            continue
        
        horce_list = []
        all_score = 0
        min_users_score = 100
        
        for horce_id in data[race_id].keys():
            if not horce_id in users_score_data[race_id]:
                continue
            
            scores = {}
            ex_dict = {}
            p_data = rank_model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )
            score = p_data[0]
            score = kernel_data["model"].score_samples( np.array( [ [ p_data[0] - kernel_data["max_score"] ] ] ) )[0]
            all_score += score
            ex_dict["score"] = math.exp( score )
            ex_dict["users_score"] = 0
            ex_dict["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_dict["odds"] = data[race_id][horce_id]["answer"]["odds"]
            ex_dict["popular"] = data[race_id][horce_id]["answer"]["popular"]
            ex_dict["horce_num"] = data[race_id][horce_id]["answer"]["horce_num"]
            #ex_dict["win_rate"] = data[race_id][horce_id]["answer"]["popular_win_rate"]
            ex_dict["horce_id"] = horce_id
            ex_dict["ex_score"] = 0

            for k in users_score_data[race_id][horce_id]:
                ex_dict["users_score"] += users_score_data[race_id][horce_id][k]

            min_users_score = min( min_users_score, ex_dict["users_score"] )
            horce_list.append( ex_dict )

        if len( horce_list ) < 5 or len( horce_list ) > 11:
        #if len( horce_list ) < 5:
            continue

        sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )
        score_rate = 1
        popular_rate = 0.1

        if all_score == 0:
            continue

        #min_users_score -= 1
        for i in range( 0, len( sort_result ) ):
            #sort_result[i]["users_score"] -= min_users_score
            sort_result[i]["ex_score"] = sort_result[i]["score"]# * sort_result[i]["users_score"]
            
        #for i in range( 0, len( sort_result ) ):
        #    print( sort_result[i]["ex_score"], sort_result[i]["score"], sort_result[i]["users_score"] )

        #print( "" )
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

        odds_list = []
        bet_candidate = []
        sum_odds = 0
        #sort_result = sorted( sort_result, key=lambda x:x["ex_score"], reverse = True )
        users_sort_result = sorted( sort_result, key=lambda x:x["users_score"], reverse = True )
        rank_sort_result = sorted( sort_result, key=lambda x:x["score"], reverse = True )
        all_ex_score = 0
        base_horce_num_list = [ sort_result[0]["horce_num"], sort_result[1]["horce_num"] ]
        #base_horce_num_list = [ sort_result[0]["horce_num"] ]
        check_formation_count = [ 3, 2 ]
        
        for i in range( 0, len( check_formation_count ) ):
            rank_1 = sort_result[i]["rank"]
            horce_num_1 = sort_result[i]["horce_num"]
            ex_score_1 = sort_result[i]["ex_score"]
            formation_count = 0

            for r in range( 0, len( users_sort_result ) ):
                if formation_count == check_formation_count[i]:
                    break
                
                rank_2 = users_sort_result[r]["rank"]
                horce_num_2 = users_sort_result[r]["horce_num"]

                if horce_num_2 in base_horce_num_list:
                    continue

                users_score = users_sort_result[r]["users_score"]

                #if users_score < 6:
                #    continue
                
                ex_score_2 = users_sort_result[r]["ex_score"]
                wide_odds = wide_odds_get( horce_num_1, horce_num_2 )

                if len( wide_odds ) == 0:
                    continue

                sum_odds += wide_odds["min"]
                bet_candidate.append( { "horce_num": [ horce_num_1, horce_num_2 ], \
                                       "rank": [ rank_1, rank_2 ], \
                                       "wide_odds": wide_odds["min"], \
                                       "bet_count": 5,
                                       "ex_score": ex_score_1 + ex_score_2 } )
                all_ex_score += ( ex_score_2 + ex_score_1 )
                formation_count += 1
        
        ex_score_list = []

        if len( bet_candidate ) < 0:
            continue

        #if 20 < all_ex_score and all_ex_score < 60:
        #    continue

        for i in range( 0, len( bet_candidate ) ):
            rate = 0

            for partern in partern_list:
                if bet_candidate[i]["horce_num"][0] in partern["horce_num"] and \
                  bet_candidate[i]["horce_num"][1] in partern["horce_num"]:
                    rate += partern["score"]

            ex_score_list.append( rate * bet_candidate[i]["wide_odds"] )
            #ex_score_list.append( bet_candidate[""])

        #print( sum( ex_score_list ) )
        ex_score_key = int( sum( ex_score_list ) )

        #if 10 < ex_score_key:
        #    continue

        c = 10
        #c = min( ( have_money * 0.01 ) / 3, 20 )
        
        #for i in range( 0, len( bet_candidate ) ):
        #    bet_candidate[i]["bet_count"] = max( int( c * ( ex_score_list[i] / all_ex_score ) ), 1 )
            #print( bet_candidate[i]["wide_odds"], bet_candidate[i]["bet_count"] )

        lib.dic_append( recovery_data, ex_score_key, { "count": 0, "recovery": 0 } )
        
        for bc in bet_candidate:
            rank_1 = bc["rank"][0]
            rank_2 = bc["rank"][1]
            horce_num_1 = bc["horce_num"][0]
            horce_num_2 = bc["horce_num"][1]
                
            buy = True
            test_result["bet_count"] += bc["bet_count"]
            have_money -= bc["bet_count"]
            recovery_data[ex_score_key]["count"] += 1
            
            if rank_1 <= 3 and rank_2 <= 3:
                try:
                    wide_odds = odds_data[race_id]["ワイド"][int(rank_1+rank_2-3)] / 100
                except:
                    continue
                    
                test_result["win"] += 1
                test_result["money"] += wide_odds * bc["bet_count"]
                have_money += wide_odds * bc["bet_count"]
                recovery_data[ex_score_key]["recovery"] += wide_odds * bc["bet_count"]
                #if wide_odds > 30:
                #    print( wide_odds )
            
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

    print( min( move_money_list ) )
    plt.plot( list( range( 0, len( move_money_list ) ) ), move_money_list )
    plt.savefig( "/Volumes/Gilgamesh/move_money.png" )
    key_list = list( recovery_data.keys() )
    key_list = sorted( key_list )

    #for k in key_list:
    #    count = recovery_data[k]["count"]
    #    recovery = recovery_data[k]["recovery"] / recovery_data[k]["count"]
    #    print( "{}: {} {}".format( k, recovery, count ) )
