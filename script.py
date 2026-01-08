import logging
import requests
from telebot import TeleBot,types,util
from telebot.util import user_link
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import pymysql.cursors
from datetime import datetime

#**********Fot loging************
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)
#*********************************

bot = TeleBot("7680227515:AAEGWTrv01USEQW6ktKj89fzfnGpoCvsXUM",parse_mode="HTML")

markup = InlineKeyboardMarkup()

#today = datetime.date()
@bot.message_handler(commands=['id'])
def debug(dbg):
    user = dbg.from_user.id
    bot.send_message(dbg.chat.id, user)
    
@bot.message_handler(commands=['start'])
def start(msg):
    bot.send_message(msg.chat.id,f"Привіт! {user_link(msg.from_user)} Відправ сюди QR код зі своєї робочої локації",
                      reply_markup=markup)
    
@bot.message_handler(content_types=["photo"])
def scanQr(msg):
    user_name = msg.from_user.username
    connection = pymysql.connect(host='srv1574.hstgr.io', port=3306, user='u197934251_GRKY', password='Gorkiy270588',
                                 database='u197934251_GRKYPeople',
                                 cursorclass=pymysql.cursors.DictCursor)
    mycursor = connection.cursor()
    mycursor.execute("SELECT nickname FROM grky_people")
    myresults = mycursor.fetchall()
    userstatus = False
    for result in myresults:
        if user_name == result['nickname']:
            userstatus = True
            bot.send_message(msg.chat.id, f"Користувач {user_name} присутній в базі")
            break
        else: userstatus = False


    if userstatus == True:
        file_info = bot.get_file(msg.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        todaydate = datetime.today().strftime('%d-%m-%Y')

        with open("qr.png", 'wb') as new_file:
            new_file.write(downloaded_file)

        with open("qr.png", "rb") as img:
            url = "https://api.qrserver.com/v1/read-qr-code/"
            files = {"file": img}

            response = requests.post(url, files=files)

            if response.status_code == 200:
                data = response.json()
                scanneddata = data[0]['symbol'][0]['data']
                bot.send_chat_action(chat_id=msg.chat.id, action="typing")
                # bot.send_message(msg.chat.id, scanneddata)

            else:
                bot.send_message(msg.chat.id, f"Error: {response.status_code}\n send the correct qr img",
                                 reply_markup=markup)

        mycursor = connection.cursor()
        mycursor.execute(f"SELECT * FROM grky_loc_qr where date='{todaydate}'")
        myresult = mycursor.fetchall()

        if len(myresult) != 0:
            row = myresult[0]
            # bot.send_message(msg.chat.id, row)
            # bot.send_message(msg.chat.id, scanneddata)
            if scanneddata in row.values():
                qrresult = True
                bot.send_message(msg.chat.id, f"QR код вірний!")
                #bot.send_message(msg.chat.id, f"DEBUG MESSAGE: scanned data = {scanneddata}{qrresult}")
            else:
                qrresult = False
                bot.send_message(msg.chat.id, 'Невірний QR код!')
                bot.send_message(msg.chat.id, f"DEBUG MESSAGE: scanned data =  {scanneddata}{qrresult}")
        else:
            bot.send_message(msg.chat.id, 'Невірна дата')

        if qrresult == True:
            user_name = msg.from_user.username
            global starttime
            #bot.send_message(wstart.chat.id, qrresult)
            now = datetime.now()
            todaydate = datetime.today().strftime('%d-%m-%Y')
            starttime = now.strftime("%H:%M")
            location = scanneddata.split(":")
            location = location[0]
            bot.send_message(msg.chat.id, f"Час початку робочого дня:{starttime}")

            mycursor = connection.cursor()
            mycursor.execute(f"update grky_timesheet set {user_name} = '{todaydate} loc-{location}_start-{starttime}' where date = '{todaydate}'")
    else:
        bot.send_message(msg.chat.id,f"Користувач {user_name} в базі не знайдений, зверніться до адміністратора персоналу.")


@bot.message_handler(commands=['end'])
def endwork(wend):
    user_name = wend.from_user.username
    todaydate = datetime.today().strftime('%d-%m-%Y')
    now = datetime.now()
    endtime = now.strftime("%H:%M")
    etime = datetime.strptime(f"{endtime}", "%H:%M" )
    connection = pymysql.connect(host='srv1574.hstgr.io', port=3306, user='u197934251_GRKY', password='Gorkiy270588',
                                 database='u197934251_GRKYPeople',
                                 cursorclass=pymysql.cursors.DictCursor)
    mycursor = connection.cursor()
    mycursor.execute(f"select {user_name} from grky_timesheet where date = '{todaydate}'")
    myresults = mycursor.fetchall()
    if len(myresults) != 0:
      for sqlresult in myresults:
          tableresult = sqlresult[user_name]
    tabletime = tableresult.split('start-')
    tabletime = tabletime[1]
    stime = datetime.strptime(f"{tabletime}", "%H:%M")
    totaltime = etime - stime
    bot.send_message(wend.chat.id,f"Зміну закрито. Робочий час за зміну складає: {totaltime}")
    mycursor.execute(f"update grky_timesheet set {user_name} = '{tableresult} end-{endtime} time-{totaltime}' where date = '{todaydate}'")


@bot.message_handler(commands=['time'])
def worktime(wtime):
    user_name = wtime.from_user.username
    todaydate = datetime.today().strftime('%d-%m-%Y')

    connection = pymysql.connect(host='srv1574.hstgr.io', port=3306, user='u197934251_GRKY', password='Gorkiy270588',
                                 database='u197934251_GRKYPeople',
                                 cursorclass=pymysql.cursors.DictCursor)
    mycursor = connection.cursor()
    mycursor.execute(f"select {user_name} from grky_timesheet where date='{todaydate}'")
    myresult = mycursor.fetchall()
    row = myresult[0]
    time = row[user_name]
    bot.send_message(wtime.chat.id, f"Загальний час роботи {todaydate}: {time}")

bot.infinity_polling()

#@bot.message_handler(commands=['user'])
def usercheck(usrchk):
    user_name = usrchk.from_user.username
    connection = pymysql.connect(host='srv1574.hstgr.io', port=3306, user='u197934251_GRKY', password='Gorkiy270588',
                                 database='u197934251_GRKYPeople',
                                 cursorclass=pymysql.cursors.DictCursor)
    mycursor = connection.cursor()
    mycursor.execute("SELECT nickname FROM grky_people")
    myresults = mycursor.fetchall()
    for result in myresults:
        if user_name == result['nickname']:
            status = True
            bot.send_message(usrchk.chat.id, f"Користувач {user_name} присутній в базі")

#@bot.message_handler(commands=['begin'])
def startwork(wstart):
    user_name = wstart.from_user.username
    global starttime
    #bot.send_message(wstart.chat.id, qrresult)
    now = datetime.now()
    todaydate = datetime.today().strftime('%d-%m-%Y')
    starttime = now.strftime("%H:%M")
    bot.send_message(wstart.chat.id,f"Час початку робочого дня:{starttime}")

    connection = pymysql.connect(host='srv1574.hstgr.io', port=3306, user='u197934251_GRKY', password='Gorkiy270588',
                                 database='u197934251_GRKYPeople',
                                 cursorclass=pymysql.cursors.DictCursor)
    mycursor = connection.cursor()
    mycursor.execute(f"update grky_timesheet set {user_name} = 'start: {starttime}' where date = '{todaydate}'")