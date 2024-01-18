displayView = function(){
    // the code required to display a view
};

window.onload = function(){
    showView("welcome-view")
};

function showView(viewName) {
    let html = document.getElementById(viewName).innerHTML;
    document.getElementById("content").innerHTML = html;
}