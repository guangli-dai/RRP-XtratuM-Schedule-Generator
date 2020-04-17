/*
 * $FILE: partition0.c
 *
 * Fent Innovative Software Solutions
 *
 * $LICENSE:
 * This program is free software; you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation; either version 2 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
 */
#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include <xm.h>
#include <irqs.h>

#define PRINT(...) do { \
 printf("[P%d] ", XM_PARTITION_SELF); \
 printf(__VA_ARGS__); \
} while (0)

volatile xm_s32_t lock;
xm_u64_t wcet_times[6] = {1000, 10000, 50000, 100000, 500000, 1000000};
xm_u64_t wcet_time;
xm_u64_t worst_response;
//xm_u64_t interval_length[6] = {10000, 10000, 1000, 100, 100, 100};
void HwTimerHandler(trapCtxt_t *ctxt)                                       /* XAL trap API */
{
    xmTime_t hw1, hw2, exec, temp_exec;
    xm_u64_t i=0, useless = rand();
    XM_get_time(XM_EXEC_CLOCK, &exec);
    XM_get_time(XM_HW_CLOCK, &hw1);
    //PRINT("Starting a job at %ld.\n", (xm_u32_t) hw1);
    //while(i<wcet_time)
    //        i++;
    while(i < wcet_time)
    {
        XM_get_time(XM_EXEC_CLOCK, &temp_exec);
        i = temp_exec - exec;
    }
    //PRINT("End value of i is %lld.\n", i);
    XM_get_time(XM_HW_CLOCK, &hw2);
    //PRINT("Job ends at %ld.\n", (xm_u32_t) hw2);
    //PRINT("Job takes %lld microseconds.\n", (xm_u64_t)hw2 - (xm_u64_t)hw1);
    if((xm_u64_t)hw2 - (xm_u64_t)hw1 > worst_response || worst_response == 0  )
            worst_response = (xm_u64_t)hw2 - (xm_u64_t)hw1;
    XM_set_timer(XM_HW_CLOCK, hw2 + 79000LL, 0);
    ++lock;
}

void PartitionMain(void)
{
    xmTime_t hwClock, execClock;

    int wcet_counter = 0;
    PRINT("Starting example 001...\n");

#ifdef CONFIG_LEON3FT    
    InstallTrapHandler(XAL_XMEXT_TRAP(XM_VT_EXT_HW_TIMER), HwTimerHandler); /* Install timer handler */
#elif CONFIG_ARM
    InstallIrqHandler(XAL_XMEXT_TRAP(XM_VT_EXT_HW_TIMER), HwTimerHandler); /* Install timer handler */
    HwSti();                                                                /* Enable irqs */
#else
    #error No valid architecture
#endif

    XM_clear_irqmask(0, (1<<XM_VT_EXT_HW_TIMER));                           /* Unmask timer irqs */

    XM_get_time(XM_HW_CLOCK, &hwClock);                                     /* Read hardware clock */
    XM_get_time(XM_EXEC_CLOCK, &execClock);                                 /* Read execution clock */

    for(wcet_counter=0; wcet_counter < 6; wcet_counter ++)
    {
        lock = 0;
        worst_response = 0;
        wcet_time = wcet_times[wcet_counter];
        XM_set_timer(XM_HW_CLOCK, hwClock+79000LL, 0);        /* Set hardware time driven timer */
        while (lock < 100);
        printf("%lld,%lld\n", wcet_time, worst_response);
    }
//#ifdef CONFIG_ARM
//    	__asm__ __volatile__("wfe\n\t":::)
//#endif
//    ;

    PRINT("Halting\n");
    XM_halt_partition(XM_PARTITION_SELF);
}
