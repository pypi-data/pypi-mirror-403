# -*- coding: UTF-8 -*-
# Copyright 2024 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from django.utils.text import format_lazy
from lino.api import dd, _, pgettext


class EnrolmentStates(dd.Workflow):
    verbose_name = _("Enrolment state")
    verbose_name_plural = _("Enrolment states")


add = EnrolmentStates.add_item
add('10', _("Draft"), "draft", button_text="☐")  # ⚹
add('20', _("Talk"), "talk", button_text="☎")
add('30', _("Done"), "done", button_text="☑")

EnrolmentStates.draft.add_transition()
EnrolmentStates.talk.add_transition()
EnrolmentStates.done.add_transition()
