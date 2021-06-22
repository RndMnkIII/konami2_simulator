#include <stdio.h>

int main()
{
    __uint8_t hi_bit = (__uint8_t) (1 << (sizeof(__uint8_t) * 8 - 1));
    printf("valor: %0X\n", hi_bit);

    __uint16_t hi_bit2 = (__uint16_t) (1 << (sizeof(__uint16_t) * 8 - 1));
    printf("valor: %0X\n", hi_bit2);

    __uint32_t hi_bit3 = (__uint32_t) (1 << (sizeof(__uint32_t) * 8 - 1));
    printf("valor: %0X\n", hi_bit3);    
    return 0;
}