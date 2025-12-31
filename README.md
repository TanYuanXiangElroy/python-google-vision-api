# Google Lens Visual Intelligence Service

Trying to do a reverse engineer of google lens so I can use it in another one of my project I am thinking off

# Project Description

This project was created as I wanted to try to make a "pokedex" and instead of fiddeling around with AI I wanted to use , the Google Lens engine as it is capable of identifying exact product names, brands, and fictional characters (e.g., "Pokémon Center Charmander Plush").


# Features
So I didn't want to fiddel around with web design so I used a simple streamlit page that I can upload local files or capture images directly via webcam and I can test the various implemtations I come accross (for now there is 3 google Vision API, Sepreapi, Google lens scrapping)

I use them to get the frequence of word that come out in the title to get the "best guess"


# The Architecture (The Process)

So it is a simple Client-Server where Streamlit is the front end and Flask is the back end calling the API/doing the scrapping

For scraping it uses ImgBB to upload a image temporarily to generate a publicly accessible URL for Serpreapi and google lens to access

And for the scraping it Spins up a  Chrome instance. Navigates to lens.google.com/collects the dynamic HTML using BeautifulSoup and is simplified

# Lessons Learned: API vs. Scraping
While playing arround, I tried the official Google Cloud Vision API vs the Lens "Scraper". The difference in data quality was significant.

1. The Limitation of Enterprise APIs
When passing a Charmander plush to the official Google Cloud Vision API, the model returned generic labels. It prioritized safety over specificity.
![google offical API output](image/Google Cloud Vision API output.png)

Result: "Stuffed Toy" (Technically true, but useless for a Pokedex).

2. The Power of Consumer API
By letting Sepreapi to scrap Google Lens for us, we gained access to Google's data in simple clean json data to use it to impliment and I realised thats why alot of people use other people API
![SeprAPI output](image/SerpApi output.png)

Result: Direct clear links to "Charmander Plush" listings.

3. Web scraping google lens by my self
So here is a successful picture of what it looked like to scrap I could improve it to give cleaner data but I only needed the title to try to test what the picture represents which is also what I did with Sereapi
![len scrap output](image/Selenium Scraping output (1).png)

You can see the Rrsult: "Charmander" appeared the most times. "Pokemon" appeared second most times. The identification make it pretty accuret compared to Google Cloud Vision API which only guess plush toy


# How to Run
## Prerequisites
```bash
Python 3.9+
Google Chrome installed on the host machine.
An API Key from ImgBB.
And API key for Serpapi or Google Cloud Vision API if you want to try the other 2 methods
```
1. Setup Environment
Clone the repository and create a .env file in the root directory and download the json key and rename it as my-google-cloud-key.json: 

```Bash
IMGBB_KEY=your_api_key_here
SERPAPI_KEY=your_api_key_here
```
2. Install Dependencies

```Bash
pip install -r requirements.txt
```
3. Start the Backend (Flask)
This service listens for image requests on Port 5000.

```Bash
python server.py
# Output: Running on http://0.0.0.0:5000
```
4. Start the Frontend (Streamlit)
Open a new terminal to run the UI.

```Bash
streamlit run app.py
# Output: Local URL: http://localhost:8501
```
# Future Improvements

If you have any other suggesstion on how to web scrap better do let me know as I only know how to do that google stop me form web scraping after a few attempts and when I switch wifi I need to restart the authentication by running scrape_lens.py to test if the class change and allow for my ip to show I am a human been

And also I should try add docker instead of a VM (I should do it soon)

Find some way to host the web scraping on the cloud instead of localy as I still can't figure out how to bypass google Auth
