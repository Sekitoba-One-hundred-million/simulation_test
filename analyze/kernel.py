import math
import torch
import random
import optuna
import numpy as np
from tqdm import tqdm
from statistics import stdev
import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity

import sekitoba_library as lib
import sekitoba_data_manage as dm

#max_limit_score = 40

def simulation( rank_model, data ):
    rank_score_data = {}

    for race_id in data.keys():
        rank_score_data[race_id] = {}
        for horce_id in data[race_id].keys():
            rank_score_data[race_id][horce_id] = rank_model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )[0]

    rate_check = { "one": {}, "two": {}, "three": {} }
            
    for race_id in data.keys():
        year = race_id[0:4]
        
        if not year in lib.test_years:
            continue
        
        horce_list = []
        score_list = []
        
        for horce_id in data[race_id].keys():
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

        #stand_score_list = lib.standardization( score_list )
        softmax_score_list = lib.softmax( score_list )
        horce_list = sorted( horce_list, key = lambda x:x["score"], reverse = True )
        
        for i in range( 0, len( horce_list ) ):
            #score = ( horce_list[i]["score"] + stand_score_list[i] + softmax_score_list[i] ) * 0.3
            score = horce_list[i]["score"] # / ( i + 1 )
            rank = horce_list[i]["rank"]
            #score = min( int( score * 10 ), max_limit_score )
            score = int( score * 10 )
            #print( score )
            lib.dic_append( rate_check["one"], score, { "count": 0, "rate": 0 } )
            lib.dic_append( rate_check["two"], score, { "count": 0, "rate": 0 } )
            lib.dic_append( rate_check["three"], score, { "count": 0, "rate": 0 } )

            rate_check["one"][score]["count"] += 1
            rate_check["two"][score]["count"] += 1
            rate_check["three"][score]["count"] += 1

            if rank == 1:
                rate_check["one"][score]["rate"] += 1
                rate_check["two"][score]["rate"] += 1
                rate_check["three"][score]["rate"] += 1
            elif rank == 1:
                rate_check["two"][score]["rate"] += 1
                rate_check["three"][score]["rate"] += 1
            elif rank == 3:
                rate_check["three"][score]["rate"] += 1

    result = {}
    for kind in rate_check.keys():
        result[kind] = {}
        
        for score in rate_check[kind].keys():
            result[kind][score] = rate_check[kind][score]["rate"] / rate_check[kind][score]["count"]

    
    #kind = "one"
    #score_key = sorted( list( rate_check[kind].keys() ) )
    
    #for score in score_key:
    #    plt.bar( score, result[kind][score] )
    #    print( score, result[kind][score], rate_check[kind][score]["count"] )

    #plt.show()

    return result
            
def main( rank_model, data ):
    rate_data = simulation( rank_model, data )

    kernel_data = {}

    for kind in rate_data.keys():
        kernel_data[kind] = []
        score_list = sorted( list( rate_data[kind].keys() ) )
        rate = 0
        max_limit_score = max( score_list )
        
        for score in score_list:
            rate = rate_data[kind][score]

            for i in range( 0, int( rate * 100 ) ):
                s = score - max_limit_score
                kernel_data[kind].append( s / 10 )
                kernel_data[kind].append( ( s * -1 ) / 10 )
            
            #if kind == "one":
            #    print( rate, score )

    kind = "three"
    kernel_data[kind] = np.array( kernel_data[kind] ).reshape( len( kernel_data[kind] ), 1 )
    kde = KernelDensity(kernel='gaussian', bandwidth=0.25).fit( kernel_data[kind] )

    score_list = []

    for score in rate_data[kind].keys():
        if max_limit_score < score:
            continue
        
        score_list.append( score / 10 )

    score_list = np.array( sorted( score_list ) ).reshape( len( rate_data[kind] ), 1 )
    log_density = kde.score_samples( score_list )
    #plt.plot( score_list, np.exp( log_density ) )
    #plt.show()

    return { "model": kde, "max_score": max_limit_score / 10 }
