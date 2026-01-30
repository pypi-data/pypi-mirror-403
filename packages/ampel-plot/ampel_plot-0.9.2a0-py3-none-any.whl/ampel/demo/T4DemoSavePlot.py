#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/demo/T4DemoSavePlot.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                25.07.2022
# Last Modified Date:  16.11.2025
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import matplotlib.pyplot as plt
from random import random, randrange
from ampel.types import UBson
from ampel.struct.UnitResult import UnitResult
from ampel.abstract.AbsT4Unit import AbsT4Unit
from ampel.enum.DocumentCode import DocumentCode
from ampel.model.PlotSpec import PlotSpec


class T4DemoSavePlot(AbsT4Unit):

	plot: PlotSpec = PlotSpec(
		tags = ["DEMO_PLOT"],
		file_name = "plot_{first_suffix}_{second_suffix}.svg",
		title = "A title - {first_arg}\n{second_arg}"
	)

	def do(self) -> UBson | UnitResult:

		fig, ax = plt.subplots()
		x = [random() for _ in range(20)]
		y = [randrange(-50, 50) / 100 for _ in range(20)]
		dy = [randrange(0, 10) / 100 for _ in range(20)]
		ax.scatter(x, y, s=10, zorder=20)
		ax.errorbar(x, y, yerr=dy, fmt="o", ms=0, zorder=10, color='darkgrey')
		ax.axhline(y=0, color='black', linestyle='-')
		ax.set_xlabel('Demo x-label')
		ax.set_ylabel('Demo y-label')

		try:
			plot_record = self.plot.create_record(
				fig,
				logger = self.logger,
				first_suffix = "one",
				second_suffix = "two",
				first_arg = "foo",
				second_arg = "bar"
			)
			return UnitResult(body={"plot": plot_record})
			# return {"plot": plot_record}  <- would work too
		except Exception as e:
			self.logger.error("Plot creation failed", exc_info=e)
			return UnitResult(body={"error": str(e)}, code=DocumentCode.EXCEPTION)
		finally:
			plt.close(fig) # avoid figure accumulation
