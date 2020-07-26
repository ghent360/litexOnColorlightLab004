#include <generated/soc.h>
#include <generated/csr.h>

void clock_init(void);
unsigned clock(void);

void clock_init(void)
{
  	timer0_en_write(0);
	timer0_reload_write(0);
	timer0_load_write(0xffffffff);
	timer0_en_write(1);
}

unsigned clock(void)
{
	timer0_update_value_write(1);
    return (unsigned)timer0_value_read();
}
