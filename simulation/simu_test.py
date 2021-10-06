import numpy as np
import random
from tqdm import tqdm

import sekitoba_library as lib
import sekitoba_data_manage as dm

N = 1000

def probability( p_data ):
    number = -1
    count = 0
    r_check = random.random()
    
    for i in range( 0, len( p_data ) ):
        count += p_data[i]
        
        if r_check <= count:
            number = i
            break

    if number == -1:
        number = len( p_data )

    return number    

def main( data, model ):
    count = 0
    win = 0
    money = 0
    race_num = len( data["test_count"] )

    for i in tqdm( range( 0, race_num ) ):
        current_count = data["test_count"][i]
        use_data = data["test_teacher"][count:count+current_count]
        use_answer = data["test_answer"][count:count+current_count]
        predict_data = model.forward( np.array( use_data, np.float32 ) ).data
            
        answer = sorted( use_answer, key=lambda x:x["rank"] )
        predict_answer = []

        for p_data in predict_data:
            number = 0
            
            for n in range( 0, N ):
                number += probability( p_data )

            number /= N
            predict_answer.append( { "diff": number, "count": len( predict_answer ) + 1 } )

        predict_answer = sorted( predict_answer, key=lambda x:x["diff"] )
        
        if predict_answer[0]["count"] == answer[0]["count"]:
            money += answer[0]["odds"]
            win += 1

        count += current_count

    print( "勝率{}%\n回収率{}%".format( win / race_num * 100, money / race_num * 100 ) )
                
        
    
