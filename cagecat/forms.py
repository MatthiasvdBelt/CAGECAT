import wtforms
from wtforms import StringField, EmailField, HiddenField, SelectField, IntegerField, DecimalField
from wtforms import Form, validators as val

# name and id are set to the variable name
# description equals the corresponding help text word
from cagecat.valid_input_cblaster import is_safe_string, is_safe_string_value


cblaster_search_databases = [
    ('nr', 'nr'),
    ('refseq_protein', 'Refseq protein'),
    ('swissprot', 'Swissprot'),
    ('pdbaa', 'pdbaa')
]

# <option value="nr">nr</option>
# <option value="refseq_protein">RefSeq protein</option>
# <option value="swissprot">Swissprot</option>
# <option value="pdbaa">pdbaa</option>

class JobInfoForm(Form):
    job_title = StringField(
        label=u'Job title',
        validators=[val.length(max=60), is_safe_string_value],
        description='job_title'
    )

    mail_address = EmailField(
        label=u'Email address for notification',
        validators=[val.length(max=100)],
        description='email_notification'
    )

class SearchSectionForm(Form):
    entrez_query = StringField(
        label=u'Entrez query',
        validators=[is_safe_string_value,],
        description='entrez_query',
        render_kw={
            'placeholder': 'Aspergillus[organism]'
        }
    )

    database_type = SelectField(
        # TODO: when other values than choices are posted, check if it raises error
        label=u'Database',
        validators=[val.input_required(), is_safe_string_value],
        choices=cblaster_search_databases,
        description='database_type'
    )

    hitlist_size = IntegerField(
        label=u'Maximum hits',
        validators=[val.input_required(), is_safe_string_value],
        description='max_hits',
        default=500,
        id='max_hits',
        render_kw={
            'min': 1,
            'max': 10000,
            'step': 1
        }
    )

class FilteringSectionForm(Form):
    max_evalue = DecimalField(
        label=u'Max. e-value',
        validators=[val.input_required(), is_safe_string_value],
        description='max_evalue',
        render_kw={
            'min': 0.01,
            'max': 100,
            'step': 0.01
        }
    )

    pass






class JobTypeForm(Form):
    prev_job_id = HiddenField()

    pass

class PreviousJob(JobTypeForm):
    pass
