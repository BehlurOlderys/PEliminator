/*
 * main_loop.h
 *
 *  Created on: 28 kwi 2022
 *      Author: Florek
 */

#ifndef MAIN_LOOP_H_
#define MAIN_LOOP_H_


#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

struct main_params{
  TaskHandle_t handle_a;
  TaskHandle_t handle_b;
};

void half_a_processor(void *arg);
void half_b_processor(void *arg);

void main_loop(void *arg);

#endif /* MAIN_LOOP_H_ */
