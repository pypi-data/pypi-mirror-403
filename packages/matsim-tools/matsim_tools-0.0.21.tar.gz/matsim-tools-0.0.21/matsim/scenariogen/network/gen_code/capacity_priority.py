# -*- coding: utf-8 -*-
def features(ft, data):
		data[0] = (ft.get("length") - 128.2457324488668) / 113.93955441207002
		data[1] = (ft.get("speed") - 18.73397457158651) / 5.565821413411222
		data[2] = (ft.get("num_foes") - 0.9718076285240465) / 2.157886558579616
		data[3] = (ft.get("num_lanes") - 1.1785516860143725) / 0.4419464243794225
		data[4] = (ft.get("junction_inc_lanes") - 2.742399115533444) / 0.9105845223710698
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

params = [1908.879310344828, 1743.3990147783254, 1777.931034482759, 1607.2595281306715, 1658.8965517241381, 2075.4771856495936, 2065.158194098828, 2345.383532723433, 1394.0689655172414, 1383.6453201970446, 1666.2068965517244, 1487.5862068965519, 1666.8965517241381, 1666.4039408866995]
def score(params, inputs):
    if inputs[3] <= 2.9900644421577454:
        if inputs[8] <= 0.5:
            if inputs[6] <= 0.5:
                if inputs[1] <= -0.12199000269174576:
                    var0 = params[0]
                else:
                    var0 = params[1]
            else:
                if inputs[0] <= -0.7064336240291595:
                    var0 = params[2]
                else:
                    var0 = params[3]
        else:
            if inputs[3] <= 0.7273467928171158:
                if inputs[1] <= -1.619522750377655:
                    var0 = params[4]
                else:
                    var0 = params[5]
            else:
                if inputs[1] <= -0.12199000269174576:
                    var0 = params[6]
                else:
                    var0 = params[7]
    else:
        if inputs[15] <= -0.5:
            if inputs[1] <= -0.12199000269174576:
                if inputs[0] <= -0.7552314102649689:
                    var0 = params[8]
                else:
                    var0 = params[9]
            else:
                var0 = params[10]
        else:
            if inputs[0] <= -0.8427339792251587:
                var0 = params[11]
            else:
                if inputs[0] <= -0.7567673325538635:
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
