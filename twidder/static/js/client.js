// Constants
const HOST = "http://localhost:8080";

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
    let email = localStorage.getItem("email");
    if (token == null || email == null) {
        // data are manipulated or something is wrong
        localStorage.removeItem("token");
        localStorage.removeItem("email");
        showWelcomeView();
        return;
    }

    // TODO init socket
    // TODO load user data

    let success = true;
    if (!success) {
        localStorage.removeItem("token");
        localStorage.removeItem("email");
        showWelcomeView();
        showSuccess("You have been logged out.");
        return;
    }

    await showUserView();
}

function showWelcomeView() {
    // load view
    document.getElementById("content").innerHTML = document.getElementById("welcome-view").innerHTML;

    // history API
    history.pushState("welcome", "", "/");

    // register gender selection
    let htmlSelect = document.getElementById("input-sign-up-gender");
    if (htmlSelect != null) {
        checkValidGender(htmlSelect);
    }
}

async function showUserView() {
    // load view
    document.getElementById("content").innerHTML = document.getElementById("user-view").innerHTML;

    // history API
    if (window.location.pathname === "/browse") showTab("browse");
    else if (window.location.pathname === "/account") showTab("account");
    else showTab("home");

    // show user content
    await reloadUserData();
}

function showTab(tabName) {
    // deactivate all buttons
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

    // hide all tabs
    document.getElementById("tab-home").style.display = "none";
    document.getElementById("tab-browse").style.display = "none";
    document.getElementById("tab-account").style.display = "none";

    // activate correct button
    document.getElementById("sidebar-tab-" + tabName).classList.add("active");

    // show correct tab
    document.getElementById("tab-" + tabName).style.display = "flex";

    // change page title
    document.title = "Twidder | " + tabName.charAt(0).toUpperCase() + tabName.slice(1);

    // push new history state
    if (window.location.pathname.split("/")[1] !== tabName) {
        history.pushState(tabName, "", tabName);
    }

    // always show the top part of the page
    jumpToStart();
}

async function reloadUserData() {
    // load locally saved data
    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return;
    }

    // load user data
    let userDataRequest = fetch(HOST + "/api/v1/users/" + email, {
        method: "GET",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });
    let userPostsRequest = fetch(HOST + "/api/v1/posts?" + new URLSearchParams({user_email: email}).toString(), {
        method: "GET",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });
    let userDataResponse = await userDataRequest;
    let userPostsResponse = await userPostsRequest;

    if (userDataResponse.status !== 200 || userPostsResponse.status !== 200) {
        showError("Error")
        return false;
    }

    let user = await userDataResponse.json();
    let posts = (await userPostsResponse.json()).posts;

    // Home tab
    document.getElementById("home-user-name").innerHTML = user.firstname + " " + user.lastname;
    document.getElementById("home-user-gender").innerHTML = user.gender;
    document.getElementById("home-user-location").innerHTML = user.city + ", " + user.country;
    document.getElementById("home-user-email").innerHTML = user.email;

    // Account tab
    document.getElementById("input-account-first-name").value = user.firstname;
    document.getElementById("input-account-last-name").value = user.lastname;
    document.getElementById("input-account-city").value = user.city;
    document.getElementById("input-account-country").value = user.country;
    document.getElementById("input-account-gender").value = user.gender;
    document.getElementById("account-email").innerHTML = user.email;

    // User's posts
    let htmlWall = document.getElementById("home-wall");

    let oldPosts = document.getElementsByClassName("home-post");
    for (let i = oldPosts.length - 1; i >= 0; i--) {
        oldPosts[i].remove();
    }

    let postTemplateHtml = document.getElementById("home-post-template").innerHTML;
    for (let i = 0; i < posts.length; i++) {
        const newPostHtml = document.createElement("div");
        newPostHtml.innerHTML = postTemplateHtml;
        newPostHtml.children[0].innerHTML = getDateTimeFormat(new Date(posts[i]["edited"])); // TODO show icon for edited posts
        newPostHtml.children[1].innerHTML = posts[i]["author"];
        const textNode = document.createTextNode(posts[i]["content"]);
        newPostHtml.children[2].appendChild(textNode);
        newPostHtml.children[3].setAttribute("id", "home-post-id-" + posts[i]["id"]);
        newPostHtml.children[4].setAttribute("id", "home-post-id-" + posts[i]["id"]);
        newPostHtml.classList.add("home-post");
        htmlWall.appendChild(newPostHtml);
    }
}

async function login(email, password) {
    // create a new session
    const response = await fetch(HOST + "/api/v1/session", {
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
        showError("Invalid username or password.");
        return;
    } else if (response.status !== 200) {
        showError("Error");
        return;
    }

    let token = response.headers.get("Authorization");

    // save data locally
    localStorage.setItem("token", token);
    localStorage.setItem("email", email);

    // reload app content
    loadApp().then();
}


async function logout() {
    let token = localStorage.getItem("token");
    if (token != null) {
        const response = await fetch(HOST + "/api/v1/session", {
            method: "DELETE", cache: "no-cache", headers: {
                "Content-Type": "application/json", "Authorization": token,
            },
        });

        if (response.status !== 200) {
            showError("Error");
            return false;
        }
    }

    showSuccess("You have successfully logged out.")
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    loadApp().then();
}

async function formEditAccountDetails(form) {
    let firstName = form["input-account-first-name"].value;
    let lastName = form["input-account-last-name"].value;
    let city = form["input-account-city"].value;
    let country = form["input-account-country"].value;
    let gender = form["input-account-gender"].value;

    if (!["Male", "Female", "Other"].includes(gender)) {
        showError("Invalid gender!")
        return;
    }

    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return;
    }

    const response = await fetch(HOST + "/api/v1/users/" + email, {
        method: "PATCH",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
        body: JSON.stringify({
            firstname: firstName,
            lastname: lastName,
            gender: gender,
            city: city,
            country: country,
        }),
    });

    if (response.status !== 200) {
        showError("Error")
        return;
    }

    // update user data in home tab
    document.getElementById("home-user-name").innerHTML = firstName + " " + lastName;
    document.getElementById("home-user-gender").innerHTML = gender;
    document.getElementById("home-user-location").innerHTML = city + ", " + country;

    showSuccess("Account details successfully changed!");
}

async function formChangePassword(form) {
    let passwordOld = form["input-change-password-old"].value;
    let passwordNew = form["input-change-password-new"].value;
    let passwordNew2 = form["input-change-password-new-repeat"].value;
    
    if (passwordNew === passwordOld) {
        showError("New password can't be the same!");
        return
    }

    if (passwordNew !== passwordNew2) {
        showError("Passwords doesn't match!");
        return
    }

    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return;
    }

    let response = await fetch(HOST + "/api/v1/users/" + email, {
        method: "PATCH",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization" : token,
        },
        body: JSON.stringify({
            old_password: passwordOld,
            new_password: passwordNew,
        }),
    });

    if (response.status === 403) {
        showError("Invalid password.");
        return;
    } else if (response.status !== 200) {
        showError("Error");
        return;
    }

    showSuccess("Password successfully changed!");
    form["input-change-password-old"].value = "";
    form["input-change-password-new"].value = "";
    form["input-change-password-new-repeat"].value = "";
}

async function buttonDeleteUserAccount() {
    // TODO ask user if they are sure

    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return;
    }

    let response = await fetch(HOST + "/api/v1/users/" + email, {
        method: "DELETE",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });

    if (response.status !== 200) {
        showError("Error");
        return;
    }

    showSuccess("Account successfully deleted.")
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    loadApp().then();
}

async function addPostHome() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return;
    }

    let wallHtml = document.getElementById("home-wall");
    let newPostBoxHtml = document.getElementById("input-home-new-post");
    let userMessage = newPostBoxHtml.value;

    const response = await fetch(HOST + "/api/v1/posts", {
        method: "POST",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
        body: JSON.stringify({
            email: email,
            message: userMessage,
        }),
    });

    if (response.status === 403) {
        showError("User does not exist")
        return;
    } else if (response.status !== 200) {
        showError("Error")
        return;
    }

    let newPostID = (await response.json()).id

    newPostBoxHtml.value = "";
    let postTemplateHtml = document.getElementById("home-post-template").innerHTML;
    const newPostHtml = document.createElement("div");
    newPostHtml.innerHTML = postTemplateHtml;
    newPostHtml.children[0].innerHTML = getDateTimeFormat(new Date());
    newPostHtml.children[1].innerHTML = email;
    const textNode = document.createTextNode(userMessage);
    newPostHtml.children[2].appendChild(textNode);
    newPostHtml.classList.add("home-post");
    newPostHtml.style.animation = "home-post-appear 0.75s";
    newPostHtml.children[3].style.animation = "home-post-appear-inner 1.0s";
    newPostHtml.children[4].style.animation = "home-post-appear-inner 1.0s";
    newPostHtml.children[3].setAttribute("id", "home-post-id-" + newPostID);
    newPostHtml.children[4].setAttribute("id", "home-post-id-" + newPostID);
    wallHtml.insertBefore(newPostHtml, wallHtml.childNodes[2]);

    setTimeout(function () {
        newPostHtml.style.animation = "";
        newPostHtml.children[3].style.animation = "";
        newPostHtml.children[4].style.animation = "";
    }, 1000);
}

async function addPostBrowse() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return;
    }

    let userEmailHtml = document.getElementById("browse-user-email");
    let wallHtml = document.getElementById("browse-wall");
    let newPostBoxHtml = document.getElementById("input-browse-new-post");
    let userEmail = userEmailHtml.innerHTML;
    let userMessage = newPostBoxHtml.value;

    const response = await fetch(HOST + "/api/v1/posts", {
        method: "POST",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
        body: JSON.stringify({
            email: userEmail,
            message: userMessage,
        }),
    });

    if (response.status === 403) {
        showError("User does not exist")
        return;
    } else if (response.status !== 200) {
        showError("Error")
        return;
    }

    let newPostID = (await response.json()).id

    newPostBoxHtml.value = "";
    let postTemplateHtml = document.getElementById("browse-post-template").innerHTML;
    const newPostHtml = document.createElement("div");
    newPostHtml.innerHTML = postTemplateHtml;
    newPostHtml.children[0].innerHTML = getDateTimeFormat(new Date());
    newPostHtml.children[1].innerHTML = email;
    const textNode = document.createTextNode(userMessage);
    newPostHtml.children[2].appendChild(textNode);
    newPostHtml.classList.add("browse-post");
    newPostHtml.style.animation = "browse-post-appear 0.75s";
    newPostHtml.children[3].style.animation = "browse-post-appear-inner 1.0s";
    newPostHtml.children[4].style.animation = "browse-post-appear-inner 1.0s";
    newPostHtml.children[3].setAttribute("id", "browse-post-id-" + newPostID);
    newPostHtml.children[4].setAttribute("id", "browse-post-id-" + newPostID);
    wallHtml.insertBefore(newPostHtml, wallHtml.childNodes[2]);

    setTimeout(function () {
        newPostHtml.style.animation = "";
        newPostHtml.children[3].style.animation = "";
        newPostHtml.children[4].style.animation = "";
    }, 1000);
}

async function searchUser() {
    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let searchInputHtml = document.getElementById("input-user-email");
    let userEmail = searchInputHtml.value;

    let userDataRequest = fetch(HOST + "/api/v1/users/" + userEmail, {
        method: "GET",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });
    let userPostsRequest = await fetch(HOST + "/api/v1/posts?" + new URLSearchParams({user_email: userEmail}).toString(), {
        method: "GET",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });

    const userDataResponse = await userDataRequest;
    const userPostsResponse = await userPostsRequest;

    if (userDataResponse.status === 404 || userDataResponse.status === 404) {
        showInfo("User not found")
        return;
    } else if (userDataResponse.status !== 200 || userPostsResponse.status !== 200) {
        showError("Error")
        return;
    } 

    let userData = await userDataResponse.json();
    let posts = (await userPostsResponse.json()).posts;

    let searchButtonHtml = document.getElementById("browse-search-button");
    searchButtonHtml.innerHTML = "Reload";

    let containerUserPage = document.getElementById("container-user-page");
    containerUserPage.style.display = "block";

    let userNameHtml = document.getElementById("browse-user-name");
    userNameHtml.innerHTML = userData.firstname + " " + userData.lastname;

    let userGenderHtml = document.getElementById("browse-user-gender");
    userGenderHtml.innerHTML = userData.gender;

    let userLocationHtml = document.getElementById("browse-user-location");
    userLocationHtml.innerHTML = userData.city + ", " + userData.country;

    let userEmailHtml = document.getElementById("browse-user-email");
    userEmailHtml.innerHTML = userData.email;

    let htmlWall = document.getElementById("browse-wall");

    let oldPosts = document.getElementsByClassName("browse-post");
    for (let i = oldPosts.length - 1; i >= 0; i--) {
        oldPosts[i].remove();
    }

    let postTemplateHtml = document.getElementById("browse-post-template").innerHTML;
    for (let i = 0; i < posts.length; i++) {
        const newPostHtml = document.createElement("div");
        newPostHtml.innerHTML = postTemplateHtml;
        newPostHtml.children[0].innerHTML = getDateTimeFormat(new Date(posts[i]["edited"])); // TODO for created != edited show edited icon
        newPostHtml.children[1].innerHTML = posts[i]["author"];
        const textNode = document.createTextNode(posts[i]["content"]);
        newPostHtml.children[2].appendChild(textNode);
        newPostHtml.children[3].setAttribute("id", "browse-post-id-" + posts[i]["id"]);
        newPostHtml.children[4].setAttribute("id", "browse-post-id-" + posts[i]["id"]);
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
    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let postID = button.getAttribute("id").replace("home-post-id-", "");
    let response = await fetch(HOST + "/api/v1/posts/" + postID, {
        method: "DELETE",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });
    if (response.status === 404) {
        showError("Post not found")
        return;
    } else if (response.status !== 200) {
        showError("Error")
        return;
    }
    document.getElementById("home-post-id-" + postID).parentElement.remove(); // TODO animation
}

async function deleteBrowsePost(button) {
    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let postID = button.getAttribute("id").replace("browse-post-id-", "");
    let response = await fetch(HOST + "/api/v1/posts/" + postID, {
        method: "DELETE",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });
    if (response.status === 404) {
        showError("Post not found")
        return;
    } else if (response.status !== 200) {
        showError("Error")
        return;
    }
    document.getElementById("browse-post-id-" + postID).parentElement.remove(); // TODO animation
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

let lastYPos = window.scrollY;
window.onscroll = function() {
    // show search bar
    let currentYPos = window.scrollY;
    let searchFormHtml = document.getElementById("form-search-user");
    if (searchFormHtml != null) {
        if (lastYPos > currentYPos) {
            searchFormHtml.style.top = "0px";
        } else {
            searchFormHtml.style.top = "-60px";
        }
    }
    lastYPos = currentYPos;

    // show jump button
    let jumpToStartHtml = document.getElementById("jump-to-start");
    if (jumpToStartHtml != null) {
        if (document.body.scrollTop > 20 || document.documentElement.scrollTop > 20) {
            jumpToStartHtml.style.bottom = "20px";
        } else {
            jumpToStartHtml.style.bottom = "-60px";
        }
    }
}

function jumpToStart() {
    document.body.scrollTop = 0;
    document.documentElement.scrollTop = 0;
}

function showMessage(message, type) {
    let messageHtml = document.getElementById("pop-message");
    messageHtml.innerHTML = message;
    messageHtml.classList.remove(...messageHtml.classList);
    messageHtml.classList.add(type)
    if (!messageHtml.classList.contains('show')) {
        messageHtml.classList.add("show")
        setTimeout(function() {
            messageHtml.innerHTML = "";
            messageHtml.className = messageHtml.className.replace("show", "");
        }, 4500);
    }
}

function showInfo(message) {
    showMessage(message, "info");
}

function showSuccess(message) {
    showMessage(message, "success");
}

function showError(message) {
    showMessage(message, "error");
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
    let lastName = form["input-sign-up-last-name"].value;
    let gender = form["input-sign-up-gender"].value;
    let city = form["input-sign-up-city"].value;
    let country = form["input-sign-up-country"].value;
    let email = form["input-sign-up-email"].value;
    let password = form["input-sign-up-password"].value;
    let password2 = form["input-sign-up-password-repeat"].value;

    if (password !== password2) {
        showError("Passwords doesn't match!");
        return
    }

    if (!["Male", "Female", "Other"].includes(gender)) {
        showError("Invalid gender!")
        return
    }

    const response = await fetch(HOST + "/api/v1/users", {
        method: "POST",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            email: email,
            password: password,
            firstname: firstName,
            lastname: lastName,
            gender: gender,
            city: city,
            country: country,
        }),
    });

    switch (response.status) {
        case 200: // Ok
            await login(email, password);
            showSuccess("Account successfully register!");
            break;
        case 404: // Forbidden
            showError("Invalid data!"); // TODO decide on error message
            break
        default:
            showError("Error");
    }
}

// other helper function

function getDateTimeFormat(date) {
    return date.getDate() + "." + (date.getMonth() + 1) + "." + date.getFullYear() + " " + date.getHours() + ":" + date.getMinutes();
}
