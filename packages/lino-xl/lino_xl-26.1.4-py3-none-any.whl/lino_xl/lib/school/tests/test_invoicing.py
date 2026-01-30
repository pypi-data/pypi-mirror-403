# -*- coding: UTF-8 -*-
# Copyright 2025 Rumma & Ko Ltd
# License: GNU Affero General Public License v3 (see file COPYING for details)

"""
Tests for invoice generation from enrolments.

To run this test:
    $ pytest lino_xl/lib/school/tests/test_invoicing.py
"""

from lino.api import rt, dd


def test_enrolment_invoicing_methods():
    """Test that Enrolment has the required invoicing methods."""
    Enrolment = rt.models.school.Enrolment
    
    # Check that InvoiceGenerator methods exist
    assert hasattr(Enrolment, 'get_invoiceable_partner')
    assert hasattr(Enrolment, 'get_invoiceable_product')
    assert hasattr(Enrolment, 'get_invoiceable_qty')
    assert hasattr(Enrolment, 'get_invoiceable_title')
    assert hasattr(Enrolment, 'get_invoiceable_end_date')
    assert hasattr(Enrolment, 'create_invoice')
    assert hasattr(Enrolment, 'compute_invoicing_info')
    
    # Check target_voucher_model is set
    assert Enrolment.target_voucher_model is not None


def test_enrolment_invoicing_info(client):
    """Test that invoicing info can be computed."""
    if not dd.is_installed('invoicing'):
        return  # Skip if invoicing not installed
    
    # Create a simple enrolment
    Group = rt.models.school.Group
    User = rt.models.users.User
    StoredYear = rt.models.periods.StoredYear
    
    # Get or create required objects
    year = StoredYear.get_or_create_from_date(dd.today())
    pupil = User.objects.filter(user_type__pupil=True).first()
    
    if not pupil:
        pupil = User(username='testpupil', first_name='Test', last_name='Pupil')
        pupil.full_clean()
        pupil.save()
    
    group = Group.objects.first()
    if not group:
        group = Group(designation='Test Group', year=year)
        group.full_clean()
        group.save()
    
    Enrolment = rt.models.school.Enrolment
    enrolment = Enrolment(pupil=pupil, group=group)
    enrolment.full_clean()
    enrolment.save()
    
    # Test invoicing info computation
    info = enrolment.compute_invoicing_info(None, dd.today())
    assert info is not None
    assert info.generator == enrolment
    
    # Test other methods
    assert enrolment.get_invoiceable_qty() == 1
    assert enrolment.get_invoiceable_end_date() == group.year.end_date
    assert enrolment.get_invoiceable_title() is not None


def test_enrolment_invoice_action_exists():
    """Test that the create_invoice action is registered."""
    Enrolment = rt.models.school.Enrolment
    
    # Check action is registered
    actions = Enrolment.get_actions()
    assert 'create_invoice' in [a.action.action_name for a in actions]
    
    # Get the action
    ba = Enrolment.get_action_by_name('create_invoice')
    assert ba is not None
    assert ba.action.icon_name == 'money'
    assert ba.action.show_in_toolbar is True


def test_enrolment_tables_show_invoice_actions():
    """Test that enrolment tables expose the invoice action."""
    EnrolmentsByGroup = rt.models.school.EnrolmentsByGroup
    
    # Check column names include the action
    column_names = str(EnrolmentsByGroup.column_names)
    assert 'create_invoice' in column_names
    
    # Check the detail layout includes invoicing panel
    Enrolments = rt.models.school.Enrolments
    dl = Enrolments.detail_layout
    assert 'invoicing' in dl.main
