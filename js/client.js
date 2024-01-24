// VIEWS

// displayView = function(){
//     // the code required to display a view
// };

window.onload = function(){
    let token = localStorage.getItem("token");
    if (token != null && getUserData(token) != null) {
        showView("user-view");
    } else {
        showView("welcome-view");
    }
};

function showView(viewName) {
    // load view
    let html = document.getElementById(viewName).innerHTML;
    document.getElementById("content").innerHTML = html;

    // show user content
    let userData = getUserData();
    if (userData != null) {
        let htmlAccountUsername = document.getElementById("account-username");
        if (htmlAccountUsername != null) {
            htmlAccountUsername.innerHTML = userData.firstname + " " + userData.familyname;
        }

        let htmlAccountGender = document.getElementById("account-gender");
        if (htmlAccountGender != null) {
            htmlAccountGender.innerHTML = userData.gender;
        }

        let htmlAccountLocation = document.getElementById("account-location");
        if (htmlAccountLocation != null) {
            htmlAccountLocation.innerHTML = userData.city + ", " + userData.country;
        }

        let htmlAccountEmail = document.getElementById("account-email");
        if (htmlAccountEmail != null) {
            htmlAccountEmail.innerHTML = userData.email;
        }
    }
}

function showTab(tabName) {
    let homeTabButton = document.getElementById("sidebar-tab-home");
    let browseTabButton = document.getElementById("sidebar-tab-browse");
    let accountTabButton = document.getElementById("sidebar-tab-account");

    if (homeTabButton.classList.contains('active')) {
        homeTabButton.classList.remove("active");
    }
    if (browseTabButton.classList.contains('active')) {
        browseTabButton.classList.remove("active");
    }
    if (accountTabButton.classList.contains('active')) {
        accountTabButton.classList.remove("active");
    }

    let homeTab = document.getElementById("tab-home");
    let browseTab = document.getElementById("tab-browse");
    let accountTab = document.getElementById("tab-account");

    homeTab.style.display = "none";
    browseTab.style.display = "none";
    accountTab.style.display = "none";

    switch(tabName) {
        case "home":
            homeTabButton.classList.add("active");
            homeTab.style.display = "flex";
            break;
        case "browse":
            browseTab.style.display = "flex";
            browseTabButton.classList.add("active");
            break;
        case "account":
            accountTab.style.display = "flex";
            accountTabButton.classList.add("active");
            break;
        default:
            alert("tab doesn't exist!");
    }
}

// LOGIN

function loginForm(form) {
    let email = form["input-login-email"].value;
    let password = form["input-login-password"].value;
    return login(email, password);
}

function login(email, password) {
    let result = serverstub.signIn(email, password);

    if (result["success"]) {
        let token = result["data"];
        localStorage.setItem("token", token);
        showView("user-view");
        return true;
    } else {
        alert(result["message"]);
        return false;
    }
}

// LOGOUT

function logout() {
    let token = localStorage.getItem("token");
    localStorage.removeItem("token");

    let result = serverstub.signOut(token);

    if (!result["success"]) {
        alert(result["message"]);
    }

    showView("welcome-view");
}

// REGISTER

function registerForm(form) {
    let firstName = form["input-sign-up-first-name"].value;
    let familyName = form["input-sign-up-last-name"].value;
    let gender = form["input-sign-up-gender"].value;
    let city = form["input-sign-up-city"].value;
    let country = form["input-sign-up-country"].value;
    let email = form["input-sign-up-email"].value;
    let password = form["input-sign-up-password"].value;
    let password2 = form["input-sign-up-password-repeat"].value;

    if (password != password2) {
        alert("Passwords doesn't match!");
        return
    }

    let user = {
        email: email,
        password: password,
        firstname: firstName,
        familyname: familyName,
        gender: gender,
        city: city,
        country: country,
    };

    let result = serverstub.signUp(user);

    if (result["success"]) {
        login(email, password);
    } else {
        alert(result["message"]);
    }
}

// USER DATA

function getUserData() {
    let token = localStorage.getItem("token");
    if (token === null) {
        return null;
    }

    let result = serverstub.getUserDataByToken(token);
    if (!result["success"]) {
        return null;
    }

    return result["data"];
}

// CHANGE PASSWORD

function changedPasswordForm(form) {
    let passwordOld = form["input-change-password-old"].value;
    let passwordNew = form["input-change-password-new"].value;
    let passwordNew2 = form["input-change-password-new-repeat"].value;

    if (passwordNew == passwordOld) {
        alert("New password can't be the same!");
        return
    }

    if (passwordNew != passwordNew2) {
        alert("Passwords doesn't match!");
        return
    }

    let token = localStorage.getItem("token");
    if (token === null) {
        alert("You need to be signed in!");
        return
    }

    let result = serverstub.changePassword(token, passwordOld, passwordNew);
    alert(result["message"]);
    if (result["success"]) {
        showView("user-view");
    }
}

// INTERACTIVE CSS

function checkSamePasswords(htmlPassword, htmlPassword2) {
    let password1 = document.getElementById(htmlPassword);
    let password2 = document.getElementById(htmlPassword2);
    if (password1.value == password2.value) {
        password1.setCustomValidity("");
        password2.setCustomValidity("");
    } else {
        password1.setCustomValidity("Passwords doesn't match!");
        password2.setCustomValidity("Passwords doesn't match!");
    }
}
