import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import sekitoba_library as lib
import sekitoba_data_manage as dm

from simulation import bet_select

def softmax( data ):
    result = []
    sum_data = 0
    value_max = max( data )

    for i in range( 0, len( data ) ):
        sum_data += math.exp( data[i] - value_max )

    for i in range( 0, len( data ) ):
        result.append( math.exp( data[i] - value_max ) / sum_data )

    return result

def main( model, data ):
    recovery_rate = 0
    test = {}
    test_result = { "count": 0, "money": 0, "win": 0 }
    N = 20
    n = 5
    money = 50000
    ave_score = 0
    win_score = 0
    lose_score = 0
    
    for race_id in tqdm( data.keys() ):
        horce_list = []
        score_list = []
        
        for horce_id in data[race_id].keys():
            p_data = model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )
            ex_value = {}
            score = p_data[0] * -1
            ex_value["score"] = score
            ex_value["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_value["odds"] = data[race_id][horce_id]["answer"]["odds"]
            score_list.append( score )
            horce_list.append( ex_value )

        score_list = softmax( score_list )

        for i in range( 0, len( score_list ) ):
            horce_list[i]["score"] = score_list[i]
        
        sort_result = sorted( horce_list, key=lambda x:x["score"], reverse = True )
        max_rate = 0
        
        rate_list = []
        odds_list = []

        for i in range( 0, n ):
            rate_list.append( horce_list[i]["score"] )
            odds_list.append( horce_list[i]["odds"] )

        bet_list = bet_select.main( rate_list, odds_list, N )

        for i in range( 0, n ):
            bet_horce = sort_result[i]
            test_result["count"] += bet_list[i]
        
            if bet_horce["rank"] == 1:
                #recovery_rate += bet_horce["odds"] * bet_list[i]
                #test_result["win"] += 1
                test_result["money"] += bet_horce["odds"] * bet_list[i]
                #lib.log.write( "odds:" + str( bet_horce["odds"] ) + " score:" + str( max( score_list ) ) )

    recovery_rate = test_result["money"] / test_result["count"]
    recovery_rate *= 100

    print( "回収率{}%".format( recovery_rate ) )
    #print( "勝率{}%".format( win_rate ) )
    print( "賭けた回数{}回".format( test_result["count"] ) )
    #lib.log.write( "回収率{}%".format( recovery_rate ) )
    #lib.log.write( "勝率{}%".format( win_rate ) )
    #lib.log.write( "賭けた回数{}回".format( test_result["count"] ) )




