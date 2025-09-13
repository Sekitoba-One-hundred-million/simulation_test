import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import SekitobaLibrary as lib
from SekitobaLibrary import ManageRecoveryScore
import SekitobaDataManage as dm

def recovery_score_create( cluster_data, data, c ):
    score = 0
    nama_list = cluster_data["name"]
    data_type = cluster_data["type"]
    cluster_list = cluster_data["cluster"]


    for cluster in cluster_list:
        manage_recovery_score = ManageRecoveryScore( {},
                                                     data_name_list = nama_list,
                                                     data_type = data_type,
                                                     cd = cluster )

        for name in cluster.keys():
            value = data[name][c]
            add_score = manage_recovery_score.check_score( value, name )

            if add_score == lib.escapeValue:
                continue

            score += add_score

    return score / len( cluster_data )

def change_win_rate( horce_data_list ):
    score_list = []
    odds_list = []
    
    for horce_data in horce_data_list:
        score_list.append( horce_data["rank_score"] )
        odds_list.append( horce_data["odds"] )
        
    min_score = min( score_list )
    all_score = 0

    for i in range( 0, len( score_list ) ):
        score_list[i] = max( score_list[i] - min_score * 1.1, 0 )
        score_list[i] *= ( 2 - ( i / 10 ) )
        score_list[i] = math.pow( score_list[i], 2 )
        all_score += score_list[i]

    for i in range( 0, len( score_list ) ):
        score_list[i] = ( score_list[i] / all_score )
        horce_data_list[i]["rate"] = score_list[i]

    #print( "rate:{}".format( score_list ) )
    #print( "odds:{}".format( odds_list ) )

def main( test_years = lib.simu_years, show = True ):
    recovery_rate = 0
    recovery_cluster_data = dm.pickle_load( "recovery_cluster_data.pickle" )
    recovery_simu_data = dm.pickle_load( "recovery_simu_data.pickle" )
    quinella_odds_data = dm.pickle_load( "quinella_odds_data.pickle" )
    manage_recovery_score = ManageRecoveryScore( {},
                                                 data_name_list = recovery_cluster_data["name"],
                                                 data_type = recovery_cluster_data["type"],
                                                 cd = recovery_cluster_data["cluster"] )
    data = dm.pickle_load( lib.name.simu_name() )
    model_list = dm.pickle_load( lib.name.model_name() )
    #index_data = [ [ 3, 5 ], [ 6, 7, 8 ], [ 7, 8 ] ]
    index_data = [ [ 3, 5 ], [ 6, 7, 8 ] ]
    test = {}
    test_result = { "count": 0, "bet_count": 0, "one_money": 0, "three_money": 0, "one_win": 0, "three_win": 0, "three_money": 0 }
    money = 2000
    bet_money = 10#int( money / 200 )
    money_list = []
    ave_score = 0
    win_score = 0
    lose_score = 0
    mdcd_score = 0
    mdcd_count = 0
    recovery_check = {}
    t = 1#len( index_data )

    odds_data = dm.pickle_load( "odds_data.pickle" )
    #users_score_data = dm.pickle_load( "users_score_data.pickle")
    race_id_list = list( data.keys() )
    random.shuffle( race_id_list )

    for race_id in tqdm( race_id_list ):
        year = race_id[0:4]
        race_place_num = race_id[4:6]
        number = race_id[-2:]

        if not year in test_years:
            continue

        if not race_id in quinella_odds_data:
            continue

        odds_index = 1
        horce_list = []
        score_list = []
        instance_list = []
        recovery_predict_data = {}
        current_odds = odds_data[race_id]

        predict_recovery_data = {}
        
        for horce_id in recovery_simu_data[race_id].keys():
            for name in recovery_cluster_data["name"]:
                lib.dic_append( predict_recovery_data, name, [] )
                data_index = recovery_cluster_data["name"].index( name )
                predict_recovery_data[name].append( recovery_simu_data[race_id][horce_id][odds_index]["data"][data_index] )

        for name in recovery_cluster_data["name"]:
            if recovery_cluster_data["type"][name] == float:
                predict_recovery_data[name] = lib.standardization( predict_recovery_data[name], abort = [ lib.escapeValue ] )

        for horce_id in data[race_id].keys():
            scores = {}
            ex_value = {}
            p_score = 0

            if data[race_id][horce_id][odds_index]["answer"]["new"]:
                break

            for model in model_list:
                p_score += model.predict( np.array( [ data[race_id][horce_id][odds_index]["data"] ] ) )[0]
                
            score_list.append( p_score )
            ex_value["score"] = 0
            ex_value["rank"] = data[race_id][horce_id][odds_index]["answer"]["rank"]
            ex_value["odds"] = data[race_id][horce_id][odds_index]["answer"]["odds"]
            ex_value["popular"] = data[race_id][horce_id][odds_index]["answer"]["popular"]
            ex_value["horce_num"] = data[race_id][horce_id][odds_index]["answer"]["horce_num"]
            ex_value["horce_id"] = horce_id
            ex_value["recovery"] = recovery_score_create( recovery_cluster_data,
                                                          predict_recovery_data,
                                                          len( horce_list ) )
            ex_value["rank_score"] = p_score
            ex_value["score"] = p_score
            horce_list.append( ex_value )

        if len( horce_list ) < 5:
            continue

        min_score = min( score_list )
        
        horce_list = sorted( horce_list, key=lambda x:x["recovery"], reverse = True )

        for i in range( 0, len( horce_list ) ):
            horce_list[i]["recovery"] = int( i + 1 )

        sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )
        change_win_rate( sort_result )

        for i in range( 0, len( sort_result ) ):
            rank = sort_result[i]["rank"]
            mdcd_score += math.pow( rank - ( i + 1 ), 2 )
            mdcd_count += 1

        for i in range( 0, min( len( sort_result ), t ) ):
            bet_horce = sort_result[i]
            odds = bet_horce["odds"]
            horce_id = bet_horce["horce_id"]
            rank = bet_horce["rank"]
            score = bet_horce["score"]
            popular = int( bet_horce["popular"] )
            ex_value = bet_horce["rate"] * odds
            recovery_score = bet_horce["recovery"]

            if ex_value < 1:
                continue

            if 5 < recovery_score:
                continue

            base_horce_num = int( bet_horce["horce_num"] )
            quinella_bet_list = []

            for r in range( 1, len( sort_result ) ):
                quinella_horce = sort_result[r]
                quinella_horce_num = int( quinella_horce["horce_num"] )
                min_horce_num = min( base_horce_num, quinella_horce_num )
                max_horce_num = max( base_horce_num, quinella_horce_num )
                quinella_odds = quinella_odds_data[race_id][min_horce_num][max_horce_num]

                if quinella_horce["recovery"] < 5:
                    quinella_bet_list.append( { "odds": quinella_odds, "rank": quinella_horce["rank"] } )
                
            bc = 1
            test_result["bet_count"] += bc * len( quinella_bet_list )
            test_result["count"] += 1
            money -= int( bc * bet_money * len( quinella_bet_list ) )

            if 2 < rank:
                continue
            
            for r in range( 0, len( quinella_bet_list ) ):
                if quinella_bet_list[r]["rank"] < 3:
                    odds = quinella_bet_list[r]["odds"]
                    test_result["one_win"] += 1
                    test_result["one_money"] += odds * bc
                    money += odds * bc * bet_money

        money_list.append( money )
    
    one_recovery_rate = ( test_result["one_money"] / test_result["bet_count"] ) * 100
    one_win_rate = ( test_result["one_win"] / test_result["count"] ) * 100 * t
    
    if show:
        print( "" )
        print( "選択数:{}".format( t ) )
        print( "回収率{}%".format( one_recovery_rate ) )
        print( "勝率{}%".format( one_win_rate ) )
        print( "賭けたレース数{}回".format( test_result["count"] ) )
        print( "賭けた金額{}".format( test_result["bet_count"] ) )
        print( "金額:{}".format( money ) )
        print( "最低金額:{}".format( min( money_list ) ) )
        print( "mdcd:{}".format( round( mdcd_score / mdcd_count, 4 ) ) )
