import matplotlib
import numpy as np
from tephi import tests
import matplotlib.pyplot as plt
import os.path
import tephi
from tephi.constants import default
#
matplotlib.use("tkagg")

def _load_result(filename):
    with np.load(tests.get_result_path(filename)) as f:
        result = f["arr_0"]
    return result

_expected_dews = _load_result("dews.npz")
_expected_temps = _load_result("temps.npz")


_lrT_temps = _expected_temps.T
_lrT_dews = _expected_dews.T

tephigram = tephi.TephiAxes()
tephigram2 = tephi.TephiAxes()

tephigram.plot(_lrT_dews)
tephigram.add_isobars()
tephigram.add_wet_adiabats()
tephigram.add_mixing_ratios()


tephigram2.plot(_lrT_dews)
# profile.barbs(new__lr_dews, new__lr_temps)

tephigram2.add_mixing_ratios()
tephigram2.mixing_ratio.nbins=10

tephigram2.add_isobars()
tephigram.isobar.text_config["color"] = "red"



# tephi.ISOBAR.line
print(tephi.constants.default)






# tephigram2.barbs()

plt.show()


# import matplotlib.pyplot as plt
# import os.path
#
# import tephi
#
# winds = os.path.join(tephi.DATA_DIR, 'barbs.txt')
# column_titles = ('pressure', 'dewpoint', 'wind_speed', 'wind_direction')
# barb_data = tephi.loadtxt(winds, column_titles=column_titles)
# dews = zip(barb_data.pressure, barb_data.dewpoint)
# barbs = zip(barb_data.wind_speed, barb_data.wind_direction, barb_data.pressure)
# tpg = tephi.TephiAxes()
# profile = tpg.plot(dews)
# profile.barbs(barbs)
# plt.show()
#
# profile = tephigram.plot(temps_1)
#
# tephigram.figure.set_size_inches(8,8)
# # tephigram.add_isobars()
# # tephigram.add_wet_adiabats()
# # tephigram.add_humidity_mixing_ratios()
#
# matplotlib.pyplot.show()
#
# dew_point = os.path.join(tephi.DATA_DIR, 'dews.txt')
# dry_bulb = os.path.join(tephi.DATA_DIR, 'temps.txt')
# column_titles = [('pressure', 'dewpoint'), ('pressure', 'temperature')]
# dew_data, temp_data = tephi.loadtxt(dew_point, dry_bulb, column_titles=column_titles)
#
# tephigram = tephi.TephiAxes()
# print("temps: ", temps)
# print("temp_data: ", temp_data)
#
# print("dews: ", dews)
# print("dew_data: ", dew_data)
# dprofile = tephigram.plot(dew_data)
# dbarbs = [(0, 0, 900), (15, 120, 600), (35, 240, 300)]
# dprofile.barbs(dbarbs)
# tprofile = tephigram.plot(temps)
# tbarbs = [(10, 15, 900), (21, 45, 600), (25, 135, 300)]
# tprofile.barbs(tbarbs)
#

