import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import SekitobaLibrary as lib
import SekitobaDataManage as dm

from analyze.odds_cluster import OddsCluster
from analyze.select_horce import SelectHorce

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
    index_data = [ [ 3, 4, 5 ], [ 7, 8 ] ]
    moneyList = []
    recovery_rate = 0
    raceCount = 0
    count = 0
    win_rate = 0
    money = 1000
    bet_money = 20#int( money / 200 )
    #t = 1
    t = len( index_data )

    recovery_cluster_data = dm.pickle_load( "recovery_cluster_data.pickle" )
    recovery_simu_data = dm.pickle_load( "recovery_simu_data.pickle" )
    wide_odds_data = dm.pickle_load( "wide_odds_data.pickle" )
    #triplet_odds_data = dm.pickle_load( "triplet_odds_data.pickle" )
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

        if not race_id in wide_odds_data:
            continue

        #if not race_id in triplet_odds_data:
        #    continue
        
        horce_list = []
        score_list = []
        instance_list = []
        current_odds = odds_data[race_id]

        for horce_id in data[race_id].keys():
            scores = {}
            ex_value = {}
            p_score = 0

            if data[race_id][horce_id]["answer"]["new"]:
                break

            for model in model_list:
                p_score += model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )[0]
                
            score_list.append( p_score )
            ex_value["score"] = p_score
            ex_value["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_value["odds"] = data[race_id][horce_id]["answer"]["odds"]
            ex_value["popular"] = data[race_id][horce_id]["answer"]["popular"]
            ex_value["horce_num"] = data[race_id][horce_id]["answer"]["horce_num"]
            ex_value["horce_id"] = horce_id
            horce_list.append( ex_value )

        if len( horce_list ) < 5:
            continue

        min_score = min( score_list )
        score_list = softmax( score_list )
        sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )
        
        for i in range( 0, len( score_list ) ):
            horce_list[i]["score"] = score_list[i]

        #selectHorce = SelectHorce( wide_odds_data[race_id], triplet_odds_data[race_id], horce_list )
        #betHorceList, bestScore = selectHorce.selectHorce()
        #key = int( bestScore * 20 )
        #lib.dic_append( testDict, key, { "count": 0, "recovery": 0 } )

        for i in range( 0, min( len( sort_result ), t ) ):
            bet_horce = sort_result[i]
            odds = bet_horce["odds"]
            rank = bet_horce["rank"]
            popular = bet_horce["popular"]
            horce_num = bet_horce["horce_num"]

            if not popular in index_data[i]:
                continue

            count += 1
            raceCount += 1
            bc = 1
            money -= int( bc * bet_money )

            if rank == 1:
                recovery_rate += odds
                money += odds * bc * bet_money

            for r in range( 0, min( len( sort_result ), 4 ) ):
                rank2 = sort_result[r]["rank"]
                horce_num2 = sort_result[r]["horce_num"]

                if horce_num == horce_num2:
                    continue

                count += 1
                money -= int( bc * bet_money )

                if rank <= 3 and rank2 <= 3:
                    win_rate += 1
                    min_horce_num = int( min( horce_num, horce_num2 ) )
                    max_horce_num = int( max( horce_num, horce_num2 ) )

                    try:
                        recovery_rate += wide_odds_data[race_id][min_horce_num][max_horce_num]["min"]
                        money += wide_odds_data[race_id][min_horce_num][max_horce_num]["min"] * bet_money
                    except:
                        continue

            moneyList.append( money )

    recovery_rate = ( recovery_rate / count ) * 100
    win_rate = ( win_rate / raceCount ) * 100

    if show:
        print( "" )
        print( "選択数:{}".format( count ) )
        print( "回収率:{}%".format( recovery_rate ) )
        print( "勝率:{}%".format( win_rate ) )
        print( "賭けたレース数:{}回".format( raceCount ) )
        print( "取得金額:{}円".format( money ) )
        print( "最低金額:{}円".format( min( moneyList ) ) )
