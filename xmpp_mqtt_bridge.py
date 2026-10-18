import os
import time
import xmpp
import paho.mqtt.client as mqtt

from dotenv import load_dotenv

load_dotenv()

# XMPP connection
xmpp_jid = os.getenv("XMPP_JID")
xmpp_pasword = os.getenv("XMPP_PASSWORD")
xmpp_resource = os.getenv("XMPP_RESOURCE")
xmpp_receiver = os.getenv("XMPP_RECEIVER")

# MQTT connection
mqtt_broker = os.getenv("MQTT_BROKER", "test.mosquitto.org")
mqtt_port = int(os.getenv("MQTT_PORT", "1883"))
mqtt_topic = os.getenv("MQTT_TOPIC")

mqtt_client = mqtt.Client(
    mqtt.CallbackAPIVersion.VERSION2, client_id="jeziel_xmpp_bridge"
)


def on_mqtt_connect(client, userdata, flags, reason_code, properties):
    if reason_code == 0:
        print("[MQTT] Conectado ao broker.")
    else:
        print(f"[MQTT] Falha na conexao: {reason_code}")


def xmpp_to_mqtt(connection, message):
    """Recebe mensagens XMPP e as encaminha ao MQTT."""

    body = message.getBody()

    if not body:
        return

    sender = str(message.getFrom())
    body = body.strip()

    print(f"[XMPP] Mensagem de {sender}: {body}")

    # Publica o texto recebido no broker MQTT.
    info = mqtt_client.publish(mqtt_topic, payload=body, qos=1)

    # Aguarda a confirmacao da publicacao.
    info.wait_for_publish(timeout=5)

    if info.is_published():
        print(f"[MQTT] Publicado em '{mqtt_topic}': {body}")
        connection.send(
            xmpp.protocol.Message(to=xmpp_receiver, body="mensagem publicada")
        )
    else:
        print("[MQTT] A publicacao ainda nao foi confirmada.")


def main():
    # Conecta ao broker MQTT.
    mqtt_client.on_connect = on_mqtt_connect

    try:
        mqtt_client.connect(mqtt_broker, mqtt_port, keepalive=60)
        mqtt_client.loop_start()
    except Exception as error:
        print(f"[MQTT] Erro de conexao: {error}")
        return

    # Aguarda a conexao MQTT antes de aceitar mensagens XMPP.
    for _ in range(50):
        if mqtt_client.is_connected():
            break
        time.sleep(0.1)

    if not mqtt_client.is_connected():
        print("[MQTT] Nao foi possivel conectar ao broker.")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
        return

    # Conecta ao servidor XMPP.
    jid = xmpp.protocol.JID(xmpp_jid)
    domain = jid.getDomain()

    connection = xmpp.Client(domain, debug=[])

    try:
        if not connection.connect():
            print("[XMPP] Falha ao conectar ao servidor.")
            return

        auth = connection.auth(jid.getNode(), xmpp_pasword, xmpp_resource)

        if not auth:
            print("[XMPP] Falha na autenticacao.")
            return

        connection.RegisterHandler("message", xmpp_to_mqtt)
        connection.sendInitPresence()

        print("[XMPP] Conectado e autenticado.")
        print("[BRIDGE] Aguardando mensagens do Pidgin...")
        connection.send(
            xmpp.protocol.Message(to=xmpp_receiver, body="Conexão bem sucedida")
        )

        while True:
            connection.Process(1)

    except KeyboardInterrupt:
        print("\n[BRIDGE] Encerrando...")
    except Exception as error:
        print(f"[BRIDGE] Erro: {error}")
    finally:
        try:
            connection.disconnect()
        except Exception:
            pass

        mqtt_client.loop_stop()
        mqtt_client.disconnect()


if __name__ == "__main__":
    main()
