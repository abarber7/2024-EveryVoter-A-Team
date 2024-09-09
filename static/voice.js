document.addEventListener("DOMContentLoaded", function () {
    const button = document.getElementById('voice-button');
    const status = document.getElementById('voice-status');
    
    // Ensure the button and status elements exist before proceeding
    if (button && status) {
        const candidates = JSON.parse(document.getElementById('candidates-data').textContent);

        button.addEventListener('click', function() {
            // Prepare the media recorder for audio capture
            if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
                navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
                    const mediaRecorder = new MediaRecorder(stream);
                    let audioChunks = [];

                    mediaRecorder.ondataavailable = function(event) {
                        audioChunks.push(event.data);
                    };

                    mediaRecorder.onstop = function() {
                        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
                        const formData = new FormData();
                        formData.append('audio', audioBlob, 'voice_vote.wav');

                        button.textContent = 'Processing...';
                        button.disabled = true;
                        button.classList.add('btn-warning');
                        
                        fetch('/process_audio', {
                            method: 'POST',
                            body: formData
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.transcript) {
                                const transcript = data.transcript.toLowerCase();
                                status.textContent = `You said: ${transcript}`;

                                const candidate = candidates.find(c => transcript.includes(c.toLowerCase()));
                                if (candidate) {
                                    status.textContent += ` (Recognized: ${candidate})`;
                                    
                                    // Send the recognized candidate to the backend for processing
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
                        });
                    };

                    mediaRecorder.start();

                    setTimeout(function() {
                        mediaRecorder.stop();
                    }, 5000);  // Adjust this duration as necessary
                });
            } else {
                status.textContent = 'Your browser does not support audio recording.';
            }
        });
    } else {
        console.error('Voice button or status element not found. Make sure election is ongoing and candidates are available.');
    }
});