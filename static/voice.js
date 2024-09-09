document.addEventListener("DOMContentLoaded", function () {
    // Get references to DOM elements
    const button = document.getElementById('voice-button');
    const status = document.getElementById('voice-status');
    const transcriptOutput = document.getElementById('transcript-output');
    
    // Log these elements to check if they are found
    console.log(button, status, transcriptOutput);
    
    // Ensure all elements are found before proceeding
    if (button && status && transcriptOutput) {
        console.log("All elements found, proceeding with voice recognition...");

        const candidates = JSON.parse(document.getElementById('candidates-data').textContent);

        // Add event listener for the "Speak Now" button
        button.addEventListener('click', function () {
            console.log("Voice button clicked");

            // Check if the browser supports audio recording
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ audio: true }).then(function (stream) {
                    const mediaRecorder = new MediaRecorder(stream);
                    let audioChunks = [];

                    // Update button to show "Listening..." when recording starts
                    button.textContent = 'Listening...';
                    button.disabled = true;
                    button.classList.add('btn-warning');

                    // Capture audio data
                    mediaRecorder.ondataavailable = function (event) {
                        audioChunks.push(event.data);
                        console.log("Audio chunk received", event.data);
                    };

                    // When recording stops
                    mediaRecorder.onstop = function () {
                        console.log("Recording stopped");

                        // Create a Blob from the audio data
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'voice_vote.wav');

                        // Update button to show "Processing..."
                        button.textContent = 'Processing...';

                        // Send the audio to the server for processing
                        fetch('/process_audio', {
                            method: 'POST',
                            body: formData
                        })
                            .then(response => response.json())
                            .then(data => {
                                console.log("Transcript received: ", data);

                                // Check if the transcript is received
                                if (data.transcript) {
                                    const transcript = data.transcript.toLowerCase();
                                    status.textContent = `You said: ${transcript}`;

                                    // Update the dedicated space with the transcript
                                    transcriptOutput.textContent = `Transcription result: "${transcript}"`;

                                    // Find the closest matching candidate based on the transcript
                                    const candidate = candidates.find(c => {
                                        const words = c.toLowerCase().split(" ");
                                        return words.every(word => transcript.includes(word));
                                    });

                                    if (candidate) {
                                        status.textContent += ` (Recognized: ${candidate})`;

                                        // Send the recognized candidate to the backend for vote submission
                                        fetch('/voice_vote', {
                                            method: 'POST',
                                            headers: {
                                                'Content-Type': 'application/json',
                                            },
                                            body: JSON.stringify({ candidate })
                                        })
                                            .then(response => response.json())
                                            .then(data => {
                                                status.textContent = data.message;

                                                // Reset button after processing
                                                button.textContent = 'Speak Now';
                                                button.disabled = false;
                                                button.classList.remove('btn-warning');
                                                button.classList.add('btn-secondary');
                                            });
                                    } else {
                                        status.textContent = 'Candidate not recognized, please try again.';
                                        button.textContent = 'Speak Now';
                                        button.disabled = false;
                                        button.classList.remove('btn-warning');
                                        button.classList.add('btn-secondary');
                                    }
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

                    // Start recording
                    mediaRecorder.start();
                    console.log("Recording started");

                    // Automatically stop recording after 5 seconds
                    setTimeout(function () {
                        mediaRecorder.stop();
                    }, 5000);
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