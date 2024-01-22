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

function saveUser(formData){
    let first_name = formData["input-sign-up-first-name"].value; 
    let family_name = formData["input-sign-up-last-name"].value; 
    let gender = formData["input-sign-up-gender"].value; 
    let city = formData["input-sign-up-city"].value; 
    let country = formData["input-sign-up-country"].value;
    let email = formData["input-sign-up-email"].value; 
    let password = formData["input-sign-up-password"].value; 

    var user ={
        email: email, 
        password: password,
        firstname: first_name, 
        familyname: family_name, 
        gender: gender, 
        city: city, 
        country: country,  
    };

    if (!serverstub.signUp(user)["success"]){
        //console.log(serverstub.signUp(user)["message"])
        return serverstub.signUp(user)["message"]  
    } else {
        //console.log(serverstub.signUp(user)["success"])
        return serverstub.signUp(user)["success"]
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