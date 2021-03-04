import os
import json
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from PIL import Image
from  time import sleep

with open('config.json') as config_file:
    CONFIG = json.load(config_file)
    config_file.close()

chrome_options = webdriver.ChromeOptions()

# chrome_options.add_argument("--headless")
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--kiosk-printing')
chrome_options.add_argument("--ignore-certificate-errors")
driver = webdriver.Chrome(CONFIG['dirChromeDriver'], options=chrome_options)
driver.set_script_timeout(600)

def scriptBody(username, returnType = 'followers'):
    script = f"let username = '{username}'"
    script += '''
        let followers = [], followings = []
        try {
        let res = await fetch(`https://www.instagram.com/${username}/?__a=1`)

        res = await res.json()
        let userId = res.graphql.user.id

        let after = null, has_next = true
        while (has_next) {
            await fetch(`https://www.instagram.com/graphql/query/?query_hash=c76146de99bb02f6415203be841dd25a&variables=` + encodeURIComponent(JSON.stringify({
            id: userId,
            include_reel: true,
            fetch_mutual: true,
            first: 50,
            after: after
            }))).then(res => res.json()).then(res => {
            has_next = res.data.user.edge_followed_by.page_info.has_next_page
            after = res.data.user.edge_followed_by.page_info.end_cursor
            followers = followers.concat(res.data.user.edge_followed_by.edges.map(({node}) => {
                return {
                username: node.username,
                full_name: node.full_name
                }
            }))
            })
        }
        console.log('Followers', followers)

        has_next = true
        after = null
        while (has_next) {
            await fetch(`https://www.instagram.com/graphql/query/?query_hash=d04b0a864b4b54837c0d870b0e77e076&variables=` + encodeURIComponent(JSON.stringify({
            id: userId,
            include_reel: true,
            fetch_mutual: true,
            first: 50,
            after: after
            }))).then(res => res.json()).then(res => {
            has_next = res.data.user.edge_follow.page_info.has_next_page
            after = res.data.user.edge_follow.page_info.end_cursor
            followings = followings.concat(res.data.user.edge_follow.edges.map(({node}) => {
                return {
                username: node.username,
                full_name: node.full_name
                }
            }))
            })
        }'''
    script += f"return {returnType}"

    script +=   '''} catch (err) {
            return 'Invalid username'
        }'''
    return script

def scriptGetFollowers(username):
    return scriptBody(username)

def scriptGetFollowings(username):
    return scriptBody(username, 'followings')

def openUserPage(username):
    driver.get(f"https://instagram.com/{username}")

def goToHome():
    driver.get("https://instagram.com")

def waitElement(tag, attr, value, timeout = 15, driver = driver):
    element = WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.XPATH, f"//{tag}[@{attr}='{value}']")))
    return element

def waitElementByText(tag, text, timeout = 15, driver = driver):
    element = WebDriverWait(driver, timeout).until(ec.visibility_of_element_located((By.XPATH, f"//{tag}[contains(text(), '{text}')]")))
    return element

def login(username, password):
    print("Login")

    usernameInput = waitElement("input", "name", "username")
    usernameInput.send_keys(username)
    
    passwordInput = waitElement("input", "name", "password")
    passwordInput.send_keys(password)

    submitButton = waitElement("button", "type", "submit")
    submitButton.click()

    # close initial popup
    closePopupButton = waitElement("div", "class", "cmbtv")
    closePopupButton.click()

def clickWithActions(element):
    actions = ActionChains(driver)
    actions.click(element)
    actions.perform()

def getFollowersAccount(username):
    openUserPage(username)
    anchorFollowers = waitElement('a', 'href', f'/{username}/followers/')
    clickWithActions(anchorFollowers)

    popupFollowers = waitElement('div', 'class', 'isgrP')
    ulFollowers = popupFollowers.find_element_by_tag_name('ul')
    itemsUl = ulFollowers.find_elements_by_tag_name('li')

    userFollowers = list

    for item in itemsUl:
        usernameFollower, nameFollower, actionFollower = item.text.split("\n")
        obj = {'username': usernameFollower, 'name': nameFollower, 'action': actionFollower}
        userFollowers.append(obj)
    return userFollowers

def getFollowersAccountByJS(username):
    return driver.execute_script(scriptGetFollowers(username))

def getFollowingsAccountByJS(username):
    return driver.execute_script(scriptGetFollowings(username))

def followUser(username):
    openUserPage(username)

    try:
        buttonSendMessage = waitElementByText('button', CONFIG['textButtonSendMessage'], 5)

        if buttonSendMessage:
            return False
    except:
        pass


    buttonFollow = waitElementByText('button', CONFIG['textButtonFollow'])

    if buttonFollow:
        clickWithActions(buttonFollow)
        return True

    return False        

def unfollowUser(username):
    openUserPage(username)

    try:
        buttonFollowing = waitElement('span', 'aria-label', CONFIG['textButtonFollowing'])

        if buttonFollowing:
            clickWithActions(buttonFollowing)
            buttonUnfollow = waitElementByText('button', CONFIG['textButtonFollowingConfirm'])
            clickWithActions(buttonUnfollow)

            return True
    except:
        print("Error function unfollowUser")
        pass


    return False        

def start():
    print("Start bot followers instagram")

    driver.set_window_size(1120, 1050)
    goToHome()

    return driver