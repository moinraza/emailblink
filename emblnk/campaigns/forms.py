from wtforms.validators import DataRequired, Email, Optional
from wtforms import StringField, SelectField, SelectMultipleField, TextAreaField, DateTimeLocalField, SubmitField
from flask_wtf import FlaskForm

class ListsAndSchedule(FlaskForm):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(ListsAndSchedule, self).__init__(*args, **kwargs)
        self.to_lists.choices = choices

    to_lists = SelectMultipleField('Select contact lists')
    send_datetime = DateTimeLocalField('Schedule campaign', format='%m/%d/%y', )
    #submit = SubmitField('Create Campaign')

class CampaignInfoForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(CampaignInfoForm, self).__init__(*args, **kwargs)
        self.sender.choices = choices

    sender = SelectField('Select a Sender', validators=[DataRequired()])
    sender_name = StringField('Define Sender Name (Optional)')
    campaign_name = StringField('Campaign Name', validators=[DataRequired()])
    reply_to = StringField('Reply-to address (Optional)', validators=[Optional(), Email()])
    subject_line = StringField('Subject', validators=[DataRequired()])
    pre_text_loader = StringField('Pre-text Loader (Optional)',)
    #submit = SubmitField('Save & Next')

class CampaignTemplateForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices')
        super(CampaignTemplateForm, self).__init__(*args, **kwargs)
        self.template.choices = choices
    template = SelectField('Choose a Template', validators=[DataRequired()])

class MessageForm(FlaskForm):
    message = TextAreaField('Create a Message', validators=[DataRequired()])
    #submit = SubmitField('Create Message & Next')

class TemplateForm(FlaskForm):
    template_name = StringField('Template Name', validators=[DataRequired()])
    message = TextAreaField('Message (Email HTML)', validators=[DataRequired()])
    submit = SubmitField('Save & Exit')