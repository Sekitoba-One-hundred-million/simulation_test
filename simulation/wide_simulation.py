import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import sekitoba_library as lib
import sekitoba_data_manage as dm

def bet_select( horce_list, baren_odds_data, wide_odds_data ):
    bet_patern_list = []
    rank_patern_list = []
    
    for i in range( 0, len( horce_list ) ):
        score1 = horce_list[i]["score"]
        rank1 = horce_list[i]["rank"]
        users_score1 = horce_list[i]["users_score"]
        horce_num1 = horce_list[i]["horce_num"]
        
        for r in range( 0, len( horce_list ) ):
            score2 = horce_list[r]["score"]
            rank2 = horce_list[r]["rank"]
            users_score2 = horce_list[r]["users_score"]
            horce_num2 = horce_list[r]["horce_num"]

            if i == r:
                continue

            for t in range( 0, len( horce_list ) ):
                horce_num3 = horce_list[t]["horce_num"]
                
                if i == t or r == t:
                    continue

                rank_patern_list.append( [ horce_num1, horce_num2, horce_num3 ] )

            if r <= i:
                continue
            
            min_horce_num = int( min( horce_num1, horce_num2 ) )
            max_horce_num = int( max( horce_num1, horce_num2 ) )
            wide_odds = -1
            baren_odds = -1
            
            try:
                baren_odds = baren_odds_data[min_horce_num][max_horce_num]
                wide_odds = wide_odds_data[min_horce_num][max_horce_num]["min"]
            except:
                continue

            bet_patern_list.append( { "kind": "wide",
                                     "bet_count": 0,
                                     "score": ( score1, score2 ),
                                     "rank": ( rank1, rank2 ),
                                     "users_score": ( users_score1, users_score2 ),
                                     "horce_num": ( min_horce_num, max_horce_num ),
                                     "odds": wide_odds } )

            bet_patern_list.append( { "kind": "baren",
                                     "bet_count": 0,
                                     "score": ( score1, score2 ),
                                     "rank": ( rank1, rank2 ),
                                     "users_score": ( users_score1, users_score2 ),
                                     "horce_num": ( min_horce_num, max_horce_num ),
                                     "odds": baren_odds } )

    bet_count = 30
    
    for count in range( 0, bet_count ):
        best_score = -100000
        best_index = -1
        
        for i in range( 0, len( bet_patern_list ) ):
            score = 0
            bet_patern_list[i]["bet_count"] += 1

            for rank_patern in rank_patern_list:
                check_rank = -1
                
                if bet_patern_list[i]["kind"] == "wide":
                    check_rank = 3
                elif bet_patern_list[i]["kind"] == "baren":
                    check_rank = 2

                instance_score = 0
                
                if bet_patern_list[i]["horce_num"][0] in rank_patern[0:check_rank] and \
                  bet_patern_list[i]["horce_num"][1] in rank_patern[0:check_rank]:
                    instance_score += ( bet_patern_list[i]["score"][0] + bet_patern_list[i]["score"][1] ) * bet_patern_list[i]["odds"]
                    instance_score *= bet_patern_list[i]["bet_count"]
                    instance_score *= math.pow( 0.6, bet_patern_list[i]["bet_count"] )
                else:
                    instance_score -= ( bet_patern_list[i]["score"][0] + bet_patern_list[i]["score"][1] ) * bet_patern_list[i]["bet_count"]

                score += instance_score

            if best_score < score:
                best_index = i
                best_score = score

            bet_patern_list[i]["bet_count"] -= 1

        bet_patern_list[best_index]["bet_count"] += 1
        #print( bet_patern_list[best_index] )

    return bet_patern_list

def main( rank_model, data ):
    have_money = 3000
    check_money = 3000
    max_have_money = have_money
    move_money_list = []
    recovery_data = {}
    test_result = { "count": 0, "bet_count": 0, "money": 0, "win": 0 }
    popular_kind_win_rate_data = dm.pickle_load( "popular_kind_win_rate_data.pickle" )
    baren_odds_data = dm.pickle_load( "baren_odds_data.pickle" )
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

        max_have_money = max( have_money, max_have_money )
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

        pattern_list = []

        for i in range( 0, len( horce_list ) ):
            for r in range( i + 1, len( horce_list ) ):
                for t in range( r + 1, len( horce_list ) ):
                    pattern_list.append( [ i, r, t ] )

        buy = False
        bet_count = 1#int( max_have_money / check_money ) * 10
        #if all_horce_num < 9:
        #    bet_count *= 2
        bet_candidate = bet_select( horce_list, baren_odds_data[race_id], wide_odds_data[race_id] )
        #users_sort_result = sorted( horce_list, key=lambda x:x["users_score"], reverse = True )
        #rank_sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )
        #base_horce_num_list = [ rank_sort_result[0]["horce_num"], rank_sort_result[1]["horce_num"] ]
        #base_horce_num_list = [ rank_sort_result[0]["horce_num"] ]
        #check_formation_count = [ 2, 1 ]
        #check_formation_count = [ 1 ]
        
        for bc in bet_candidate:
            if bc["bet_count"] == 0:
                continue

            kind = bc["kind"]
            rank_1 = bc["rank"][0]
            rank_2 = bc["rank"][1]
            horce_num_1 = bc["horce_num"][0]
            horce_num_2 = bc["horce_num"][1]
                
            buy = True

            test_result["bet_count"] += bc["bet_count"]
            have_money -= bc["bet_count"]
            #lib.dic_append( recovery_data, rk, { "recovery": 0, "count": 0 } )
            #recovery_data[rk]["count"] += bc["bet_count"] 

            if kind ==  "wide":
                if rank_1 <= 3 and rank_2 <= 3:
                    try:
                        wide_odds = odds_data[race_id]["ワイド"][int(rank_1+rank_2-3)] / 100
                    except:
                        continue

                    test_result["win"] += 1
                    test_result["money"] += wide_odds * bc["bet_count"]
                    have_money += wide_odds * bc["bet_count"]
                    print( "wide", wide_odds, bc["bet_count"] )
            elif kind == "baren":
                if rank_1 <= 3 and rank_2 <= 3:
                    try:
                        baren_odds = odds_data[race_id]["馬連"] / 100
                    except:
                        continue

                    test_result["win"] += 1
                    test_result["money"] += baren_odds * bc["bet_count"]
                    have_money += baren_odds * bc["bet_count"]
                    print( "baren", baren_odds, bc["bet_count"] )
            
        if buy:
            test_result["count"] += 1
            move_money_list.append( have_money )

        print( have_money, ( test_result["money"] / test_result["bet_count"] ) * 100 )

    recovery_rate = ( test_result["money"] / test_result["bet_count"] ) * 100
    win_rate = ( test_result["win"] / test_result["count"] ) * 100
    
    print( "" )
    print( "回収率{}%".format( recovery_rate ) )
    print( "勝率{}%".format( win_rate ) )
    print( "賭けた回数{}回".format( test_result["bet_count"] ) )
    print( "賭けたレース数{}回".format( test_result["count"] ) )
    print( "獲得金額{}円".format( int( have_money ) ) )

    print( min( move_money_list ) )    
    plt.plot( list( range( 0, len( move_money_list ) ) ), move_money_list )
    plt.savefig( "/Volumes/Gilgamesh/move_money.png" )

    #key_list = sorted( list( recovery_data.keys() ) )

    #for k in key_list:
    #    recovery = recovery_data[k]["recovery"] / recovery_data[k]["count"]
    #    print( k, recovery, recovery_data[k]["count"] )
