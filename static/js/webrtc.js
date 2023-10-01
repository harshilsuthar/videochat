"use strict";

let startButton = document.getElementById("startButton");
let callButton = document.getElementById("callButton");
let hangupButton = document.getElementById("hangupButton");

const videoChatContainer = document.getElementById("main");
const localVideoComponent = document.getElementById("localVideo");
const remoteVideoComponent = document.getElementById("remoteVideo");

// startButton.addEventListener("click",1);
// callButton.addEventListener("click", call);

// Variables.
const mediaConstraints = {
    audio: false,
    video: { width: 1280, height: 720 },
};
let localStream;
let remoteStream;
let isRoomCreator;
let rtcPeerConnection; // Connection between the local device and the remote peer.
let roomId;

const iceServers = {
    iceServers: [
        { urls: "stun:stun.l.google.com:19302" },
        { urls: "stun:stun1.l.google.com:19302" },
        { urls: "stun:stun2.l.google.com:19302" },
        { urls: "stun:stun3.l.google.com:19302" },
        { urls: "stun:stun4.l.google.com:19302" },
    ],
};
let websocket_type = location.protocol === 'https:' ? 'wss://' : 'ws://'
const socket = new WebSocket(websocket_type+ window.location.host +"/ws/call/1/");

socket.onmessage = async function (e) {
    var data = JSON.parse(e.data);
    var type = data["type"];
    console.log(data);
    if (type == 'room_created'){
        console.log("Socket event callback: room_created");
        await setLocalStream(mediaConstraints);
        isRoomCreator = true
    }
    else if (type == "room_joined") {
        console.log('Socket event callback: room_joined')
        await setLocalStream(mediaConstraints);
        socket.send(
            JSON.stringify({
                type: "start_call",
            })
        );
    } else if (type == "start_call") {
        console.log("Socket event callback: start_call");
        if (isRoomCreator) {
            rtcPeerConnection = new RTCPeerConnection(iceServers);
            addLocalTracks(rtcPeerConnection);
            rtcPeerConnection.ontrack = setRemoteStream;
            rtcPeerConnection.onicecandidate = sendIceCandidate;
            await createOffer(rtcPeerConnection);
        }
    }

    else if (type == 'room_full'){
        console.log('Socket event callback: full_room')
        alert('The room is full, please try another one')
    }

    else if (type == "webrtc_offer") {
        console.log("Socket event callback: webrtc_offer");
        if (!isRoomCreator) {
            rtcPeerConnection = new RTCPeerConnection(iceServers);
            addLocalTracks(rtcPeerConnection);
            rtcPeerConnection.ontrack = setRemoteStream;
            rtcPeerConnection.onicecandidate = sendIceCandidate;
            console.log(data['sdp'],'----');
            rtcPeerConnection.setRemoteDescription(
                new RTCSessionDescription(data['sdp'])
            );
            await createAnswer(rtcPeerConnection);
        }
    } else if (type == "webrtc_answer") {
        try {
            console.log("Socket event callback: webrtc_answer",data['sdp']);
            rtcPeerConnection.setRemoteDescription(
                new RTCSessionDescription(data['sdp'])
            );
        } catch (error) {
            console.log(error);
        }
    } else if (type == "webrtc_ice_candidate") {
        console.log("Socket event callback: webrtc_ice_candidate");
        // ICE candidate configuration.
        var candidate = new RTCIceCandidate({
            sdpMLineIndex: data.label,
            candidate: data.candidate,
        });
        rtcPeerConnection.addIceCandidate(candidate);
    }
};

async function setLocalStream(mediaConstraints) {
    let stream;
    console.log('setting local stream =========\n\n');
    try {
        stream = await navigator.mediaDevices.getUserMedia(mediaConstraints);
    } catch (error) {
        console.error("Could not get user media", error);
    }
    localStream = stream;
    console.log(localStream, '---------local stream');
    localVideoComponent.srcObject = stream;
}

async function createOffer(rtcPeerConnection) {
    let sessionDescription;
    try {
        sessionDescription = await rtcPeerConnection.createOffer();
        rtcPeerConnection.setLocalDescription(sessionDescription);
    } catch (error) {
        console.error(error);
    }
    console.log(sessionDescription);
    socket.send(
        JSON.stringify({
            type: "webrtc_offer",
            sdp: sessionDescription,
        })
    );
}

function addLocalTracks(rtcPeerConnection) {
    localStream.getTracks().forEach((track) => {
        rtcPeerConnection.addTrack(track, localStream);
    });
}

function setRemoteStream(e) {
    remoteVideoComponent.srcObject = e.streams[0];
    remoteStream = e.stream;
}

function sendIceCandidate(e) {
    if (e.candidate) {
        socket.send(
            JSON.stringify({
                type: "webrtc_ice_candidate",
                label: e.candidate.sdpMLineIndex,
                candidate: e.candidate.candidate,
            })
        );
    }
}
async function createAnswer(rtcPeerConnection) {
    let sessionDescription;
    console.log('calling create anser function');
    try {
        sessionDescription = await rtcPeerConnection.createAnswer();
        rtcPeerConnection.setLocalDescription(sessionDescription);
    } catch (error) {
        console.error(error);
    }

    socket.send(
        JSON.stringify({
            type: "webrtc_answer",
            sdp: sessionDescription,
            roomId,
        })
    );
}
