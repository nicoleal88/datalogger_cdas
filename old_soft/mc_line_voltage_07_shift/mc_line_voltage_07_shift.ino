/*

 */
 
#define arrayLength 64

#include <TimerOne.h>

const unsigned char PS_16 = (1 << ADPS2);
const unsigned char PS_32 = (1 << ADPS2) | (1 << ADPS0);
const unsigned char PS_64 = (1 << ADPS2) | (1 << ADPS1);
const unsigned char PS_128 = (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);

int sensorPin_vR = A0;      // select the input pin for the IR LED signal
int sensorPin_vS = A1;
int sensorPin_vT = A2;
int sensorPin_iR = A3;      // select the input pin for the IR LED signal
int sensorPin_iS = A4;
int sensorPin_iT = A5;
int sensorPin_iN = A6;      // select the input pin for the IR LED signal

int ledPin = 13;              // select the pin for the LED
int sensorValue_vR = 0;       // variable to store the value coming from the sensor
int sensorValue_vS = 0;
int sensorValue_vT = 0;
int sensorValue_iR = 0;       // variable to store the value coming from the sensor
int sensorValue_iS = 0;
int sensorValue_iT = 0;
int sensorValue_iN = 0;

int prevValue_vR = 0;          // variable to store the previous value coming from the sensor
int prevValue_vS = 0;
int prevValue_vT = 0;
int prevValue_iR = 0;          // variable to store the previous value coming from the sensor
int prevValue_iS = 0;
int prevValue_iT = 0;
int prevValue_iN = 0;

uint8_t arrayOfValues[10];

int ledState = LOW;       // El LED empieza apagado
volatile unsigned long Count = 1; // time counter
int Tflag = LOW;           // ready-to-transfer flag

float nZ = 0;
float nZLast = 0;
float deltaN;

volatile int index = 0;

int array_vR[arrayLength];
int array_vS[arrayLength];
int array_vT[arrayLength];
int array_iR[arrayLength];
int array_iS[arrayLength];
int array_iT[arrayLength];
int array_iN[arrayLength];

int t = 20000 / 40;  //20000 = Period in us 

void setup() {
  
  // set up the ADC
  ADCSRA &= ~PS_128;  // remove bits set by Arduino library

  // you can choose a prescaler from above.
  // PS_16, PS_32, PS_64 or PS_128
  ADCSRA |= PS_32;    // set our own prescaler to 64 
  
  // declare the ledPin as an OUTPUT:
  pinMode(ledPin, OUTPUT);
  Timer1.initialize(t);                      // Dispara cada t us
  Timer1.attachInterrupt(ISR_Blink);   // Activa la interrupcion y la asocia a ISR_Blink
  Serial.begin(115200);
}

void ISR_Blink()
{
  index = (Count-1); // % arrayLength;
  
  prevValue_vR = sensorValue_vR;
  prevValue_vS = sensorValue_vS;
  prevValue_vT = sensorValue_vT;
  prevValue_iR = sensorValue_iR;
  prevValue_iS = sensorValue_iS;
  prevValue_iT = sensorValue_iT;
  prevValue_iN = sensorValue_iN;

  sensorValue_vR = analogRead(sensorPin_vR);
  sensorValue_vS = analogRead(sensorPin_vS);
  sensorValue_vT = analogRead(sensorPin_vT);
  sensorValue_iR = analogRead(sensorPin_iR);
  sensorValue_iS = analogRead(sensorPin_iS);
  sensorValue_iT = analogRead(sensorPin_iT);
  sensorValue_iN = analogRead(sensorPin_iN);

  array_vR[index] = sensorValue_vR;
  array_vS[index] = sensorValue_vS;
  array_vT[index] = sensorValue_vT;
  array_iR[index] = sensorValue_iR;
  array_iS[index] = sensorValue_iS;
  array_iT[index] = sensorValue_iT;
  array_iN[index] = sensorValue_iN;

  //Send data
  if (Count >= arrayLength){
      //long time = micros();
      packageGen(findPP(array_vR, arrayLength),findPP(array_vS, arrayLength),findPP(array_vT, arrayLength),findPP(array_iR, arrayLength),findPP(array_iS, arrayLength),findPP(array_iT, arrayLength),findPP(array_iN, arrayLength),findnZ(array_vR, arrayLength));
      int bytes = Serial.write(arrayOfValues, sizeof(arrayOfValues));
      //long time2 = micros();
      //Serial.println(time2 - time);
      Serial.println();
      Tflag = !Tflag;
      Count = 0;
    }
    Count++;
  }

void loop() {
  digitalWrite(ledPin, Tflag);
}

int findPP(int Array[], int n){
  int maxValue = Array[0];
  int minValue = Array[0];
  for(int i = 0; i < n; i++){
    int value = Array[i];
    if (value > maxValue){
      maxValue = value;
    }
    else if (value < minValue){
      minValue = value;
    }
  }
  return maxValue - minValue;
}

int findnZ(int Array[], int n){
  float nZs[3];
  int nZindex = 0;
  for(int i = 0; i < n-1; i++){
    int valueA = Array[i];
    int valueB = Array[i+1];
    if ((valueA < 512 && valueB >= 512)||(valueA >= 512 && valueB < 512)){
      nZ = (i+1.0) - ((valueB - 512.0)/(valueB-valueA));
      nZs[nZindex] = nZ;
      nZindex++;
    }
  }
  deltaN = nZs[2]-nZs[0];  //Puede ser positivo o negativo
  nZindex = 0;
  return int((4608.0-(deltaN*102.4)));
/*
deltaN: Tiempo entre dos cruces por cero, cada unidad equivale a 500us
El valor de deltaN puede variar entre 35 (55Hz), 40(50Hz, valor nominal) y 45 (45Hz)
Para adaptar la señal al rango 0-1023 se usan las dos constantes:
5*a = 512 => a = 102.4
b-40*a = 512 => b = 4608
*/
}    

void packageGen (int a, int b, int c, int d, int e, int f, int g, int h){
  arrayOfValues[0] = getOffset(a);
  arrayOfValues[1] = getOffset(b);
  arrayOfValues[2] = getOffset(c);
  arrayOfValues[3] = getOffset(d);
  arrayOfValues[4] = getOffset(e);
  arrayOfValues[5] = getOffset(f);
  arrayOfValues[6] = getOffset(g);
  arrayOfValues[7] = getOffset(h);
  uint16_t indexCode = getIndexCode(a,b,c,d,e,f,g,h);
  arrayOfValues[8] = (uint8_t)(indexCode);
  arrayOfValues[9] = (uint8_t)(indexCode >> 8);
  return;
}

uint8_t getOffset(int thisValue) {
  uint8_t offsetCode = (uint8_t)(thisValue % 256);
  if (offsetCode == 10){    // This loop will fix the error that rises when
    offsetCode++;           // New Line character is sent.
  }
  return offsetCode;
}

uint16_t getIndex(int thisValue) {
  uint16_t indexCode = (uint16_t)(thisValue / 256);
  return indexCode;
}

uint16_t getIndexCode(int this_a, int this_b, int this_c, int this_d, int this_e, int this_f, int this_g, int this_h) {
  uint16_t returnIndex = 0;
  uint16_t tmp = 0;
  returnIndex = getIndex(this_a);
  tmp = getIndex(this_b) << 2;
  returnIndex = returnIndex | tmp;
  tmp = getIndex(this_c) << 4;
  returnIndex = returnIndex | tmp;
  tmp = getIndex(this_d) << 6;
  returnIndex = returnIndex | tmp;
  tmp = getIndex(this_e) << 8;
  returnIndex = returnIndex | tmp;
  tmp = getIndex(this_f) << 10;
  returnIndex = returnIndex | tmp;
  tmp = getIndex(this_g) << 12;
  returnIndex = returnIndex | tmp;
  tmp = getIndex(this_h) << 14;
  returnIndex = returnIndex | tmp;
  return returnIndex;
}
