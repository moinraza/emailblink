from flask import Blueprint, request, render_template, current_app, redirect, url_for, flash, session, make_response
from emblnk.models import Campaign, CampaignRecipient, CampaignTracking, List, Senders, Contact, Templates
from flask_login import current_user, login_required
from emblnk.campaigns.forms import CampaignInfoForm, ListsAndSchedule, MessageForm, TemplateForm
from emblnk import db
from emblnk.campaigns.MailSender import SendCampaign
from emblnk.campaigns.html_email_temp import test_mail_content
from emblnk.models import generate_unique_slug
from datetime import datetime

tracking = Blueprint('tracking', __name__)

@tracking.route("/clicks/<campaign_tracking_id>", methods=['GET'])
def clicks(campaign_tracking_id):
    recipient = CampaignRecipient.query.filter_by(url_slug=campaign_tracking_id).first()
    tracking = CampaignTracking.query.filter_by(recipient_id=recipient.recipient_id).first()
    if tracking:
        tracking.click_count += 1
    else:
        tracking = CampaignTracking(recipient_id=recipient.recipient_id,
                                    click_url=request.args.get('url'), open_count=1, click_count=1, event_name='Clicked', event_time=datetime.utcnow())
        db.session.add(tracking)
    db.session.commit()
    contact = Contact.query.get(recipient.contact_id)
    camp = Campaign.query.get(recipient.campaign_id)
    print(f'{contact} Clicked a link from {camp.campaign_name}')
    return redirect(request.args.get('url', '/'))

@tracking.route("/opens/<campaign_tracking_id>", methods=['GET'])
def opens(campaign_tracking_id):
    recipient = CampaignRecipient.query.filter_by(url_slug=campaign_tracking_id).first()
    tracking = CampaignTracking.query.filter_by(recipient_id=recipient.recipient_id).first()
    if tracking:
        tracking.open_count += 1
    else:
        tracking = CampaignTracking(recipient_id=recipient.recipient_id, open_count=1, click_count=0, event_name='Opened', event_time=datetime.utcnow())
        db.session.add(tracking)
    db.session.commit()
    contact = Contact.query.get(recipient.contact_id)
    camp = Campaign.query.get(recipient.campaign_id)
    print(f'{contact} Opened {camp.campaign_name}')
    return make_response('', 200)

"""@tracking.route("/opens/<campaign_tracking_id>", methods=['GET'])
def opens(campaign_tracking_id):
    recipient = CampaignRecipient.query.filter_by(url_slug=campaign_tracking_id).first()
    campaign = Campaign.query.get(recipient.recipient_id)
    tracking = CampaignTracking.query.filter_by(recipient_id=recipient.recipient_id).first()
    if tracking:
        tracking.open_count += 1
        campaign.total_opens += 1
    else:
        tracking = CampaignTracking(recipient_id=recipient.recipient_id, open_count=1, click_count=0, event_name='Opened', event_time=datetime.utcnow())
        campaign.total_opens = 1
        campaign.unique_opens += 1
        db.session.add(tracking)
    db.session.commit()
    contact = Contact.query.get(recipient.contact_id)
    camp = Campaign.query.get(recipient.campaign_id)
    print(f'{contact} Opened {camp.campaign_name}')
    return make_response('', 200)"""

@tracking.route('/unsubscribe/<campaign_tracking_id>')
def unsubscribe(campaign_tracking_id):
    recipient = CampaignRecipient.query.filter_by(url_slug=campaign_tracking_id).first()
    contact = Contact.query.get(recipient.contact_id)
    contact.subscribed = False
    db.session.commit()
    return f'{contact.email} is unsubscribed'

"""
@tracking.route('/campaign/new', methods=['GET', 'POST'])
@login_required
def create_campaign():
    step = session.get('step', 1)
    lists = List.query.filter_by(user=current_user).order_by(List.list_name).all()
    senders = Senders.query.filter_by(user=current_user).all()
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
                message = message_form.message.data,
                sender = sender,
                slug = generate_unique_slug(current_user.id,
                                            length=32, int_only=False))
            db.session.add(campaign)
            add_lists_in_campaign(selected_lists, campaign=campaign)
            db.session.commit()
 
            Camp = SendCampaign(
                lists=selected_lists,
                sender_id=sender.id,
                subject= session['subject_line'],
                message=str(session['message']))
            Camp.send_mail()

            clear_campaign_session_data()
            return redirect(url_for('campaigns.campaigns'))
    return render_template('campaigns/create_campaign.html', step=step, campaign_info_form=campaign_info_form, message_form=message_form, recipient_schedule_form=recipient_schedule_form, lists=choices)
"""