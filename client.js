displayView = function(){
    // the code required to display a view
};

// window.onload = function(){
//     showView("welcome-view")
// };

function showView(viewName) {
    let html = document.getElementById(viewName).innerHTML;
    document.getElementById("content").innerHTML = html;
}

function signUp() {
    if (isSignUpFormValid) {
        // TODO
    }
}

function isSignUpFormValid() {
    // check for blank fields
    if (document.getElementById("").value == "") {
        return false
    }
    if (document.getElementById("").value == 0) {
        return false
    }
    if (document.getElementById("").value == 0) {
        return false
    }
    if (document.getElementById("").value == 0) {
        return false
    }
    if (document.getElementById("").value == 0) {
        return false
    }
    if (document.getElementById("").value == 0) {
        return false
    }
    if (document.getElementById("").value == 0) {
        return false
    }
    if (document.getElementById("").value == 0) {
        return false
    }
    return true
}