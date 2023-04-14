"""Stores complete forms, created using form sections

Author: Matthias van den Belt
"""

from cagecat.forms.form_sections import *


class GeneralForm(Form):
    """Has job info and submit input fields

    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.job_info = JobInfoForm()
        self.submit = SubmitForm()

class CblasterSearchBaseForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.general = GeneralForm()
        self.clustering = ClusteringSectionForm()
        self.summary_table = SummaryTableForm()
        self.binary_table = BinaryTableForm()
        self.additional_options = AdditionalOptionsSectionForm()
        self.intermediate_genes = IntermediateGenesSectionForm()

class CblasterSearchForm(Form):  # TODO: refactor to CblasterSearchRemoteForm
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = CblasterSearchBaseForm()
        self.search = SearchSectionForm()
        self.filtering = FilteringSectionForm()
    # TODO:
    #  input = InputSectionForm()
    # search_modes = InputSearchModeForm()
    # remote_type = InputRemoteTypeForm()
        self.remote_input_types_file = InputSearchRemoteInputTypeFile()
        self.remote_input_types_ncbi_entries = InputSearchRemoteInputTypeNCBIEntries()
        self.hmm = InputHMMForm()

class CblasterSearchHMMForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = CblasterSearchBaseForm()
        self.hmm = InputHMMForm()


class CblasterRecomputeForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = CblasterSearchBaseForm()

class CblasterGNEForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.general = GeneralForm()
        self.summary_table = SummaryTableGNEForm()
        self.additional_options = AdditionalOptionsGNEForm()

class CblasterExtractSequencesForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.general = GeneralForm()
        self.filtering = ExtractSequencesFilteringForm()
        self.output = ExtractSequencesOutputForm()
        self.download = ExtractSequencesDownloadSequencesForm()

class CblasterExtractSequencesFormHMM(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.general = GeneralForm()
        self.filtering = ExtractSequencesFilteringForm()
        self.output = ExtractSequencesOutputForm()

class CblasterExtractClustersForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.general = GeneralForm()
        self.filtering = ClustersFilteringForm()
        self.output = ExtractClustersOutputForm()

class CblasterVisualisationForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.general = GeneralForm()
        self.filtering = ClustersFilteringForm()
        self.output = CblasterVisualisationOutputForm()

class ClinkerBaseForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.general = GeneralForm()
        self.alignment = ClinkerAlignmentForm()
        self.output = ClinkerOutputForm()
        self.additional_options = ClinkerAdditionalOptionsForm()

class ClinkerDownstreamForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = ClinkerBaseForm()

class ClinkerInitialForm(Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.base = ClinkerBaseForm()
        self.input = ClinkerInputForm()
