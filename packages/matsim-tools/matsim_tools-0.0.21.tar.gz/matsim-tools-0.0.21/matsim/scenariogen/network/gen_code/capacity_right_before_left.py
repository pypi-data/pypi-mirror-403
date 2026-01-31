# -*- coding: utf-8 -*-
def features(ft, data):
		data[0] = (ft.get("length") - 84.85605230386052) / 69.6657919738212
		data[1] = (ft.get("speed") - 8.520410958904108) / 0.7550373502208979
		data[2] = (ft.get("num_foes") - 5.093399750933997) / 2.941097764970295
		data[3] = (ft.get("num_lanes") - 1.0722291407222915) / 0.27744320509328974
		data[4] = (ft.get("junction_inc_lanes") - 3.1170610211706102) / 0.5101659730540836
		data[5] = ft.get("change_speed")
		data[6] = ft.get("dir_l")
		data[7] = ft.get("dir_r")
		data[8] = ft.get("dir_s")
		data[9] = ft.get("dir_multiple_s")
		data[10] = ft.get("dir_exclusive")
		data[11] = ft.get("priority_lower")
		data[12] = ft.get("priority_equal")
		data[13] = ft.get("priority_higher")
		data[14] = ft.get("num_to_links")
		data[15] = ft.get("change_num_lanes")
		data[16] = ft.get("is_secondary_or_higher")
		data[17] = ft.get("is_primary_or_higher")
		data[18] = ft.get("is_motorway")
		data[19] = ft.get("is_link")

params = [1000.0, 1361.3793103448277, 1712.9885057471265, 262.7586206896552, 1719.3103448275865, 0.0, 1475.1724137931037, 1912.3607427055701, 1588.2068965517242, 1061.700277093596, 708.4137931034483, 1617.9310344827586, 1664.5436105476674, 1546.7780172413793]
def score(params, inputs):
    if inputs[0] <= -0.8906243741512299:
        if inputs[2] <= -0.3717658556997776:
            if inputs[15] <= -0.5:
                var0 = params[0]
            else:
                if inputs[17] <= 0.5:
                    var0 = params[1]
                else:
                    var0 = params[2]
        else:
            if inputs[0] <= -0.9539266228675842:
                if inputs[0] <= -0.957586944103241:
                    var0 = params[3]
                else:
                    var0 = params[4]
            else:
                var0 = params[5]
    else:
        if inputs[2] <= 0.9882705770432949:
            if inputs[4] <= -1.2095299139618874:
                if inputs[1] <= 1.588781014084816:
                    var0 = params[6]
                else:
                    var0 = params[7]
            else:
                if inputs[10] <= 0.5:
                    var0 = params[8]
                else:
                    var0 = params[9]
        else:
            if inputs[10] <= 0.5:
                if inputs[0] <= 0.11611075419932604:
                    var0 = params[10]
                else:
                    var0 = params[11]
            else:
                if inputs[0] <= -0.39403918385505676:
                    var0 = params[12]
                else:
                    var0 = params[13]
    return var0

def batch_loss(params, inputs, targets):
    error = 0
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
