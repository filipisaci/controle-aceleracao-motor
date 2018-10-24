#!/usr/bin/python3
import RPi.GPIO as GPIO
import time
import threading
from tkinter import *
from tkinter import messagebox
from PIL import Image
from PIL import ImageTk
from functools import partial
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

### Variaveis globais
sensor = 29
motorHorario = 31
motorAntiHorario = 33
ligado = 0
setpoint = 0
tempoSubida = 0
contador = 0
entrada = 0
sentidoAtual = 0
numeroDentes = 10
rpm = 0
t = 0
t2 = 0
intervaloEmail = 10
controleThread = 0
# contador eh cada vez que o sensor passar pelo dente
contador = 0
# tempoParaUmaVolta = periodo
tempoUmaVolta = 0
# tempoStart é usada para calcular o periodo
tempoStart = time.time()

GPIO.setmode(GPIO.BOARD)
GPIO.setup(motorHorario, GPIO.OUT)
GPIO.setup(motorAntiHorario, GPIO.OUT)
GPIO.setup(sensor, GPIO.IN)

ph = GPIO.PWM(motorHorario, 50) 
ph.start(0)

pa = GPIO.PWM(motorAntiHorario, 50) 
pa.start(0)

master = Tk()
master.minsize(400,400)
master.geometry("400x400")
master.title("Supervisorio")

def on_closing():
    global t, t2
    print('Threads correntes ao sair: ', threading.active_count())
    GPIO.cleanup()
    print('Saindo...')
    master.destroy()
    sys.exit() 

def enviaEmail():
    global sentidoAtual, rpm
    print('Enviando e-mail')
    fromaddr = "engmecasatc@gmail.com"
    toaddr = "filipi.saci@gmail.com;emaildasusanthiel@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "STATUS REPORT DO MOTOR"
    body = "<html> Motor girando no sentido: " + str(sentidoAtual) + "    -  Com a velocidade: " +  str(round(rpm, 2)) + " RPMs </html>"
    msg.attach(MIMEText(body, 'html'))
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "s1a2t3c4")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    t2 = threading.Timer(intervaloEmail, enviaEmail)
    t2.start()

def validaEntrada(entrada):
    return entrada >= 20 and entrada <= 50

def converteEntrada(entrada):
    return int(entrada * (100/50))

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(motorHorario, GPIO.OUT)
    GPIO.setup(motorAntiHorario, GPIO.OUT)
    GPIO.setup(sensor, GPIO.IN)

### Controle do calculo da velocidade
def ajustaBounce():
    controleBounce = int(e1.get())
    if controleBounce >= 20 and controleBounce <= 30:
        GPIO.add_event_detect(sensor, GPIO.RISING, bouncetime=200)
    elif controleBounce > 30 and controleBounce <= 40:
        GPIO.add_event_detect(sensor, GPIO.RISING, bouncetime=150)
    elif controleBounce > 40 and controleBounce <= 50:
        GPIO.add_event_detect(sensor, GPIO.RISING, bouncetime=100)

def calculoVelocidade():
    global contador, tempoStart, tempoUmaVolta, rpm, t, ligado, controleThread
    if controleThread != 2:
        controleThread += 1
        t = threading.Timer(1, calculoVelocidade)
        t.start()
    if ligado == 1:
        print('Threads correntes em execução: ', threading.active_count())
        while contador != numeroDentes:
                if GPIO.event_detected(sensor):
                    contador += 1
                if (contador == numeroDentes):
                    tempoUmaVolta = time.time() - tempoStart
                    tempoStart = time.time()
                    contador = 0
                    frequencia = 1 / tempoUmaVolta
                    rpm = frequencia * 60
                if not ligado:
                    rpm = 0
                labelVelocidade['text'] = str(round(rpm,2)) + ' RPM'
    
    
def callbackBotaoLigaHorario():
    global setpoint, tempoSubida, ph, sentidoAtual, ligado, controleThread
    setpoint = int(e1.get())
    if validaEntrada(setpoint):
        setpoint = converteEntrada(setpoint)
        botao1.config(state="disabled")
        botao2.config(state="normal")
        botao3.config(state="disabled")
        ligado = 1
        sentidoAtual = 'horario'
        tempoSubida = int(e2.get())
        fracaoTempo = int((setpoint/tempoSubida))
        rampaSubida(setpoint, fracaoTempo, ph)
        if controleThread == 0:
            controleThread += 1
            t = threading.Timer(1, calculoVelocidade)
            t.start()
    else:
        messagebox.showerror("Error", "Informe um valor entre 20 e 50 RPMs")

def callbackBotaoLigaAntiHorario():
    global setpoint, tempoSubida, pa, sentidoAtual, ligado, controleThread
    setpoint = int(e1.get())
    if validaEntrada(setpoint):
        setpoint = converteEntrada(setpoint)
        botao1.config(state="disabled")
        botao2.config(state="normal")
        botao3.config(state="disabled")
        ligado = 1
        sentidoAtual = 'antihorario'
        tempoSubida = int(e2.get())
        fracaoTempo = int((setpoint/tempoSubida))
        rampaSubida(setpoint, fracaoTempo, pa)
        if controleThread == 0:
            controleThread += 1
            t = threading.Timer(1, calculoVelocidade)
            t.start()
    else:
        messagebox.showerror("Error", "Informe um valor entre 20 e 50 RPMs")

def rampaSubida(setpoint, fracaoTempo, p):
    for i in range (0, setpoint, fracaoTempo):
        p.ChangeDutyCycle(i)
        time.sleep(1)
        if (i+fracaoTempo >= setpoint):
            p.ChangeDutyCycle(setpoint)
            time.sleep(1)
    ajustaBounce()

def callbackBotaoDesliga():
    global setpoint, tempoSubida, ph, pa, sentidoAtual, sensor, t, t2
    botao1.config(state="normal")
    botao2.config(state="disabled")
    botao3.config(state="normal")
    setpoint = int(e1.get())
    tempoSubida = int(e2.get())
    fracaoTempo = int((setpoint/tempoSubida))* -1
    if(sentidoAtual == 'horario' and ligado == 1):
        rampaDescida(setpoint, fracaoTempo, ph)
    elif(sentidoAtual == 'antihorario' and ligado == 1):
        rampaDescida(setpoint, fracaoTempo, pa)
    GPIO.remove_event_detect(sensor)

def rampaDescida(setpoint, fracaoTempo, p):
    global ligado
    ligado = 0
    for i in range (setpoint, 0, fracaoTempo):
        p.ChangeDutyCycle(i)
        time.sleep(1)
        if (i+fracaoTempo <= 0):
            p.ChangeDutyCycle(0)
            time.sleep(1)
    GPIO.cleanup()
    setup()

# Thread para envio de e-mail
t2 = threading.Timer(intervaloEmail, enviaEmail)
t2.start()

### Desenhando a tela
Label(master, text="Setpoint: ").grid(row=1, pady=4)
e1 = Entry(master)
e1.grid(row=1, column=3, pady=4)

Label(master, text="Tempo de subida: ").grid(row=2, pady=4)
e2 = Entry(master)
e2.grid(row=2, column=3, pady=4)

botao1 = Button(master, text="Anti horario", command=callbackBotaoLigaHorario, height=1, width=10, compound=LEFT)
botao1.place(x = 20, y = 60)

botao2 = Button(master, text="OFF", state="disabled", command=callbackBotaoDesliga, height=1, width=10, compound=LEFT)
botao2.place(x = 150, y = 60)

botao3 = Button(master, text="Horario", command=callbackBotaoLigaAntiHorario, height=1, width=10, compound=LEFT)
botao3.place(x = 280, y = 60)

imgMotor = ImageTk.PhotoImage(file="motor.jpg")
labelMotor = Label(master, image = imgMotor, bg='white')
labelMotor.images = imgMotor
labelMotor.place(x=70, y=120)

labelVelocidade = Label(master, text="O RPM", bg=('blue'), fg=('white'))
labelVelocidade.place(x=175, y=370)

master.protocol("WM_DELETE_WINDOW", on_closing)
mainloop()
