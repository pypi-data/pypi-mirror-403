# -*- coding: UTF-8 -*-
# Copyright 2026 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from lino.api import dd, rt, _


class CartItemMixin(dd.Model):
    """Mixin to add to a :class:`lino_xl.lib.shopping.models.CartItem`
    to make it compatible with invoicing.

    """

    class Meta:
        abstract = True

    product = dd.ForeignKey("products.Product", blank=True, null=True)
    qty = dd.QuantityField(_("Quantity"), blank=True, null=True)
