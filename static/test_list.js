function ShowTest(tag_id){
    var tag = document.getElementById(tag_id);
    tag.classList.remove("no_view")
}

function CancelTest(tag_id){
    var tag = document.getElementById(tag_id);
    tag.classList.add("no_view")
}

function DownloadTests(tag_id){
    var tag = document.getElementById(tag_id);
    tag.class.remove('download_tests')
}
