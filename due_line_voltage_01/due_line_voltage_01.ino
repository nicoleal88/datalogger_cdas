/*
Datalogger for CDAS with Arduino DUE

  -----------------------------------------------------------------------------------------------------------------------
--| A0L | A1L | A2L | A3L | A4L | A5L | A6L | DeltaN | A0-3H | A4-6+DNH | A7L | A8L | A9L | A10L | A7-10H | A11L | A11H |----  17 bytes total
  -----------------------------------------------------------------------------------------------------------------------

A0L    : Is the lower byte of A0 (10 bits) ADC output:                    -> 8bits
A1L    : Is the lower byte of A1 (10 bits) ADC output:                    -> 8bits
...
A7L    : Is the lower byte of A7 (10 bits) ADC output:                    -> 8bits
A0-3H  : Is the remaining bits (2 bits) of ADC output of A0, A1, A2, A3   -> 8bits

         -----------------------------
         | A3_H | A2_H | A1_H | A0_H |    : 8 bits total inside A0-3H
         -----------------------------

A4-6+DNH : Is the remaining bits (2 bits) of ADC output of A4, A5, A6 and DeltaN -> 8bits

         ---------------------------------
         | DeltaN_H | A6_H | A5_H | A4_H |    : 8 bits total inside A4-6+DNH
         ---------------------------------

A7L    : Is the lower byte of A8 (10 bits) ADC output:                    -> 8bits
...
A10L   : Is the lower byte of A10 (10 bits) ADC output:                   -> 8bits
A7-10H : Is the remaining bits (2 bits) of ADC output of A7, A8, A9, A10  -> 8bits

         -------------------------------
         | A10_H | A9_H | A8_H | A7_H |    : 8 bits total inside A7-10H
         -------------------------------
A11H   : Is the upper nibble of A11 ADC input
A11L   : Is the lower nibble of A11 ADC input

NOTE : Be carefull with possible data type overflow in processData method.
       When DC measuring, all data are added (arrayLength) in an unsigned
       int variable (0 - 65535). As ADC data is 10-bit size, it may overflow
       addition before dividing by the arrayLength.
*/

#define arrayLength 64

#include <DueTimer.h>

int sensorPin_A0  = A0;     // Analog pins : 11 inputs
int sensorPin_A1  = A1;
int sensorPin_A2  = A2;
int sensorPin_A3  = A3;
int sensorPin_A4  = A4;
int sensorPin_A5  = A5;
int sensorPin_A6  = A6;
int sensorPin_A7  = A7;
int sensorPin_A8  = A8;
int sensorPin_A9  = A9;
int sensorPin_A10 = A10;
int sensorPin_A11 = A11;

int ledPin = 13;            // select the pin for the LED

uint8_t arrayOfValues[17];  // this array is transmitted after data processing

int Tflag = LOW;            // ready-to-transfer flag

volatile int my_index = 0;  // this index controls bank writting and Tflag

volatile int array_A0_bank0[arrayLength];  // bank 0
volatile int array_A1_bank0[arrayLength];
volatile int array_A2_bank0[arrayLength];
volatile int array_A3_bank0[arrayLength];
volatile int array_A4_bank0[arrayLength];
volatile int array_A5_bank0[arrayLength];
volatile int array_A6_bank0[arrayLength];
volatile int array_A7_bank0[arrayLength];
volatile int array_A8_bank0[arrayLength];
volatile int array_A9_bank0[arrayLength];
volatile int array_A10_bank0[arrayLength];
volatile int array_A11_bank0[arrayLength];

volatile int array_A0_bank1[arrayLength];  // bank 1
volatile int array_A1_bank1[arrayLength];
volatile int array_A2_bank1[arrayLength];
volatile int array_A3_bank1[arrayLength];
volatile int array_A4_bank1[arrayLength];
volatile int array_A5_bank1[arrayLength];
volatile int array_A6_bank1[arrayLength];
volatile int array_A7_bank1[arrayLength];
volatile int array_A8_bank1[arrayLength];
volatile int array_A9_bank1[arrayLength];
volatile int array_A10_bank1[arrayLength];
volatile int array_A11_bank1[arrayLength];

volatile int * A0_bank = &array_A0_bank0[0];    // A0 bank pointer. By default on bank 0
volatile int * A1_bank = &array_A1_bank0[0];    // A1 bank pointer. By default on bank 0
volatile int * A2_bank = &array_A2_bank0[0];    // A2 bank pointer. By default on bank 0
volatile int * A3_bank = &array_A3_bank0[0];    // A3 bank pointer. By default on bank 0
volatile int * A4_bank = &array_A4_bank0[0];    // A4 bank pointer. By default on bank 0
volatile int * A5_bank = &array_A5_bank0[0];    // A5 bank pointer. By default on bank 0
volatile int * A6_bank = &array_A6_bank0[0];    // A6 bank pointer. By default on bank 0
volatile int * A7_bank = &array_A7_bank0[0];    // A7 bank pointer. By default on bank 0
volatile int * A8_bank = &array_A8_bank0[0];    // A8 bank pointer. By default on bank 0
volatile int * A9_bank = &array_A9_bank0[0];    // A9 bank pointer. By default on bank 0
volatile int * A10_bank = &array_A10_bank0[0];  // A10 bank pointer. By default on bank 0
volatile int * A11_bank = &array_A11_bank0[0];  // A11 bank pointer. By default on bank 0

volatile boolean dataType[12] =  {HIGH,         // AC: vR - UPS input
                                  HIGH,         // AC  vS - UPS input
                                  HIGH,         // AC: vT - UPS input
                                  HIGH,         // AC: iR - UPS input
                                  HIGH,         // AC: iS - UPS input
                                  HIGH,         // AC: iT - UPS input
                                  HIGH,         // AC: iN - UPS input
                                  HIGH,         // AC: vO - UPS output
                                  LOW,          // DC: Temp - CDAS Temperature from LM35
                                  LOW,          // DC: None
                                  LOW,          // DC: None
                                  LOW};         // DC: None

volatile int bankFlag = LOW;                    // LOW means bank0, HIGH means bank1
volatile int * ptrsVector[12];                  // Signals pointers vector
volatile unsigned int processedData[12];        // If AC -> Peak to peak data is stored
                                                // If DC -> Mean value is stored
volatile int deltaNScaled = 0;                  // Delta N scaled
int t = 20000 / 40;                             // 20000 = Period in us  -> 20ms

void setup() {
  pinMode(ledPin, OUTPUT);
  Timer3.attachInterrupt(ISR_Blink).start(t);
  Serial.begin(115200);
}

void ISR_Blink()
{
  //Measures
  *(A0_bank+my_index) = analogRead(sensorPin_A0);
  *(A1_bank+my_index) = analogRead(sensorPin_A1);
  *(A2_bank+my_index) = analogRead(sensorPin_A2);
  *(A3_bank+my_index) = analogRead(sensorPin_A3);
  *(A4_bank+my_index) = analogRead(sensorPin_A4);
  *(A5_bank+my_index) = analogRead(sensorPin_A5);
  *(A6_bank+my_index) = analogRead(sensorPin_A6);
  *(A7_bank+my_index) = analogRead(sensorPin_A7);
  *(A8_bank+my_index) = analogRead(sensorPin_A8);
  *(A9_bank+my_index) = analogRead(sensorPin_A9);
  *(A10_bank+my_index) = analogRead(sensorPin_A10);
  *(A11_bank+my_index) = analogRead(sensorPin_A11);
  my_index++;

  //Prepare to send data
  if (my_index >= arrayLength){
    ptrsVector[0] = A0_bank;     // Pointers vector that is used by findPPo function
    ptrsVector[1] = A1_bank;
    ptrsVector[2] = A2_bank;
    ptrsVector[3] = A3_bank;
    ptrsVector[4] = A4_bank;
    ptrsVector[5] = A5_bank;
    ptrsVector[6] = A6_bank;
    ptrsVector[7] = A7_bank;
    ptrsVector[8] = A8_bank;
    ptrsVector[9] = A9_bank;
    ptrsVector[10] = A10_bank;
    ptrsVector[11] = A11_bank;
    if (bankFlag == LOW){
      A0_bank = &array_A0_bank1[0];
      A1_bank = &array_A1_bank1[0];
      A2_bank = &array_A2_bank1[0];
      A3_bank = &array_A3_bank1[0];
      A4_bank = &array_A4_bank1[0];
      A5_bank = &array_A5_bank1[0];
      A6_bank = &array_A6_bank1[0];
      A7_bank = &array_A7_bank1[0];
      A8_bank = &array_A8_bank1[0];
      A9_bank = &array_A9_bank1[0];
      A10_bank = &array_A10_bank1[0];
      A11_bank = &array_A11_bank1[0];
    } else {
      A0_bank = &array_A0_bank0[0];
      A1_bank = &array_A1_bank0[0];
      A2_bank = &array_A2_bank0[0];
      A3_bank = &array_A3_bank0[0];
      A4_bank = &array_A4_bank0[0];
      A5_bank = &array_A5_bank0[0];
      A6_bank = &array_A6_bank0[0];
      A7_bank = &array_A7_bank0[0];
      A8_bank = &array_A8_bank0[0];
      A9_bank = &array_A9_bank0[0];
      A10_bank = &array_A10_bank0[0];
      A11_bank = &array_A11_bank0[0];
    }
    Tflag = HIGH;
    bankFlag = !bankFlag;
    my_index = 0;
  }
}

void loop() {
  if (Tflag == HIGH){
    digitalWrite(ledPin, Tflag);
    dataProcessing(arrayLength);
    deltaNScaled = findnZo(arrayLength);
    packageGenO();
    int bytes = Serial.write(arrayOfValues, sizeof(arrayOfValues));
    Serial.println();
    Tflag = LOW;
  }
  digitalWrite(ledPin, Tflag);
}

void dataProcessing(int n){
  int maxArray[12];
  int minArray[12];
  int thisData[12] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  for (int i = 0; i < 12; i++){       // Initializing the maximum and minimum arrays
    if (dataType[i] == HIGH){         // If dataType is HIGH means AC input
      maxArray[i] = *(ptrsVector[i]);
      minArray[i] = *(ptrsVector[i]);
    } else {
      
    }
  }
  for (int i = 0; i < 12; i++){
    for (int j = 0; j < n; j++){
      int value = *(ptrsVector[i]+j);
      if (dataType[i] == HIGH){       // If dataType is HIGH means AC input
        if (value > maxArray[i]){     // If AC then max and min values are updated
          maxArray[i] = value;
        }
        else if (value < minArray[i]){
          minArray[i] = value;
        }
      } else {                        // If dataType is LOW means DC input
        processedData[i] += value;    // All values are added to be meant at the end
      }                               // BE CAREFULL WITH DATA TYPE OVERFLOW!!!!!
    }
    if (dataType[i] == HIGH){
      processedData[i] = maxArray[i] - minArray[i];
    } else {
      processedData[i] = processedData[i] / arrayLength;
    }
  }
  return;
}

int findnZo(int n){                   // Frequency is measured using A0 port
  float nZs[3] = { 0.0, 0.0, 0.0 };
  float nZ = 0.0;
  int nZindex = 0;
  for (int i = 0; i < n-1; i++){
    int valueA = *(ptrsVector[0]+i);
    int valueB = *(ptrsVector[0]+i+1);
    if ((valueA < 512 && valueB >= 512)||(valueA >= 512 && valueB < 512)){
      nZ = (i+1.0) - ((valueB - 512.0)/(valueB-valueA));
      nZs[nZindex] = nZ;
      nZindex++;
    }
    if (nZindex == 3){
      break;
    }
  }
  float deltaN = nZs[2] - nZs[0];  // Puede ser positivo o negativo <-- ??
  nZindex = 0;
  return int((4608.0-(deltaN*102.4)));
  /* deltaN calculation: This value is transformed to use the full 10bit scale
                         The value may be 35 (55Hz), 40(50Hz, nominal value) or 45 (45Hz).
                         0    -> 35 (55Hz)
                         512  -> 40 (50Hz)
                         1023 -> 45 (45Hz)
                         So:
                              5*a = 512    => a = 102.4
                              b-40*a = 512 => b = 4608
  */
}

void packageGenO(){
  arrayOfValues[0]  = getOffset(processedData[0]);
  arrayOfValues[1]  = getOffset(processedData[1]);
  arrayOfValues[2]  = getOffset(processedData[2]);
  arrayOfValues[3]  = getOffset(processedData[3]);
  arrayOfValues[4]  = getOffset(processedData[4]);
  arrayOfValues[5]  = getOffset(processedData[5]);
  arrayOfValues[6]  = getOffset(processedData[6]);
  arrayOfValues[7]  = getOffset(deltaNScaled);
  uint16_t indexCode  = getIndexCode(processedData[0], 
                                     processedData[1], 
                                     processedData[2], 
                                     processedData[3], 
                                     processedData[4], 
                                     processedData[5], 
                                     processedData[6], 
                                     deltaNScaled);
  arrayOfValues[8] = (uint8_t)(indexCode);
  arrayOfValues[9] = (uint8_t)(indexCode >> 8);
  arrayOfValues[10] = getOffset(processedData[7]);
  arrayOfValues[11] = getOffset(processedData[8]);
  arrayOfValues[12] = getOffset(processedData[9]);
  arrayOfValues[13] = getOffset(processedData[10]);
  indexCode         = getIndexCode(processedData[7], 
                                   processedData[8], 
                                   processedData[9], 
                                   processedData[10], 
                                   (uint8_t)(0),         // The upper nibble is discarded
                                   (uint8_t)(0), 
                                   (uint8_t)(0), 
                                   (uint8_t)(0));
  arrayOfValues[14] = (uint8_t)(indexCode);
  arrayOfValues[15] = (uint8_t)(processedData[11]);       // A11 is not indexed.
  arrayOfValues[16] = (uint8_t)(processedData[11] >> 8);
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
