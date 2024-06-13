from pyomo.core import Constraint
import numpy as np
from datetime import datetime

np_true = np.bool_(True)


def constraints_from_dict(cons, model, prefix):
	if type(cons) is dict:
		if not cons:
			return

		def rule(model, *k):
			if len(k) == 1:
				k = k[0]
			ret = cons[k]
			if ret is True:
				return Constraint.Feasible
			return ret
		result = Constraint(cons.keys(), rule=rule)
		setattr(model, prefix, result)
	else:
		result = Constraint(expr=cons)
		setattr(model, prefix, result)


def choose_week_for_calc(config_date, dates):
	converted_month_dict = {
		'Jan':"01",
		'Feb':"02",
		'Mar':"03",
		'Apr':"04",
		'May':"05",
		'Jun':"07",
		'Jul':"08",
		'Aug':"09",
		'Sep':"09",
		'Oct':"10",
		"Nov":"11",
		'Dec':"12",
	}
	day_diff = {}
	for date in dates:
		try:
			month = date.split('-')[1]
			sheet_date = datetime.strptime(
				date.replace(month, converted_month_dict.get(month,month)), "%d-%m-%Y"
			)
			diff = (sheet_date - config_date).days
			if diff > 0:
				continue
			day_diff[date] = diff
		except Exception:
			continue
	if day_diff:
		week = max(day_diff, key=day_diff.get)
	else:
		if 'lat' in dates:
			week = '03-Mar-2022'
		else:
			week = '03-03-2022'

	return week