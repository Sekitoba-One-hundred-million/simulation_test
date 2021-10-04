from tqdm import tqdm

import sekitoba_library as lib
import sekitoba_data_manage as dm
from data_analyze.train_index_get import train_index_get

dm.dl.file_set( "race_cource_info.pickle" )
dm.dl.file_set( "race_cource_wrap.pickle" )
dm.dl.file_set( "first_pace_analyze_data.pickle" )
dm.dl.file_set( "race_info_data.pickle" )
dm.dl.file_set( "race_data.pickle" )
dm.dl.file_set( "first_pace_analyze_data.pickle" )
dm.dl.file_set( "passing_data.pickle" )
dm.dl.file_set( "horce_data_storage.pickle" )
dm.dl.file_set( "corner_horce_body.pickle" )
dm.dl.file_set( "baba_index_data.pickle" )

def use_corner_check( s ):
    if s == 4:
        return [ "1", "3" ]
    elif s == 3:
        return [ "2", "3" ]
    
    return [ "3" ]

def start_check( s ):
    if s == 0:
        return 1
    
    return 0

def list_max( l ):
    try:
        return max( l )
    except:
        return 0

def main( update = False ):
    result = None
    
    if not update:
        result = dm.pickle_load( "test_simu_learn_data.pickle" )

    if result == None:
        result = {}
    else:
        return result

    result["answer"] = []
    result["teacher"] = []
    result["test_answer"] = []
    result["test_teacher"] = []
    result["test_count"] = []
    result["year"] = []
    
    simu_data = {}
    max_diff = -1

    race_data = dm.dl.data_get( "race_data.pickle" )
    horce_data = dm.dl.data_get( "horce_data_storage.pickle" )
    race_cource_wrap = dm.dl.data_get( "race_cource_wrap.pickle" )
    race_info = dm.dl.data_get( "race_info_data.pickle" )
    first_pace_analyze_data = dm.dl.data_get( "first_pace_analyze_data.pickle" )
    passing_data = dm.dl.data_get( "passing_data.pickle" )
    race_cource_info = dm.dl.data_get( "race_cource_info.pickle" )
    corner_horce_body = dm.dl.data_get( "corner_horce_body.pickle" )
    baba_index_data = dm.dl.data_get( "baba_index_data.pickle" )
    train_index = train_index_get()

    for k in tqdm( race_data.keys() ):
        race_id = lib.id_get( k )
        year = race_id[0:4]
        race_place_num = race_id[4:6]
        day = race_id[9]
        num = race_id[7]

        try:
            current_wrap = race_cource_wrap[race_id]
        except:
            continue

        key_place = str( race_info[race_id]["place"] )
        key_dist = str( race_info[race_id]["dist"] )
        key_kind = str( race_info[race_id]["kind"] )        
        key_baba = str( race_info[race_id]["baba"] )
        
        info_key_dist = key_dist
        
        if race_info[race_id]["out_side"]:
            info_key_dist += "外"
            
        rci_dist = race_cource_info[key_place][key_kind][info_key_dist]["dist"]
        rci_info = race_cource_info[key_place][key_kind][info_key_dist]["info"]
        race_limb = [0] * 9
        count = 0
        train_index_list = train_index.main( race_data[k], horce_data, race_id )

        for kk in race_data[k].keys():
            horce_name = kk.replace( " ", "" )
            current_data, past_data = lib.race_check( horce_data[horce_name],
                                                     year, day, num, race_place_num )#今回と過去のデータに分ける
            cd = lib.current_data( current_data )
            pd = lib.past_data( past_data, current_data )
                
            if not cd.race_check():
                continue
            
            try:
                limb_math = lib.limb_search( passing_data[horce_name], pd )
            except:
                limb_math = 0

            race_limb[limb_math] += 1

        for kk in race_data[k].keys():
            horce_name = kk.replace( " ", "" )
            current_data, past_data = lib.race_check( horce_data[horce_name],
                                                     year, day, num, race_place_num )#今回と過去のデータに分ける
            cd = lib.current_data( current_data )
            pd = lib.past_data( past_data, current_data )

            if not cd.race_check():
                continue
                
            key_horce_num = str( int( cd.horce_number() ) )
            t = []
            
            try:
                horce_body = corner_horce_body[race_id]["4"][key_horce_num]
            except:
                continue

            
            speed, up_speed, _ = pd.speed_index( baba_index_data[horce_name] )
            dm.dn.append( t, race_limb[0], "その他の馬の数" )
            dm.dn.append( t, race_limb[1], "逃げaの馬の数" )
            dm.dn.append( t, race_limb[2], "逃げbの馬の数" )
            dm.dn.append( t, race_limb[3], "先行aの馬の数" )
            dm.dn.append( t, race_limb[4], "先行bの馬の数" )
            dm.dn.append( t, race_limb[5], "差しaの馬の数" )
            dm.dn.append( t, race_limb[6], "差しbの馬の数" )
            dm.dn.append( t, race_limb[7], "追いの馬の数" )
            dm.dn.append( t, race_limb[8], "後方の馬の数" )
            dm.dn.append( t, float( key_place ), "場所" )
            dm.dn.append( t, float( key_dist ), "距離" )
            dm.dn.append( t, float( key_kind ), "芝かダート" )
            dm.dn.append( t, float( key_baba ), "馬場" )
            dm.dn.append( t, rci_dist[-1], "直線の距離" )
            dm.dn.append( t, lib.limb_search( passing_data[horce_name], pd ), "過去データからの予想脚質" )
            dm.dn.append( t, horce_body, "最終コーナーの馬身" )
            dm.dn.append( t, list_max( speed ), "最大のスピード指数" )
            dm.dn.append( t, list_max( up_speed ), "最大の上りスピード指数" )
            dm.dn.append( t, pd.best_weight(), "ベスト体重と現在の体重の差" )
            dm.dn.append( t, pd.race_interval(), "中週" )
            dm.dn.append( t, pd.average_speed(), "平均速度" )
            dm.dn.append( t, pd.pace_up_check(), "ペースと上りの関係" )
            dm.dn.append( t, train_index_list[count]["a"], "調教ペースの傾き" )
            dm.dn.append( t, train_index_list[count]["b"], "調教ペースの切片" )
            dm.dn.append( t, train_index_list[count]["time"], "調教ペースの指数タイム" )

            count += 1
            max_diff = max( int( max( cd.diff(), 0 ) * 10 ), max_diff )

            result["year"].append( year )
            result["answer"].append( min( int( max( cd.diff(), 0 ) * 10 ), 100 ) )
            result["teacher"].append( t )
            
            if year == "2020":
                result["test_answer"].append( cd.diff() )
                result["test_teacher"].append( t )                

        if year == "2020":
            result["test_count"].append( count )

    print( len( result["test_answer"] ) , len( result["test_teacher"] ), sum( result["test_count"] ) )
    dm.pickle_upload( "test_simu_learn_data.pickle", result )
    #dm.pickle_upload( "straight_horce_body_minmax.pickle", hm )
    #dm.pickle_upload( "straight_horce_body_simu_data.pickle", simu_data )

    return result
