// var ncbiPattern = "^[A-Z]{3}(\\d{5}|\\d{7})(\\.\\d{1,3})? *$"
// Examples: "ABC12345", "ABC9281230.999", "PAK92813.22" up to .999th version
var maxJobsToShow = 25
var jobIDPattern = "^([A-Z]\\d{3}){3}[A-Z]\\d{2}$"
var months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
var checkmarkPath = 'https://cagecat.bioinformatics.nl/static/images/checkmark.svg'
var currentlyExecutingPath = 'https://cagecat.bioinformatics.nl/static/images/dna_loader.gif'

function updateJobExecutionStage(url){
    $.ajax(url, {
        dataType: 'json',
        success: function(data){
            if (data['jobStatus'] === 'queued' || data['jobStatus'] === 'waiting'){
                console.log('Job is queued or waiting')
                return;
            }

            if (data['finished'] === data['total'] - 1 || data['jobStatus'] === 'finished' || data['jobStatus'] === 'failed'){
                redirect(window.location.href);
            }

            let currentStageIndex = data['finished'] + 1;
            for (let i = 1; i < currentStageIndex; i++){
                let elem = document.getElementById('stage' + i.toString());
                elem.src = checkmarkPath;
                elem.style.width = '25px';
            }

            let currentStage = document.getElementById('stage' + currentStageIndex.toString());
            currentStage.src = currentlyExecutingPath;
        },
        error: function(data){
            console.log('Error fetching stage. Returned:' + data);
        }
    })
}

function startJobExecutionStageUpdater(job_id){
    let url = '/results/stage/' + job_id;
    updateJobExecutionStage(url);
    setInterval(updateJobExecutionStage, 7500, url)


}

function enableOrDisableOption(id, enable) {
    // For checkboxes
    var elem = document.getElementById(id);

    elem.checked = enable;
    elem.disabled = !enable;
}

function toggleElementVisibility(id) {
    $('#'+id)[0].classList.toggle('no-display');
}

function toggleDisabled(){
    for (let i=0; i< arguments.length; i++){
        var id = arguments[i];
        var elem = document.getElementById(id);

        if (elem.disabled === false){
            removeRequiredAndEnabled(id);
        }
        else {
            setRequiredAndEnabled(id);
        }
    }
}

function setRequiredAndEnabled(id){
    document.getElementById(id).setAttribute('required', 'required');
    document.getElementById(id).removeAttribute('disabled');
}

function removeRequiredAndEnabled(id){
    document.getElementById(id).setAttribute('disabled', 'disabled');
    document.getElementById(id).removeAttribute('required');
}

function showInputOptions(selectionOption, resetQueries){
    let genomeFileUploadDiv = $('#genomeFileUploadDiv')[0];
    let ncbiEntriesDiv = $('#ncbiEntriesDiv')[0];
    let searchPrevJobOptions = $('#searchPrevJobOptions')[0];
    let inputFileMessages = $('#inputFileMessages')[0];

    if (resetQueries){
        $('#requiredSequencesSelector')[0].options.length = 0;
    }
    if (selectionOption === 'file'){
        genomeFileUploadDiv.classList.remove('no-display');
        inputFileMessages.classList.remove('no-display'); // is actually part of genomeFileUploadDiv, but divs are not rendering correct. should be fixed in future.
        ncbiEntriesDiv.classList.add('no-display');

        // enable
        setRequiredAndEnabled('genomeFiles');

        // disable elements
        removeRequiredAndEnabled('ncbiEntriesTextArea');

        enableOrDisableOption('searchSection', true);

        document.getElementById("submit").removeAttribute("disabled");

    }
    else if (selectionOption === 'ncbi_entries'){
        genomeFileUploadDiv.classList.add('no-display');
        inputFileMessages.classList.add('no-display'); // is actually part of genomeFileUploadDiv, but divs are not rendering correct. should be fixed in future.
        ncbiEntriesDiv.classList.remove('no-display');

        // enable
        setRequiredAndEnabled('ncbiEntriesTextArea')

        // disable elements
        removeRequiredAndEnabled('genomeFiles');

        enableOrDisableOption('searchSection', true);
        validateNCBIEntries();

    } else if (selectionOption === 'prev_session'){ //deprecated or still used?
        console.log('selectionOption prev_session is still in use')
        genomeFileUploadDiv.classList.add('no-display');
        ncbiEntriesDiv.classList.add('no-display');
        searchPrevJobOptions.classList.remove('no-display');

        // disable elements
        removeRequiredAndEnabled('genomeFiles');
        removeRequiredAndEnabled('ncbiEntriesTextArea');
        document.getElementById("searchLabelSessionFile").classList.add("disabled");

        enableOrDisableOption('searchSection', false);

        document.getElementById("submit").removeAttribute("disabled");

        if (!resetQueries){
            document.getElementById('radioPrevSession').setAttribute('checked', 'checked');
        }
    }
}

function showModule(ev, moduleName){
    console.log('For future tool implementation which could be a starting point')
    return;
    var i, moduleSelector, moduleContent;

    moduleContent = document.getElementsByClassName('moduleContent');
    for (i=0; i < moduleContent.length; i++){
        moduleContent[i].classList.add('no-display');
    }

    document.getElementById(moduleName).classList.remove('no-display');

    // Could add "active" to the moduleSelector class for better visualisation
}

function changeHitAttribute(){
    if (document.getElementById('keyFunction').value !== "len"){
        setRequiredAndEnabled('hitAttribute');
    }
    else {
        removeRequiredAndEnabled('hitAttribute');
    }
}

function validateNCBIEntries() {
    let textArea = document.getElementById("ncbiEntriesTextArea");
    let lines = textArea.value.split("\n");
    document.getElementById("requiredSequencesSelector").options.length = 0;

    let requiredSequences = document.getElementById("requiredSequencesSelector");
    for (let i=0; i<lines.length; i++){
        if (!(lines[i] === "")){

            let opt = document.createElement("option");
            opt.text = lines[i];
            opt.value = lines[i];
            requiredSequences.add(opt);

    }
    }
}

function addSelectedToForm(downstream_prog) {
    if (downstream_prog === "sequences") {
        $('#selectedQueries')[0].value = getSelectedQueries();
    }
    else if (downstream_prog === "clusters"){
        $('#selectedClusters1')[0].value = getSelectedClusters('');
    }
    else if (downstream_prog === "clinker_query"){
        $('#selectedClusters3')[0].value = getSelectedClusters('');
    }
    else {
        console.log("Invalid  type");
    }
}

// TODO future: modularize below functions
function getSelectedClusters(prefix){
    let msg = '';
    $('#' + prefix + 'selectedClustersSelector option').each(function(){
        msg += this.innerText;
        msg += '\n'
    });
    return msg.trimEnd('\n');
}

function getSelectedQueries(){
    let msg ='';
    $('#selectedQueriesSelector option').each(function(){
        msg += this.innerText;
        msg += '\n';
    })
    return msg.trimEnd('\n');
}

function changePower(value, elemToChange){
    let elem = document.getElementById(elemToChange);
    elem.innerText = parseInt(elem.innerText) + value;
}

function getGenBankFileNames() {
    var valid_ext = ["gbk", "gb", "genbank", "gbf", "gbff"];

    $('#selectedFileName')[0].classList.remove('no-display');

    let files = $('#fileUploadClinker')[0].files;
    let selected_files = 'Selected files: ';
    let separator = ', '
    for (let i=0; i < files.length; i++){
        if (i === files.length-1) {
            separator = ''
        }
        let text = files[i].name + separator;
        selected_files += text;
    }
    $('#selectedFileName')[0].innerText = selected_files

    let invalid_files = 'Invalid genome file(s): '
    let separator2 = ', '
    let invalid_counter = 0;
    for (let i=0; i < files.length; i++){
        let file = files[i];
        if (i === files.length-1) {
            separator2 = ''
        }

        if (! valid_ext.includes(file.name.split('.').pop())){
            let text = file.name + separator2;
            invalid_files += text;
            invalid_counter += 1;
        }
    }

    let incorrectExtensionMessageElement = $('#clinkerFileUploadIncorrectExtension')[0];
    let incorrectExtensionMessageElementText = $('#clinkerFileUploadIncorrectExtensionText')[0];

    if (invalid_counter > 0){
        incorrectExtensionMessageElementText.innerText = invalid_files;
        incorrectExtensionMessageElement.classList.remove('no-display');
        $('#submit')[0].setAttribute('disabled', 'disabled')
    }
    else {
        incorrectExtensionMessageElement.classList.add('no-display');
        $('#submit')[0].removeAttribute('disabled');
    }
}


function readFileContents() {
    let requiredSequencesSelect = document.getElementById("requiredSequencesSelector");
    requiredSequencesSelect.options.length = 0;  // Clear all options
    var valid_ext = ["fasta", "fa", "fsa", "fna", "faa", "gbk", "gb", "genbank", "gbf", "gbff"]
    var file = document.getElementById("genomeFiles").files[0];
    var reader = new FileReader();
    let ext = file.name.split(".").pop().toLowerCase();

    $('#selectedFileName')[0].innerText = 'Selected file: ' + file.name

    reader.onload = function(evt){
        if (!valid_ext.includes(ext)){
            document.getElementById('selectedFileName').classList.add('no-display');
            document.getElementById("fileUploadIncorExt").classList.remove('no-display');
            document.getElementById("fileUploadIncorExtText").innerText = "Invalid query file extension: ." + ext;
            $('#submit')[0].setAttribute('disabled', 'disabled')
            return;
        }
        else {
            document.getElementById('selectedFileName').classList.remove('no-display');
            document.getElementById("fileUploadIncorExt").classList.add('no-display');
            $('#submit')[0].removeAttribute('disabled');
        }

        let parser;
        let parsed;
        if (["fasta", "fa", "fsa", "fna", "faa"].includes(ext)) {
            document.getElementById("sanitizationMessage").classList.add('no-display');
            parser = new fastaParser();
            parsed = parser.parse(reader.result);

            for (let i=0; i<parsed.length; i++){
                let copy = parsed[i].sequence.slice().replace(/[ATCGatcg]/g, '')
                if (copy.length === 0) {
                    document.getElementById("nucleotideFastaWarning").classList.remove('no-display');
                }
                else {
                    document.getElementById("nucleotideFastaWarning").classList.add('no-display');
                }

                let id = parsed[i].id.slice(1).split(' ')[0];
                let opt = document.createElement("option");
                opt.text = id;
                opt.value = id;

                requiredSequencesSelect.add(opt);
            }
        }
        else {
            document.getElementById("nucleotideFastaWarning").classList.add('no-display');
            document.getElementById("sanitizationMessage").classList.remove('no-display');
            let splitted = reader.result.split("\n");
            let starter = '/protein_id='
            let splitter = '"'
                for (let i=0; i<splitted.length; i++){
                    if (splitted[i].includes(starter)){
                        let txt = splitted[i].trim().split(splitter)[1].split(' ')[0];
                        let opt = document.createElement("option");
                        opt.text = txt;
                        opt.value = txt;

                        requiredSequencesSelect.add(opt);
                    }
                }
            }

            // TODO: maybe in future
            // parsed = genbankToJson(reader.result);
            // console.log(parsed);
            // for (let i=0; i<parsed.length; i++){
            //
            //     let copy = parsed[i].sequence.slice().replace(/[ATCGatcg]/g, '');
            //     if (copy.length === 0) {
            //         document.getElementById("genpeptFileError").classList.add('no-display');
            //     }
            //     else {
            //         document.getElementById("genpeptFileError").classList.remove('no-display');
            //     }
            //
            // }

        }
    reader.readAsText(file, "UTF-8");
}

function addRequiredSeqs(){
    let selector = document.getElementById("requiredSequencesSelector");
    let selected = [];
    for (let i=0; i < selector.options.length; i++){
        if (selector.options[i].selected){
            selected.push(selector.options[i].value);
        }
    }
    document.getElementById("requiredSequences").value = selected.join(";");
}

function showPreviousJobs(disableBodyOnLoad){
    if (disableBodyOnLoad){
        parent.document.body.onload = null;
        // To prevent double loading as for plots the previous jobs are loaded before the big plot is loaded
    }

    let overview = document.getElementById("previousJobsOverview");
    let numberOfJobsToShow;
    if (localStorage.length > maxJobsToShow){
        numberOfJobsToShow = maxJobsToShow
    }
    else {
        numberOfJobsToShow = localStorage.length
    }
    // let maxJobsToShow = if (localStorage.length > 25) {25} else {localStorage.length}

    for (let i=0; i <numberOfJobsToShow; i++){
        try{
            let jobId = localStorage.getItem(i).split(";")[0];

            let li = document.createElement("li");
            li.classList.add("jobs");

            let a = document.createElement("a");
            a.href = "/results/" + jobId;
            a.innerText = jobId;

            li.appendChild(a);
            overview.insertBefore(li, overview.childNodes[0]);
        }
        catch (error){
            console.log('Error fetching previous jobs')
            determineHeight();
            return;
        }
    }
    let li = document.createElement("li");
    let a = document.createElement("a");
    a.classList.add("no-link-decoration");
    a.href = "/results/";
    a.innerText =  "Previous jobs";
    li.appendChild(a);

    overview.insertBefore(li, overview.childNodes[0]);
}



function showHelp(textType){
    let frameDiv = document.getElementById('htmlFrame');

    $.get('/docs/' + textType, function(data, status){
        document.getElementById("explanationTitle").innerText = data.title;
        document.getElementById("explanationModule").innerText = "Module: " + data.module;
        document.getElementById("explanationText").innerText = data.text;

        if (data.hasOwnProperty('frame')){
            frameDiv.innerHTML = data.frame;
        }
        else{
            frameDiv.innerHTML = '';
        }
    });

    if (document.getElementById("explanationColumn").classList.contains('invisible')){
        toggleExplanationColumn();
    }
}


function toggleExplanationColumn() {
    let rightCol = document.getElementById('explanationColumn');
    let middleCol = document.getElementById('middleColumn');
    let inputs = document.getElementsByClassName('input-layer');
    let toggleButton = document.getElementById('toggleHelpButton');

    if (rightCol.classList.contains('invisible')) {
        // rightCol.classList.remove('no-display');
        rightCol.classList.remove('invisible');
        rightCol.classList.add('visible');
        middleCol.classList.add('shrink-it');
        middleCol.classList.add('enlarge-it');

        toggleButton.innerText = ">>"
    } else {
        rightCol.classList.remove('visible');
        rightCol.classList.add('invisible');
        middleCol.classList.remove('shrink-it');
        middleCol.classList.add('enlarge-it');

        toggleButton.innerText = "<<"
    }

    for (let i=0; i < inputs.length; i++){
        inputs[i].classList.toggle('wider-input');
    }
}

function determineHeight() {
    var body = document.body,
        html = document.documentElement;

    let height_tmp = Math.max(body.scrollHeight, body.offsetHeight,
        html.clientHeight, html.scrollHeight, html.offsetHeight).toString();

    let height = height_tmp - document.getElementById('navigationBar').offsetHeight - 8;

    document.getElementById('statusColumn').style.height = height + 'px';

    let explanationCol = document.getElementById('explanationColumn');
    if (explanationCol !== null) {
        explanationCol.style.height = height + 'px';
    }
}

function toggleRemoteOptions(enable){
    let individualElements = ['radioFasta', 'radioNCBIEntries', 'genomeFiles', 'ncbiEntriesTextArea',
        'searchPrevJobId', 'radioPrevSession ', 'searchEnteredJobId', 'searchUploadedSessionFile'];
    let fieldsets = ['searchSectionFullFieldset', 'filteringSectionFullFieldset'];
    let sections = ['filteringSection', 'searchSection']

    for (let i=0; i < individualElements.length; i++) {
        if (document.getElementById(individualElements[i]) !== null) {
            if (enable) {
                setRequiredAndEnabled(individualElements[i]);
            } else {
                removeRequiredAndEnabled(individualElements[i]);
            }
        }
    }

    for (let i=0; i < fieldsets.length; i++){
        if (enable){
            document.getElementById(fieldsets[i]).classList.remove('no-display');
        }
        else {
            document.getElementById(fieldsets[i]).classList.add('no-display');
        }
    }

    for (let i=0; i< sections.length; i++) {
        if (enable){
            document.getElementById(sections[i]).removeAttribute('disabled');
        }
        else {
            document.getElementById(sections[i]).setAttribute('disabled', 'disabled');
        }
    }
}

function hideElement(elementId) {
    document.getElementById(elementId).style.display = 'none';
}

function showElement(elementId){
    document.getElementById(elementId).style.display = 'block';
}

function changeSearchMode(mode){
    let fieldsetDiv = document.getElementById('hmmFullFieldset');
    let fieldset = document.getElementById('hmmSection');
    let remoteOptions = document.getElementById('remoteOptionsSection');
    let radioFasta = document.getElementById('radioFasta');

    let ncbiDiv = document.getElementById('ncbiEntriesDiv');
    let intermediateGenesDiv = document.getElementById('intermediateGenesDiv');
    let intermediateGenesSectionFieldSet = document.getElementById('intermediateGenesSection');

    document.getElementById("requiredSequencesSelector").options.length = 0;

    if (mode === 'remote'){
        fieldsetDiv.classList.add('no-display');
        fieldset.setAttribute('disabled', 'disabled');
        remoteOptions.classList.remove('no-display');
        remoteOptions.removeAttribute('disabled');

        toggleRemoteOptions(true);
        radioFasta.click()
        document.getElementById('entrez_query').removeAttribute('disabled');
        document.getElementById('database_type').removeAttribute('disabled');

        intermediateGenesDiv.classList.remove('no-display');
        intermediateGenesSectionFieldSet.removeAttribute('disabled');
    }
    else if (mode === 'hmm'){
        fieldsetDiv.classList.remove('no-display');
        fieldset.removeAttribute('disabled');
        remoteOptions.classList.add('no-display');
        remoteOptions.setAttribute('disabled', 'disabled');

        ncbiDiv.classList.add('no-display');

        toggleRemoteOptions(false);
        document.getElementById('entrez_query').setAttribute('disabled', 'disabled');
        document.getElementById('database_type').setAttribute('disabled', 'disabled');

        intermediateGenesDiv.classList.add('no-display');
        intermediateGenesSectionFieldSet.setAttribute('disabled', 'disabled');
    }
    else if (mode === 'combi_remote'){
        fieldsetDiv.classList.remove('no-display');
        fieldset.removeAttribute('disabled');
        remoteOptions.classList.remove('no-display');
        remoteOptions.removeAttribute('disabled');

        toggleRemoteOptions(true);
        radioFasta.click()
        document.getElementById('entrez_query').removeAttribute('disabled');
        document.getElementById('database_type').removeAttribute('disabled');

        intermediateGenesDiv.classList.add('no-display');
        intermediateGenesSectionFieldSet.setAttribute('disabled', 'disabled');
    }
    else {
        console.log('Invalid mode');
    }
}

function moveSelectedElements(target, selectionType){
    let src;
    let dest;

    if (target === 'selected') {
        src = '#unselected'+ selectionType;
        dest = '#selected' + selectionType;
    }
    else if (target === 'unselected'){
        src = '#selected' + selectionType;
        dest = '#unselected' + selectionType;
    }
    else {
        console.log('Incorrect target');
    }

    let result = !$(src+'Selector' + ' option:selected').remove().appendTo(dest+ 'Selector');
    let selectedQueriesSelector = $('#selectedQueriesSelector')[0];

    $('#selectedClusterButton')[0].innerText = 'Select clusters (' + $('#selectedClustersSelector')[0].length.toString() + ')'
    $('#selectedQueryButton')[0].innerText = 'Select queries (' + selectedQueriesSelector.length.toString() + ')'

    return result;
}

function showSelection(toShow){
    let show;
    let hide;

    if (toShow === 'cluster'){
        show = $('#clusterSelection')[0];
        hide = $('#queriesSelection')[0];
    }
    else {
        show = $('#queriesSelection')[0];
        hide = $('#clusterSelection')[0];
    }
    show.classList.remove('no-display');
    hide.classList.add('no-display');
}

function addClustersToUse(){
    let elem = $('#selectedReferenceCluster')[0];
    let merged = []

    for (let i=0; i < elem.children.length; i++){
        if (i !== elem.selectedIndex) {
            // console.log(elem.children[i]);
            merged.push(elem.children[i].value)
        }
    }
    $('#selectedClustersToUse')[0].value = merged.join(' ');
}


document.addEventListener('scroll', function(e){
    let elem = $('#filler')[0];

    if (elem !== undefined) {
        elem.style.height = window.scrollY + 'px';
    }
})

function setExampleInput(tool_name){
    if (tool_name === 'cblaster_search'){
        let exampleQueries = 'QBE85649.1\n' +
            'QBE85641.1\n' +
            'QBE85642.1\n' +
            'QBE85643.1\n' +
            'QBE85644.1\n' +
            'QBE85645.1\n' +
            'QBE85646.1\n' +
            'QBE85647.1\n' +
            'QBE85648.1';


        let firstRadio = $('#remoteMode')[0];
        firstRadio.click();

        let secondRadio = $('#radioNCBIEntries')[0];
        secondRadio.click();
        $('#job_title')[0].value = 'Example input (Burnettramic Acids)';
        $('#max_hits')[0].value = "800";
        $('#percentageQueryGenes')[0].value = "40";
        $('#ncbiEntriesTextArea')[0].value = exampleQueries;
        secondRadio.click();  // to make required sequences pop up
    }
    else if (tool_name === 'clinker') {
        $('#identity')[0].value = '0.28';
        $('#clinkerDecimals')[0].value = '3';
        $('#job_title')[0].value = 'Example visualization input (BA)';
    }
    else {
            console.log('Incorrect tool name:' + tool_name)
        }
}

function getOutputFromPlot(plotting_type){
    let frame = document.getElementById("newWindow");
    let doc = frame.contentDocument || frame.contentWindow.document;
    let clusters;

    let clusterSelector = $('#unselectedClustersSelector')[0];
    let querySelector = $('#unselectedQueriesSelector')[0];

    if (plotting_type === 'search'){
        clusters = doc.getElementsByClassName("tickTextGroup");

        setTimeout(function(){
            let ticks = doc.getElementsByClassName("tick");
            for (let i=0; i < ticks.length; i++){
                const query_name = ticks[i].childNodes[1];
                let text = query_name.textContent;

                let option = document.createElement('option');
                option.value = text;
                option.innerText = text;
                option.classList.add('smaller-font');

                querySelector.appendChild(option);
            }
        }, 100); // sometimes loading would fail. A timeout leads to a succesfull load
    }
    else if (plotting_type === 'visualize'){
        clusters = doc.getElementsByClassName("clusters")[0].childNodes;
    }
    else {
        console.log('Incorrect plotting type')
    }

    for (let i=0; i < clusters.length; i++) {
        let text;
        if (plotting_type === 'search') {
            text = clusters[i].firstChild.childNodes[0].textContent;

        } else if (plotting_type === 'visualize') {
            if (clusters[i].firstChild.childNodes[0].textContent !== 'Query Cluster') {
                text = clusters[i].firstChild.childNodes[0].textContent;
            }

        } else {
            console.log('Incorrect plotting type')
        }
        if (text !== undefined) { // in case of visualize and "Query Cluster"
            let option = document.createElement('option');
            option.value = text;
            option.innerText = text;
            option.classList.add('smaller-font');
            clusterSelector.appendChild(option);
        }
    }
}

function checkConsent(){
    if (Cookies.get('consent') === '1'){
        $('#consent').remove();
    }
}

function hideNotifications(notification_id){
    if (Cookies.get(notification_id) === '1'){
        $('#' + notification_id).remove();
    }
}


// Note: functions below are labeled as unused by PyCharm (or your interpreter) but they are used (check usages manually)
function initReadQueryFile(){
    var file = document.getElementById("genomeFiles").files[0];
    if (file) {
        var reader = new FileReader();
        reader.readAsText(file, "UTF-8");
        reader.onload = function (evt) {
            // console.log(evt.target.result);
        }

        reader.onerror = function (evt) {
            console.log("Error reading file");
        }
    }
}

function postLoadingIFrame(){
    document.getElementById("resultLoadedMessage").classList.add('fade-out');
    document.getElementById("loadingImage").classList.add('no-display');
}

function storeJobId(id, j_type, j_title){
    let maxToShow = 250;

    for (let i=0; i<maxToShow; i++){
        let str = i.toString();
        if (localStorage.getItem(str) === null){
            let date = new Date();
            let seconds = date.getSeconds();
            if (seconds.toString().length === 1){
                seconds = '0' + seconds;
            }
            let time = [months[date.getMonth()], date.getDate(), date.getFullYear(), '-', ' '].join(' ') + [date.getHours(), date.getMinutes(), seconds].join(':')
            let msg = id + ";" + j_type + ";" + time + ';' + j_title;
            console.log(msg);
            localStorage.setItem(str, msg);
            return;
        }
    }
}

function showDetailedPreviousJobs(){
    let overview = document.getElementById("detailedPreviousJobs");

    for (let i=0; i <localStorage.length; i++) {
        let msg = localStorage.getItem(i).split(";");
        let tr = document.createElement("tr");

        let td = document.createElement("td");
        let a = document.createElement("a");
        a.style = 'font-size: 17px;';
        a.classList.add('monospaced');
        a.href = "/results/" + msg[0];
        a.innerText = msg[0]
        td.appendChild(a);
        tr.appendChild(td);

        let td1 = document.createElement("td");
        td1.innerText = msg[1];
        tr.appendChild(td1);

        let td2 = document.createElement("td");
        td2.innerText = msg[2];
        tr.appendChild(td2);

        let td3 = document.createElement("td");
        td3.innerText = msg[3];
        tr.appendChild(td3);

        overview.insertBefore(tr, overview.childNodes[0]);
    }

    let tr = document.createElement("tr");

    let th = document.createElement("th");
    th.innerText = "Job ID";
    th.style.width = "15%"
    tr.appendChild(th);

    let th1 = document.createElement("th");
    th1.innerText = "Type of job";
    th1.style.width = "20%"
    tr.appendChild(th1);

    let th2 = document.createElement("th");
    th2.innerText = "Date";
    th2.style.width = "30%"
    tr.appendChild(th2);

    let th3 = document.createElement("th");
    th3.innerText = "Title";
    th3.style.width = "30%"
    tr.appendChild(th3);

    overview.insertBefore(tr, overview.childNodes[0]);
}

function redirect(url){
    setTimeout(function(){
        window.location.href = url;
    }, 50);
}

function addAccordionListeners() {
    // from: https://www.w3schools.com/howto/howto_js_accordion.asp
    let acc = document.getElementsByClassName("accordion");

    for (let i = 0; i < acc.length; i++) {
        acc[i].addEventListener("click", function () {

            this.classList.toggle("active");
            let panel = this.nextElementSibling;

            if (panel.id === 'dummy'){
                panel = panel.nextElementSibling;
            }

            if (panel.style.maxHeight) {
                panel.style.maxHeight = null;
            } else {
                panel.style.maxHeight = panel.scrollHeight + "px";
            }

            if (acc[i].id === "advancedSection"){
                if (acc[i].innerText === "Advanced +"){
                    acc[i].innerText = "Advanced -";
                }
                else {
                    acc[i].innerText = "Advanced +";
                }
            }

            setTimeout(() => {determineHeight();}, 410);
        });


    }
}



setInterval(function(){
    $.ajax('/status', {
        dataType: 'json',
        success: function(data) {
            $('#status_server')[0].innerText = data['server_status'];
            $('#status_running')[0].innerText = data['running'];
            $('#status_queued')[0].innerText = data['queued'];
            $('#status_completed')[0].innerText = data['completed'];
        },
        error: function (data){
            console.log('Unable to fetch server status')
        }
    })
}, 15000)
