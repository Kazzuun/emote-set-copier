# 7tv emote set copier

Command line tool to copy 7tv emote sets.


## Usage

Download a fitting executable from [releases](https://github.com/Kazzuun/emote-set-copier/releases/latest).

OR

1. Clone the repo.
   ```sh
   git clone https://github.com/Kazzuun/emote_set_copier.git
   ```
2. Install requirements.
   ```sh
   pip install -r requirements.txt
   ```
3. Run the script.
   ```sh
   python main.py
   ```

Notice that the copying process might take a long time if there are multiple emotes. Adding emotes might also fail once in a while due to ratelimit of the 7tv api, but the script will wait until it can add again.


## Warning

The script asks if you want to save the token in a file. It will save it there in plain text which can be dangerous. Only choose yes if you are sure this is fine.


## Finding the token

1. Go to 7tv's [website](https://7tv.app/). Make sure you are logged in.
2. Open developer tools (ctrl + shift + I).
3. Navigate to the _Storage_ tab.
4. Open _Local Storage_.
5. Copy the value of the 7tv-token entry.
