function enableOrDisableOption(id, enable) {
    // For checkboxes
    var elem = document.getElementById(id);

    elem.checked = enable;
    elem.disabled = !enable;
}

function option5change(){
    var elem = document.getElementById("option5")
    var enable = !elem.checked

    enableOrDisableOption("option1", enable);
    enableOrDisableOption("option2", enable);
}

function validateForm(){
    var x = document.forms["optionForm"]["e-value"];
    console.log(x.value);
    // TODO

    return true; // Accepts form (and therefore continues to next page if true
    // is returned)
}
function changeFooterVisibility(){
    var elem = document.getElementById("showFooterCheckbox");
    // var footer = document.getElementById("custom_footer");
    //console.log(elem);
    // console.log($("custom_footer"));

    var footer = $("#custom_footer"); // uses ID
    let speed = "slow"
    if (!elem.checked) {
        footer.slideUp(speed);
    }
    else {
        footer.slideDown(speed)
    }

}

function toggleElementVisibility(id) {
    var elem = document.getElementById(id);

    if (elem.style.display === "none") {
        elem.style.display = "block";
    } else {
        elem.style.display = "none";
    }
}

function toggleDisabled(id){
    var elem = document.getElementById(id);

    if (elem.disabled === false){
        removeRequiredAndEnabled(id);
    }
    else {
        setRequiredAndEnabled(id);
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

function showInputOptions(selectionOption){
    if (selectionOption === 'fasta'){
        document.getElementById('genomeFileUploadDiv').style.display = 'block';
        document.getElementById('ncbiEntriesDiv').style.display = 'none';
        document.getElementById('searchPrevJobOptions').style.display = 'none';

        // enable
        setRequiredAndEnabled('genomeFile');

        // disable elements
        removeRequiredAndEnabled('ncbiEntriesTextArea');
        removeRequiredAndEnabled('searchEnteredJobId');
        removeRequiredAndEnabled('searchUploadedSessionFile');

        enableOrDisableOption('searchSection', true);

    }
    else if (selectionOption === 'ncbi_entries'){
        document.getElementById('genomeFileUploadDiv').style.display = 'none';
        document.getElementById('ncbiEntriesDiv').style.display = 'block';
        document.getElementById('searchPrevJobOptions').style.display = 'none';

        // enable
        setRequiredAndEnabled('ncbiEntriesTextArea')

        // disable elements
        removeRequiredAndEnabled('genomeFile');
        removeRequiredAndEnabled('searchEnteredJobId');
        removeRequiredAndEnabled('searchUploadedSessionFile');

        enableOrDisableOption('searchSection', true);

    } else if (selectionOption === 'prev_session'){
        document.getElementById('genomeFileUploadDiv').style.display = 'none';
        document.getElementById('ncbiEntriesDiv').style.display = 'none';
        document.getElementById('searchPrevJobOptions').style.display = 'block';

        //enable
        setRequiredAndEnabled('searchEnteredJobId');

        // disable elements
        removeRequiredAndEnabled('genomeFile');
        removeRequiredAndEnabled('ncbiEntriesTextArea');

        enableOrDisableOption('searchSection', false);
    }
}

function showModule(ev, moduleName){
    var i, moduleSelector, moduleContent;

    moduleContent = document.getElementsByClassName('moduleContent');
    for (i=0; i < moduleContent.length; i++){
        moduleContent[i].style.display ="none";
    }

    document.getElementById(moduleName).style.display = "block";

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

function changePrevSessionType(){
    let clickedButton = event.target;
    let module = clickedButton.id.split("Prev")[0];
    console.log(module);

    if (clickedButton.value === "sessionFile"){
        setRequiredAndEnabled(module + "UploadedSessionFile")
        removeRequiredAndEnabled(module + "EnteredJobId")
    }
    else if (clickedButton.value === "jobID"){
        removeRequiredAndEnabled(module + "UploadedSessionFile")
        setRequiredAndEnabled(module + "EnteredJobId")
    }
}


// When option 5 becomes checked: uncheck option 1 and 2, and make them unclickable