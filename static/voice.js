document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById('voice-button');
    const status = document.getElementById('voice-status');
    const transcriptOutput = document.getElementById('transcript-output');
    
    if (button && status && transcriptOutput) {
        console.log("All elements found, proceeding with voice recognition...");

        // Add event listener for the "Speak Now" button
        button.addEventListener('click', function () {
            console.log("Voice button clicked");

            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
                    const mediaRecorder = new MediaRecorder(stream);
                    let audioChunks = [];

                    button.textContent = 'Listening...';
                    button.disabled = true;
                    button.classList.add('btn-warning');

                    mediaRecorder.ondataavailable = function (event) {
                        audioChunks.push(event.data);
                        console.log("Audio chunk received", event.data);
                    };

                    mediaRecorder.onstop = function () {
                        console.log("Recording stopped");

                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'voice_vote.wav');

                        button.textContent = 'Processing...';

                        fetch('/process_audio', {
                            method: 'POST',
                            body: formData
                        })
                            .then(response => response.json())
                            .then(data => {
                                console.log("Transcript received: ", data);

                                if (data.transcript) {
                                    const transcript = data.transcript.toLowerCase();
                                    status.textContent = `You said: ${transcript}`;
                                    transcriptOutput.textContent = `Transcription result: "${transcript}"`;

                                    // Send the transcript to the backend for matching and vote submission
                                    fetch('/voice_vote', {
                                        method: 'POST',
                                        headers: {
                                            'Content-Type': 'application/json',
                                        },
                                        body: JSON.stringify({ transcript: transcript })
                                    })
                                        .then(response => response.json())
                                        .then(data => {
                                            status.textContent = data.message;
                                            button.textContent = 'Speak Now';
                                            button.disabled = false;
                                            button.classList.remove('btn-warning');
                                            button.classList.add('btn-secondary');
                                        });
                                } else {
                                    status.textContent = 'Error processing audio. Please try again.';
                                    button.textContent = 'Speak Now';
                                    button.disabled = false;
                                    button.classList.remove('btn-warning');
                                    button.classList.add('btn-secondary');
                                }
                            })
                            .catch(error => {
                                console.error("Error during processing: ", error);
                                status.textContent = 'An error occurred. Please try again.';
                                button.textContent = 'Speak Now';
                                button.disabled = false;
                                button.classList.remove('btn-warning');
                                button.classList.add('btn-secondary');
                            });
                    };

                    mediaRecorder.start();
                    console.log("Recording started");

                    setTimeout(function () {
                        mediaRecorder.stop();
                    }, 2000);
                }).catch(error => {
                    console.error("Error accessing media devices: ", error);
                    status.textContent = 'Unable to access your microphone. Please check your browser settings.';
                });
            } else {
                status.textContent = 'Your browser does not support audio recording.';
            }
        });
    } else {
        console.error('Voice button, status element, or transcript output not found.');
    }
});