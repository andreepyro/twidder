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
    if (isSignUpFormValid()) {
        alert("valid")
    } else {
        alert("invalid")
    }
}

function login() {
    alert("login")
}

function isSignUpFormValid() {
    // TODO implement
    return true
}