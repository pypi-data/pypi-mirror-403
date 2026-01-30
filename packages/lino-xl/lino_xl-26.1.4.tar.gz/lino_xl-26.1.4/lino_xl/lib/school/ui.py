# -*- coding: UTF-8 -*-
# Copyright 2024-2025 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

from django.db import models
from django.conf import settings
from django.utils.html import mark_safe
from etgen import html as xghtml
# from lino.utils.html import E, join_elems, tostring, SAFE_EMPTY
from lino.core import constants
from lino.core import actions
from lino.modlib.users.mixins import UserAuthored, My
from lino.modlib.system.choicelists import DisplayColors
from lino.modlib.periods.choicelists import PeriodStates
from lino.mixins import Referrable, Sequenced, Created
from lino.api import dd, rt, _, gettext

from .roles import PrimaStaff, PrimaTeacher, PrimaPupil


FIXED_6339 = False  # 6339 (Actor.hide_editing() doesn't work well under React)


class Grades(dd.Table):
    required_roles = dd.login_required(PrimaStaff)
    model = 'school.Grade'
    detail_layout = """
    id ref cert_template
    designation
    rating_conditions
    projects.ProjectTemplatesByGrade GroupsByGrade
    """


class SubjectDetail(dd.DetailLayout):
    main = "general CoursesBySubject"
    general = dd.Panel("""
    designation id advanced
    icon_text image_file rating_type
    SkillsBySubject
    """, _("General"))


class Subjects(dd.Table):
    required_roles = dd.login_required(PrimaStaff)
    model = 'school.Subject'
    detail_layout = "school.SubjectDetail"
    column_names = "seqno designation advanced icon_text rating_type image_file *"


class Skills(dd.Table):
    required_roles = dd.login_required(PrimaStaff)
    model = 'school.Skill'
    detail_layout = """
    designation id
    subject with_final_exams #with_smilies
    projects.ProjectTemplatesBySkill ratings.ChallengesBySkill cert.RatingsBySkill
    """


class SkillsBySubject(Skills):
    master_key = "subject"
    column_names = "designation with_final_exams *"
    default_display_modes = {None: constants.DISPLAY_MODE_GRID}


class GroupDetail(dd.DetailLayout):
    main = "general #ratings.ExamsByGroup ratings.SummariesByGroup ratings.FinalExamsByGroup certs more "

    general = dd.Panel("""
    CoursesByGroup
    pupils_and_projects
    # projects.PupilsAndProjectsByGroup
    """, _("General"))

    certs = dd.Panel("""
    body
    EnrolmentsByGroup
    """, _("Certificates"))

    # scores = dd.Panel("""
    # ratings.SkillsByGroup
    # ratings.ChallengeScoresByGroup ratings.PupilScoresByGroup
    # """, _("Scores"))

    more = dd.Panel("""
    designation
    year grade id
    CastsByGroup
    # ExamsByGroup
    """, _("More"))


class Groups(dd.Table):
    abstract = True
    required_roles = dd.login_required((PrimaTeacher, PrimaPupil))
    model = 'school.Group'
    # allow_create = False
    # allow_delete = False
    detail_layout = "school.GroupDetail"
    insert_layout = """
    designation
    grade year
    """
    column_names = "designation grade year id *"
    # default_display_modes = {None: constants.DISPLAY_MODE_SUMMARY}
    parameters = dict(
        teacher=dd.ForeignKey('users.User', verbose_name=_(
            "Teacher"), blank=True, null=True),
        pupil=dd.ForeignKey('users.User', verbose_name=_(
            "Pupil"), blank=True, null=True)
    )


class AllGroups(Groups):
    required_roles = dd.login_required(PrimaStaff)
    # allow_create = True
    # allow_delete = True


class GroupsByGrade(Groups):
    master_key = "grade"

# class GroupsByTeacher(Groups):
#     master_key = "cast__user"


class MyGroups(Groups):
    label = _("My groups")
    # default_display_modes = {None: constants.DISPLAY_MODE_LIST}
    default_display_modes = {None: constants.DISPLAY_MODE_TILES}
    editable = False
    preview_limit = 100
    allow_create = False
    # hide_top_toolbar = True

    @classmethod
    def param_defaults(self, ar, **kw):
        kw = super().param_defaults(ar, **kw)
        me = ar.get_user()
        if me.user_type.has_required_roles([dd.SiteAdmin]):
            return kw
        if me.user_type.has_required_roles([PrimaTeacher]):
            kw["teacher"] = me
        elif me.user_type.has_required_roles([PrimaPupil]):
            kw["pupil"] = me.partner.get_person()
        return kw

    @classmethod
    def get_request_queryset(self, ar, **filter):
        qs = super().get_request_queryset(ar, **filter)
        qs = qs.filter(models.Q(year__state=PeriodStates.open))
        qs = qs.exclude(grade__isnull=True)
        if (pv := ar.param_values) is None:
            return qs
        # raise Exception(f"20241210 {pv}")
        if pv.teacher is not None:
            qs = qs.filter(cast__user=pv.teacher).distinct()
        if pv.pupil is not None:
            qs = qs.filter(enrolments_by_group__pupil=pv.pupil).distinct()
        # print(f"20241016 {qs.explain()}")
        # print(f"20241016 {qs.query}")
        return qs

    @classmethod
    def row_as_paragraph(cls, ar, row):
        s = ar.obj2htmls(row)
        sar = CoursesByGroup.create_request(row, parent=ar)
        items = [sar.obj2htmls(o) for o in sar]
        if len(items):
            s += ": " + ", ".join(items)
        # else:
        #     s += ": " + _("No courses in {group}").format(group=row)
        return mark_safe(s)


class Roles(dd.Table):
    required_roles = dd.login_required(PrimaStaff)
    model = 'school.Role'
    column_names = "designation id *"
    detail_layout = """
    designation
    CastsByRole
    """


class CourseDetail(dd.DetailLayout):
    main = "ratings.ExamsByCourse ratings.SummariesByCourse ratings.FinalExamsByCourse cert.SectionResponsesByCourse more"
    # general = dd.Panel("""
    # ratings.ExamsByCourse #ratings.RatingsByCourse
    # """, label=_("General"))

    # summaries = dd.Panel("""
    # ratings.SummariesByCourse
    # """, _("Summaries"))

    more = dd.Panel("""
    group subject
    body
    """, _("More"))


class Courses(dd.Table):
    model = 'school.Course'
    required_roles = dd.login_required(PrimaTeacher)
    abstract = True
    detail_layout = "school.CourseDetail"
    insert_layout = """
    group
    subject
    """

    if FIXED_6339:

        @classmethod
        def hide_editing(cls, user_type):
            if not user_type.has_required_roles([PrimaStaff]):
                return True
            return super().hide_editing(user_type)
    else:

        @classmethod
        def get_insert_action(cls):
            return actions.ShowInsert(required_roles=dd.login_required(PrimaStaff))

        @classmethod
        def get_delete_action(cls):
            return actions.DeleteSelected(required_roles=dd.login_required(PrimaStaff))


class AllCourses(Courses):
    required_roles = dd.login_required(PrimaStaff)


class CoursesByGroup(Courses):
    master_key = "group"
    # label = _("Subjects given")
    order_by = ['subject']
    default_display_modes = {None: constants.DISPLAY_MODE_SUMMARY}

    # @classmethod
    # def get_parent_links(cls, ar):
    #     mi = ar.master_instance
    #     if isinstance(mi, rt.models.school.Group):
    #         sar = rt.models.school.MyGroups.create_request(parent=ar)
    #         yield sar.obj2htmls(mi)


class CoursesBySubject(Courses):
    master_key = "subject"
    # label = _("Subjects given")
    order_by = ['subject']
    default_display_modes = {None: constants.DISPLAY_MODE_SUMMARY}


class Casts(dd.Table):
    required_roles = dd.login_required(PrimaStaff)
    model = 'school.Cast'
    # detail_layout = """
    # group #subject role user
    # #ratings.ExamsByCast
    # """


class CastsByGroup(Casts):
    required_roles = dd.login_required(PrimaTeacher)
    master_key = "group"
    stay_in_grid = True
    order_by = ['role', 'user']
    default_display_modes = {70: constants.DISPLAY_MODE_GRID,
                             None: constants.DISPLAY_MODE_SUMMARY}
    insert_layout = """
    role
    user
    """


class CastsByUser(Casts):
    required_roles = dd.login_required(PrimaStaff)
    master_key = "user"
    # label = _("Subjects given")
    default_display_modes = {None: constants.DISPLAY_MODE_SUMMARY}
    insert_layout = """
    group
    role
    #subject
    """


class CastsByRole(Casts):
    required_roles = dd.login_required(PrimaStaff)
    master_key = "role"
    # label = _("Subjects given")
    # default_display_modes = {None: constants.DISPLAY_MODE_GRID}
    insert_layout = """
    group
    user
    """

# class CastsBySubject(Casts):
#     required_roles = dd.login_required(PrimaTeacher)
#     master_key = "subject"
#     column_names = "user group role *"
#     # default_display_modes = { None: constants.DISPLAY_MODE_LIST}
#     default_display_modes = { None: constants.DISPLAY_MODE_GRID}
#     insert_layout = """
#     user
#     group
#     role
#     """

# Removed 20250323
# class MyCasts(Casts, My):
#     required_roles = dd.login_required(PrimaTeacher)
#     # default_display_modes = {None: constants.DISPLAY_MODE_LIST}
#     default_display_modes = {None: constants.DISPLAY_MODE_SUMMARY}
#     order_by = ['group__designation', 'user', 'role']
#     # order_by = ['group__designation', 'subject__seqno', 'user', 'role']
#     # group_by =
#
#     @classmethod
#     def param_defaults(self, ar, **kw):
#         kw = super().param_defaults(ar, **kw)
#         if ar.get_user().user_type.has_required_roles([dd.SiteAdmin]):
#             kw["user"] = None
#         return kw
#
#     @classmethod
#     def table_as_summary(self, ar):
#         groups = []
#         items = []
#         current_group = None
#         current_casts = []
#
#         # if ar.get_user().user_type.has_required_roles([dd.SiteAdmin]):
#         #     def castf(cast):
#         #         text = str(cast.role)
#         #         text += " " + _("by {teacher}").format(teacher=cast.user)
#         #         return text
#         # else:
#         #     def castf(cast):
#         #         text = str(cast.role)
#         #         if cast.role is not None:
#         #             text += " " + _("as {role}").format(role=cast.role)
#         #         # text += " " + _("in {group}").format(group=cast.group)
#         #         return text
#
#         def collect(cast):
#             # current_casts.append(ar.obj2html(cast, castf(cast)))
#             current_casts.append(ar.obj2html(cast))
#
#         def end_group():
#             items.append(E.li(ar.obj2html(current_group), ": ",
#                          *join_elems(current_casts, ", ")))
#         for cast in ar:
#             if cast.group == current_group:
#                 collect(cast)
#                 continue
#             if current_group is not None:
#                 end_group()
#                 current_casts = []
#             current_group = cast.group
#             collect(cast)
#         if current_group is not None:
#             end_group()
#         if len(items) == 0:
#             return SAFE_EMPTY
#         return tostring(E.ul(*items))


class EnrolmentDetail(dd.DetailLayout):
    main = "general ratings invoicing"
    general = dd.Panel("""
    pupil group successful
    projects.ProjectsByEnrolment cert.CertificatesByEnrolment
    """, _("General"))
    ratings = dd.Panel("""
    ratings.ChallengeRatingsByEnrolment ratings.FinalRatingsByEnrolment
    """, _("Ratings"))
    invoicing = dd.Panel("""
    invoicing_info
    """, _("Invoicing"))


class Enrolments(dd.Table):
    required_roles = dd.login_required(PrimaStaff)
    model = 'school.Enrolment'
    # default_display_modes = {None: constants.DISPLAY_MODE_SUMMARY}
    detail_layout = "school.EnrolmentDetail"
    column_names = "pupil group successful state workflow_buttons *"


class EnrolmentsByGroup(Enrolments):
    required_roles = dd.login_required(PrimaTeacher)
    master_key = "group"
    column_names = "pupil certificates successful workflow_buttons *"
    insert_layout = """
    pupil
    """
    stay_in_grid = True
    allow_delete = False


class EnrolmentsByPupil(Enrolments):
    required_roles = dd.login_required(PrimaPupil)
    master_key = "pupil"
    column_names = "group certificates successful *"
    default_display_modes = {None: constants.DISPLAY_MODE_SUMMARY}
    insert_layout = """
    group
    """
    stay_in_grid = True
    # allow_delete = False
