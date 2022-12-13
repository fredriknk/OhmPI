#include <ESP8266WiFi.h> // Import ESP8266 WiFi library
#include <PubSubClient.h>// Import PubSubClient library to initialize MQTT protocol
#include <Adafruit_MCP23X17.h>

// Update these with values suitable for your network.

const char* ssid = "raspi-webgui";//use your ssid
const char* password = "ChangeMe";//use your password
const char* mqtt_server = "ohmpy.umons.ac.be";
const char* mqtt_user = "mqtt_user";
const char* mqtt_password = "mqtt_password";
const float conversion_factor = 0.01289; /* use 1MOhm resistor on pin A0 for a max voltage of 13.2V */
const char* cmd_on = "On";
const char* cmd_off = "Off";
const int battery_check_interval = 300000;
const float min_voltage = 11.5;

WiFiClient espClient;
PubSubClient client(espClient);
Adafruit_MCP23X17 mcp;

#define MSG_BUFFER_SIZE  (50)
#define analogPin A0 /* ESP8266 Analog Pin ADC0 = A0 */
#define CHARGER_PIN 0
#define LOAD_PIN 1
#define D1 5
#define D2 4

unsigned long lastMsg = 0;
char msg[MSG_BUFFER_SIZE];
int adcValue = 0;  /* Variable to store Output of ADC */
float voltage = 0.0;
int use_mcp = 0;
int power_saving_mode = 0;
unsigned long lastBatteryCheck = 0;

void setup_mcp() {
  if (!mcp.begin_I2C()) {
    Serial.println("No I2C!");
    while (1);
  }
  mcp.pinMode(CHARGER_PIN, OUTPUT);
  mcp.pinMode(LOAD_PIN, OUTPUT);  
}

void setup_no_mcp() {
  pinMode(D1, OUTPUT);
  pinMode(D2, OUTPUT);
}

void setup_wifi() {

  delay(10);
  // We start by connecting to a WiFi network
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);

  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  randomSeed(micros());

  Serial.println("");
  Serial.println("WiFi connected");
  Serial.println("IP address: ");
  Serial.println(WiFi.localIP());
}

// Check for Message received on define topic for MQTT Broker
void callback(char* topic, byte* payload, unsigned int length) {
  char cmd[length+1];
  memcpy(cmd, payload, length);
  cmd[length] = '\0';
 
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  Serial.print(cmd);
  Serial.println();

  
  // Switch relays according to commands (pay attention to the wiring of the relay card
  
  if (length == 2 && memcmp(payload, "On", 2) == 0) {
    digitalWrite(LED_BUILTIN, LOW); // Turn the D1 LED on, the load off then the charger on
    
    if( use_mcp == 1 ){
      mcp.digitalWrite(LOAD_PIN, LOW);
      delay(250);
      mcp.digitalWrite(CHARGER_PIN, HIGH);
    }
    else {
      digitalWrite(D2, LOW);
      delay(250);
      digitalWrite(D1, HIGH);
    }
    
    
  } else if (length == 3 && memcmp(payload, "Off", 3) == 0) {

    if( use_mcp == 1 ){
      mcp.digitalWrite(LED_BUILTIN, HIGH);  // Turn the D1 LED off, the charger off then the load on
      mcp.digitalWrite(CHARGER_PIN, LOW);
      delay(250);
      mcp.digitalWrite(LOAD_PIN, HIGH);
    }
    else{
      digitalWrite(LED_BUILTIN, HIGH);  // Turn the D1 LED off, the charger off then the load on
      digitalWrite(D1, LOW);
      delay(250);
      digitalWrite(D2, HIGH);
    } 
    
  } else if (length == 12 && memcmp(payload, "Read voltage", 12) == 0) {
    unsigned long now = millis();
    if (now - lastMsg > 2000) {
      lastMsg = now;

      read_voltage(); 
      
      /* Print the output in the Serial Monitor */
      Serial.print("ADC Value = ");
      Serial.print(voltage);
      Serial.println(" V");
      snprintf (msg, MSG_BUFFER_SIZE, "battery voltage: %d.%02d V", (int)voltage, (int)(voltage*100)%100);
      client.publish("batteries/level", msg);
      delay(500);
  }
  }
  
}

void read_voltage(){
  adcValue = analogRead(analogPin); /* Read the Analog Input value */
  voltage = adcValue*conversion_factor;
}

void reconnect() {
  // Loop until we're reconnected
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    // Create a random client ID
    String clientId = "ESP8266Client-";
    clientId += String(random(0xffff), HEX);
    // Attempt to connect
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("connected");
      // Once connected, publish an announcement...
      client.publish("batteries/level", "ready");
      // ... and resubscribe
      client.subscribe("batteries/commands");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      // Wait 5 seconds before retrying
      delay(5000);
    }
  }
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);     // Initialize the BUILTIN_LED pin as an output
  Serial.begin(115200);
  setup_wifi();
  client.setServer(mqtt_server, 1883);
  client.setCallback(callback);
  if( use_mcp == 1 ){
    setup_mcp();
  }
  else {
    setup_no_mcp();
  }
  
}

void loop() {

  if (!client.connected()) {
    reconnect();
  }
  client.loop();
  
  unsigned long now = millis();
  
  if(now - lastBatteryCheck > battery_check_interval){
    lastBatteryCheck = now;
    read_voltage();

    if(voltage < min_voltage){
      // Send the command to the MQTT broker to shutdown the Raspberry
      Serial.println("Sending signal to shut down the PI");
    }
    
  }


  // Ajouter if(power_saving_mode == 1){ sleep(XXX); }

  
}
