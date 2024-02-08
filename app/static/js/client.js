// Constants
const HOST = "http://localhost:8080";

// Extending localStorage to object (credits: https://stackoverflow.com/a/3146971)
Storage.prototype.setObject = function (key, value) {
    this.setItem(key, JSON.stringify(value));
}

Storage.prototype.getObject = function (key) {
    let value = this.getItem(key);
    return value && JSON.parse(value);
}

// App state management
window.onload = function() {
    // page load
    loadApp().then();
};

window.addEventListener('popstate', function(e) {
    // going back/forward using history API
    loadApp().then(); // TODO don't load the whole app, but decide here (so we don't fetch user data all over again)
});

async function loadApp() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showView("welcome-view");
    }

    if (!await loadUserDataByToken(token)) {
        localStorage.setItem("token", null);
        localStorage.setItem("user", null);
        showMessage("You have been logged out.");
        showView("welcome-view");
    }

    showView("user-view");
}

function showView(viewName) {
    // load view
    document.getElementById("content").innerHTML = document.getElementById(viewName).innerHTML;
  
    // show user content
    let user = localStorage.getObject("user");
    if (user != null) {
        reloadHomeTab();

        // Account tab
        document.getElementById("input-account-first-name").value = user.first_name;
        document.getElementById("input-account-last-name").value = user.family_name;
        document.getElementById("input-account-city").value = user.city;
        document.getElementById("input-account-country").value = user.country;
        document.getElementById("input-account-gender").value = user.gender;
        document.getElementById("account-email").innerHTML = user.email;
    }

    // register gender selection
    let htmlSelect = document.getElementById("input-sign-up-gender");
    if (htmlSelect != null) {
        checkValidGender(htmlSelect);
    }

    // load correct tab
    if (viewName === "welcome-view") {
        history.pushState("welcome", '', "/");
    }
    if (viewName === "user-view") {
        if (window.location.pathname === "/browse") showTab("browse");
        else if (window.location.pathname === "/account") showTab("account");
        else showTab("home");
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

    let modifyHistory = window.location.pathname.split("/")[1] !== tabName;

    switch(tabName) {
        case "home":
            homeTabButton.classList.add("active");
            homeTab.style.display = "flex";
            document.title = "Twidder | Home";
            if (modifyHistory) history.pushState("home", '', "home");
            break;
        case "browse":
            browseTab.style.display = "flex";
            browseTabButton.classList.add("active");
            document.title = "Twidder | Browse";
            if (modifyHistory) history.pushState("browse", '', "browse");
            break;
        case "account":
            accountTab.style.display = "flex";
            accountTabButton.classList.add("active");
            document.title = "Twidder | Account";
            if (modifyHistory) history.pushState("account", '', "account");
            break;
        default:
            showMessage("tab doesn't exist!");
    }

    jumpToStart();
}

async function login(email, password) {
    // create a new session
    const response = await fetch(HOST + "/sign_in", {
        method: "POST",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            email: email,
            password: password,
        }),
    });

    if (response.status === 401) {
        showMessage("Invalid username or password.");
    } else if (response.status !== 200) {
        showMessage("Error");
        return;
    }

    // load & save data
    let token = response.headers.get("Authorization");
    if (!await loadUserDataByToken(token)) {
        showMessage("Error");
        return;
    }
    localStorage.setItem("token", token);

    // reload app content
    loadApp().then();
}

async function loadUserDataByToken(token) {
    let userDataRequest = fetch(HOST + "/get_user_data_by_token", {
        method: "GET",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });
    let userPostsRequest = fetch(HOST + "/get_user_messages_by_token", {
        method: "GET",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });

    const userDataResponse = await userDataRequest;
    const userPostsResponse = await userPostsRequest;

    if (userDataResponse.status !== 200 || userPostsResponse.status !== 200) {
        return false;
    }

    let user = await userDataResponse.json();
    let posts = await userPostsResponse.json();

    localStorage.setObject("user", user);
    localStorage.setObject("posts", posts.posts);

    return true;
}

async function logout() {
    let token = localStorage.getItem("token");

    // TODO IMPLEMENT ME

    localStorage.removeItem("token");
    loadApp().then();
}

async function changedPasswordForm(form) {
    let passwordOld = form["input-change-password-old"].value;
    let passwordNew = form["input-change-password-new"].value;
    let passwordNew2 = form["input-change-password-new-repeat"].value;

    if (passwordNew === passwordOld) {
        showMessage("New password can't be the same!");
        return
    }

    if (passwordNew !== passwordNew2) {
        showMessage("Passwords doesn't match!");
        return
    }

    let token = localStorage.getItem("token");
    if (token == null) {
        showMessage("Error: couldn't load token");
        return;
    }

    // TODO implement me

    showTab("home"); // TODO only when successful
}

// ADD POST

async function addPostHome() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showMessage("Error: couldn't load token");
        return;
    }

    let user = localStorage.getObject("user");
    if (user == null) {
        showMessage("Error: couldn't load user data");
        return;
    }

    let wallHtml = document.getElementById("home-wall");
    let newPostBoxHtml = document.getElementById("input-home-new-post");
    let userMessage = newPostBoxHtml.value;

    // TODO implement me

    newPostBoxHtml.value = "";
    let postTemplateHtml = document.getElementById("home-post-template").innerHTML;
    const newPostHtml = document.createElement("div");
    newPostHtml.innerHTML = postTemplateHtml;
    newPostHtml.children[0].innerHTML = "now";
    newPostHtml.children[1].innerHTML = user.email;
    const textNode = document.createTextNode(userMessage);
    newPostHtml.children[2].appendChild(textNode);
    newPostHtml.classList.add("home-post");
    newPostHtml.style.animation = "home-post-appear 1.5s";
    newPostHtml.children[3].style.animation = "home-post-appear-inner 2.0s";
    newPostHtml.children[4].style.animation = "home-post-appear-inner 2.0s";
    wallHtml.insertBefore(newPostHtml, wallHtml.childNodes[2]);

    setTimeout(function () {
        newPostHtml.style.animation = "";
        newPostHtml.children[3].style.animation = "";
        newPostHtml.children[4].style.animation = "";
    }, 2000);
}

async function addPostBrowse() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showMessage("Error: couldn't load token");
        return;
    }

    let user = localStorage.getObject("user");
    if (user == null) {
        showMessage("Error: couldn't load user data");
        return;
    }

    let userEmailHtml = document.getElementById("browse-user-email");
    let wallHtml = document.getElementById("browse-wall");
    let newPostBoxHtml = document.getElementById("input-browse-new-post");
    let userEmail = userEmailHtml.innerHTML;
    let userMessage = newPostBoxHtml.value;

    // TODO implement me

    newPostBoxHtml.value = "";
    let postTemplateHtml = document.getElementById("browse-post-template").innerHTML;
    const newPostHtml = document.createElement("div");
    newPostHtml.innerHTML = postTemplateHtml;
    newPostHtml.children[0].innerHTML = user.email;
    const textNode = document.createTextNode(userMessage);
    newPostHtml.children[1].appendChild(textNode);
    newPostHtml.classList.add("browse-post");
    newPostHtml.style.animation = "browse-post-appear 1s";
    newPostHtml.children[3].style.animation = "browse-post-appear-inner 2.0s";
    newPostHtml.children[4].style.animation = "browse-post-appear-inner 2.0s";
    wallHtml.insertBefore(newPostHtml, wallHtml.childNodes[2]);

    setTimeout(function () {
        newPostHtml.style.animation = "";
        newPostHtml.children[3].style.animation = "";
        newPostHtml.children[4].style.animation = "";
    }, 2000);
}

function reloadHomeTab() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showMessage("Error: couldn't load token");
        return;
    }

    let user = localStorage.getObject("user");
    if (user == null) {
        showMessage("Error: couldn't load user data");
        return;
    }

    document.getElementById("home-user-name").innerHTML = user.first_name + " " + user.family_name;
    document.getElementById("home-user-gender").innerHTML = user.gender;
    document.getElementById("home-user-location").innerHTML = user.city + ", " + user.country;
    document.getElementById("home-user-email").innerHTML = user.email;

    let htmlWall = document.getElementById("home-wall");

    let posts = localStorage.getObject("posts");
    if (posts == null) {
        showMessage("Error: couldn't load user posts");
        return;
    }

    let oldPosts = document.getElementsByClassName("home-post");
    for (let i = oldPosts.length - 1; i >= 0; i--) {
        oldPosts[i].remove();
    }

    let postTemplateHtml = document.getElementById("home-post-template").innerHTML;
    for (let i = 0; i < posts.length; i++) {
        const newPostHtml = document.createElement("div");
        newPostHtml.innerHTML = postTemplateHtml;
        newPostHtml.children[0].innerHTML = posts[i]["edited"]; // TODO for created != edited show edited icon
        newPostHtml.children[1].innerHTML = posts[i]["author"];
        const textNode = document.createTextNode(posts[i]["content"]);
        newPostHtml.children[2].appendChild(textNode);
        newPostHtml.children[3].setAttribute("id", posts[i]["id"]);
        newPostHtml.children[4].setAttribute("id", posts[i]["id"]);
        newPostHtml.classList.add("home-post");
        htmlWall.appendChild(newPostHtml);
    }
}

async function searchUser() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showMessage("Error: couldn't load token");
        return;
    }

    let searchInputHtml = document.getElementById("input-user-email");
    let userEmail = searchInputHtml.value;

    // TODO implement me

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

    // TODO implement me

    let userMessages = userPostsResult["data"]

    let oldPosts = document.getElementsByClassName("browse-post");
    for (var i = oldPosts.length - 1; i >= 0; i--) {
        oldPosts[i].remove();
    }


    let postTemplateHtml = document.getElementById("browse-post-template").innerHTML;
    for (let i = 0; i < userMessages.length; i++) {
        const newPostHtml = document.createElement("div");
        newPostHtml.innerHTML = postTemplateHtml;
        newPostHtml.children[0].innerHTML = userMessages[i]["author"];
        const textNode = document.createTextNode(userMessages[i]["content"]);
        newPostHtml.children[1].appendChild(textNode);
        newPostHtml.children[3].setAttribute("id", userMessages[i]["id"]);
        newPostHtml.children[4].setAttribute("id", userMessages[i]["id"]);
        newPostHtml.classList.add("browse-post");
        htmlWall.appendChild(newPostHtml);
    }
}

async function editHomePost(button) {
    let postID = button.getAttribute("id");
    alert("EDIT POST: " + postID); // TODO IMPLEMENT ME
}

async function editBrowsePost(button) {
    let postID = button.getAttribute("id");
    alert("EDIT POST: " + postID); // TODO IMPLEMENT ME
}

async function deleteHomePost(button) {
    let postID = button.getAttribute("id");
    alert("DELETE POST: " + postID); // TODO IMPLEMENT ME
}

async function deleteBrowsePost(button) {
    let postID = button.getAttribute("id");
    alert("DELETE POST: " + postID); // TODO IMPLEMENT ME
}

// INTERACTIVE CSS ELEMENTS

function checkSamePasswords(htmlPassword, htmlPassword2) {
    let password1 = document.getElementById(htmlPassword);
    let password2 = document.getElementById(htmlPassword2);
    if (password1.value === password2.value) {
        password1.setCustomValidity("");
        password2.setCustomValidity("");
    } else {
        password1.setCustomValidity("Passwords doesn't match!");
        password2.setCustomValidity("Passwords doesn't match!");
    }
}

function checkValidGender(htmlSelect) {
    if (htmlSelect.value === "") {
        htmlSelect.setCustomValidity("Please select your gender!");
    } else {
        htmlSelect.setCustomValidity("");
    }
}

function searchButtonUpdate() {
    let searchButtonHtml = document.getElementById("browse-search-button");
    searchButtonHtml.innerHTML = "Search";
}

var lastYPos = window.scrollY;
window.onscroll = function() {
    // show search bar
    let searchFormHtml = document.getElementById("form-search-user");
    let currentYPos = window.scrollY;
        if (lastYPos > currentYPos) {
        searchFormHtml.style.top = "0px";
    } else {
        searchFormHtml.style.top = "-60px";
    }
    lastYPos = currentYPos;

    // show jump button
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

function showMessage(message) {
    let messageHtml = document.getElementById("pop-message");
    messageHtml.innerHTML = message;
    if (!messageHtml.classList.contains('show')) {
        messageHtml.className = "show";
        setTimeout(function() {
            messageHtml.innerHTML = "";
            messageHtml.className = messageHtml.className.replace("show", "");
        }, 4500);
    }
}

function showRegisterContainer() {
    document.getElementById("register-container").style.display = "block";
}

function hideRegisterContainer() {
    document.getElementById("register-container").style.display = "none";
}

document.addEventListener('keydown', function (e) {
    if (e.key === "Escape") {
        // close register form if visible
        if (document.getElementById("register-container").style.display === "block") {
            document.getElementById("register-container").style.display = "none";
        }
    }
});

window.onclick = function (event) {
    if (event.target === document.getElementById("register-container")) {
        hideRegisterContainer();
    }
}

async function formLogin(form) {
    let email = form["input-login-email"].value;
    let password = form["input-login-password"].value;
    await login(email, password);
}

async function formRegister(form) {
    let firstName = form["input-sign-up-first-name"].value;
    let familyName = form["input-sign-up-last-name"].value;
    let gender = form["input-sign-up-gender"].value;
    let city = form["input-sign-up-city"].value;
    let country = form["input-sign-up-country"].value;
    let email = form["input-sign-up-email"].value;
    let password = form["input-sign-up-password"].value;
    let password2 = form["input-sign-up-password-repeat"].value;

    if (password !== password2) {
        showMessage("Passwords doesn't match!");
        return
    }

    if (!["Male", "Female", "Other"].includes(gender)) {
        showMessage("Invalid gender!")
        return
    }

    const response = await fetch(HOST + "/sign_up", {
        method: "POST",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            email: email,
            password: password,
            firstname: firstName,
            familyname: familyName,
            gender: gender,
            city: city,
            country: country,
        }),
    });

    switch (response.status) {
        case 200: // Ok
            await login(email, password);
            break;
        case 404: // Forbidden
            showMessage("Invalid data!"); // TODO decide on error message
            break
        default:
            showMessage("Error");
    }
}
