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
    recovery_rate = 0
    raceCount = 0
    count = 0
    win_rate = 0
    money = 3000
    bet_money = 60#int( money / 200 )
    money_list = []
    testDict = {}

    wide_odds_data = dm.pickle_load( "wide_odds_data.pickle" )
    triplet_odds_data = dm.pickle_load( "triplet_odds_data.pickle" )
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

        if not race_id in triplet_odds_data:
            continue
        
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

        if not race_id in wide_odds_data:
            continue

        for i in range( 0, len( score_list ) ):
            horce_list[i]["score"] = score_list[i]

        selectHorce = SelectHorce( wide_odds_data[race_id], triplet_odds_data[race_id], horce_list )
        betHorceList, bestScore = selectHorce.selectHorce()

        #if int( bestScore * 20 ) <= 10:
        #    continue
        
        #key = int( bestScore * 20 )
        #lib.dicAppend( testDict, key, { "count": 0, "recovery": 0 } )
        score = 0

        for betHorce in betHorceList:
            score += betHorce["score"]

        #if score > 0.9:
        #    continue
        
        getMoney, oddsList = selectHorce.bet_check( betHorceList, current_odds )

        if not getMoney == 0:
            win_rate += 1

        #testDict[key]["count"] += selectHorce.betCount
        #testDict[key]["recovery"] += getMoney
        recovery_rate += getMoney
        count += selectHorce.betCount
        raceCount += 1
        money -= selectHorce.betCount
        money += getMoney
        money_list.append( money )
    
    recovery_rate = ( recovery_rate / count ) * 100
    win_rate = ( win_rate / raceCount ) * 100
    
    if show:
        print( "" )
        print( "選択数:{}".format( count ) )
        print( "回収率:{}%".format( recovery_rate ) )
        print( "勝率:{}%".format( win_rate ) )
        print( "得た金額:{}円".format( int( money * 100 ) ) )
        print( "賭けたレース数:{}回".format( raceCount ) )

    #for k in sorted( list( testDict.keys() ) ):
    #    recovery = testDict[k]["recovery"] / testDict[k]["count"]
    #    print( k, round( recovery * 100, 4 ), testDict[k]["count"] )
