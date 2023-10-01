const WS_PORT = 8000; //make sure this matches the port for the webscokets server

var localUuid;
var localDisplayName;
var localStream;
var serverConnection;
var peerConnections = {}; // key is uuid, values are peer connection object and user defined display name string
var already_connected = false;
var user_full_name;
var peerConnectionConfig = {
    iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { urls: "stun:stun1.l.google.com:19302" },
        { urls: "stun:stun2.l.google.com:19302" },
        { urls: "stun:stun3.l.google.com:19302" },
        { urls: "stun:stun4.l.google.com:19302" },
    ],
};

function start(room_number, call_type, member_id, user_full_name) {
    user_full_name = user_full_name;
    console.log(room_number,'--room_number\n', call_type, '---call_type\n', member_id, '---member_id\n', user_full_name,'---full_name\n');
    console.log(peerConnections);
    if (!room_number || !call_type) {
        console.log("room number or call type not defined");
        return;
    }

    if (already_connected) {
        alert("Your call is ongoing");
        return;
    }
    localUuid = room_number+'-'+member_id

    console.log("_________ localUuid ______>", localUuid);

    // check if "&displayName=xxx" is appended to URL, otherwise alert user to populate
    localDisplayName = user_full_name;
    document
        .getElementById("localVideoContainer")
        .appendChild(makeLabel(localDisplayName));

    // specify no audio for user media
    if (call_type == "video") {
        var constraints = {
            video: {
                width: { max: 320 },
                height: { max: 240 },
                frameRate: { max: 30 },
                facingMode: { exact: "user" },
            },
            audio: true,
        };
        $(".options .mic").removeClass("mic_action_on")
        $(".options .mic").addClass("mic_action_off")
        $(".options .mic").children("i").html("mic_off")
        console.log($(".options .mic").find("i"));
        $(".options .video").removeClass("video_action_on")
        $(".options .video").addClass("video_action_off")
        $(".options .video").children("i").html("videocam_off")

    } else if (call_type == "voice") {
        var constraints = {
            audio: true,
        };
        $(".options .mic").removeClass("mic_action_on")
        $(".options .mic").addClass("mic_action_off")
        $(".options .mic").children("i").html("mic_off")
        console.log($(".options .mic").children("i"));

    }

    // set up local video stream
    if (navigator.mediaDevices.getUserMedia) {
        navigator.mediaDevices
            .getUserMedia(constraints)
            .then((stream) => {
                localStream = stream;
                document.getElementById("localVideo").srcObject = stream;
            })
            .catch(errorHandler)

            // set up websocket and message all existing clients
            .then(() => {
                // console.log(window.location.hostname);
                let websocket_type = location.protocol === 'https:' ? 'wss://' : 'ws://'
                serverConnection = new WebSocket(
                        websocket_type +
                        window.location.host +
                        "/ws/call/" +
                        room_number +
                        "/"
                );
                already_connected = true;

                // console.log(serverConnection);

                serverConnection.onmessage = gotMessageFromServer;
                serverConnection.onopen = (event) => {
                    serverConnection.send(
                        JSON.stringify({
                            type: "start_call",
                            displayName: localDisplayName,
                            uuid: localUuid,
                            dest: "all",
                        })
                    );
                };
                serverConnection.onclose = (event) => {

                    for (let key in peerConnections) {
                        console.log(peerConnections[key], "--------closed");
                        peerConnections[key]["pc"].close();
                    }
                };
            })
            .catch(errorHandler);
    } else {
        alert("Your browser does not support getUserMedia API");
    }
}

function gotMessageFromServer(message) {
    var signal = JSON.parse(message.data);
    var peerUuid = signal.uuid;
    if(signal.type == 'closing_signal'){
        try{
            try{
                if(signal.localUuid in peerConnections){
                    peerConnections[signal.localUuid].pc.close();
                    delete peerConnections[signal.localUuid];
                }
            }catch(e){
                console.log(e);
            }
            console.log(localUuid, signal.localUuid);
            if(localUuid == signal.localUuid){
                console.log('closing local uuid');
                serverConnection.close();
                document.getElementById("localVideo").srcObject = null
                $('.videoLabel').remove()
                $('.back').click()
                localStream.getTracks().forEach(function(track) {
                    track.stop();
                });
                already_connected = false;
            }
            else{
                console.log(Object.keys(peerConnections).length,'------peerlist length', 'closing other peer');
                if(Object.keys(peerConnections).length == 0){
                    $(".call_end_action").click();
                }
                $('#remoteVideo_'+signal.localUuid).remove()
            }
            return;
        }catch(e){
            console.log(e);
        }
    }
    // Ignore messages that are not for us or from ourselves
    else if (
        peerUuid == localUuid ||
        (signal.dest != localUuid && signal.dest != "all")
    ) {
        return;
    } else if (signal.displayName && signal.dest == "all") {
        // set up peer connection object for a newcomer peer
        setUpPeer(peerUuid, signal.displayName);
        serverConnection.send(
            JSON.stringify({
                type: "start_call",
                displayName: localDisplayName,
                uuid: localUuid,
                dest: peerUuid,
            })
        );
    } else if (signal.displayName && signal.dest == localUuid) {
        // initiate call if we are the newcomer peer
        if(peerUuid in peerConnections){
            setUpPeer(peerUuid, signal.displayName);
        }
        else{
            setUpPeer(peerUuid, signal.displayName, true);
        }
    } else if (signal.sdp) {
        peerConnections[peerUuid].pc
            .setRemoteDescription(new RTCSessionDescription(signal.sdp))
            .then(function () {
                // Only create answers in response to offers
                if (signal.sdp.type == "offer") {
                    peerConnections[peerUuid].pc
                        .createAnswer()
                        .then((description) =>
                            createdDescription(description, peerUuid)
                        )
                        .catch(errorHandler);
                }
            })
            .catch(errorHandler);
    } else if (signal.ice) {
        peerConnections[peerUuid].pc
            .addIceCandidate(new RTCIceCandidate(signal.ice))
            .catch(errorHandler);
    }
}

function setUpPeer(peerUuid, displayName, initCall = false) {
    peerConnections[peerUuid] = {
        displayName: displayName,
        pc: new RTCPeerConnection(peerConnectionConfig),
    };
    peerConnections[peerUuid].pc.onicecandidate = (event) =>
        gotIceCandidate(event, peerUuid);
    peerConnections[peerUuid].pc.ontrack = (event) =>
        gotRemoteStream(event, peerUuid);
    peerConnections[peerUuid].pc.oniceconnectionstatechange = (event) =>
        checkPeerDisconnect(event, peerUuid);
    peerConnections[peerUuid].pc.addStream(localStream);

    if (initCall) {
        peerConnections[peerUuid].pc
            .createOffer()
            .then((description) => createdDescription(description, peerUuid))
            .catch(errorHandler);
    }
}

function gotIceCandidate(event, peerUuid) {
    if (event.candidate != null) {
        try{
            serverConnection.send(
                JSON.stringify({
                    type: "start_call",
                    ice: event.candidate,
                    uuid: localUuid,
                    dest: peerUuid,
                })
            );
        }catch(e){
            console.log(e);
        }

    }
}

function createdDescription(description, peerUuid) {
    // console.log(`got description, peer ${peerUuid}`);
    peerConnections[peerUuid].pc
        .setLocalDescription(description)
        .then(function () {
            serverConnection.send(
                JSON.stringify({
                    type: "start_call",
                    sdp: peerConnections[peerUuid].pc.localDescription,
                    uuid: localUuid,
                    dest: peerUuid,
                })
            );
        })
        .catch(errorHandler);
}

function gotRemoteStream(event, peerUuid) {
    console.log(`got remote stream, peer ${peerUuid}`);
    //assign stream to new HTML video element
    var old_video_div = document.getElementById('remoteVideo_'+peerUuid)
    console.log(old_video_div,peerUuid,'------old video');

    if(old_video_div){
        console.log('find old video div');
        // old_video_div.removeChild(old_video_div.childNodes[0])
        old_video_div.innerHTML = null;
        var vidElement = document.createElement("video");
        vidElement.setAttribute("autoplay", "");
        // vidElement.setAttribute("muted", "");
        vidElement.srcObject = event.streams[0];
        old_video_div.appendChild(vidElement)
        old_video_div.appendChild(makeLabel(peerConnections[peerUuid].displayName));
    }
    else{
        var vidElement = document.createElement("video");
        vidElement.setAttribute("autoplay", "");
        vidElement.setAttribute("muted", "");
        vidElement.srcObject = event.streams[0];

        var vidContainer = document.createElement("div");
        vidContainer.setAttribute("id", "remoteVideo_" + peerUuid);
        vidContainer.setAttribute("class", "videoContainer");
        vidContainer.appendChild(vidElement);
        vidContainer.appendChild(makeLabel(peerConnections[peerUuid].displayName));

        document.getElementById("videos").appendChild(vidContainer);
    }
    updateLayout();
}

function checkPeerDisconnect(event, peerUuid) {
    var state = peerConnections[peerUuid].pc.iceConnectionState;
    console.log(`connection with peer ${peerUuid} ${state}`);
    if (state === "failed" || state === "closed" || state === "disconnected") {
        delete peerConnections[peerUuid];
        document
            .getElementById("videos")
            .removeChild(document.getElementById("remoteVideo_" + peerUuid));
        updateLayout();
    }
}

function updateLayout() {
    // console.log("_________ ______>");
    // console.log("updating layout");
    // update CSS grid based on number of diplayed videos
    var rowHeight = "98vh";
    var colWidth = "98vw";

    var numVideos = Object.keys(peerConnections).length + 1; // add one to include local video

    if (numVideos > 1 && numVideos <= 4) {
        // 2x2 grid
        rowHeight = "48vh";
        colWidth = "48vw";
    } else if (numVideos > 4) {
        // 3x3 grid
        rowHeight = "32vh";
        colWidth = "32vw";
    }

    document.documentElement.style.setProperty(`--rowHeight`, rowHeight);
    document.documentElement.style.setProperty(`--colWidth`, colWidth);
}

function makeLabel(label) {
    var vidLabel = document.createElement("div");
    vidLabel.appendChild(document.createTextNode(label));
    vidLabel.setAttribute("class", "videoLabel");
    return vidLabel;
}

function errorHandler(error) {
    console.log(error);
}


$(document).on("click", ".call_end_action", function () {
    try{
        $('.connect').removeAttr('disabled');
        serverConnection.send(JSON.stringify({
            type:'closing_signal',
            localUuid:localUuid
        }))
    }catch(e){
        console.log(e);
    }

});


$(document).on("click", ".video_action_on", function(e){
    $(this).removeClass("video_action_on")
    $(this).addClass("video_action_off")
    $(this).children("i").html("videocam_off")
    console.log("clicking video action");
    if ($(this).parent(".options").find(".mic_action_on").length) {
        console.log("video turn on mic turn off");
        navigator.mediaDevices
            .getUserMedia({
                video: {
                    width: { max: 320 },
                    height: { max: 240 },
                    frameRate: { max: 30 },
                    facingMode: { exact: "user" },
                },
                audio: false
            })
            .then((stream) => {
            $("#localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = stream;
            for(key in peerConnections){
                console.log(key, "add remote stream");
                peerConnections[key].pc.removeStream(localStream)
                peerConnections[key].pc.addStream(stream)
                peerConnections[key].pc.createOffer()
                .then((description) => createdDescription(description, key))
                .catch(errorHandler);
            }
            localStream.getTracks().forEach(function(track) {
                track.stop();
            });
            localStream = stream
        });
    }else{
        console.log("video turn on mic turn on");
        navigator.mediaDevices
            .getUserMedia({
                video: {
                    width: { max: 320 },
                    height: { max: 240 },
                    frameRate: { max: 30 },
                    facingMode: { exact: "user" },
                },
                audio: true
            })
            .then((stream) => {
            $("#localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = stream;
            for(key in peerConnections){
                console.log(key, "add remote stream");
                peerConnections[key].pc.removeStream(localStream)
                peerConnections[key].pc.addStream(stream)
                peerConnections[key].pc.createOffer()
                .then((description) => createdDescription(description, key))
                .catch(errorHandler);
            }
            localStream.getTracks().forEach(function(track) {
                track.stop();
            });
            localStream = stream
        });
    }
});

$(document).on("click", ".video_action_off", function(e){
    $(this).addClass("video_action_on")
    $(this).removeClass("video_action_off")
    $(this).children("i").html("videocam")
    if ($(this).parent(".options").find(".mic_action_on").length) {
        console.log("video turn off mic turn off");
        document.getElementById("localVideo").srcObject = null;
        localStream.getTracks().forEach(function(track) {
            track.stop();
        });
        for(key in peerConnections){
            peerConnections[key].pc.removeStream(localStream)
        }
        // localStream = null

    }else{
        console.log("video turn off mic turn on");

        navigator.mediaDevices
            .getUserMedia({
                video: false,
                audio: true
            })
            .then((stream) => {
            $("#localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = stream;
            for(key in peerConnections){
                console.log(key, "add remote stream");
                peerConnections[key].pc.removeStream(localStream)
                peerConnections[key].pc.addStream(stream)
                peerConnections[key].pc.createOffer()
                .then((description) => createdDescription(description, key))
                .catch(errorHandler);
            }
            localStream.getTracks().forEach(function(track) {
                track.stop();
            });
            localStream = stream
        });
    }
});

$(document).on("click", ".mic_action_on", function(e){
    $(this).removeClass("mic_action_on")
    $(this).addClass("mic_action_off")
    $(this).children("i").html("mic_off")
    console.log("clicking video action");
    if ($(this).parent(".options").find(".video_action_on").length) {
        console.log("video turn off mic turn on");
        navigator.mediaDevices
            .getUserMedia({
                video: false,
                audio: true
            })
            .then((stream) => {
            $("#localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = stream;
            for(key in peerConnections){
                console.log(key, "add remote stream");
                peerConnections[key].pc.removeStream(localStream)
                peerConnections[key].pc.addStream(stream)
                peerConnections[key].pc.createOffer()
                .then((description) => createdDescription(description, key))
                .catch(errorHandler);
            }
            localStream.getTracks().forEach(function(track) {
                track.stop();
            });
            localStream = stream
        });
    }else{
        console.log("video turn on mic turn on");
        navigator.mediaDevices
            .getUserMedia({
                video: {
                    width: { max: 320 },
                    height: { max: 240 },
                    frameRate: { max: 30 },
                    facingMode: { exact: "user" },
                },
                audio: true
            })
            .then((stream) => {
            $("#localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = stream;
            for(key in peerConnections){
                console.log(key, "add remote stream");
                peerConnections[key].pc.removeStream(localStream)
                peerConnections[key].pc.addStream(stream)
                peerConnections[key].pc.createOffer()
                .then((description) => createdDescription(description, key))
                .catch(errorHandler);
            }
            localStream.getTracks().forEach(function(track) {
                track.stop();
            });
            localStream = stream
        });
    }
});

$(document).on("click", ".mic_action_off", function(e){
    $(this).removeClass("mic_action_off")
    $(this).addClass("mic_action_on")
    $(this).children("i").html("mic")
    console.log("clicking video action");
    if ($(this).parent(".options").find(".video_action_on").length) {
        console.log("video turn off mic turn off");

        document.getElementById("localVideo").srcObject = null;
        localStream.getTracks().forEach(function(track) {
            track.stop();
        });
        for(key in peerConnections){
            peerConnections[key].pc.removeStream(localStream)
        }
        // localStream = null
    }else{
        console.log("video turn on mic turn off");

        navigator.mediaDevices
            .getUserMedia({
                video: {
                    width: { max: 320 },
                    height: { max: 240 },
                    frameRate: { max: 30 },
                    facingMode: { exact: "user" },
                },
                audio: false
            })
            .then((stream) => {
            $("#localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = null;
            document.getElementById("localVideo").srcObject = stream;
            for(key in peerConnections){
                console.log(key, "add remote stream");
                peerConnections[key].pc.removeStream(localStream)
                peerConnections[key].pc.addStream(stream)
                peerConnections[key].pc.createOffer()
                .then((description) => createdDescription(description, key))
                .catch(errorHandler);
            }
            localStream.getTracks().forEach(function(track) {
                track.stop();
            });
            localStream = stream
        });
    }
});
