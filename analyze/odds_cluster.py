import SekitobaLibrary as lib

class OddsCluster:
    def __init__( self, horceList ):
        self.cluster = {}
        self.horceList = horceList
        self.favoriteRate = 0.5
        self.midLevelRate = 0.3
        self.longShotRate = 0.2
        self.splitRateList = [ self.favoriteRate, self.midLevelRate, self.longShotRate ]

    def clustering( self ):
        useHorceList = sorted( self.horceList, key=lambda x:x["odds"] )
        oddsList = []
        useOddsList = []
        regressionList = []
        beforeStd = lib.escapeValue
        oddsRank = 1

        for horce in useHorceList:
            oddsList.append( horce["odds"] )
            useOddsList.append( horce["odds"] )
            minOdds = lib.minimum( useOddsList )

            if minOdds * 5 < horce["odds"]:
                oddsRank += 1
                useOddsList.clear()
                self.cluster[horce["horce_id"]] = oddsRank

                if not len( oddsList ) == 1:
                    a, _ = lib.regression_line( oddsList[-3:] )
                    regressionList.append( a )
                    continue

            if len( oddsList ) == 1:
                self.cluster[horce["horce_id"]] = oddsRank
                continue

            a, _ = lib.regression_line( oddsList[-3:] )
            regressionList.append( a )

            if len( regressionList ) == 1:
                self.cluster[horce["horce_id"]] = oddsRank
                continue

            beforeOdds = oddsList[-2]
            currentStd = lib.stdev( regressionList )
            regression1 = regressionList[-2]
            regression2 = regressionList[-1]
            
            if ( not beforeStd == lib.escapeValue and horce["odds"] / beforeOdds > 1.2 ) and \
              ( beforeStd * 2 < currentStd or \
               ( 2 <= len( useOddsList ) and minOdds * 4 < horce["odds"] ) ):
                oddsRank += 1
                useOddsList.clear()

            beforeStd = currentStd
            oddsRank = min( oddsRank, 4 )
            self.cluster[horce["horce_id"]] = oddsRank

        #for horce in useHorceList:
        #    print( horce["odds"], self.cluster[horce["horce_id"]] )
