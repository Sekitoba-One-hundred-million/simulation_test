import copy
import math
from tqdm import tqdm

import SekitobaLibrary as lib
import SekitobaDataManage as dm

WIDE = "wide"
ONE = "one"

class SelectHorce:
    def __init__( self, wide_odds_data, horce_data ):
        self.use_count = 10
        self.bet_rate = 1
        self.goal_rate = 2
        self.bet_result_count = 0
        self.wide_odds_data = wide_odds_data
        self.horce_data = horce_data
        self.select_horce_list = []

    def create_rate( self ):
        rate_data = []
        all_rate = 0
        
        for i in range( 0, len( self.horce_data ) ):
            score_1 = self.horce_data[i]["score"]
            horce_num_1 = self.horce_data[i]["horce_num"]
            
            for r in range( i + 1, len( self.horce_data ) ):
                score_2 = self.horce_data[r]["score"]
                horce_num_2 = self.horce_data[r]["horce_num"]

                for t in range( r + 1, len( self.horce_data ) ):
                    score_3 = self.horce_data[t]["score"]
                    horce_num_3 = self.horce_data[t]["horce_num"]
                    rate = score_1 * score_2 * score_3

                    rate_data.append( { "rate": rate, \
                                       "horce_num_list": [ horce_num_1, horce_num_2, horce_num_3 ], \
                                       "use": False } )
                    all_rate += rate

        for i in range( 0, len( rate_data ) ):
            rate_data[i]["rate"] /= all_rate

        return rate_data

    def create_candidate( self ):
        candidate = []

        for horce_num_1 in self.wide_odds_data.keys():
            for horce_num_2 in self.wide_odds_data[horce_num_1].keys():
                horce_num_list = [ horce_num_1, horce_num_2 ]
                candidate.append( { "horce_num_list": horce_num_list, \
                                   "odds": self.wide_odds_data[horce_num_1][horce_num_2]["min"], \
                                   "kind": "wide",
                                   "use": False } )

        return candidate

    def create_score( self, bet_list ):
        score = 0

        for rd in self.rate_data:
            for bet in bet_list:
                if bet["horce_num_list"][0] in rd["horce_num_list"] \
                  and bet["horce_num_list"][1] in rd["horce_num_list"]:
                    score += math.pow( rd["rate"], 2.2 ) * math.pow( bet["odds"], 0.6 )

        return score

    def selectHorce( self ):
        rateData = self.create_rate()
        candiateList = self.create_candidate()        

    def bet_check( self, bet_list, current_odds ):
        get_money = 0

        for bet in bet_list:
            rank = 0
            check = True

            for hd in self.horce_data:
                if bet["kind"] == WIDE and hd["horce_num"] in bet["horce_num_list"]:
                    if hd["rank"] > 3:
                        check = False
                        break
                    else:
                        rank += hd["rank"]
                elif bet["kind"] == ONE and hd["horce_num"] in bet["horce_num_list"]:
                    if not hd["rank"] == 1:
                        check = False
                        break
                    else:
                        rank = hd["rank"]

            if check:
                if bet["kind"] == WIDE:
                    try:
                        get_money += ( current_odds["ワイド"][int(rank-3)] / 100 ) * bet["count"]
                    except:
                        pass
                elif bet["kind"] == ONE:
                    get_money += bet["odds"] * bet["count"]

        return get_money
