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
    // check for blank fields
    let password = document.getElementById("input-sign-up-password").value;
    let repeat_pwd = document.getElementById("input-sign-up-password-repeat").value;

    //console.log(password)
    //console.log(repeat_pwd)

    if (password != repeat_pwd){
        return false
    }

    return true
}