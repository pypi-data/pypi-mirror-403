# -*- coding: UTF-8 -*-
# Copyright 2024-2025 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from django.utils.html import format_html, mark_safe
from django.utils.text import format_lazy
from lino.core import constants
from lino.utils.html import E, join_elems
from lino.utils import nextref
from lino.utils.mldbc.mixins import BabelDesignated
from lino.modlib.checkdata.choicelists import Checker
from lino.modlib.users.mixins import UserAuthored
from lino.mixins.clonable import Clonable
from lino.modlib.periods.choicelists import PeriodStates
from lino.modlib.memo.mixins import Previewable
from lino.modlib.printing.mixins import MultiCachedPrintable
from lino.mixins import Referrable, Sequenced
from lino_prima.lib.ratings.choicelists import RatingTypes
from lino_xl.lib.invoicing.mixins import InvoiceGenerator
from lino.api import dd, rt, pgettext, _
from .choicelists import EnrolmentStates
from .ui import *
from .roles import PrimaStaff


class Grade(BabelDesignated, Referrable):  # hard-coded list in zeugnisse
    class Meta:
        app_label = 'school'
        verbose_name = _("Grade")  # Jahrgangsstufe, Schulstufe
        verbose_name_plural = _("Grades")
        abstract = dd.is_abstract_model(__name__, 'Grade')

    cert_template = dd.ForeignKey(
        'cert.CertTemplate', blank=True, null=True)
    rating_conditions = dd.BabelTextField(_("Rating conditions"), blank=True)


class Subject(BabelDesignated, Sequenced):
    class Meta:
        app_label = 'school'
        verbose_name = pgettext("in school", "Subject")
        verbose_name_plural = _("Subjects")
        abstract = dd.is_abstract_model(__name__, 'Subject')
        ordering = ['seqno']
    advanced = dd.BooleanField(_("Advanced"), default=False)
    icon_text = dd.CharField(_("Icon"), max_length=5, blank=True, null=True)
    rating_type = RatingTypes.field(blank=True, null=True)
    if dd.is_installed("uploads"):
        image_file = dd.ForeignKey(
            'uploads.Upload', verbose_name=_("Image"), blank=True, null=True)
    else:
        image_file = dd.DummyField()


class Skill(BabelDesignated, Sequenced):
    class Meta:
        app_label = 'school'
        verbose_name = _("Skill")
        verbose_name_plural = _("Skills")
        abstract = dd.is_abstract_model(__name__, 'Skill')
    subject = dd.ForeignKey('school.Subject')
    with_final_exams = dd.BooleanField(_("With final exams"))  # Mit Abschlusstests

    # def __str__(self):
    #     return f"{self.subject}:{super().__str__()}"

    def get_siblings(self):
        return self.__class__.objects.filter(subject=self.subject)


class Group(BabelDesignated, MultiCachedPrintable, Previewable):
    # zeugnisse.Klasse
    class Meta:
        app_label = 'school'
        verbose_name = _("Group")
        verbose_name_plural = _("Groups")
        abstract = dd.is_abstract_model(__name__, 'Group')
        ordering = ['designation']

    quickfix_checkdata_label = _("Fill missing courses and certificates")
    extra_display_modes = {constants.DISPLAY_MODE_TILES}

    grade = dd.ForeignKey('school.Grade', blank=True, null=True)
    year = dd.ForeignKey('periods.StoredYear', blank=True)
    # remark = dd.BabelTextField(_("Remark"), blank=True)

    def get_print_period(self):
        # Return the first opened period of the year of this group. If this year
        # has no opened period at all, return the last closed period. Which just
        # means that the site admin should close the first period in order to
        # activate printing of the second period.
        periods = rt.models.periods.StoredPeriod.objects.filter(year=self.year)
        if (pp := periods.filter(state=PeriodStates.open).first()) is None:
            return periods.last()
        return pp

    def get_printable_target_stem(self):
        period = self.get_print_period()
        return f"{self._meta.verbose_name}-{period.ref}-{self.designation}"

    def get_printable_children(self):  # implements MultiCachedPrintable
        current = self.get_print_period()
        qs = rt.models.cert.Certificate.objects.filter(
            enrolment__group=self, period=current)
        qs = qs.order_by('enrolment__pupil__last_name', 'enrolment__pupil__id')
        return qs

    def on_duplicate(self, ar, master):
        if (next := self.year.get_next_row()):
            self.year = next
        # if (next := self.grade.get_next_row()):
        #     self.grade = next
        self.body = ""
        if self.grade is not None:
            self.grade = self.grade.get_next_row()
        if (next := nextref(self.designation)) is not None:
            self.designation = next
        else:
            self.designation += " (copy)"
        super().on_duplicate(ar, master)
        # ar.param_values['year'] = None

    # def after_duplicate(self, ar, old):
    #     # print("20250726", repr(old))
    #     self.check_summaries.run_from_ui(ar)

    # def on_create(self, ar):
    #     print(f"20250514 {ar} {ar.selected_rows}")
    #     pass

    @classmethod
    def get_simple_parameters(cls):
        yield super().get_simple_parameters()
        yield 'year'

    # @classmethod
    # def param_defaults(cls, ar, **kw):
    #     kw = super().param_defaults(ar, **kw)
    #     kw.update(year=rt.models.periods.StoredYear.get_or_create_from_date(
    #         dd.today()))
    #     return kw

    def full_clean(self, *args, **kwargs):
        if self.year_id is None:
            self.year = rt.models.periods.StoredYear.get_or_create_from_date(dd.today())
        super().full_clean(*args, **kwargs)

    def as_tile(self, ar, prev, **kwargs):
        s = f"""<span style="font-size:2rem; float:left; padding-right:1rem;">{
            ar.obj2htmls(self)}</span> """
        s += _("{} pupils").format(Enrolment.objects.filter(group=self).count())
        s += "<br>"
        sar = rt.models.school.CoursesByGroup.create_request(
            parent=ar, master_instance=self)
        s += " ".join([
            sar.obj2htmls(
                obj, obj.subject.icon_text or str(obj.subject), title=str(obj.subject))
            for obj in sar])
        s = constants.TILE_TEMPLATE.format(chunk=s)
        if prev is not None and prev.grade != self.grade:
            s = """<p style="display:block;"></p>""" + s
        return mark_safe(s)

    def as_paragraph(self, ar, **kwargs):
        s = ar.obj2htmls(self)
        if not ar.is_obvious_field("year"):
            s += format_html(_(" ({year})"), year=str(self.year))
        return mark_safe(s)

    def __str__(self):
        s = super().__str__()
        if not self.year.covers_date(dd.today()):
            s += format_html(_(" ({year})"), year=self.year)
        return mark_safe(s)

    def get_detail_action(self, ar):
        if ar is not None:
            return rt.models.school.MyGroups.detail_action
            # return rt.models.school.MyGroups.get_request_detail_action(ar)
        return super().get_detail_action(ar)

    @dd.delayedhtmlbox(verbose_name=_("Projects"), default=None)
    def pupils_and_projects(self, ar):
        if ar is None:
            return None
        return pupils_and_projects(self, ar)

    def teachers_and_roles(self):
        qs = rt.models.school.Cast.objects.filter(group=self)
        rv = ""
        last_role = None
        for cast in qs.order_by('role', 'user__last_name'):
            if cast.role != last_role:
                if rv:
                    rv += "; "
                rv += str(cast.role) + ": "
                last_role == cast.role
            elif rv:
                rv += ", "
            rv += cast.user.first_name + " " + cast.user.last_name.upper()
        return rv


def pupils_and_projects(grp, ar):
    ProjectTemplate = rt.models.projects.ProjectTemplate
    Enrolment = rt.models.school.Enrolment
    Project = rt.models.projects.Project
    ProjectsByEnrolment = rt.models.projects.ProjectsByEnrolment
    # grp = ar.master_instance
    # print(f"20241017 cellattrs {ar.renderer.cellattrs}")
    templates = ProjectTemplate.objects.filter(
        grade=grp.grade).order_by("display_color")
    if not templates.exists():
        return _("There are no {projects} configured for grade {grade}.").format(
            projects=Project._meta.verbose_name_plural, grade=grp.grade)

    cellstyle = "padding:2pt; margin:0pt; text-align:center;"
    insert_button_attrs = dict(style="text-align:center;")

    def makecell(sar, tpl):
        qs = Project.objects.filter(
            enrolment=sar.master_instance, template=tpl)
        n = qs.count()
        if n == 0:
            btn = sar.gen_insert_button(None, insert_button_attrs,
                                        template=str(tpl), templateHidden=tpl.pk)
            if btn is None:
                return ""
            return E.td(btn, style=cellstyle)
            # return E.p(txt, btn, align="center")
            # return str("+")
        if n > 1:
            ar2 = rt.models.projects.ProjectsByEnrolment.create_request(
                sar.master_instance, param_values=dict(template=tpl), parent=ar)
            return E.td(ar2.ar2button(label="?!"), style=cellstyle+"background-color:lightblue;")
        prj = qs.first()
        ratings = prj.get_general_ratings()
        if ratings.done == ratings.todo:
            color = "#48c78e"
            txt = "☑"  # U+2611
        else:
            color = "#ffe08a"
            txt = "⚒"  # U+2692
        if False:
            if prj.total_max_score:
                score = format_score(100 * prj.total_score /
                                     prj.total_max_score) + "%"
            else:
                score = NOT_RATED
            if prj.ratings_done is None:
                cv = 0
            else:
                cv = int(prj.ratings_done / 20)  # a value 0..5
            # completion = "▇" * cv + "▁" * (5-cv)
            # completion = "|" * cv + "." * (5-cv)
            completion = "▮" * cv + "▯" * (5-cv)
            txt = f"{completion} {score}"
        return E.td(sar.obj2html(prj, txt),
                    style=cellstyle + "background-color:" + color)

    table = xghtml.Table()
    table.attrib.update(ar.renderer.tableattrs)
    headers = [E.td(gettext("Pupil"))]
    # cellstyle = "text-align:center;"
    for prj in templates:
        # print(f"20241017 {prj.display_color}")
        # headers.append(E.td(
        #     ar.obj2html(prj, prj.short_header,
        #         style=f"color:{prj.display_color.font_color};"),
        #     style=cellstyle + f"background-color:{prj.display_color.name};"))
        # headers.append(E.td(
        #     ar.obj2html(prj, prj.short_header),
        #     style=cellstyle + f"background-color:{prj.display_color.name};color:{prj.display_color.font_color};"))
        headers.append(E.td(prj.short_header,
                            style=cellstyle + f"background-color:{prj.display_color.name};color:{prj.display_color.font_color};"))
    table.head.append(E.tr(*headers))
    for enr in Enrolment.objects.filter(group=grp):
        sar = ProjectsByEnrolment.create_request(parent=ar, master_instance=enr)
        cells = [E.td(ar.obj2html(enr, str(enr.pupil)))]
        for prj in templates:
            cells.append(makecell(sar, prj))
        table.body.append(E.tr(*cells))

    el = table.as_element()
    # if len(toolbar := ar.plain_toolbar_buttons()):
    #     el = E.div(el, E.p(*toolbar))
    return el


dd.update_field(Group, 'body', verbose_name=_("Remark"))
dd.update_field(Group, 'body_short_preview', verbose_name=_("Remark"))

Group.clone_row.required_roles = {dd.SiteAdmin}


class Course(Previewable):
    class Meta:
        app_label = 'school'
        verbose_name = _("Course")
        verbose_name_plural = _("Courses")
        abstract = dd.is_abstract_model(__name__, 'Course')
        ordering = ['group', 'subject__seqno']

    group = dd.ForeignKey('school.Group', related_name='courses')
    subject = dd.ForeignKey('school.Subject', related_name='courses')
    # remark = dd.BabelTextField(_("Remark"), blank=True)
    quick_search_fields = "subject__designation"

    allow_cascaded_delete = ['group']

    def __str__(self):
        return _("{subject} in {group}").format(
            subject=self.subject, group=self.group)

    def get_str_words(self, ar):
        if not ar.is_obvious_field("subject"):
            yield str(self.subject)
        if not ar.is_obvious_field("group"):
            yield _("in {group}").format(group=self.group)

    def get_skill_choices(self):
        if self.subject is not None:
            return rt.models.school.Skill.objects.filter(subject=self.subject)
        return rt.models.school.Skill.objects.all()

    def get_parent_links(self, ar):
        if self.group:
            # sar = rt.models.school.MyGroups.create_request(parent=ar)
            yield ar.obj2htmls(self.group)

    # def disabled_fields(self, ar):
    #     df = super().disabled_fields(ar)
    #     if not ar.has_required_roles(PrimaStaff):
    #         df.add("insert")
    #         df.add("delete")


dd.update_field(Course, 'body', verbose_name=_("Remark"))
dd.update_field(Course, 'body_short_preview', verbose_name=_("Remark"))


class Role(BabelDesignated):
    class Meta:
        app_label = 'school'
        verbose_name = _("Role")
        verbose_name_plural = _("Roles")
        abstract = dd.is_abstract_model(__name__, 'Role')


class Cast(dd.Model):  # zeugnisse.LehrerRolle

    class Meta:
        app_label = 'school'
        verbose_name = _("Cast")
        verbose_name_plural = _("Casts")
        abstract = dd.is_abstract_model(__name__, 'Cast')
        # ordering = ['user', 'group__designation', 'subject', 'role']
        ordering = ['user', 'group__designation', 'role']
        # unique_together = ['user', 'group', 'role']

    user = dd.ForeignKey(
        "users.User",
        verbose_name=_("Teacher"),
        related_name="%(app_label)s_%(class)s_set_by_user",
        blank=True,
        null=True)
    group = dd.ForeignKey('school.Group')
    # subject = dd.ForeignKey('school.Subject')
    role = dd.ForeignKey('school.Role', blank=True, null=True)

    # allow_cascaded_delete = ['group']
    # We do NOT want the casts of a group to get copied to the next year when we
    # duplicate a group

    def __str__(self):
        # text = str(self.subject)
        text = str(self.user)
        if self.role is not None:
            text += " " + _("as {role}").format(role=self.role)
        text += " " + _("in {group}").format(group=self.group)
        return text

    def get_str_words(self, ar):
        if ar.is_obvious_field("group"):
            yield "{}: {}".format(self.role, self.user)
            # yield format_html("{}: {}", self.role, ar.obj2htmls(self.user))
            return
        if not ar.is_obvious_field("user"):
            yield _("{teacher} as").format(teacher=self.user)
        yield str(self.role)
        yield _("in {group}").format(group=self.group)

    @classmethod
    def get_simple_parameters(cls):
        yield super().get_simple_parameters()
        yield "user"  # cls.author_field_name)
        yield 'group__year'

    # @classmethod
    # def param_defaults(cls, ar, **kw):
    #     kw = super().param_defaults(ar, **kw)
    #     kw.update(group__year=rt.models.periods.StoredYear.get_or_create_from_date(
    #         dd.today()))
    #     return kw


# dd.update_field(Cast, 'user', verbose_name=_("Teacher"))


class Enrolment(InvoiceGenerator):

    class Meta:
        app_label = 'school'
        verbose_name = _("Enrolment")
        verbose_name_plural = _("Enrolments")
        abstract = dd.is_abstract_model(__name__, 'Enrolment')
        ordering = ['pupil__last_name', 'pupil__first_name', 'group__year', 'id']

    group = dd.ForeignKey('school.Group', related_name='enrolments_by_group')
    pupil = dd.ForeignKey(dd.plugins.school.pupil_model, verbose_name=_("Pupil"))
    successful = dd.YesNo.field(_("Successful"), blank=True)
    state = EnrolmentStates.field(default="draft")

    quick_search_fields = ['pupil__last_name', 'pupil__first_name']
    workflow_state_field = 'state'
    allow_cascaded_delete = ['group']
    # IOW When end user deletes a group, Lino removes all enrolments
    # automatically, but Lino will veto when user tries to delete a pupil for
    # which there is an enrolment.

    def __str__(self):
        return f"{self.pupil} ({self.group})"
    
    def get_invoiceable_end_date(self):
        return self.group.year.end_date
    
    def get_invoiceable_partner(self):
        """Return the partner who will receive the invoice.
        Override this method if you need custom logic to determine the invoice recipient.
        """
        # Default: invoice the pupil. Override if you need invoice to go to parent/guardian
        return dd.plugins.school.get_invoiceable_partner(self.pupil)
    
    def get_invoiceable_product(self, max_date=None):
        """Return the product/service to invoice for this enrolment.
        Override this to link enrolments to specific products in your products catalog.
        """
        # You need to configure this based on your site's product structure
        # Example: return a product based on the grade or group
        if self.group and (grade := self.group.grade):
            Product = rt.models.products.Product
            return Product.objects.filter(name=f"Grade {grade.ref} Tuition").first()
        return None
    
    def get_invoiceable_qty(self):
        """Return the quantity to invoice."""
        # Default: 1 enrolment = 1 invoice item
        return self.default_invoiceable_qty
    
    def get_invoiceable_title(self, number=None):
        """Return the title/description for the invoice item."""
        return _("{pupil} - {group} ({year})").format(
            pupil=self.pupil,
            group=self.group,
            year=self.group.year
        )
    
    @classmethod
    def get_generators_for_plan(cls, plan, partner=None):
        qs = super().get_generators_for_plan(plan, partner)
        if partner is None:
            partner = plan.partner
        if partner is not None:
            qs = cls.filter_by_invoice_recipient(qs, partner,
                dd.plugins.school.enrolment_invoiceable_partner_field)
        return qs
    
    @dd.action(show_in_toolbar=True, icon_name='money',
               required_roles=dd.login_required(PrimaStaff))
    def create_invoice(self, ar):
        """Create an invoice for this enrolment."""
        if not dd.is_installed('invoicing'):
            raise Warning(_("The invoicing plugin is not installed."))
        
        partner = self.get_invoiceable_partner()
        if partner is None:
            raise Warning(_(
                "Cannot create invoice: no invoiceable partner configured."))
        
        product = self.get_invoiceable_product(dd.today())
        if product is None:
            raise Warning(_(
                "Cannot create invoice: no invoiceable product configured. "
                "Please configure a product for school enrolments."))
        
        # Get the invoicing task for school enrolments
        # You'll need to configure this in your site's fixtures/demo data
        Task = rt.models.invoicing.Task
        task = Task.objects.filter(
            target_journal__ref='SLS'
        ).first()
        
        if task is None:
            raise Warning(_(
                "Cannot create invoice: no invoicing task configured. "
                "Please configure an invoicing task with a target journal "
                "for sales invoices."))
        
        # Create the plan
        Plan = rt.models.invoicing.Plan
        plan = Plan(user=ar.get_user(), invoicing_task=task)
        plan.full_clean()
        plan.save()
        
        # Create an invoice item for this enrolment
        info = self.compute_invoicing_info(None, dd.today())
        InvoicingItem = rt.models.invoicing.Item
        item = InvoicingItem(
            plan=plan,
            partner=partner,
            generator_type=rt.models.contenttypes.ContentType.objects.get_for_model(self.__class__),
            generator_id=self.pk,
            selected=True
        )
        item.full_clean()
        item.save()
        
        # Execute the item to create the actual invoice
        invoice = item.create_invoice(ar)

        # sar = invoice.get_default_table().request(selected_rows=[invoice], parent=ar, master_instance=invoice.journal)
        # js = ar.renderer.instance_handler(sar, invoice, None)
        # ar.set_response(eval_js=js)

        sar.goto_instance(invoice)
        
        ar.success(_(
            "Invoice created for {enrolment}.").format(enrolment=self),
            refresh=True)

    def get_str_words(self, ar):
        if not ar.is_obvious_field("pupil"):
            yield str(self.pupil)
        if not ar.is_obvious_field("group"):
            yield _("in {group}").format(group=self.group)

    # def as_summary_item(self, ar, text=None):
    #     if text is None:
    #         if ar.is_obvious_field("pupil"):
    #             text = f"{self.group}"
    #         elif ar.is_obvious_field("group"):
    #             text = f"{self.pupil}"
    #         else:
    #             text = str(self)
    #     return super().as_summary_item(ar, text)

    def get_parent_links(self, ar):
        if self.group:
            # sar = rt.models.school.MyGroups.create_request(parent=ar)
            yield ar.obj2htmls(self.group)

    @dd.displayfield(_("Certificates"))
    def certificates(self, ar):
        if ar is None:
            return ''
        Certificate = rt.models.cert.Certificate
        elems = []
        sar = rt.models.cert.CertificatesByEnrolment.create_request(
            parent=ar, master_instance=self)
        if True:
            qs = Certificate.objects.filter(
                enrolment=self, period__year=self.group.year)
            for crt in qs:
                elems.append(sar.obj2html(crt, crt.period.nickname))
        else:
            insert_button_attrs = dict(style="text-align: center;")
            qs = rt.models.periods.StoredPeriod.objects.filter(year=self.group.year)
            for p in qs:
                try:
                    crt = Certificate.objects.get(enrolment=self, period=p)
                except Certificate.DoesNotExist:
                    btn = sar.gen_insert_button(None, insert_button_attrs,
                                                enrolment=str(self), enrolmentHidden=self.pk,
                                                period=str(p), periodHidden=p.pk)
                    if btn is not None:
                        elems.append(btn)
                    continue
                elems.append(sar.obj2html(crt, p.nickname))
        return E.p(*join_elems(elems, sep=", "))

    def disable_delete(self, ar=None):
        if ar and not ar.get_user().user_type.has_required_roles([PrimaStaff]):
            return _("Cannot delete ")
        return super().disable_delete(ar)


class GroupChecker(Checker):
    verbose_name = _("Check for missing courses")
    model = Group
    msg_missing = _("No course for {subject} in {group}.")

    def get_checkdata_problems(self, ar, obj, fix=False):
        CertSection = rt.models.cert.CertSection
        if obj.grade is None:
            return
        tpl = obj.grade.cert_template
        for cs in CertSection.objects.filter(cert_template=tpl):
            if cs.subject_id and cs.subject.advanced:
                qs = Course.objects.filter(group=obj, subject=cs.subject)
                if not qs.exists():
                    yield (True, format_lazy(
                        self.msg_missing, subject=cs.subject, group=obj))
                    if fix:
                        course = Course(subject=cs.subject, group=obj)
                        course.full_clean()
                        course.save()


GroupChecker.activate()


@dd.receiver(dd.post_analyze)
def my_details(sender, **kw):
    sender.models.system.SiteConfigs.set_detail_layout("""
    default_build_method
    simulate_today
    """)
