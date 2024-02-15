// Constants
const HOST = "localhost:8080";
const POPUP_MESSAGE_TIME = 4500

// App state management
window.onload = function() {
    loadApp().then();
};

window.onpopstate = function (e) {
    console.log("Url path changed: " + window.location.href);

    // going back/forward using history API
    let token = localStorage.getItem("token");
    let email = localStorage.getItem("email");
    if (token == null || email == null) {
        // user is not logged in, set correct state
        history.pushState("welcome", "", "/");
    } else {
        // user is logged in, switch to correct tab
        if (window.location.pathname === "/browse") showTab("browse");
        else if (window.location.pathname === "/account") showTab("account");
        else showTab("home");
    }
}

async function loadApp() {
    console.log("Loading application");

    let token = localStorage.getItem("token");
    let email = localStorage.getItem("email");
    if (token == null || email == null) {
        showWelcomeView();
        return;
    }

    console.log("Initializing socket connection");
    const socket = new WebSocket('ws://' + HOST + '/session');

    socket.onopen = (event) => {
        console.log("Socket is open");
        // send the session id (token) to the server
        socket.send(token);
    }

    socket.onmessage = (event) => {
        console.log("Socket message received: " + event.data);
        // check for server response
        if (event.data === "ok") {
            showUserView().then();
        } else if (event.data === "fail") {
            showError("failed to initialize connection");
        } else {
            showError("Unexpected error")
            console.log("unexpected message from the server: " + event.data);
        }
    }

    socket.onclose = (event) => {
        console.log("Socket is closed");
        // logging user out
        let token = localStorage.getItem("token");
        let email = localStorage.getItem("email");
        if (token != null && email != null) {
            localStorage.removeItem("token");
            localStorage.removeItem("email");
            showWelcomeView();
            showInfo("You have been logged out.");
            return;
        }
        console.log("socket closed");
    }

    socket.onerror = (event) => {
        console.log("Socket error");
        showError("Connection error");
    }
}

function showWelcomeView() {
    console.log("Loading welcome view");

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
    console.log("Loading user view");

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
    console.log("Showing tab: " + tabName);

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

    if (tabName === "browse") {
        if (window.location.search.startsWith("?email=")) {
            // search for user from query
            let userEmail = window.location.search.replace("?email=", "");
            loadBrowseUser(userEmail).then();
            document.getElementById("input-user-email").value = userEmail;
        } else {
            // specify query by current value
            let userEmail = document.getElementById("input-user-email").value;
            if (userEmail !== "") {
                history.replaceState("browse", "", "browse?email=" + userEmail);
            }
        }
    }
}

async function reloadUserData() {
    console.log("Loading user data");

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
    let userDataRequest = fetch("http://" + HOST + "/api/v1/users/" + email, {
        method: "GET",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });
    let userPostsRequest = fetch("http://" + HOST + "/api/v1/posts?" + new URLSearchParams({user_email: email}).toString(), {
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
        showError("Unexpected error")
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
    reloadWall(
        document.getElementById("home-wall"),
        document.getElementById("home-post-template").innerHTML,
        posts,
        email
    );
}

function formSearchUser(form) {
    let userEmail = form["input-user-email"].value;
    loadBrowseUser(userEmail).then();

    // History API
    history.pushState("browse", "", "browse?email=" + userEmail);
}

async function loadBrowseUser(userEmail) {
    console.log("Querying user data: " + userEmail);

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

    let userDataRequest = fetch("http://" + HOST + "/api/v1/users/" + userEmail, {
        method: "GET", cache: "no-cache", headers: {
            "Content-Type": "application/json", "Authorization": token,
        },
    });
    let userPostsRequest = await fetch("http://" + HOST + "/api/v1/posts?" + new URLSearchParams({user_email: userEmail}).toString(), {
        method: "GET", cache: "no-cache", headers: {
            "Content-Type": "application/json", "Authorization": token,
        },
    });

    const userDataResponse = await userDataRequest;
    const userPostsResponse = await userPostsRequest;

    if (userDataResponse.status === 404 || userDataResponse.status === 404) {
        showInfo("User not found.")
        return;
    } else if (userDataResponse.status !== 200 || userPostsResponse.status !== 200) {
        showError("Unexpected error")
        return;
    }

    let userData = await userDataResponse.json();
    let posts = (await userPostsResponse.json()).posts;

    document.getElementById("browse-search-button").innerHTML = "Reload";

    // User data
    document.getElementById("container-user-page").style.display = "block";
    document.getElementById("browse-user-name").innerHTML = userData.firstname + " " + userData.lastname;
    document.getElementById("browse-user-gender").innerHTML = userData.gender;
    document.getElementById("browse-user-location").innerHTML = userData.city + ", " + userData.country;
    document.getElementById("browse-user-email").innerHTML = userData.email;

    // User posts
    reloadWall(
        document.getElementById("browse-wall"),
        document.getElementById("browse-post-template").innerHTML,
        posts,
        email
    );
}


function reloadWall(htmlWall, postTemplateHtml, posts, email) {
    // remove all old posts
    for (let i = htmlWall.children.length - 1; i >= 0; i--) {
        let element = htmlWall.children[i];
        if (element.classList.contains("user-post")) {
            element.remove();
        }
    }

    // sort posts by date
    posts.sort(function(a, b){
      return new Date(b.created) - new Date(a.created);
    });

    // add new posts from template
    for (let i = 0; i < posts.length; i++) {
        const newPostHtml = document.createElement("div");
        newPostHtml.innerHTML = postTemplateHtml;
        newPostHtml.classList.add("user-post");
        newPostHtml.setAttribute("data-id", posts[i]["id"]);
        newPostHtml.children[0].innerHTML = getDateTimeFormat(new Date(posts[i]["edited"])); // TODO show icon for edited posts
        newPostHtml.children[1].innerHTML = posts[i]["author"];
        let lines = posts[i]["content"].split("\n");
        for (let j = 0; j < lines.length; j++) {
            newPostHtml.children[2].appendChild(document.createTextNode(lines[j]));
            newPostHtml.children[2].appendChild(document.createElement("br"));
        }
        newPostHtml.children[3].style.display = posts[i]["author"] === email || posts[i]["user"] === email ? "block" : "none";
        newPostHtml.children[4].style.display = posts[i]["author"] === email ? "block" : "none";
        htmlWall.appendChild(newPostHtml);
    }
}

async function login(email, password) {
    console.log("Log in request");

    // create a new session
    const response = await fetch("http://" + HOST + "/api/v1/session", {
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
    } else if (response.status !== 201) {
        showError("Unexpected error");
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
    console.log("Log out request");

    let token = localStorage.getItem("token");
    if (token != null) {
        const response = await fetch("http://" + HOST + "/api/v1/session", {
            method: "DELETE", cache: "no-cache", headers: {
                "Content-Type": "application/json", "Authorization": token,
            },
        });

        if (response.status === 200) {
            showSuccess("You have successfully logged out.");
        } else {
            showError("Unexpected error");
        }
    }

    localStorage.removeItem("token");
    localStorage.removeItem("email");
    showWelcomeView();
}

async function formEditAccountDetails(form) {
    console.log("Edit account details request");

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

    const response = await fetch("http://" + HOST + "/api/v1/users/" + email, {
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

    if (response.status === 403) {
        showError("Invalid email!"); // other 403 error shouldn't happen considering the checks above
    } else if (response.status !== 200) {
        showError("Unexpected error")
        return;
    }

    // update user data in home tab
    document.getElementById("home-user-name").innerHTML = firstName + " " + lastName;
    document.getElementById("home-user-gender").innerHTML = gender;
    document.getElementById("home-user-location").innerHTML = city + ", " + country;

    showSuccess("Account details successfully changed!");
}

async function formChangePassword(form) {
    console.log("Change password request");

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

    let response = await fetch("http://" + HOST + "/api/v1/users/" + email, {
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
        showError("Wrong old password.");
        return;
    } else if (response.status !== 200) {
        showError("Unexpected error");
        return;
    }

    showSuccess("Password successfully changed!");
    form["input-change-password-old"].value = "";
    form["input-change-password-new"].value = "";
    form["input-change-password-new-repeat"].value = "";
}

async function buttonDeleteUserAccount() {
    console.log("Delete account request");

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

    let response = await fetch("http://" + HOST + "/api/v1/users/" + email, {
        method: "DELETE",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });

    if (response.status !== 200) {
        showError("Unexpected error");
        return;
    }

    showSuccess("Account successfully deleted.")
    localStorage.removeItem("token");
    localStorage.removeItem("email");
    showWelcomeView();
}

async function addPostHome() {
    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return;
    }

    let newPostBoxHtml = document.getElementById("input-home-new-post");
    if (await addPostToWall(
        document.getElementById("home-wall"),
        document.getElementById("home-post-template").innerHTML,
        email,
        newPostBoxHtml.value,
    )) {
        newPostBoxHtml.value = "";
    }
}

async function addPostBrowse() {
    let newPostBoxHtml = document.getElementById("input-browse-new-post");
    if (await addPostToWall(
        document.getElementById("browse-wall"),
        document.getElementById("browse-post-template").innerHTML,
        document.getElementById("browse-user-email").innerHTML,
        newPostBoxHtml.value,
    )) {
        newPostBoxHtml.value = "";
    }
}

async function addPostToWall(htmlWall, postTemplateHtml, userEmail, content) {
    console.log("Creating a new post: " + userEmail + ", " + content);

    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return false;
    }

    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return false;
    }

    const response = await fetch("http://" + HOST + "/api/v1/posts", {
        method: "POST",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
        body: JSON.stringify({
            email: userEmail,
            message: content,
        }),
    });

    if (response.status === 403) {
        showError("User does not exist.")
        return false;
    } else if (response.status !== 201) {
        showError("Unexpected error")
        return false;
    }

    // get new post id
    let newPostID = (await response.json()).id

    // create the new post element
    const newPostHtml = document.createElement("div");
    newPostHtml.innerHTML = postTemplateHtml;
    newPostHtml.classList.add("user-post");
    newPostHtml.setAttribute("data-id", newPostID);
    newPostHtml.children[0].innerHTML = getDateTimeFormat(new Date());
    newPostHtml.children[1].innerHTML = email;
    let lines = content.split("\n");
    for (let j = 0; j < lines.length; j++) {
        newPostHtml.children[2].appendChild(document.createTextNode(lines[j]));
        newPostHtml.children[2].appendChild(document.createElement("br"));
    }
    newPostHtml.style.animation = "post-appear 0.75s";
    newPostHtml.children[3].style.animation = "post-appear-inner 1.0s";
    newPostHtml.children[4].style.animation = "post-appear-inner 1.0s";
    htmlWall.insertBefore(newPostHtml, htmlWall.childNodes[2]);

    // clear animation eventually
    setTimeout(function () {
        newPostHtml.style.animation = "";
        newPostHtml.children[3].style.animation = "";
        newPostHtml.children[4].style.animation = "";
    }, 1000);

    return true;
}

async function buttonEditPost(button) {
    let postID = button.parentElement.getAttribute("data-id");
    console.log("Edit post, post id: " + postID);
    alert("EDIT POST: " + postID); // TODO IMPLEMENT ME
}

async function buttonDeletePost(button) {
    let token = localStorage.getItem("token");
    if (token == null) {
        showError("Error: couldn't load token");
        return;
    }

    let postID = button.parentElement.getAttribute("data-id");
    console.log("Delete post, post id: " + postID);

    let response = await fetch("http://" + HOST + "/api/v1/posts/" + postID, {
        method: "DELETE",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json",
            "Authorization": token,
        },
    });
    if (response.status === 404) {
        // if it doesn't exist, it might've been deleted but other user in the mean tim
        showError("Post not found.")
        button.parentElement.remove();
        return;
    } else if (response.status !== 200) {
        showError("Unexpected error")
        return;
    }

    // show animation
    button.parentElement.style.animation = "post-disappear 0.25s 0.25s";
    button.parentElement.children[3].style.animation = "post-disappear-inner 0.50s";
    button.parentElement.children[4].style.animation = "post-disappear-inner 0.50s";

    // remove element eventually
    setTimeout(function () {
        button.parentElement.remove();
    }, 500);
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
    console.log("Showing popup message, message: " + message + ", type: " + type);

    let messageHtml = document.getElementById("pop-message");
    messageHtml.innerHTML = message;
    messageHtml.classList.remove(...messageHtml.classList);
    messageHtml.classList.add(type)
    if (!messageHtml.classList.contains('show')) {
        messageHtml.classList.add("show")
        setTimeout(function() {
            messageHtml.innerHTML = "";
            messageHtml.className = messageHtml.className.replace("show", "");
        }, POPUP_MESSAGE_TIME);
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

window.onkeydown = function (event) {
    if (event.key === "Escape") {
        // close register form if visible
        if (document.getElementById("register-container").style.display === "block") {
            document.getElementById("register-container").style.display = "none";
        }
    }
}

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

    const response = await fetch("http://" + HOST + "/api/v1/users", {
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

    if (response.status === 201) {
        await login(email, password);
        showSuccess("Account successfully register!");
    } else if (response.status === 403) {
        showError("Invalid email!"); // other 403 error shouldn't happen considering the checks above
    } else if (response.status === 409) {
        showError("This email is already taken!");
    } else {
        showError("Unexpected error");
    }
}

// other helper function

function getDateTimeFormat(date) {
    return date.getDate() + "." + (date.getMonth() + 1) + "." + date.getFullYear() + (date.getHours() < 10 ? " 0" : " ") + date.getHours() + (date.getMinutes() < 10 ? ":0" : ":") + date.getMinutes();
}
