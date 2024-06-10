from pyomo.core import Constraint
import numpy as np

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
