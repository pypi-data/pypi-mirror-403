var findDocumentsFromUserInput = function(e){
    $("#semantic_search_docs_results").html("")
    query = $("#sem_search_input").val();
    findDocuments(query);
}

var findDocuments = function(query, callback){
    if (typeof query == "undefined" || query == ""){
        html_str = "<div class='text-danger d-flex align-items-center justify-content-center'>No documents found...</div>"
        $("#semantic_search_docs_results").html(html_str)
        return
    }
    $("#semantic_search_docs_results").html("<div class=\"loading-docs d-flex align-items-center justify-content-center\"><div class=\"spinner-border\" role=\"status\"><span class=\"sr-only\">Loading...</span></div></div>");

    threshold = $("#sem_settings_threshold").val()
    top_k = $("#sem_settings_top_k").val()

    var payload = {
      query: query,
      threshold: threshold,
      top_k: top_k,
    }

    $("#results_infos").html("-");
    $.ajax({
      url: semanticSearchUrl,
      type : "POST",
      dataType: "json",
      data: payload,
      success: function( data ){
        if (!data || data.length === 0) {
            $("#semantic_search_docs_results").html(
                "<div class='text-danger d-flex align-items-center justify-content-center'>No documents found...</div>"
            );
            if (callback) callback();
            return;
        }
        $("#results_infos").html(data.length);

        $("#semantic_search_docs_results").empty();
        const docsMap = groupSnippetsByDoc(data);
        const sortedDocs = sortDocsByRelevance(docsMap);
        sortedDocs.forEach(renderDocument);

        if (callback) {callback();}
      },
      error: function(data){
        // Show an error
        html_str = "<div class='card'><div class='card-body text-danger'>"
        html_str += data.responseJSON["message"]
        html_str += "</div></div>"
        $("#semantic_search_docs_results").html(html_str)
        $.notify("An error occurred.", "danger");
       }
    });
}

var groupSnippetsByDoc = function(rawData) {
    const docs = {};
    const distance = isDistanceMetrics();

    rawData.forEach((item, idx) => {
        const docId = item["data_id"];
        if (!docId) return;

        // Init document entry first time we see a new id
        if (!docs[docId]) {
            const hasPid = item["data_pid"] && item["data_pid"] !== 'None';
            const href   = hasPid ? item["data_pid"] : "/data?id=" + docId;

            docs[docId] = {
                data_id:    docId,
                title:      item["data_title"] || '',
                url:        href,
                bestScore:   distance ? +Infinity : -Infinity,
                snippets:   []
            };
        }

        // Save highest score
        const curScore = item["score"];
        if (curScore !== undefined && curScore !== null) {
            if (distance){
                if (curScore < docs[docId].bestScore) docs[docId].bestScore = curScore;
            }else{
                if (curScore > docs[docId].bestScore) docs[docId].bestScore = curScore;
            }
        }

        docs[docId].snippets.push({
            idx:        idx,
            content:    item["content"]  || '',
            score:      curScore,
            snippet_id: item["snippet_id"] || null
        });
    });

    Object.values(docs).forEach(doc => {
        doc.snippets.sort((a, b) => {
            const sA = a.score ?? -Infinity;
            const sB = b.score ?? -Infinity;
            return distance ? (sA - sB) : (sB - sA);
        });
    });

    return docs;
}

var sortDocsByRelevance = function(docsMap) {
    const distance = isDistanceMetrics();
    return Object.values(docsMap).sort((a, b) => {
        const sA = a.bestScore === -Infinity ? -1 : a.bestScore;
        const sB = b.bestScore === -Infinity ? -1 : b.bestScore;
        return distance ? (sA - sB) : (sB - sA);
    });
}

var isDistanceMetrics = function(){
    const func = $("#semantic_search_vector_function").attr("data-vector-func");
    return func === "l2_distance"
}

function renderDocument(doc) {
    let html = "<div class='card mb-3'><div class='card-body'>";

    // Document title with link
    html += "<a class='answer_link' target='_blank' href='" + doc.url + "'>"
          +   doc.title
          + "</a>";

    // Render all snippets of document
    doc.snippets.forEach(snippet => {
        const dataIdAttr    = " data-id='" + doc.data_id + "' ";
        const snippetIdAttr = snippet.snippet_id ? " data-snippet-id='" + snippet.snippet_id + "' " : "";
        const collapseId = "collapseText" + snippet.idx;

        html += "<div class='doc' " + dataIdAttr + snippetIdAttr + ">";

        // Expand buttons
        html += "<a data-toggle='collapse' role='button' aria-expanded='false' "
             +    "data-target='#" + collapseId + "' aria-controls='" + collapseId + "'>"
             +    "<i class='fas fa-caret-right collapseBtn'></i>"
             + "</a> ";

        // Similarity Score
        if (snippet.score) {
            html += showScore(snippet.score);
        }

        // Snippet content
        html += "<div class='collapse' id='" + collapseId + "'>"
             +   "<div class='card card-body'>"
             +   snippet.content
             +   "</div></div>";
    });

    html += "</div>";
    html += "</div></div>";

    $("#semantic_search_docs_results").append(html);
}

var showScore = function(score_str){
    const funcDisplay = $("#semantic_search_vector_function_display").attr("data-vector-func-disp");
    let html_score = "";
    let score = Math.round(parseFloat(score_str) * 100) / 100;

    html_score += "<span class=\"badge bg-secondary score_badge\" title=\""+ funcDisplay +"\">"
    html_score += score
    html_score += "</span>"
    return html_score
}

var collapseDocument  = function(e){
    let btn = e.target;
    let target = $(btn).parent().attr("data-target");
    $(target).collapse("toggle");
    if ($(btn).hasClass("fa-caret-right")) {
        $(btn).removeClass("fa-caret-right");
        $(btn).addClass("fa-caret-down");
    } else{
        $(btn).removeClass("fa-caret-down");
        $(btn).addClass("fa-caret-right");
    }
};

var showSettings = function(){
    $( "#semantic-search-settings-modal" ).modal('show');
}

var configureMinScoreSlider = function(){
    const $slider = $("#sem_settings_threshold");
    const $output = $("#sem_settings_threshold_output");
    const distance = isDistanceMetrics();

    if (distance) {
        $slider.attr({
            min: 0,
            max: 10,
            step: 0.1,
            value: 2
        });
        $output.text($slider.val());
    }else{
        $slider.attr({
            min: 0,
            max: 1,
            step: 0.01,
            value: 0.4
        });
        $output.text($slider.val());
    }
    $slider.off('input').on('input', function(){
        $output.text(this.value);
    });
}

$("#semantic_search_form").submit(function(e) {
    e.preventDefault();
    findDocumentsFromUserInput();
});


$(document).on('click', '#search_btn', findDocumentsFromUserInput);
$(document).on('click', '.collapseBtn', collapseDocument);
$(document).on('click', '.semantic_search_settings', showSettings);
$(document).ready(function () {
    configureMinScoreSlider();
});