from flask import Blueprint, request, render_template, current_app, redirect, url_for, flash, jsonify, abort, session
from emblnk.models import (Campaign, Contact, List, generate_unique_slug, CampaignTracking,
                        CampaignRecipient, User, Senders)
from flask_login import current_user, login_required
from emblnk.main.forms import UploadContacts, MapContactsForm, AddContact, CreateContactList
from emblnk.main.upload_contacts import UploadContact, MapContacts
from emblnk import db
import secrets
import os
import re
import pandas as pd

main = Blueprint('main', __name__)

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def save_file(file_data):
    random_hex = secrets.token_hex(8)
    root, extension = os.path.splitext(file_data.filename)
    file_fn = random_hex+extension
    file_path = os.path.join(current_app.root_path, 'static/files', file_fn)
    file_data.save(str(file_path))
    return file_fn

@main.route('/dashboard')
@main.route('/home')
@main.route('/')
@login_required
def home():
    campaigns = Campaign.query.filter_by(user=current_user).all()
    contacts = Contact.query.filter_by(user=current_user).all()
    senders = None
    total_contacts = len(contacts)
    total_campaigns = len(campaigns)
    unsubcribes = Contact.query.filter_by(subscribed=False, user=current_user).all()
    total_unsubcribes = len(unsubcribes)
    return render_template('main/home.html', active_page='home', title='Dashboard',
                           total_campaigns=total_campaigns, total_contacts=total_contacts,
                           total_unsubcribes=total_unsubcribes, campaigns=campaigns,
                           contacts=contacts)


@main.route('/contacts/', methods=['GET', 'POST'])
@login_required
def contacts():
    contacts = Contact.query.filter_by(user=current_user).all()[:]
    lists = List.query.filter_by(user=current_user).all()
    last_row_id = Contact.query.filter_by(user=current_user).order_by(Contact.contact_id.desc()).first()
    if last_row_id:
        last_row_id = last_row_id.contact_id
    form = AddContact()
    form.usr = current_user
    if request.method == 'POST':
        if form.validate_on_submit():
            contact = Contact(email=form.email.data, first_name=form.first_name.data,
                            last_name=form.last_name.data, company=form.company_name.data,
                            user_id=current_user.id, slug=generate_unique_slug(current_user.id, last_row_id=last_row_id))
            db.session.add(contact)
            db.session.commit()
            flash('Contact added', 'success')
            return jsonify({"message": "Contact added"})
        else:
            errors = [error for field, messages in form.errors.items() for error in messages]
            return jsonify({"errors": errors})
    return render_template('main/contacts.html', active_page='contacts', title='Contacts', contacts=contacts, form=form, lists=lists)


@main.route('/contacts2/', methods=['GET', 'POST'])
@login_required
def contacts2():
    page = request.args.get('page', type=int, default=1)
    contacts = Contact.query.filter_by(user=current_user).paginate(page=page, per_page=10)
    print("hi", contacts)
    lists = List.query.filter_by(user=current_user).all()
    last_row_id = Contact.query.filter_by(user=current_user).order_by(Contact.contact_id.desc()).first()
    if last_row_id:
        last_row_id = last_row_id.contact_id
    form = AddContact()
    form.usr = current_user
    if request.method == 'POST':
        if form.validate_on_submit():
            contact = Contact(email=form.email.data, first_name=form.first_name.data,
                            last_name=form.last_name.data, company=form.company_name.data,
                            user_id=current_user.id, slug=generate_unique_slug(current_user.id, last_row_id=last_row_id))
            db.session.add(contact)
            db.session.commit()
            flash('Contact added', 'success')
            return jsonify({"message": "Contact added"})
        else:
            errors = [error for field, messages in form.errors.items() for error in messages]
            return jsonify({"errors": errors})
    return render_template('main/contacts2.html', active_page='contacts', title='Contacts', contacts=contacts, form=form, lists=lists)

@main.route("/apply_bulk_actions", methods=['POST'])
def apply_bulk_actions():
    action  = request.form['bulk_action']
    selected_contact_ids = request.form['selected_contact_ids']
    selected_contacts = selected_contact_ids.split(',')
    if action == '':
        flash('Please, select required fields', 'danger')
        return redirect(url_for('main.contacts'))
    if action == 'move_to_list':
        list_ = request.form['list_name']
        list_ = List.query.get(int(list_))
        for contact in selected_contacts:
            list_.contacts.append(Contact.query.get(int(contact)))
            db.session.commit()
        flash(f'Contacts added to {list_.list_name}', 'success')
        return redirect(url_for('main.contacts'))
    elif action == 'delete':
        for contact in selected_contacts:
            db.session.delete(Contact.query.get(int(contact)))
            db.session.commit()
        flash('Contacts deleted', 'success')
        return redirect(url_for('main.contacts'))
    elif action == 'unsubscribe':
        for contact in selected_contacts:
            C = Contact.query.get(int(contact))
            C.subscribed = False
            db.session.commit()
        flash('Contacts Unsubscribed', 'success')
        return redirect(url_for('main.contacts'))
    elif action == 'subscribe':
        for contact in selected_contacts:
            C = Contact.query.get(int(contact))
            C.subscribed = True
            db.session.commit()
        flash('Contacts Subscribed', 'success')
        return redirect(url_for('main.contacts'))
    return redirect(url_for('main.contacts'))

@main.route('/contacts/lists/', methods=['GET', 'POST'])
@login_required
def contact_lists():
    form = CreateContactList()
    lists = List.query.filter_by(user=current_user).all()
    last_row_id = List.query.filter_by(user=current_user).order_by(List.list_id.desc()).first()
    if last_row_id:
        last_row_id = last_row_id.list_id
    if lists:
        for i in lists:
            if i.slug == None:
                i.slug = generate_unique_slug(current_user.id, last_row_id=last_row_id, length=5)
                db.session.commit()
    if form.validate_on_submit():
        create_list = List(list_name=form.name.data, user=current_user, 
                           slug=generate_unique_slug(current_user.id, last_row_id=last_row_id, length=5))
        db.session.add(create_list)
        db.session.commit()
        flash('List Created', 'success')
        return redirect(url_for('main.contact_lists'))
    return render_template('main/list.html', active_page='lists', title='Lists', form=form, lists=lists)

@main.route('/contacts/<contact_id>')
@login_required
def contact_details(contact_id):
    contact = Contact.query.filter_by(slug=contact_id, user=current_user).first()
    tracking_ = CampaignTracking.query.filter_by(recipient_id=10).all()
    if contact:
        for i in CampaignTracking.query.all():
            print(i.event_name)
        interactions = {} #this will store campaign as key and tracking as values
        campaigns = contact.campaigns
        if campaigns:
            for campaign in campaigns:
                campaign_recipient = CampaignRecipient.query.filter_by(campaign_id=campaign.campaign_id).first()
                tracking  = CampaignTracking.query.filter_by(recipient_id=campaign_recipient.recipient_id).all()
                interactions[campaign_recipient] = tracking
        print(interactions)
        for i, j in interactions.items():
            print("Campaign: ",i.campaign.campaign_name)
            for k in j:
                print('Event:', k.event_name)
        return render_template('main/contact_details.html', active_page='contacts', title='Contacts', contact=contact, interactions=interactions)
    else:
        abort(404)

@main.route('/contacts/lists/<slug>')
@login_required
def list_contacts(slug):
    list_ = List.query.filter_by(slug=slug, user=current_user).first()
    if list_:
        contacts = list_.contacts
        return render_template('main/list_contacts.html', active_page='lists', title='Contacts', list_name = list_.list_name, contacts=contacts)
    else:
        abort(404)

@main.route('/upload/error/', methods=['GET', 'POST'])
@login_required
def upload_error():
    if 'upload_error_details' in session.keys():
        error_details = session['upload_error_details']
        return render_template('/main/uploaderror.html', error_details=error_details)
    else:
        return redirect(url_for('main.upload'))

@main.route('/contacts/upload/', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadContacts()
    if form.validate_on_submit():
        file_name = save_file(form.contacts.data)
        try:
            upload = UploadContact(file_name)
            upload.check_if_file_has_email()
            user = User.query.get(current_user.id)
            user.upload_file = file_name
            db.session.commit()
            return redirect(url_for('main.map_contacts'))
        except Exception as e:
            session['upload_error_details'] = str(e)
            return redirect(url_for('main.upload_error'))
    return render_template('main/upload.html', active_page='contacts', form=form, title='Upload Contacts')


@main.route('/contacts/upload/map_contacts/', methods=['GET', 'POST'])
@login_required
def map_contacts():
    map = MapContacts(current_user.upload_file)
    file_data = map.analyze_file()
    invalid_email_address = []
    lists = []
    for i in List.query.filter_by(user=current_user).all():
        lists.append((i.list_id, i.list_name))
    cols_with_email = list(set(file_data['columns_with_email'])) if file_data['columns_with_email'] != [] else file_data['columns']
    form = MapContactsForm(choices=file_data['columns'], lists=lists, email_choices=cols_with_email)
    if form.validate_on_submit():
        emails = list(map.df[form.email.data])
        first_name = list(map.df[form.first_name.data])
        last_name = list(map.df[form.last_name.data])
        company = list(map.df[form.company.data])
        data_to_insert = []
        for email, fname, lname, comp in zip(emails, first_name, last_name, company):
            if validate_email(email=str(email)):
                existing_contact = Contact.query.filter_by(email=email).first()
                if existing_contact:
                    existing_contact.first_name = fname
                    existing_contact.last_name = lname
                    existing_contact.company = comp
                    db.session.commit()
                else:
                    s = generate_unique_slug(current_user.id, length=8, int_only=False)
                    data_to_insert.append({
                        'email': email,
                        'first_name': fname,
                        'last_name' : lname,
                        'company': comp,
                        'user': current_user,
                        'user_id':current_user.id,
                        'slug':s
                    })
            else:
                invalid_email_address.append(email)
        db.session.bulk_insert_mappings(Contact, data_to_insert)
        db.session.commit()
        flash('Contacts have been uploaded', 'success')
        return redirect(url_for('main.contacts'))
    return render_template('main/map_contacts.html', data=file_data, active_page='contacts', form=form)

@main.route("/see")
def see_contacts():
    x = Contact.query.all()
    c = [i.email for i in x]
    return c