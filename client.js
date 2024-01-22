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
    // check for blank fields
    let password = document.getElementById("input-sign-up-password").innerHTML = html;
    let repeat_pwd = document.getElementById("input-sign-up-password-repeat").innerHTML = html;

    if (password != repeat_pwd){
        return false
    }

    return true
}