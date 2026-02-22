# spotichrd
Get chords and chat about songs you're listening to instantly.

![spotichrd Image](files/spotichrd.png)

# Installation
1. Clone the repository
```
git clone https://github.com/Nathan-Kimm/wics-hackathon
```
2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate      # Mac/Linux
venv\Scripts\activate         # Windows

3. Install all Python dependencies (Ensure pip is installed)
```
pip install -r requirements.txt
```
4. Load the Chrome extension
- Open `chrome://extension`
- Enable Developer Mode
- Click on "Load unpacked"
- Select the cloned repository folder

5.Run the MCP and Flask server (In separate terminals)
```
python3 backend/app.py
python3 MCP/server.py
```

## Inspiration
We were inspired by a common experience of hearing a song and wanting to play guitar or another instrument along with it. This usually required us to jump between multiple apps of websites trying to find the chords or sheet music/tabs to go with it or spend time learning by ear. This takes time, especially when you just wanted to quickly play along. Our solution makes finding the chords instantly accessible when a song is playing on Spotify and allows users to also ask questions related to the song for more resources or to find similar songs.
## What it does
Spotichord is a Chrome extension that connects to your Spotify account and elevates your listening experience in real time. As you play a song, it displays the track, artist, and album art, while a built-in AI chat, powered by Gemini API, lets you ask anything: from basic questions like artist info and similar tracks to advanced explorations such as remixing chords or finding tutorials to play the song. By bringing chords, insights, and guidance together in one place, Spotichord solves the problem of fragmented music learning.
## How we built it
Spotichord leverages the Spotify API to identify the song you’re currently listening to and instantly displays its chord progression for easy reference. Beyond just showing chords, the built-in chat lets you interact with the song in real time. The chat uses MCP (Model Context Protocol) which defines functions to give the chatbot more functionality that it would not have through just an LLM. You can ask general questions like, “What are some ways I can mix up this chord progression?” or utilize more advanced MCP-powered tools for specific functionality, such as finding the best YouTube tutorials for playing the song or finding similar artists/songs from reliable websites.
## Challenges we ran into
The biggest challenge we faced was setting up the MCP. Designing an architecture and prompts that allowed the model to distinguish when to use a tool versus when to rely on its own knowledge took considerable effort. After multiple iterations, we were able to create a fully functional and reliable system.
## Accomplishments that we're proud of
We are proud that we were able to implement the MCP feature as well as create an overall full-stack application that can be easily scaled in the future.
## What we learned
Through this project, we learned how to integrate the Gemini API into an MCP architecture. Furthermore, we learned how to use the Spotify API and integrate it into a Google extension.
## What's next for spotichrd
- Additional MCP Functions
- Additional Information Scraped from Spotify for Analysis
- Expand to Support Multiple Instruments: Allow users to view and interact with progressions for guitar, piano, bass, and more
