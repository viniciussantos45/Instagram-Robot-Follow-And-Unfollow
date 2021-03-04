import json
import datetime as date

from  time import sleep
from library import start, login, getFollowersAccount, getFollowersAccountByJS, followUser, getFollowingsAccountByJS, unfollowUser

CONFIG = {} 
BASEDATA = {}

with open('config.json') as config_file:
    CONFIG = json.load(config_file)
    config_file.close()

with open('basedata.json') as base_data_file:
    BASEDATA = json.load(base_data_file)
    base_data_file.close()

def userFollowedInRobot(username):
    for followingUser in BASEDATA['followed_the_robot']:
        if followingUser['username'] == username:
            return True
    return False

def saveBaseData():
    with open('basedata.json', 'w') as base_data_file:
        json.dump(BASEDATA, base_data_file)
        base_data_file.close()

def loadBaseData():
    with open('basedata.json') as base_data_file:
        BASEDATA = json.load(base_data_file)
        base_data_file.close()

def isFollowMe(username):
    for followingUser in BASEDATA['myFollowings']:
        if followingUser['username'] == username:
            return True
    return False


def loadFollowersReciprocal():
    loadBaseData()

    usernamesFollowing = list()
    usernamesFollower = list()
    usernamesReciprocal = list()
    usernamesNotReciprocal = list()

    for followingUser in BASEDATA['myFollowings']:
        usernamesFollowing.append(followingUser['username'])

    for followerUser in BASEDATA['myFollowers']:
        usernamesFollower.append(followerUser['username'])

    for usernameFlg in usernamesFollowing:
        if usernameFlg in usernamesFollower:
            usernamesReciprocal.append(usernameFlg)
        else:
            usernamesNotReciprocal.append(usernameFlg)

    BASEDATA['followersReciprocal'] = usernamesReciprocal
    BASEDATA['followersNotReciprocal'] = usernamesNotReciprocal
    saveBaseData()

    return usernamesReciprocal

def getDictFollwedInRobot(username):
    for followingUser in BASEDATA['followed_the_robot']:
        if followingUser['username'] == username:
            return followingUser
    return False

def removeDictFromArray(keyReference, keyValue, arr):
    copyArr = arr
    
    for index, item in enumerate(arr):
        if item[keyReference] == keyValue:
            copyArr.pop(index)
            return copyArr
    return copyArr

def unfollowNotReciprocal(limit = 3, timeSleep = 20):
    loadFollowersReciprocal()

    c = 0
    while c < limit:
        username = BASEDATA['followersNotReciprocal'][c]
        if userFollowedInRobot(username):
            dataFollowed = getDictFollwedInRobot(username)

            followDateTime = date.datetime.strptime(dataFollowed['followDateTime'],'%Y-%m-%d %H:%M:%S')
            now = date.datetime.now()

            differenceHours = (now - followDateTime)
            differenceHours = differenceHours.total_seconds()/3600

            if differenceHours > 72:
                unFollowed = unfollowUser(username)
                if unFollowed :
                    BASEDATA['followersNotReciprocal'].remove(username)
                    print(f"Unfollow {username}")
                    BASEDATA['myFollowings'] = removeDictFromArray('username', username, BASEDATA['myFollowings'])
            else:
                print(f"User {username} was followed for {differenceHours} hours")

                c += 1
                limit += 1
                continue
        else:
            unFollowed = unfollowUser(username)
            if unFollowed:
                BASEDATA['followersNotReciprocal'].remove(username)
                print(f"Unfollow {username}")
                BASEDATA['myFollowings'] = removeDictFromArray('username', username, BASEDATA['myFollowings'])

        saveBaseData()
        c += 1
        sleep(timeSleep)




driverInsta = start()
login(CONFIG['username'], CONFIG['password'])

# Verify if last execute
last_search_followers = date.datetime.strptime(BASEDATA['execute_list_followers_base'],'%Y-%m-%d %H:%M:%S')
now = date.datetime.now()

differenceHours = (now - last_search_followers)
differenceHours = differenceHours.total_seconds()/3600
if differenceHours > 24:
    # search followers in base accounts
    for user_base in CONFIG['accounts_base_follow']:
        print(f"Searching followers for {user_base} ...")
        followers = getFollowersAccountByJS(user_base)
        BASEDATA['followers_base'][user_base] = followers
    
    #update base list
    BASEDATA['execute_list_followers_base'] = date.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    saveBaseData()

    #update my interactions
    myFollowers = getFollowersAccountByJS(CONFIG['username'])
    myFollowings = getFollowingsAccountByJS(CONFIG['username'])

    BASEDATA['myFollowers'] = myFollowers
    BASEDATA['myFollowings'] = myFollowings

    saveBaseData()
    loadFollowersReciprocal()


# Following users from base
for user_base in CONFIG['accounts_base_follow']:

    print(f"Following users of {user_base}")
    for user_to_follow in BASEDATA['followers_base'][user_base]:
        loadBaseData()

        username_to_follow = user_to_follow['username']
        fullname_to_follow = user_to_follow['full_name']

        if username_to_follow != CONFIG['username'] and not userFollowedInRobot(username_to_follow):
            followed = followUser(username_to_follow)

            if followed:
                print(f"Followed '{username_to_follow}' of user base: '{user_base}'")

                userFollowed = {'username': username_to_follow, 'base': user_base,  'followDateTime': date.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                BASEDATA['followed_the_robot'].append(userFollowed)
                BASEDATA['last_follow'] = userFollowed

                saveBaseData()
                unfollowNotReciprocal(CONFIG['unfollow_per_followed'], CONFIG['time_between_follow'] / 2)
                #sleep(CONFIG['time_between_follow'])
        

driverInsta.quit()
print('Finish script')
    