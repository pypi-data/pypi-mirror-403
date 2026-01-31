# -*- coding: utf-8 -*-
def features(ft, data):
		data[0] = (ft.get("length") - 90.194) / 65.6979546409171
		data[1] = (ft.get("speed") - 13.334) / 1.6680000000000001
		data[2] = (ft.get("num_foes") - 9.4) / 4.223742416388575
		data[3] = (ft.get("num_lanes") - 1.5) / 0.6708203932499369
		data[4] = (ft.get("junction_inc_lanes") - 5.6) / 1.854723699099141
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

params = [0.3, 0.365, 0.2359375, 0.3809090909090909, 0.29133333333333333, 0.5506666666666666, 0.4649090909090909, 0.6357142857142858, 0.2523020833333333, 0.32633333333333336, 0.3809090909090909, 0.4649090909090909, 0.6357142857142858, 0.5506666666666666, 0.3809090909090909, 0.2686666666666666, 0.2359375, 0.3395, 0.3, 0.5506666666666666, 0.6357142857142858, 0.4649090909090909, 0.365, 0.3, 0.2359375, 0.3809090909090909, 0.29133333333333333, 0.4649090909090909, 0.5506666666666666, 0.6357142857142858, 0.2523020833333333, 0.32633333333333336, 0.3809090909090909, 0.4649090909090909, 0.6357142857142858, 0.5506666666666666]
def score(params, inputs):
    if inputs[0] <= -0.6409156647600256:
        if inputs[0] <= -0.8370998669230032:
            if inputs[1] <= -2.1584090378316554:
                var0 = params[0]
            else:
                var0 = params[1]
        else:
            var0 = params[2]
    else:
        if inputs[0] <= 1.8481190578419047:
            if inputs[0] <= 0.07638063105863846:
                if inputs[15] <= -1.9394416799486809:
                    var0 = params[3]
                else:
                    var0 = params[4]
            else:
                if inputs[2] <= 0.5450737071569283:
                    var0 = params[5]
                else:
                    var0 = params[6]
        else:
            var0 = params[7]
    if inputs[0] <= 0.7093046554202866:
        if inputs[9] <= 0.7264475811861677:
            if inputs[17] <= 0.7481153983381182:
                if inputs[12] <= 0.4526313117019047:
                    var1 = params[8]
                else:
                    var1 = params[9]
            else:
                var1 = params[10]
        else:
            var1 = params[11]
    else:
        if inputs[4] <= 0.5017437628555758:
            var1 = params[12]
        else:
            var1 = params[13]
    if inputs[0] <= 0.45643386321346946:
        if inputs[15] <= -1.766959311332069:
            var2 = params[14]
        else:
            if inputs[12] <= 0.709724932773842:
                if inputs[14] <= 3.9477904718126124:
                    var2 = params[15]
                else:
                    var2 = params[16]
            else:
                if inputs[5] <= 2.5957385403421003:
                    var2 = params[17]
                else:
                    var2 = params[18]
    else:
        if inputs[9] <= 0.11346051055633487:
            if inputs[14] <= 3.516921896728185:
                var2 = params[19]
            else:
                var2 = params[20]
        else:
            var2 = params[21]
    if inputs[0] <= -0.8266503338011447:
        if inputs[0] <= -1.1316131667521994:
            var3 = params[22]
        else:
            if inputs[4] <= -1.224844318790756:
                var3 = params[23]
            else:
                var3 = params[24]
    else:
        if inputs[0] <= 0.6415315700002113:
            if inputs[9] <= 0.2709412971841829:
                if inputs[15] <= -1.9923353055456352:
                    var3 = params[25]
                else:
                    var3 = params[26]
            else:
                var3 = params[27]
        else:
            if inputs[14] <= 3.1910885503474105:
                var3 = params[28]
            else:
                var3 = params[29]
    if inputs[0] <= 0.933810683146636:
        if inputs[9] <= 0.6584552930008878:
            if inputs[17] <= 0.32400339903496367:
                if inputs[12] <= 0.8595956344434971:
                    var4 = params[30]
                else:
                    var4 = params[31]
            else:
                var4 = params[32]
        else:
            var4 = params[33]
    else:
        if inputs[4] <= 0.6467121356341781:
            var4 = params[34]
        else:
            var4 = params[35]
    return (var0 + var1 + var2 + var3 + var4) * 0.2

def batch_loss(params, inputs, targets):
    error = 0
    for x, y in zip(inputs, targets):
        preds = score(params, x)
        error += (preds - y) ** 2
    return error
