from flask import Blueprint, request, render_template, current_app, redirect, url_for, flash, session, make_response
from emblnk.models import Campaign, CampaignRecipient, CampaignTracking, List, Senders, Contact, Templates
from flask_login import current_user, login_required
from emblnk.campaigns.forms import CampaignInfoForm, ListsAndSchedule, MessageForm, TemplateForm, CampaignTemplateForm
from emblnk import db
from emblnk.campaigns.MailSender import SendCampaign
from emblnk.campaigns.html_email_temp import test_mail_content
from emblnk.models import generate_unique_slug
from datetime import datetime

campaign = Blueprint('campaigns', __name__)

def clear_campaign_session_data():
    campaign_session_data = ['campaign_name', 'subject_line', 'pre_text_loader', 'step',
                             'sender', 'message']
    for key in list(session.keys()):
        if key in campaign_session_data:
            session.pop(key, None)

def add_lists_and_contacts_in_campaign(lists, campaign):
    for i in lists:
        list_ = List.query.get(i)
        if list_:
            campaign.to_lists.append(list_)
            for contact in list_.contacts:
                campaign.to_contacts.append(contact)
            db.session.commit()
    return True

def check_unsubscribe_link(message):
    return True if "%UNSUBSCRIBE%" in message else False

@campaign.route('/campaigns')
@login_required
def campaigns():
    page = request.args.get('page', type=int, default=1)
    campaigns = Campaign.query.filter_by(user=current_user).order_by(Campaign.created_at.desc()).paginate(page=page, per_page=10)
    total_campaigns = campaigns.total
    print(str(type(campaigns)))
    return render_template('campaigns/campaigns.html', title='Campaigns', total_campaigns=total_campaigns, campaigns=campaigns, active_page='campaigns')

@campaign.route('/campaigns/<camp_id>')
@login_required
def view_campaign_details(camp_id):
    campaign = Campaign.query.get(camp_id)
    to_lists = campaign.to_lists
    return render_template('/campaigns/campaign_details.html',active_page='campaigns', campaign=campaign, lists=to_lists)

@campaign.route("/templates")
@login_required
def templates():
    page = request.args.get('page', type=int, default=1)
    templates = Templates.query.filter_by(user=current_user).order_by(Templates.created_at.desc()).paginate(page=page, per_page=10)
    total_templates = templates.total
    return render_template('campaigns/templates.html', title='Templates',total_templates=total_templates, templates=templates, active_page='templates',)

@campaign.route("/templates/<slug>")
@login_required
def template_view(slug):
    temp = Templates.query.filter_by(slug=slug).first()
    message = temp.message
    temp_name = temp.template_name
    return render_template('campaigns/template_view.html', message=message, temp_name=temp_name)

@campaign.route('/templates/new', methods=['GET', 'POST'])
@login_required
def create_template():
    if request.method == "POST":
        temp_name = request.form['template_name']
        edioter_data = request.form['edioterdata']
        if edioter_data != "":
            template = Templates(user=current_user, user_id=current_user.id, template_name=temp_name,
                                message=edioter_data, slug=generate_unique_slug(2, length=64, int_only=False))
            db.session.add(template)
            db.session.commit()
            flash('Template Created', 'success')
            return redirect(url_for('campaigns.templates'))
        else:
            flash('Oops! your message field is empty please fill', 'danger')
    return render_template('campaigns/create_template.html',active_page='templates')

@campaign.route('/campaign/new', methods=['GET', 'POST'])
@login_required
def create_campaign():
    message = ''
    step = session.get('step', 1)
    lists = List.query.filter_by(user=current_user).order_by(List.list_name).all()
    senders = Senders.query.filter_by(user=current_user).all()
    temps = Templates.query.filter_by(user=current_user)
    sender_list = []
    for i in senders:
        data = i.id, i.email
        sender_list.append(data)
    choices = []
    for i in lists:
        data = i.list_id, i.list_name
        choices.append(data)
    campaign_info_form = CampaignInfoForm(choices=sender_list)
    message_form = MessageForm()
    recipient_schedule_form = ListsAndSchedule(choices=choices)
    if request.method == 'POST':
        if campaign_info_form.validate_on_submit():
            session['campaign_name'] = campaign_info_form.campaign_name.data
            session['subject_line'] = campaign_info_form.subject_line.data
            session['pre_text_loader'] = campaign_info_form.pre_text_loader.data
            session['sender'] = campaign_info_form.sender.data
            session['step'] = 2
            return redirect(url_for('campaigns.create_campaign'))
        if message_form.validate_on_submit():
            session['message'] = message_form.message.data
            unsubscribe_warning = check_unsubscribe_link(session['message'])
            session['step'] = 3
            print('---------------SESSION-2-------------', session)
            return redirect(url_for('campaigns.create_campaign'))
        selected_lists = request.form.getlist('lists')
        send_options = request.form['campaign-send-options']
        send_datetime = request.form.get('campaign-send-datetime')
        print(message)
        if selected_lists:
            sender = Senders.query.get(session['sender'])
            campaign = Campaign(
                user = current_user,
                campaign_name = session['campaign_name'],
                subject = session['subject_line'],
                pre_loader = session['pre_text_loader'],
                message = session['message'],
                sender = sender,
                slug = generate_unique_slug(current_user.id,
                                            length=32, int_only=False))
            db.session.add(campaign)
            add_lists_and_contacts_in_campaign(selected_lists, campaign=campaign)
            db.session.commit()
            Camp = SendCampaign(
                lists=selected_lists,
                sender_id=sender.id,
                subject= session['subject_line'],
                message=str(session['message']),
                campaign=campaign)
            Camp.send_mail()
            clear_campaign_session_data()
            return redirect(url_for('campaigns.campaigns'))
    return render_template('campaigns/create_campaign.html', temps=temps ,active_page='campaigns', step=step, campaign_info_form=campaign_info_form, message_form=message_form, recipient_schedule_form=recipient_schedule_form, lists=choices)


@campaign.route('/new-campaign/', methods=['GET', 'POST'])
@login_required
def new_campaign():
    if not 'step' in session:
        session['step'] = 1
    lists = List.query.filter_by(user=current_user).order_by(List.list_name).all()
    senders = Senders.query.filter_by(user=current_user).all()
    if senders == []:
        flash("Create a sender before creating campaign", "info")
        return redirect(url_for('users.senders'))
    temps = Templates.query.filter_by(user=current_user).all()
    temp_list = []
    for i in temps:
        data = i.template_id, i.template_name
        temp_list.append(data)
    sender_list = []
    for i in senders:
        data = i.id, i.email
        sender_list.append(data)
    choices = []
    for i in lists:
        data = i.list_id, i.list_name
        choices.append(data)
    campaign_info_form = CampaignInfoForm(choices=sender_list)
    template_form = CampaignTemplateForm(choices=temp_list)
    message_form = MessageForm()
    recipient_schedule_form = ListsAndSchedule(choices=choices)
    if campaign_info_form.validate_on_submit():
        session['step'] = 2
        sender = Senders.query.get(campaign_info_form.sender.data)
        campaign = Campaign(
                user = current_user,
                campaign_name = campaign_info_form.campaign_name.data,
                subject = campaign_info_form.subject_line.data,
                pre_loader = campaign_info_form.pre_text_loader.data,
                message = "",
                sender = sender,
                slug = generate_unique_slug(current_user.id,
                                            length=32, int_only=False))
        db.session.add(campaign)
        
    if message_form.validate_on_submit():
        pass
    
    if recipient_schedule_form.validate_on_submit():
        pass
        #session.pop('step', None)
    return render_template('campaigns/new1.html', step=session["step"], active_page='campaigns',
                            campaign_info_form=campaign_info_form, message_form=message_form, template_form = template_form,
                            recipient_schedule_form=recipient_schedule_form, lists=choices)

@campaign.route('/campaigns/<campaign_id>')
@login_required
def campaign_details(campaign_id):
    campaigns = Campaign.query.filter_by(campaign_id=campaign_id).first()
    return render_template('campaigns/campaign_details.html', title='Contacts',active_page='campaigns', campaigns=campaigns)

"""-----------------Tracking-----------------"""