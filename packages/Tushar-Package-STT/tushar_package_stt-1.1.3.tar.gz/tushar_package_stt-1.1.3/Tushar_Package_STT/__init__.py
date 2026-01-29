#pip install selenium

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

#pip install webdriver-manager
from webdriver_manager.chrome import ChromeDriverManager
from os import getcwd
import mtranslate as mt

chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--use-fake-ui-for-media-stream")  # To auto-allow microphone access
chrome_options.add_argument("--headless=new")  # Run in headless mode


driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
website = "https://bytemetushar.github.io/STT_Helper_page/"
driver.get(website)
rec_file =f"{getcwd()}\\input.text"


def QueryModifier(Query):
    new_query = Query.lower().strip()
    query_words = new_query.split()
    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        if query_words[-1][-1] in ['.','?','!']:
            new_query = new_query[:-1]+"?"
        else:
            new_query += "?"
    else:
        if query_words[-1][-1] in ['.','?','!']:
            new_query = new_query[:-1]+"."
        else:
            new_query += "."
    return new_query.capitalize()


def UniversalTranslator(Text):
    english_translation = mt.translate(Text,"en","auto")
    return english_translation


def listen():
    try:
        start_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.ID, "startButton")))
        start_button.click()
        print("Listening...")
        output_text = ""
        is_second_click = False
        while True:
            output_element = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "output")))
            current_text = output_element.text.strip()
            if "Start" in start_button.text and is_second_click:
                if output_text:
                    is_second_click = False
            elif "Listening..." in start_button.text:
                is_second_click = True
            if current_text != output_text:
                output_text = current_text
                updated_text = QueryModifier(UniversalTranslator(output_text))
                with open(rec_file,"w") as file:
                    file.write(updated_text.lower())
                    print("Sir said:"+ updated_text)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        print("Error:", e)
