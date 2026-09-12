import math
import torch
import random
import numpy as np
from tqdm import tqdm
import matplotlib.pyplot as plt

import SekitobaLibrary as lib
from SekitobaLibrary import ManageRecoveryScore
import SekitobaDataManage as dm


def recovery_score_create(cluster_data, data, c):
    score = 0
    nama_list = cluster_data["name"]
    data_type = cluster_data["type"]
    cluster_list = cluster_data["cluster"]

    for cluster in cluster_list:
        manage_recovery_score = ManageRecoveryScore({}, data_name_list=nama_list, data_type=data_type, cd=cluster)

        for name in cluster.keys():
            value = data[name][c]
            add_score = manage_recovery_score.check_score(value, name)

            if add_score == lib.escapeValue:
                continue

            score += add_score

    return score / len(cluster_data)


def change_win_rate(horce_data_list):
    score_list = []
    odds_list = []

    for horce_data in horce_data_list:
        score_list.append(horce_data["rank_score"])
        odds_list.append(horce_data["odds"])

    min_score = min(score_list)
    all_score = 0

    for i in range(0, len(score_list)):
        score_list[i] = max(score_list[i] - min_score * 1.1, 0)
        score_list[i] *= 2 - (i / 10)
        score_list[i] = math.pow(score_list[i], 2)
        all_score += score_list[i]

    for i in range(0, len(score_list)):
        score_list[i] = score_list[i] / all_score
        horce_data_list[i]["rate"] = score_list[i]

    # print( "rate:{}".format( score_list ) )
    # print( "odds:{}".format( odds_list ) )


def data_load(model_data, simu_data, reverse_list, name, reverse):
    simu_data[name] = dm.pickle_load(name + "_simu_data.pickle")
    model_data[name] = dm.pickle_load(name + "_model.pickle")

    if reverse:
        reverse_list.append(name)


def main(test_years=lib.simu_years, show=True):
    recovery_rate = 0
    BASE_KEY = "time_index"
    model_data = {}
    simu_data = {}
    revrse_list = []
    data_load(model_data, simu_data, revrse_list, "rank", True)
    data_load(model_data, simu_data, revrse_list, "time_index", True)
    data_load(model_data, simu_data, revrse_list, "race_time", False)
    data_load(model_data, simu_data, revrse_list, "diff", False)
    data_load(model_data, simu_data, revrse_list, "rate", True)

    money = 3000
    bet_money = 30  # int( money / 200 )
    money_list = []
    check_data = {"bet_count": 0, "win": 0, "money": 0}
    odds_data = dm.pickle_load("odds_data.pickle")
    # users_score_data = dm.pickle_load( "users_score_data.pickle")
    race_id_list = list(simu_data[BASE_KEY].keys())
    random.shuffle(race_id_list)

    for race_id in tqdm(race_id_list):
        year = race_id[0:4]
        race_place_num = race_id[4:6]
        number = race_id[-2:]

        if not year in test_years:
            continue

        all_score = 0
        horce_list = []
        current_odds = odds_data[race_id]
        skip = False

        for kind in model_data.keys():
            if not race_id in simu_data[kind]:
                skip = True
                break

            for horce_id in simu_data[BASE_KEY][race_id].keys():
                if not horce_id in simu_data[kind][race_id]:
                    skip = True
                    break

        if skip:
            continue

        for horce_id in simu_data[BASE_KEY][race_id].keys():
            scores = {}
            ex_value = {}

            # if simu_data["rank"][race_id][horce_id]["answer"]["new"]:
            #    break

            for kind in model_data.keys():
                scores[kind] = 0
                for model in model_data[kind]:
                    if kind == "rate":
                        scores[kind] += float(
                            model.predict_proba(np.array([simu_data[kind][race_id][horce_id]["data"]]))[0][-1]
                        )
                    else:
                        scores[kind] += float(model.predict(np.array([simu_data[kind][race_id][horce_id]["data"]]))[0])

                scores[kind] /= len(model_data[kind])

            scores["time_index"] += simu_data["time_index"][race_id][horce_id]["answer"]["time_index"]

            for key in scores.keys():
                ex_value[key + "_score"] = scores[key]

            ex_value["rank"] = simu_data[BASE_KEY][race_id][horce_id]["answer"]["rank"]
            ex_value["odds"] = simu_data[BASE_KEY][race_id][horce_id]["answer"]["odds"]
            ex_value["popular"] = simu_data[BASE_KEY][race_id][horce_id]["answer"]["popular"]
            ex_value["horce_id"] = horce_id
            horce_list.append(ex_value)

        if len(horce_list) < 5:
            continue

        select_horce = lib.SelectHorce(horce_list, list(model_data.keys()), revrse_list, current_odds)
        get_money = select_horce.exacta(BASE_KEY)

        if get_money == lib.escapeValue:
            continue

        if get_money > 0:
            check_data["win"] += 1
            check_data["money"] += get_money

        check_data["bet_count"] += 1
        money += get_money * bet_money
        money_list.append(money)

    moeny_rate = (check_data["money"] / check_data["bet_count"]) * 100
    win_rate = (check_data["win"] / check_data["bet_count"]) * 100

    if show:
        print("")
        print("回収率{}%".format(moeny_rate))
        print("勝率{}%".format(win_rate))
        print("賭けたレース数{}回".format(check_data["bet_count"]))
        print("賭けた金額{}".format(check_data["bet_count"] * bet_money))
        print("金額:{}".format(money))
        print("最低金額:{}".format(min(money_list)))
        # print( "mdcd:{}".format( round( mdcd_score / mdcd_count, 4 ) ) )

    # return one_win_rate, three_win_rate, round( mdcd_score / mdcd_count, 4 )
