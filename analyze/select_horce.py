import copy
import math
from tqdm import tqdm

import SekitobaLibrary as lib
import SekitobaDataManage as dm

WIDE = "wide"
TRIPLET = "triplet"
ONE = "one"

class SelectHorce:
    def __init__( self, wide_odds_data, triplet_odds_data, horce_data ):
        self.allBetCount = 10
        self.purpose = 1.5
        self.bet_result_count = 0
        self.betCount = 0
        self.wide_odds_data = wide_odds_data
        self.triplet_odds_data = triplet_odds_data
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
        horceNumList = []

        for horce in self.horce_data:
            horceNumList.append( horce["horce_num"] )

        for horce_num_1 in self.wide_odds_data.keys():
            if not horce_num_1 in horceNumList:
                continue
            
            for horce_num_2 in self.wide_odds_data[horce_num_1].keys():
                if not horce_num_2 in horceNumList:
                    continue

                candidate.append(
                    { "horce_num_list": [ horce_num_1, horce_num_2 ], \
                      "odds": self.wide_odds_data[horce_num_1][horce_num_2]["min"], \
                      "kind": "wide",
                      "use": False,
                      "index": len( candidate ) } )

        for horce_num_1 in self.triplet_odds_data.keys():
            if not horce_num_1 in horceNumList:
                continue
            
            for horce_num_2 in self.triplet_odds_data[horce_num_1].keys():
                if not horce_num_2 in horceNumList:
                    continue

            for horce_num_3 in self.triplet_odds_data[horce_num_1][horce_num_2].keys():
                if not horce_num_3 in horceNumList:
                    continue

                candidate.append(
                    { "horce_num_list": [ horce_num_1, horce_num_2, horce_num_3 ], \
                      "odds": self.triplet_odds_data[horce_num_1][horce_num_2][horce_num_3], \
                      "kind": "triplet",
                      "use": False,
                      "index": len( candidate ) } )
                
        return candidate

    def createBetCount( self, odds ):
        return max( int( ( self.allBetCount * self.purpose ) / odds ), 1 )

    def checkBetHorce( self, candiateList, rateDataList ):
        result = {}
        alreadyBetList = []
        maxScore = -10000

        for candiate in candiateList:
            if candiate["use"]:
                alreadyBetList.append( candiate )

        for candiate in candiateList:
            if candiate["use"]:
                continue

            odds = candiate["odds"]
            betCount = self.createBetCount( odds )

            if self.allBetCount < betCount + self.betCount:
                continue

            candiateRate = 0

            for rateData in rateDataList:
                if rateData["use"]:
                    continue

                rate = rateData["rate"]
                
                for horceNum in candiate["horce_num_list"]:
                    if not horceNum in rateData["horce_num_list"]:
                        rate = 0
                        break

                candiateRate += rate
                
            candiate["rate"] = candiateRate
            betRisk = math.pow( betCount, 1 )
            score = ( candiateRate / betRisk ) * math.pow( odds, 1 )
            sr = 1

            for alreadyBet in alreadyBetList:
                c = 0

                for horceNum in candiate["horce_num_list"]:
                    if horceNum in alreadyBet["horce_num_list"]:
                        c += 1

                if len( alreadyBet["horce_num_list"] ) - 1 == c:
                    sr = 2
                    break

            score *= sr
            candiate["score"] = score

            if maxScore < score:
                maxScore = score
                result = copy.deepcopy( candiate )

        return result, maxScore
        
    def selectHorce( self ):
        result = []
        currentBetCount = 0
        allScore = 0
        allRate = 0
        rateDataList = self.create_rate()
        candiateList = self.create_candidate()
        
        while 1:
            if self.allBetCount <= self.betCount:
                break
            
            betHorce, bestScore = self.checkBetHorce( candiateList, rateDataList )

            if len( betHorce ) == 0:
                break
            
            candiateList[betHorce["index"]]["use"] = True
            betHorce["count"] = self.createBetCount( betHorce["odds"] )
            allScore += bestScore

            #if self.allBetCount < self.betCount + betHorce["count"]:
            #    break
            
            self.betCount += betHorce["count"]
            allRate += betHorce["rate"]
            result.append( betHorce )

            for i in range( 0, len( rateDataList ) ):
                if rateDataList[i]["use"]:
                    continue
                
                use = True

                for horceNum in betHorce["horce_num_list"]:
                    if not horceNum in rateDataList[i]["horce_num_list"]:
                        use = False
                        break

                if use:
                    #rateDataList[i]["use"] = use
                    rateDataList[i]["rate"] *= 0.5

        return result, allScore

    def bet_check( self, bet_list, current_odds ):
        get_money = 0
        oddsList = []

        for bet in bet_list:
            rank = 0
            check = True

            for hd in self.horce_data:
                if not hd["horce_num"] in bet["horce_num_list"]:
                    continue
                
                if bet["kind"] == WIDE or bet["kind"] == TRIPLET:
                    if hd["rank"] > 3:
                        check = False
                        break
                    else:
                        rank += hd["rank"]

            if check:
                if bet["kind"] == WIDE:
                    try:
                        get_money += ( current_odds["ワイド"][int(rank-3)] / 100 ) * bet["count"]
                        oddsList.append( [ current_odds["ワイド"][int(rank-3)] / 100, bet["horce_num_list"] ] )
                    except:
                        pass
                elif bet["kind"] == TRIPLET:
                    get_money += bet["odds"] * bet["count"]

        return get_money, oddsList
