import math
import json
import torch
import random
import optuna
import numpy as np
from tqdm import tqdm
from statistics import stdev
import matplotlib.pyplot as plt

import sekitoba_library as lib
import sekitoba_data_manage as dm

rank_model = dm.pickle_load( "rank_model.pickle" )
data = dm.pickle_load( "rank_simu_data.pickle" )

rank_score_list = []
rank_score_data = {}

for race_id in data.keys():
    rank_score_data[race_id] = {}
    
    for horce_id in data[race_id].keys():
        rank_score_data[race_id][horce_id] = rank_model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )[0]

def objective( trial ):
    score_rate = trial.suggest_float( "score_rate", 0, 10 )
    stand_score_rate = trial.suggest_float( "stand_score_rate", 0, 10 )
    softmax_score_rate = trial.suggest_float( "softmax_score_rate", 0, 10 )
    rate_score_rate = trial.suggest_float( "rate_score_rate", 0, 5 )
    money = simulation( score_rate, stand_score_rate, softmax_score_rate, rate_score_rate )

    return money * -1
    
def standardization( data ):
    result = []
    ave = sum( data ) / len( data )
    std = stdev( data )

    for i in range( 0, len( data ) ):
        result.append( ( data[i] - ave ) / std )

    return result

def simulation( score_rate, stand_score_rate, softmax_score_rate, rate_score_rate ):
    test_result = { "count": 0, "bet_count": 0, "one_money": 0, "one_win": 0 }
    
    for race_id in data.keys():
        year = race_id[0:4]
        number = race_id[-2:]
        
        if not year in lib.test_years:
            continue
        
        horce_list = []
        score_list = []
        
        for horce_id in data[race_id].keys():
            scores = {}
            ex_value = {}
            score = rank_score_data[race_id][horce_id]
            ex_value["score"] = score
            ex_value["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_value["odds"] = data[race_id][horce_id]["answer"]["odds"]
            ex_value["popular"] = data[race_id][horce_id]["answer"]["popular"]
            ex_value["horce_num"] = data[race_id][horce_id]["answer"]["horce_num"]
            ex_value["horce_id"] = horce_id
            horce_list.append( ex_value )
            score_list.append( score )

        if len( horce_list ) < 3:
            continue

        stand_score_list = standardization( score_list )
        softmax_score_list = lib.softmax( score_list )
        rate_score_list = []

        for i in range( 0, len( horce_list ) ):
            horce_list[i]["stand_score"] = stand_score_list[i]
            horce_list[i]["softmax_score"] = softmax_score_list[i]
            rate_score_list.append( horce_list[i]["score"] * score_rate + horce_list[i]["stand_score"] * stand_score_rate + horce_list[i]["softmax_score"] * softmax_score_rate )

        rate_score_list = lib.softmax( rate_score_list )

        for i in range( 0, len( horce_list ) ):
            horce_list[i]["rate_score"] = rate_score_list[i]
        
        sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )
        use_horce_num = []
        bc = 1
        buy = False
        
        for i in range( 0, len( sort_result ) ):
            score = sort_result[i]["score"]
            stand_score = sort_result[i]["stand_score"]
            softmax_score = sort_result[i]["softmax_score"]
            odds = sort_result[i]["odds"]
            rank = sort_result[i]["rank"]
            
            #rate = ( score / 15 ) + ( stand_score / 15 ) + ( softmax_score / 14 )
            rate = sort_result[i]["rate_score"] / ( ( i + 1 ) * rate_score_rate )
            ex = rate * odds

            if ex < 1:
                continue
            
            bc = 1#int( score * odds )
            buy = True
            test_result["bet_count"] += bc

            if rank == 1:
                test_result["one_win"] += 1
                test_result["one_money"] += odds * bc

        if buy:
            test_result["count"] += 1
                                
    one_recovery_rate = ( test_result["one_money"] / test_result["bet_count"] ) * 100 
    one_win_rate = ( test_result["one_win"] / test_result["count"] ) * 100
    
    #print( "" )
    #print( "選択数:{}".format( t ) )
    print( "単勝 回収率{}%".format( one_recovery_rate ) )
    print( "単勝 勝率{}%".format( one_win_rate ) )
    print( "賭けた回数{}回".format( test_result["count"] ) )

    money = ( one_recovery_rate - 100 ) * test_result["count"]
    return money

def main():
    study = optuna.create_study()
    study.optimize(objective, n_trials=200)
    print( study.best_params )

    f = open( "best_params.json", "w" )
    json.dump( study.best_params, f )
    f.close()

    simulation( study.best_params["score_rate"], \
               study.best_params["stand_score_rate"], \
               study.best_params["softmax_score_rate"], \
               study.best_params["rate_score_rate"] )
