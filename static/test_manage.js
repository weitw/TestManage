function ShowTest(tag_id){
    var tag = document.getElementById(tag_id);
    tag.classList.remove("is_view")
}

function CancelTest(tag_id){
    var tag = document.getElementById(tag_id);
    tag.classList.add("is_view")
}

function DownlodTests(tag_id){
    var tag = document.getElementById(tag_id);
    tag.class.remove('download_tests')
}
