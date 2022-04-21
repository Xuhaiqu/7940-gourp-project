# 7940-gourp-project

Group number: 45
Group members (Github Account):
- Zhan Wenxun (zhanwenxun)
- Yang Xu (???)
- Xu Haiqu (Xuhaiqu)

chatbot name: group45

## Commands
1. /start : Start the service, showing the available commands
2. /recipe (keyword) : Realize precise search (冰糖红枣炖银耳)
3. /search (partial keyword) : Realize fuzzy search (红枣)
4. /tag : Show tags for all recipes (no duplicates)
5. /tag (keyword) : Show recipe names that belong to this tag
6. /favorite : Show your favorite recipe names
7. /help : Show developer info

## Deployments
#### CMD
1. pip install -r requirements.txt
2. python chatbot.py

#### Docker
1. docker build . -t chatbot
2. docker run --name mycontainer -d chatbot
