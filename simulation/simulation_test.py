import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import SekitobaLibrary as lib
import SekitobaDataManage as dm

from analyze.odds_cluster import OddsCluster

def standardization( data ):
    result = []
    ave = sum( data ) / len( data )
    conv = 0

    for d in data:
        conv = math.pow( d - ave, 2 )

    conv /= len( data )
    conv = math.sqrt( conv )

    for d in data:
        result.append( ( d - ave ) / conv )

    return result

def softmax( data ):
    result = []
    sum_data = 0

    for i in range( 0, len( data ) ):
        sum_data += math.exp( data[i] )

    for i in range( 0, len( data ) ):
        result.append( math.exp( data[i] ) / sum_data )

    return result

def score_add( score_data ):
    score_keys = list( score_data.keys() )
    result = [ 0 ] * len( score_data[score_keys[0]] )
    rate_data = { "rank": 1, "one": 0, "two": 0, "three": 1 }

    for k in score_keys:
        score_data[k] = softmax( score_data[k] )

    for k in score_keys:
        for i in range( 0, len( score_data[k] ) ):
            result[i] += score_data[k][i] * rate_data[k]

    return result
    #return softmax( result )

def main( test_years = lib.simu_years, show = True ):
    data = dm.pickle_load( lib.name.simu_name() )
    model_list = dm.pickle_load( lib.name.model_name() )
    recovery_rate = 0
    index_data = [ 3, 100, 6, 8, 10, 10 ]
    test = {}
    test_result = { "count": 0, "bet_count": 0, "one_money": 0, "three_money": 0, "one_win": 0, "three_win": 0, "three_money": 0 }
    money = 3000
    bet_money = 60#int( money / 200 )
    money_list = []
    ave_score = 0
    win_score = 0
    lose_score = 0
    mdcd_score = 0
    mdcd_count = 0
    recovery_check = {}
    t = 1

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

        horce_list = []
        score_list = []
        instance_list = []
        current_odds = odds_data[race_id]

        for horce_id in data[race_id].keys():
            scores = {}
            ex_value = {}
            p_score = 0

            #if data[race_id][horce_id]["answer"]["new"]:
            #    break

            for model in model_list:
                p_score += model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )[0]
                
            score_list.append( p_score )
            ex_value["score"] = p_score
            ex_value["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_value["odds"] = data[race_id][horce_id]["answer"]["odds"]
            ex_value["popular"] = data[race_id][horce_id]["answer"]["popular"]
            ex_value["horce_id"] = horce_id
            horce_list.append( ex_value )

        if len( horce_list ) < 5:
            continue

        cc = 0
        oddsCluster = OddsCluster( horce_list )
        oddsCluster.clustering()

        for k in oddsCluster.cluster.keys():
            if oddsCluster.cluster[k] == 1:
                cc += 1
            
        min_score = min( score_list )
        
        #for i in range( 0, len( score_list ) ):
        #    score_list[i] -= min_score
        #    score_list[i] = math.pow( score_list[i], 2 ) / ( 1 + i * 0.2 )

        #all_score = sum( score_list )

        #for i in range( 0, len( score_list ) ):
        #    score_list[i] /= all_score

        #score_list = softmax( score_list )

        #for i in range( 0, len( score_list ) ):
        #    horce_list[i]["score"] = score_list[i]

        sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )

        for i in range( 0, len( sort_result ) ):
            rank = sort_result[i]["rank"]
            score = sort_result[i]["score"]
            mdcd_score += math.pow( rank - ( i + 1 ), 2 )
            mdcd_count += 1

        t = len( index_data )
        
        for i in range( 0, min( len( sort_result ), t ) ):
            bet_horce = sort_result[i]
            odds = bet_horce["odds"]
            horce_id = bet_horce["horce_id"]
            rank = bet_horce["rank"]
            score = bet_horce["score"]
            popular = bet_horce["popular"]
            ex_value = score * odds
            line_ex = 1 + i / 0.9
            
            #if 4 <= cc:
            #    continue

            #if not oddsCluster.cluster[horce_id] == 1:
            #    continue

            #if popular > 2:
            #    continue

            #if popular < index_data[i]:
            #    continue

            #if odds > 60:
            #    continue
            #if ex_value < 1.3:
            #    continue

            lib.dicAppend( test, i, {} )
            lib.dicAppend( test[i], popular, { "data": 0, "count": 0 } )
            test[i][popular]["count"] += 1
            bc = 1
            #bc = int( 1 + min( ( ex_value - 1 ) * 10, 4 ) )
            test_result["bet_count"] += bc
            test_result["count"] += 1
            money -= int( bc * bet_money )

            if rank == 1:
                test_result["one_win"] += 1
                test_result["one_money"] += odds * bc
                test[i][popular]["data"] += odds
                money += odds * bc * bet_money

            if rank <= min( 3, len( current_odds["複勝"] ) ):
                rank_index = int( bet_horce["rank"] - 1 )
                three_odds = current_odds["複勝"][rank_index] / 100
                test_result["three_win"] += 1
                test_result["three_money"] += three_odds# * bet_money

        money_list.append( money )
    
    one_recovery_rate = ( test_result["one_money"] / test_result["bet_count"] ) * 100 
    three_recovery_rate = ( test_result["three_money"] / test_result["bet_count"] ) * 100
    one_win_rate = ( test_result["one_win"] / test_result["count"] ) * 100
    three_win_rate = ( test_result["three_win"] / test_result["count"] ) * 100
    
    for i in test.keys():
        p_list = sorted( list( test[i].keys() ) )
        for p in p_list:
            test[i][p]["data"] /= test[i][p]["count"]
            print( "index:{} popular:{} recovery:{} count:{}".format( i, p, test[i][p]["data"] * 100, test[i][p]["count"] ) )

    if show:
        print( "" )
        print( "選択数:{}".format( t ) )
        print( "単勝 回収率{}%".format( one_recovery_rate ) )
        print( "複勝 回収率{}%".format( three_recovery_rate ) )
        print( "単勝 勝率{}%".format( one_win_rate ) )
        print( "複勝 勝率{}%".format( three_win_rate ) )
        print( "賭けたレース数{}回".format( test_result["count"] ) )
        print( "賭けた金額{}".format( test_result["bet_count"] ) )
        print( "金額:{}".format( money ) )
        print( "最低金額:{}".format( min( money_list ) ) )
        print( "mdcd:{}".format( round( math.sqrt( mdcd_score / mdcd_count ), 4 ) ) )
