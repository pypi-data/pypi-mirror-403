#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File:                Ampel-plot/ampel-plot/ampel/model/PlotSpec.py
# License:             BSD-3-Clause
# Author:              valery brinnel <firstname.lastname@gmail.com>
# Date:                12.02.2021
# Last Modified Date:  15.11.2025
# Last Modified By:    valery brinnel <firstname.lastname@gmail.com>

import os
from matplotlib.figure import Figure
from typing import Any, Literal

from ampel.util.tag import merge_tags
from ampel.types import StockId, Tag, OneOrMany
from ampel.util.compression import TCompression
from ampel.base.AmpelBaseModel import AmpelBaseModel
from ampel.abstract.AbsIdMapper import AbsIdMapper
from ampel.base.AuxUnitRegister import AuxUnitRegister
from ampel.protocol.LoggerProtocol import LoggerProtocol
from ampel.content.NewSVGRecord import NewSVGRecord
from ampel.plot.create import fig_to_record


class PlotSpec(AmpelBaseModel):
	"""
	Specification for a plot's output.

	Covers metadata such as file name, title, tags, and figure text,
    rendering options like width and height, and storage settings such as
    compression or disk save paths. 

	If `id_mapper` is set (e.g. ZTFIdMapper) and a template contains 'stock',
	the native Ampel stock ID will be converted to the corresponding external ID.
	For this feature to work, an AmpelContext must have been loaded at least once.

	The optional parameter `disk_save` ensures that plots are also written to disk.
	By default, plots are saved into the database.

	Example configuration:
	{
		"tags": ["SALT", "SNCOSMO"],
		"file_name": "{stock}_{model}_fit.svg",
		"title": "{stock} {catalog} lightcurve fit",
		"width": 10,
		"height": 6,
		"id_mapper": "ZTFIdMapper",
		"disk_save": "/tmp/"
	}

	This will create a file called `/tmp/ZTF27dpytkhq_salt2_fit.svg` for a transient
	with internal ID 274878346346. The plot title will be
	"ZTF27dpytkhq Ned based lightcurve fit".

	It is the responsibility of the class using PlotSpec to ensure that
	the correct arguments are passed to `get_file_name()` or `get_title()`.
	For example, if the template is "plot_{stock}_{model}.svg",
	then `{'stock': 123, 'model': 'salt'}` must be provided.

	Examples:
	--------
	In []: a = PlotSpec(file_name="plot_{stock}_{model}_fit.svg")
	In []: a.get_file_name(stock=12345678, model="salt2")
	Out[]: 'plot_12345678_salt2_fit.svg'

	# Note the reversed order of placeholders
	In []: a = PlotSpec(file_name="plot_{model}_{stock}_fit.svg")
	In []: a.get_file_name(stock=12345678, model="salt2")
	Out[]: 'plot_salt2_12345678_fit.svg'

	# Example using id_mapper (error shown intentionally):
	In []: a = PlotSpec(file_name="plot_{model}_{stock}_fit.svg", id_mapper="ZTFIdMapper")
	---------------------------------------------------------------------------
	ValidationError: 1 validation error for PlotSpec
	id_mapper
		Unknown unit ZTFIdMapper (type=value_error)

	As mentioned above, an AmpelContext must be loaded once for ID mapping to work.
	In production this is handled automatically, but in a local notebook you may
	encounter this error if no context has been loaded.

	To fix the error:
	In []: ctx = DevAmpelContext.load("ampel_conf.yaml")

	Then:
	In []: a = PlotSpec(file_name="plot_{model}_{stock}_fit.svg", id_mapper="ZTFIdMapper")
	In []: a.get_file_name(stock=12345678, model="salt2")
	Out[]: 'plot_salt2_ZTF31aabrxlc_fit.svg'
	"""

	file_name: str
	title: str | None
	fig_include_title: bool | None
	fig_text: str | None  # for matplotlib
	tags: Tag | list[Tag] | None
	width: int | None
	height: int | None
	detached: bool = True
	id_mapper: str | type[AbsIdMapper] | None = None
	disk_save: str | None = None  # Local folder path
	mpl_kwargs: dict[str, Any] | None = None

	# 0: no compression, 'svg' value will be a string
	# 1: compression_behavior svg, 'svg' value will be compressed bytes (usage: store plots into db)
	# 2: compression_behavior svg and include uncompressed string into key 'svg_str'
	# (useful for saving plots into db and additionally to disk for offline analysis)
	compression_behavior: Literal[0, 1, 2] | None
	compression_alg: TCompression = "ZIP_BZIP2"
	compression_level: int = 9


	def create_record(self,
		mpl_fig: Figure,
		tag_complement: OneOrMany[Tag] | None = None,
		extra: dict[str, Any] | None = None,
		close: bool = True,
		logger: LoggerProtocol | None = None,
		**fmt_args
	) -> NewSVGRecord:
		"""
		Create a new SVG record from a matplotlib figure, applying the
		formatting rules defined in this PlotSpec instance.

		:param mpl_fig: The matplotlib figure to convert into an SVG record.
		:param tag_complement: Additional tags to merge with those defined in this PlotSpec.
		:param extra: Extra metadata to include in the record.
		:param close: Whether to close the matplotlib figure after conversion.
		:param logger: Logger instance for debug output.
		:param fmt_args: Keyword arguments used to render placeholders in
		 ``file_name``, ``title``, or ``fig_text``.

		 For example::

			 spec = PlotSpec(
				 file_name="plot_{stock}_{model}.svg",
				 title="Fit for {stock}"
			 )
			 spec.create_record(mpl_fig, stock=123, model="salt2")

		 This will produce a record with::

			 file_name = "plot_123_salt2.svg"
			 title     = "Fit for 123"

		:return: A record containing the SVG representation of the figure,
		along with metadata such as tags, compression settings,
		and optional disk save path.
		"""

		svg_doc = fig_to_record(
			mpl_fig,
			file_name = self.get_file_name(**fmt_args),
			title = self.get_title(**fmt_args),
			fig_include_title = self.fig_include_title,
			extra = extra,
			width = self.width,
			height = self.height,
			tags = self.tags if not tag_complement else merge_tags(self.tags, tag_complement),
			compression_behavior = self.get_compression_behavior(),
			compression_alg = self.compression_alg,
			compression_level = self.compression_level,
			detached = self.detached,
			logger = logger,
			close = close
		)

		if self.disk_save:
			fname = os.path.join(self.disk_save, self.get_file_name(**fmt_args))
			if logger and getattr(logger, "verbose", 0) > 1:
				logger.debug(f"Saving {fname}")
			with open(fname, "w") as f:
				f.write(
					svg_doc.pop("svg_str")  # type: ignore
					if self.get_compression_behavior() == 2
					else svg_doc['svg']
				)

		return svg_doc

	def get_file_name(self, **kwargs) -> str:
		return self._format_attr(self.file_name, **kwargs)

	def get_title(self, **kwargs) -> str | None:
		return self._format_attr(self.title, **kwargs) if self.title else None

	def get_fig_text(self, **kwargs) -> str | None:
		return self._format_attr(self.fig_text, **kwargs) if self.fig_text else None

	def get_compression_behavior(self) -> int:
		if self.compression_behavior is not None:
			return self.compression_behavior
		if self.disk_save:
			return 2
		return 1

	def _format_attr(self, template: str, **kwargs) -> str:
		if not template:
			return ""
		if "stock" in template and self.id_mapper and "stock" in kwargs:
			kwargs = kwargs.copy()
			kwargs["stock"] = self._get_ext_name(kwargs["stock"])
		try:
			return template.format(**kwargs)
		except KeyError as e:
			raise ValueError(f"Missing format argument: {e.args[0]}") from e

	def _get_ext_name(self, ampel_id: StockId) -> str:
		"""If no id mapper is available, the stringified ampel id is returned"""
		if self.id_mapper is None:
			return str(ampel_id)
		if isinstance(self.id_mapper, str):
			self.id_mapper = AuxUnitRegister.get_aux_class(self.id_mapper, sub_type=AbsIdMapper)
		return self.id_mapper.to_ext_id(ampel_id)
