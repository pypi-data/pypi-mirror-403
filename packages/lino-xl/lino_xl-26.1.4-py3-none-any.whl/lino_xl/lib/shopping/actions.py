# -*- coding: UTF-8 -*-
# Copyright 2026 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)


from lino.api import dd, rt, _


class StartOrder(dd.Action):
    label = _("Start order")
    icon_name = "money"
    sort_index = 53

    def run_from_ui(self, ar, **kw):
        # for plan in ar.selected_rows:
        plan = ar.selected_rows[0]
        plan.run_start_order(ar)
        ar.success(refresh=True)


class AddToCart(dd.Action):
    label = _("Add to cart")
    button_text = " 🛒 "  # (U+1F6D2)

    # icon_name = 'lightning'

    def run_from_ui(self, ar):
        my_cart = rt.models.shopping.Cart.create_user_plan(ar.get_user())
        texts = []
        CartItem = rt.models.shopping.CartItem
        for obj in ar.selected_rows:
            texts.append(str(obj))
            qs = CartItem.objects.filter(cart=my_cart, product=obj)
            if qs.count() == 0:
                cart_item = CartItem(cart=my_cart, product=obj, qty=1)
            else:
                cart_item = qs.first()
                cart_item.qty += 1
            cart_item.full_clean()
            if not ar.xcallback_answers:  # because this is called again after confirm
                cart_item.save()

        def ok(ar2):
            ar2.goto_instance(my_cart)

        msg = _("{} has been placed to your shopping cart. Proceed to payment now?")
        ar.confirm(ok, msg.format(", ".join(texts)))
