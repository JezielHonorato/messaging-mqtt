import os
import tkinter as tk
import paho.mqtt.client as mqtt

from dotenv import load_dotenv

load_dotenv()

# MQTT connection
mqtt_broker = os.getenv("MQTT_BROKER", "test.mosquitto.org")
mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
mqtt_topic = os.getenv("MQTT_TOPIC")

# Interface grafica
root = tk.Tk()
root.title("Cliente MQTT")
root.geometry("320x220")
root.config(bg="#f4f4f9")

checkbox_var = tk.BooleanVar(value=False)

lbl_title = tk.Label(
    root, text="Status do Dispositivo", font=("Helvetica", 14, "bold"), bg="#f4f4f9"
)
lbl_title.pack(pady=10)

chk_status = tk.Checkbutton(
    root,
    text="Dispositivo Ativo",
    variable=checkbox_var,
    font=("Helvetica", 11),
    state="disabled",
    bg="#f4f4f9",
)
chk_status.pack(pady=10)

btn_indicator = tk.Button(
    root,
    text="DESLIGADO",
    bg="#e74c3c",
    fg="white",
    font=("Helvetica", 12, "bold"),
    width=15,
    height=2,
    state="disabled",
)
btn_indicator.pack(pady=10)


def atualizar_interface(estado):
    checkbox_var.set(estado)

    if estado:
        btn_indicator.config(text="LIGADO", bg="#2ecc71")
    else:
        btn_indicator.config(text="DESLIGADO", bg="#e74c3c")


def alternar_interface():
    atualizar_interface(not checkbox_var.get())


def processar_comando(payload):
    comando = payload.strip().upper()

    print(f"[GUI] Processando comando: {comando}")

    if comando == "ON":
        atualizar_interface(True)

    elif comando == "OFF":
        atualizar_interface(False)

    elif comando == "TOGGLE":
        alternar_interface()

    else:
        print(f"[GUI] Comando desconhecido: {comando}")


# callback MQTT
def on_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Conectado ao broker.")
        client.subscribe(mqtt_topic, qos=1)
        print(f"[MQTT] Inscrito no topico: {mqtt_topic}")
    else:
        print(f"[MQTT] Falha na conexao: {reason_code}")


def on_message(client, userdata, msg):
    try:
        payload = msg.payload.decode("utf-8").strip()

        print(f"[MQTT] Mensagem recebida em " f"'{msg.topic}': {payload}")

        root.after(0, processar_comando, payload)

    except UnicodeDecodeError:
        print("[MQTT] A mensagem recebida nao e UTF-8 valido.")


def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    print(f"[MQTT] Desconectado: {reason_code}")


# MQTT cinnection
mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2, client_id="jeziel_tkinter_gui"
)

mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message
mqtt_client.on_disconnect = on_disconnect


def encerrar():
    print("[GUI] Encerrando aplicacao...")

    mqtt_client.disconnect()
    mqtt_client.loop_stop()
    root.destroy()


try:
    mqtt_client.connect(mqtt_broker, mqtt_port, keepalive=60)
    mqtt_client.loop_start()

except Exception as error:
    print(f"[MQTT] Erro de conexao: {error}")

root.protocol("WM_DELETE_WINDOW", encerrar)
root.mainloop()
