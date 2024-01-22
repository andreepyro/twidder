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
        // TODO
    } else {
        alert("passwords doesn't match!")
    }
}

function login() {
    alert("login")
}

function isSignUpFormValid() {
    let password1 = document.getElementById("input-sign-up-password");
    let password2 = document.getElementById("input-sign-up-password-repeat");

    if (password1.value != password2.value){
        return false
    }

    return true
}

function checkSamePasswords() {
    let password1 = document.getElementById("input-sign-up-password");
    let password2 = document.getElementById("input-sign-up-password-repeat");
    if (password1.value == password2.value) {
        password1.style.color = "green";
        password2.style.color = "green";
    } else {
        password1.style.color = "red";
        password2.style.color = "red";
    }
}