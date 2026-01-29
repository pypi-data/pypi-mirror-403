const output = document.getElementById('result');
const startBtn = document.getElementById('start-btn');

const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

if (SpeechRecognition) {
    const recognition = new SpeechRecognition();
    recognition.interimResults = false; 
    recognition.lang = 'en-US';
    recognition.continuous = true;

    recognition.onresult = (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; ++i) {
            transcript += event.results[i][0].transcript;
        }
        output.textContent = transcript.trim();
    };
    
    startBtn.addEventListener('click', () => {
        output.textContent = ''; 
        recognition.start();
        startBtn.textContent = 'Active...';
    });

    recognition.onend = () => {
        recognition.start(); // Loop listening
    };

} else {
    alert("Browser not supported!");
}