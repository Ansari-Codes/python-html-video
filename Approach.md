get prompt
list per scene title

cycle:
    ith scene as s
    generate explaination approach using scene title, main prompt and all previous titles only along with last scene approaches and htmls
    save progress
    feed approach to llm to generate html prompt with stylistics and details
    save progress
    feed html prompt to generate html
    save html
    save progress
    generate audio transcript
    save progress
    generate audio
    save progress

cycle:
    for each scene:
        render .mp4s for all scenes

attach all .mp4s
attach all .mp3s/.wavs
combine audio with vide

project/
│
├── project.json
│
├── scenes/
│      001/
│          approach.md
│          storyboard.json
│          html_prompt.md
│          index.html
│          transcript.txt
│          audio.wav
│          render.mp4
│          metadata.json
│
│      002/
│
├── assets/
├── cache/
├── logs/
├── renders/
└── final.mp4