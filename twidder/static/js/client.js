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

        let payload = btoa(JSON.stringify({
            email: email, session_id: token,
        }));

        socket.send(payload);
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
    document.getElementById("welcome-view").style.display = "block";
    document.getElementById("user-view").style.display = "none";
    document.getElementById("loading-view").style.display = "none";

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

    // load user content
    await reloadUserData();

    // load view
    document.getElementById("welcome-view").style.display = "none";
    document.getElementById("user-view").style.display = "block";
    document.getElementById("loading-view").style.display = "none";

    // history API
    if (window.location.pathname === "/browse") showTab("browse");
    else if (window.location.pathname === "/account") showTab("account");
    else showTab("home");
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
            let searchBar = document.getElementById("input-user-email");
            let userEmail = window.location.search.replace("?email=", "");
            if (searchBar.value !== userEmail) {
                loadBrowseUser(userEmail).then();
                searchBar.value = userEmail;
            }
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
            "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, null),
        },
    });
    let userPostsRequest = fetch("http://" + HOST + "/api/v1/posts?" + new URLSearchParams({user_email: email}).toString(), {
        method: "GET",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, null),
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
    setProfilePicture("home-user-image", user.image, user.gender);

    // Account tab
    document.getElementById("input-account-first-name").value = user.firstname;
    document.getElementById("input-account-last-name").value = user.lastname;
    document.getElementById("input-account-city").value = user.city;
    document.getElementById("input-account-country").value = user.country;
    document.getElementById("input-account-gender").value = user.gender;
    document.getElementById("account-email").innerHTML = user.email;
    setProfilePicture("account-user-image", user.image, user.gender);

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
            "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, null),
        },
    });
    let userPostsRequest = await fetch("http://" + HOST + "/api/v1/posts?" + new URLSearchParams({user_email: userEmail}).toString(), {
        method: "GET", cache: "no-cache", headers: {
            "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, null),
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
    setProfilePicture("browse-user-image", userData.image, userData.gender);

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

        // general information
        newPostHtml.setAttribute("data-id", posts[i]["id"]);
        newPostHtml.getElementsByClassName("time")[0].innerHTML = getDateTimeFormat(new Date(posts[i]["created"]));
        newPostHtml.getElementsByClassName("author")[0].innerHTML = posts[i]["author"];

        // show media
        let mediaContainer = newPostHtml.getElementsByClassName("media-content")[0];
        let mediaData = posts[i]["media"];
        if (mediaData != null) {
            let mediaContent = null;
            if (mediaData.startsWith("data:image")) {
                mediaContent = mediaContainer.getElementsByTagName("img")[0];
            } else if (mediaData.startsWith("data:video")) {
                mediaContent = mediaContainer.getElementsByTagName("video")[0];
            } else {
                console.log("unsupported media type")
            }
            if (mediaContent != null) {
                mediaContent.src = mediaData;
                mediaContent.style.display = "block";
            }
        }

        // show content
        let lines = posts[i]["content"].split("\n");
        for (let j = 0; j < lines.length; j++) {
            newPostHtml.getElementsByClassName("content")[0].appendChild(document.createTextNode(lines[j]));
            newPostHtml.getElementsByClassName("content")[0].appendChild(document.createElement("br"));
        }

        // start animation
        newPostHtml.getElementsByClassName("button-edit")[0].style.display = "none"; // NOTE: hiding edit button until the feature is implemented
        // newPostHtml.getElementsByClassName("button-edit")[0].style.display = posts[i]["author"] === email || posts[i]["user"] === email ? "block" : "none";
        newPostHtml.getElementsByClassName("button-delete")[0].style.display = posts[i]["author"] === email ? "block" : "none";

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
    let email = localStorage.getItem("email");
    if (token != null && email != null) {
        const response = await fetch("http://" + HOST + "/api/v1/session", {
            method: "DELETE", cache: "no-cache", headers: {
                "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, null),
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

    let body = {
        firstname: firstName,
        lastname: lastName,
        gender: gender,
        city: city,
        country: country,
    };
    const response = await fetch("http://" + HOST + "/api/v1/users/" + email, {
        method: "PATCH",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, body),
        },
        body: JSON.stringify(body),
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

    // update profile picture (only if it is not set yet)
    if (!document.getElementById("account-user-image").src.startsWith("data:image")) {
        setProfilePicture("home-user-image", null, gender);
        setProfilePicture("account-user-image", null, gender);
    }

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
            "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, null),
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

async function addPostHome(form) {
    let email = localStorage.getItem("email");
    if (email == null) {
        showError("Error: couldn't load user email");
        return;
    }

    let messageInput = form["input-home-new-post"];
    let fileInput = form["home-post-file-upload"];
    let imageContent = document.getElementById("post-home-uploaded-image");
    let videoContent = document.getElementById("post-home-uploaded-video");
    let file = fileInput.files.length > 0 ? fileInput.files[0] : null;

    if (await addPostToWall(
        document.getElementById("home-wall"),
        document.getElementById("home-post-template").innerHTML,
        email,
        messageInput.value,
        file != null && file.type.match('image.*') ? imageContent.src : null,
        file != null && file.type.match('video.*') ? videoContent.src : null,
    )) {
        messageInput.value = null;
        fileInput.value = null;
        document.getElementById("post-home-uploaded-image").style.display = "none";
        document.getElementById("post-home-uploaded-video").style.display = "none";
        document.getElementById("home-post-remove-content").style.display = "none";
    }
}

async function addPostBrowse(form) {
    let messageInput = form["input-browse-new-post"];
    let fileInput = form["browse-post-file-upload"];
    let imageContent = document.getElementById("post-browse-uploaded-image");
    let videoContent = document.getElementById("post-browse-uploaded-video");
    let file = fileInput.files.length > 0 ? fileInput.files[0] : null;

    if (await addPostToWall(
        document.getElementById("browse-wall"),
        document.getElementById("browse-post-template").innerHTML,
        document.getElementById("browse-user-email").innerHTML,
        messageInput.value,
        file != null && file.type.match('image.*') ? imageContent.src : null,
        file != null && file.type.match('video.*') ? videoContent.src : null,
    )) {
        messageInput.value = null;
        fileInput.value = null;
        document.getElementById("post-browse-uploaded-image").style.display = "none";
        document.getElementById("post-browse-uploaded-video").style.display = "none";
        document.getElementById("browse-post-remove-content").style.display = "none";
    }
}

async function addPostToWall(htmlWall, postTemplateHtml, userEmail, content, image, video) {
    console.log("Creating a new post: " + userEmail + ", " + content + (", image" ? image != null : "") + (", video" ? video != null : ""));

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

    let body = {
        email: userEmail,
        message: content,
        media: image != null ? image : video  // NOTE: here we assume that only image or video or none of those is provided
    };
    const response = await fetch("http://" + HOST + "/api/v1/posts", {
        method: "POST",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, body),
        },
        body: JSON.stringify(body),
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
    newPostHtml.getElementsByClassName("time")[0].innerHTML = getDateTimeFormat(new Date());
    newPostHtml.getElementsByClassName("author")[0].innerHTML = email;

    // show media
    let mediaContent = newPostHtml.getElementsByClassName("media-content")[0];
    if (image != null) {
        let imageContent = mediaContent.getElementsByTagName("img")[0];
        imageContent.src = image;
        imageContent.style.display = "block";
    }
    if (video != null) {
        let videoContent = mediaContent.getElementsByTagName("video")[0];
        videoContent.src = video;
        videoContent.style.display = "block";
    }

    // show content
    let lines = content.split("\n");
    for (let j = 0; j < lines.length; j++) {
        newPostHtml.getElementsByClassName("content")[0].appendChild(document.createTextNode(lines[j]));
        newPostHtml.getElementsByClassName("content")[0].appendChild(document.createElement("br"));
    }

    // NOTE: hiding edit button until the feature is implemented
    newPostHtml.getElementsByClassName("button-edit")[0].style.display = "none"

    // animation
    newPostHtml.style.animation = "post-appear 0.75s";
    newPostHtml.getElementsByClassName("button-edit")[0].style.animation = "post-appear-inner 1.0s";
    newPostHtml.getElementsByClassName("button-delete")[0].style.animation = "post-appear-inner 1.0s";

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
    showError("THIS FEATURE IS NOT IMPLEMENTED YET");
}

async function buttonDeletePost(button) {
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

    let postID = button.parentElement.getAttribute("data-id");
    console.log("Delete post, post id: " + postID);

    let response = await fetch("http://" + HOST + "/api/v1/posts/" + postID, {
        method: "DELETE",
        cache: "no-cache",
        headers: {
            "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, null),
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
    button.parentElement.style.animation = "post-disappear 0.50s";
    button.parentElement.getElementsByClassName("content")[0].style.animation = "post-disappear-content 0.50";
    button.parentElement.getElementsByClassName("button-edit")[0].style.animation = "post-disappear-inner 0.50s";
    button.parentElement.getElementsByClassName("button-delete")[0].style.animation = "post-disappear-inner 0.00s";

    // remove element eventually
    setTimeout(function () {
        button.parentElement.remove();
    }, 500);
}

function setProfilePicture(elementID, imageData, gender) {
    let imageElement = document.getElementById(elementID);
    if (imageData != null) {
        imageElement.src = imageData;
    } else {
        switch (gender) {
            case 'Male':
                imageElement.src = "./static/src/user-male.svg";
                break;
            case 'Female':
                imageElement.src = "./static/src/user-female.svg";
                break;
            default:
                imageElement.src = "./static/src/user-solid.svg";
        }
    }
}

function userImageUpload(input) {
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

    let file = input.files[0];
    if (!file.type.match('image.*')) {
        showError("Only image file can be uploaded!");
        input.value = null;
        return;
    }

    let reader = new FileReader();
    reader.onloadend = async function () {
        let body = {
            image: reader.result,
        };

        fetch("http://" + HOST + "/api/v1/users/" + email, {
            method: "PATCH",
            cache: "no-cache",
            headers: {
                "Content-Type": "application/json", "Authorization": await getAuthorizationHeader(email, token, body),
            },
            body: JSON.stringify(body),
        }).then(function (response) {
            if (response.status !== 200) {
                showError("Unexpected error");
                return;
            }

            // update UI
            document.getElementById("account-user-image").src = reader.result;
            document.getElementById("home-user-image").src = reader.result;
        });
    }
    reader.readAsDataURL(file);
}

function postFileUpload(input, imageElementID, videoElementID, removeElementID) {
    let file = input.files[0];
    let imageContent = document.getElementById(imageElementID);
    let videoContent = document.getElementById(videoElementID);
    let removeButton = document.getElementById(removeElementID);

    if (!file.type.match('image.*') && !file.type.match('video.*')) {
        showError("Only image or video can be uploaded!");
        input.value = null;
        return;
    }

    let reader = new FileReader();
    reader.onloadend = function () {
        removeButton.style.display = "block";

        if (file.type.match('image.*')) {
            imageContent.src = reader.result;
            imageContent.style.display = "block";
            videoContent.src = "";
            videoContent.style.display = "none";
        }

        if (file.type.match('video.*')) {
            imageContent.src = "";
            imageContent.style.display = "none";
            videoContent.src = reader.result;
            videoContent.style.display = "block";
        }

        removeButton.onclick = ev => {
            removeButton.style.display = "none";
            imageContent.style.display = "none";
            videoContent.style.display = "none";
            imageContent.src = "";
            videoContent.src = "";
        };
    }
    reader.readAsDataURL(file);
}

// INTERACTIVE CSS ELEMENTS

function checkSamePasswords(htmlPassword, htmlPassword2) {
    let password1 = document.getElementById(htmlPassword);
    let password2 = document.getElementById(htmlPassword2);
    password1.setCustomValidity(password1.value === "" || password1.value === password2.value || password2.value === "" ? "" : "Passwords doesn't match!")
    if (password1.value === password2.value) {
        password1.setCustomValidity("");
        password2.setCustomValidity("");
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

// authorization
async function getAuthorizationHeader(userEmail, sessionID, payload) {
    let message = payload != null ? JSON.stringify(payload) : "";

    // implementation from https://stackoverflow.com/a/76117805
    const encoder = new TextEncoder();
    const payload_encode = encoder.encode(message);
    const sessionID_encode = encoder.encode(sessionID);

    // Import the secretKey as a CryptoKey
    const cryptoKey = await window.crypto.subtle.importKey(
        "raw",
        sessionID_encode,
        {name: "HMAC", hash: "SHA-256"},
        false,
        ["sign"]
    );

    // Sign the payload with hmac and cryptokey
    const signature = await window.crypto.subtle.sign(
        "HMAC",
        cryptoKey,
        payload_encode
    );

    // Convert the signature ArrayBuffer to a hex string
    const hash = Array.from(new Uint8Array(signature));
    const hashHex = hash
        .map((b) => b.toString(16).padStart(2, "0"))
        .join("");

    return btoa(JSON.stringify({
        email: userEmail, hash: hashHex,
    }));
}
    