/*
 
Datalogger for CDAS with Arduino DUE

*/

#define arrayLength 64

/*
 * #include <TimerOne.h> 
 * The DUE has a different microcontroller, an Atmel ATSAM3X8E, 
 * it does not have the same timers you can find in Arduino UNO's ATmega328P.
 */

#include <DueTimer.h>

int sensorPin_vR = A0;      // select the input pin for the IR LED signal
int sensorPin_vS = A1;
int sensorPin_vT = A2;
int sensorPin_iR = A3;      // select the input pin for the IR LED signal
int sensorPin_iS = A4;
int sensorPin_iT = A5;
//int sensorPin_iN = A6;      // select the input pin for the IR LED signal

int ledPin = 13;              // select the pin for the LED

uint8_t arrayOfValues[10];

//volatile unsigned long Count = 1; // time counter
int Tflag = LOW;           // ready-to-transfer flag

volatile int my_index = 0;

volatile int array_vR_bank0[arrayLength];  // bank 0
volatile int array_vS_bank0[arrayLength];
volatile int array_vT_bank0[arrayLength];
volatile int array_iR_bank0[arrayLength];
volatile int array_iS_bank0[arrayLength];
volatile int array_iT_bank0[arrayLength];
//volatile int array_iN_bank0[arrayLength];

volatile int array_vR_bank1[arrayLength];  // bank 1
volatile int array_vS_bank1[arrayLength];
volatile int array_vT_bank1[arrayLength];
volatile int array_iR_bank1[arrayLength];
volatile int array_iS_bank1[arrayLength];
volatile int array_iT_bank1[arrayLength];
//volatile int array_iN_bank1[arrayLength];

volatile int * vR_bank = &array_vR_bank0[0];          // vR bank pointer
volatile int * vS_bank = &array_vS_bank0[0];          // vS bank pointer
volatile int * vT_bank = &array_vT_bank0[0];          // vT bank pointer
volatile int * iR_bank = &array_iR_bank0[0];          // iR bank pointer
volatile int * iS_bank = &array_iS_bank0[0];          // iS bank pointer
volatile int * iT_bank = &array_iT_bank0[0];          // iT bank pointer
//volatile int * iN_bank = &array_iN_bank0[0];          // iN bank pointer
volatile int bankFlag = LOW;     // LOW means bank0, HIGH means bank1

volatile int * ptrsVector[6];    // Signals pointers vector
volatile int PPs[6];             // Peak to peak vector
volatile int deltaNScaled = 0;   // Delta N scaled

int t = 20000 / 40;  //20000 = Period in us 

void setup() {

  // declare the ledPin as an OUTPUT:
  pinMode(ledPin, OUTPUT);

  Timer3.attachInterrupt(ISR_Blink).start(t);

  Serial.begin(115200);
}

void ISR_Blink()
{
  //Measures
  *(vR_bank+my_index) = analogRead(sensorPin_vR);
  *(vS_bank+my_index) = analogRead(sensorPin_vS);
  *(vT_bank+my_index) = analogRead(sensorPin_vT);
  *(iR_bank+my_index) = analogRead(sensorPin_iR);
  *(iS_bank+my_index) = analogRead(sensorPin_iS);
  *(iT_bank+my_index) = analogRead(sensorPin_iT);
//  *(iN_bank+my_index) = analogRead(sensorPin_iN);
  my_index++;

  //Prepare to send data
  if (my_index >= arrayLength){
   ptrsVector[0] = vR_bank;     // Pointers vector that is used by findPPo function
   ptrsVector[1] = vS_bank;
   ptrsVector[2] = vT_bank;
   ptrsVector[3] = iR_bank;
   ptrsVector[4] = iS_bank;
   ptrsVector[5] = iT_bank;
//   ptrsVector[6] = iN_bank;
   if (bankFlag == LOW){
     vR_bank = &array_vR_bank1[0];
     vS_bank = &array_vS_bank1[0];
     vT_bank = &array_vT_bank1[0];
     iR_bank = &array_iR_bank1[0];
     iS_bank = &array_iS_bank1[0];
     iT_bank = &array_iT_bank1[0];
//     iN_bank = &array_iN_bank1[0];
   } else {
     vR_bank = &array_vR_bank0[0];
     vS_bank = &array_vS_bank0[0];
     vT_bank = &array_vT_bank0[0];
     iR_bank = &array_iR_bank0[0];
     iS_bank = &array_iS_bank0[0];
     iT_bank = &array_iT_bank0[0];
//     iN_bank = &array_iN_bank0[0];
   }
   Tflag = HIGH;
   bankFlag = !bankFlag;
   my_index = 0;
  }
}

void loop() {
  if (Tflag == HIGH){
    digitalWrite(ledPin, Tflag);
    findPPo(arrayLength);  // Finds Peak to Peak and stores it in PPs pointer allocation
    deltaNScaled = findnZo(arrayLength);
//    packageGenO();
//    int bytes = Serial.write(arrayOfValues, sizeof(arrayOfValues));
    Serial.print(PPs[0]);
    Serial.print("\t");
    Serial.print(PPs[1]);
    Serial.print("\t");
    Serial.print(PPs[2]);
    Serial.print("\t");
    Serial.print(PPs[3]);
    Serial.print("\t");
    Serial.print(PPs[4]);
    Serial.print("\t");
    Serial.print(PPs[5]);
    Serial.print("\t");
    Serial.print(millis());
    Serial.println("\t");
    Tflag = LOW;
  }
  digitalWrite(ledPin, Tflag);
}

void findPPo(int n){
  int maxArray[6];
  int minArray[6];
  int thisPPs[6] = {0, 0, 0, 0, 0, 0};
  for (int i = 0; i < 6; i++){      // initializing the maximum and minimum arrays
    maxArray[i] = *(ptrsVector[i]);
    minArray[i] = *(ptrsVector[i]);
  }
  for (int i = 0; i < 6; i++){
    for(int j = 0; j < n; j++){
      int value = *(ptrsVector[i]+j);
      if (value > maxArray[i]){
        maxArray[i] = value;
      }
      else if (value < minArray[i]){
        minArray[i] = value;
      }
    }
    PPs[i] = maxArray[i] - minArray[i];
  }
  return;
}

int findnZo(int n){
  float nZs[3]={0.0, 0.0, 0.0};
  float nZ = 0.0;
  int nZindex = 0;
  for(int i = 0; i < n-1; i++){ //El for comienza en 1 porque cuando el cruce se presenta en i=0 aparece un valor errtico
    int valueA = *(ptrsVector[0]+i);
    int valueB = *(ptrsVector[0]+i+1);
 //   int valueA = Array[i];
 //   int valueB = Array[i+1];
    if ((valueA < 512 && valueB >= 512)||(valueA >= 512 && valueB < 512)){
      nZ = (i+1.0) - ((valueB - 512.0)/(valueB-valueA));
      nZs[nZindex] = nZ;
      nZindex++;
    }
    if (nZindex == 3){
      break;
    }
  }
  float deltaN = nZs[2]-nZs[0];  //Puede ser positivo o negativo
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

//void packageGenO(){
//  arrayOfValues[0] = getOffset(PPs[0]);
//  arrayOfValues[1] = getOffset(PPs[1]);
//  arrayOfValues[2] = getOffset(PPs[2]);
//  arrayOfValues[3] = getOffset(PPs[3]);
//  arrayOfValues[4] = getOffset(PPs[4]);
//  arrayOfValues[5] = getOffset(PPs[5]);
//  arrayOfValues[6] = getOffset(PPs[5]);    // N current
//  arrayOfValues[7] = getOffset(deltaNScaled);
//  uint16_t indexCode = getIndexCode(PPs[0],PPs[1],PPs[2],PPs[3],PPs[4],PPs[5],PPs[5],deltaNScaled);
//  arrayOfValues[8] = (uint8_t)(indexCode);
//  arrayOfValues[9] = (uint8_t)(indexCode >> 8);
//  return;
//}
//
//uint8_t getOffset(int thisValue) {
//  uint8_t offsetCode = (uint8_t)(thisValue % 256);
//  if (offsetCode == 10){    // This loop will fix the error that rises when
//    offsetCode++;           // New Line character is sent.
//  }
//  return offsetCode;
//}
//
//uint16_t getIndex(int thisValue) {
//  uint16_t indexCode = (uint16_t)(thisValue / 256);
//  return indexCode;
//}
//
//uint16_t getIndexCode(int this_a, int this_b, int this_c, int this_d, int this_e, int this_f, int this_g, int this_h) {
//  uint16_t returnIndex = 0;
//  uint16_t tmp = 0;
//  returnIndex = getIndex(this_a);
//  tmp = getIndex(this_b) << 2;
//  returnIndex = returnIndex | tmp;
//  tmp = getIndex(this_c) << 4;
//  returnIndex = returnIndex | tmp;
//  tmp = getIndex(this_d) << 6;
//  returnIndex = returnIndex | tmp;
//  tmp = getIndex(this_e) << 8;
//  returnIndex = returnIndex | tmp;
//  tmp = getIndex(this_f) << 10;
//  returnIndex = returnIndex | tmp;
//  tmp = getIndex(this_g) << 12;
//  returnIndex = returnIndex | tmp;
//  tmp = getIndex(this_h) << 14;
//  returnIndex = returnIndex | tmp;
//  return returnIndex;
//}
