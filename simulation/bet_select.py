import sekitoba_library as lib
import matplotlib.pyplot as plt

import copy

def regression( x_list, y_list ):
    n = len( x_list )
    ave_x = sum( x_list ) / n
    ave_y = sum( y_list ) / n
    ave_xx = 0

    for i in range( 0, len( x_list ) ):
        ave_xx += pow( x_list[i], 2 )

    ave_xx /= n
    Sxx = 0
    Sxy = 0
    Sx_xx = 0
    Sxx_xx = 0
    Sxx_y = 0

    for i in range( 0, len( x_list ) ):
        Sxx += pow( x_list[i] - ave_x, 2 )
        Sxy += ( x_list[i] - ave_x ) * ( y_list[i] - ave_y )
        Sx_xx += ( x_list[i] - ave_x ) * ( pow( x_list[i], 2 ) - ave_xx )
        Sx_xx += ( x_list[i] - ave_x ) * ( pow( x_list[i], 2 ) - ave_xx )
        Sxx_y += ( pow( x_list[i], 2 ) - ave_xx ) * ( y_list[i] - ave_y )

    Sxx /= n
    Sxy /= n
    Sx_xx /= n
    Sxx_xx /= n
    Sxx_y /= n

    b = ( Sxy * Sxx_xx - Sxx_y * Sx_xx ) / ( Sxx * Sxx_xx - pow( Sx_xx, 2 ) )
    c = ( Sxx_y * Sxx - Sxy * Sx_xx ) / ( Sxx * Sxx_xx - pow( Sx_xx, 2 ) )
    a = ave_y - b * ave_x - c * ave_xx
    print( a, b, c )
    return a, b, c


def score_get( x_list, odds_list, rate_list, n ):
    ex = 0
    risk = 0

    for i in range( 0, len( x_list ) ):
        ex += odds_list[i] * x_list[i]
        risk += pow( x_list[i], 2 ) / rate_list[i]
        
        if x_list[i] * odds_list[i] <= n:
            return -1, -1

    ex /= n
    risk /= n

    return ex, risk

def main( rate_list, odds_list, N ):
    x_list = [0] * len( rate_list )
    ex_list = []
    risk_list = []
    bed_list = []

    for i in range( 1, pow( N + 1, len( x_list ) ) ):
        x_list[0] += 1
        
        for r in range( 0, len( x_list ) - 1 ):
            if x_list[r] == N + 1:
                x_list[r] = 0
                x_list[r+1] += 1

        if sum( x_list ) == 20:
            ex, risk = score_get( x_list, odds_list, rate_list, N )
            if not ex == -1 and not risk == -1:
                risk_list.append( risk )
                ex_list.append( ex )
                bed_list.append( copy.copy( x_list ) )
                

    #zip_list = zip( risk_list, ex_list )
    #zip_sort = sorted( zip_list )
    #risk_list, ex_list = zip( *zip_sort )
    
    #a, b = lib.xy_regression_line( ex_list, risk_list )
    a, b, c = regression( ex_list, risk_list )
    
    x_list = []
    y_list = []
    max_y = -1
    check = 0
    
    for i in range( 0, len( risk_list ) ):
        x = ex_list[i]
        y = a + b * x + c * pow( x, 2 )

        if y <= risk_list[i]:
            continue

        diff_y = abs( y - risk_list[i] )
        
        if max_y < diff_y:
            max_y = diff_y
            check = i

    """
    for i in range( int( min( ex_list ) ), int( max( ex_list ) ) ):
        x = i
        y = a + b * x + c * pow( x, 2 )
        x_list.append( x )
        y_list.append( y )
        
    plt.scatter( ex_list, risk_list )
    plt.plot( x_list, y_list, color='red' )
    plt.scatter( ex_list[check], risk_list[check] )
    plt.savefig( "test.png" )
    """
    return bed_list[check]
                
    
