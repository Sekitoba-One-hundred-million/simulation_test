import math
import copy
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import SekitobaLibrary as lib
from SekitobaLibrary import ManageRecoveryScore
import SekitobaDataManage as dm

def create_pattern_key( horce_num_list ):
    return "{}-{}-{}".format( horce_num_list[0], horce_num_list[1], horce_num_list[2] )

def create_quinella_key( horce_num_list ):
    use_horce_num_list = sorted( horce_num_list )

    return "{}-{}".format( use_horce_num_list[0], use_horce_num_list[1] )

def create_horce_pattern( horce_list, triplet_odds_data, quinella_odds_data ):
    all_score = 0
    triplet_odds_dict = {}
    quinella_odds_dict = {}
    horce_pattern_list = {}
    
    for i in range( 0, len( horce_list ) ):
        for r in range( 0, len( horce_list ) ):
            if i == r:
                continue
            
            for t in range( 0, len( horce_list ) ):
                if i == t or r == t:
                    continue
                
                horce_num_list = [ horce_list[i]["horce_num"], \
                                   horce_list[r]["horce_num"], \
                                   horce_list[t]["horce_num"] ]
                sort_tripret_horce_num_list = sorted( horce_num_list )
                sort_quinella_horce_num_list = sorted( horce_num_list[0:2] )
                horce_score = horce_list[i]["score"] * math.pow( horce_list[r]["score"], 2 ) * math.pow( horce_list[t]["score"], 3 )
                #horce_score = math.pow( horce_score, 3 )

                triplet_odds = triplet_odds_data[sort_tripret_horce_num_list[0]][sort_tripret_horce_num_list[1]][sort_tripret_horce_num_list[2]]
                quinella_odds = quinella_odds_data[sort_quinella_horce_num_list[0]][sort_quinella_horce_num_list[1]]

                triplet_key = create_pattern_key( sort_tripret_horce_num_list )
                quinella_key = create_quinella_key( sort_quinella_horce_num_list )
                pattern_key = create_pattern_key( horce_num_list )

                lib.dic_append( triplet_odds_dict, triplet_key, { "odds": triplet_odds, "pattern": [], "kind": "triplet" } )
                lib.dic_append( quinella_odds_dict, quinella_key, { "odds": quinella_odds, "pattern": [], "kind": "quinella" } )
                quinella_odds_dict[quinella_key]["pattern"].append( pattern_key )
                triplet_odds_dict[triplet_key]["pattern"].append( pattern_key )
                horce_pattern_list[pattern_key] = { "score": horce_score, \
                                                    "horce_num": horce_num_list, \
                                                    "triplet_odds": triplet_odds, \
                                                    "quinella_odds": quinella_odds, \
                                                    "bet": False }
                all_score += horce_score

    odds_data = {}
    odds_data.update( triplet_odds_dict )
    odds_data.update( quinella_odds_dict )
    rate_score = 0

    for key in horce_pattern_list.keys():
        horce_pattern_list[key]["score"] /= all_score
        rate_score += horce_pattern_list[key]["score"]

    return horce_pattern_list, odds_data

def main( test_years = lib.simu_years, show = True ):
    recovery_rate = 0
    data = dm.pickle_load( lib.name.simu_name() )
    triplet_odds_data = dm.pickle_load( "triplet_odds_data.pickle" )
    quinella_odds_data = dm.pickle_load( "quinella_odds_data.pickle" )
    model_list = dm.pickle_load( lib.name.model_name() )
    test = {}
    test_result = { "count": 0, "bet_count": 0, "win": 0, "money": 0 }
    money = 2000
    bet_money = 50
    money_list = []
    ave_score = 0
    win_score = 0
    t = 1

    race_id_list = list( data.keys() )
    random.shuffle( race_id_list )

    for race_id in tqdm( race_id_list ):
        year = race_id[0:4]
        race_place_num = race_id[4:6]
        number = race_id[-2:]

        if not year in test_years:
            continue

        if not race_id in quinella_odds_data or not race_id in triplet_odds_data:
            continue

        horce_list = []
        horce_num_list = [ lib.escapeValue ] * 3

        for horce_id in data[race_id].keys():
            ex_value = {}
            p_score = 0

            #if data[race_id][horce_id]["answer"]["new"]:
            #    break

            for model in model_list:
                p_score += model.predict( np.array( [ data[race_id][horce_id]["data"] ] ) )[0]

            p_score /= len( model_list )
            ex_value["score"] = math.log( 1 + math.exp( p_score ) )
            ex_value["rank"] = data[race_id][horce_id]["answer"]["rank"]
            ex_value["odds"] = data[race_id][horce_id]["answer"]["odds"]
            ex_value["popular"] = data[race_id][horce_id]["answer"]["popular"]
            ex_value["horce_num"] = int( data[race_id][horce_id]["answer"]["horce_num"] )
            ex_value["horce_id"] = horce_id
            ex_value["rank_score"] = p_score
            horce_list.append( ex_value )

            if ex_value["rank"] < 4:
                horce_num_list[int(ex_value["rank"]-1)] = ex_value["horce_num"]

        if len( horce_list ) < 5 or lib.escapeValue in horce_num_list:
            continue

        all_score = 0
        answer_key_data = {}
        answer_key_data["quinella"] = create_quinella_key( horce_num_list[0:2] )
        answer_key_data["triplet"] = create_pattern_key( sorted( horce_num_list ) )
        horce_list = sorted( horce_list, key=lambda x:x["score"], reverse = True )

        for i in range( 0, len( horce_list ) ):
            horce_list[i]["score"] /= ( i + 1 )
            all_score += horce_list[i]["score"]

        for i in range( 0, len( horce_list ) ):
            horce_list[i]["score"] /= all_score
            horce_list[i]["ex_score"] = horce_list[i]["score"] * horce_list[i]["odds"]
            #print( horce_list[i]["score"], i + 1 )

        try:
            horce_pattern_data, odds_data = create_horce_pattern( horce_list, \
                                                                  triplet_odds_data[race_id], \
                                                                  quinella_odds_data[race_id] )
        except:
            continue

        if len( horce_list ) < 8:
            continue
        
        bet_key_list = []
        #print( horce_list[0]["horce_num"], horce_list[1]["horce_num"] )
        formation_horce_data = { "first": [], "second": [], "third": [] }
        horce_list = sorted( horce_list, key=lambda x:x["score"], reverse=True )

        for i in range( 0, 3 ):
            finish = False

            if horce_list[i]["ex_score"] < 1:
                continue
            
            finish = True
            horce_num_1 = horce_list[i]["horce_num"]
            candiate_bet_key_list = []

            for r in range( 0, len( horce_list ) ):
                horce_num_2 = horce_list[r]["horce_num"]
                
                if horce_num_1 == horce_num_2:
                    continue

                #if horce_list[r]["odds"] < 1.5:
                #    continue

                bet_key = create_quinella_key( [ horce_num_1, horce_num_2 ] )

                if not bet_key in bet_key_list:
                    candiate_bet_key_list.append( bet_key )
                    
                if len( candiate_bet_key_list ) == 5:
                    break

            bet_key_list.extend( candiate_bet_key_list )

        if len( bet_key_list ) == 0:
            continue
        
        win = 0
        test_result["bet_count"] += len( bet_key_list )

        for kind in answer_key_data.keys():
            answer_key = answer_key_data[kind]
            
            if answer_key in bet_key_list:
                test_result["money"] += odds_data[answer_key]["odds"]
                win = 1

        #print( race_id, bet_key_list, answer_key_data, win )
        test_result["count"] += 1
        test_result["win"] += win

    recovery_rate = ( test_result["money"] / test_result["bet_count"] ) * 100
    #three_recovery_rate = ( test_result["three_money"] / test_result["bet_count"] ) * 100
    win_rate = ( test_result["win"] / test_result["count"] ) * 100
    #three_win_rate = ( test_result["three_win"] / test_result["count"] ) * 100

    if show:
        print( "" )
        print( "回収率{}%".format( recovery_rate ) )
        #print( "複勝 回収率{}%".format( three_recovery_rate ) )
        print( "勝率{}%".format( win_rate ) )
        #print( "複勝 勝率{}%".format( three_win_rate ) )
        print( "賭けたレース数{}回".format( test_result["count"] ) )
        print( "賭けた金額{}".format( test_result["bet_count"] ) )
        #print( "金額:{}".format( money ) )
        #print( "最低金額:{}".format( min( money_list ) ) )
