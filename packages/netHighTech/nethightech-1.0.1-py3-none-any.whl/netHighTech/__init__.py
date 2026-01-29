import time
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 1. PATH FIX: Package ke folder ka rasta nikalne ke liye
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--use-fake-ui-for-media-stream")
chrome_options.add_argument("--headless=new")
# GPU disable karne se speed behtar hoti hai
chrome_options.add_argument("--disable-gpu") 

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

# 2. WEBSITE PATH FIX: BASE_DIR use karein
website = f"file:///{os.path.join(BASE_DIR, 'index.html')}"
rec_file = os.path.join(BASE_DIR, "input.txt")

driver.get(website)

def listen():
    try:
        start_button = WebDriverWait(driver, 20).until(EC.element_to_be_clickable((By.ID,'start-btn')))
        start_button.click()
        print("Listening... (netHighTech Active)")
        
        while True:
            try:
                output_element = driver.find_element(By.ID, 'result')
                current_output = output_element.text.strip().lower()

                if len(current_output) > 1:
                    with open(rec_file, 'w', encoding='utf-8') as f:
                        f.write(current_output)
                    
                    print("Jarvis Heard:", current_output)
                    
                    driver.execute_script("document.getElementById('result').textContent = '';")
                    
                    # Thoda sa intezar taake duplication na ho
                    time.sleep(0.3)

            except:
                pass

            time.sleep(0.3)
    except Exception as e:
        print("Error:", e)