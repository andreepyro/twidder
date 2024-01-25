// VIEWS

// displayView = function(){
//     // the code required to display a view
// };

window.onload = function() {
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
    let token = localStorage.getItem("token");
    if (userData != null && token!=null) {

        let htmlWall = document.getElementById("wall");
        if (htmlWall != null) {
            let result = serverstub.getUserMessagesByToken(token);
            if (result["success"]){
                let messages = result["data"]
                for (var i = 0; i < messages.length; i++) {
                    const newPostHtml = document.createElement("div");
                    const node = document.createTextNode(messages[i]["content"]);
                    newPostHtml.appendChild(node);
                    newPostHtml.classList.add("post");
                    htmlWall.appendChild(newPostHtml);
                  }  

            }   
        }

        let htmlHomeUsername = document.getElementById("home-username");
        if (htmlHomeUsername != null) {
            htmlHomeUsername.innerHTML = userData.firstname + " " + userData.familyname;
        }

        let htmlHomeGender = document.getElementById("home-gender");
        if (htmlHomeGender != null) {
            htmlHomeGender.innerHTML = userData.gender;
        }

        let htmlHomeLocation = document.getElementById("home-location");
        if (htmlHomeLocation != null) {
            htmlHomeLocation.innerHTML = userData.city + ", " + userData.country;
        }

        let htmlHomeEmail = document.getElementById("home-email");
        if (htmlHomeEmail != null) {
            htmlHomeEmail.innerHTML = userData.email;
        }

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
            showMessage("tab doesn't exist!");
    }

    jumpToStart();
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
        showMessage(result["message"]);
        return false;
    }
}

// LOGOUT

function logout() {
    let token = localStorage.getItem("token");
    localStorage.removeItem("token");

    let result = serverstub.signOut(token);

    if (!result["success"]) {
        showMessage(result["message"]);
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
        showMessage("Passwords doesn't match!");
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
        showMessage(result["message"]);
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
        showMessage("New password can't be the same!");
        return
    }

    if (passwordNew != passwordNew2) {
        showMessage("Passwords doesn't match!");
        return
    }

    let token = localStorage.getItem("token");
    if (token === null) {
        showMessage("You need to be signed in!");
        return
    }

    let result = serverstub.changePassword(token, passwordOld, passwordNew);
    showMessage(result["message"]);
    if (result["success"]) {
        showView("user-view");
    }
}

// ADD POST

function addPost() {
    let token = localStorage.getItem("token");
    let userData = getUserData();

    if (token == null || userData == null) {
        return;
    }

    let wallHtml = document.getElementById("wall");
    let newPostBoxHtml = document.getElementById("input-post-bar");
    let userMessage = newPostBoxHtml.value;

    let result = serverstub.postMessage(token, userMessage, userData.email)
    if (!result["success"]) {
        showMessage(result["message"]);
        return;
    }   

    newPostBoxHtml.value = "";
    const newPostHtml = document.createElement("div");
    const node = document.createTextNode(userMessage);
    newPostHtml.appendChild(node);
    newPostHtml.classList.add("post");
    newPostHtml.style.animation = "appear 1s";
    wallHtml.insertBefore(newPostHtml, wallHtml.firstChild);

    setTimeout(function(){ newPostHtml.style.animation = ""; }, 1500);
}

function addPostOnWall() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showMessage("You need to be signed in!");
        return;
    }

    let userData = getUserData();
    if (userData == null) {
        showMessage("Couldn't load user data!");
        return;
    }

    let userEmailHtml = document.getElementById("browse-user-email");
    let wallHtml = document.getElementById("browse-wall");
    let newPostBoxHtml = document.getElementById("input-browse-new-post");
    let userEmail = userEmailHtml.innerHTML;
    let userMessage = newPostBoxHtml.value;

    let result = serverstub.postMessage(token, userMessage, userEmail)
    if (!result["success"]) {
        showMessage(result["message"]);
        return;
    }   

    newPostBoxHtml.value = "";
    let postTemplateHtml = document.getElementById("browse-post-template").innerHTML;
    const newPostHtml = document.createElement("div");
    newPostHtml.innerHTML = postTemplateHtml;
    newPostHtml.children[0].innerHTML = userData.email;
    const textNode = document.createTextNode(userMessage);
    newPostHtml.children[1].appendChild(textNode);
    newPostHtml.classList.add("browse-post");
    newPostHtml.style.animation = "appear 1s";
    wallHtml.insertBefore(newPostHtml, wallHtml.childNodes[2]);

    setTimeout(function(){ newPostHtml.style.animation = ""; }, 1500);
}

// SEARCH USER
function searchUser() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showMessage("You need to be signed in!");
        return;
    }

    let searchInputHtml = document.getElementById("input-user-email");
    let userEmail = searchInputHtml.value;

    let userDataResult = serverstub.getUserDataByEmail(token, userEmail);
    if (!userDataResult["success"]) {
        showMessage(userDataResult["message"]);
        return;
    }

    let userData = userDataResult["data"];

    let searchButtonHtml = document.getElementById("browse-search-button");
    searchButtonHtml.innerHTML = "Reload";

    let containerUserPage = document.getElementById("container-user-page");
    containerUserPage.style.display = "block";

    let userNameHtml = document.getElementById("browse-user-name");
    userNameHtml.innerHTML = userData.firstname + " " + userData.familyname;

    let userGenderHtml = document.getElementById("browse-user-gender");
    userGenderHtml.innerHTML = userData.gender;

    let userLocationHtml = document.getElementById("browse-user-location");
    userLocationHtml.innerHTML = userData.city + ", " + userData.country;

    let userEmailHtml = document.getElementById("browse-user-email");
    userEmailHtml.innerHTML = userData.email;

    let htmlWall = document.getElementById("browse-wall");
    let userPostsResult = serverstub.getUserMessagesByEmail(token, userEmail);
    if (!userPostsResult["success"]){
        showMessage(userPostsResult["message"]);
    }
    let userMessages = userPostsResult["data"]

    let oldPosts = document.getElementsByClassName("browse-post");
    for (var i = oldPosts.length - 1; i >= 0; i--) {
        oldPosts[i].remove();
    }


    let postTemplateHtml = document.getElementById("browse-post-template").innerHTML;
    for (let i = 0; i < userMessages.length; i++) {
        const newPostHtml = document.createElement("div");
        newPostHtml.innerHTML = postTemplateHtml;
        newPostHtml.children[0].innerHTML = userMessages[i]["writer"];
        const textNode = document.createTextNode(userMessages[i]["content"]);
        newPostHtml.children[1].appendChild(textNode);
        newPostHtml.classList.add("browse-post");
        htmlWall.appendChild(newPostHtml);
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

function searchButtonUpdate() {
    let searchButtonHtml = document.getElementById("browse-search-button");
    searchButtonHtml.innerHTML = "Search";
}

var lastYPos = window.scrollY;
window.onscroll = function() {
  let searchFormHtml = document.getElementById("form-search-user");
  let currentYPos = window.scrollY;
  if (lastYPos > currentYPos) {
    searchFormHtml.style.top = "0px";
  } else {
    searchFormHtml.style.top = "-60px";
  }
  lastYPos = currentYPos;

  let jumpToStartHtml = document.getElementById("jump-to-start");
  if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
    jumpToStartHtml.style.bottom = "20px";
  } else {
    jumpToStartHtml.style.bottom = "-60px";
  }
}

function jumpToStart() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}

// POPUP MESSAGE

function showMessage(message) {
    let messageHtml = document.getElementById("pop-message");
    if (!messageHtml.classList.contains('show')) {
        messageHtml.className = "show";
        setTimeout(function(){ messageHtml.className = messageHtml.className.replace("show", ""); }, 4500);
    }
}
