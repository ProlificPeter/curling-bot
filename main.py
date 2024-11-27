import os
import sys
import pprint
from Observer import Observer
from google_auth_oauthlib.flow import InstalledAppFlow
import googleapiclient.discovery
import googleapiclient.errors
import google.oauth2.credentials
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import discord
from dotenv import load_dotenv

# Set Environment Variables based on path
envPathProd = os.path.join(os.path.dirname(__file__), '.env')
envPathStage = os.path.join(os.path.dirname(__file__), '.env.stage')
# Default Environment is Prod
isProd = True
envPath = envPathProd

load_dotenv(envPath)
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DISCORD_GUILD')
CHANNEL_ID = int(os.getenv('DISCORD_CHANNEL_ID')) # pyright: ignore

# CONSTANTS
HOST = "localhost"
PORT_A = 4455
PORT_B = 4456
SHEET_A_NAME = "Sheet A"
SHEET_B_NAME = "Sheet B"
VALID_BROADCAST_STATUSES = ('active', 'completed')
INVALID_BROADCAST_STATUSES = ('upcoming')
# CLIENT_SECRETS_FILE = "client_secrets_output.json"
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
SCOPES = ['https://www.googleapis.com/auth/youtube',
'https://www.googleapis.com/auth/youtube.force-ssl',
'https://www.googleapis.com/auth/youtubepartner',
'https://www.googleapis.com/auth/youtube.upload']

# Google Shenanigans


# flow = InstalledAppFlow.from_client_secrets_file(
#     CLIENT_SECRET_FILE,
#     scopes=SCOPES)

# credentials = flow.run_local_server(host='localhost',
#     port=8080,
#     authorization_prompt_message='Please visit this URL: {url}',
#     success_message='The auth flow is complete; you may close this window.',
#     open_browser=True)



# Check if launched with staging argument
if len(sys.argv) > 0:
    print("Arguments fed.")
    if "--staging" in sys.argv:
        isProd = False
        envPath = envPathStage


# Configure Observers
try:
    observerA = Observer(HOST, PORT_A, SHEET_A_NAME)
except ValueError as e:
    print("Sheet A has not connected")

try:
    observerB = Observer(HOST, PORT_B, SHEET_B_NAME)
except ValueError as e:
    print("Sheet B has not connected")




# Default intents are now required to pass to Client
intents = discord.Intents.all()
client = discord.Client(intents=intents)

# Default Colors
HEX_RED = 0xff0000
HEX_GREEN = 0x00ff00
HEX_BLUE = 0x0000ff
HEX_YELLOW = 0xffff00

def get_authenticated_service():
    creds = None
      # The file token.json stores the user's access and refresh tokens, and is
      # created automatically when the authorization flow completes for the first
      # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CLIENT_SECRET_FILE, SCOPES
            )
            creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    return creds

# Retrieve a list of broadcasts with the specified status.
async def listActiveBroadcasts(youtube):
    list_broadcasts_request = youtube.liveBroadcasts().list(
        broadcastStatus="active",
        broadcastType="all",
        part='snippet',
        maxResults=20
    )
    response = list_broadcasts_request.execute()
    print(response)
    activeBroadcastList = []
    if response:
        for broadcast in response.get('items', []):
            activeBroadcastList.append(broadcast['snippet']['title'])
    else:
        activeBroadcastList.append("No Active Broadcasts")
    print(activeBroadcastList)
    return(activeBroadcastList)

# Retrieve a list of broadcasts with the specified status.
async def listUpcomingBroadcasts(youtube):
    pp = pprint.PrettyPrinter(depth=4)
    list_broadcasts_request = youtube.liveBroadcasts().list(
        broadcastStatus="upcoming",
        broadcastType="all",
        part='snippet',
        maxResults=20
    )
    response = list_broadcasts_request.execute()
    pp.pprint(response)
    upcomingStreamList = []
    if response:
        for broadcast in response.get('items', []):
            upcomingStreamList.append(broadcast['snippet']['title'])
        else:
            upcomingStreamList.append("No Upcoming Broadcasts")
    print(upcomingStreamList)
    return upcomingStreamList

# TODO: Move Command Handles to this function
async def handleCommand(command, message):
    # print("handleCommand fired")
    matchSplit = command + " "
    cleanedMessage = message.content.split(matchSplit)
    match command:
        case "!command":
            print(command)
        case _:
            print("Whoops!")

async def provideStreams():
    print("Streams")

# Set up YouTube
api_service_name = "youtube"
api_version = "v3"
credentials = get_authenticated_service()
youtube = googleapiclient.discovery.build(
        api_service_name, api_version, credentials=credentials)

@client.event
async def on_ready():
    print(f'{client.user.name} has connected to Discord!')



@client.event
async def on_message(message):
    # Check if the message was from the bot -- ignore if so
    if message.author == client.user:
        return
    #  Check if it's in the dedicated channel, then Check for Spotify URL,
    if message.channel.id != CHANNEL_ID:
        # print("URL posted outside of dedicated channel")
        return
    # TODO: Fix the if statement to not fire when
    if client.user in message.mentions:
        # Handle !hipster command request
        if "!command" in message.content.lower():
            embed = discord.Embed(title="BiffBot Available Commands", description="Be sure to @BiffBot before adding your command!", color=HEX_BLUE)
            await message.channel.send(embed=embed)
                # print("!command fired")
        elif "!streams" in message.content.lower():
            activeStreams = await listActiveBroadcasts(youtube)
            prettyPrintActive = ""
            # TODO: Output list of active streams
            # embed = discord.Embed(title="List of Available Streams", description="")
            for stream in activeStreams:
                prettyPrintActive = prettyPrintActive + stream + "\n"
            embed = discord.Embed(title="Active Streams", description=prettyPrintActive, color=HEX_GREEN)
            await message.channel.send(embed=embed)
        elif "!borked" in message.content.lower():
            borkedStreams = await listUpcomingBroadcasts(youtube)
            prettyPrintBorked = ""
            for stream in borkedStreams:
                prettyPrintBorked = prettyPrintBorked + stream + "\n"
            embed = discord.Embed(title="Borked Streams", description=prettyPrintBorked, color=HEX_RED)
            await message.channel.send(embed=embed)

        else:
            embed = discord.Embed(title="Hello, still working on myself; try checking out !command for available functions!", color=0xffff00)
            await message.channel.send(embed=embed)
            print("Failure fired")



client.run(TOKEN)
