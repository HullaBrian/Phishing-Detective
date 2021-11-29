import json
import os
import time

if bool(json.load(open("config.json"))["startup"]["verifyLibraries"]):
    import packageManager  # makes sure all necessary packages are installed

if bool(json.load(open("config.json"))["startup"]["installTor"]):
    import installTor  # Installs tor

import selenium.common.exceptions
import datetime
import urllib3.exceptions
from command import command
import art
import requests

global url
global commands
global whiteListedPorts
global settings


class hlp(command):
    def __init__(self):
        super().__init__("help", ["help"])

    def execute(self, filler):
        print("\nhelp   Displays this menu")
        print("\"Set\" Commands")
        for x in range(len("\"Set\" Commands")):
            print("-", end="")
        print()

        print("\tCommand", end="")
        maxCommandNameLength = 0
        for command in commands:
            if len(command.title) > maxCommandNameLength:
                maxCommandNameLength = len(command.title)
        if maxCommandNameLength >= len("Command"):
            for x in range(maxCommandNameLength - len("Command") + 3):
                print(" ", end="")
        else:
            for x in range(len("Command") + 3):
                print(" ", end="")

        print("Description")

        print("\t", end="")
        for x in range(len("Command")):
            print("-", end="")
        if maxCommandNameLength >= len("Command"):
            for x in range(maxCommandNameLength - len("Command") + 3):
                print(" ", end="")
        else:
            for x in range(len("Command") + 3):
                print(" ", end="")
        for x in range(len("Description")):
            print("-", end="")
        print()

        setCommands = []
        for command in commands:
            if command.requiredCommands[0] == "set":
                setCommands.append(command)
        for command in setCommands:
            print("\t" + str(command.title), end="")
            for x in range(max(maxCommandNameLength, len("Command")) - len(command.title) + 3):
                print(" ", end="")
            print(str(command.hlp))

        # Section seperator

        print("\n\"Get\" Commands")
        for x in range(len("\"Get\" Commands")):
            print("-", end="")
        print()

        print("\tCommand", end="")
        maxCommandNameLength = 0
        for command in commands:
            if len(command.title) > maxCommandNameLength:
                maxCommandNameLength = len(command.title)
        if maxCommandNameLength >= len("Command"):
            for x in range(maxCommandNameLength - len("Command") + 3):
                print(" ", end="")
        else:
            for x in range(len("Command") + 3):
                print(" ", end="")

        print("Description")

        print("\t", end="")
        for x in range(len("Command")):
            print("-", end="")
        if maxCommandNameLength >= len("Command"):
            for x in range(maxCommandNameLength - len("Command") + 3):
                print(" ", end="")
        else:
            for x in range(len("Command") + 3):
                print(" ", end="")
        for x in range(len("Description")):
            print("-", end="")
        print()

        setCommands = []
        for command in commands:
            if command.requiredCommands[0] == "get":
                setCommands.append(command)
        for command in setCommands:
            print("\t" + str(command.title), end="")
            for x in range(max(maxCommandNameLength, len("Command")) - len(command.title) + 3):
                print(" ", end="")
            print(str(command.hlp))


class setUrl(command):
    def __init__(self):
        super(setUrl, self).__init__("set url", ["set", "url"], True, hlp="sets the url to a given url")
        self.hlp = "sets the url to a given url"

    def execute(self, data):
        global url
        url = data
        print(" ")
        print("url ==> " + url)
        print(" ")


class getInfo(command):
    def __init__(self):
        super().__init__("get info", ["get", "info"], hlp="gets the relevant information on a given url")
        self.hlp = "give the relevant information on a given url"
        self.info = []
        self.expirationDate = 0

    def execute(self, filler):
        import whois
        whois_info = whois.whois(url)

        self.info = []
        self.info.append(bool(whois_info.domain_name))
        self.info.append(whois_info.registrar)
        self.info.append(whois_info.whois_server)
        self.info.append(whois_info.creation_date)
        self.info.append(whois_info)

        print("Registered: " + str(self.info[0]))
        print("Registrar: " + str(self.info[1]))
        print("Server: " + str(self.info[2]))
        print("Creation date: " + str(self.info[3]))
        print("Other info: " + str(self.info[4]))

        self.expirationDate = whois_info.expiration_date

    def getInformation(self):
        import whois
        try:
            whois_info = whois.whois(url)
        except Exception:
            print("Invalid url")
            return

        return whois_info["org"]


class sslverify(command):
    def __init__(self):
        super().__init__("get sslverify", ["get", "sslverify"], hlp="verifies the SSL certificate of the url")
        self.hlp = "verifies the SSL certificate of the url"

    def execute(self, filler):
        import socket
        import ssl
        try:
            ctx = ssl.create_default_context()
            with ctx.wrap_socket(socket.socket(), server_hostname=url) as s:
                s.connect((url, 443))
            print(url + " has a VALID SSL certificate")
        except Exception as e:
            print(url + " has an INVALID SSL certificate, error:", e)


class isRegistered(command):
    def __init__(self):
        super().__init__("get registration", ["get", "registration"], False, "determines whether or not a domain is registered or not")
        self.hlp = "determines whether or not a domain is registered or not"

    def execute(self, data):
        import whois
        try:
            whois_info = whois.whois(url)
        except Exception:
            print("Invalid url")
            return
        tmp = bool(whois_info.domain_name)
        if tmp:
            print(url + " is a registered domain under " + whois_info.registrar)
        else:
            print(url + " is not a registered domain")


class getPort(command):
    def __init__(self):
        super().__init__("get port", ["get", "port"], hlp="retrieves the port of the url")
        self.hlp = "retrieves the port of the url"

    def execute(self, filler):
        try:
            port = int(url.split(":")[2].split("/")[0])  # Ex. https://google.com:80/ -> ["80/"] -> 80
        except IndexError:
            print("Could not find a port number in " + url)
            return
        print(url + " runs through port", port)

        if port not in whiteListedPorts:
            print("Port detected as suspicious")
        else:
            print("Port detected as a commonly used port number")


class getScreenShot(command):
    def __init__(self):
        super().__init__("get screenshot", ["get", "screenshot"], hlp="retrieves a screenshot of a given url using TOR")
        self.hlp = "retrieves a screenshot of a given url using TOR"

    def execute(self, data):
        from selenium import webdriver
        options = webdriver.ChromeOptions()
        if settings["browser"]["headlessMode"]:
            options.add_argument("--headless")  # Launch headless browser
        options.add_argument(f"--window-size={settings['screenshot']['width']},{settings['screenshot']['height']}")

        if settings["browser"]["forceTor"]:
            os.system("start Tor_Browser/Browser/TorBrowser/Tor/tor.exe")
            print("Applying proxy...", end="")
            if settings["browser"]["proxy"] == "":
                options.add_argument('--proxy-server=%s' % "socks5://127.0.0.1:9050")  # Use tor proxy
            else:
                print("Proxy specified conflict with forceTor setting. Either change the proxy to \"\", or turn off forceTor")
            print("Done!")
        else:
            if settings["browser"]["proxy"] != "":
                print("Applying proxy...", end="")
                options.add_argument('--proxy-server=%s' % f"{settings['browser']['proxy']}")  # Use other proxy
                print("Done!")

        driver = webdriver.Chrome(options=options)

        print("Loading url...", end="")
        try:
            driver.get(url)
            print("Done!")
        except selenium.common.exceptions.WebDriverException:
            print("Failed to load url.")

        print("Taking screenshot...", end="")
        driver.save_screenshot("screenshots/{}.png".format(url[url.index("//") + 2:].replace("/", "").replace(".", "")))
        print("Done!\nScreenshot will be saved under the 'screenshots' folder.")

        os.system('taskkill /IM "tor.exe" /F')  # Make sure to end tor
        print("Killed tor client.")


def main():
    art.tprint("Phishing-Detective")  # we can discuss fonts later, I say we get some of the primary code done before
    # To add a command, simply add a command(command title, required titles) object to commands
    global commands
    commands = []
    print("Registering commands...", end="")
    commands.append(setUrl())
    commands.append(getInfo())
    commands.append(sslverify())
    commands.append(getPort())
    commands.append(isRegistered())

    print("Applying settings from " + os.getcwd() + "/config.json")
    global settings
    try:
        with open("config.json") as config:
            settings = json.dumps(config)
    except FileNotFoundError:
        print("Configuration file not found. Creating new file...", end="")
        config = open("config.json", "w+")
        settings = {
            "screenshot": {
                "width": 1920,
                "height": 1080
            },
            "browser": {
                "forceTor": True,
                "proxy": "socks5://127.0.0.1:9050",
                "defaultBrowser": "chrome",
                "headlessMode": True
            },
            "startup": {
                "verifyLibraries": True,
                "installTor": True
            }
        }
        json.dump(settings, config)

    # Used for tor related commands
    try:
        commands.append(getScreenShot())
    except ConnectionRefusedError:
        print("\nError registering a TOR related command. Please verify that TOR is installed properly.\n[WARNING] "
              "Stopping run due to TOR error.")
        return
    except urllib3.exceptions.NewConnectionError:
        print("\nError registering a TOR related command. Please verify that TOR is installed properly.\n[WARNING] "
              "Stopping run due to TOR error.")
        return
    except urllib3.exceptions.MaxRetryError:
        print("\nError registering a TOR related command. Please verify that TOR is installed properly.\n[WARNING] "
              "Stopping run due to TOR error.")
        return
    except requests.exceptions.ConnectionError:
        print("\nError registering a TOR related command. Please verify that TOR is installed properly.\n[WARNING] "
              "Stopping run due to TOR error.")
        return

    commands.append(hlp())  # Put the help addition at the end of adding commands to properly generate the help command
    print("DONE!")

    global whiteListedPorts
    whiteListedPorts = [80, 443]

    while True:  # Loops until exits
        prompt = "pd> "
        print(prompt, end="")

        command = input().lower().split(" ")
        if len(command) >= 3:
            cmd = command[0]
            subcmd = command[1]
            arg = command[2]
            params = [cmd, subcmd, arg]
        elif len(command) >= 2:
            cmd = command[0]
            subcmd = command[1]
            params = [cmd, subcmd]
        elif len(command) >= 1:
            cmd = command[0]
            params = [cmd]

        if cmd == "exit":
            exit()
            break
        executedCommand = False
        if len(params) == 1:
            if params[0] == "url":
                try:
                    print("Current url is \"" + url + "\"")
                except NameError:
                    print("No url is set")
                executedCommand = True
        for command in commands:
            if command.matchesParams(params):
                command.execute(params[-1])
                executedCommand = True
        if not executedCommand:
            print("Invalid command")
            from difflib import SequenceMatcher
            mostSimilarCommandId = ""
            highestSimiliarity = 0
            for command in commands:
                if SequenceMatcher(None, command.title, cmd).ratio() > highestSimiliarity:
                    highestSimiliarity = SequenceMatcher(None, command.title, cmd).ratio()
                    mostSimilarCommandId = command.title
            print("\tDid you mean '" + mostSimilarCommandId + "'?")


main()
