import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Dynamic Path nikalne ke liye
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def listen():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    # Shuru mein headless OFF rakho taake error dikhay
    chrome_options.add_argument("--headless=new") 
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # Path ko join karne ka sahi tarika
    html_path = f"file:///{os.path.join(BASE_DIR, 'index.html')}"
    input_path = os.path.join(BASE_DIR, "input.txt")
    
    driver.get(html_path)
    
    try:
        # Start button click
        driver.find_element(By.ID, 'start-btn').click()
        print("Jarvis is Listening...")
        
        while True:
            output = driver.find_element(By.ID, 'result').text.strip()
            if len(output) > 1:
                with open(input_path, 'w', encoding='utf-8') as f:
                    f.write(output)
                print("Heard:", output)
                driver.execute_script("document.getElementById('result').textContent = '';")
            time.sleep(0.5)
    except Exception as e:
        print(f"Error: {e}")
